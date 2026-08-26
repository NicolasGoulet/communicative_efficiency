# Prompt: Start PBM-Held-Out T5 and BabyLlama-Sized LLaMA Generation

Copy the text below into a fresh Codex task started for
`generate_baselines_mila`.

```text
Work in the existing dedicated worktree:

/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/.worktrees/generate-pbm-transformers

Expected branch: codex/pbm-transformer-generators
Expected starting commit: a455000568f70506d4501d62f32c7c3a24e6fd53

Goal

Execute the frozen PBM-held-out small-transformer generation experiment on
Mila for both architectures. The implementation already exists; do not redesign
the experiment unless validation exposes a concrete defect.

Use $rsync-mila, $smoke-test-mila-jobs, and $submit-mila-slurm-jobs. Read every
applicable SKILL.md before taking cluster actions. Also read, in this order:

1. docs/pbm-transformer-pipeline.md
2. configs/pbm_transformers_from_scratch_v1.json
3. README.md
4. slurm/submit_pbm_transformers.sh
5. slurm/run_pbm_transformer_cell.sbatch
6. tests/test_pbm_transformer_production.py

Frozen scientific design

- Train both models from scratch with no pretrained checkpoint and no teacher
  distillation:
  - babyllama_sized_llama_58m: decoder-only LLaMA, 58,343,936 parameters;
  - t5_58m: encoder-decoder T5, 58,540,544 parameters.
- Call the first model “BabyLlama-sized LLaMA trained from scratch,” not a
  BabyLlama replication.
- Use the same 16k byte-level BPE tokenizer trained only on non-PBM training
  data.
- Brown, Manchester, and Providence must never enter tokenizer training,
  training, validation, or epoch selection. They are evaluation only.
- Use eight cumulative age cutoffs. This is 2 architectures x 8 cutoffs = 16
  final models, not 24 models and not PBM cross-validation folds.
- Select the epoch using the whole-child-disjoint validation split, then start
  again from fresh random initialization and refit for that epoch count on
  development = train + validation. Only the refitted model generates PBM.
- Generate one unconstrained-length stochastic response per matching PBM
  target with temperature 1, top-p 1, and max_new_tokens 128.
- The token ceiling is only a safety bound. The final censored fraction must be
  <= 0.1%; otherwise fail the run and version a corrected rerun rather than
  interpreting truncated lengths.
- Do not generate 100 responses per context. Qwen full100 remains the response
  cloud; these are architecture baselines.

Authoritative input

/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency/results/transformer_training_expansion/full_20260825

It must contain BUILD_COMPLETE_AND_AUDITED. Rehash and verify its manifest
before transfer and again on Mila. Expected counts are 763,494 training,
175,216 whole-child-disjoint validation, 938,710 development, and 446,508 PBM
evaluation examples, with zero PBM overlap in learning inputs.

Execution contract

1. Verify the worktree is clean, on the expected branch/commit, and synchronized
   with its upstream. Preserve unrelated work and never force-push.
2. Run the full local unit suite, shell syntax checks, git diff --check, the
   fake-sbatch DAG test, and the Slurm resource validator. Fix defects with
   focused tests before changing production code; commit and push reviewed
   fixes on this feature branch.
3. Transfer only the required code and immutable input handoff to Mila using
   rsync. Do not use Git for data. Rehash the transferred handoff.
4. Create or verify the dedicated frozen Mila runtime outside the run root.
   A login-node import test is not a GPU smoke.
5. Use the exact production wrapper for a representative two-task GPU smoke:
   one BabyLlama-sized LLaMA task and one T5 task, with production dimensions,
   1,024 training examples, and 25 PBM targets. Validate finite training loss,
   checkpoint/resume artifacts, generation schema and row identity, nonblank
   output, EOS/censoring fields, CUDA use, and both architecture labels.
6. I authorize submission of the existing exact smoke-gated production DAG.
   Production tasks must remain afterok-dependent on the passing smoke audit;
   each array element must use --ntasks=1 and exactly one GPU request family.
   Do not bypass the smoke, wave audits, fresh-run-root rule, or censoring gate.
7. Monitor the DAG through SMOKE_PASSED, WAVE1_READY, WAVE2_READY,
   COMPLETE_AND_AUDITED, and FINAL_REPORT_READY. Diagnose failures from logs and
   resume only through the implemented audited mechanism; do not create an
   ad-hoc alternative run.
8. Retrieve the compact reports, manifests, final markers, and
   handoff/pbm_transformer_responses_scorer_ready.csv.gz. Independently verify
   hashes, 16 completed cells, all 446,508 PBM response rows, architecture and
   age-bin coverage, zero PBM learning leakage, blank/failure counts, and the
   censoring threshold.
9. Stop after the audited generation handoff. Do not start Mistral scoring;
   that belongs to the separate compute_surprisal_mila workflow and requires
   its own exact-wrapper smoke and explicit handoff.

Do not silently change architecture dimensions, tokenizer scope, data splits,
age schedule, seed, batch/optimization defaults, decoding settings, or sample
count. If the frozen run is infeasible, report the measured failure and propose
the smallest versioned correction before changing it.

Success means either:

- the full gated generation DAG finishes and the locally retrieved handoff
  independently passes every audit; or
- the DAG is safely running/queued behind passing dependencies, in which case
  report the exact run root, commit, job IDs, completed markers, current Slurm
  states, resource configuration, log paths, and the next audit boundary.

In the final response, lead with actual status. Include exact tests, commit and
remote branch, Mila run root, all job IDs/states, markers reached, output paths
and hashes, deviations from the frozen contract, and blockers. Do not claim
training, generation, or completion from submission alone.
```
