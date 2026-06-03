# Utterance Effort Measurement Package Write-Up

Created: 2026-06-02

This note explains the software resources used to compute utterance-level effort
measures. The guiding principle is that counts should be computed from the same
cleaned utterance string that is submitted for surprisal scoring. Child forms,
family-specific forms, nonwords, and shortenings are therefore preserved as
written rather than corrected to adult target forms.

## Current Candidate Measures

| Measure | Main candidate | Fallback / diagnostic | Why |
| --- | --- | --- | --- |
| Words | local lexical-token regex over cleaned text | whitespace word count diagnostic | Aligns exactly with scored target text; punctuation is excluded. |
| Morphemes | CHAT `%mor` proxy and surface suffix heuristic shown side by side | manual decision pending | `%mor` tracks linguistic/MLU-style structure; surface suffix heuristic better reflects the scored string when repetitions or retracings are preserved. |
| Syllables | CMUdict for known words + `syllables` package for OOV word forms | G2P-vowel, Pyphen, vowel heuristic diagnostics | CMUdict is preferred when available; `syllables` handles written nonwords better than G2P vowel-nucleus counts in cases like `firetruck`. |
| Phonemes | CMUdict for known words + `g2p-en` for OOV word forms | token-level audit columns | G2P is naturally a phoneme predictor and lets us preserve child/nonword spellings. |

## Package Roles

### `cmudict`

Role: reference pronunciation dictionary for English words.

CMUdict maps English word forms to North American English ARPABET
pronunciations. It is the strongest source we use for dictionary-covered words.
For syllables, we count ARPABET vowel phones with stress digits. For phonemes,
we count ARPABET phones.

Use in this project:

- dictionary-covered syllable counts;
- dictionary-covered phoneme counts;
- diagnostic OOV flags.

Limitations:

- many child forms, nonce forms, proper names, special forms, and shortened
  spellings are OOV;
- CMUdict represents canonical pronunciations, not the child's actual phonetic
  realization;
- words may have multiple pronunciations, so the audit records ambiguity flags.

Reporting language:

> For dictionary-covered English words, syllable and phoneme counts were derived
> from CMUdict ARPABET pronunciations. Rows containing out-of-dictionary word
> forms were flagged and handled by separate fallback procedures without
> correcting the observed spelling.

Source: https://www.speech.cs.cmu.edu/cgi-bin/cmudict

### `pronouncing`

Role: Python interface to CMUdict.

`pronouncing` provides convenient access to CMUdict pronunciations and a
syllable-count helper based on the ARPABET phones.

Use in this project:

- fetch candidate CMUdict pronunciations for each word;
- compute CMU-only syllable counts;
- record multiple-pronunciation diagnostics.

Limitations:

- inherits CMUdict coverage limits;
- not used for OOV fallback.

Source: https://pronouncing.readthedocs.io/en/latest/

### `g2p-en`

Role: grapheme-to-phoneme fallback for OOV word forms.

`g2p-en` predicts ARPABET-like phoneme sequences from spelling. This is useful
because the project keeps child forms as written. For example, a child form such
as `commydit` is not corrected; it is passed directly to the G2P model.

Use in this project:

- OOV phoneme fallback;
- token-level phoneme audit for nonwords and names.

Important decision:

- `g2p-en` is **not** currently the main syllable counter.
- We keep its vowel-nucleus syllable count as a diagnostic only.

Why not main syllables:

- manual review caught `firetruck`: G2P predicts `F AY1 R T R AH2 K`, which
  gives two vowel nuclei, while the intended effort count for review was
  `fi-re-truck` = 3 syllables.

Limitations:

- G2P predictions are model-generated pronunciations, not observed child
  productions;
- English spelling-to-sound is ambiguous;
- phoneme counts for unusual child forms remain estimates.

Reporting language:

> For out-of-dictionary word forms, phoneme counts were estimated using an
> English grapheme-to-phoneme model applied to the observed spelling. These
> estimates were flagged separately and treated as generated phonological
> approximations, not as manually verified child pronunciations.

Source: https://github.com/Kyubyong/g2p

### `syllables`

Role: OOV syllable fallback.

The `syllables` package estimates syllable counts from the written word form. It
is used only when CMUdict has no entry for a token.

Use in this project:

- OOV syllable fallback for preserved child/nonword spellings;
- side-by-side diagnostic in the review workbook.

Why this fallback:

- it handles examples such as `firetruck`, `dabadoo`, and `boing` in a way that
  better matched the user's review judgments than G2P vowel-nucleus syllables;
- CMUdict remains preferred whenever available, consistent with the package's
  own documentation that CMUdict is preferable where accuracy matters.

Limitations:

- it is an estimator, not a gold standard;
- unusual child forms still need audit;
- it gives syllable counts, not phonemes.

Reporting language:

> For word forms absent from CMUdict, syllable counts were estimated from the
> observed spelling using the `syllables` package. These fallback cases were
> flagged and reviewed in a stratified validation sample.

Source: https://pypi.org/project/syllables/

### `pyphen`

Role: diagnostic only.

Pyphen provides hyphenation patterns. Hyphenation is related to but not identical
with syllabification. In the review probe, Pyphen is shown only as a comparison
column.

Use in this project:

- diagnostic comparison for syllable-like segmentation;
- not used in the main recommended counts.

Why not main:

- it can split written hyphenation in ways that do not match the intended
  spoken syllable count;
- example: Pyphen treats `boing` as `bo-ing`, which overcounts for our effort
  review.

Source: https://pyphen.org/

### Local Regex Word Counter

Role: main word count.

Words are counted using a local regular-expression tokenizer over the cleaned
utterance text. Punctuation is excluded. Internal apostrophes are preserved
inside word tokens, so `don't` is one word.

Use in this project:

- main word count candidate;
- aligns with the target text sent for surprisal scoring.

Limitations:

- this is an orthographic token count, not a CHAT morpheme count;
- compounds and underscores follow the cleaned-text tokenization.

Reporting language:

> Word counts were computed as lexical orthographic tokens in the cleaned target
> utterance, excluding punctuation and preserving the word forms submitted for
> surprisal scoring.

### CHAT `%mor` Parser

Role: linguistic morphology / MLU-style diagnostic.

When available, `%mor` tiers are parsed to estimate a linguistic morpheme count.
This is conceptually different from surface production effort because CHAT
retracing and repetition markers may collapse material that remains in the
cleaned surface utterance.

Use in this project:

- candidate morpheme count;
- diagnostic comparison against surface suffix heuristic;
- flags where `%mor` and surface string differ substantially.

Limitations:

- this script is a transparent proxy, not a replacement for official CLAN `mlu`;
- `%mor` may encode linguistic structure rather than every surface repetition;
- the final choice between `%mor` and surface morphology is theoretical.

Reporting language:

> CHAT `%mor` tiers were used to derive a linguistic morphology/MLU-style count
> where available. Because the present analyses score the cleaned surface
> utterance, `%mor` counts were compared against surface-aligned counts and
> cases with retracing/repetition mismatch were flagged.

Source: https://talkbank.org/0info/manuals/CLAN.html

## Infrastructure Packages

### `openpyxl`

Role: spreadsheet output only.

Used to create the formatted LibreOffice-friendly review workbook. It does not
affect counts.

### `pandas`

Role: CSV loading and tabular data handling.

Used to read scoring files and write audit tables. It does not define any
scientific count.

### NLTK Resources

Role: runtime support for `g2p-en`.

The `g2p-en` package requires NLTK resources. These were installed locally under:

```text
data/nltk_data/
```

They are treated as data/runtime resources, not source code.

## Reviewer-Facing Summary

The current defensible strategy is:

1. Count effort from the same cleaned text used for surprisal scoring.
2. Do not correct child forms to adult targets.
3. Use dictionary pronunciations when available.
4. Use explicit, flagged fallbacks for OOV word forms.
5. Keep diagnostic columns and a stratified manual review workbook so reviewers
   can see how ambiguous cases were handled.

Current review files:

```text
results/count_validation/publication_measurement_review_50.xlsx
results/count_validation/publication_measurement_review_50.csv
results/count_validation/publication_measurement_review_50_tokens.csv
results/count_validation/publication_measurement_probe_50.csv
```

