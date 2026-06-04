# Child Demographic Codebook

This project keeps demographic metadata in an explicit child-level codebook
instead of treating CHAT header fields as final model covariates.

The current codebook is generated from:

- local extracted child metadata:
  `results/metadata/strict_naturalistic_custom_early20k_child_metadata_summary.csv`
- manually curated source overrides:
  `configs/manual_child_demographic_overrides.csv`
- builder:
  `src/build_child_demographic_codebook.py`

Run:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/build_child_demographic_codebook.py
```

Outputs:

```text
results/metadata/strict_naturalistic_child_demographic_codebook_2026-06-03.csv
results/metadata/pbm_child_demographic_codebook_2026-06-03.csv
results/metadata/strict_naturalistic_child_demographic_codebook_summary_2026-06-03.csv
```

## Coding Principles

- Keep local CHAT fields and curated fields separate.
- Use official TalkBank/PhonBank pages as first-pass evidence.
- Record source URL, scope, confidence, and notes for every curated SES or race
  claim.
- Do not infer race/ethnicity from child names, locations, accents, corpus
  names, or geography.
- Do not silently convert corpus-level or community-level descriptions into
  child-specific covariates.

## Scope Labels

- `child_specific`: source describes the individual child/family.
- `corpus_level_single_child`: one-child corpus where the corpus description
  effectively applies to that child/family.
- `corpus_level`: source describes all included children/families.
- `corpus_level_predominant`: source says the corpus is mostly from a group,
  but not necessarily every child.
- `community_or_study_population`: source describes the recruitment community
  or population rather than each child individually.
- `community_description`: source describes community race/ethnicity, not the
  individual child's race/ethnicity.
- `unknown`: no defensible value found yet.

## Current Interpretation

For PBM, sex is complete, but SES/class and race are not:

- Brown has child-specific class for Adam and Sarah, and child-specific race for
  Adam.
- Manchester has corpus-level-predominant middle-class status, not
  child-specific SES.
- Providence has no SES/class or race/ethnicity values available from the
  official page or local extracted metadata.

For the full 79-child strict naturalistic set, SES/class is available for some
corpora, but the evidence is mixed in scope:

- child-specific or single-child strong evidence: Brown Adam, Brown Sarah,
  Forrester, Lara.
- corpus-level evidence: Belfast, Weist.
- corpus-level-predominant evidence: Manchester.
- community/study-population evidence: Post.
- no current SES/class value: Providence, Wells, MPI-EVA-Manchester,
  Demetras1, Kuczaj, Sachs.

Race/ethnicity is even sparser:

- child-specific or single-child strong evidence: Brown Adam, Forrester, Lara.
- community-level only: Post.
- unknown for all other current strict naturalistic children.

As of 2026-06-03, these fields are suitable for descriptive reporting and
audits. They should be used as core predictors only with explicit restrictions
or sensitivity analyses, because most values are missing or corpus-level rather
than child-specific.
