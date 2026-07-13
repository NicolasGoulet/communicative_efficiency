# Child Utterance Counts

This plot uses the current strict naturalistic coverage summary:

`results/big_cleaned_dataset/default_naturalistic_merged_006_023/all_child_longitudinal_age_coverage_summary.csv`

## Summary

| children | total_child_utterances | median_per_child | min_per_child | max_per_child |
| --- | --- | --- | --- | --- |
| 79 | 1,140,218 | 2,989 | 274 | 154,593 |

## Thin-Bar Histogram

Bars are sorted from the highest to lowest child utterance count. The y-axis is log-scaled because a few children have very large counts compared with many small Wells children.

![Thin vertical bars by child](../figs/child_utterance_count_histogram/child_utterance_counts_thin_vertical.png)

## Readable Horizontal Version

Same data, rotated for labels.

![Horizontal bars by child](../figs/child_utterance_count_histogram/child_utterance_counts_horizontal.png)

## Age Range Covered By Each Child

Line segments show the minimum-to-maximum age range available for each child. Dots show the observed recording ages inside that range, with larger dots indicating more child utterances at that exact age.

![Age coverage sorted by first observed age](../figs/child_utterance_count_histogram/child_age_coverage_sorted_by_first_age.png)

## Age Range In The Same Order As The Histogram

This is the same coverage information, but sorted by total child utterance count to match the thin-bar histogram above.

![Age coverage sorted by utterance count](../figs/child_utterance_count_histogram/child_age_coverage_sorted_by_utterance_count.png)

## Demographic Metadata Availability

This section uses the current strict-naturalistic demographic codebook plus a small online source-backed patch file:

`results/metadata/strict_naturalistic_child_demographic_codebook_2026-06-03.csv`

`configs/child_demographic_online_value_patches.csv`

Unknown means "not available in the current extracted metadata", not that the child lacks the attribute. Nationality is not currently available as a child-specific extracted field; the report therefore includes only dataset-level corpus region.

Full CSVs:

- [child metadata profile](../results/child_utterance_count_histogram/child_metadata_profile.csv)
- [field availability summary](../results/child_utterance_count_histogram/child_metadata_availability_summary.csv)
- [dataset metadata summary](../results/child_utterance_count_histogram/dataset_metadata_availability_summary.csv)
- [online research audit](../results/child_utterance_count_histogram/child_demographic_online_research_audit.csv)

| field | known_child_specific | known_corpus_level | known_predominant_or_community | unknown_or_unavailable | total_children | note |
| --- | --- | --- | --- | --- | --- | --- |
| SES / social class | 3 | 15 | 15 | 46 | 79 | Current codebook combines local CHAT metadata and manual TalkBank page checks. |
| Race / ethnicity | 2 | 1 | 3 | 73 | 79 | Sparse; community-level descriptions should not be treated as child-specific race codes. |
| Parental education | 2 | 6 | 0 | 71 | 79 | Available only when documented in corpus-level or child-specific notes. |
| Sex / gender marker | 78 | 0 | 0 | 1 | 79 | From local extracted metadata plus documented online patches; label kept as sex because that is the source-field name. |
| Child-specific nationality | 0 | 0 | 0 | 79 | 79 | Not currently extracted locally. Corpus region is shown separately and must not be interpreted as nationality. |
| Corpus region | 0 | 79 | 0 | 0 | 79 | Dataset-level geography only. |

## Online Research Audit

Official corpus pages were checked where local metadata had holes. The only new value patches found in this pass are the Gina and Helen sex/gender markers from the official MPI-EVA-Manchester page. The SES/race/nationality holes mostly remain unavailable in public corpus pages, so they stay coded as unknown/unavailable instead of being guessed.

| dataset | child_id | fields_checked | result | source_type | source_url | source_note | coding_decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Demetras1 | * | SES/race/nationality | not_found_on_public_corpus_page | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Demetras1.html | Official page gives participant count, USA location, Trevor birthdate, and recording design; it does not expose SES, race/ethnicity, or child-specific nationality. | Keep SES/race/nationality unknown in current extracted metadata. |
| Kuczaj | * | SES/race/nationality | not_found_on_public_corpus_page | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Kuczaj.html | Official page gives participant count, USA location, diary-study design, and Abe's recording ages; it does not expose SES, race/ethnicity, or child-specific nationality. | Keep SES/race/nationality unknown in current extracted metadata. |
| MPI-EVA-Manchester | Gina | sex | patched_from_official_page_pronouns | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/MPI-EVA-Manchester.html | Official page uses feminine pronouns for Gina/Rubi, including her play and her mother. | Patch sex marker to female with medium confidence. |
| MPI-EVA-Manchester | Helen | sex | patched_from_official_page_pronouns | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/MPI-EVA-Manchester.html | Official page uses feminine pronouns for Helen/Hannah, including her play and her mother. | Patch sex marker to female with medium confidence. |
| MPI-EVA-Manchester | * | SES/race/nationality | not_found_on_public_corpus_page | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/MPI-EVA-Manchester.html | Official page documents four dense-sampling children in England, home recordings, and pseudonym/true-name notes; it does not expose SES, race/ethnicity, or child-specific nationality. | Keep SES/race/nationality unknown in current extracted metadata. |
| Providence | * | sex/language_background | already_available_or_confirmed | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official page lists the six children's sex markers and says the corpus contains monolingual English-speaking children in Providence, RI. | No new SES/race/nationality values; local sex markers are already populated. |
| Providence | * | SES/race/nationality | not_found_on_public_corpus_page | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official page gives sex, age range, sessions, monolingual English background, and collection design, but no SES, race/ethnicity, or child-specific nationality. | Keep SES/race/nationality unknown in current extracted metadata. |
| Sachs | * | SES/race/nationality | not_found_on_public_corpus_page | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Sachs.html | Official page says this is Jacqueline Sachs' longitudinal study of her daughter Naomi and gives USA location and age coverage; it does not expose SES, race/ethnicity, or child-specific nationality. | Keep SES/race/nationality unknown in current extracted metadata. |
| Weist | Ben | sex | not_found_on_public_corpus_page | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official page lists Ben with birthdate, ages, and transcripts, and documents middle-class professional-parent family background for all Fredonia children; it does not expose Ben's sex marker. | Keep Ben sex marker unknown rather than inferring from name. |
| Weist | * | SES/parental_education | already_available_or_confirmed | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official page says all Fredonia children came from middle-class homes and their parents were professionals. | Keep existing corpus-level SES and parental-education coding. |
| Wells | * | SES/race/nationality | not_exposed_per_child_on_public_page | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official page says family-background details were collected and used for sample design, but the current public page does not expose per-child SES, race/ethnicity, or child-specific nationality values. | Keep Wells SES/race/nationality unavailable in current metadata until deeper original materials are coded. |

## Dataset-Level Metadata Coverage

| dataset | children | child_utterances | sex_known | ses_known | race_known | parent_education_known | corpus_regions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Wells | 32 | 37,967 | 32 | 0 | 0 | 0 | UK |
| Manchester | 12 | 232,614 | 12 | 12 | 0 | 0 | UK |
| Belfast | 8 | 22,942 | 8 | 8 | 0 | 0 | UK / Northern Ireland |
| Providence | 6 | 121,339 | 6 | 0 | 0 | 0 | US |
| Weist | 6 | 46,347 | 5 | 6 | 0 | 6 | US |
| MPI-EVA-Manchester | 4 | 462,100 | 4 | 0 | 0 | 0 | UK |
| Brown | 3 | 92,555 | 3 | 2 | 1 | 1 | US |
| Post | 3 | 8,068 | 3 | 3 | 3 | 0 | US |
| Demetras1 | 1 | 6,842 | 1 | 0 | 0 | 0 | US |
| Forrester | 1 | 6,663 | 1 | 1 | 1 | 0 | UK |
| Kuczaj | 1 | 37,109 | 1 | 0 | 0 | 0 | US |
| Lara | 1 | 49,328 | 1 | 1 | 1 | 1 | UK |
| Sachs | 1 | 16,344 | 1 | 0 | 0 | 0 | US |

## Child Mini Reports

Each row is one child. The source labels are intentionally explicit: child-specific is strongest; corpus-level and community-level entries are useful documentation but should be used cautiously in models.

### Belfast

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Barbara | 2,901 | 28.3-49.6 | female | local_extracted_metadata | UK / Northern Ireland | upper-working-class children | corpus_level | unknown | unknown | unknown |
| Conor | 3,920 | 44.5-54.2 | male | local_extracted_metadata | UK / Northern Ireland | upper-working-class children | corpus_level | unknown | unknown | unknown |
| Courtney | 2,423 | 40-48.4 | female | local_extracted_metadata | UK / Northern Ireland | upper-working-class children | corpus_level | unknown | unknown | unknown |
| David | 2,572 | 24.1-50.1 | male | local_extracted_metadata | UK / Northern Ireland | upper-working-class children | corpus_level | unknown | unknown | unknown |
| John | 1,994 | 42.0-52.0 | male | local_extracted_metadata | UK / Northern Ireland | upper-working-class children | corpus_level | unknown | unknown | unknown |
| Michelle | 3,505 | 28.9-52.6 | female | local_extracted_metadata | UK / Northern Ireland | upper-working-class children | corpus_level | unknown | unknown | unknown |
| Rachel | 1,606 | 29.8-38.1 | female | local_extracted_metadata | UK / Northern Ireland | upper-working-class children | corpus_level | unknown | unknown | unknown |
| Stuart | 4,021 | 41.4-53.1 | male | local_extracted_metadata | UK / Northern Ireland | upper-working-class children | corpus_level | unknown | unknown | unknown |

### Brown

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Adam | 46,496 | 27.1-62.4 | male | local_extracted_metadata | US | middle-class well-educated family | child_specific | Black | child_specific | well_educated_family |
| Eve | 11,750 | 18-27 | female | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |
| Sarah | 34,309 | 27.2-61.2 | female | local_extracted_metadata | US | working-class family | child_specific | unknown | unknown | unknown |

### Demetras1

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Trevor | 6,842 | 24.9-47.9 | male | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |

### Forrester

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ella | 6,663 | 12.0-60 | female | local_extracted_metadata | UK | middle-class participants | corpus_level_single_child | White | corpus_level_single_child | unknown |

### Kuczaj

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Abe | 37,109 | 28.8-60.4 | male | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |

### Lara

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lara | 49,328 | 21.4-39.8 | female | local_extracted_metadata | UK | two white university-graduate parents | child_specific | White | child_specific | two_university_graduate_parents |

### MPI-EVA-Manchester

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Eleanor | 85,263 | 24.1-37 | female | local_extracted_metadata | UK | unknown | unknown | unknown | unknown | unknown |
| Fraser | 150,447 | 24.0-37.1 | male | local_extracted_metadata | UK | unknown | unknown | unknown | unknown | unknown |
| Gina | 71,797 | 36.0-56.0 | female | official_talkbank_page | UK | unknown | unknown | unknown | unknown | unknown |
| Helen | 154,593 | 36.1-61.6 | female | official_talkbank_page | UK | unknown | unknown | unknown | unknown | unknown |

### Manchester

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Anne | 20,707 | 22.2-33.3 | female | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Aran | 17,588 | 23.4-34.9 | male | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Becky | 24,432 | 24.2-35.5 | female | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Carl | 25,663 | 20.7-32.5 | male | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Dominic | 21,927 | 22.8-34.5 | male | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Gail | 17,280 | 23.9-35.4 | female | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Joel | 18,756 | 23.0-34.4 | male | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| John | 13,770 | 23.5-34.8 | male | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Liz | 16,676 | 23.3-34.6 | female | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Nicole | 17,798 | 24.8-36.3 | female | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Ruth | 20,831 | 23.5-35.7 | female | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |
| Warren | 17,186 | 22.2-33.7 | male | local_extracted_metadata | UK | predominantly middle-class families | corpus_level_predominant | unknown | unknown | unknown |

### Post

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lew | 2,442 | 22.7-32.2 | female | local_extracted_metadata | US | predominantly white working-class rural Southern community | community_or_study_population | predominantly_white_community | community_description | unknown |
| She | 2,637 | 19.6-29.3 | female | local_extracted_metadata | US | predominantly white working-class rural Southern community | community_or_study_population | predominantly_white_community | community_description | unknown |
| Tow | 2,989 | 19.2-29.1 | female | local_extracted_metadata | US | predominantly white working-class rural Southern community | community_or_study_population | predominantly_white_community | community_description | unknown |

### Providence

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Alex | 19,155 | 16.9-41.5 | male | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |
| Ethan | 13,604 | 11.1-35.0 | male | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |
| Lily | 28,028 | 13.1-48.1 | female | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |
| Naima | 33,778 | 11.9-46.3 | female | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |
| Violet | 10,795 | 14-47.8 | female | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |
| William | 15,979 | 16.4-40.6 | male | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |

### Sachs

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Naomi | 16,344 | 15.0-57.1 | female | local_extracted_metadata | US | unknown | unknown | unknown | unknown | unknown |

### Weist

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ben | 3,371 | 28.2-39.7 | unknown | unknown | US | middle-class homes with professional parents | corpus_level | unknown | unknown | professional_parents |
| Emily | 7,437 | 30.2-53.6 | female | local_extracted_metadata | US | middle-class homes with professional parents | corpus_level | unknown | unknown | professional_parents |
| Emma | 6,863 | 31.3-56.1 | female | local_extracted_metadata | US | middle-class homes with professional parents | corpus_level | unknown | unknown | professional_parents |
| Jillian | 5,876 | 25.0-34 | female | local_extracted_metadata | US | middle-class homes with professional parents | corpus_level | unknown | unknown | professional_parents |
| Matt | 11,113 | 27.3-60.2 | male | local_extracted_metadata | US | middle-class homes with professional parents | corpus_level | unknown | unknown | professional_parents |
| Roman | 11,687 | 26.7-55.7 | male | local_extracted_metadata | US | middle-class homes with professional parents | corpus_level | unknown | unknown | professional_parents |

### Wells

| child_id | child_utterances | age_range_months | sex | sex_source_type | corpus_region | ses_label | ses_scope | race_ethnicity | race_scope | parental_education |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Abigail | 1,161 | 17.9-56 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Benjamin | 1,471 | 17.7-60.8 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Betty | 1,949 | 18.1-59.1 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Darren | 1,566 | 18.1-58.2 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Debbie | 1,412 | 18.3-47.9 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Ellen | 2,577 | 17.9-57.7 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Elspeth | 1,258 | 18-60.1 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Frances | 1,516 | 18.0-58.3 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Gary | 1,909 | 18-57 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Gavin | 1,753 | 18.7-57.6 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Geoffrey | 1,288 | 18-59.7 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Gerald | 1,610 | 18.2-57.2 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Harriet | 1,431 | 18.1-58.1 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Iris | 1,601 | 18-56.1 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Jack | 2,172 | 17.9-57.0 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Jason | 1,312 | 18-60.6 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Jonathan | 2,320 | 18.2-55.5 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Laura | 889 | 18.0-42.1 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Lee | 424 | 17.9-42.0 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Martin | 663 | 17.9-41.9 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Nancy | 471 | 18.1-39.1 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Neil | 659 | 18.1-42.0 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Neville | 1,024 | 17.8-41.9 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Olivia | 911 | 18-41.7 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Penny | 766 | 18.3-41.9 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Rosie | 274 | 19-42.4 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Samantha | 652 | 18.2-42.4 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Sean | 342 | 18.4-42.3 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Sheila | 684 | 21.1-42.8 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Simon | 538 | 17.7-41.7 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Stella | 710 | 18.3-42 | female | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |
| Tony | 654 | 17.9-42.3 | male | local_extracted_metadata | UK | unknown | unavailable_in_current_metadata | unknown | unknown | unknown |

## Demographic Source Notes

These rows show the provenance notes currently available for children or corpora with any non-empty metadata source fields. The full CSV above preserves all profile columns.

| dataset | child_id | sex_source_type | sex_source_url | sex_source_note | sex_confidence | ses_source_type | ses_source_url | ses_source_note | race_source_type | race_source_url | race_source_note | parental_education_source_url | parental_education_source_note | demographic_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Belfast | Barbara | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Belfast.html | Project description describes the study as eight upper-working-class children in Belfast; recruitment targeted families with local input from upper-working-class and lower-middle-class adults. | unknown | unknown | unknown | unknown | Overrides local CHAT MC tag because official corpus description is more specific. | unknown |
| Belfast | Conor | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Belfast.html | Project description describes the study as eight upper-working-class children in Belfast; recruitment targeted families with local input from upper-working-class and lower-middle-class adults. | unknown | unknown | unknown | unknown | Overrides local CHAT MC tag because official corpus description is more specific. | unknown |
| Belfast | Courtney | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Belfast.html | Project description describes the study as eight upper-working-class children in Belfast; recruitment targeted families with local input from upper-working-class and lower-middle-class adults. | unknown | unknown | unknown | unknown | Overrides local CHAT MC tag because official corpus description is more specific. | unknown |
| Belfast | David | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Belfast.html | Project description describes the study as eight upper-working-class children in Belfast; recruitment targeted families with local input from upper-working-class and lower-middle-class adults. | unknown | unknown | unknown | unknown | Overrides local CHAT MC tag because official corpus description is more specific. | unknown |
| Belfast | John | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Belfast.html | Project description describes the study as eight upper-working-class children in Belfast; recruitment targeted families with local input from upper-working-class and lower-middle-class adults. | unknown | unknown | unknown | unknown | Overrides local CHAT MC tag because official corpus description is more specific. | unknown |
| Belfast | Michelle | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Belfast.html | Project description describes the study as eight upper-working-class children in Belfast; recruitment targeted families with local input from upper-working-class and lower-middle-class adults. | unknown | unknown | unknown | unknown | Overrides local CHAT MC tag because official corpus description is more specific. | unknown |
| Belfast | Rachel | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Belfast.html | Project description describes the study as eight upper-working-class children in Belfast; recruitment targeted families with local input from upper-working-class and lower-middle-class adults. | unknown | unknown | unknown | unknown | Overrides local CHAT MC tag because official corpus description is more specific. | unknown |
| Belfast | Stuart | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Belfast.html | Project description describes the study as eight upper-working-class children in Belfast; recruitment targeted families with local input from upper-working-class and lower-middle-class adults. | unknown | unknown | unknown | unknown | Overrides local CHAT MC tag because official corpus description is more specific. | unknown |
| Brown | Adam | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Brown.html | Official Brown page describes Adam's family as middle class and well educated. | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Brown.html | Official Brown page describes Adam as Black and as a Standard American English speaker rather than an AAE speaker. | https://talkbank.org/childes/access/Eng-NA/Brown.html | Official Brown page describes Adam's family as well educated. | unknown |
| Brown | Eve | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | unknown | unknown | unknown | unknown | unknown | unknown | unknown | Official Brown page does not appear to provide Eve SES/class or race/ethnicity. | unknown |
| Brown | Sarah | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Brown.html | Official Brown page describes Sarah as the child of a working-class family. | unknown | unknown | unknown | unknown | No source found for race/ethnicity. | unknown |
| Demetras1 | Trevor | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | unknown | unknown | unknown | unknown | unknown | unknown | unknown | Official TalkBank page does not appear to provide SES/class or race/ethnicity. | unknown |
| Forrester | Ella | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Forrester.html | Official Forrester page states all participants in the dialogs are British white and middle class. | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Forrester.html | Official Forrester page states all participants in the dialogs are British white and middle class. | unknown | unknown | One-child corpus; corpus-level description effectively applies to the included child/family. |
| Kuczaj | Abe | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | unknown | unknown | unknown | unknown | unknown | unknown | unknown | Official TalkBank page does not appear to provide SES/class or race/ethnicity. | unknown |
| Lara | Lara | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Lara.html | Official Lara page describes Lara as the first-born monolingual English daughter of two white university graduates. | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Lara.html | Official Lara page describes Lara as the daughter of two white university graduates. | https://talkbank.org/childes/access/Eng-UK/Lara.html | Official Lara page describes both parents as university graduates. | unknown |
| MPI-EVA-Manchester | Eleanor | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | unknown | unknown | unknown | unknown | unknown | unknown | unknown | Official TalkBank page does not appear to provide SES/class or race/ethnicity. | unknown |
| MPI-EVA-Manchester | Fraser | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | unknown | unknown | unknown | unknown | unknown | unknown | unknown | Official TalkBank page does not appear to provide SES/class or race/ethnicity. | unknown |
| MPI-EVA-Manchester | Gina | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/MPI-EVA-Manchester.html | Official page describes Gina/Rubi recordings with phrases including "her play" and "her mother". | medium | unknown | unknown | unknown | unknown | unknown | unknown | unknown | Official TalkBank page does not appear to provide SES/class or race/ethnicity. | unknown |
| MPI-EVA-Manchester | Helen | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/MPI-EVA-Manchester.html | Official page describes Helen/Hannah recordings with phrases including "her play" and "her mother". | medium | unknown | unknown | unknown | unknown | unknown | unknown | unknown | Official TalkBank page does not appear to provide SES/class or race/ethnicity. | unknown |
| Manchester | Anne | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Aran | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Becky | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Carl | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Dominic | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Gail | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Joel | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | John | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Liz | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Nicole | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Ruth | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Manchester | Warren | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Manchester.html | Official Manchester page says SES was not a recruitment criterion but children were from predominantly middle-class families. | unknown | unknown | unknown | unknown | This is corpus-level and not child-specific. | unknown |
| Post | Lew | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Post.html | Official Post page says the area was chosen as a rural Southern community with a predominantly white working-class population and that participating families lived in that community. | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Post.html | Official Post page describes the community as predominantly white; this is not an individual child race code. | unknown | unknown | Use class more confidently than race; race remains community-level only. |
| Post | She | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Post.html | Official Post page says the area was chosen as a rural Southern community with a predominantly white working-class population and that participating families lived in that community. | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Post.html | Official Post page describes the community as predominantly white; this is not an individual child race code. | unknown | unknown | Use class more confidently than race; race remains community-level only. |
| Post | Tow | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Post.html | Official Post page says the area was chosen as a rural Southern community with a predominantly white working-class population and that participating families lived in that community. | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Post.html | Official Post page describes the community as predominantly white; this is not an individual child race code. | unknown | unknown | Use class more confidently than race; race remains community-level only. |
| Providence | Alex | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page provides sex age sessions and monolingual home interaction description but no SES/class or race/ethnicity. | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page does not appear to provide race/ethnicity. | unknown | unknown | Ethan later diagnosed with Asperger's at age 5 per official page; not SES/race. |
| Providence | Ethan | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page provides sex age sessions and monolingual home interaction description but no SES/class or race/ethnicity. | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page does not appear to provide race/ethnicity. | unknown | unknown | Ethan later diagnosed with Asperger's at age 5 per official page; not SES/race. |
| Providence | Lily | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page provides sex age sessions and monolingual home interaction description but no SES/class or race/ethnicity. | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page does not appear to provide race/ethnicity. | unknown | unknown | Ethan later diagnosed with Asperger's at age 5 per official page; not SES/race. |
| Providence | Naima | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page provides sex age sessions and monolingual home interaction description but no SES/class or race/ethnicity. | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page does not appear to provide race/ethnicity. | unknown | unknown | Ethan later diagnosed with Asperger's at age 5 per official page; not SES/race. |
| Providence | Violet | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page provides sex age sessions and monolingual home interaction description but no SES/class or race/ethnicity. | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page does not appear to provide race/ethnicity. | unknown | unknown | Ethan later diagnosed with Asperger's at age 5 per official page; not SES/race. |
| Providence | William | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page provides sex age sessions and monolingual home interaction description but no SES/class or race/ethnicity. | official_talkbank_page | https://talkbank.org/phon/access/Eng-NA/Providence.html | Official Providence page does not appear to provide race/ethnicity. | unknown | unknown | Ethan later diagnosed with Asperger's at age 5 per official page; not SES/race. |
| Sachs | Naomi | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | unknown | unknown | unknown | unknown | unknown | unknown | unknown | Official TalkBank page does not appear to provide SES/class or race/ethnicity. | unknown |
| Weist | Ben | unknown | unknown | unknown | unknown | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says all Fredonia children came from middle-class homes and their parents were professionals. | unknown | unknown | unknown | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says parents were professionals. | unknown |
| Weist | Emily | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says all Fredonia children came from middle-class homes and their parents were professionals. | unknown | unknown | unknown | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says parents were professionals. | unknown |
| Weist | Emma | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says all Fredonia children came from middle-class homes and their parents were professionals. | unknown | unknown | unknown | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says parents were professionals. | unknown |
| Weist | Jillian | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says all Fredonia children came from middle-class homes and their parents were professionals. | unknown | unknown | unknown | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says parents were professionals. | unknown |
| Weist | Matt | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says all Fredonia children came from middle-class homes and their parents were professionals. | unknown | unknown | unknown | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says parents were professionals. | unknown |
| Weist | Roman | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says all Fredonia children came from middle-class homes and their parents were professionals. | unknown | unknown | unknown | https://talkbank.org/childes/access/Eng-NA/Weist.html | Official Weist page says parents were professionals. | unknown |
| Wells | Abigail | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Benjamin | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Betty | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Darren | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Debbie | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Ellen | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Elspeth | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Frances | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Gary | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Gavin | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Geoffrey | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Gerald | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Harriet | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Iris | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Jack | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Jason | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Jonathan | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Laura | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Lee | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Martin | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Nancy | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Neil | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Neville | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Olivia | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Penny | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Rosie | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Samantha | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Sean | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Sheila | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Simon | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Stella | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |
| Wells | Tony | local_extracted_metadata | local_extracted_metadata | Sex/gender marker came from local extracted CHAT/metadata rows. | medium | official_talkbank_page | https://talkbank.org/childes/access/Eng-UK/Wells.html | Official Wells page says family-background details were collected and used for sample design but the current local extracted metadata and page do not expose per-child SES/class values. | unknown | unknown | unknown | unknown | unknown | Potentially recoverable only from deeper original Wells materials if available. |

## Largest Children

| dataset | child_id | child_utterances | child_sessions | child_age_min_months | child_age_max_months | child_age_bins |
| --- | --- | --- | --- | --- | --- | --- |
| MPI-EVA-Manchester | Helen | 154,593 | 184 | 36.07 | 61.63 | 5 |
| MPI-EVA-Manchester | Fraser | 150,447 | 205 | 24.03 | 37.10 | 3 |
| MPI-EVA-Manchester | Eleanor | 85,263 | 180 | 24.07 | 37 | 3 |
| MPI-EVA-Manchester | Gina | 71,797 | 118 | 36.03 | 55.97 | 4 |
| Lara | Lara | 49,328 | 120 | 21.43 | 39.83 | 4 |
| Brown | Adam | 46,496 | 55 | 27.13 | 62.40 | 7 |
| Kuczaj | Abe | 37,109 | 210 | 28.80 | 60.37 | 7 |
| Brown | Sarah | 34,309 | 139 | 27.17 | 61.20 | 7 |
| Providence | Naima | 33,778 | 87 | 11.87 | 46.33 | 5 |
| Providence | Lily | 28,028 | 79 | 13.07 | 48.07 | 6 |
| Manchester | Carl | 25,663 | 33 | 20.73 | 32.50 | 3 |
| Manchester | Becky | 24,432 | 34 | 24.23 | 35.50 | 2 |

## Smallest Children

| dataset | child_id | child_utterances | child_sessions | child_age_min_months | child_age_max_months | child_age_bins |
| --- | --- | --- | --- | --- | --- | --- |
| Wells | Penny | 766 | 9 | 18.30 | 41.87 | 4 |
| Wells | Stella | 710 | 8 | 18.27 | 42 | 5 |
| Wells | Sheila | 684 | 9 | 21.07 | 42.83 | 5 |
| Wells | Martin | 663 | 9 | 17.87 | 41.93 | 4 |
| Wells | Neil | 659 | 8 | 18.13 | 42.03 | 5 |
| Wells | Tony | 654 | 9 | 17.87 | 42.27 | 5 |
| Wells | Samantha | 652 | 9 | 18.20 | 42.37 | 5 |
| Wells | Simon | 538 | 9 | 17.70 | 41.73 | 4 |
| Wells | Nancy | 471 | 8 | 18.07 | 39.10 | 4 |
| Wells | Lee | 424 | 8 | 17.93 | 41.97 | 4 |
| Wells | Sean | 342 | 9 | 18.37 | 42.30 | 5 |
| Wells | Rosie | 274 | 9 | 19 | 42.37 | 5 |

## Dataset Contribution

| dataset | children | utterances | share_pct |
| --- | --- | --- | --- |
| MPI-EVA-Manchester | 4 | 462,100 | 40.53 |
| Manchester | 12 | 232,614 | 20.40 |
| Providence | 6 | 121,339 | 10.64 |
| Brown | 3 | 92,555 | 8.12 |
| Lara | 1 | 49,328 | 4.33 |
| Weist | 6 | 46,347 | 4.06 |
| Wells | 32 | 37,967 | 3.33 |
| Kuczaj | 1 | 37,109 | 3.25 |
| Belfast | 8 | 22,942 | 2.01 |
| Sachs | 1 | 16,344 | 1.43 |
| Post | 3 | 8,068 | 0.71 |
| Demetras1 | 1 | 6,842 | 0.60 |
| Forrester | 1 | 6,663 | 0.58 |
