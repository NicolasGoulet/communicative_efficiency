# Conversational Eligibility and Listener-Outcome Working Sample

Generated from immutable raw CHAT main-tier adjacency and the current full-79 scorer-ready child rows.

## Audit

- status: `REVIEW`
- child rows: `1,140,218`
- raw CHAT files: `2,752`
- raw-line alignments: `1,140,218`
- unresolved raw rows: `0`
- primary immediate-caregiver response rows: `629,334` (55.2%)
- rows with an immediate next caregiver response: `614,908` (53.9%)
- manual validation rows: `325`

## Interpretation Boundary

The primary eligibility flag is structural: a nonempty child main tier immediately follows an allowed caregiver main tier in the same raw CHAT file, and the scorer's k1 caregiver context is nonempty. It does not assume that the child turn is semantically contingent.

Imitation, routines/reading, backchannels, repair/clarification, acknowledgement, and question-type columns are named candidates because they are rule-based screening labels. The stratified manual-review CSV must be coded before any of these becomes an exclusion or listener-utility outcome.

The immediate next-caregiver text enables a downstream predictive-gain prototype without calling caregiver input an adult endpoint. No predictive model is fit by this builder.
