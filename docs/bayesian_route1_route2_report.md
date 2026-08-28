# Bayesian Route 1 / Route 2 program: audited pilot handoff

Status: **PILOT STOP — production not run**

This is a post-hoc Bayesian robustness and extension program over the preserved
PBM-discovery, non-PBM-replication, and all-79 descriptive scopes. Existing
outcomes had already been inspected. The seven real-data fits reported here
are computational/likelihood pilots, not scientific posterior results.

## Outcome

The frozen gate returned `STOP_UNSAFE`. No production posterior,
language-model scoring, Mila job, alternative aggregation, or changed estimand
was launched.

- total_projected_cpu_hours=8312.046 exceeds 2000.0

The complete 189-fit suite projects to
**8312.0 CPU-hours**
against the frozen 2,000-hour ceiling. Maximum projected single-fit wall time
is 33.5 hours;
peak memory is 2.8
GB; total posterior output is 84.8 GB.

## Immutable data and synthetic gates

- Route 1 child utterances: 1,140,695; paired k0-k3 long rows: 4,562,780.
- Route 1 audited condition cells: 118,380; cell counts sum exactly to 4,562,780.
- Route 2 eligible observed utterances: 1,122,396; children: 79; corpora: 13.
- Literal effort-rank endpoints: 145,618 zero and 127,565 one; maximum rank200 error 1.42e-14.
- Synthetic posterior fits: 6/6; deterministic and posterior recovery gates: PASS.

## Representative real-data pilot diagnostics

| Fit | Seconds | max R-hat | min bulk ESS | divergences | peak RSS GB |
|---|---:|---:|---:|---:|---:|
| B1_pilot | 87.7 | 1.033 | 93.4 | 0 | 0.46 |
| B2_pilot | 79.2 | 1.032 | 93.5 | 0 | 0.49 |
| B3_primary_pilot | 86.4 | 1.038 | 93.2 | 0 | 0.50 |
| B3_qwen_adjusted_pilot | 82.1 | 1.023 | 135.4 | 0 | 0.51 |
| B4_beta_binomial_pilot | 79.8 | 1.063 | 29.1 | 0 | 0.51 |
| B4_zoib_pilot | 115.0 | 1.038 | 121.3 | 0 | 0.51 |
| B5_pilot | 6.9 | 1.047 | 81.1 | 0 | 0.51 |

All seven representative pilot fits produced zero divergent transitions. The STOP is imposed by the frozen resource gate, and no pilot coefficient is licensed for scientific interpretation.

## Registered production projection

| Family | Fits | CPU-hours | max wall-hours | output GB |
|---|---:|---:|---:|---:|
| B1 | 27 | 446.0 | 7.3 | 3.9 |
| B2 | 27 | 1421.9 | 23.3 | 8.9 |
| B3 | 54 | 2987.6 | 25.1 | 28.2 |
| B4 | 54 | 3455.2 | 33.5 | 43.4 |
| B5 | 27 | 1.4 | 0.0 | 0.4 |

The registry is unchanged across `pbm_discovery`, `non_pbm_replication`, and
`all79_descriptive`, three age shapes, and weak/skeptical/wide prior sets.
The STOP cannot be bypassed by silently changing the likelihood, raw-row unit,
sample role, or Qwen adjustment.

## Scientific interpretation boundaries

- Lower surprisal means greater scorer predictability or conventionality, not greater Shannon information transmitted.
- Raw child effort and Qwen-relative effort are distinct estimands.
- Qwen responses are not meaning-preserving alternatives.
- Exact-string response entropy is model-, prompt-, and temperature-dependent.
- Cross-child slope correlation is coordinated development, not optimization or causality.
- This is a post-hoc Bayesian extension with a preserved split, not a prospective confirmation.

## Reproducibility state

- Branch: `agent/bayesian-route1-route2-v1`; report-build HEAD: `f52a7f102dd87a6a566ef72bbf24519efda16202`.
- Frozen starting SHA: `f52a7f102dd87a6a566ef72bbf24519efda16202`.
- Backend: repository-local brms 2.23.0, cmdstanr 0.9.0, CmdStan 2.39.0.
- Source paper SHA-256: `cecf8f0e696c3b95a3b4033352e484e3c0b863560959c793e8d67ebd957f1957`.
- Production completion marker: deliberately absent.

The next safe step is scientific/computational review of the 189-fit CPU plan
and compilation/execution strategy. Resuming production requires a new
explicitly reviewed gate; it is not an automatic controller action.
