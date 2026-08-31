# Bidirectional Dyadic Communicative-Efficiency Analysis

Status: **core analysis complete and audited**. The listener-utility and manually
validated response-function extensions remain gated; they are not silently
treated as null results.

## Scientific question

For the ordered sequence `caregiver A_t → child C_t → caregiver A_t+1`, do
momentary changes in scorer predictability and production effort propagate in
both directions, and does that coupling change with child age?

The strict analysis contains **413,084** exact caregiver-child-caregiver triads
from 79 children and 13 corpora. Every child, preceding-caregiver, and
responding-caregiver score joined one-to-one with an exact text-hash match.

## Main result

The strongest result is an **age-dependent reversal in effort coupling**.
Around 24 months, a one-SD increase in the preceding speaker's within-session
contextual surprisal is followed by slightly longer next turns. From roughly
36 months onward, higher surprisal is instead followed by shorter child and
caregiver turns. The other-58 confirmation sample passes the frozen
two-adjacent-age simultaneous-band rule for F2 and F3, but not for F1.

| Family | Age | Estimate [simultaneous 95% interval] | Excludes null? |
|---|---:|---:|---:|
| F1 | 24 | 0.062 [-0.071, 0.195] | no |
| F1 | 36 | -0.007 [-0.111, 0.097] | no |
| F1 | 42 | -0.095 [-0.227, 0.037] | no |
| F1 | 60 | -0.083 [-0.245, 0.080] | no |
| F2 | 24 | 1.037 [1.018, 1.056] | yes |
| F2 | 36 | 0.971 [0.959, 0.984] | yes |
| F2 | 42 | 0.949 [0.932, 0.966] | yes |
| F2 | 60 | 0.941 [0.920, 0.962] | yes |
| F3 | 24 | 1.040 [1.023, 1.057] | yes |
| F3 | 36 | 0.968 [0.956, 0.979] | yes |
| F3 | 42 | 0.964 [0.950, 0.979] | yes |
| F3 | 60 | 0.923 [0.903, 0.944] | yes |

F1 is measured in child k3 bits per one within-session SD of caregiver k3,
with child effort controlled. F2 and F3 are incidence-rate ratios. Thus F3's
estimate of 0.964
at 42 months corresponds to about a
3.6%
shorter modeled caregiver response per child-k3 SD, conditional on the frozen
controls. This is an observational within-session association, not a causal
effect.

![Primary coupling curves](../figs/bidirectional_dyadic_efficiency_20260829/primary_bidirectional_coupling.png)

## Bayesian joint synthesis

The bounded Bayesian model uses 75 children with at least 30 triads and six
sessions, propagating the shared session-clustered covariance of three
child-level standardized coefficients. Four exclusions were determined by the
pre-fit support rule. All final fits had zero divergences and zero treedepth
saturation; total compute, including diagnostic repairs, was
**0.80 CPU-hours**.

| ID | Estimand | Posterior mean [95% CrI] | P(positive) | P(ROPE) |
|---|---|---:|---:|---:|
| D1 | Adult-to-child fixed-effort predictability | 0.001 [-0.015, 0.020] | 0.515 | 1.000 |
| D1b | Adult-to-child effort coupling at 42 months | -0.035 [-0.073, 0.003] | 0.035 | 0.797 |
| D2 | Child-to-caregiver response-effort coupling at 42 months | -0.069 [-0.124, -0.012] | 0.009 | 0.224 |
| D5a | Correlation: adult-to-child k3 and effort | -0.162 [-0.559, 0.280] | 0.240 | 0.253 |
| D5b | Correlation: adult-to-child k3 and child-to-caregiver effort | -0.598 [-0.830, -0.271] | 0.001 | 0.004 |
| D5c | Correlation: reciprocal effort couplings | 0.483 [0.120, 0.759] | 0.995 | 0.020 |

At 42 months, adult-to-child fixed-effort predictability coupling is essentially
zero. Adult-to-child effort shortening is small and uncertain. Child-to-
caregiver effort shortening is supported. The reciprocal effort slopes
correlate positively across children/dyads, but this heterogeneity result is
descriptive and somewhat corpus-sensitive; it remains positive in every
leave-one-corpus refit.

![Bayesian synthesis](../figs/bidirectional_dyadic_efficiency_20260829/bayesian_bidirectional_synthesis.png)

## Decomposition and robustness

The pooled 42-month decomposition keeps k0, k3, and context support separate.
It finds positive same-component coupling for unconditional form surprisal and
context support in F1, while the net k3 fixed-effort coupling is near zero.
Effort shortening appears in the k0 and context-support variants as well. These
standardized variants are not algebraically subtractable.

![Score decomposition](../figs/bidirectional_dyadic_efficiency_20260829/decomposition_at_42_months.png)

The robustness package passed **99.0%**
minimum corpus-stratified whole-child bootstrap completion, 13 leave-one-corpus
checks per family, age equalization, 200 session-level and row-level age
scrambles, and 200 within-session turn shuffles. All nine permutation tests had
`p = 0.0050`. The binned bootstrap independently
confirmed F2 and F3 but not F1.

The metadata-validated parent sensitivity retains 412,667 adult-to-child and
412,657 child-to-adult rows. Its largest departure from the caregiver curves is
only **0.0011**, so the substantive result is unchanged when
the relevant adult turn is explicitly a mother or father.

## What this means for communicative efficiency

The evidence supports reciprocal, developmentally changing **effort
adaptation**. It does not yet show that shorter responses preserve meaning or
improve listener success. The reversal is compatible with increasing ability
to resolve or respond economically to locally unusual speech, but competing
accounts include turn function, discourse structure, transcription, and
scorer representation.

Two stronger layers remain unavailable:

- **Downstream predictive utility:** `WAITING_FOR_AUDITED_SCORES`.
  No score archive may be joined until all five conditions for each scorer pass
  independent relocation audit.
- **Validated response function:** `WAITING_FOR_VALIDATED_325_ROW_LABELS`.
  The 325-row sample exists, but zero rows currently contain a manual label.

Therefore this report does not claim causal optimization, preserved utility,
or semantic efficiency.

## Reproducibility

The frozen contract is
`configs/bidirectional_dyadic_efficiency_20260829/analysis_contract.json`.
The staged products and hash manifests are under
`results/bidirectional_dyadic_efficiency_20260829/`. The core program contains
15 frequentist fits, three parent-only sensitivities, a 200-replicate
robustness package, and 15 final Bayesian fits after five diagnostic-only
repairs.
