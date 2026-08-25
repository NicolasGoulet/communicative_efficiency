# PBM-Excluded Transformer Training Expansion

Last verified: 2026-08-25.

## Purpose

This handoff prepares naturalistic caregiver-child speech for the proposed
BabyLlama-style causal model and T5-style encoder-decoder model. Both
architectures receive exactly the same examples. The model comparison must
therefore reflect architecture and training, not different corpus selections
or context construction.

Brown, Manchester, and Providence (PBM; 21 children) are never training data.
They are an untouched evaluation sample used to generate and score model
responses to the same PBM contexts. The existing 58 non-PBM children and the
six additional corpora form the intended development pool.

This is a model-training expansion, not a change to the authoritative 79-child
observational analysis sample.

## Current Status

The complete audited local handoff is:

```text
results/transformer_training_expansion/full_20260825/
```

It contains `BUILD_COMPLETE_AND_AUDITED`. All six expansion corpora are
present at their expected child counts.

| Added corpus | Intended children | Download | Stage 0 | Eligible child targets |
| --- | ---: | --- | --- | ---: |
| Tardif | 24 | complete | complete | 2,693 |
| Valian | 21 | complete | complete | 14,135 |
| Higginson | 3 | complete | complete | 5,052 |
| Howe | 16 | complete | complete | 10,049 |
| Edinburgh | 47 | complete | complete | 2,968 |
| Thomas | 1 | complete | complete | 210,102 |

The available handoff contains:

- 763,494 training examples;
- 175,216 whole-child validation examples;
- 938,710 total non-PBM development examples for final refitting;
- 446,508 PBM evaluation examples;
- eight cumulative age-model datasets;
- zero PBM datasets in training/development files;
- zero non-PBM training datasets in PBM evaluation files;
- no missing corpus and no fatal audit issue.

The validation set is large because whole children, rather than individual
utterances, are held out and one selected MPI-EVA-Manchester child contributes
many rows. This is intentional for child-disjoint model selection. After the
architecture and hyperparameters are fixed, each final age model should be
refit using the corresponding `development.jsonl.gz`, which returns the
validation children to the non-PBM training pool before PBM generation.

## Source Data

Tardif, Valian, and Higginson came from the official TalkBank North American
MOR archive:

```text
URL: https://talkbank.org/childes/access/Eng-NA/0-Eng-NA-MOR.zip
Local: data/zip_files/0-Eng-NA-MOR.zip
Size: approximately 95 MB
SHA-256: b7ad9046e5fbab91f5aec3bd15f82c6a98ce9abf19699f8c76d84d7196d3eeb2
```

The archive passed `unzip -t`. The selected raw CHAT trees are under
`data/raw_data/{Tardif,Valian,Higginson}/`; their Stage-0 outputs are under
`data/preprocessed_data/`.

The three official authenticated UK downloads were recovered from the local
`NicolasGoulet.github.io` repository, copied into this project, verified, and
removed from the website repository. Their local source contracts are:

```text
Howe.zip       436,805 bytes     SHA-256 14e7123be595b618edc5773b310cfbdfd54c657f2c3d3791dbabc38a5c763f04
Edinburgh.zip  4,058,039 bytes   SHA-256 969aa808bc85f208d9655951807e70d9566a8e05f6621d686c5588600f996776
Thomas.zip     23,579,424 bytes  SHA-256 0b5e030b53858ef9668e22b5d949441e701206e1afdaf103c2f205142ec34ddc
```

All three passed ZIP CRC tests. The installer audit is
`results/transformer_training_expansion/installed_source_archives.csv`.

The authenticated ZIP installation and Stage-0 preparation are automated:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  src/install_childes_training_expansion_archives.py
```

The installer checks `data/zip_files/` and `/home/apaixonada/Downloads/` for
the exact filenames `Howe.zip`, `Edinburgh.zip`, and `Thomas.zip`. It verifies
ZIP CRCs, rejects unsafe paths, extracts only CHAT files, refuses to overwrite
an existing raw corpus, runs the shared preprocessor, and records source sizes
and SHA-256 values.

## Corpus-Specific Preparation

All corpora use the same Stage-0 cleaning policy as the existing CHILDES data:
per-child `chi.csv` and `caretakers.csv`, stable CHAT line provenance, cleaned
utterance text, age, session, file, speaker, and role-specific utterance IDs.

Additional layout/selection rules are implemented in
`src/prepare_datasets.py`:

- Tardif: one root CHAT file per child; exclude the book-only `e26book.cha`;
  within the other files retain only the `mechanical toys` and `regular toys`
  blocks. This is explicitly toy-play data, not a claim that every retained
  minute is unstructured conversation.
- Valian: group files such as `01a`, `01b`, and `01c` into child `01`.
- Higginson: retain the existing one-directory-per-child layout.
- Howe: group numbered sessions by filename child prefix.
- Edinburgh: group age/session filenames by child prefix.
- Edinburgh age: use the precise `@ID` age when compatible with the filename's
  9- or 15-month wave; fall back to that wave when the header is missing or
  differs by more than two months. This repairs `martin0902.cha`'s erroneous
  `0;00.03` header. The prepared age range is 9–16 months with zero missing
  ages.
- Thomas: group all root sessions as one longitudinal child.

The Howe and Edinburgh rules have unit tests but remain provisional until they
are checked against the authenticated raw filenames.

## Example Contract

Each JSONL row includes:

- `example_id`: stable hash of corpus, child, and CHAT reference line;
- `dataset`, `child_id`, `session_id`, `file`, `line_no`, and
  `reference_line`;
- exact `age_months`, floored age month, and target age bin;
- `context_turns`: up to the previous three non-empty caregiver turns in the
  same session;
- `context_text`: those turns joined with `<turn>`;
- `target_text`: the real cleaned child utterance;
- context/target word-count diagnostics;
- `split`: train, validation, or held-out PBM evaluation.

Context is capped at the most recent 60 whitespace-delimited tokens, matching
the earlier additive LSTM setup. Empty-context child targets are retained, as
they were in that setup. Model-specific tokenization is deliberately deferred:
the BabyLlama and T5 tokenizers differ, but the underlying text examples do
not.

## Age Schedule

The eight target bins reproduce the existing merged-early schedule:

```text
006-023
024-029
030-035
036-041
042-047
048-053
054-059
060-065
```

Training is cumulative. For example, the `030-035` model receives every
eligible non-PBM development example from 6 through 35 months, while PBM
generation for that model is restricted to PBM targets aged 30 through 35
months.

Available-row schedule:

| Target bin | Train | Validation | Final refit development | PBM targets |
| --- | ---: | ---: | ---: | ---: |
| 006-023 | 31,040 | 3,606 | 34,646 | 62,816 |
| 024-029 | 237,236 | 11,127 | 248,363 | 162,210 |
| 030-035 | 438,842 | 16,184 | 455,026 | 142,447 |
| 036-041 | 618,511 | 59,541 | 678,052 | 37,206 |
| 042-047 | 672,464 | 88,776 | 761,240 | 16,345 |
| 048-053 | 730,474 | 127,066 | 857,540 | 12,909 |
| 054-059 | 762,202 | 153,562 | 915,764 | 10,033 |
| 060-065 | 763,494 | 175,216 | 938,710 | 2,542 |

The final three bins have relatively few PBM targets, especially 60–65. That
is a precision limitation and should not be hidden by pooling age bins after
results are inspected.

## File Map

```text
manifest.json
dataset_audit.csv
age_model_schedule.csv
validation_children.csv
BUILD_COMPLETE_AND_AUDITED

examples/
  train_all_ages.jsonl.gz
  validation_all_ages.jsonl.gz
  development_all_ages.jsonl.gz
  pbm_evaluation_all_ages.jsonl.gz

cumulative_age_models/through_<END>_months/
  train.jsonl.gz
  validation.jsonl.gz
  development.jsonl.gz

pbm_target_age_bins/
  pbm_<START>-<END>.jsonl.gz
```

`manifest.json` records every compressed-file SHA-256. All current gzip files
passed decompression integrity checks. Future builds use a zero timestamp in
the gzip header so identical source data and configuration produce identical
compressed payload hashes.

## Correct Training Use

For either BabyLlama or T5:

1. Select architecture and hyperparameters using only `train` and
   `validation` for each cumulative cutoff.
2. Freeze those choices without examining PBM generation/scoring results.
3. Refit the final model on `development.jsonl.gz` for that cutoff.
4. Generate responses only for the matching `pbm_<BIN>.jsonl.gz` targets.
5. Preserve unconstrained-length output for the effort-adaptation question;
   a separate same-length generation may be produced only for the
   fixed-effort information question.
6. Score real and generated targets with the same downstream scorers and keep
   raw bits separated by scorer/tokenizer.

There are eight age models per architecture, not 24 training folds. PBM's
three corpora are evaluation strata, not three opportunities to retrain on the
other two PBM corpora. Training on any PBM corpus would violate the stated
generalization test.

## Reproduction

The frozen selection and source contract is:

```text
configs/transformer_training_expansion.json
```

Run the preprocessing tests:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest \
  tests.test_build_transformer_training_expansion \
  tests.test_install_childes_training_expansion_archives \
  tests.test_preprocessing \
  tests.test_cleaning
```

After all six expansion corpora have Stage-0 outputs, create a new complete
handoff:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  src/build_transformer_training_expansion.py \
  --output-dir results/transformer_training_expansion/full_<DATE>
```

The builder writes `BUILD_COMPLETE_AND_AUDITED` only when all six added corpora
are present at their expected child counts and no fatal audit problem exists.
