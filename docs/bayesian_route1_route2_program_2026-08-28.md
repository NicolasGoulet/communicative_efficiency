# Bayesian Route 1 / Route 2 Analysis Program

Status: **design proposal only**, reviewed 2026-08-28. No Bayesian model in
this document has been fitted and no result may be inferred from the proposed
direction. Existing frequentist results have already been inspected, so this
program is a post-hoc robustness and extension program, not a new
outcome-blind preregistration.

## Source paper and methodological translation

The immediate methodological source is Natalia Levshina, *A Bayesian dawn in
linguistics: Trends, benefits and good practices*, local PDF:

```text
/home/apaixonada/Downloads/2509.17161v1.pdf
SHA-256 cecf8f0e696c3b95a3b4033352e484e3c0b863560959c793e8d67ebd957f1957
```

The paper is a review of Bayesian statistics in linguistics, not a theory of
child communicative efficiency. Its relevant contributions here are:

- partial pooling for complex child/corpus random-effects structures;
- direct posterior statements about effect magnitude and direction;
- appropriate likelihoods for counts, bounded outcomes, and endpoint masses;
- shrinkage and explicit propagation of model uncertainty;
- Bayesian hierarchical synthesis across heterogeneous units;
- mandatory prior predictive checks, prior sensitivity, convergence checks,
  posterior predictive checks, and cautious use of Bayes factors.

The project should not adopt Bayesian estimation merely to replace a
frequentist interval with a credible interval. Each proposed model below uses
Bayesian machinery to answer a question that the existing model suite does not
answer cleanly.

## Scientific boundaries

Route 1 and Route 2 remain distinct:

1. **Route 1:** how scorer-indexed utterance predictability changes with age
   at fixed measured production effort.
2. **Route 2:** how child production effort adapts to conversational demand
   and to the generated response distribution for the same context.

Lower surprisal alone is predictability/conventionality, not communicative
efficiency. Shorter speech alone is not efficiency. The joint program may
describe coordinated developmental change in predictability and effort, but
it must not claim a meaning-preserving optimum.

The frozen sample roles remain:

```text
PBM discovery: Brown, Manchester, Providence — 21 children
non-PBM replication: the other 10 strict-naturalistic corpora — 58 children
all-79 descriptive: all 13 corpora — 79 children
```

Because the non-PBM outcomes have already been inspected in earlier analyses,
the term `replication` in this new program describes a preserved sample split,
not a pristine prospective confirmation.

Hall, structured recordings, and clinical/control datasets are outside this
first Bayesian program. The downstream caregiver-response scores currently
running on Mila are also outside Phase 1 and may enter only after their
archives and local relocation audits pass.

## Authoritative existing inputs

No new language-model scoring is required for the five priority analyses.

Route 1:

```text
results/direct_surprisal_replication/mistral_full79/
  child_direct_surprisal_wide.csv.gz
results/direct_surprisal_replication/mistral_full79/modular/prepared/
  trajectory_input.csv.gz
```

Route 2 and joint response clouds:

```text
results/full79_joint_efficiency_analysis/metrics/
  model_rows.parquet
  child_age_metric_cells.parquet
  observed_cloud_metrics.parquet
```

Existing frequentist comparators:

```text
results/direct_surprisal_replication/mistral_full79/modular/models/
results/full79_joint_efficiency_analysis/models/
```

The Route 2 table has 1,122,396 eligible observed utterances, 79 children, 13
corpora, and a 100-response Qwen reference for each included context. Its
effort percentile has genuine endpoint mass: 145,618 rows at zero and 127,565
at one. Every percentile multiplied by 200 is integer-valued to floating-point
tolerance, reflecting the frozen midrank construction over 100 responses.

## Larger candidate inventory

The candidate pool is deliberately broader than the first implementation:

| Rank | ID | Candidate analysis | Status |
|---:|---|---|---|
| 1 | B1 | Joint k0-k3 context-depth Route 1 model | Phase 1 |
| 2 | B5 | Joint child-level Route 1/Route 2 developmental slopes | Phase 1 |
| 3 | B3 | Raw Route 2 effort-adaptation model | Phase 1 |
| 4 | B4 | Empirical Qwen-rank model with endpoint-aware likelihood | Phase 1 |
| 5 | B2 | Route 1 location-scale conventionalization model | Phase 1 |
| 6 | B6 | Exact-length child-minus-Qwen k3 gap model | Backlog |
| 7 | B7 | PBM-to-non-PBM posterior predictive transport | Validation layer |
| 8 | B8 | Linear/quadratic/smooth age model stacking | Validation layer |
| 9 | B9 | PBM paired-scorer hierarchical synthesis | Backlog |
| 10 | B10 | Child-versus-caregiver multivariate trajectory model | Backlog |
| 11 | B11 | Corpus-level heterogeneity/meta-analytic model | Backlog |
| 12 | B12 | Downstream caregiver utility at fixed effort | Await audited scores |

Only B1-B5 should be implemented in the first lane. B7 and B8 are required
validation procedures for those models, not excuses to expand the primary
model count after inspecting results.

## The five priority models

### B1 — Joint context-depth Route 1 model

**Question.** Does development change unconditional predictability, proximal
context support, and longer-context support differently at fixed word effort?

Create a paired long table from the same observed child utterances at `k0`,
`k1`, `k2`, and `k3`. The primary complete-case table requires all four
scores. Aggregate only for computational tractability to
child × session × exact/top-coded word count × context condition, retaining
the cell mean, SD, count, and standard error.

Use a robust hierarchical measurement-error likelihood:

```text
mean_bits[j,k] ~ Student-t(nu, mu[j,k], sqrt(se[j,k]^2 + sigma[k]^2))

mu[j,k] = alpha[k]
        + f[k](age_months)
        + beta[k, word_count_top12]
        + child_intercept[child,k]
        + child_age_slope[child,k] * age
        + corpus_intercept[corpus,k]
```

Condition-specific child effects are correlated and regularized. Derive from
the joint posterior rather than refitting separate gain outcomes:

```text
k0 - k1
k1 - k2
k2 - k3
k0 - k3
```

Primary outputs are age derivatives and supported-age contrasts for each
condition and each incremental gain. This directly tests whether the existing
negative total `k0-k3` developmental result reflects less unconditional
rarity, less immediate-context dependence, or saturation before three turns.

### B2 — Route 1 location-scale conventionalization model

**Question.** At fixed effort, do older children become only more predictable
on average, or also more consistently predictable?

Use contextual `k3` total surprisal with a robust distributional model:

```text
k3_bits ~ Student-t(nu, mu, sigma)

mu       = f(age, word_count_top12) + child/corpus effects
log sigma = g(age) + word_count_top12 + child/corpus effects
```

The primary mean estimand remains the Route 1 fixed-effort age trajectory.
The new estimand is the posterior age change in residual dispersion at common
1-4-word effort levels. A negative dispersion change means greater consistency
under the scorer; it is not automatically greater communicative efficiency.
Do not use bits per tokenizer token as the primary outcome.

### B3 — Bayesian raw-effort Route 2 response surface

**Question.** How does child word effort adapt to response-space uncertainty
over development, without conditioning automatically on Qwen expected length?

The preferred raw-row likelihood is negative binomial:

```text
child_words ~ NegBinomial(mu, shape)

log mu = f(age)
       + f(response_entropy)
       + ti(age, response_entropy)
       + f(context_word_count)
       + child random intercept
       + child random age slope
       + child random entropy slope
       + corpus random intercept
```

This is the Bayesian analogue of the frozen M1 total-association model. A
separate sensitivity adds `f(qwen_mean_word_count)` and must retain a distinct
estimand. The final model may not silently condition on generated expected
effort.

Because 1.12 million rows may make full NUTS impractical, implementation must
benchmark the exact raw-row formula on a deterministic representative pilot.
If a final raw-row fit is infeasible, stop and document the projection before
changing the likelihood or unit. A cell-level measurement-error alternative
may be proposed, but it is a different estimand and requires explicit review.

### B4 — Endpoint-aware generated-relative effort model

**Question.** Where does the child fall in the 100-response Qwen effort
distribution, and how does that position change with age and response-space
uncertainty?

The primary outcome is the frozen empirical midrank. Since
`200 * effort_percentile_in_qwen` is integer-valued, first test a
beta-binomial rank likelihood:

```text
rank200 ~ BetaBinomial(trials=200, mu, phi)

logit mu = f(age)
         + f(response_entropy)
         + ti(age, response_entropy)
         + f(context_word_count)
         + child random intercept/slopes
         + corpus random intercept
```

This retains exact zero and one ranks and represents uncertainty in the finite
generated reference more honestly than forcing ranks into `(0,1)`. The paper's
zero-one-inflated beta model is the registered sensitivity; it separately
models endpoint probability, upper-versus-lower endpoint probability, and the
interior beta mean. Compare calibration and posterior predictive performance,
not p-value-like thresholds.

### B5 — Joint child-level information-effort development

**Question.** Do children who become more predictable at fixed effort also
show stronger adaptation of effort to contextual demand?

Avoid a noisy information/effort ratio. Estimate child-level Route 1 and Route
2 developmental coefficients with uncertainty, then synthesize them in a
bivariate hierarchical measurement-error model:

```text
[estimated_R1_age_slope, estimated_R2_age_or_age_x_entropy_slope]_child
    ~ MVN([latent_R1_slope, latent_R2_slope]_child,
          known_or_bootstrapped_estimation_covariance_child)

[latent_R1_slope, latent_R2_slope]_child
    ~ MVN(corpus-level mean, Sigma_between_children)
```

The primary new estimand is the posterior distribution of the between-child
correlation in developmental slopes, plus the population mean vector. Report
how much the correlation changes under leave-one-child and leave-one-corpus
analyses. This tests coordinated development while preserving the distinct
Route 1 and Route 2 outcomes.

If reliable within-child slope covariance cannot be recovered from joint
bootstrap draws or a shared fit, the analysis must stop rather than assume the
measurement errors are independent.

## Mandatory validation layer

Every priority model must use the same predeclared validation workflow:

1. Freeze input hashes, row identities, exclusions, aggregation, formulas,
   priors, and posterior queries before fitting the production model.
2. Run synthetic parameter-recovery tests for the relevant likelihood and
   random-effects structure.
3. Perform prior predictive checks and save plots/tables before inspecting the
   posterior.
4. Fit PBM discovery, non-PBM replication, and all-79 descriptive scopes
   without changing formulas between scopes.
5. Compare linear, quadratic, and low-rank smooth age functions using
   leave-one-child/corpus predictive checks and PSIS-LOO stacking. Do not pick
   the curve with the most favorable developmental result.
6. Report R-hat, bulk/tail ESS, divergences, treedepth saturation, energy
   diagnostics, and chain traces. A nominally completed sampler is not enough.
7. Run posterior predictive checks by age, word effort, child, corpus, and
   relevant entropy/rank bands.
8. Run weak, skeptical, and wider prior sensitivities. Conclusions that change
   materially must be labeled prior-sensitive.
9. Report posterior effect distributions, supported-range contrasts,
   probability of direction, and probability inside a scientifically defined
   ROPE. Bayes factors are not primary.
10. Compare against the existing frequentist models as a robustness check;
    Bayesian estimates are not required to reproduce them exactly.

The first implementation must define effect-scale ROPEs before production
fits. They should represent practically negligible changes in bits, words, or
rank percentile over a six-month interval, not generic coefficient cutoffs.

## Computation and dependency decision

The current Python project environment contains no PyMC, Bambi, Stan, or brms.
The existing nonlinear suite uses `mgcv::bam`. The implementation task should
prefer `brms` with a pinned CmdStan backend because it directly supports the
required Student-t, negative-binomial, zero-one-inflated beta, distributional,
and multivariate formulas. This is a preference, not permission to install
unreviewed global dependencies.

Before changing dependencies:

- audit the existing local R installation and package versions;
- choose a repository-local reproducible environment;
- implement a tiny synthetic compile/sample smoke;
- benchmark one representative real-data pilot;
- project memory, disk, and runtime for every production fit.

Do not run these statistical models on Mila GPUs. If workstation CPU fitting
is infeasible, produce a compact benchmark report and a CPU compute plan
before any cluster submission work.

## Proposed staged workflow and namespace

Use a new isolated namespace:

```text
results/bayesian_route1_route2_20260828/
figs/bayesian_route1_route2_20260828/
docs/bayesian_route1_route2_report.md
docs/bayesian_route1_route2_report.html
```

Required stages:

```text
contract -> datasets -> priors -> synthetic-smoke -> real-pilot
         -> models -> diagnostics -> synthesis -> plots -> report -> audit
```

Each stage consumes saved predecessor artifacts and writes a schema/hash
manifest. Plotting and reporting never refit. Production completion requires
all five model families, all registered sample scopes, prior and posterior
predictive checks, sensitivity fits, influence diagnostics, a deterministic
report rebuild, and an independent final audit.

## Interpretation contract

- B1 and B2 concern predictability/conventionality at controlled effort.
- B3 and B4 concern effort adaptation, absolute and Qwen-relative.
- B5 concerns coordination between those developmental processes.
- None of B1-B5 proves optimization, intended-meaning preservation, or human
  comprehension.
- Raw bits remain scorer-specific. Cross-tokenizer score magnitudes are never
  pooled.
- Generated responses define a model-based reference distribution, not the
  child's feasible meaning-preserving alternatives.
- Null or contrary posterior evidence is a valid result and must not trigger
  replacement by an unregistered model.
