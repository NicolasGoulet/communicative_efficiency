# Roadmap

Phased checklist for building the project. Use `TODO.md` for the lower-level
working queue.

## Phase 1: Project Context

- [x] Create `AGENTS.md`.
- [x] Create `TODO.md`.
- [x] Create design and guideline skeletons.
- [ ] Fill in project definitions and human decisions.
- [ ] Review context files for contradictions.

## Phase 2: Data Layout Documentation

- [ ] Document raw data locations.
- [ ] Document preprocessed data locations.
- [ ] Document expected per-child output files.
- [ ] Document immutable data policy.

## Phase 3: Preprocessing Validation

- [ ] Confirm canonical cleaning rules.
- [ ] Add editable examples for CHAT marker handling.
- [ ] Validate session age handling.
- [ ] Validate caretaker merging behavior.
- [ ] Decide and test empty-utterance policy.

## Phase 4: Vocabulary And Baselines

- [ ] Confirm dictionary file naming conventions.
- [ ] Validate unigram vocabulary building.
- [ ] Validate bigram probability building or loading.
- [ ] Validate random/unigram/bigram generated utterance columns.

## Phase 5: No-Context Scoring

- [ ] Define scoring output schema.
- [ ] Implement or validate no-context target-only scoring.
- [ ] Add tests or small fixtures.
- [ ] Save run metadata with outputs.

## Phase 6: Caretaker-Context Scoring

- [ ] Define context construction rules.
- [ ] Validate target-token masking.
- [ ] Support chosen context sizes.
- [ ] Add checks that context tokens are not scored as targets.

## Phase 7: Aggregation And Plots

- [ ] Document plot input schemas.
- [ ] Identify current output folders.
- [ ] Add validation checks for empty / invalid rows.
- [ ] Regenerate selected plots.

## Phase 8: Analysis And Reporting

- [ ] Decide main analysis tables.
- [ ] Decide figure set.
- [ ] Record reproducible commands.
- [ ] Write interpretation notes.
