# Complete Analysis Machine

`src/build_complete_analysis_machine.py` is the project-level controller for
the paper's reusable analysis families. It does not combine every outcome into
one regression. It sequences the existing, scientifically distinct pipelines
and records one command manifest per component and phase.

## Scientific registry

The machine-readable registry is
`configs/complete_analysis_machine_v1.json`. It currently covers:

- direct TinyDialogues PBM utterance surprisal;
- direct Mistral PBM/non-PBM utterance surprisal;
- exact paired TinyDialogues-versus-Mistral robustness;
- the Route 1 model atlas;
- Route 2 raw response-space and generated-relative effort models;
- corrected cross-fitted PBM Bayes decomposition;
- the frozen sustained-onset analysis;
- separate Mistral, Qwen3-14B, and TinyDialogues PBM word pipelines;
- the explicitly blocked non-PBM58 Mistral word confirmation.

PBM discovery, non-PBM confirmation, and scorer robustness remain separate.
The machine never pools raw surprisal magnitudes across tokenizers.

## Phases

```text
prepare -> fit -> plots -> reports -> synthesis
```

Each phase runs commands sequentially without a shell. A phase is reused only
when its component configuration, command list, completion manifest, and
declared output artifact hashes still agree. Downstream phases require PASS
manifests from every applicable upstream phase. Readiness is refreshed after
each component, which allows a cross-scorer report to unlock only after all
three scorer audits finish in the same report phase. Logs are written under the ignored
`results/complete_analysis_machine_v1/` directory.

The word pipelines add a stronger scientific gate: real effect fitting and
outcome plotting require a checksummed frozen protocol. Input inventory,
exact occurrence pairing, lexical eligibility, support coverage, and feature
construction can run before the freeze because those stages do not summarize
developmental outcomes. Each scorer's report phase ends with `audit-all` and
must publish `COMPLETE_AND_AUDITED`; the three-scorer synthesis additionally
requires one registry hash and one exact supported-occurrence identity hash.

## Commands

Inspect readiness without running analyses:

```bash
.venv/bin/python src/build_complete_analysis_machine.py --stage preflight
```

Run a bounded component selection:

```bash
.venv/bin/python src/build_complete_analysis_machine.py \
  --stage fit \
  --components direct_tinydialogues_pbm,paired_direct_tiny_mistral
```

Run all currently eligible phases and build the artifact index:

```bash
.venv/bin/python src/build_complete_analysis_machine.py --stage all
```

The intentionally blocked non-PBM58 word component remains visible in the
preflight and synthesis reports until its same-pass Mistral production exists.
This is an audit result, not a reason to pool the full-79 utterance tree into a
word-level confirmation.

## Legacy monolithic components

The direct and paired pipelines already expose independent model, plot, and
report stages. The Route 1 model-atlas command separates saved-sample fitting
from report rendering. The two Route 2 scripts still fit, plot, and report in a
single historical call; the controller labels those products as a single fit
phase and audits their table and report artifacts. Their estimands remain
separate even though their implementation predates the phase controller.

## Failure policy

- Missing inputs are `BLOCKED_PREFLIGHT` and are never invented.
- A nonzero command exit is `FAILED` and stops later commands for that
  component/phase.
- A successful command with missing declared outputs is
  `FAILED_ARTIFACT_AUDIT`.
- Other ready components continue, so one unavailable sensitivity does not
  erase completed analyses.
- Synthesis is `REVIEW`, never `PASS`, while any registered component is
  blocked or failed. It lists blockers and reports; it does not rewrite a null
  or contrary result as support.
