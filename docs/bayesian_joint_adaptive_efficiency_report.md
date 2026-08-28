# Bayesian Joint Adaptive-Efficiency Analysis

Status: **PASS**. This is a focused post-hoc
joint extension over **78 children** and
**13 corpora**. Corpus is a background hierarchical
effect, not the research question.

## Main question

Do children jointly develop (a) context-sensitive allocation of production
effort and (b) more predictable utterance forms at fixed effort?

## Posterior results

| Hypothesis | Estimand | Posterior mean [95% CrI] | P(theory direction) | P(ROPE) |
|---|---|---:|---:|---:|
| H1 | Demand-sensitive effort at 42 months | 0.006 [0.000, 0.012] | 0.972 | 0.904 |
| H2 | Developmental change in demand sensitivity | -0.002 [-0.004, 0.001] | — | 0.999 |
| H3 | Fixed-effort predictability development | -0.685 [-1.131, -0.239] | 0.997 | 0.195 |
| H4 | Coordinated child-level development | -0.005 [-0.310, 0.295] | 0.511 | 0.479 |

H2 is deliberately two-sided because the developmental reversal had already
been inspected. Its row therefore does not promote a selected sign as a new
confirmatory probability.

### Scientific reading

- **H1:** The posterior favors a positive entropy/effort association at 42
  months (`P(positive) = 0.972`), but
  `90.4%` of the posterior remains inside the declared small-effect ROPE. This is
  evidence for a modest direction, not a large effort response.
- **H2:** The age-by-entropy coefficient is close to zero, with
  `99.9%` of its posterior in the ROPE. The estimated entropy response attenuates
  with age, but this focused linear joint model does not support a practically
  large developmental change.
- **H3:** Fixed-effort contextual surprisal decreases with age
  (`P(negative) = 0.997`). This is the clearest joint-model result and describes
  growing scorer predictability/conventionality.
- **H4:** The key cross-child correlation is centered almost exactly at zero
  and has a wide interval. There is no evidence here that children with
  stronger fixed-effort predictability development also strengthen their
  demand-sensitive effort allocation.

![Population coefficient intervals](../figs/bayesian_joint_adaptive_efficiency_20260828/population_effects.png)

## Effort calibration across age

The ratio below compares the model's `log(1 + words)` prediction at the
observed all-79 response-entropy p90 versus p10. It is not the raw
negative-binomial word-count ratio from the completed GAMM analysis.

| Age | High/low entropy ratio in modeled (words + 1) | P(entropy slope > 0) |
|---:|---:|---:|
| 18 | 1.033 [1.011, 1.055] | 0.996 |
| 24 | 1.029 [1.011, 1.047] | 0.997 |
| 30 | 1.025 [1.010, 1.040] | 0.998 |
| 36 | 1.020 [1.006, 1.035] | 0.995 |
| 42 | 1.016 [0.999, 1.033] | 0.972 |
| 48 | 1.012 [0.991, 1.033] | 0.866 |
| 54 | 1.008 [0.982, 1.034] | 0.709 |
| 60 | 1.003 [0.972, 1.035] | 0.582 |

![Developmental effort calibration](../figs/bayesian_joint_adaptive_efficiency_20260828/entropy_adaptation_by_age.png)

## Coordinated development

H4 concerns the between-child correlation between the fixed-effort
predictability age slope and the developmental change in demand-sensitive
effort. A negative value is the efficiency-motivated direction because more
negative surprisal development would accompany a more positive change in the
entropy/effort relationship. Regardless of sign, this is coordinated
variation—not evidence of optimization.

| Child-level association | Correlation [95% CrI] |
|---|---:|
| Predictability development × effort at 42 months | 0.102 [-0.215, 0.404] |
| Predictability development × effort development | -0.005 [-0.310, 0.295] |
| Effort at 42 months × effort development | 0.783 [0.581, 0.909] |

The pronounced positive association is internal to the two effort
coefficients: children with a higher entropy/effort slope at 42 months also
tend to have a more positive developmental change in that slope. In contrast,
neither effort coefficient shows a clear child-level association with
fixed-effort predictability development. Intercept/slope parameterization can
affect the within-effort correlation, so the age-specific effort curves remain
the primary interpretation.

![Between-child correlations](../figs/bayesian_joint_adaptive_efficiency_20260828/between_child_correlations.png)

## Robustness and computation

- Prior sensitivity: mu_r2_entropy_42 shift 0.0001; mu_r2_age_entropy shift 0.0001; mu_r1_age shift 0.0477; rho_r1_age_entropy shift 0.0147.
- Leave-one-corpus influence: H1-H3 retained their signs under every corpus omission; H4 reversed sign in 5/13 omissions. The largest shifts by parameter were mu_r1_age 0.1517, mu_r2_entropy_42 0.0037, mu_r2_age_entropy 0.0014, rho_r1_age_entropy 0.0841.
- Total fitting runtime: 19.3 minutes.
- The model uses a three-dimensional session-clustered measurement-error
  likelihood over child coefficients; it does not run NUTS over 1.1 million
  utterance rows.

## Interpretation boundary

- This is a post-hoc joint extension; the underlying outcomes were inspected previously.
- PBM is a discovery label, not a Bayesian prior.
- Corpus is background hierarchical structure, not the scientific focus.
- Lower k3 surprisal means greater scorer predictability or conventionality, not greater Shannon information transmitted.
- Exact-string response entropy is generator-, prompt-, temperature-, and surface-form-dependent.
- The Route 2 coefficient describes log(1 + words), not listener benefit.
- Cross-child correlations indicate coordinated developmental variation, not optimization or causality.
- A strong communicative-efficiency claim remains contingent on the downstream caregiver-response utility analysis.

The next decisive test remains downstream caregiver-response predictive gain:
whether the observed child utterance improves prediction of the caregiver's
actual next response, exceeds a shuffled-child negative control, and becomes
more useful at fixed effort with age.
