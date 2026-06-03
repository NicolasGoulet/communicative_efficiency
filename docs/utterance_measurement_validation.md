# Utterance Measurement Validation

Created: 2026-06-02

This note records the current publication-oriented counting strategy for Route 1
effort / complexity measures. The implemented audit probe is:

```text
src/validate_utterance_measurement_strategies.py
```

Default outputs:

```text
results/count_validation/publication_measurement_probe_50.csv
results/count_validation/publication_measurement_probe_50.md
results/count_validation/publication_measurement_review_50.csv
results/count_validation/publication_measurement_review_50_tokens.csv
results/count_validation/publication_measurement_review_50.xlsx
```

## Reference Hierarchy

The probe reports several strategies side by side rather than hiding
methodological disagreements.

1. **Words**
   - Current reference: cleaned orthographic lexical tokens, punctuation
     excluded.
   - This is aligned with the string we actually send for surprisal scoring.

2. **Morphemes**
   - Domain-native reference: CHAT `%mor` tiers and CLAN MLU-style treatment.
   - The current script implements a transparent `%mor` proxy and also reports
     a surface-string suffix heuristic.
   - Important: CHAT retracing/repetition markers such as `[/]` can make
     `%mor` / MLU-style counts intentionally diverge from the cleaned surface
     utterance. The probe flags this with `raw_repetition_marker` and
     `mor_surface_mismatch`.

3. **Syllables**
   - Current recommended count: CMU Pronouncing Dictionary ARPABET
     pronunciations for dictionary-covered words, plus the `syllables` package
     for OOV word forms as written.
   - G2P-derived syllables are retained only as a diagnostic, because examples
     such as `firetruck` show that G2P vowel-nucleus counts can undercount the
     syllabification intended for this project's effort measure.
   - `pyphen`, the `syllables` package, and the older vowel/final-e heuristic
     are kept as diagnostics, not as the preferred publication count.

4. **Phonemes**
   - Current recommended count: CMUdict ARPABET segment count for
     dictionary-covered words, plus `g2p-en` ARPABET predictions for OOV word
     forms as written.
   - This is a canonical phonological count of the cleaned word string, not a
     claim about the child's realized phonetic production.
   - CMU-only diagnostic columns remain blank when a row contains CMUdict OOV
     words. The recommended columns are complete because OOV words are passed to
     `g2p-en` without correcting the spelling.

## External Method Anchors

- TalkBank / CLAN documentation identifies CLAN as the analysis tool for CHAT,
  with MLU, WDLEN, MOR, and `%mor`-based morphosyntactic analysis.
- CMU Pronouncing Dictionary provides North American English word-to-ARPABET
  pronunciations; vowels carry stress markers, which makes syllable counting
  transparent.
- `syllables` is the current OOV syllable fallback. `g2p-en` is the current OOV
  phoneme fallback. Both should be reported as generated layers rather than as
  dictionary evidence.
- Phonemizer with an espeak-ng backend remains a possible sensitivity-analysis
  alternative if reviewers ask for a different G2P backend.

Useful links:

```text
https://talkbank.org/0info/manuals/CLAN.html
https://www.speech.cs.cmu.edu/cgi-bin/cmudict
https://bootphon.github.io/phonemizer/
```

See also:

```text
docs/utterance_measurement_package_writeup.md
```

This companion note explains why each package is used, what it is not used for,
and how to describe the method to reviewers.

## Levshina / Word-Level Bits Context

In this project, **context** means the preceding caretaker utterance window:

```text
context_k1
context_k2
context_k3
```

Word-level bits should be computed over the target words in the current
utterance. For a causal LLM, each target word is also conditioned on previous
target words within the same utterance, but the reported target surprisal should
not include the context tokens themselves. This means a word-level
Levshina-style table would be something like:

```text
dataset, child_id, file, line_no, utt_id, context_k, target_word_index,
target_word, word_bits, word_count, morpheme_count, syllable_count, phoneme_count
```

The context is preceding context; the complexity counts belong to the current
target word or utterance.

## 2026-06-02 Verification

Commands run:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_validate_utterance_measurement_strategies
env UV_CACHE_DIR=/tmp/uv-cache uv run python src/validate_utterance_measurement_strategies.py --sample-size 50
env UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests
```

Results:

```text
8 focused tests passed.
50 validation rows written.
153 full-suite tests passed.
```

Installed Python dependencies for this measurement layer:

```text
cmudict
pronouncing
pyphen
syllables
g2p-en
openpyxl
```

NLTK resources required by `g2p-en` were installed locally under:

```text
data/nltk_data/
```

This folder is data-like infrastructure and should be transferred with the data
bundle or regenerated, not pushed through Git.
