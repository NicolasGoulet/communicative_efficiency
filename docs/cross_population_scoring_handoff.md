# Cross-population scoring handoff

Status: **locally complete and audited; Mila scoring not submitted** (2026-08-26).

## What is ready

| Design | Source folders | Scoreable children | Child targets | Setting |
| --- | ---: | ---: | ---: | --- |
| Strict naturalistic 79 | 79 | 79 | 1,140,696 | longitudinal caregiver-child |
| Training expansion | 112 | 112 | 244,999 | naturalistic/play-based caregiver-child |
| Champaign/EHS | 170 | 168 | 152,279 | structured observation |
| Clinical/matched controls | 494 | 481 | 215,820 | clinical/control protocols |
| Hall snapshot | 37 | 37 | 71,830 | home/school/transition |
| **Total** | **892** | **877** | **1,825,624** | separate designs |

The 15 source folders without scoreable child targets are explicitly recorded:
13 clinical/control folders and two EHS folders. Hall has 70,510 primary rows;
the 71,830-row total is its 37-child sensitivity panel.

The strict-naturalistic count includes the literal Forrester child utterance
`nan`. Earlier pandas loading treated that lexical form as missing, explaining
the one-row difference from the 1,140,695-row direct-Mistral table. The new
scorer loader preserves it as speech.

## Clinical children

The 15 groups are Ambrose HL/TD, Cummings PD, Feldman SLI/TD, Flusberg DS,
Hooshyar DS/TD, Nicholas HL/TD, Rescorla LT/TD, Rondal DS/TD, and UCSD SLI.
Primary within-source comparisons are available for Ambrose, Feldman,
Hooshyar, Nicholas, Rescorla, and Rondal. Cummings PD, Flusberg DS, and UCSD
SLI do not have a matched control group in the same source.
Cummings PD and UCSD SLI have no local caregiver tiers, so all of their k1–k3
rows are explicitly context-unavailable; only k0 can be scored for those groups.

## Frozen scoring contract

- Models: Mistral-7B-v0.3, TinyDialogues, and Qwen3-14B, kept separate.
- Targets: real child utterances.
- Contexts: k0, k1, k2, and k3; unavailable context remains unavailable.
- Products: same-pass utterance, word, token, and token-to-word allocation.
- Reuse: PBM three-scorer word products and Hall Mistral.
- Pending: 101 model-by-dataset cells = 404 dataset-context contracts in 14
  group/model runs.

All 14 local CPU preparations and all 404 frozen pending contracts passed. GPU
smoke and model scoring remain intentionally unrun until the Mila handoff.

Archive:
`results/cross_population_scoring_handoff/cross_population_child_scoring_20260826_v1.tar.gz`

SHA-256:
`e441d48f14c568b7cabd97aac1389bdfb15d1916ba144afc924adaf24d9baf28`

The compute implementation and one-OTP commands are in the sibling compute
repository at `docs/cross_population_word_surprisal_runbook_2026-08-26.md`.
