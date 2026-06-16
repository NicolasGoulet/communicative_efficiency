# Interpreted M1-M6 Super Atlas v2

This report is the interpreted companion to the original exhaustive M1-M6 super atlas. It leaves the original atlas unchanged and adds the missing plain-language layer: what each model asks, how it was implemented, how to read the plots, what coefficients mean, what is primary evidence, and what should not be overclaimed.

No new statistical models are fit in this synthesis. New model ideas are listed as proposed/not yet run unless a saved artifact already exists.

## Main Takeaway

The strongest current result is Model 2 with exact continuous effort controls and child fixed intercepts:

```text
sum_bits ~ age_c + target_effort_c + C(child_id)
```

Across words, morphemes, two syllable measures, and phonemes, the saved M2 rows show negative age coefficients. In plain language: for comparable production effort, and after each child gets their own baseline, older child utterances are predicted to have lower total Mistral surprisal. This is best interpreted as a developmental change in utterance-level predictability/information under effort control, not as proof that children communicate less.

This is Route 1 evidence: informativeness under controlled effort. The future Route 2 question is different: whether context uncertainty predicts how much effort or length the child chooses to produce.


## Source Context Inspected

This synthesis was built from the current repository reports and local course/project notes, especially:

- `AGENTS.md`, `TODO.md`, and `docs/notes.md`.
- the current supervisor-facing utterance-information report;
- the original M1-M6 super atlas, M1-M2/M1-M6 deep dive, fixed-effort atlas, context fixed-effort atlas, age-scrambling robustness report, and model zoo;
- response-level context entropy and Mila generation-plan notes;
- the Pawar and Cychosz paper summary and local PDF;
- the original November 2024 project-start draft and the Overleaf-style current-paper draft from the attachment cache;
- local `school_agent` Advanced Data Analytics notes on prediction versus explanation, model selection, clustered/longitudinal data, mixed models, and correlated observations;
- local `school_agent` project notes on hypotheses, variable map, confounds/controls, and modeling strategy;
- local paper notes for the CogSci child communicative-efficiency paper and the redundant-references-with-language-learners paper.

The named `school_agent` paper notes for the CogSci and redundant-reference papers are stubs, so this document uses them for framing only. It does not invent detailed methods/results that were not present in those notes.


## Project Motivation / Recent Email Context

The current project began from the idea that child communicative efficiency can be studied by jointly measuring informativeness and effort in naturalistic CHILDES conversations. The original November 2024 project draft framed informativeness as surprisal or likelihood, effort as utterance length/MLU-like complexity, and efficiency as a relation between the two. It also explicitly raised comparisons to caretakers, generated baselines, social variables, and clinical language data.

The current Overleaf-style draft reframes the work around developmental communicative efficiency: children may become more adult-like in balancing information content against production effort, with large language models used as one way to quantify contextual surprisal.

The exact recent email context has also been saved as `docs/project_motivation_recent_email_context_2026-06-16.md` and is quoted verbatim here:

```text
Hi Nicolas, Eva,

It was good catching up just now. I did a quick literature research on the idea of communicative efficiency in child language. The most closely related study is this CogSci paper (2023) on "Communicative efficiency is present in young children and becomes more adult-like with age": [https://escholarship.org/uc/item/7mm0z6fk](https://escholarship.org/uc/item/7mm0z6fk)

Here, through experiments with 4-year olds, they showed that these children tended to be influenced by communicative efficiency in a task where they reduce utterance (or message) length when a short message is sufficient to convey meanings accurately.

Here's another paper from the same leading author suggesting there's communicative efficiency modulated behavior in production "Speakers use more redundant references with language learners: Evidence for communicatively-efficient referential choice": [https://www.sciencedirect.com/science/article/pii/S0749596X22000651](https://www.sciencedirect.com/science/article/pii/S0749596X22000651)

 In light of these findings, I think for our purpose we can test a similar idea except in naturalistic conversations, as opposed to controlled experimental settings. The idea is to assess whether children's natural language use is shaped by efficiency criteria, and if so, when does it start to emerge. the thing with CHILDES is that we can do analyses with children under 4, and track the progression over the developmental time line.

One simple analysis we could consider is as follows. At each developmental stage, e.g. 1 year, 1.5, 2, etc. We can develop a computational model to predict the utterance length of the child speaker; we could do the same prediction with adult speaker (as a comparison). In this model, we can incorporate explicit criteria related to efficiency, and see if such criteria actually help the model in inferring whether a child would produce a lengthy or short message. We can then plot model accuracy as a function of developmental stage, and observe when efficiency-based utterance length modulation starts to kick in through the development.

One efficiency criterion related to the CogSci paper above and also our analyses so far is "contextual predictability" or "contextual informativeness". If there is enough information in the (preceding) contexts say from parent's utterance, the child should just produce a short message and therefore minimizing effort in production. However, if there is not enough information in context, perhaps the child is more likely to produce a longer message. So in other words, contextual informativeness might predict utterance length of children, and we can test if this is true or not, for both children and adults.

There are other possible confounding criteria we can consider, for instance, one predictor is the utterance length of caretaker's preceding context, another predictor can be whether the preceding context is a statement vs question, and if a question, whether it's a what/why/how/binary question, which all could influence the length of child production; similarly, frequency of words and familiarity of topic in the preceding context also matters.

If we can show that contextual predictability and informativeness somehow best predicts child utterance length, despite controlling for various confounds, that might be something novel to report.

Let me know what you both think, and I'd be happy to chat more next Thursday when we meet. For now Nicolas, I think you may want to read the above two papers to get a clear sense of what's been done and found so far.

Just to relate the idea below to the current analysis; basically I see two ways that we can quantify communicative efficiency of child speech:

1) Given context, do children optimize informativeness in their speech with utterance length constrained? I think this is similar to surprisal(utterance|context) which Nicolas has been looking at so far.

2) Given context, do children optimize utterance length (or production effort) in their speech? I believe that this is not something we have looked into, but it complements the above question where we allow length to be a variable, and therefore, seek to predict when children shorten or lengthen utterances, and whether that modulation is "optimized' based on context. Specifically, I am guessing that for more contextually predictive scenarios, i.e. entropy or surprisal of (next word(s)|context) is low, children should tend to utter a short sentence compared to cases where that quantity is high. There's some related work here that uses LLM to estimate contextual predictability: [https://onlinelibrary.wiley.com/doi/epdf/10.1111/cogs.70202](https://onlinelibrary.wiley.com/doi/epdf/10.1111/cogs.70202)

If we can investigate both aspects, it seems a good package; and of course, it'd be a plus if we can examine how SES, gender, and clinical condition affect communicative efficiency in children.
```


## Coverage

| model | primary continuous rows | context rows | robustness rows | plot references |
| --- | --- | --- | --- | --- |
| M1 | 5 | 20 | 80 | 46 |
| M2 | 5 | 20 | 80 | 54 |
| M3 | 5 | 20 | 80 | 57 |
| M4 | 5 | 60 | 60 | 67 |
| M5 | 5 | 60 | 60 | 63 |
| M6 | 5 | 60 | 60 | 63 |

## Source Artifact Inventory

| artifact_id | label | path | exists | rows | columns | first_columns |
| --- | --- | --- | --- | --- | --- | --- |
| deep_fit | M1/M2 primary fit summary | results/m1_m2_utterance_information_deep_dive/model_fit_summary.csv | True | 10 | 14 | model_id, model_label, effort_col, effort_label, formula, n_obs, n_children, r2 |
| deep_coef | M1/M2 primary coefficient table | results/m1_m2_utterance_information_deep_dive/model_coefficients.csv | True | 20 | 13 | model_id, model_label, effort_col, effort_label, term, term_label, original_col, coef |
| expanded | M1-M3 estimator-family sensitivity summary | results/m1_m2_utterance_information_deep_dive/expanded_model_family_summary.csv | True | 110 | 24 | approach_id, model_family_id, model_family_label, effort_col, effort_label, readable_formula, fit_type, effect_scale |
| m4_context | M4 context-entropy sensitivity summary | results/m1_m2_utterance_information_deep_dive/m4_context_entropy_model_summary.csv | True | 25 | 24 | model_id, model_label, question, formula, fit_type, effort_col, effort_label, outcome |
| m5_m6_saturated | M5/M6 effort-level exploratory summary | results/m1_m2_utterance_information_deep_dive/m5_m6_saturated_model_summary.csv | True | 10 | 17 | model_id, model_label, question, formula, fit_type, effect_scale, effort_col, effort_label |
| dual | M1-M6 continuous and effort-level model summary | results/m1_m6_dual_effort_quick_share/dual_model_summary.csv | True | 60 | 39 | model_id, model_title, question, effort_strategy, effort_col, effort_label, formula, readable_formula |
| fixed_summary | M1-M6 fixed-effort continuous model summary | results/m1_m6_fixed_effort_slices/fixed_effort_model_summary.csv | True | 30 | 39 | model_id, model_title, question, effort_strategy, effort_col, effort_label, formula, readable_formula |
| fixed_predictions | M1-M6 fixed-effort prediction rows | results/m1_m6_fixed_effort_slices/fixed_effort_predictions.csv | True | 8.046e+04 | 22 | age_months, age_c, effort_value, effort_c, context_entropy_bits, context_entropy_c, predicted_sum_bits, pred_ci_low |
| atlas_fit | M1-M6 fixed-effort atlas fit summary | results/m1_m6_fixed_effort_atlas/atlas_model_fit_summary.csv | True | 6 | 8 | model_id, mean_r2_observed_fitted, min_r2_observed_fitted, max_r2_observed_fitted, significant_age_slopes_p_lt_05, negative_age_slopes, positive_age_slopes, effort_units_tested |
| atlas_slopes | M1-M6 fixed-effort atlas slice slopes | results/m1_m6_fixed_effort_atlas/atlas_fixed_slice_slopes.csv | True | 402 | 9 | model_id, model_title, effort_col, effort_label, atlas_bin, fixed_effort_value, slope_bits_per_month, slope_bits_per_6_months |
| atlas_manifest | M1-M6 fixed-effort atlas figure manifest | results/m1_m6_fixed_effort_atlas/atlas_figure_manifest.csv | True | 30 | 4 | model_id, effort_col, effort_label, figure |
| context_m1_m6 | Context-window M1-M6 model summary | results/context_m1_m6_fixed_effort_atlas/context_m1_m6_model_summary.csv | True | 240 | 43 | context_k, model_id, model_family, model_label, context_variant, question, effort_col, effort_label |
| context_m1_m6_slopes | Context-window M1-M6 fixed-slice slopes | results/context_m1_m6_fixed_effort_atlas/context_m1_m6_slice_slopes.csv | True | 2340 | 11 | context_k, model_id, model_family, model_label, context_variant, effort_col, effort_label, atlas_bin |
| context_m1_m6_manifest | Context-window M1-M6 figure manifest | results/context_m1_m6_fixed_effort_atlas/context_m1_m6_figure_manifest.csv | True | 195 | 8 | context_k, model_id, model_family, model_label, context_variant, effort_col, effort_label, figure |
| context_fixed | Context-predictor adjunct model summary | results/context_fixed_effort_atlas/context_fixed_effort_model_summary.csv | True | 80 | 26 | context_k, model_id, model_label, question, effort_col, effort_label, context_size_col, context_size_label |
| context_fixed_manifest | Context-predictor adjunct figure manifest | results/context_fixed_effort_atlas/context_fixed_effort_figure_manifest.csv | True | 65 | 6 | context_k, model_id, model_label, effort_col, effort_label, figure |
| robustness | Age-bin bootstrap and scrambling summary | results/age_scrambling_robustness/age_scrambling_robustness_summary.csv | True | 420 | 21 | context_k, model_id, effort_col, effort_label, model_title, question, readable_formula, robustness_method |
| robustness_figures | Age-bin robustness figure manifest | results/age_scrambling_robustness/age_scrambling_figure_manifest.csv | True | 10 | 3 | figure_id, path, description |
| robustness_clear_figures | Clear robustness figure manifest | results/age_scrambling_robustness/age_scrambling_clear_figure_manifest.csv | True | 6 | 4 | figure_id, path, model_id, description |

## Model Ladder

| model | title | readable formula | primary scientific role |
| --- | --- | --- | --- |
| M1 | Pooled age and effort | sum_bits ~ age + effort | M1 is a baseline and a warning light. It shows the age-effort association before accounting for stable differences between children or corpora. |
| M2 | Age and effort with child identity | sum_bits ~ age + effort + C(child_id) | M2 is the cleanest first candidate for the supervisor-facing result: it asks whether same-child developmental change predicts total bits at fixed effort. |
| M3 | Age by effort | sum_bits ~ age * effort + C(child_id) | M3 tells us whether a single age slope hides different trajectories for short versus long utterances. |
| M4 | Context predictor added | sum_bits ~ age + effort + context predictor + C(child_id) | M4 asks whether the developmental result survives a control for how predictable the next-token context is. |
| M5 | Age by context predictor | sum_bits ~ age * context predictor + effort + C(child_id) | M5 is about developmental context sensitivity: whether older children show a different relation between context predictability and produced information. |
| M6 | Interaction-rich stress test | sum_bits ~ age * effort + age * context + effort * context + C(child_id) | M6 is a robustness stress test: it asks whether the simpler M2-M5 stories collapse under richer interactions. |

## Estimator And Library Guide

| label | library/object | what it is | where used | dependence handling |
| --- | --- | --- | --- | --- |
| OLS | `statsmodels.formula.api.ols` | ordinary linear regression on additive total bits | M1 baseline; primary M1-M6 atlas fits after adding child fixed effects where specified | none unless cluster covariance or `C(child_id)` is added |
| OLS + child-clustered SE | `fit(cov_type='cluster', cov_kwds={'groups': child_id})` | same OLS fitted line with standard errors adjusted for repeated utterances within child | primary dual-effort, fixed-effort, context atlas, and many deep-dive rows | affects uncertainty/p-values, not fitted means |
| Child fixed intercepts | `C(child_id)` in statsmodels formulas | one intercept per child | primary M2-M6 formulas | controls stable child baselines; it is not a random effect |
| Child fixed age slopes | `age_c:C(child_id)` | one linear age slope adjustment per child | M2/M3 sensitivity checks | diagnostic for child-specific developmental slopes |
| Gaussian GLM | `statsmodels.formula.api.glm(..., family=Gaussian())` | GLM version of the additive-bit linear model | M1-M3 sensitivity rows | no child dependence unless formula includes child terms |
| Gamma GLM, log link | `statsmodels.formula.api.glm(..., family=Gamma(link=Log()))` | positive-outcome sensitivity model; coefficients are on log expected bits | M1-M3 and M4 sensitivity rows | no child dependence unless formula includes child terms |
| GEE Gaussian/Gamma | `statsmodels.formula.api.gee(..., groups='child_id')` | population-average model clustered by child | M2/M3 and M4 sensitivity rows | models within-child correlation through GEE clustering |
| MixedLM random child intercept/slope | `statsmodels` mixed linear model | linear mixed model with random child intercept and sometimes random age slope | M2/M3 sensitivity rows only | random effects; several rows are singular/warning-prone, so use as diagnostics |

## Is Child Identity Control Too Strong?

Short answer: child identity control is appropriate and scientifically useful here, but it changes the question. It is not automatically "better" in every sense.

M1 asks a pooled question: across all rows, does age predict total information after effort control? Because children and corpora occupy different age ranges, M1 can confound development with which child, corpus, transcription style, and recording context happens to contribute data at a given age. This is why M1 is useful as a warning light rather than as the primary result.

M2 adds child fixed intercepts. That means each child receives a separate baseline level of predicted information, while the model estimates one shared age slope. In plain terms, M2 asks whether the age effect remains after removing stable child-to-child baseline differences. This is a conservative move if the target is within-child developmental change.

The worry is real: if children occupy different age ranges, child fixed effects discard between-child age composition. Some of that between-child variation may reflect meaningful developmental structure, but it is inseparable from corpus and child composition unless modeled carefully. M2 therefore answers a narrower question than "do older children in the dataset differ from younger children?" It answers "within the child-adjusted comparison, is later age associated with different target information at fixed effort?"

Child fixed effects can be too restrictive if the scientific estimand is a population developmental trajectory that legitimately includes between-child differences. They can also leave weak support where a child's age range is short or where older ages are represented by only a few children. They do not solve time-varying confounding, caregiver style changes, topic/task changes, or sparse age-bin support.

The right interpretation is therefore balanced:

- M1 is vulnerable to child/corpus composition.
- M2 is more conservative for within-child development.
- M2 can be too narrow if we also care about between-child developmental differences.
- Random slopes, within/between decomposition, age-overlap restrictions, corpus controls, age-bin balancing, and leave-one-child/corpus-out checks should be added before making a final dissertation-level causal/developmental claim.

Recommended next formulas are listed in the technical companion. None of those additions are claimed as results in this v2 report unless they already exist in saved artifacts.


## Child Identity: Fixed Effects, Random Effects, And Clustered SE

There are three different ideas that are easy to blur together:

1. `C(child_id)` means child fixed intercepts. Each child gets their own baseline level of `sum_bits`. The main age coefficient is then a shared child-adjusted age slope. This is the cleanest current primary Route 1 specification when the question is "does the age trend remain after stable child differences are removed?"
2. `(1 | child_id)` is mixed-model shorthand for a random child intercept. It also lets children have different baselines, but it treats those baselines as partially pooled draws from a population distribution. In `statsmodels`, this is a `MixedLM` with `groups=child_id`.
3. Child-clustered standard errors are not a child-identity control. They keep the same fitted mean as the OLS formula, but adjust uncertainty because utterances from the same child are correlated.

The random-slope version is:

```text
(1 + age_c | child_id)
```

Conceptually, this lets each child have both a different baseline and a different developmental slope, with partial pooling. It is attractive scientifically, but it can be unstable or singular when some children have narrow age coverage. That is why the current report treats MixedLM as sensitivity evidence rather than the primary result.

Practical recommendation for the corrected Route 1 ladder:

- Primary: OLS with `C(child_id)` and child-clustered standard errors.
- Sensitivity: GEE clustered by child.
- Sensitivity: MixedLM random intercept and random age slope, if stable.
- Diagnostic: within/between age decomposition to separate within-child development from between-child age composition.

So `C(child_id)` and `(1 | child_id)` are not interchangeable notation. They answer related but different questions and rely on different assumptions.

Do not fit `C(child_id)` and `(1 | child_id)` as if they were two independent controls in the same model. A child fixed intercept already gives each child its own baseline, while a random child intercept models child baselines through a partially pooled distribution. For this project, compare them as separate child-structure variants.

Likewise, a between-child predictor such as `child_mean_age` is not interpretable in the same formula as `C(child_id)`, because the child fixed intercepts absorb child-level constants. Use `age_within_child + C(child_id)` for a fixed-effect within-child check, or use a Mundlak-style `age_within_child + child_mean_age` model with clustered/GEE/random child structure for the within/between comparison.


## Formula Hierarchy For Interactions

The corrected Route 1 ladder must obey the hierarchy principle: if an interaction is in the model, its lower-order terms stay in the model too.

In Patsy/statsmodels syntax:

```text
age_c * effort_c
```

expands to:

```text
age_c + effort_c + age_c:effort_c
```

So the compact formula is not dropping main effects. Still, reports should write the expansion in words because readers will ask. The same applies to `age_c * context_entropy_c` and `target_source * age_c * effort_c`.

The cleaned Route 1 core should be:

```text
M1: sum_bits ~ age_c + effort_c
M2: sum_bits ~ age_c + effort_c + C(child_id)
M3: sum_bits ~ age_c * effort_c + C(child_id)
M4a: M3 + parent_context_effort_c
M4b: M3 + context_entropy_c
M4c: M3 + question_type
M5: M3 + parent_context_effort_c + context_entropy_c + question_type
M6: M3 + age_c:context_entropy_c + effort_c:context_entropy_c + parent_context_effort_c + question_type
```

M4a/M4b/M4c are especially important because they test one parent/context control at a time before the all-controls model.


## Baseline Comparison Logic

Yes: the cleaner baseline-comparison logic is to repeat the Route 1 atlas separately for each target source.

First-pass descriptive/comparative atlases:

```text
real child target:      M1-M6
random target:          M1-M6
unigram target:         M1-M6
bigram target:          M1-M6
trigram target:         M1-M6
LSTM target(s):         M1-M6
caretaker target:       optional separate role comparison, not the same baseline family
```

This means the same formulas, effort units, context windows, age bins, and robustness checks should be used independently for each source. Then we compare age coefficients, fixed-effort age curves, context-control stability, and age-scrambling robustness across sources.

Why independent atlases first? Because they show the developmental trajectory each source would have on its own. If the real child trajectory looks different from random/ngram/LSTM trajectories, that is much easier to explain visually and scientifically.

Only after the independent atlases exist should we fit the pooled formal comparison:

```text
sum_bits ~ target_source * age_c * effort_c + context_controls + C(child_id)
```

That pooled model tests whether source differences in the age-effort trajectory are statistically supported. But it should be the formal test after the source-specific atlases, not the only analysis.

Implementation detail: effort should be recomputed on the actual target utterance for each source. For same-word-length baselines, word count may be matched by construction, but morphemes, syllables, and phonemes can still differ. Keep the original child row id so source-specific rows remain paired to the same age, child, session, and context.


## Evidence Hierarchy

| level | evidence | use |
| --- | --- | --- |
| primary | M2 continuous exact-effort models, fixed-effort M2 plots, M2 age-scrambling robustness. | Supervisor-facing central result. |
| robustness | M3/M4/M6 stability, estimator sensitivity, GEE/GLM/MixedLM checks, context-window variants, fixed-slice support. | Appendix or defense of the main M2 story. |
| exploratory | M5, saturated M6 interactions, low/mid/high effort-level rows, current next-token entropy interpretation. | Generate next analyses; do not headline without stronger stability. |

## Major Plot Family Guide

| plot family | where | x/y/facets | lines/colors/ribbons | interpretation | caveat |
| --- | --- | --- | --- | --- | --- |
| cross-atlas heatmaps | figs/m1_m6_super_atlas | Rows are model variants; columns are effort units or robustness methods. | Cells are colored by coefficient, R2, sign share, or outside-null share. | Use as a map of which results are stable before opening detailed galleries. | Heatmaps compress many models; they are not a substitute for fixed-effort plots. |
| dual continuous vs effort-level plots | figs/m1_m6_dual_effort_quick_share | x is child age; y is predicted total bits; columns are effort units; rows are effort strategy. | Lines are model-predicted age trends; colors separate effort references or levels; ribbons are model confidence bands when available. | Compare exact continuous effort control against low/mid/high effort categories. | Low/mid/high categories are coarse and can reverse signs because exact effort still varies inside a category. |
| estimator deep-dive plots | figs/m1_m2_utterance_information_deep_dive | x is age; y is predicted total bits; panels/figures separate estimators and effort units. | Lines are fitted mean predictions. OLS and child-clustered OLS can share the same line; their uncertainty differs. | Check whether the conclusion depends on OLS, GLM, GEE, or MixedLM choices. | Gamma/log coefficients are on a log scale; use prediction plots rather than raw coefficients for intuition. |
| fixed-effort slice atlas | figs/m1_m6_fixed_effort_atlas | x is age; y is predicted total bits; facets group exact effort values. | Each colored line is one fixed effort value; shaded bands are model confidence bands for the fitted mean. | This is the cleanest visual answer to 'what happens at the same utterance size?' | A line at a sparse effort value is less supported; inspect row-support plots. |
| context-window fixed-effort atlas | figs/context_m1_m6_fixed_effort_atlas | x is age; y is predicted total bits; context windows k0-k3 and context variants are split across files. | Colored lines are fixed effort values. Ribbons are fitted mean uncertainty. | Check whether the age pattern survives no context, k1, k2, k3, entropy, and context-size variants. | Context entropy is next-token entropy; context size is a surface control, not semantic/pragmatic context richness. |
| age-scrambling robustness plots | figs/age_scrambling_robustness | x is age; y is anchored predicted mean total bits or age slope. | The observed line is compared with balanced-bootstrap and scrambled-age null ribbons. | If the observed slope is outside scrambled/null ranges, true age ordering is doing real work. | These are aggregated child-session-context-unit checks; coefficients need not equal utterance-level coefficients. |
| supervisor-facing M2 simple plots | figs/m2_simple_plots | x is age; y is predicted total bits; each plot uses one effort unit. | Colored lines are exact fixed effort values; the black line is the global adjusted trend. | Best compact plots for explaining the current primary result. | M2 has parallel fixed-effort lines because it does not include age-by-effort interaction. |

## What Fixed Effort Means

Fixed effort means the plotted prediction compares children at the same exact utterance size: for example, 3 words versus 3 words, or 6 morphemes versus 6 morphemes. The model is still fit on all eligible utterances. The fixed value is only the slice through the fitted surface used for the plot. This matters because raw age-bin means confound development with the fact that older children often produce longer utterances.

## Raw Means Versus Model-Adjusted Predictions

Raw age-bin means are descriptive summaries of what the data look like in each age bin. They are not controlled for effort, child identity, context, or corpus composition. Model-adjusted predictions are fitted expectations after the variables in the formula are controlled or fixed. When raw means and model predictions differ, the model is answering the controlled scientific question, not simply redrawing the average data.

## What To Cherry-Pick For The Supervisor Report

- Use the M2 continuous-effort result table for words/morphemes/syllables/phonemes.
- Use the M2 fixed-effort plots from `figs/m2_simple_plots` or the fixed-effort atlas.
- Use the M2 age-scrambling robustness plot as the compact robustness check.
- Mention M1 only as the reason child identity control matters.
- Mention M4 only as a provisional context-control check.
- Keep M5/M6 in the appendix unless the supervisor asks about interactions.

## What Not To Overclaim

- Do not claim the current result proves full communicative efficiency. It is an informativeness-under-effort-control result.
- Do not say older children communicate less. Lower surprisal at fixed effort may mean more contextual predictability, conventionality, adult-likeness, or scorer familiarity.
- Do not treat next-token context entropy as response-level uncertainty.
- Do not treat child fixed effects as the only correct answer. They answer a within-child-adjusted question and should be supplemented by within/between and overlap checks.
- Do not present p-values as model selection. The model ladder is theory-driven and robustness-driven.

## M1: Pooled age and effort

M1 deliberately pools children. Its main value is diagnostic: it shows how the apparent developmental direction can change when children and corpora occupy different age ranges. A pooled age coefficient mixes within-child change with between-child and between-corpus composition.

Computed atlas summary: continuous-effort age signs: 0 negative, 5 positive across 5 effort units; fixed-effort slices: 0% negative age slopes; context-window atlas age signs: 7 negative, 13 positive across 20 rows; robustness outside-null share: 81%.

### Formula, Estimator, And Child Structure

| item | value |
| --- | --- |
| scientific question | Pooling children, does age predict utterance total information after controlling utterance effort? |
| readable formula | sum_bits ~ age + effort |
| actual centered implementation | sum_bits ~ age_c + target_effort_c |
| primary estimator/library | ordinary linear regression / OLS via statsmodels.formula.api.ols |
| child identity role | omitted in the fitted mean; child can be used only for clustered SE in sensitivity rows |
| evidence role | Baseline and confounding warning. |

### Coefficient Dictionary

| term | plain-language meaning |
| --- | --- |
| age | Expected change in total target bits for one additional month, after this model's controls. |
| effort | Expected change in total bits for one more word/morpheme/syllable/phoneme in that model row. |
| age x effort | Whether the developmental age slope is different for shorter versus longer utterances. |
| context entropy | Association between current next-token context uncertainty and total bits in the produced target. |
| age x context entropy | Whether the context-entropy association changes as children get older. |
| effort x context entropy | Whether the effort slope differs in more uncertain versus less uncertain contexts. |
| effort level | Low/mid/high bins of one effort unit. These are diagnostics, not a replacement for exact fixed-effort control. |

Age effects in this family should be read in bits per month. Effort effects should be read in bits per one additional effort unit. Interaction terms should be read as slope changes, not as standalone main effects.

### Scientific Interpretation

Primary continuous-effort sign summary: 0 negative, 5 positive, and 0 exactly zero coefficients across 5 saved rows.

Supervisor-facing cherry-pick: Use only to explain why child identity control matters.

What not to overclaim: Do not treat the pooled age slope as the developmental result.


### Primary Continuous-Effort Rows

These rows are the clearest exact-effort versions for this model family. They keep words, morphemes, syllables, and phonemes in separate models to avoid collinearity.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.993 | 6.354 | <.001 |  |  |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |  |  |  |  | fit |

### Continuous Versus Low/Mid/High Effort Rows

Use these as a strategy comparison. The continuous rows control exact effort; the effort-level rows ask a coarser question about low, middle, and high effort categories.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.993 | 6.354 | <.001 |  |  |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort | 4.47e+05 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |  |  |  |  | fit |
| effort_level | Words | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.4211 | 0.1334 | 0.005 |  |  |  |  |  |  |  |  | fit |
| effort_level | Morphemes | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.3898 | 0.1672 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.452 | 0.134 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.4269 | 0.1638 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | sum_bits ~ age + effort_level | 4.47e+05 | 21 | 0.4502 | 0.1537 | <.001 |  |  |  |  |  |  |  |  | fit |

### Estimator Sensitivity Rows

These rows show whether a similar model story survives OLS, child-clustered OLS, GLM, GEE, or MixedLM variants. They are robustness evidence, not separate primary claims.

| model_family_label | fit_type | effect_scale | effort_label | readable_formula | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Morphemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -8.55e+09 | -6.64e-04 | <.001 | 0.1845 | <.001 |  |  |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Phonemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -8.849e+10 | 0.001138 | <.001 | 0.07251 | <.001 |  |  |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -2.041e+07 | 7.07e-04 | <.001 | 0.1794 | <.001 |  |  |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -3.665e+06 | 0.001311 | <.001 | 0.166 | <.001 |  |  |
| Gamma GLM, log link | glm_gamma_log | log mean bits | Words | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | -1.706e+07 | -7.77e-04 | <.001 | 0.2143 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Morphemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.5978 | 0.009018 | <.001 | 5.446 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Phonemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.632 | 0.0681 | <.001 | 2.07 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6345 | 0.05143 | <.001 | 5.212 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Syllables: pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6177 | 0.06904 | <.001 | 4.822 | <.001 |  |  |
| Gaussian GLM | glm_gaussian | additive bits | Words | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.873 | 6.354 | <.001 |  |  |
| OLS | ols | additive bits | Morphemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.5978 | 0.009018 | <.001 | 5.446 | <.001 |  |  |
| OLS | ols | additive bits | Phonemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.632 | 0.0681 | <.001 | 2.07 | <.001 |  |  |
| OLS | ols | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6345 | 0.05143 | <.001 | 5.212 | <.001 |  |  |
| OLS | ols | additive bits | Syllables: pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6177 | 0.06904 | <.001 | 4.822 | <.001 |  |  |
| OLS | ols | additive bits | Words | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.873 | 6.354 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Morphemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Phonemes | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |
| OLS, child-clustered SE | ols_cluster | additive bits | Words | sum_bits ~ age + effort | fit | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.993 | 6.354 | <.001 |  |  |

### Context-Window Atlas Rows

These rows repeat the model logic over k0-k3 and, for M4-M6, over entropy, context-size, and entropy-plus-size variants. The purpose is context robustness.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M1 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7122 | -0.06145 | 0.005 | 6.17 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7522 | 0.005929 | 0.707 | 2.343 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7414 | -0.008835 | 0.569 | 5.841 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.725 | 0.009849 | 0.508 | 5.418 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M1 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7189 | -0.06724 | 0.005 | 7.138 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6268 | -0.02637 | 0.382 | 5.731 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6649 | 0.03523 | 0.161 | 2.182 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6644 | 0.01867 | 0.449 | 5.479 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6482 | 0.03667 | 0.153 | 5.076 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M1 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6395 | -0.03427 | 0.294 | 6.668 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6074 | -0.003091 | 0.921 | 5.537 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6426 | 0.05686 | 0.032 | 2.105 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6445 | 0.04012 | 0.126 | 5.298 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6279 | 0.05785 | 0.032 | 4.903 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M1 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6218 | -0.01155 | 0.727 | 6.455 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.5978 | 0.009018 | 0.774 | 5.446 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.632 | 0.0681 | 0.012 | 2.07 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6345 | 0.05143 | 0.053 | 5.212 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6177 | 0.06904 | 0.012 | 4.822 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M1 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.613 | 3.09e-04 | 0.993 | 6.354 | <.001 |  |  |  |  |  |  |  |  |  |  |

### Balanced Bootstrap And Scrambling Robustness

These rows aggregate to child-session-context units. They ask whether the age slope survives equalized age-bin sampling and weakens when true age ordering is broken.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | age_bin_group_scramble | 5 | 2 | 2 | 0.544 | 0.129 |
| k0 | balanced_bootstrap | 5 | 2 | 3 | 0.756 |  |
| k0 | unit_age_scramble | 5 | 2 | 5 | 0.526 | 0.010 |
| k0 | within_child_age_scramble | 5 | 2 | 5 | 0.6 | 1.000 |
| k1 | age_bin_group_scramble | 5 | 0 | 4 | 0.502 | 0.010 |
| k1 | balanced_bootstrap | 5 | 0 | 4 | 0.818 |  |
| k1 | unit_age_scramble | 5 | 0 | 5 | 0.518 | 0.010 |
| k1 | within_child_age_scramble | 5 | 0 | 2 | 1 | 0.762 |
| k2 | age_bin_group_scramble | 5 | 0 | 5 | 0.486 | 0.010 |
| k2 | balanced_bootstrap | 5 | 0 | 5 | 0.924 |  |
| k2 | unit_age_scramble | 5 | 0 | 5 | 0.508 | 0.010 |
| k2 | within_child_age_scramble | 5 | 0 | 2 | 1 | 0.099 |
| k3 | age_bin_group_scramble | 5 | 0 | 5 | 0.514 | 0.010 |
| k3 | balanced_bootstrap | 5 | 0 | 4 | 0.966 |  |
| k3 | unit_age_scramble | 5 | 0 | 5 | 0.526 | 0.010 |
| k3 | within_child_age_scramble | 5 | 0 | 4 | 1 | 0.020 |

### Plot Gallery For M1

The repeated plot families were explained once above. In this gallery, read each plot family the same way: x-axis is usually child age, y-axis is predicted or observed total bits, colors usually separate effort values/levels or model variants, facets split effort units/context windows, and ribbons are model-confidence or bootstrap/null intervals depending on the family.

#### M1-M6 context-window fixed-effort atlas plots

![k0_m1_nb_morphemes_fixed_effort_atlas.png / k0 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_morphemes_fixed_effort_atlas.png)
*k0_m1_nb_morphemes_fixed_effort_atlas.png; k0; Morphemes*

![k0_m1_nb_phonemes_fixed_effort_atlas.png / k0 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_phonemes_fixed_effort_atlas.png)
*k0_m1_nb_phonemes_fixed_effort_atlas.png; k0; Phonemes*

![k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k0 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k0; Syllables: CMU/pkg*

![k0_m1_nb_syllables_pkg_fixed_effort_atlas.png / k0 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_pkg_fixed_effort_atlas.png)
*k0_m1_nb_syllables_pkg_fixed_effort_atlas.png; k0; Syllables: pkg*

![k0_m1_nb_words_fixed_effort_atlas.png / k0 / Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_words_fixed_effort_atlas.png)
*k0_m1_nb_words_fixed_effort_atlas.png; k0; Words*

![k1_m1_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_morphemes_fixed_effort_atlas.png)
*k1_m1_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m1_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_phonemes_fixed_effort_atlas.png)
*k1_m1_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m1_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m1_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m1_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_words_fixed_effort_atlas.png)
*k1_m1_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m1_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_morphemes_fixed_effort_atlas.png)
*k2_m1_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m1_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_phonemes_fixed_effort_atlas.png)
*k2_m1_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m1_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m1_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m1_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_words_fixed_effort_atlas.png)
*k2_m1_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m1_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_morphemes_fixed_effort_atlas.png)
*k3_m1_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m1_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_phonemes_fixed_effort_atlas.png)
*k3_m1_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m1_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m1_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m1_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_words_fixed_effort_atlas.png)
*k3_m1_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m1_coefficients_by_effort_version.png](../figs/m1_m2_utterance_information_deep_dive/m1_coefficients_by_effort_version.png)
*m1_coefficients_by_effort_version.png*

![m1_expanded_age_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m1_expanded_age_coefficients.png)
*m1_expanded_age_coefficients.png*

![m1_expanded_r2.png](../figs/m1_m2_utterance_information_deep_dive/m1_expanded_r2.png)
*m1_expanded_r2.png*

![m1_glm_gamma_log_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m1_glm_gamma_log_adjusted_age_lines.png)
*m1_glm_gamma_log_adjusted_age_lines.png*

![m1_glm_gaussian_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m1_glm_gaussian_adjusted_age_lines.png)
*m1_glm_gaussian_adjusted_age_lines.png*

![m1_low_mid_high_effort_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m1_low_mid_high_effort_adjusted_age_predictions.png)
*m1_low_mid_high_effort_adjusted_age_predictions.png*

![m1_m2_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png)
*m1_m2_adjusted_age_predictions.png*

![m1_m2_age_coefficients_by_effort.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_age_coefficients_by_effort.png)
*m1_m2_age_coefficients_by_effort.png*

![m1_m2_delta_r2_variable_importance.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_delta_r2_variable_importance.png)
*m1_m2_delta_r2_variable_importance.png*

![m1_m2_effort_coefficients_by_measure.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_effort_coefficients_by_measure.png)
*m1_m2_effort_coefficients_by_measure.png*

![m1_m2_residual_diagnostics_words.png / Words](../figs/m1_m2_utterance_information_deep_dive/m1_m2_residual_diagnostics_words.png)
*m1_m2_residual_diagnostics_words.png; Words*

![m1_ols_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m1_ols_adjusted_age_lines.png)
*m1_ols_adjusted_age_lines.png*

![m1_ols_cluster_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m1_ols_cluster_adjusted_age_lines.png)
*m1_ols_cluster_adjusted_age_lines.png*

#### M1-M6 continuous versus effort-level plots

![m1_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m1_dual_effort_predictions.png)
*m1_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m1_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m1_nb_morphemes_atlas_bins.png)
*m1_nb_morphemes_atlas_bins.png; Morphemes*

![m1_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m1_nb_phonemes_atlas_bins.png)
*m1_nb_phonemes_atlas_bins.png; Phonemes*

![m1_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m1_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m1_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_pkg_atlas_bins.png)
*m1_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m1_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m1_nb_words_atlas_bins.png)
*m1_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m1_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m1_granular_primary_fixed_effort_slices.png)
*m1_granular_primary_fixed_effort_slices.png*

![m1_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m1_marginal_adjusted_global_trends.png)
*m1_marginal_adjusted_global_trends.png*

![m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m1_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m1_top_frequency_12_fixed_effort_slices.png)
*m1_top_frequency_12_fixed_effort_slices.png*

![m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m1_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m1_age_slope_robustness_intervals.png)
*m1_age_slope_robustness_intervals.png*

![m1_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m1_clear_robustness_regression_lines.png)
*m1_clear_robustness_regression_lines.png*



## M2: Age and effort with child identity

M2 is the current cleanest result. It asks whether a same-child developmental trajectory remains after exact production effort is held constant. Negative age coefficients mean that, for comparable utterance size and child baseline, older children's target utterances receive lower total Mistral surprisal.

Computed atlas summary: continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 100% negative age slopes; context-window atlas age signs: 20 negative, 0 positive across 20 rows; robustness outside-null share: 76%.

### Formula, Estimator, And Child Structure

| item | value |
| --- | --- |
| scientific question | Does the age effect remain after controlling utterance effort and each child's baseline? |
| readable formula | sum_bits ~ age + effort + child identity |
| actual centered implementation | sum_bits ~ age_c + target_effort_c + C(child_id) |
| primary estimator/library | ordinary linear regression / OLS via statsmodels.formula.api.ols |
| child identity role | fixed intercept through C(child_id); clustered SE in primary report rows |
| evidence role | Primary current evidence. |

### Coefficient Dictionary

| term | plain-language meaning |
| --- | --- |
| age | Expected change in total target bits for one additional month, after this model's controls. |
| effort | Expected change in total bits for one more word/morpheme/syllable/phoneme in that model row. |
| age x effort | Whether the developmental age slope is different for shorter versus longer utterances. |
| context entropy | Association between current next-token context uncertainty and total bits in the produced target. |
| age x context entropy | Whether the context-entropy association changes as children get older. |
| effort x context entropy | Whether the effort slope differs in more uncertain versus less uncertain contexts. |
| effort level | Low/mid/high bins of one effort unit. These are diagnostics, not a replacement for exact fixed-effort control. |

Age effects in this family should be read in bits per month. Effort effects should be read in bits per one additional effort unit. Interaction terms should be read as slope changes, not as standalone main effects.

### Scientific Interpretation

Primary continuous-effort sign summary: 5 negative, 0 positive, and 0 exactly zero coefficients across 5 saved rows.

Supervisor-facing cherry-pick: Cherry-pick the continuous exact-effort M2 table, fixed-effort plots, and k3 robustness plot.

What not to overclaim: Do not say children communicate less; say lower predicted Mistral surprisal at fixed effort within the child-adjusted comparison.


### Primary Continuous-Effort Rows

These rows are the clearest exact-effort versions for this model family. They keep words, morphemes, syllables, and phonemes in separate models to avoid collinearity.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  | fit |

### Continuous Versus Low/Mid/High Effort Rows

Use these as a strategy comparison. The continuous rows control exact effort; the effort-level rows ask a coarser question about low, middle, and high effort categories.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort + child identity | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  | fit |
| effort_level | Words | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4353 | 0.08168 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Morphemes | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4064 | 0.117 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4631 | 0.07177 | 0.005 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4398 | 0.1069 | <.001 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | sum_bits ~ age + effort_level + child identity | 4.47e+05 | 21 | 0.4622 | 0.08531 | <.001 |  |  |  |  |  |  |  |  | fit |

### Estimator Sensitivity Rows

These rows show whether a similar model story survives OLS, child-clustered OLS, GLM, GEE, or MixedLM variants. They are robustness evidence, not separate primary claims.

| model_family_label | fit_type | effect_scale | effort_label | readable_formula | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Morphemes | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -9.764e+09 | -0.006172 | <.001 | 0.1858 | <.001 |  |  |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Phonemes | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -1.09e+11 | -0.004326 | <.001 | 0.07309 | <.001 |  |  |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -2.117e+07 | -0.003852 | <.001 | 0.1801 | <.001 |  |  |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -3.49e+06 | -0.003385 | 0.003 | 0.1662 | <.001 |  |  |
| Gamma GEE, log link, clustered by child | gee_gamma_log | log mean bits | Words | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | -1.475e+07 | -0.005415 | <.001 | 0.2138 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Morphemes | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -9.437e+09 | -0.005968 | <.001 | 0.1858 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Phonemes | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -9.773e+10 | -0.004147 | <.001 | 0.07297 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -1.964e+07 | -0.003677 | <.001 | 0.1799 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -3.211e+06 | -0.003214 | <.001 | 0.1662 | <.001 |  |  |
| Gamma GLM, log link + child fixed intercepts | glm_gamma_log | log mean bits | Words | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | -1.484e+07 | -0.005295 | <.001 | 0.2142 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Morphemes | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.5923 | -0.1354 | <.001 | 5.489 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Phonemes | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.6273 | -0.06478 | 0.011 | 2.084 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.631 | -0.06318 | 0.015 | 5.236 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Syllables: pkg | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.6139 | -0.04838 | 0.044 | 4.831 | <.001 |  |  |
| Gaussian GEE, clustered by child | gee_gaussian | additive bits | Words | sum_bits ~ age + effort, grouped by child | fit | 4.47e+05 | 21 | 0.6087 | -0.1224 | <.001 | 6.367 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Morphemes | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6152 | -0.1958 | <.001 | 5.508 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Phonemes | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6456 | -0.1064 | 0.003 | 2.087 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6474 | -0.1149 | 0.003 | 5.245 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Syllables: pkg | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6308 | -0.08571 | 0.131 | 4.837 | <.001 |  |  |
| Linear mixed model, random child age slope | mixedlm | additive bits | Words | sum_bits ~ age + effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6277 | -0.1852 | <.001 | 6.386 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Morphemes | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.07 | -0.1355 | <.001 | 5.489 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Phonemes | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.035 | -0.06486 | <.001 | 2.084 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.032 | -0.06326 | <.001 | 5.236 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Syllables: pkg | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.049 | -0.04846 | <.001 | 4.831 | <.001 |  |  |
| Linear mixed model, random child intercept | mixedlm | additive bits | Words | sum_bits ~ age + effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.054 | -0.1225 | <.001 | 6.367 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Morphemes | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Phonemes | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |
| OLS + child fixed intercepts | ols_cluster | additive bits | Words | sum_bits ~ age + effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Morphemes | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6152 | -0.196 | <.001 | 5.508 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Phonemes | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6456 | -0.0861 | <.001 | 2.087 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6474 | -0.09669 | <.001 | 5.245 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6308 | -0.08275 | <.001 | 4.837 | <.001 |  |  |
| OLS + child fixed intercepts and age slopes | ols_cluster | additive bits | Words | sum_bits ~ age + effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6277 | -0.1525 | <.001 | 6.386 | <.001 |  |  |

### Context-Window Atlas Rows

These rows repeat the model logic over k0-k3 and, for M4-M6, over entropy, context-size, and entropy-plus-size variants. The purpose is context robustness.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M2 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7204 | -0.1784 | <.001 | 6.195 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7578 | -0.09847 | 0.001 | 2.352 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7461 | -0.0907 | 0.003 | 5.848 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7303 | -0.07571 | 0.009 | 5.411 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k0 | M2 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7252 | -0.1582 | <.001 | 7.127 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.639 | -0.1585 | <.001 | 5.772 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6743 | -0.08519 | <.001 | 2.196 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6729 | -0.08207 | <.001 | 5.502 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6572 | -0.06724 | 0.001 | 5.084 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k1 | M2 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6495 | -0.1431 | <.001 | 6.677 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6217 | -0.1425 | <.001 | 5.581 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6542 | -0.07096 | 0.005 | 2.12 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6551 | -0.06903 | 0.007 | 5.323 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.639 | -0.0542 | 0.021 | 4.914 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k2 | M2 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6338 | -0.1287 | <.001 | 6.468 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  |  |  |  |  |
| k3 | M2 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  |  |  |  |  |

### Balanced Bootstrap And Scrambling Robustness

These rows aggregate to child-session-context units. They ask whether the age slope survives equalized age-bin sampling and weakens when true age ordering is broken.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | age_bin_group_scramble | 5 | 5 | 5 | 0.472 | 0.010 |
| k0 | balanced_bootstrap | 5 | 5 | 1 | 1 |  |
| k0 | unit_age_scramble | 5 | 5 | 5 | 0.554 | 0.010 |
| k0 | within_child_age_scramble | 5 | 5 | 5 | 0.502 | 0.010 |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.494 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 0 | 0.998 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.484 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.504 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 5 | 0.492 | 0.010 |
| k2 | balanced_bootstrap | 5 | 5 | 0 | 0.996 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.494 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.516 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 5 | 0.5 | 0.010 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.99 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.52 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.514 | 0.010 |

### Plot Gallery For M2

The repeated plot families were explained once above. In this gallery, read each plot family the same way: x-axis is usually child age, y-axis is predicted or observed total bits, colors usually separate effort values/levels or model variants, facets split effort units/context windows, and ribbons are model-confidence or bootstrap/null intervals depending on the family.

#### M1-M6 context-window fixed-effort atlas plots

![k0_m2_nb_morphemes_fixed_effort_atlas.png / k0 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_morphemes_fixed_effort_atlas.png)
*k0_m2_nb_morphemes_fixed_effort_atlas.png; k0; Morphemes*

![k0_m2_nb_phonemes_fixed_effort_atlas.png / k0 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_phonemes_fixed_effort_atlas.png)
*k0_m2_nb_phonemes_fixed_effort_atlas.png; k0; Phonemes*

![k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k0 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k0; Syllables: CMU/pkg*

![k0_m2_nb_syllables_pkg_fixed_effort_atlas.png / k0 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_pkg_fixed_effort_atlas.png)
*k0_m2_nb_syllables_pkg_fixed_effort_atlas.png; k0; Syllables: pkg*

![k0_m2_nb_words_fixed_effort_atlas.png / k0 / Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_words_fixed_effort_atlas.png)
*k0_m2_nb_words_fixed_effort_atlas.png; k0; Words*

![k1_m2_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_morphemes_fixed_effort_atlas.png)
*k1_m2_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m2_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_phonemes_fixed_effort_atlas.png)
*k1_m2_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m2_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m2_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m2_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_words_fixed_effort_atlas.png)
*k1_m2_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m2_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_morphemes_fixed_effort_atlas.png)
*k2_m2_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m2_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_phonemes_fixed_effort_atlas.png)
*k2_m2_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m2_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m2_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m2_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_words_fixed_effort_atlas.png)
*k2_m2_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m2_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_morphemes_fixed_effort_atlas.png)
*k3_m2_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m2_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_phonemes_fixed_effort_atlas.png)
*k3_m2_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m2_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m2_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m2_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_words_fixed_effort_atlas.png)
*k3_m2_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m1_m2_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png)
*m1_m2_adjusted_age_predictions.png*

![m1_m2_age_coefficients_by_effort.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_age_coefficients_by_effort.png)
*m1_m2_age_coefficients_by_effort.png*

![m1_m2_delta_r2_variable_importance.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_delta_r2_variable_importance.png)
*m1_m2_delta_r2_variable_importance.png*

![m1_m2_effort_coefficients_by_measure.png](../figs/m1_m2_utterance_information_deep_dive/m1_m2_effort_coefficients_by_measure.png)
*m1_m2_effort_coefficients_by_measure.png*

![m1_m2_residual_diagnostics_words.png / Words](../figs/m1_m2_utterance_information_deep_dive/m1_m2_residual_diagnostics_words.png)
*m1_m2_residual_diagnostics_words.png; Words*

![m2_coefficients_by_effort_version.png](../figs/m1_m2_utterance_information_deep_dive/m2_coefficients_by_effort_version.png)
*m2_coefficients_by_effort_version.png*

![m2_expanded_age_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m2_expanded_age_coefficients.png)
*m2_expanded_age_coefficients.png*

![m2_expanded_r2.png](../figs/m1_m2_utterance_information_deep_dive/m2_expanded_r2.png)
*m2_expanded_r2.png*

![m2_gee_gamma_log_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_gee_gamma_log_adjusted_age_lines.png)
*m2_gee_gamma_log_adjusted_age_lines.png*

![m2_gee_gaussian_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_gee_gaussian_adjusted_age_lines.png)
*m2_gee_gaussian_adjusted_age_lines.png*

![m2_glm_gamma_log_child_fe_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_glm_gamma_log_child_fe_adjusted_age_lines.png)
*m2_glm_gamma_log_child_fe_adjusted_age_lines.png*

![m2_low_mid_high_effort_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m2_low_mid_high_effort_adjusted_age_predictions.png)
*m2_low_mid_high_effort_adjusted_age_predictions.png*

![m2_mixed_random_age_slope_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_age_slope_adjusted_age_lines.png)
*m2_mixed_random_age_slope_adjusted_age_lines.png*

![m2_mixed_random_intercept_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_intercept_adjusted_age_lines.png)
*m2_mixed_random_intercept_adjusted_age_lines.png*

![m2_ols_child_fe_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_adjusted_age_lines.png)
*m2_ols_child_fe_adjusted_age_lines.png*

![m2_ols_child_fe_age_slope_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_age_slope_adjusted_age_lines.png)
*m2_ols_child_fe_age_slope_adjusted_age_lines.png*

#### M1-M6 continuous versus effort-level plots

![m2_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m2_dual_effort_predictions.png)
*m2_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m2_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m2_nb_morphemes_atlas_bins.png)
*m2_nb_morphemes_atlas_bins.png; Morphemes*

![m2_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m2_nb_phonemes_atlas_bins.png)
*m2_nb_phonemes_atlas_bins.png; Phonemes*

![m2_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m2_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m2_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_pkg_atlas_bins.png)
*m2_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m2_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m2_nb_words_atlas_bins.png)
*m2_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m2_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m2_granular_primary_fixed_effort_slices.png)
*m2_granular_primary_fixed_effort_slices.png*

![m2_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m2_marginal_adjusted_global_trends.png)
*m2_marginal_adjusted_global_trends.png*

![m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m2_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m2_top_frequency_12_fixed_effort_slices.png)
*m2_top_frequency_12_fixed_effort_slices.png*

![m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Supervisor-facing Model 2 simple plots

![m2_morphemes_fixed_effort_and_global_trend.png / Morphemes](../figs/m2_simple_plots/m2_morphemes_fixed_effort_and_global_trend.png)
*m2_morphemes_fixed_effort_and_global_trend.png; Morphemes*

![m2_phonemes_fixed_effort_and_global_trend.png / Phonemes](../figs/m2_simple_plots/m2_phonemes_fixed_effort_and_global_trend.png)
*m2_phonemes_fixed_effort_and_global_trend.png; Phonemes*

![m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png / Syllables: CMU/pkg](../figs/m2_simple_plots/m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png)
*m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png; Syllables: CMU/pkg*

![m2_syllables_pkg_fixed_effort_and_global_trend.png / Syllables: pkg](../figs/m2_simple_plots/m2_syllables_pkg_fixed_effort_and_global_trend.png)
*m2_syllables_pkg_fixed_effort_and_global_trend.png; Syllables: pkg*

![m2_words_fixed_effort_and_global_trend.png / Words](../figs/m2_simple_plots/m2_words_fixed_effort_and_global_trend.png)
*m2_words_fixed_effort_and_global_trend.png; Words*

#### Age-bin bootstrap and scrambling robustness plots

![m2_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m2_age_slope_robustness_intervals.png)
*m2_age_slope_robustness_intervals.png*

![m2_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png)
*m2_clear_robustness_regression_lines.png*



## M3: Age by effort

M3 tests whether the age trend differs across effort values. The interaction term is best read through fixed-effort plots: non-parallel lines mean the age slope changes for shorter versus longer utterances.

Computed atlas summary: continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 94% negative age slopes; context-window atlas age signs: 20 negative, 0 positive across 20 rows; robustness outside-null share: 80%.

### Formula, Estimator, And Child Structure

| item | value |
| --- | --- |
| scientific question | Does the developmental age effect depend on utterance effort? |
| readable formula | sum_bits ~ age * effort + child identity |
| actual centered implementation | sum_bits ~ age_c * target_effort_c + C(child_id) |
| primary estimator/library | ordinary linear regression / OLS via statsmodels.formula.api.ols |
| child identity role | fixed intercept through C(child_id); mixed random-intercept/slope rows are sensitivity checks |
| evidence role | Robustness and mechanism check. |

### Coefficient Dictionary

| term | plain-language meaning |
| --- | --- |
| age | Expected change in total target bits for one additional month, after this model's controls. |
| effort | Expected change in total bits for one more word/morpheme/syllable/phoneme in that model row. |
| age x effort | Whether the developmental age slope is different for shorter versus longer utterances. |
| context entropy | Association between current next-token context uncertainty and total bits in the produced target. |
| age x context entropy | Whether the context-entropy association changes as children get older. |
| effort x context entropy | Whether the effort slope differs in more uncertain versus less uncertain contexts. |
| effort level | Low/mid/high bins of one effort unit. These are diagnostics, not a replacement for exact fixed-effort control. |

Age effects in this family should be read in bits per month. Effort effects should be read in bits per one additional effort unit. Interaction terms should be read as slope changes, not as standalone main effects.

### Scientific Interpretation

Primary continuous-effort sign summary: 5 negative, 0 positive, and 0 exactly zero coefficients across 5 saved rows.

Supervisor-facing cherry-pick: Use only if explaining whether short and long utterances have different age slopes.

What not to overclaim: Do not make the age-by-effort interaction central unless it is stable across effort units.


### Primary Continuous-Effort Rows

These rows are the clearest exact-effort versions for this model family. They keep words, morphemes, syllables, and phonemes in separate models to avoid collinearity.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 |  |  | -0.003787 | 0.515 |  |  | fit |
| continuous | Morphemes | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 |  |  | 0.00228 | 0.727 |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 |  |  | 0.00703 | 0.252 |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 |  |  | 0.009859 | 0.022 |  |  | fit |
| continuous | Phonemes | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 |  |  | 0.002729 | 0.220 |  |  | fit |

### Continuous Versus Low/Mid/High Effort Rows

Use these as a strategy comparison. The continuous rows control exact effort; the effort-level rows ask a coarser question about low, middle, and high effort categories.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 |  |  | -0.003787 | 0.515 |  |  | fit |
| continuous | Morphemes | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 |  |  | 0.00228 | 0.727 |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 |  |  | 0.00703 | 0.252 |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 |  |  | 0.009859 | 0.022 |  |  | fit |
| continuous | Phonemes | sum_bits ~ age * effort + child identity | 4.47e+05 | 21 | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 |  |  | 0.002729 | 0.220 |  |  | fit |
| effort_level | Words | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4401 | -0.0722 | 0.033 |  |  |  |  |  |  |  |  | fit |
| effort_level | Morphemes | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4122 | -0.0701 | 0.064 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4688 | -0.06415 | 0.033 |  |  |  |  |  |  |  |  | fit |
| effort_level | Syllables: pkg | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4466 | -0.05571 | 0.073 |  |  |  |  |  |  |  |  | fit |
| effort_level | Phonemes | sum_bits ~ age * effort_level + child identity | 4.47e+05 | 21 | 0.4676 | -0.07701 | 0.009 |  |  |  |  |  |  |  |  | fit |

### Estimator Sensitivity Rows

These rows show whether a similar model story survives OLS, child-clustered OLS, GLM, GEE, or MixedLM variants. They are robustness evidence, not separate primary claims.

| model_family_label | fit_type | effect_scale | effort_label | readable_formula | status | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | age_effort_coef | age_effort_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Morphemes | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -3.732e+09 | -0.005665 | <.001 | 0.1911 | <.001 | -0.001651 | <.001 |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Phonemes | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -3.432e+10 | -0.003763 | <.001 | 0.07498 | <.001 | -6.51e-04 | <.001 |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -9.342e+06 | -0.003282 | <.001 | 0.1846 | <.001 | -0.001583 | <.001 |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -2.174e+06 | -0.00289 | 0.001 | 0.1698 | <.001 | -0.001324 | <.001 |
| Gamma GEE, log link + interaction, clustered by child | gee_gamma_log | log mean bits | Words | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | -6.274e+06 | -0.004872 | <.001 | 0.2206 | <.001 | -0.002085 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Morphemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -3.583e+09 | -1.16e-04 | 0.138 | 0.188 | <.001 | -0.001265 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Phonemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -2.867e+10 | 0.001765 | <.001 | 0.07379 | <.001 | -5.49e-04 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -9.405e+06 | 0.00132 | <.001 | 0.1825 | <.001 | -0.001299 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -2.279e+06 | 0.001832 | <.001 | 0.1684 | <.001 | -0.001072 | <.001 |
| Gamma GLM, log link + interaction | glm_gamma_log | log mean bits | Words | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | -7.589e+06 | -1.48e-04 | 0.055 | 0.219 | <.001 | -0.001715 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Morphemes | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -3.05e+09 | -0.005556 | <.001 | 0.1902 | <.001 | -0.001637 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Phonemes | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -2.596e+10 | -0.003664 | <.001 | 0.0745 | <.001 | -6.47e-04 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Syllables: CMU/pkg | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -7.775e+06 | -0.00319 | <.001 | 0.1837 | <.001 | -0.001555 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Syllables: pkg | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -1.805e+06 | -0.002794 | <.001 | 0.1691 | <.001 | -0.001311 | <.001 |
| Gamma GLM, log link + interaction + child fixed intercepts | glm_gamma_log | log mean bits | Words | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | -5.518e+06 | -0.004859 | <.001 | 0.22 | <.001 | -0.002082 | <.001 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Morphemes | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.5924 | -0.1361 | <.001 | 5.482 | <.001 | 0.002283 | 0.720 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Phonemes | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.6276 | -0.06714 | 0.014 | 2.077 | <.001 | 0.00273 | 0.209 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.6313 | -0.06578 | 0.014 | 5.217 | <.001 | 0.007032 | 0.240 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Syllables: pkg | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.6143 | -0.05206 | 0.050 | 4.806 | <.001 | 0.009861 | 0.019 |
| Gaussian GEE + interaction, clustered by child | gee_gaussian | additive bits | Words | sum_bits ~ age * effort, grouped by child | fit | 4.47e+05 | 21 | 0.6086 | -0.1215 | <.001 | 6.379 | <.001 | -0.003783 | 0.505 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Morphemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.598 | 0.004168 | 0.037 | 5.416 | <.001 | 0.0103 | <.001 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Phonemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6322 | 0.06241 | <.001 | 2.059 | <.001 | 0.004518 | <.001 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6348 | 0.04521 | <.001 | 5.181 | <.001 | 0.01174 | <.001 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Syllables: pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6181 | 0.06146 | <.001 | 4.787 | <.001 | 0.01407 | <.001 |
| Gaussian GLM + interaction | glm_gaussian | additive bits | Words | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.613 | -0.001242 | 0.526 | 6.342 | <.001 | 0.003893 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Morphemes | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6152 | -0.1928 | <.001 | 5.497 | <.001 | 0.003414 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Phonemes | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6457 | -0.1004 | 0.005 | 2.079 | <.001 | 0.003128 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6475 | -0.109 | 0.063 | 5.223 | <.001 | 0.00797 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Syllables: pkg | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6311 | -0.07614 | 0.032 | 4.806 | <.001 | 0.01145 | <.001 |
| Linear mixed model + interaction, random child age slope | mixedlm | additive bits | Words | sum_bits ~ age * effort + (age / child_id) | fit | 4.47e+05 | 21 | 0.6277 | -0.189 | <.001 | 6.402 | <.001 | -0.005014 | <.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Morphemes | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | 0.6131 | -0.136 | <.001 | 5.482 | <.001 | 0.002287 | 0.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Phonemes | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.029 | -0.06723 | <.001 | 2.077 | <.001 | 0.002729 | <.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.025 | -0.06586 | <.001 | 5.217 | <.001 | 0.00703 | <.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Syllables: pkg | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | -2.038 | -0.05214 | <.001 | 4.806 | <.001 | 0.009859 | <.001 |
| Linear mixed model + interaction, random child intercept | mixedlm | additive bits | Words | sum_bits ~ age * effort + (1 / child_id) | fit | 4.47e+05 | 21 | 0.6259 | -0.1214 | <.001 | 6.379 | <.001 | -0.003779 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Morphemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.598 | 0.004168 | 0.037 | 5.416 | <.001 | 0.0103 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Phonemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6322 | 0.06241 | <.001 | 2.059 | <.001 | 0.004518 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6348 | 0.04521 | <.001 | 5.181 | <.001 | 0.01174 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Syllables: pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6181 | 0.06146 | <.001 | 4.787 | <.001 | 0.01407 | <.001 |
| OLS + age by effort interaction | ols | additive bits | Words | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.613 | -0.001242 | 0.526 | 6.342 | <.001 | 0.003893 | <.001 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Morphemes | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 | 0.00228 | 0.727 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Phonemes | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 | 0.002729 | 0.220 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 | 0.00703 | 0.252 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 | 0.009859 | 0.022 |
| OLS + interaction + child fixed intercepts | ols_cluster | additive bits | Words | sum_bits ~ age * effort + C(child_id) | fit | 4.47e+05 | 21 | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 | -0.003787 | 0.515 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Morphemes | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6152 | -0.2023 | <.001 | 5.498 | <.001 | 0.003415 | 0.628 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Phonemes | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6457 | -0.1008 | <.001 | 2.079 | <.001 | 0.003132 | 0.216 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6475 | -0.1119 | <.001 | 5.223 | <.001 | 0.007986 | 0.239 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6311 | -0.1053 | <.001 | 4.806 | <.001 | 0.01146 | 0.015 |
| OLS + interaction + child fixed intercepts and age slopes | ols_cluster | additive bits | Words | sum_bits ~ age * effort + C(child_id) + age:C(child_id) | fit | 4.47e+05 | 21 | 0.6277 | -0.1448 | <.001 | 6.402 | <.001 | -0.005015 | 0.460 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Morphemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.598 | 0.004168 | 0.891 | 5.416 | <.001 | 0.0103 | 0.034 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Phonemes | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6322 | 0.06241 | 0.014 | 2.059 | <.001 | 0.004518 | 0.008 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Syllables: CMU/pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6348 | 0.04521 | 0.070 | 5.181 | <.001 | 0.01174 | 0.023 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Syllables: pkg | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.6181 | 0.06146 | 0.017 | 4.787 | <.001 | 0.01407 | <.001 |
| OLS + interaction, child-clustered SE | ols_cluster | additive bits | Words | sum_bits ~ age * effort | fit | 4.47e+05 | 21 | 0.613 | -0.001242 | 0.970 | 6.342 | <.001 | 0.003893 | 0.422 |

### Context-Window Atlas Rows

These rows repeat the model logic over k0-k3 and, for M4-M6, over entropy, context-size, and entropy-plus-size variants. The purpose is context robustness.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M3 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7211 | -0.1727 | <.001 | 6.256 | <.001 |  |  |  |  | -0.02036 | 0.010 |  |  |  |  |
| k0 | M3 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7581 | -0.094 | 0.002 | 2.366 | <.001 |  |  |  |  | -0.005153 | 0.071 |  |  |  |  |
| k0 | M3 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7463 | -0.08636 | 0.002 | 5.88 | <.001 |  |  |  |  | -0.01175 | 0.110 |  |  |  |  |
| k0 | M3 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7305 | -0.07272 | 0.009 | 5.431 | <.001 |  |  |  |  | -0.007984 | 0.121 |  |  |  |  |
| k0 | M3 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.7263 | -0.1515 | <.001 | 7.217 | <.001 |  |  |  |  | -0.02929 | <.001 |  |  |  |  |
| k1 | M3 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.639 | -0.1576 | <.001 | 5.782 | <.001 |  |  |  |  | -0.003203 | 0.612 |  |  |  |  |
| k1 | M3 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6743 | -0.08562 | <.001 | 2.195 | <.001 |  |  |  |  | 4.94e-04 | 0.820 |  |  |  |  |
| k1 | M3 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6729 | -0.0827 | <.001 | 5.498 | <.001 |  |  |  |  | 0.001689 | 0.768 |  |  |  |  |
| k1 | M3 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6573 | -0.069 | 0.002 | 5.071 | <.001 |  |  |  |  | 0.004698 | 0.233 |  |  |  |  |
| k1 | M3 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6497 | -0.1408 | <.001 | 6.709 | <.001 |  |  |  |  | -0.01004 | 0.079 |  |  |  |  |
| k2 | M3 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6217 | -0.1427 | <.001 | 5.579 | <.001 |  |  |  |  | 6.28e-04 | 0.922 |  |  |  |  |
| k2 | M3 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6542 | -0.07275 | 0.007 | 2.115 | <.001 |  |  |  |  | 0.00207 | 0.347 |  |  |  |  |
| k2 | M3 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6552 | -0.07101 | 0.007 | 5.309 | <.001 |  |  |  |  | 0.005351 | 0.370 |  |  |  |  |
| k2 | M3 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6391 | -0.05728 | 0.026 | 4.893 | <.001 |  |  |  |  | 0.00822 | 0.048 |  |  |  |  |
| k2 | M3 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6339 | -0.1274 | <.001 | 6.486 | <.001 |  |  |  |  | -0.005741 | 0.318 |  |  |  |  |
| k3 | M3 | none | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6131 | -0.1362 | <.001 | 5.482 | <.001 |  |  |  |  | 0.00228 | 0.727 |  |  |  |  |
| k3 | M3 | none | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6444 | -0.06723 | 0.017 | 2.077 | <.001 |  |  |  |  | 0.002729 | 0.220 |  |  |  |  |
| k3 | M3 | none | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.646 | -0.06586 | 0.017 | 5.217 | <.001 |  |  |  |  | 0.00703 | 0.252 |  |  |  |  |
| k3 | M3 | none | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6298 | -0.05214 | 0.055 | 4.806 | <.001 |  |  |  |  | 0.009859 | 0.022 |  |  |  |  |
| k3 | M3 | none | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.47e+05 | 21 | 0.6259 | -0.1216 | <.001 | 6.379 | <.001 |  |  |  |  | -0.003787 | 0.515 |  |  |  |  |

### Balanced Bootstrap And Scrambling Robustness

These rows aggregate to child-session-context units. They ask whether the age slope survives equalized age-bin sampling and weakens when true age ordering is broken.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k0 | age_bin_group_scramble | 5 | 5 | 5 | 0.51 | 0.010 |
| k0 | balanced_bootstrap | 5 | 5 | 3 | 1 |  |
| k0 | unit_age_scramble | 5 | 5 | 5 | 0.496 | 0.010 |
| k0 | within_child_age_scramble | 5 | 5 | 5 | 0.318 | 0.010 |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.528 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 0 | 0.998 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.492 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.498 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 5 | 0.524 | 0.020 |
| k2 | balanced_bootstrap | 5 | 5 | 1 | 0.998 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.49 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.494 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 5 | 0.524 | 0.010 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.994 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.46 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.51 | 0.010 |

### Plot Gallery For M3

The repeated plot families were explained once above. In this gallery, read each plot family the same way: x-axis is usually child age, y-axis is predicted or observed total bits, colors usually separate effort values/levels or model variants, facets split effort units/context windows, and ribbons are model-confidence or bootstrap/null intervals depending on the family.

#### M1-M6 context-window fixed-effort atlas plots

![k0_m3_nb_morphemes_fixed_effort_atlas.png / k0 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_morphemes_fixed_effort_atlas.png)
*k0_m3_nb_morphemes_fixed_effort_atlas.png; k0; Morphemes*

![k0_m3_nb_phonemes_fixed_effort_atlas.png / k0 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_phonemes_fixed_effort_atlas.png)
*k0_m3_nb_phonemes_fixed_effort_atlas.png; k0; Phonemes*

![k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k0 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k0; Syllables: CMU/pkg*

![k0_m3_nb_syllables_pkg_fixed_effort_atlas.png / k0 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_pkg_fixed_effort_atlas.png)
*k0_m3_nb_syllables_pkg_fixed_effort_atlas.png; k0; Syllables: pkg*

![k0_m3_nb_words_fixed_effort_atlas.png / k0 / Words](../figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_words_fixed_effort_atlas.png)
*k0_m3_nb_words_fixed_effort_atlas.png; k0; Words*

![k1_m3_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_morphemes_fixed_effort_atlas.png)
*k1_m3_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m3_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_phonemes_fixed_effort_atlas.png)
*k1_m3_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m3_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m3_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m3_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_words_fixed_effort_atlas.png)
*k1_m3_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m3_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_morphemes_fixed_effort_atlas.png)
*k2_m3_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m3_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_phonemes_fixed_effort_atlas.png)
*k2_m3_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m3_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m3_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m3_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_words_fixed_effort_atlas.png)
*k2_m3_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m3_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_morphemes_fixed_effort_atlas.png)
*k3_m3_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m3_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_phonemes_fixed_effort_atlas.png)
*k3_m3_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m3_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m3_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m3_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_words_fixed_effort_atlas.png)
*k3_m3_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m3_expanded_interaction_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m3_expanded_interaction_coefficients.png)
*m3_expanded_interaction_coefficients.png*

![m3_expanded_r2.png](../figs/m1_m2_utterance_information_deep_dive/m3_expanded_r2.png)
*m3_expanded_r2.png*

![m3_gee_gamma_log_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_adjusted_age_lines.png)
*m3_gee_gamma_log_interaction_adjusted_age_lines.png*

![m3_gee_gamma_log_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_interaction_age_lines.png)
*m3_gee_gamma_log_interaction_interaction_age_lines.png*

![m3_gee_gaussian_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_adjusted_age_lines.png)
*m3_gee_gaussian_interaction_adjusted_age_lines.png*

![m3_gee_gaussian_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_interaction_age_lines.png)
*m3_gee_gaussian_interaction_interaction_age_lines.png*

![m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png)
*m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png*

![m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png)
*m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png*

![m3_glm_gamma_log_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_adjusted_age_lines.png)
*m3_glm_gamma_log_interaction_adjusted_age_lines.png*

![m3_glm_gamma_log_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_interaction_age_lines.png)
*m3_glm_gamma_log_interaction_interaction_age_lines.png*

![m3_glm_gaussian_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_adjusted_age_lines.png)
*m3_glm_gaussian_interaction_adjusted_age_lines.png*

![m3_glm_gaussian_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_interaction_age_lines.png)
*m3_glm_gaussian_interaction_interaction_age_lines.png*

![m3_mixed_random_age_slope_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_adjusted_age_lines.png)
*m3_mixed_random_age_slope_interaction_adjusted_age_lines.png*

![m3_mixed_random_age_slope_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_interaction_age_lines.png)
*m3_mixed_random_age_slope_interaction_interaction_age_lines.png*

![m3_mixed_random_intercept_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_adjusted_age_lines.png)
*m3_mixed_random_intercept_interaction_adjusted_age_lines.png*

![m3_mixed_random_intercept_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_interaction_age_lines.png)
*m3_mixed_random_intercept_interaction_interaction_age_lines.png*

![m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png)
*m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png*

![m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png)
*m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png*

![m3_ols_child_fe_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_adjusted_age_lines.png)
*m3_ols_child_fe_interaction_adjusted_age_lines.png*

![m3_ols_child_fe_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png)
*m3_ols_child_fe_interaction_interaction_age_lines.png*

![m3_ols_cluster_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_adjusted_age_lines.png)
*m3_ols_cluster_interaction_adjusted_age_lines.png*

![m3_ols_cluster_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_interaction_age_lines.png)
*m3_ols_cluster_interaction_interaction_age_lines.png*

![m3_ols_interaction_adjusted_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_adjusted_age_lines.png)
*m3_ols_interaction_adjusted_age_lines.png*

![m3_ols_interaction_interaction_age_lines.png](../figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_interaction_age_lines.png)
*m3_ols_interaction_interaction_age_lines.png*

#### M1-M6 continuous versus effort-level plots

![m3_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m3_dual_effort_predictions.png)
*m3_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m3_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m3_nb_morphemes_atlas_bins.png)
*m3_nb_morphemes_atlas_bins.png; Morphemes*

![m3_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m3_nb_phonemes_atlas_bins.png)
*m3_nb_phonemes_atlas_bins.png; Phonemes*

![m3_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m3_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m3_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_pkg_atlas_bins.png)
*m3_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m3_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m3_nb_words_atlas_bins.png)
*m3_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m3_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m3_granular_primary_fixed_effort_slices.png)
*m3_granular_primary_fixed_effort_slices.png*

![m3_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m3_marginal_adjusted_global_trends.png)
*m3_marginal_adjusted_global_trends.png*

![m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m3_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m3_top_frequency_12_fixed_effort_slices.png)
*m3_top_frequency_12_fixed_effort_slices.png*

![m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m3_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m3_age_slope_robustness_intervals.png)
*m3_age_slope_robustness_intervals.png*

![m3_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png)
*m3_clear_robustness_regression_lines.png*



## M4: Context predictor added

M4 adds the current context predictor. This is a robustness check for the utterance-information claim, not the final context-efficiency model. The current entropy feature is next-token entropy, so it only partly represents the uncertainty of a full possible response.

Computed atlas summary: continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 100% negative age slopes; context-window atlas age signs: 45 negative, 0 positive across 45 rows; robustness outside-null share: 80%.

### Formula, Estimator, And Child Structure

| item | value |
| --- | --- |
| scientific question | Does context entropy, matched context size, or both explain total information beyond age, target effort, and child identity? |
| readable formula | sum_bits ~ age + effort + context predictor + child identity |
| actual centered implementation | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |
| primary estimator/library | ordinary linear regression / OLS via statsmodels.formula.api.ols |
| child identity role | fixed intercept through C(child_id); GEE rows cluster by child |
| evidence role | Context-control robustness. |

### Coefficient Dictionary

| term | plain-language meaning |
| --- | --- |
| age | Expected change in total target bits for one additional month, after this model's controls. |
| effort | Expected change in total bits for one more word/morpheme/syllable/phoneme in that model row. |
| age x effort | Whether the developmental age slope is different for shorter versus longer utterances. |
| context entropy | Association between current next-token context uncertainty and total bits in the produced target. |
| age x context entropy | Whether the context-entropy association changes as children get older. |
| effort x context entropy | Whether the effort slope differs in more uncertain versus less uncertain contexts. |
| effort level | Low/mid/high bins of one effort unit. These are diagnostics, not a replacement for exact fixed-effort control. |

Age effects in this family should be read in bits per month. Effort effects should be read in bits per one additional effort unit. Interaction terms should be read as slope changes, not as standalone main effects.

### Scientific Interpretation

Primary continuous-effort sign summary: 5 negative, 0 positive, and 0 exactly zero coefficients across 5 saved rows.

Supervisor-facing cherry-pick: Use to say that adding the current next-token entropy predictor does not remove the M2-like age result.

What not to overclaim: Do not treat next-token entropy as full response uncertainty.


### Primary Continuous-Effort Rows

These rows are the clearest exact-effort versions for this model family. They keep words, morphemes, syllables, and phonemes in separate models to avoid collinearity.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  | fit |

### Continuous Versus Low/Mid/High Effort Rows

Use these as a strategy comparison. The continuous rows control exact effort; the effort-level rows ask a coarser question about low, middle, and high effort categories.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  | fit |
| continuous | Morphemes | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  | fit |
| continuous | Syllables: pkg | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  | fit |
| continuous | Phonemes | sum_bits ~ age + effort + context_entropy + child identity | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  | fit |
| effort_level | Words | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4363 | 0.0829 | <.001 |  |  | -0.4785 | <.001 |  |  |  |  | fit |
| effort_level | Morphemes | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4072 | 0.1197 | <.001 |  |  | -0.5201 | <.001 |  |  |  |  | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4639 | 0.07374 | 0.005 |  |  | -0.5254 | <.001 |  |  |  |  | fit |
| effort_level | Syllables: pkg | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4407 | 0.1106 | <.001 |  |  | -0.5295 | <.001 |  |  |  |  | fit |
| effort_level | Phonemes | sum_bits ~ age + effort_level + context_entropy + child identity | 4.414e+05 | 21 | 0.4633 | 0.08804 | <.001 |  |  | -0.5842 | <.001 |  |  |  |  | fit |

### M4 Context Deep-Dive Rows

These rows are useful for separating estimator sensitivity from the context-predictor question.

| model_id | model_label | fit_type | effort_label | formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | entropy_coef | entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4a | M4a: child FE + context entropy | ols_cluster | Words | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6266 | -0.1269 | 3.29e-05 | -0.4716 | 8.14e-37 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Words | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.6098 | -0.1268 | 2.09e-05 | -0.4715 | 1.44e-38 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Words | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -1.784e+07 | -0.005747 | 2.69e-05 | -0.01973 | 7.33e-38 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Words | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6266 | -0.1276 | 4.34e-05 | -0.4704 | 2.15e-41 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Words | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6266 | -0.1264 | 3.94e-05 | -0.4715 | 7.49e-37 | fit |
| M4a | M4a: child FE + context entropy | ols_cluster | Morphemes | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6136 | -0.1401 | 1.92e-04 | -0.5123 | 4.22e-43 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Morphemes | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.5932 | -0.14 | 1.32e-04 | -0.5122 | 3.60e-45 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Morphemes | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -1.232e+10 | -0.006534 | 3.96e-05 | -0.02081 | 9.37e-42 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Morphemes | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6136 | -0.1406 | 2.31e-04 | -0.5113 | 1.78e-47 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Morphemes | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6136 | -0.1409 | 3.05e-04 | -0.5123 | 4.67e-43 | fit |
| M4a | M4a: child FE + context entropy | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.01333 | -0.5398 | 7.26e-57 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Syllables: CMU/pkg | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.6322 | -0.06438 | 0.01121 | -0.5398 | 1.29e-59 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Syllables: CMU/pkg | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -2.542e+07 | -0.004073 | 6.70e-04 | -0.0216 | 2.05e-46 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6468 | -0.06492 | 0.01498 | -0.5391 | 1.57e-62 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6469 | -0.06733 | 0.01494 | -0.5399 | 1.70e-56 | fit |
| M4a | M4a: child FE + context entropy | ols_cluster | Syllables: pkg | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.03841 | -0.541 | 2.56e-59 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Syllables: pkg | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.6149 | -0.04795 | 0.03389 | -0.541 | 3.43e-62 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Syllables: pkg | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -4.219e+06 | -0.003548 | 0.002013 | -0.0215 | 6.06e-47 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Syllables: pkg | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6304 | -0.04848 | 0.04219 | -0.5403 | 2.20e-65 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Syllables: pkg | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6307 | -0.0519 | 0.04986 | -0.541 | 5.99e-59 | fit |
| M4a | M4a: child FE + context entropy | ols_cluster | Phonemes | sum_bits ~ age_c + effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.01283 | -0.5814 | 3.34e-70 | fit |
| M4b | M4b: GEE + context entropy | gee_gaussian | Phonemes | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | 0.6287 | -0.06508 | 0.01079 | -0.5814 | 1.33e-73 | fit |
| M4c | M4c: Gamma/log GEE + context entropy | gee_gamma_log | Phonemes | sum_bits ~ age_c + effort_c + context_entropy_c | 4.414e+05 | 21 | -1.394e+11 | -0.004539 | 1.48e-04 | -0.02295 | 1.27e-51 | fit |
| M4d | M4d: age by context entropy + child FE | ols_cluster | Phonemes | sum_bits ~ age_c * context_entropy_c + effort_c + C(child_id) | 4.414e+05 | 21 | 0.6453 | -0.06571 | 0.01437 | -0.5805 | 4.07e-81 | fit |
| M4e | M4e: M3 plus context entropy + child FE | ols_cluster | Phonemes | sum_bits ~ age_c * effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6454 | -0.06773 | 0.01781 | -0.5812 | 9.05e-70 | fit |

### Context-Window Atlas Rows

These rows repeat the model logic over k0-k3 and, for M4-M6, over entropy, context-size, and entropy-plus-size variants. The purpose is context robustness.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M4E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M4S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6388 | -0.1636 | <.001 | 5.773 | <.001 | 0.06736 | 0.206 |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6743 | -0.08687 | <.001 | 2.196 | <.001 | 0.02783 | 0.548 |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6728 | -0.08435 | <.001 | 5.502 | <.001 | 0.06356 | 0.204 |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6571 | -0.06823 | <.001 | 5.083 | <.001 | 0.04786 | 0.346 |  |  |  |  |  |  |  |  |
| k1 | M4E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6495 | -0.1481 | <.001 | 6.68 | <.001 | 0.05917 | 0.274 |  |  |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6397 | -0.1576 | <.001 | 5.772 | <.001 | -0.0464 | 0.357 | -0.1462 | <.001 |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6751 | -0.08125 | <.001 | 2.195 | <.001 | -0.06489 | 0.143 | -0.04865 | <.001 |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6737 | -0.07842 | <.001 | 5.501 | <.001 | -0.03417 | 0.477 | -0.1285 | <.001 |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.658 | -0.06222 | 0.002 | 5.081 | <.001 | -0.05367 | 0.281 | -0.1244 | <.001 |  |  |  |  |  |  |
| k1 | M4ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6506 | -0.1414 | <.001 | 6.679 | <.001 | -0.06001 | 0.247 | -0.1813 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6403 | -0.1562 | <.001 | 5.767 | <.001 |  |  | -0.1421 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6755 | -0.08311 | <.001 | 2.194 | <.001 |  |  | -0.04665 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6741 | -0.07966 | <.001 | 5.497 | <.001 |  |  | -0.1263 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6585 | -0.06479 | 0.002 | 5.078 | <.001 |  |  | -0.1208 | <.001 |  |  |  |  |  |  |
| k1 | M4S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.651 | -0.1402 | <.001 | 6.671 | <.001 |  |  | -0.175 | <.001 |  |  |  |  |  |  |
| k2 | M4E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.622 | -0.1458 | <.001 | 5.582 | <.001 | -0.4256 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6549 | -0.06995 | 0.006 | 2.12 | <.001 | -0.4942 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6557 | -0.06891 | 0.006 | 5.324 | <.001 | -0.4558 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6396 | -0.05248 | 0.017 | 4.913 | <.001 | -0.4543 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6343 | -0.1318 | <.001 | 6.47 | <.001 | -0.4107 | <.001 |  |  |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6223 | -0.142 | <.001 | 5.582 | <.001 | -0.4253 | <.001 | -0.05438 | <.001 |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6551 | -0.0665 | 0.008 | 2.12 | <.001 | -0.4898 | <.001 | -0.01751 | <.001 |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.656 | -0.06519 | 0.009 | 5.324 | <.001 | -0.4521 | <.001 | -0.04709 | <.001 |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6399 | -0.04875 | 0.027 | 4.913 | <.001 | -0.4506 | <.001 | -0.04487 | <.001 |  |  |  |  |  |  |
| k2 | M4ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6347 | -0.1273 | <.001 | 6.47 | <.001 | -0.4087 | <.001 | -0.06994 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6227 | -0.1433 | <.001 | 5.577 | <.001 |  |  | -0.05554 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6552 | -0.0717 | 0.005 | 2.118 | <.001 |  |  | -0.01841 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6561 | -0.06963 | 0.007 | 5.319 | <.001 |  |  | -0.04898 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.64 | -0.05479 | 0.021 | 4.909 | <.001 |  |  | -0.04671 | <.001 |  |  |  |  |  |  |
| k2 | M4S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.635 | -0.1289 | <.001 | 6.464 | <.001 |  |  | -0.07164 | <.001 |  |  |  |  |  |  |
| k3 | M4E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6138 | -0.1369 | <.001 | 5.489 | <.001 | -0.5111 | <.001 | -0.03298 | <.001 |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6455 | -0.06221 | 0.016 | 2.084 | <.001 | -0.577 | <.001 | -0.0106 | <.001 |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6469 | -0.06126 | 0.018 | 5.235 | <.001 | -0.5362 | <.001 | -0.02838 | <.001 |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6306 | -0.04483 | 0.052 | 4.829 | <.001 | -0.537 | <.001 | -0.02722 | <.001 |  |  |  |  |  |  |
| k3 | M4ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6268 | -0.123 | <.001 | 6.368 | <.001 | -0.4699 | <.001 | -0.0427 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6142 | -0.1375 | <.001 | 5.485 | <.001 |  |  | -0.03407 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6455 | -0.06667 | 0.013 | 2.082 | <.001 |  |  | -0.01139 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6471 | -0.06497 | 0.016 | 5.232 | <.001 |  |  | -0.02985 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6308 | -0.05014 | 0.044 | 4.827 | <.001 |  |  | -0.0288 | <.001 |  |  |  |  |  |  |
| k3 | M4S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6272 | -0.1239 | <.001 | 6.363 | <.001 |  |  | -0.04386 | <.001 |  |  |  |  |  |  |

### Balanced Bootstrap And Scrambling Robustness

These rows aggregate to child-session-context units. They ask whether the age slope survives equalized age-bin sampling and weakens when true age ordering is broken.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.552 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 3 | 1 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.498 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.516 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 5 | 0.48 | 0.010 |
| k2 | balanced_bootstrap | 5 | 5 | 1 | 0.998 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.542 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.51 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 4 | 0.53 | 0.040 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.944 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.49 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.468 | 0.010 |

### Plot Gallery For M4

The repeated plot families were explained once above. In this gallery, read each plot family the same way: x-axis is usually child age, y-axis is predicted or observed total bits, colors usually separate effort values/levels or model variants, facets split effort units/context windows, and ribbons are model-confidence or bootstrap/null intervals depending on the family.

#### M1-M6 context-window fixed-effort atlas plots

![k1_m4e_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_morphemes_fixed_effort_atlas.png)
*k1_m4e_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m4e_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_phonemes_fixed_effort_atlas.png)
*k1_m4e_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m4e_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_words_fixed_effort_atlas.png)
*k1_m4e_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m4es_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_morphemes_fixed_effort_atlas.png)
*k1_m4es_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m4es_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_phonemes_fixed_effort_atlas.png)
*k1_m4es_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m4es_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_words_fixed_effort_atlas.png)
*k1_m4es_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m4s_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_morphemes_fixed_effort_atlas.png)
*k1_m4s_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m4s_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_phonemes_fixed_effort_atlas.png)
*k1_m4s_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m4s_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_words_fixed_effort_atlas.png)
*k1_m4s_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m4e_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_morphemes_fixed_effort_atlas.png)
*k2_m4e_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m4e_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_phonemes_fixed_effort_atlas.png)
*k2_m4e_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m4e_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_words_fixed_effort_atlas.png)
*k2_m4e_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m4es_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_morphemes_fixed_effort_atlas.png)
*k2_m4es_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m4es_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_phonemes_fixed_effort_atlas.png)
*k2_m4es_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m4es_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_words_fixed_effort_atlas.png)
*k2_m4es_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m4s_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_morphemes_fixed_effort_atlas.png)
*k2_m4s_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m4s_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_phonemes_fixed_effort_atlas.png)
*k2_m4s_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m4s_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_words_fixed_effort_atlas.png)
*k2_m4s_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m4e_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_morphemes_fixed_effort_atlas.png)
*k3_m4e_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m4e_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_phonemes_fixed_effort_atlas.png)
*k3_m4e_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m4e_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_words_fixed_effort_atlas.png)
*k3_m4e_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m4es_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_morphemes_fixed_effort_atlas.png)
*k3_m4es_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m4es_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_phonemes_fixed_effort_atlas.png)
*k3_m4es_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m4es_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_words_fixed_effort_atlas.png)
*k3_m4es_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m4s_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_morphemes_fixed_effort_atlas.png)
*k3_m4s_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m4s_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_phonemes_fixed_effort_atlas.png)
*k3_m4s_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m4s_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_words_fixed_effort_atlas.png)
*k3_m4s_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m4_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.png)
*m4_context_entropy_adjusted_predictions.png*

![m4_context_entropy_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_coefficients.png)
*m4_context_entropy_coefficients.png*

![m4_context_entropy_descriptive_bins.png](../figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_descriptive_bins.png)
*m4_context_entropy_descriptive_bins.png*

![m4_effort_quantile_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_effort_quantile_adjusted_predictions.png)
*m4_effort_quantile_adjusted_predictions.png*

![m4_m4a_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4a_context_entropy_adjusted_predictions.png)
*m4_m4a_context_entropy_adjusted_predictions.png*

![m4_m4b_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4b_context_entropy_adjusted_predictions.png)
*m4_m4b_context_entropy_adjusted_predictions.png*

![m4_m4c_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4c_context_entropy_adjusted_predictions.png)
*m4_m4c_context_entropy_adjusted_predictions.png*

![m4_m4d_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4d_context_entropy_adjusted_predictions.png)
*m4_m4d_context_entropy_adjusted_predictions.png*

![m4_m4e_context_entropy_adjusted_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m4_m4e_context_entropy_adjusted_predictions.png)
*m4_m4e_context_entropy_adjusted_predictions.png*

#### M1-M6 continuous versus effort-level plots

![m4_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m4_dual_effort_predictions.png)
*m4_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m4_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m4_nb_morphemes_atlas_bins.png)
*m4_nb_morphemes_atlas_bins.png; Morphemes*

![m4_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m4_nb_phonemes_atlas_bins.png)
*m4_nb_phonemes_atlas_bins.png; Phonemes*

![m4_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m4_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m4_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_pkg_atlas_bins.png)
*m4_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m4_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m4_nb_words_atlas_bins.png)
*m4_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m4_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m4_granular_primary_fixed_effort_slices.png)
*m4_granular_primary_fixed_effort_slices.png*

![m4_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m4_marginal_adjusted_global_trends.png)
*m4_marginal_adjusted_global_trends.png*

![m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m4_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m4_top_frequency_12_fixed_effort_slices.png)
*m4_top_frequency_12_fixed_effort_slices.png*

![m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m4_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m4_age_slope_robustness_intervals.png)
*m4_age_slope_robustness_intervals.png*

![m4_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m4_clear_robustness_regression_lines.png)
*m4_clear_robustness_regression_lines.png*



## M5: Age by context predictor

M5 asks whether the relation between context entropy and target information changes with age. This is a developmental context-sensitivity question, but the current next-token entropy results should be treated as exploratory.

Computed atlas summary: continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 100% negative age slopes; context-window atlas age signs: 45 negative, 0 positive across 45 rows; robustness outside-null share: 72%.

### Formula, Estimator, And Child Structure

| item | value |
| --- | --- |
| scientific question | Does the context-predictor association itself change with age? |
| readable formula | sum_bits ~ age * context predictor + effort + child identity |
| actual centered implementation | sum_bits ~ age_c * context_entropy_c + target_effort_c + C(child_id) |
| primary estimator/library | ordinary linear regression / OLS via statsmodels.formula.api.ols |
| child identity role | fixed intercept through C(child_id) |
| evidence role | Exploratory context-age interaction. |

### Coefficient Dictionary

| term | plain-language meaning |
| --- | --- |
| age | Expected change in total target bits for one additional month, after this model's controls. |
| effort | Expected change in total bits for one more word/morpheme/syllable/phoneme in that model row. |
| age x effort | Whether the developmental age slope is different for shorter versus longer utterances. |
| context entropy | Association between current next-token context uncertainty and total bits in the produced target. |
| age x context entropy | Whether the context-entropy association changes as children get older. |
| effort x context entropy | Whether the effort slope differs in more uncertain versus less uncertain contexts. |
| effort level | Low/mid/high bins of one effort unit. These are diagnostics, not a replacement for exact fixed-effort control. |

Age effects in this family should be read in bits per month. Effort effects should be read in bits per one additional effort unit. Interaction terms should be read as slope changes, not as standalone main effects.

### Scientific Interpretation

Primary continuous-effort sign summary: 5 negative, 0 positive, and 0 exactly zero coefficients across 5 saved rows.

Supervisor-facing cherry-pick: Usually omit from supervisor draft unless discussing why response-level entropy is needed next.

What not to overclaim: Do not claim developmental context sensitivity from weak or unstable age-by-entropy terms.


### Primary Continuous-Effort Rows

These rows are the clearest exact-effort versions for this model family. They keep words, morphemes, syllables, and phonemes in separate models to avoid collinearity.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 |  |  | 0.006141 | 0.284 | fit |
| continuous | Morphemes | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 |  |  | 0.004709 | 0.339 | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 |  |  | 0.003955 | 0.478 | fit |
| continuous | Syllables: pkg | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 |  |  | 0.003946 | 0.481 | fit |
| continuous | Phonemes | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 |  |  | 0.00465 | 0.407 | fit |

### Continuous Versus Low/Mid/High Effort Rows

Use these as a strategy comparison. The continuous rows control exact effort; the effort-level rows ask a coarser question about low, middle, and high effort categories.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 |  |  | 0.006141 | 0.284 | fit |
| continuous | Morphemes | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 |  |  | 0.004709 | 0.339 | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 |  |  | 0.003955 | 0.478 | fit |
| continuous | Syllables: pkg | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 |  |  | 0.003946 | 0.481 | fit |
| continuous | Phonemes | sum_bits ~ age * context_entropy + effort + child identity | 4.414e+05 | 21 | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 |  |  | 0.00465 | 0.407 | fit |
| effort_level | Words | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.4364 | 0.08125 | <.001 |  |  | -0.4758 | <.001 |  |  | 0.01401 | 0.047 | fit |
| effort_level | Morphemes | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.4073 | 0.1181 | <.001 |  |  | -0.5173 | <.001 |  |  | 0.01404 | 0.032 | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.464 | 0.07276 | 0.006 |  |  | -0.5237 | <.001 |  |  | 0.008394 | 0.244 | fit |
| effort_level | Syllables: pkg | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.4407 | 0.1096 | <.001 |  |  | -0.5279 | <.001 |  |  | 0.008078 | 0.237 | fit |
| effort_level | Phonemes | sum_bits ~ age * context_entropy + effort_level + child identity | 4.414e+05 | 21 | 0.4633 | 0.08694 | <.001 |  |  | -0.5823 | <.001 |  |  | 0.009479 | 0.207 | fit |

### Earlier Effort-Level Context Rows

These are exploratory rows from the effort-level context model pass. They are useful for stress testing but less clean than exact fixed-effort slices.

| model_id | model_label | fit_type | effort_label | formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Words | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4363 | 0.0829 | 4.12e-06 | -0.4785 | 2.42e-32 | fit |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Morphemes | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4072 | 0.1197 | 1.99e-08 | -0.5201 | 1.39e-35 | fit |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4639 | 0.07374 | 0.005428 | -0.5254 | 6.13e-59 | fit |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Syllables: pkg | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4407 | 0.1106 | 3.43e-06 | -0.5295 | 5.81e-56 | fit |
| M5 | M5: context entropy + effort level + child FE | ols_cluster | Phonemes | sum_bits ~ age_c + context_entropy_c + C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4633 | 0.08804 | 8.51e-04 | -0.5842 | 5.07e-59 | fit |

### Context-Window Atlas Rows

These rows repeat the model logic over k0-k3 and, for M4-M6, over entropy, context-size, and entropy-plus-size variants. The purpose is context robustness.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M5E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M5S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M5E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6389 | -0.1647 | <.001 | 5.772 | <.001 | 0.07772 | 0.230 |  |  |  |  | 0.01791 | 0.005 |  |  |
| k1 | M5E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6744 | -0.08788 | <.001 | 2.196 | <.001 | 0.03693 | 0.502 |  |  |  |  | 0.01573 | 0.002 |  |  |
| k1 | M5E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6729 | -0.08541 | <.001 | 5.502 | <.001 | 0.07299 | 0.219 |  |  |  |  | 0.0163 | 0.002 |  |  |
| k1 | M5E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6572 | -0.06928 | <.001 | 5.082 | <.001 | 0.05728 | 0.331 |  |  |  |  | 0.01629 | <.001 |  |  |
| k1 | M5E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6496 | -0.1491 | <.001 | 6.68 | <.001 | 0.06788 | 0.288 |  |  |  |  | 0.01505 | 0.018 |  |  |
| k1 | M5ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6399 | -0.1584 | <.001 | 5.772 | <.001 | -0.03454 | 0.558 | -0.1459 | <.001 |  |  | 0.0173 | <.001 | -0.002025 | 0.247 |
| k1 | M5ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6752 | -0.0821 | <.001 | 2.195 | <.001 | -0.05507 | 0.273 | -0.04867 | <.001 |  |  | 0.01587 | <.001 | -3.34e-04 | 0.624 |
| k1 | M5ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6738 | -0.07929 | <.001 | 5.501 | <.001 | -0.0241 | 0.661 | -0.1286 | <.001 |  |  | 0.0164 | <.001 | -8.26e-04 | 0.669 |
| k1 | M5ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6581 | -0.0631 | 0.001 | 5.081 | <.001 | -0.04358 | 0.428 | -0.1245 | <.001 |  |  | 0.01639 | <.001 | -8.06e-04 | 0.648 |
| k1 | M5ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6507 | -0.1421 | <.001 | 6.679 | <.001 | -0.05053 | 0.396 | -0.1811 | <.001 |  |  | 0.01498 | 0.003 | -0.001203 | 0.624 |
| k1 | M5S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6403 | -0.1553 | <.001 | 5.766 | <.001 |  |  | -0.1408 | <.001 |  |  |  |  | -0.002978 | 0.156 |
| k1 | M5S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6755 | -0.08255 | <.001 | 2.193 | <.001 |  |  | -0.04623 | <.001 |  |  |  |  | -6.97e-04 | 0.338 |
| k1 | M5S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6741 | -0.07905 | <.001 | 5.496 | <.001 |  |  | -0.1253 | <.001 |  |  |  |  | -0.001844 | 0.347 |
| k1 | M5S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6585 | -0.06415 | 0.003 | 5.077 | <.001 |  |  | -0.1198 | <.001 |  |  |  |  | -0.001897 | 0.269 |
| k1 | M5S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.651 | -0.1396 | <.001 | 6.671 | <.001 |  |  | -0.174 | <.001 |  |  |  |  | -0.002223 | 0.401 |
| k2 | M5E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.622 | -0.1469 | <.001 | 5.582 | <.001 | -0.423 | <.001 |  |  |  |  | 0.01127 | <.001 |  |  |
| k2 | M5E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6549 | -0.07082 | 0.005 | 2.121 | <.001 | -0.492 | <.001 |  |  |  |  | 0.009362 | 0.002 |  |  |
| k2 | M5E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6557 | -0.06976 | 0.005 | 5.324 | <.001 | -0.4537 | <.001 |  |  |  |  | 0.009102 | 0.003 |  |  |
| k2 | M5E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6396 | -0.0533 | 0.016 | 4.913 | <.001 | -0.4522 | <.001 |  |  |  |  | 0.008871 | 0.003 |  |  |
| k2 | M5E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6343 | -0.1327 | <.001 | 6.47 | <.001 | -0.4085 | <.001 |  |  |  |  | 0.009403 | <.001 |  |  |
| k2 | M5ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6224 | -0.1411 | <.001 | 5.581 | <.001 | -0.4216 | <.001 | -0.05295 | <.001 |  |  | 0.01227 | <.001 | -0.004267 | 0.009 |
| k2 | M5ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6552 | -0.06565 | 0.009 | 2.12 | <.001 | -0.4861 | <.001 | -0.01697 | <.001 |  |  | 0.01074 | <.001 | -0.001234 | 0.009 |
| k2 | M5ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6561 | -0.06422 | 0.010 | 5.323 | <.001 | -0.4485 | <.001 | -0.04591 | <.001 |  |  | 0.01044 | <.001 | -0.003029 | 0.014 |
| k2 | M5ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.64 | -0.04782 | 0.031 | 4.912 | <.001 | -0.447 | <.001 | -0.04373 | <.001 |  |  | 0.0102 | <.001 | -0.002896 | 0.015 |
| k2 | M5ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6348 | -0.1263 | <.001 | 6.47 | <.001 | -0.405 | <.001 | -0.0683 | <.001 |  |  | 0.01073 | <.001 | -0.004204 | 0.019 |
| k2 | M5S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6228 | -0.1409 | <.001 | 5.576 | <.001 |  |  | -0.0541 | <.001 |  |  |  |  | -0.00417 | 0.010 |
| k2 | M5S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6552 | -0.06955 | 0.007 | 2.118 | <.001 |  |  | -0.01782 | <.001 |  |  |  |  | -0.001223 | 0.009 |
| k2 | M5S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6562 | -0.06748 | 0.009 | 5.318 | <.001 |  |  | -0.0477 | <.001 |  |  |  |  | -0.003028 | 0.011 |
| k2 | M5S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6401 | -0.05265 | 0.025 | 4.909 | <.001 |  |  | -0.04546 | <.001 |  |  |  |  | -0.002931 | 0.011 |
| k2 | M5S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6351 | -0.1266 | <.001 | 6.463 | <.001 |  |  | -0.0699 | <.001 |  |  |  |  | -0.004125 | 0.017 |
| k3 | M5E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 |  |  |  |  | 0.004709 | 0.339 |  |  |
| k3 | M5E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 |  |  |  |  | 0.00465 | 0.407 |  |  |
| k3 | M5E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 |  |  |  |  | 0.003955 | 0.478 |  |  |
| k3 | M5E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 |  |  |  |  | 0.003946 | 0.481 |  |  |
| k3 | M5E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 |  |  |  |  | 0.006141 | 0.284 |  |  |
| k3 | M5ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.614 | -0.1347 | <.001 | 5.488 | <.001 | -0.51 | <.001 | -0.0319 | <.001 |  |  | 0.005694 | 0.244 | -0.003641 | 0.006 |
| k3 | M5ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6456 | -0.06036 | 0.024 | 2.084 | <.001 | -0.5753 | <.001 | -0.01013 | <.001 |  |  | 0.006003 | 0.281 | -0.001034 | 0.005 |
| k3 | M5ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.647 | -0.05921 | 0.026 | 5.234 | <.001 | -0.5345 | <.001 | -0.02733 | <.001 |  |  | 0.005245 | 0.346 | -0.002541 | 0.007 |
| k3 | M5ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6307 | -0.04287 | 0.071 | 4.828 | <.001 | -0.5354 | <.001 | -0.02626 | <.001 |  |  | 0.005242 | 0.343 | -0.002424 | 0.006 |
| k3 | M5ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6269 | -0.121 | <.001 | 6.367 | <.001 | -0.4679 | <.001 | -0.04139 | <.001 |  |  | 0.00728 | 0.202 | -0.003595 | 0.010 |
| k3 | M5S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6144 | -0.1345 | <.001 | 5.484 | <.001 |  |  | -0.03311 | <.001 |  |  |  |  | -0.003561 | 0.006 |
| k3 | M5S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6457 | -0.06397 | 0.017 | 2.082 | <.001 |  |  | -0.01094 | <.001 |  |  |  |  | -0.001031 | 0.006 |
| k3 | M5S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6472 | -0.06226 | 0.022 | 5.231 | <.001 |  |  | -0.02888 | <.001 |  |  |  |  | -0.00253 | 0.006 |
| k3 | M5S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6309 | -0.04746 | 0.056 | 4.826 | <.001 |  |  | -0.02789 | <.001 |  |  |  |  | -0.002428 | 0.006 |
| k3 | M5S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6274 | -0.121 | <.001 | 6.362 | <.001 |  |  | -0.04263 | <.001 |  |  |  |  | -0.003511 | 0.009 |

### Balanced Bootstrap And Scrambling Robustness

These rows aggregate to child-session-context units. They ask whether the age slope survives equalized age-bin sampling and weakens when true age ordering is broken.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.528 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 1 | 1 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.496 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.518 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 3 | 0.536 | 0.040 |
| k2 | balanced_bootstrap | 5 | 5 | 1 | 1 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.51 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.424 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 3 | 0.488 | 0.059 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.908 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.486 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.326 | 0.020 |

### Plot Gallery For M5

The repeated plot families were explained once above. In this gallery, read each plot family the same way: x-axis is usually child age, y-axis is predicted or observed total bits, colors usually separate effort values/levels or model variants, facets split effort units/context windows, and ribbons are model-confidence or bootstrap/null intervals depending on the family.

#### M1-M6 context-window fixed-effort atlas plots

![k1_m5e_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_morphemes_fixed_effort_atlas.png)
*k1_m5e_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m5e_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_phonemes_fixed_effort_atlas.png)
*k1_m5e_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m5e_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_words_fixed_effort_atlas.png)
*k1_m5e_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m5es_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_morphemes_fixed_effort_atlas.png)
*k1_m5es_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m5es_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_phonemes_fixed_effort_atlas.png)
*k1_m5es_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m5es_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_words_fixed_effort_atlas.png)
*k1_m5es_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m5s_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_morphemes_fixed_effort_atlas.png)
*k1_m5s_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m5s_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_phonemes_fixed_effort_atlas.png)
*k1_m5s_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m5s_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_words_fixed_effort_atlas.png)
*k1_m5s_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m5e_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_morphemes_fixed_effort_atlas.png)
*k2_m5e_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m5e_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_phonemes_fixed_effort_atlas.png)
*k2_m5e_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m5e_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_words_fixed_effort_atlas.png)
*k2_m5e_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m5es_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_morphemes_fixed_effort_atlas.png)
*k2_m5es_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m5es_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_phonemes_fixed_effort_atlas.png)
*k2_m5es_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m5es_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_words_fixed_effort_atlas.png)
*k2_m5es_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m5s_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_morphemes_fixed_effort_atlas.png)
*k2_m5s_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m5s_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_phonemes_fixed_effort_atlas.png)
*k2_m5s_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m5s_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_words_fixed_effort_atlas.png)
*k2_m5s_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m5e_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_morphemes_fixed_effort_atlas.png)
*k3_m5e_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m5e_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_phonemes_fixed_effort_atlas.png)
*k3_m5e_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m5e_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_words_fixed_effort_atlas.png)
*k3_m5e_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m5es_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_morphemes_fixed_effort_atlas.png)
*k3_m5es_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m5es_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_phonemes_fixed_effort_atlas.png)
*k3_m5es_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m5es_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_words_fixed_effort_atlas.png)
*k3_m5es_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m5s_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_morphemes_fixed_effort_atlas.png)
*k3_m5s_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m5s_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_phonemes_fixed_effort_atlas.png)
*k3_m5s_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m5s_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_words_fixed_effort_atlas.png)
*k3_m5s_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m5_effort_level_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_effort_level_adjusted_age_predictions.png)
*m5_effort_level_adjusted_age_predictions.png*

![m5_m6_effort_level_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_adjusted_age_predictions.png)
*m5_m6_effort_level_adjusted_age_predictions.png*

![m5_m6_effort_level_average_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_average_age_predictions.png)
*m5_m6_effort_level_average_age_predictions.png*

![m5_m6_saturated_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.png)
*m5_m6_saturated_adjusted_age_predictions.png*

![m5_m6_saturated_selected_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png)
*m5_m6_saturated_selected_coefficients.png*

#### M1-M6 continuous versus effort-level plots

![m5_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m5_dual_effort_predictions.png)
*m5_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m5_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m5_nb_morphemes_atlas_bins.png)
*m5_nb_morphemes_atlas_bins.png; Morphemes*

![m5_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m5_nb_phonemes_atlas_bins.png)
*m5_nb_phonemes_atlas_bins.png; Phonemes*

![m5_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m5_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m5_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_pkg_atlas_bins.png)
*m5_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m5_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m5_nb_words_atlas_bins.png)
*m5_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m5_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m5_granular_primary_fixed_effort_slices.png)
*m5_granular_primary_fixed_effort_slices.png*

![m5_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m5_marginal_adjusted_global_trends.png)
*m5_marginal_adjusted_global_trends.png*

![m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m5_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m5_top_frequency_12_fixed_effort_slices.png)
*m5_top_frequency_12_fixed_effort_slices.png*

![m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m5_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m5_age_slope_robustness_intervals.png)
*m5_age_slope_robustness_intervals.png*

![m5_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m5_clear_robustness_regression_lines.png)
*m5_clear_robustness_regression_lines.png*



## M6: Interaction-rich stress test

M6 is a stress test with multiple interactions. It is useful if the M2 pattern survives it, but it is not the simplest explanation because the terms are highly conditional and collinearity can make single coefficients fragile.

Computed atlas summary: continuous-effort age signs: 5 negative, 0 positive across 5 effort units; fixed-effort slices: 90% negative age slopes; context-window atlas age signs: 45 negative, 0 positive across 45 rows; robustness outside-null share: 75%.

### Formula, Estimator, And Child Structure

| item | value |
| --- | --- |
| scientific question | Do age, target effort, and context predictors interact when predicting total information? |
| readable formula | sum_bits ~ age * effort + age * context + effort * context + child identity |
| actual centered implementation | sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id) |
| primary estimator/library | ordinary linear regression / OLS via statsmodels.formula.api.ols |
| child identity role | fixed intercept through C(child_id) |
| evidence role | Interaction-rich stress test. |

### Coefficient Dictionary

| term | plain-language meaning |
| --- | --- |
| age | Expected change in total target bits for one additional month, after this model's controls. |
| effort | Expected change in total bits for one more word/morpheme/syllable/phoneme in that model row. |
| age x effort | Whether the developmental age slope is different for shorter versus longer utterances. |
| context entropy | Association between current next-token context uncertainty and total bits in the produced target. |
| age x context entropy | Whether the context-entropy association changes as children get older. |
| effort x context entropy | Whether the effort slope differs in more uncertain versus less uncertain contexts. |
| effort level | Low/mid/high bins of one effort unit. These are diagnostics, not a replacement for exact fixed-effort control. |

Age effects in this family should be read in bits per month. Effort effects should be read in bits per one additional effort unit. Interaction terms should be read as slope changes, not as standalone main effects.

### Scientific Interpretation

Primary continuous-effort sign summary: 5 negative, 0 positive, and 0 exactly zero coefficients across 5 saved rows.

Supervisor-facing cherry-pick: Use as an appendix stress test if the simpler result is challenged.

What not to overclaim: Do not interpret one coefficient from the saturated model as a clean standalone effect.


### Primary Continuous-Effort Rows

These rows are the clearest exact-effort versions for this model family. They keep words, morphemes, syllables, and phonemes in separate models to avoid collinearity.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6266 | -0.1273 | <.001 | 6.376 | <.001 | -0.4729 | <.001 | -0.002441 | 0.726 | 0.009085 | 0.111 | fit |
| continuous | Morphemes | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6137 | -0.1417 | <.001 | 5.479 | <.001 | -0.5165 | <.001 | 0.003897 | 0.575 | 0.009103 | 0.070 | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6469 | -0.0679 | 0.016 | 5.213 | <.001 | -0.5431 | <.001 | 0.009024 | 0.154 | 0.00658 | 0.202 | fit |
| continuous | Syllables: pkg | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6307 | -0.05233 | 0.053 | 4.799 | <.001 | -0.5436 | <.001 | 0.01209 | 0.017 | 0.005176 | 0.277 | fit |
| continuous | Phonemes | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6455 | -0.06846 | 0.019 | 2.076 | <.001 | -0.5854 | <.001 | 0.003548 | 0.200 | 0.00833 | 0.086 | fit |

### Continuous Versus Low/Mid/High Effort Rows

Use these as a strategy comparison. The continuous rows control exact effort; the effort-level rows ask a coarser question about low, middle, and high effort categories.

| effort_strategy | effort_label | readable_formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continuous | Words | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6266 | -0.1273 | <.001 | 6.376 | <.001 | -0.4729 | <.001 | -0.002441 | 0.726 | 0.009085 | 0.111 | fit |
| continuous | Morphemes | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6137 | -0.1417 | <.001 | 5.479 | <.001 | -0.5165 | <.001 | 0.003897 | 0.575 | 0.009103 | 0.070 | fit |
| continuous | Syllables: CMU/pkg | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6469 | -0.0679 | 0.016 | 5.213 | <.001 | -0.5431 | <.001 | 0.009024 | 0.154 | 0.00658 | 0.202 | fit |
| continuous | Syllables: pkg | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6307 | -0.05233 | 0.053 | 4.799 | <.001 | -0.5436 | <.001 | 0.01209 | 0.017 | 0.005176 | 0.277 | fit |
| continuous | Phonemes | sum_bits ~ age * effort + age * context_entropy + effort * context_entropy + child identity | 4.414e+05 | 21 | 0.6455 | -0.06846 | 0.019 | 2.076 | <.001 | -0.5854 | <.001 | 0.003548 | 0.200 | 0.00833 | 0.086 | fit |
| effort_level | Words | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.4413 | -0.0775 | 0.023 |  |  | -0.3592 | <.001 |  |  | 0.008538 | 0.072 | fit |
| effort_level | Morphemes | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.4133 | -0.07519 | 0.050 |  |  | -0.3338 | <.001 |  |  | 0.008115 | 0.060 | fit |
| effort_level | Syllables: CMU/pkg | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.4699 | -0.06767 | 0.027 |  |  | -0.3802 | <.001 |  |  | 0.004033 | 0.442 | fit |
| effort_level | Syllables: pkg | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.4478 | -0.05867 | 0.061 |  |  | -0.3742 | <.001 |  |  | 0.002937 | 0.532 | fit |
| effort_level | Phonemes | sum_bits ~ age * effort_level + context_entropy * effort_level + age * context_entropy + child identity | 4.414e+05 | 21 | 0.469 | -0.08116 | 0.007 |  |  | -0.3343 | <.001 |  |  | 0.003877 | 0.432 | fit |

### Earlier Effort-Level Context Rows

These are exploratory rows from the effort-level context model pass. They are useful for stress testing but less clean than exact fixed-effort slices.

| model_id | model_label | fit_type | effort_label | formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Words | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4413 | -0.0775 | 0.023 | -0.3592 | 1.47e-09 | fit |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Morphemes | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4133 | -0.07519 | 0.04969 | -0.3338 | 6.61e-07 | fit |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Syllables: CMU/pkg | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4699 | -0.06767 | 0.02677 | -0.3802 | 4.23e-12 | fit |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Syllables: pkg | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.4478 | -0.05867 | 0.06095 | -0.3742 | 4.62e-11 | fit |
| M6 | M6: age/context interactions + effort level + child FE | ols_cluster | Phonemes | sum_bits ~ age_c * context_entropy_c + age_c * C(effort_level) + context_entropy_c * C(effort_level) + C(child_id) | 4.414e+05 | 21 | 0.469 | -0.08116 | 0.00742 | -0.3343 | 7.23e-07 | fit |

### Context-Window Atlas Rows

These rows repeat the model logic over k0-k3 and, for M4-M6, over entropy, context-size, and entropy-plus-size variants. The purpose is context robustness.

| context_k | model_id | context_variant | effort_label | estimator | library | covariance | n_obs | n_children | r2_observed_fitted | age_coef | age_p | target_effort_coef | target_effort_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p | age_context_size_coef | age_context_size_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | M6E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k0 | M6S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| k1 | M6E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.639 | -0.1639 | <.001 | 5.773 | <.001 | 0.082 | 0.172 |  |  | -0.001998 | 0.775 | 0.01332 | 0.030 |  |  |
| k1 | M6E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6744 | -0.08865 | <.001 | 2.192 | <.001 | 0.0396 | 0.435 |  |  | 0.001076 | 0.696 | 0.01283 | 0.011 |  |  |
| k1 | M6E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6731 | -0.08642 | <.001 | 5.49 | <.001 | 0.07668 | 0.157 |  |  | 0.003309 | 0.583 | 0.01262 | 0.018 |  |  |
| k1 | M6E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6574 | -0.07135 | <.001 | 5.062 | <.001 | 0.06127 | 0.241 |  |  | 0.006345 | 0.187 | 0.01204 | 0.012 |  |  |
| k1 | M6E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6497 | -0.1471 | <.001 | 6.702 | <.001 | 0.07117 | 0.244 |  |  | -0.008804 | 0.213 | 0.01165 | 0.057 |  |  |
| k1 | M6ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6415 | -0.1619 | <.001 | 5.802 | <.001 | -0.0727 | 0.219 | -0.129 | <.001 | -0.002118 | 0.758 | 0.01743 | <.001 | 0.003243 | 0.142 |
| k1 | M6ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6769 | -0.08725 | <.001 | 2.203 | <.001 | -0.08079 | 0.109 | -0.04256 | <.001 | 0.001092 | 0.690 | 0.01652 | <.001 | 0.001271 | 0.160 |
| k1 | M6ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6755 | -0.08461 | <.001 | 5.517 | <.001 | -0.0493 | 0.374 | -0.1147 | <.001 | 0.003331 | 0.558 | 0.01641 | <.001 | 0.003345 | 0.212 |
| k1 | M6ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6598 | -0.06931 | 0.001 | 5.086 | <.001 | -0.07058 | 0.200 | -0.1106 | <.001 | 0.006357 | 0.169 | 0.01566 | <.001 | 0.002883 | 0.208 |
| k1 | M6ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.422e+05 | 21 | 0.6522 | -0.1444 | <.001 | 6.734 | <.001 | -0.07778 | 0.204 | -0.1649 | <.001 | -0.00876 | 0.215 | 0.01618 | 0.003 | 0.004946 | 0.105 |
| k1 | M6S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6418 | -0.159 | <.001 | 5.799 | <.001 |  |  | -0.1274 | <.001 | -0.002851 | 0.642 |  |  | 0.002052 | 0.403 |
| k1 | M6S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6771 | -0.08757 | <.001 | 2.201 | <.001 |  |  | -0.04115 | <.001 | 6.43e-04 | 0.773 |  |  | 8.18e-04 | 0.370 |
| k1 | M6S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6757 | -0.0842 | <.001 | 5.516 | <.001 |  |  | -0.1132 | <.001 | 0.002148 | 0.685 |  |  | 0.002167 | 0.406 |
| k1 | M6S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6601 | -0.0703 | 0.002 | 5.087 | <.001 |  |  | -0.1083 | <.001 | 0.005177 | 0.169 |  |  | 0.001678 | 0.433 |
| k1 | M6S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6525 | -0.1417 | <.001 | 6.729 | <.001 |  |  | -0.1604 | <.001 | -0.009531 | 0.103 |  |  | 0.00362 | 0.244 |
| k2 | M6E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.622 | -0.1475 | <.001 | 5.578 | <.001 | -0.4253 | <.001 |  |  | 0.001876 | 0.791 | 0.01352 | <.001 |  |  |
| k2 | M6E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.655 | -0.07308 | 0.008 | 2.114 | <.001 | -0.4947 | <.001 |  |  | 0.00278 | 0.328 | 0.01224 | <.001 |  |  |
| k2 | M6E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6559 | -0.0722 | 0.006 | 5.307 | <.001 | -0.4554 | <.001 |  |  | 0.007145 | 0.258 | 0.01096 | <.001 |  |  |
| k2 | M6E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6398 | -0.05665 | 0.024 | 4.889 | <.001 | -0.4527 | <.001 |  |  | 0.01025 | 0.045 | 0.009547 | 0.003 |  |  |
| k2 | M6E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6343 | -0.132 | <.001 | 6.486 | <.001 | -0.411 | <.001 |  |  | -0.00449 | 0.532 | 0.01205 | <.001 |  |  |
| k2 | M6ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6242 | -0.1475 | <.001 | 5.614 | <.001 | -0.4449 | <.001 | -0.04179 | <.001 | 0.002631 | 0.703 | 0.01435 | <.001 | -6.65e-04 | 0.666 |
| k2 | M6ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6572 | -0.07354 | 0.007 | 2.128 | <.001 | -0.5063 | <.001 | -0.01272 | <.001 | 0.00307 | 0.280 | 0.01308 | <.001 | -2.02e-04 | 0.674 |
| k2 | M6ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.658 | -0.07228 | 0.006 | 5.343 | <.001 | -0.4678 | <.001 | -0.03553 | <.001 | 0.007791 | 0.179 | 0.0118 | <.001 | -3.22e-04 | 0.821 |
| k2 | M6ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6417 | -0.05626 | 0.023 | 4.918 | <.001 | -0.4657 | <.001 | -0.03415 | <.001 | 0.01085 | 0.028 | 0.01046 | 0.002 | -6.31e-04 | 0.607 |
| k2 | M6ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.415e+05 | 21 | 0.6364 | -0.1312 | <.001 | 6.525 | <.001 | -0.4245 | <.001 | -0.05664 | <.001 | -0.00354 | 0.623 | 0.01304 | <.001 | -1.54e-05 | 0.993 |
| k2 | M6S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6246 | -0.1469 | <.001 | 5.611 | <.001 |  |  | -0.04444 | <.001 | 0.001426 | 0.811 |  |  | -6.48e-04 | 0.657 |
| k2 | M6S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6571 | -0.07708 | 0.005 | 2.127 | <.001 |  |  | -0.01405 | <.001 | 0.002379 | 0.274 |  |  | -2.12e-04 | 0.638 |
| k2 | M6S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6581 | -0.07513 | 0.004 | 5.341 | <.001 |  |  | -0.0386 | <.001 | 0.006098 | 0.244 |  |  | -3.74e-04 | 0.777 |
| k2 | M6S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6418 | -0.06081 | 0.018 | 4.918 | <.001 |  |  | -0.03724 | <.001 | 0.008955 | 0.018 |  |  | -7.19e-04 | 0.524 |
| k2 | M6S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6367 | -0.131 | <.001 | 6.522 | <.001 |  |  | -0.05973 | <.001 | -0.004747 | 0.403 |  |  | -1.65e-05 | 0.992 |
| k3 | M6E | entropy | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6137 | -0.1417 | <.001 | 5.479 | <.001 | -0.5165 | <.001 |  |  | 0.003897 | 0.575 | 0.009103 | 0.070 |  |  |
| k3 | M6E | entropy | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6455 | -0.06846 | 0.019 | 2.076 | <.001 | -0.5854 | <.001 |  |  | 0.003548 | 0.200 | 0.00833 | 0.086 |  |  |
| k3 | M6E | entropy | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6469 | -0.0679 | 0.016 | 5.213 | <.001 | -0.5431 | <.001 |  |  | 0.009024 | 0.154 | 0.00658 | 0.202 |  |  |
| k3 | M6E | entropy | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6307 | -0.05233 | 0.053 | 4.799 | <.001 | -0.5436 | <.001 |  |  | 0.01209 | 0.017 | 0.005176 | 0.277 |  |  |
| k3 | M6E | entropy | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6266 | -0.1273 | <.001 | 6.376 | <.001 | -0.4729 | <.001 |  |  | -0.002441 | 0.726 | 0.009085 | 0.111 |  |  |
| k3 | M6ES | entropy_plus_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6159 | -0.1426 | <.001 | 5.526 | <.001 | -0.541 | <.001 | -0.02502 | <.001 | 0.004933 | 0.457 | 0.01042 | 0.043 | -9.73e-04 | 0.384 |
| k3 | M6ES | entropy_plus_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6476 | -0.06946 | 0.014 | 2.093 | <.001 | -0.6018 | <.001 | -0.007348 | 0.004 | 0.00395 | 0.151 | 0.009755 | 0.051 | -3.01e-04 | 0.398 |
| k3 | M6ES | entropy_plus_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6489 | -0.06831 | 0.014 | 5.256 | <.001 | -0.5605 | <.001 | -0.02076 | 0.003 | 0.009957 | 0.081 | 0.008035 | 0.129 | -6.68e-04 | 0.524 |
| k3 | M6ES | entropy_plus_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6325 | -0.05205 | 0.049 | 4.835 | <.001 | -0.5613 | <.001 | -0.02054 | <.001 | 0.0129 | 0.008 | 0.006645 | 0.174 | -9.17e-04 | 0.303 |
| k3 | M6ES | entropy_plus_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.414e+05 | 21 | 0.6285 | -0.127 | <.001 | 6.425 | <.001 | -0.4939 | <.001 | -0.03458 | <.001 | -0.001189 | 0.864 | 0.01057 | 0.071 | -5.50e-04 | 0.679 |
| k3 | M6S | context_size | Morphemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6162 | -0.1419 | <.001 | 5.523 | <.001 |  |  | -0.02546 | <.001 | 0.003169 | 0.589 |  |  | -9.64e-04 | 0.360 |
| k3 | M6S | context_size | Phonemes | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6476 | -0.07269 | 0.010 | 2.092 | <.001 |  |  | -0.007942 | 0.002 | 0.003091 | 0.148 |  |  | -3.11e-04 | 0.366 |
| k3 | M6S | context_size | Syllables: CMU/pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.649 | -0.07096 | 0.010 | 5.255 | <.001 |  |  | -0.02175 | 0.002 | 0.007908 | 0.133 |  |  | -6.95e-04 | 0.481 |
| k3 | M6S | context_size | Syllables: pkg | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6326 | -0.05648 | 0.037 | 4.836 | <.001 |  |  | -0.02169 | <.001 | 0.01067 | 0.006 |  |  | -9.51e-04 | 0.257 |
| k3 | M6S | context_size | Words | linear OLS | statsmodels.formula.api.ols | child-cluster robust SE via cov_type='cluster' | 4.443e+05 | 21 | 0.6289 | -0.1264 | <.001 | 6.423 | <.001 |  |  | -0.03497 | <.001 | -0.002699 | 0.629 |  |  | -5.52e-04 | 0.660 |

### Balanced Bootstrap And Scrambling Robustness

These rows aggregate to child-session-context units. They ask whether the age slope survives equalized age-bin sampling and weakens when true age ordering is broken.

| context_k | robustness_method | rows | negative_observed | outside_null_95 | mean_same_sign_share | median_permutation_p |
| --- | --- | --- | --- | --- | --- | --- |
| k1 | age_bin_group_scramble | 5 | 5 | 5 | 0.48 | 0.010 |
| k1 | balanced_bootstrap | 5 | 5 | 0 | 1 |  |
| k1 | unit_age_scramble | 5 | 5 | 5 | 0.456 | 0.010 |
| k1 | within_child_age_scramble | 5 | 5 | 5 | 0.52 | 0.010 |
| k2 | age_bin_group_scramble | 5 | 5 | 5 | 0.53 | 0.010 |
| k2 | balanced_bootstrap | 5 | 5 | 0 | 0.996 |  |
| k2 | unit_age_scramble | 5 | 5 | 5 | 0.496 | 0.010 |
| k2 | within_child_age_scramble | 5 | 5 | 5 | 0.514 | 0.010 |
| k3 | age_bin_group_scramble | 5 | 5 | 5 | 0.542 | 0.030 |
| k3 | balanced_bootstrap | 5 | 5 | 0 | 0.934 |  |
| k3 | unit_age_scramble | 5 | 5 | 5 | 0.516 | 0.010 |
| k3 | within_child_age_scramble | 5 | 5 | 5 | 0.554 | 0.010 |

### Plot Gallery For M6

The repeated plot families were explained once above. In this gallery, read each plot family the same way: x-axis is usually child age, y-axis is predicted or observed total bits, colors usually separate effort values/levels or model variants, facets split effort units/context windows, and ribbons are model-confidence or bootstrap/null intervals depending on the family.

#### M1-M6 context-window fixed-effort atlas plots

![k1_m6e_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_morphemes_fixed_effort_atlas.png)
*k1_m6e_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m6e_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_phonemes_fixed_effort_atlas.png)
*k1_m6e_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m6e_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_words_fixed_effort_atlas.png)
*k1_m6e_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m6es_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_morphemes_fixed_effort_atlas.png)
*k1_m6es_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m6es_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_phonemes_fixed_effort_atlas.png)
*k1_m6es_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m6es_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_words_fixed_effort_atlas.png)
*k1_m6es_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_m6s_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_morphemes_fixed_effort_atlas.png)
*k1_m6s_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_m6s_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_phonemes_fixed_effort_atlas.png)
*k1_m6s_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_m6s_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_words_fixed_effort_atlas.png)
*k1_m6s_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_m6e_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_morphemes_fixed_effort_atlas.png)
*k2_m6e_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m6e_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_phonemes_fixed_effort_atlas.png)
*k2_m6e_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m6e_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_words_fixed_effort_atlas.png)
*k2_m6e_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m6es_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_morphemes_fixed_effort_atlas.png)
*k2_m6es_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m6es_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_phonemes_fixed_effort_atlas.png)
*k2_m6es_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m6es_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_words_fixed_effort_atlas.png)
*k2_m6es_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_m6s_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_morphemes_fixed_effort_atlas.png)
*k2_m6s_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_m6s_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_phonemes_fixed_effort_atlas.png)
*k2_m6s_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_m6s_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_words_fixed_effort_atlas.png)
*k2_m6s_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_m6e_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_morphemes_fixed_effort_atlas.png)
*k3_m6e_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m6e_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_phonemes_fixed_effort_atlas.png)
*k3_m6e_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m6e_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_words_fixed_effort_atlas.png)
*k3_m6e_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m6es_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_morphemes_fixed_effort_atlas.png)
*k3_m6es_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m6es_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_phonemes_fixed_effort_atlas.png)
*k3_m6es_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m6es_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_words_fixed_effort_atlas.png)
*k3_m6es_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_m6s_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_morphemes_fixed_effort_atlas.png)
*k3_m6s_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_m6s_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_phonemes_fixed_effort_atlas.png)
*k3_m6s_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_m6s_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_words_fixed_effort_atlas.png)
*k3_m6s_nb_words_fixed_effort_atlas.png; k3; Words*

#### M1-M3 estimator deep dive plus early M4-M6 plots

![m5_m6_effort_level_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_adjusted_age_predictions.png)
*m5_m6_effort_level_adjusted_age_predictions.png*

![m5_m6_effort_level_average_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_average_age_predictions.png)
*m5_m6_effort_level_average_age_predictions.png*

![m5_m6_saturated_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.png)
*m5_m6_saturated_adjusted_age_predictions.png*

![m5_m6_saturated_selected_coefficients.png](../figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png)
*m5_m6_saturated_selected_coefficients.png*

![m6_effort_level_adjusted_age_predictions.png](../figs/m1_m2_utterance_information_deep_dive/m6_effort_level_adjusted_age_predictions.png)
*m6_effort_level_adjusted_age_predictions.png*

#### M1-M6 continuous versus effort-level plots

![m6_dual_effort_predictions.png](../figs/m1_m6_dual_effort_quick_share/m6_dual_effort_predictions.png)
*m6_dual_effort_predictions.png*

#### M1-M6 fixed-effort atlas plots

![m6_nb_morphemes_atlas_bins.png / Morphemes](../figs/m1_m6_fixed_effort_atlas/m6_nb_morphemes_atlas_bins.png)
*m6_nb_morphemes_atlas_bins.png; Morphemes*

![m6_nb_phonemes_atlas_bins.png / Phonemes](../figs/m1_m6_fixed_effort_atlas/m6_nb_phonemes_atlas_bins.png)
*m6_nb_phonemes_atlas_bins.png; Phonemes*

![m6_nb_syllables_cmu_or_pkg_atlas_bins.png / Syllables: CMU/pkg](../figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_cmu_or_pkg_atlas_bins.png)
*m6_nb_syllables_cmu_or_pkg_atlas_bins.png; Syllables: CMU/pkg*

![m6_nb_syllables_pkg_atlas_bins.png / Syllables: pkg](../figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_pkg_atlas_bins.png)
*m6_nb_syllables_pkg_atlas_bins.png; Syllables: pkg*

![m6_nb_words_atlas_bins.png / Words](../figs/m1_m6_fixed_effort_atlas/m6_nb_words_atlas_bins.png)
*m6_nb_words_atlas_bins.png; Words*

#### M1-M6 fixed-effort slice plots

![m6_granular_primary_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m6_granular_primary_fixed_effort_slices.png)
*m6_granular_primary_fixed_effort_slices.png*

![m6_marginal_adjusted_global_trends.png](../figs/m1_m6_fixed_effort_slices/m6_marginal_adjusted_global_trends.png)
*m6_marginal_adjusted_global_trends.png*

![m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png)
*m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png*

![m6_top_frequency_12_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m6_top_frequency_12_fixed_effort_slices.png)
*m6_top_frequency_12_fixed_effort_slices.png*

![m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png](../figs/m1_m6_fixed_effort_slices/m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png)
*m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png*

#### Age-bin bootstrap and scrambling robustness plots

![m6_age_slope_robustness_intervals.png](../figs/age_scrambling_robustness/m6_age_slope_robustness_intervals.png)
*m6_age_slope_robustness_intervals.png*

![m6_clear_robustness_regression_lines.png](../figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png)
*m6_clear_robustness_regression_lines.png*



## Appendix A: Context-Predictor Adjunct Atlas

The CF0-CF3 adjunct models are not part of M1-M6, but they are useful for separating target effort, context entropy, and matched context size. They should be treated as adjacent robustness/exploratory material.

| context_k | model_id | model_label | effort_label | formula | n_obs | n_children | r2_observed_fitted | age_coef | age_p | context_entropy_coef | context_entropy_p | context_size_coef | context_size_p | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k0 | CF0 | Baseline controls | Words | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7252 | -0.1582 | 1.26e-06 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Words | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF0 | Baseline controls | Morphemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7204 | -0.1784 | 1.76e-05 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Morphemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF0 | Baseline controls | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7461 | -0.0907 | 0.003016 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF0 | Baseline controls | Syllables: pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7303 | -0.07571 | 0.009199 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF0 | Baseline controls | Phonemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.7578 | -0.09847 | 0.001498 |  |  |  |  | fit |
| k0 | CF1 | Entropy only | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF2 | Matched context size only | Phonemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k0 | CF3 | Entropy plus matched context size | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) |  |  |  |  |  |  |  |  |  | skipped |
| k1 | CF0 | Baseline controls | Words | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6495 | -0.1431 | 4.82e-07 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6495 | -0.1481 | 2.84e-07 | 0.05917 | 0.2737 |  |  | fit |
| k1 | CF2 | Matched context size only | Words | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.651 | -0.1402 | 3.82e-07 |  |  | -0.175 | 1.57e-18 | fit |
| k1 | CF3 | Entropy plus matched context size | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.6506 | -0.1414 | 7.52e-07 | -0.06001 | 0.2473 | -0.1813 | 1.16e-23 | fit |
| k1 | CF0 | Baseline controls | Morphemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.639 | -0.1585 | 4.34e-06 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6388 | -0.1636 | 2.91e-06 | 0.06736 | 0.2056 |  |  | fit |
| k1 | CF2 | Matched context size only | Morphemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6403 | -0.1562 | 4.44e-06 |  |  | -0.1421 | 5.41e-16 | fit |
| k1 | CF3 | Entropy plus matched context size | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.6397 | -0.1576 | 5.93e-06 | -0.0464 | 0.3573 | -0.1462 | 8.74e-21 | fit |
| k1 | CF0 | Baseline controls | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6729 | -0.08207 | 3.73e-04 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6728 | -0.08435 | 2.20e-04 | 0.06356 | 0.2038 |  |  | fit |
| k1 | CF2 | Matched context size only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6741 | -0.07966 | 6.70e-04 |  |  | -0.1263 | 1.66e-15 | fit |
| k1 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.6737 | -0.07842 | 6.12e-04 | -0.03417 | 0.4771 | -0.1285 | 5.61e-18 | fit |
| k1 | CF0 | Baseline controls | Syllables: pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6572 | -0.06724 | 0.001341 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6571 | -0.06823 | 6.72e-04 | 0.04786 | 0.3456 |  |  | fit |
| k1 | CF2 | Matched context size only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6585 | -0.06479 | 0.002368 |  |  | -0.1208 | 8.67e-18 | fit |
| k1 | CF3 | Entropy plus matched context size | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.658 | -0.06222 | 0.002181 | -0.05367 | 0.2808 | -0.1244 | 2.21e-21 | fit |
| k1 | CF0 | Baseline controls | Phonemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6743 | -0.08519 | 1.90e-04 |  |  |  |  | fit |
| k1 | CF1 | Entropy only | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.422e+05 | 21 | 0.6743 | -0.08687 | 1.76e-04 | 0.02783 | 0.5479 |  |  | fit |
| k1 | CF2 | Matched context size only | Phonemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6755 | -0.08311 | 3.69e-04 |  |  | -0.04665 | 5.74e-14 | fit |
| k1 | CF3 | Entropy plus matched context size | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.422e+05 | 21 | 0.6751 | -0.08125 | 4.55e-04 | -0.06489 | 0.1432 | -0.04865 | 5.92e-17 | fit |
| k2 | CF0 | Baseline controls | Words | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6338 | -0.1287 | 1.26e-05 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.6343 | -0.1318 | 1.09e-05 | -0.4107 | 9.97e-30 |  |  | fit |
| k2 | CF2 | Matched context size only | Words | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.635 | -0.1289 | 6.75e-06 |  |  | -0.07164 | 5.18e-09 | fit |
| k2 | CF3 | Entropy plus matched context size | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.6347 | -0.1273 | 1.67e-05 | -0.4087 | 1.84e-26 | -0.06994 | 1.73e-09 | fit |
| k2 | CF0 | Baseline controls | Morphemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6217 | -0.1425 | 8.15e-05 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.622 | -0.1458 | 7.01e-05 | -0.4256 | 1.78e-29 |  |  | fit |
| k2 | CF2 | Matched context size only | Morphemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6227 | -0.1433 | 5.91e-05 |  |  | -0.05554 | 3.77e-07 | fit |
| k2 | CF3 | Entropy plus matched context size | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.6223 | -0.142 | 9.28e-05 | -0.4253 | 1.64e-26 | -0.05438 | 1.32e-07 | fit |
| k2 | CF0 | Baseline controls | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6551 | -0.06903 | 0.006609 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.6557 | -0.06891 | 0.005689 | -0.4558 | 2.36e-45 |  |  | fit |
| k2 | CF2 | Matched context size only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6561 | -0.06963 | 0.006892 |  |  | -0.04898 | 4.82e-08 | fit |
| k2 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.656 | -0.06519 | 0.008543 | -0.4521 | 1.31e-40 | -0.04709 | 4.44e-08 | fit |
| k2 | CF0 | Baseline controls | Syllables: pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.639 | -0.0542 | 0.02056 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.6396 | -0.05248 | 0.01741 | -0.4543 | 3.72e-44 |  |  | fit |
| k2 | CF2 | Matched context size only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.64 | -0.05479 | 0.02082 |  |  | -0.04671 | 4.85e-09 | fit |
| k2 | CF3 | Entropy plus matched context size | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.6399 | -0.04875 | 0.02692 | -0.4506 | 2.24e-39 | -0.04487 | 2.50e-09 | fit |
| k2 | CF0 | Baseline controls | Phonemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6542 | -0.07096 | 0.004888 |  |  |  |  | fit |
| k2 | CF1 | Entropy only | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.415e+05 | 21 | 0.6549 | -0.06995 | 0.005678 | -0.4942 | 1.56e-50 |  |  | fit |
| k2 | CF2 | Matched context size only | Phonemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6552 | -0.0717 | 0.005315 |  |  | -0.01841 | 2.09e-07 | fit |
| k2 | CF3 | Entropy plus matched context size | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.415e+05 | 21 | 0.6551 | -0.0665 | 0.008081 | -0.4898 | 3.60e-45 | -0.01751 | 2.11e-07 | fit |
| k3 | CF0 | Baseline controls | Words | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6259 | -0.1225 | 4.42e-05 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6266 | -0.1269 | 3.29e-05 | -0.4716 | 8.14e-37 |  |  | fit |
| k3 | CF2 | Matched context size only | Words | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6272 | -0.1239 | 2.12e-05 |  |  | -0.04386 | 3.38e-07 | fit |
| k3 | CF3 | Entropy plus matched context size | Words | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6268 | -0.123 | 4.44e-05 | -0.4699 | 2.31e-35 | -0.0427 | 3.97e-07 | fit |
| k3 | CF0 | Baseline controls | Morphemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6131 | -0.1355 | 2.52e-04 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6136 | -0.1401 | 1.92e-04 | -0.5123 | 4.22e-43 |  |  | fit |
| k3 | CF2 | Matched context size only | Morphemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6142 | -0.1375 | 1.69e-04 |  |  | -0.03407 | 5.98e-06 | fit |
| k3 | CF3 | Entropy plus matched context size | Morphemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6138 | -0.1369 | 2.32e-04 | -0.5111 | 2.56e-41 | -0.03298 | 7.33e-06 | fit |
| k3 | CF0 | Baseline controls | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6459 | -0.06326 | 0.0177 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6468 | -0.06446 | 0.01333 | -0.5398 | 7.26e-57 |  |  | fit |
| k3 | CF2 | Matched context size only | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6471 | -0.06497 | 0.01608 |  |  | -0.02985 | 7.54e-07 | fit |
| k3 | CF3 | Entropy plus matched context size | Syllables: CMU/pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6469 | -0.06126 | 0.01758 | -0.5362 | 6.53e-54 | -0.02838 | 1.88e-06 | fit |
| k3 | CF0 | Baseline controls | Syllables: pkg | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6296 | -0.04846 | 0.04938 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6304 | -0.04803 | 0.03841 | -0.541 | 2.56e-59 |  |  | fit |
| k3 | CF2 | Matched context size only | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6308 | -0.05014 | 0.04436 |  |  | -0.0288 | 2.98e-08 | fit |
| k3 | CF3 | Entropy plus matched context size | Syllables: pkg | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6306 | -0.04483 | 0.05182 | -0.537 | 3.57e-56 | -0.02722 | 5.40e-08 | fit |
| k3 | CF0 | Baseline controls | Phonemes | sum_bits ~ age_c + target_effort_c + C(child_id) | 4.47e+05 | 21 | 0.6443 | -0.06486 | 0.01348 |  |  |  |  | fit |
| k3 | CF1 | Entropy only | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id) | 4.414e+05 | 21 | 0.6453 | -0.06517 | 0.01283 | -0.5814 | 3.34e-70 |  |  | fit |
| k3 | CF2 | Matched context size only | Phonemes | sum_bits ~ age_c + target_effort_c + context_size_c + C(child_id) | 4.443e+05 | 21 | 0.6455 | -0.06667 | 0.01275 |  |  | -0.01139 | 9.16e-07 | fit |
| k3 | CF3 | Entropy plus matched context size | Phonemes | sum_bits ~ age_c + target_effort_c + context_entropy_c + context_size_c + C(child_id) | 4.414e+05 | 21 | 0.6455 | -0.06221 | 0.01639 | -0.577 | 1.81e-66 | -0.0106 | 2.72e-06 | fit |

### Context Adjunct Gallery

#### Context-predictor adjunct fixed-effort atlas plots

![k0_cf0_nb_morphemes_fixed_effort_atlas.png / k0 / Morphemes](../figs/context_fixed_effort_atlas/k0_cf0_nb_morphemes_fixed_effort_atlas.png)
*k0_cf0_nb_morphemes_fixed_effort_atlas.png; k0; Morphemes*

![k0_cf0_nb_phonemes_fixed_effort_atlas.png / k0 / Phonemes](../figs/context_fixed_effort_atlas/k0_cf0_nb_phonemes_fixed_effort_atlas.png)
*k0_cf0_nb_phonemes_fixed_effort_atlas.png; k0; Phonemes*

![k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k0 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k0; Syllables: CMU/pkg*

![k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png / k0 / Syllables: pkg](../figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png)
*k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png; k0; Syllables: pkg*

![k0_cf0_nb_words_fixed_effort_atlas.png / k0 / Words](../figs/context_fixed_effort_atlas/k0_cf0_nb_words_fixed_effort_atlas.png)
*k0_cf0_nb_words_fixed_effort_atlas.png; k0; Words*

![k1_cf0_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_fixed_effort_atlas/k1_cf0_nb_morphemes_fixed_effort_atlas.png)
*k1_cf0_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_cf0_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_fixed_effort_atlas/k1_cf0_nb_phonemes_fixed_effort_atlas.png)
*k1_cf0_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_cf0_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_fixed_effort_atlas/k1_cf0_nb_words_fixed_effort_atlas.png)
*k1_cf0_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_cf1_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_fixed_effort_atlas/k1_cf1_nb_morphemes_fixed_effort_atlas.png)
*k1_cf1_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_cf1_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_fixed_effort_atlas/k1_cf1_nb_phonemes_fixed_effort_atlas.png)
*k1_cf1_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_cf1_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_fixed_effort_atlas/k1_cf1_nb_words_fixed_effort_atlas.png)
*k1_cf1_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_cf2_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_fixed_effort_atlas/k1_cf2_nb_morphemes_fixed_effort_atlas.png)
*k1_cf2_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_cf2_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_fixed_effort_atlas/k1_cf2_nb_phonemes_fixed_effort_atlas.png)
*k1_cf2_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_cf2_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_fixed_effort_atlas/k1_cf2_nb_words_fixed_effort_atlas.png)
*k1_cf2_nb_words_fixed_effort_atlas.png; k1; Words*

![k1_cf3_nb_morphemes_fixed_effort_atlas.png / k1 / Morphemes](../figs/context_fixed_effort_atlas/k1_cf3_nb_morphemes_fixed_effort_atlas.png)
*k1_cf3_nb_morphemes_fixed_effort_atlas.png; k1; Morphemes*

![k1_cf3_nb_phonemes_fixed_effort_atlas.png / k1 / Phonemes](../figs/context_fixed_effort_atlas/k1_cf3_nb_phonemes_fixed_effort_atlas.png)
*k1_cf3_nb_phonemes_fixed_effort_atlas.png; k1; Phonemes*

![k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k1 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k1; Syllables: CMU/pkg*

![k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png / k1 / Syllables: pkg](../figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png)
*k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png; k1; Syllables: pkg*

![k1_cf3_nb_words_fixed_effort_atlas.png / k1 / Words](../figs/context_fixed_effort_atlas/k1_cf3_nb_words_fixed_effort_atlas.png)
*k1_cf3_nb_words_fixed_effort_atlas.png; k1; Words*

![k2_cf0_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_fixed_effort_atlas/k2_cf0_nb_morphemes_fixed_effort_atlas.png)
*k2_cf0_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_cf0_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_fixed_effort_atlas/k2_cf0_nb_phonemes_fixed_effort_atlas.png)
*k2_cf0_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_cf0_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_fixed_effort_atlas/k2_cf0_nb_words_fixed_effort_atlas.png)
*k2_cf0_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_cf1_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_fixed_effort_atlas/k2_cf1_nb_morphemes_fixed_effort_atlas.png)
*k2_cf1_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_cf1_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_fixed_effort_atlas/k2_cf1_nb_phonemes_fixed_effort_atlas.png)
*k2_cf1_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_cf1_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_fixed_effort_atlas/k2_cf1_nb_words_fixed_effort_atlas.png)
*k2_cf1_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_cf2_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_fixed_effort_atlas/k2_cf2_nb_morphemes_fixed_effort_atlas.png)
*k2_cf2_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_cf2_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_fixed_effort_atlas/k2_cf2_nb_phonemes_fixed_effort_atlas.png)
*k2_cf2_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_cf2_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_fixed_effort_atlas/k2_cf2_nb_words_fixed_effort_atlas.png)
*k2_cf2_nb_words_fixed_effort_atlas.png; k2; Words*

![k2_cf3_nb_morphemes_fixed_effort_atlas.png / k2 / Morphemes](../figs/context_fixed_effort_atlas/k2_cf3_nb_morphemes_fixed_effort_atlas.png)
*k2_cf3_nb_morphemes_fixed_effort_atlas.png; k2; Morphemes*

![k2_cf3_nb_phonemes_fixed_effort_atlas.png / k2 / Phonemes](../figs/context_fixed_effort_atlas/k2_cf3_nb_phonemes_fixed_effort_atlas.png)
*k2_cf3_nb_phonemes_fixed_effort_atlas.png; k2; Phonemes*

![k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k2 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k2; Syllables: CMU/pkg*

![k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png / k2 / Syllables: pkg](../figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png)
*k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png; k2; Syllables: pkg*

![k2_cf3_nb_words_fixed_effort_atlas.png / k2 / Words](../figs/context_fixed_effort_atlas/k2_cf3_nb_words_fixed_effort_atlas.png)
*k2_cf3_nb_words_fixed_effort_atlas.png; k2; Words*

![k3_cf0_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_fixed_effort_atlas/k3_cf0_nb_morphemes_fixed_effort_atlas.png)
*k3_cf0_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_cf0_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_fixed_effort_atlas/k3_cf0_nb_phonemes_fixed_effort_atlas.png)
*k3_cf0_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_cf0_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_fixed_effort_atlas/k3_cf0_nb_words_fixed_effort_atlas.png)
*k3_cf0_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_cf1_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_fixed_effort_atlas/k3_cf1_nb_morphemes_fixed_effort_atlas.png)
*k3_cf1_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_cf1_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_fixed_effort_atlas/k3_cf1_nb_phonemes_fixed_effort_atlas.png)
*k3_cf1_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_cf1_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_fixed_effort_atlas/k3_cf1_nb_words_fixed_effort_atlas.png)
*k3_cf1_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_cf2_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_fixed_effort_atlas/k3_cf2_nb_morphemes_fixed_effort_atlas.png)
*k3_cf2_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_cf2_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_fixed_effort_atlas/k3_cf2_nb_phonemes_fixed_effort_atlas.png)
*k3_cf2_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_cf2_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_fixed_effort_atlas/k3_cf2_nb_words_fixed_effort_atlas.png)
*k3_cf2_nb_words_fixed_effort_atlas.png; k3; Words*

![k3_cf3_nb_morphemes_fixed_effort_atlas.png / k3 / Morphemes](../figs/context_fixed_effort_atlas/k3_cf3_nb_morphemes_fixed_effort_atlas.png)
*k3_cf3_nb_morphemes_fixed_effort_atlas.png; k3; Morphemes*

![k3_cf3_nb_phonemes_fixed_effort_atlas.png / k3 / Phonemes](../figs/context_fixed_effort_atlas/k3_cf3_nb_phonemes_fixed_effort_atlas.png)
*k3_cf3_nb_phonemes_fixed_effort_atlas.png; k3; Phonemes*

![k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png / k3 / Syllables: CMU/pkg](../figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png)
*k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png; k3; Syllables: CMU/pkg*

![k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png / k3 / Syllables: pkg](../figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png)
*k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png; k3; Syllables: pkg*

![k3_cf3_nb_words_fixed_effort_atlas.png / k3 / Words](../figs/context_fixed_effort_atlas/k3_cf3_nb_words_fixed_effort_atlas.png)
*k3_cf3_nb_words_fixed_effort_atlas.png; k3; Words*


## Appendix B: Proposed Additions Not Claimed As Results

| proposal | formula | why | status |
| --- | --- | --- | --- |
| R1-M7 child-structure sensitivity | FE within: age_within_child * effort + controls + C(child_id); Mundlak: age_within_child * effort + child_mean_age + controls + random/clustered child structure | Checks how the age result changes under fixed child baselines, random child baselines, and within/between age decomposition without mixing incompatible child structures. | proposed/not yet run in this v2 synthesis |
| R1-M8 independent baseline atlases | repeat M1-M6 separately for real child, random, unigram, bigram, trigram, and LSTM targets | Compares developmental trajectories of each baseline source against the real child trajectory without mixing source types in the first pass. | proposed/not yet run in this v2 synthesis |
| R1-M9 formal source-trajectory comparison | sum_bits ~ target_source * age_c * effort_c + context controls + C(child_id) | Tests whether the real child age-effort trajectory differs statistically from each generated baseline trajectory. | proposed/not yet run in this v2 synthesis |
| context-control ladder | M3 + parent_context_effort, then M3 + context_entropy, then M3 + question_type, then all together | Adds the parent/context confounds one at a time before interpreting any richer context interactions. | partially present in context adjuncts; parent question-type ladder still proposed |
| age-overlap and age-bin balance checks | same M2/M3/M4/M5 formulas after overlap restriction or balanced age-bin sampling | Checks whether the trajectory is driven by children/corpora that occupy unique age ranges or dense age bins. | partially addressed by existing age-scrambling robustness; fuller source-specific version not yet run |
| corpus and session controls | sum_bits ~ age_c * effort_c + context controls + C(child_id) + C(dataset) | Tests whether corpus/transcription/session composition explains part of the child-adjusted Route 1 trend. | proposed/not yet run in this v2 synthesis |
| child random intercept plus random age slope | MixedLM: sum_bits ~ age + effort, groups=child_id, re_formula='~age' | Allows children to have different developmental slopes and shrinks noisy child-specific estimates. | M2/M3 sensitivity exists; fuller overlap/balancing interpretation still proposed |
| parked Route 2 effort outcome bridge | effort ~ age + response_entropy + expected_model_response_length + context_size + C(child_id) | Tests whether contextual uncertainty predicts how much children choose to say. | parked for later; current priority remains Route 1 |

## Appendix C: Corrected Route 1 TODO List

| priority | todo | deliverable | status |
| --- | --- | --- | --- |
| 1 | Freeze the corrected Route 1 formula ladder | Explicit M1-M6 definitions with interaction hierarchy and one effort unit per fitted row. | documentation clarified; implementation audit next |
| 2 | Create parent/context controls | `parent_context_effort_*`, `question_type`, and audited `context_entropy`/`context_size` columns for k1-k3. | context entropy/size partly exist; parent effort and question type need audit/build |
| 3 | Refit child target Route 1 ladder | M1-M6 rows for real child utterances using the cleaned formula ladder and context-control sequence. | current atlas is close but needs formula-ladder cleanup before final use |
| 4 | Repeat the whole atlas independently for each baseline | Separate M1-M6 atlases for random, unigram, bigram, trigram, and LSTM generated targets. | proposed/not yet run |
| 5 | Compare source-specific developmental trajectories | Side-by-side age slopes, fixed-effort curves, robustness checks, and a source-trajectory comparison report. | proposed/not yet run |
| 6 | Fit formal source interaction model | `sum_bits ~ target_source * age_c * effort_c + context controls + C(child_id)` after independent atlases exist. | proposed/not yet run |
| 7 | Run child-structure sensitivity | Compare separate variants: no child identity plus clustered SE, `C(child_id)`, GEE grouped by child, MixedLM random intercept/slope, fixed-effect within-child age, and Mundlak within/between age. Do not combine `C(child_id)` with random child intercepts or child-level means. | partly present as sensitivity rows; needs coherent Route 1 comparison table |
| 8 | Update supervisor-facing report only after the corrected Route 1 atlas is rerun | Short methods section plus a small number of fixed-effort plots and baseline-comparison plots. | pending |

## Appendix D: Complete Figure Inventory

This inventory is included so image coverage is auditable. The report embeds PNGs; PDF duplicates are intentionally not embedded.

| source_id | filename | models | context_k | effort_label | path |
| --- | --- | --- | --- | --- | --- |
| deep_dive | m1_coefficients_by_effort_version.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_coefficients_by_effort_version.png |
| deep_dive | m1_expanded_age_coefficients.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_expanded_age_coefficients.png |
| deep_dive | m1_expanded_r2.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_expanded_r2.png |
| deep_dive | m1_glm_gamma_log_adjusted_age_lines.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_glm_gamma_log_adjusted_age_lines.png |
| deep_dive | m1_glm_gaussian_adjusted_age_lines.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_glm_gaussian_adjusted_age_lines.png |
| deep_dive | m1_low_mid_high_effort_adjusted_age_predictions.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_low_mid_high_effort_adjusted_age_predictions.png |
| deep_dive | m1_m2_adjusted_age_predictions.png | M1;M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_m2_adjusted_age_predictions.png |
| deep_dive | m1_m2_age_coefficients_by_effort.png | M1;M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_m2_age_coefficients_by_effort.png |
| deep_dive | m1_m2_delta_r2_variable_importance.png | M1;M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_m2_delta_r2_variable_importance.png |
| deep_dive | m1_m2_effort_coefficients_by_measure.png | M1;M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_m2_effort_coefficients_by_measure.png |
| deep_dive | m1_m2_residual_diagnostics_words.png | M1;M2 |  | Words | figs/m1_m2_utterance_information_deep_dive/m1_m2_residual_diagnostics_words.png |
| deep_dive | m1_ols_adjusted_age_lines.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_ols_adjusted_age_lines.png |
| deep_dive | m1_ols_cluster_adjusted_age_lines.png | M1 |  |  | figs/m1_m2_utterance_information_deep_dive/m1_ols_cluster_adjusted_age_lines.png |
| deep_dive | m2_coefficients_by_effort_version.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_coefficients_by_effort_version.png |
| deep_dive | m2_expanded_age_coefficients.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_expanded_age_coefficients.png |
| deep_dive | m2_expanded_r2.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_expanded_r2.png |
| deep_dive | m2_gee_gamma_log_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_gee_gamma_log_adjusted_age_lines.png |
| deep_dive | m2_gee_gaussian_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_gee_gaussian_adjusted_age_lines.png |
| deep_dive | m2_glm_gamma_log_child_fe_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_glm_gamma_log_child_fe_adjusted_age_lines.png |
| deep_dive | m2_low_mid_high_effort_adjusted_age_predictions.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_low_mid_high_effort_adjusted_age_predictions.png |
| deep_dive | m2_mixed_random_age_slope_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_age_slope_adjusted_age_lines.png |
| deep_dive | m2_mixed_random_intercept_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_mixed_random_intercept_adjusted_age_lines.png |
| deep_dive | m2_ols_child_fe_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_adjusted_age_lines.png |
| deep_dive | m2_ols_child_fe_age_slope_adjusted_age_lines.png | M2 |  |  | figs/m1_m2_utterance_information_deep_dive/m2_ols_child_fe_age_slope_adjusted_age_lines.png |
| deep_dive | m3_expanded_interaction_coefficients.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_expanded_interaction_coefficients.png |
| deep_dive | m3_expanded_r2.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_expanded_r2.png |
| deep_dive | m3_gee_gamma_log_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_adjusted_age_lines.png |
| deep_dive | m3_gee_gamma_log_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_gee_gamma_log_interaction_interaction_age_lines.png |
| deep_dive | m3_gee_gaussian_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_adjusted_age_lines.png |
| deep_dive | m3_gee_gaussian_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_gee_gaussian_interaction_interaction_age_lines.png |
| deep_dive | m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_adjusted_age_lines.png |
| deep_dive | m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_child_fe_interaction_interaction_age_lines.png |
| deep_dive | m3_glm_gamma_log_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_adjusted_age_lines.png |
| deep_dive | m3_glm_gamma_log_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gamma_log_interaction_interaction_age_lines.png |
| deep_dive | m3_glm_gaussian_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_adjusted_age_lines.png |
| deep_dive | m3_glm_gaussian_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_glm_gaussian_interaction_interaction_age_lines.png |
| deep_dive | m3_mixed_random_age_slope_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_adjusted_age_lines.png |
| deep_dive | m3_mixed_random_age_slope_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_age_slope_interaction_interaction_age_lines.png |
| deep_dive | m3_mixed_random_intercept_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_adjusted_age_lines.png |
| deep_dive | m3_mixed_random_intercept_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_mixed_random_intercept_interaction_interaction_age_lines.png |
| deep_dive | m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_adjusted_age_lines.png |
| deep_dive | m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_age_slope_interaction_interaction_age_lines.png |
| deep_dive | m3_ols_child_fe_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_adjusted_age_lines.png |
| deep_dive | m3_ols_child_fe_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_child_fe_interaction_interaction_age_lines.png |
| deep_dive | m3_ols_cluster_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_adjusted_age_lines.png |
| deep_dive | m3_ols_cluster_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_cluster_interaction_interaction_age_lines.png |
| deep_dive | m3_ols_interaction_adjusted_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_adjusted_age_lines.png |
| deep_dive | m3_ols_interaction_interaction_age_lines.png | M3 |  |  | figs/m1_m2_utterance_information_deep_dive/m3_ols_interaction_interaction_age_lines.png |
| deep_dive | m4_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_adjusted_predictions.png |
| deep_dive | m4_context_entropy_coefficients.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_coefficients.png |
| deep_dive | m4_context_entropy_descriptive_bins.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_context_entropy_descriptive_bins.png |
| deep_dive | m4_effort_quantile_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_effort_quantile_adjusted_predictions.png |
| deep_dive | m4_m4a_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4a_context_entropy_adjusted_predictions.png |
| deep_dive | m4_m4b_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4b_context_entropy_adjusted_predictions.png |
| deep_dive | m4_m4c_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4c_context_entropy_adjusted_predictions.png |
| deep_dive | m4_m4d_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4d_context_entropy_adjusted_predictions.png |
| deep_dive | m4_m4e_context_entropy_adjusted_predictions.png | M4 |  |  | figs/m1_m2_utterance_information_deep_dive/m4_m4e_context_entropy_adjusted_predictions.png |
| deep_dive | m5_effort_level_adjusted_age_predictions.png | M5 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_effort_level_adjusted_age_predictions.png |
| deep_dive | m5_m6_effort_level_adjusted_age_predictions.png | M5;M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_adjusted_age_predictions.png |
| deep_dive | m5_m6_effort_level_average_age_predictions.png | M5;M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_m6_effort_level_average_age_predictions.png |
| deep_dive | m5_m6_saturated_adjusted_age_predictions.png | M5;M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_adjusted_age_predictions.png |
| deep_dive | m5_m6_saturated_selected_coefficients.png | M5;M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m5_m6_saturated_selected_coefficients.png |
| deep_dive | m6_effort_level_adjusted_age_predictions.png | M6 |  |  | figs/m1_m2_utterance_information_deep_dive/m6_effort_level_adjusted_age_predictions.png |
| deep_dive | predictor_correlation_heatmap.png |  |  |  | figs/m1_m2_utterance_information_deep_dive/predictor_correlation_heatmap.png |
| dual_effort | m1_dual_effort_predictions.png | M1 |  |  | figs/m1_m6_dual_effort_quick_share/m1_dual_effort_predictions.png |
| dual_effort | m2_dual_effort_predictions.png | M2 |  |  | figs/m1_m6_dual_effort_quick_share/m2_dual_effort_predictions.png |
| dual_effort | m3_dual_effort_predictions.png | M3 |  |  | figs/m1_m6_dual_effort_quick_share/m3_dual_effort_predictions.png |
| dual_effort | m4_dual_effort_predictions.png | M4 |  |  | figs/m1_m6_dual_effort_quick_share/m4_dual_effort_predictions.png |
| dual_effort | m5_dual_effort_predictions.png | M5 |  |  | figs/m1_m6_dual_effort_quick_share/m5_dual_effort_predictions.png |
| dual_effort | m6_dual_effort_predictions.png | M6 |  |  | figs/m1_m6_dual_effort_quick_share/m6_dual_effort_predictions.png |
| fixed_slices | m1_granular_primary_fixed_effort_slices.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_granular_primary_fixed_effort_slices.png |
| fixed_slices | m1_marginal_adjusted_global_trends.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_marginal_adjusted_global_trends.png |
| fixed_slices | m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m1_top_frequency_12_fixed_effort_slices.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M1 |  |  | figs/m1_m6_fixed_effort_slices/m1_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m2_granular_primary_fixed_effort_slices.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_granular_primary_fixed_effort_slices.png |
| fixed_slices | m2_marginal_adjusted_global_trends.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_marginal_adjusted_global_trends.png |
| fixed_slices | m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m2_top_frequency_12_fixed_effort_slices.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M2 |  |  | figs/m1_m6_fixed_effort_slices/m2_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m3_granular_primary_fixed_effort_slices.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_granular_primary_fixed_effort_slices.png |
| fixed_slices | m3_marginal_adjusted_global_trends.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_marginal_adjusted_global_trends.png |
| fixed_slices | m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m3_top_frequency_12_fixed_effort_slices.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M3 |  |  | figs/m1_m6_fixed_effort_slices/m3_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m4_granular_primary_fixed_effort_slices.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_granular_primary_fixed_effort_slices.png |
| fixed_slices | m4_marginal_adjusted_global_trends.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_marginal_adjusted_global_trends.png |
| fixed_slices | m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m4_top_frequency_12_fixed_effort_slices.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M4 |  |  | figs/m1_m6_fixed_effort_slices/m4_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m5_granular_primary_fixed_effort_slices.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_granular_primary_fixed_effort_slices.png |
| fixed_slices | m5_marginal_adjusted_global_trends.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_marginal_adjusted_global_trends.png |
| fixed_slices | m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m5_top_frequency_12_fixed_effort_slices.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M5 |  |  | figs/m1_m6_fixed_effort_slices/m5_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_slices | m6_granular_primary_fixed_effort_slices.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_granular_primary_fixed_effort_slices.png |
| fixed_slices | m6_marginal_adjusted_global_trends.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_marginal_adjusted_global_trends.png |
| fixed_slices | m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_primary_anchors_p25_p50_p75_fixed_effort_slices.png |
| fixed_slices | m6_top_frequency_12_fixed_effort_slices.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_top_frequency_12_fixed_effort_slices.png |
| fixed_slices | m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png | M6 |  |  | figs/m1_m6_fixed_effort_slices/m6_wide_anchors_p10_p50_p90_fixed_effort_slices.png |
| fixed_atlas | atlas_effort_bin_distribution.png |  |  |  | figs/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution.png |
| fixed_atlas | atlas_effort_bin_distribution_by_age.png |  |  |  | figs/m1_m6_fixed_effort_atlas/atlas_effort_bin_distribution_by_age.png |
| fixed_atlas | m1_nb_morphemes_atlas_bins.png | M1 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m1_nb_morphemes_atlas_bins.png |
| fixed_atlas | m1_nb_phonemes_atlas_bins.png | M1 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m1_nb_phonemes_atlas_bins.png |
| fixed_atlas | m1_nb_syllables_cmu_or_pkg_atlas_bins.png | M1 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m1_nb_syllables_pkg_atlas_bins.png | M1 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m1_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m1_nb_words_atlas_bins.png | M1 |  | Words | figs/m1_m6_fixed_effort_atlas/m1_nb_words_atlas_bins.png |
| fixed_atlas | m2_nb_morphemes_atlas_bins.png | M2 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m2_nb_morphemes_atlas_bins.png |
| fixed_atlas | m2_nb_phonemes_atlas_bins.png | M2 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m2_nb_phonemes_atlas_bins.png |
| fixed_atlas | m2_nb_syllables_cmu_or_pkg_atlas_bins.png | M2 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m2_nb_syllables_pkg_atlas_bins.png | M2 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m2_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m2_nb_words_atlas_bins.png | M2 |  | Words | figs/m1_m6_fixed_effort_atlas/m2_nb_words_atlas_bins.png |
| fixed_atlas | m3_nb_morphemes_atlas_bins.png | M3 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m3_nb_morphemes_atlas_bins.png |
| fixed_atlas | m3_nb_phonemes_atlas_bins.png | M3 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m3_nb_phonemes_atlas_bins.png |
| fixed_atlas | m3_nb_syllables_cmu_or_pkg_atlas_bins.png | M3 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m3_nb_syllables_pkg_atlas_bins.png | M3 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m3_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m3_nb_words_atlas_bins.png | M3 |  | Words | figs/m1_m6_fixed_effort_atlas/m3_nb_words_atlas_bins.png |
| fixed_atlas | m4_nb_morphemes_atlas_bins.png | M4 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m4_nb_morphemes_atlas_bins.png |
| fixed_atlas | m4_nb_phonemes_atlas_bins.png | M4 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m4_nb_phonemes_atlas_bins.png |
| fixed_atlas | m4_nb_syllables_cmu_or_pkg_atlas_bins.png | M4 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m4_nb_syllables_pkg_atlas_bins.png | M4 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m4_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m4_nb_words_atlas_bins.png | M4 |  | Words | figs/m1_m6_fixed_effort_atlas/m4_nb_words_atlas_bins.png |
| fixed_atlas | m5_nb_morphemes_atlas_bins.png | M5 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m5_nb_morphemes_atlas_bins.png |
| fixed_atlas | m5_nb_phonemes_atlas_bins.png | M5 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m5_nb_phonemes_atlas_bins.png |
| fixed_atlas | m5_nb_syllables_cmu_or_pkg_atlas_bins.png | M5 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m5_nb_syllables_pkg_atlas_bins.png | M5 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m5_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m5_nb_words_atlas_bins.png | M5 |  | Words | figs/m1_m6_fixed_effort_atlas/m5_nb_words_atlas_bins.png |
| fixed_atlas | m6_nb_morphemes_atlas_bins.png | M6 |  | Morphemes | figs/m1_m6_fixed_effort_atlas/m6_nb_morphemes_atlas_bins.png |
| fixed_atlas | m6_nb_phonemes_atlas_bins.png | M6 |  | Phonemes | figs/m1_m6_fixed_effort_atlas/m6_nb_phonemes_atlas_bins.png |
| fixed_atlas | m6_nb_syllables_cmu_or_pkg_atlas_bins.png | M6 |  | Syllables: CMU/pkg | figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_cmu_or_pkg_atlas_bins.png |
| fixed_atlas | m6_nb_syllables_pkg_atlas_bins.png | M6 |  | Syllables: pkg | figs/m1_m6_fixed_effort_atlas/m6_nb_syllables_pkg_atlas_bins.png |
| fixed_atlas | m6_nb_words_atlas_bins.png | M6 |  | Words | figs/m1_m6_fixed_effort_atlas/m6_nb_words_atlas_bins.png |
| context_m1_m6 | k0_m1_nb_morphemes_fixed_effort_atlas.png | M1 | k0 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m1_nb_phonemes_fixed_effort_atlas.png | M1 | k0 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M1 | k0 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m1_nb_syllables_pkg_fixed_effort_atlas.png | M1 | k0 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m1_nb_words_fixed_effort_atlas.png | M1 | k0 | Words | figs/context_m1_m6_fixed_effort_atlas/k0_m1_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_morphemes_fixed_effort_atlas.png | M2 | k0 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_phonemes_fixed_effort_atlas.png | M2 | k0 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M2 | k0 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_syllables_pkg_fixed_effort_atlas.png | M2 | k0 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m2_nb_words_fixed_effort_atlas.png | M2 | k0 | Words | figs/context_m1_m6_fixed_effort_atlas/k0_m2_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_morphemes_fixed_effort_atlas.png | M3 | k0 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_phonemes_fixed_effort_atlas.png | M3 | k0 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M3 | k0 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_syllables_pkg_fixed_effort_atlas.png | M3 | k0 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k0_m3_nb_words_fixed_effort_atlas.png | M3 | k0 | Words | figs/context_m1_m6_fixed_effort_atlas/k0_m3_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_morphemes_fixed_effort_atlas.png | M1 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_phonemes_fixed_effort_atlas.png | M1 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M1 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_syllables_pkg_fixed_effort_atlas.png | M1 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m1_nb_words_fixed_effort_atlas.png | M1 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m1_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_morphemes_fixed_effort_atlas.png | M2 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_phonemes_fixed_effort_atlas.png | M2 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M2 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_syllables_pkg_fixed_effort_atlas.png | M2 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m2_nb_words_fixed_effort_atlas.png | M2 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m2_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_morphemes_fixed_effort_atlas.png | M3 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_phonemes_fixed_effort_atlas.png | M3 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M3 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_syllables_pkg_fixed_effort_atlas.png | M3 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m3_nb_words_fixed_effort_atlas.png | M3 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m3_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_morphemes_fixed_effort_atlas.png | M4 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_phonemes_fixed_effort_atlas.png | M4 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4e_nb_words_fixed_effort_atlas.png | M4 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m4e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_morphemes_fixed_effort_atlas.png | M4 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_phonemes_fixed_effort_atlas.png | M4 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4es_nb_words_fixed_effort_atlas.png | M4 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m4es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_morphemes_fixed_effort_atlas.png | M4 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_phonemes_fixed_effort_atlas.png | M4 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m4s_nb_words_fixed_effort_atlas.png | M4 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m4s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_morphemes_fixed_effort_atlas.png | M5 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_phonemes_fixed_effort_atlas.png | M5 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5e_nb_words_fixed_effort_atlas.png | M5 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m5e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_morphemes_fixed_effort_atlas.png | M5 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_phonemes_fixed_effort_atlas.png | M5 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5es_nb_words_fixed_effort_atlas.png | M5 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m5es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_morphemes_fixed_effort_atlas.png | M5 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_phonemes_fixed_effort_atlas.png | M5 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m5s_nb_words_fixed_effort_atlas.png | M5 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m5s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_morphemes_fixed_effort_atlas.png | M6 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_phonemes_fixed_effort_atlas.png | M6 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6e_nb_words_fixed_effort_atlas.png | M6 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m6e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_morphemes_fixed_effort_atlas.png | M6 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_phonemes_fixed_effort_atlas.png | M6 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6es_nb_words_fixed_effort_atlas.png | M6 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m6es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_morphemes_fixed_effort_atlas.png | M6 | k1 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_phonemes_fixed_effort_atlas.png | M6 | k1 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k1 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k1_m6s_nb_words_fixed_effort_atlas.png | M6 | k1 | Words | figs/context_m1_m6_fixed_effort_atlas/k1_m6s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_morphemes_fixed_effort_atlas.png | M1 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_phonemes_fixed_effort_atlas.png | M1 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M1 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_syllables_pkg_fixed_effort_atlas.png | M1 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m1_nb_words_fixed_effort_atlas.png | M1 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m1_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_morphemes_fixed_effort_atlas.png | M2 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_phonemes_fixed_effort_atlas.png | M2 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M2 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_syllables_pkg_fixed_effort_atlas.png | M2 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m2_nb_words_fixed_effort_atlas.png | M2 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m2_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_morphemes_fixed_effort_atlas.png | M3 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_phonemes_fixed_effort_atlas.png | M3 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M3 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_syllables_pkg_fixed_effort_atlas.png | M3 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m3_nb_words_fixed_effort_atlas.png | M3 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m3_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_morphemes_fixed_effort_atlas.png | M4 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_phonemes_fixed_effort_atlas.png | M4 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4e_nb_words_fixed_effort_atlas.png | M4 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m4e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_morphemes_fixed_effort_atlas.png | M4 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_phonemes_fixed_effort_atlas.png | M4 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4es_nb_words_fixed_effort_atlas.png | M4 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m4es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_morphemes_fixed_effort_atlas.png | M4 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_phonemes_fixed_effort_atlas.png | M4 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m4s_nb_words_fixed_effort_atlas.png | M4 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m4s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_morphemes_fixed_effort_atlas.png | M5 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_phonemes_fixed_effort_atlas.png | M5 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5e_nb_words_fixed_effort_atlas.png | M5 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m5e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_morphemes_fixed_effort_atlas.png | M5 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_phonemes_fixed_effort_atlas.png | M5 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5es_nb_words_fixed_effort_atlas.png | M5 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m5es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_morphemes_fixed_effort_atlas.png | M5 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_phonemes_fixed_effort_atlas.png | M5 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m5s_nb_words_fixed_effort_atlas.png | M5 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m5s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_morphemes_fixed_effort_atlas.png | M6 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_phonemes_fixed_effort_atlas.png | M6 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6e_nb_words_fixed_effort_atlas.png | M6 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m6e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_morphemes_fixed_effort_atlas.png | M6 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_phonemes_fixed_effort_atlas.png | M6 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6es_nb_words_fixed_effort_atlas.png | M6 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m6es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_morphemes_fixed_effort_atlas.png | M6 | k2 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_phonemes_fixed_effort_atlas.png | M6 | k2 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k2 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k2_m6s_nb_words_fixed_effort_atlas.png | M6 | k2 | Words | figs/context_m1_m6_fixed_effort_atlas/k2_m6s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_morphemes_fixed_effort_atlas.png | M1 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_phonemes_fixed_effort_atlas.png | M1 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M1 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_syllables_pkg_fixed_effort_atlas.png | M1 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m1_nb_words_fixed_effort_atlas.png | M1 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m1_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_morphemes_fixed_effort_atlas.png | M2 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_phonemes_fixed_effort_atlas.png | M2 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M2 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_syllables_pkg_fixed_effort_atlas.png | M2 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m2_nb_words_fixed_effort_atlas.png | M2 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m2_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_morphemes_fixed_effort_atlas.png | M3 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_phonemes_fixed_effort_atlas.png | M3 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M3 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_syllables_pkg_fixed_effort_atlas.png | M3 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m3_nb_words_fixed_effort_atlas.png | M3 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m3_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_morphemes_fixed_effort_atlas.png | M4 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_phonemes_fixed_effort_atlas.png | M4 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4e_nb_words_fixed_effort_atlas.png | M4 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m4e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_morphemes_fixed_effort_atlas.png | M4 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_phonemes_fixed_effort_atlas.png | M4 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4es_nb_words_fixed_effort_atlas.png | M4 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m4es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_morphemes_fixed_effort_atlas.png | M4 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_phonemes_fixed_effort_atlas.png | M4 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png | M4 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m4s_nb_words_fixed_effort_atlas.png | M4 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m4s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_morphemes_fixed_effort_atlas.png | M5 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_phonemes_fixed_effort_atlas.png | M5 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5e_nb_words_fixed_effort_atlas.png | M5 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m5e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_morphemes_fixed_effort_atlas.png | M5 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_phonemes_fixed_effort_atlas.png | M5 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5es_nb_words_fixed_effort_atlas.png | M5 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m5es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_morphemes_fixed_effort_atlas.png | M5 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_phonemes_fixed_effort_atlas.png | M5 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png | M5 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m5s_nb_words_fixed_effort_atlas.png | M5 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m5s_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_morphemes_fixed_effort_atlas.png | M6 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_phonemes_fixed_effort_atlas.png | M6 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6e_nb_words_fixed_effort_atlas.png | M6 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m6e_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_morphemes_fixed_effort_atlas.png | M6 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_phonemes_fixed_effort_atlas.png | M6 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6es_nb_words_fixed_effort_atlas.png | M6 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m6es_nb_words_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_morphemes_fixed_effort_atlas.png | M6 | k3 | Morphemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_morphemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_phonemes_fixed_effort_atlas.png | M6 | k3 | Phonemes | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_phonemes_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: CMU/pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png | M6 | k3 | Syllables: pkg | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_syllables_pkg_fixed_effort_atlas.png |
| context_m1_m6 | k3_m6s_nb_words_fixed_effort_atlas.png | M6 | k3 | Words | figs/context_m1_m6_fixed_effort_atlas/k3_m6s_nb_words_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_morphemes_fixed_effort_atlas.png |  | k0 | Morphemes | figs/context_fixed_effort_atlas/k0_cf0_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_phonemes_fixed_effort_atlas.png |  | k0 | Phonemes | figs/context_fixed_effort_atlas/k0_cf0_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k0 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png |  | k0 | Syllables: pkg | figs/context_fixed_effort_atlas/k0_cf0_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k0_cf0_nb_words_fixed_effort_atlas.png |  | k0 | Words | figs/context_fixed_effort_atlas/k0_cf0_nb_words_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_morphemes_fixed_effort_atlas.png |  | k1 | Morphemes | figs/context_fixed_effort_atlas/k1_cf0_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_phonemes_fixed_effort_atlas.png |  | k1 | Phonemes | figs/context_fixed_effort_atlas/k1_cf0_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k1 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png |  | k1 | Syllables: pkg | figs/context_fixed_effort_atlas/k1_cf0_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf0_nb_words_fixed_effort_atlas.png |  | k1 | Words | figs/context_fixed_effort_atlas/k1_cf0_nb_words_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_morphemes_fixed_effort_atlas.png |  | k1 | Morphemes | figs/context_fixed_effort_atlas/k1_cf1_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_phonemes_fixed_effort_atlas.png |  | k1 | Phonemes | figs/context_fixed_effort_atlas/k1_cf1_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k1 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png |  | k1 | Syllables: pkg | figs/context_fixed_effort_atlas/k1_cf1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf1_nb_words_fixed_effort_atlas.png |  | k1 | Words | figs/context_fixed_effort_atlas/k1_cf1_nb_words_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_morphemes_fixed_effort_atlas.png |  | k1 | Morphemes | figs/context_fixed_effort_atlas/k1_cf2_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_phonemes_fixed_effort_atlas.png |  | k1 | Phonemes | figs/context_fixed_effort_atlas/k1_cf2_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k1 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png |  | k1 | Syllables: pkg | figs/context_fixed_effort_atlas/k1_cf2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf2_nb_words_fixed_effort_atlas.png |  | k1 | Words | figs/context_fixed_effort_atlas/k1_cf2_nb_words_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_morphemes_fixed_effort_atlas.png |  | k1 | Morphemes | figs/context_fixed_effort_atlas/k1_cf3_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_phonemes_fixed_effort_atlas.png |  | k1 | Phonemes | figs/context_fixed_effort_atlas/k1_cf3_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k1 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png |  | k1 | Syllables: pkg | figs/context_fixed_effort_atlas/k1_cf3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k1_cf3_nb_words_fixed_effort_atlas.png |  | k1 | Words | figs/context_fixed_effort_atlas/k1_cf3_nb_words_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_morphemes_fixed_effort_atlas.png |  | k2 | Morphemes | figs/context_fixed_effort_atlas/k2_cf0_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_phonemes_fixed_effort_atlas.png |  | k2 | Phonemes | figs/context_fixed_effort_atlas/k2_cf0_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k2 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png |  | k2 | Syllables: pkg | figs/context_fixed_effort_atlas/k2_cf0_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf0_nb_words_fixed_effort_atlas.png |  | k2 | Words | figs/context_fixed_effort_atlas/k2_cf0_nb_words_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_morphemes_fixed_effort_atlas.png |  | k2 | Morphemes | figs/context_fixed_effort_atlas/k2_cf1_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_phonemes_fixed_effort_atlas.png |  | k2 | Phonemes | figs/context_fixed_effort_atlas/k2_cf1_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k2 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png |  | k2 | Syllables: pkg | figs/context_fixed_effort_atlas/k2_cf1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf1_nb_words_fixed_effort_atlas.png |  | k2 | Words | figs/context_fixed_effort_atlas/k2_cf1_nb_words_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_morphemes_fixed_effort_atlas.png |  | k2 | Morphemes | figs/context_fixed_effort_atlas/k2_cf2_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_phonemes_fixed_effort_atlas.png |  | k2 | Phonemes | figs/context_fixed_effort_atlas/k2_cf2_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k2 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png |  | k2 | Syllables: pkg | figs/context_fixed_effort_atlas/k2_cf2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf2_nb_words_fixed_effort_atlas.png |  | k2 | Words | figs/context_fixed_effort_atlas/k2_cf2_nb_words_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_morphemes_fixed_effort_atlas.png |  | k2 | Morphemes | figs/context_fixed_effort_atlas/k2_cf3_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_phonemes_fixed_effort_atlas.png |  | k2 | Phonemes | figs/context_fixed_effort_atlas/k2_cf3_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k2 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png |  | k2 | Syllables: pkg | figs/context_fixed_effort_atlas/k2_cf3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k2_cf3_nb_words_fixed_effort_atlas.png |  | k2 | Words | figs/context_fixed_effort_atlas/k2_cf3_nb_words_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_morphemes_fixed_effort_atlas.png |  | k3 | Morphemes | figs/context_fixed_effort_atlas/k3_cf0_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_phonemes_fixed_effort_atlas.png |  | k3 | Phonemes | figs/context_fixed_effort_atlas/k3_cf0_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k3 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png |  | k3 | Syllables: pkg | figs/context_fixed_effort_atlas/k3_cf0_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf0_nb_words_fixed_effort_atlas.png |  | k3 | Words | figs/context_fixed_effort_atlas/k3_cf0_nb_words_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_morphemes_fixed_effort_atlas.png |  | k3 | Morphemes | figs/context_fixed_effort_atlas/k3_cf1_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_phonemes_fixed_effort_atlas.png |  | k3 | Phonemes | figs/context_fixed_effort_atlas/k3_cf1_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k3 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png |  | k3 | Syllables: pkg | figs/context_fixed_effort_atlas/k3_cf1_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf1_nb_words_fixed_effort_atlas.png |  | k3 | Words | figs/context_fixed_effort_atlas/k3_cf1_nb_words_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_morphemes_fixed_effort_atlas.png |  | k3 | Morphemes | figs/context_fixed_effort_atlas/k3_cf2_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_phonemes_fixed_effort_atlas.png |  | k3 | Phonemes | figs/context_fixed_effort_atlas/k3_cf2_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k3 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png |  | k3 | Syllables: pkg | figs/context_fixed_effort_atlas/k3_cf2_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf2_nb_words_fixed_effort_atlas.png |  | k3 | Words | figs/context_fixed_effort_atlas/k3_cf2_nb_words_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_morphemes_fixed_effort_atlas.png |  | k3 | Morphemes | figs/context_fixed_effort_atlas/k3_cf3_nb_morphemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_phonemes_fixed_effort_atlas.png |  | k3 | Phonemes | figs/context_fixed_effort_atlas/k3_cf3_nb_phonemes_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |  | k3 | Syllables: CMU/pkg | figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_cmu_or_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png |  | k3 | Syllables: pkg | figs/context_fixed_effort_atlas/k3_cf3_nb_syllables_pkg_fixed_effort_atlas.png |
| context_adjunct | k3_cf3_nb_words_fixed_effort_atlas.png |  | k3 | Words | figs/context_fixed_effort_atlas/k3_cf3_nb_words_fixed_effort_atlas.png |
| robustness | age_bin_unit_support.png |  |  |  | figs/age_scrambling_robustness/age_bin_unit_support.png |
| robustness | balanced_bootstrap_age_slope_ci.png |  |  |  | figs/age_scrambling_robustness/balanced_bootstrap_age_slope_ci.png |
| robustness | m1_age_slope_robustness_intervals.png | M1 |  |  | figs/age_scrambling_robustness/m1_age_slope_robustness_intervals.png |
| robustness | m1_clear_robustness_regression_lines.png | M1 |  |  | figs/age_scrambling_robustness/m1_clear_robustness_regression_lines.png |
| robustness | m2_age_slope_robustness_intervals.png | M2 |  |  | figs/age_scrambling_robustness/m2_age_slope_robustness_intervals.png |
| robustness | m2_clear_robustness_regression_lines.png | M2 |  |  | figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png |
| robustness | m3_age_slope_robustness_intervals.png | M3 |  |  | figs/age_scrambling_robustness/m3_age_slope_robustness_intervals.png |
| robustness | m3_clear_robustness_regression_lines.png | M3 |  |  | figs/age_scrambling_robustness/m3_clear_robustness_regression_lines.png |
| robustness | m4_age_slope_robustness_intervals.png | M4 |  |  | figs/age_scrambling_robustness/m4_age_slope_robustness_intervals.png |
| robustness | m4_clear_robustness_regression_lines.png | M4 |  |  | figs/age_scrambling_robustness/m4_clear_robustness_regression_lines.png |
| robustness | m5_age_slope_robustness_intervals.png | M5 |  |  | figs/age_scrambling_robustness/m5_age_slope_robustness_intervals.png |
| robustness | m5_clear_robustness_regression_lines.png | M5 |  |  | figs/age_scrambling_robustness/m5_clear_robustness_regression_lines.png |
| robustness | m6_age_slope_robustness_intervals.png | M6 |  |  | figs/age_scrambling_robustness/m6_age_slope_robustness_intervals.png |
| robustness | m6_clear_robustness_regression_lines.png | M6 |  |  | figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png |
| robustness | observed_age_slope_overview.png |  |  |  | figs/age_scrambling_robustness/observed_age_slope_overview.png |
| robustness | robustness_outside_null_heatmap.png |  |  |  | figs/age_scrambling_robustness/robustness_outside_null_heatmap.png |
| m2_simple | m2_morphemes_fixed_effort_and_global_trend.png | M2 |  | Morphemes | figs/m2_simple_plots/m2_morphemes_fixed_effort_and_global_trend.png |
| m2_simple | m2_phonemes_fixed_effort_and_global_trend.png | M2 |  | Phonemes | figs/m2_simple_plots/m2_phonemes_fixed_effort_and_global_trend.png |
| m2_simple | m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png | M2 |  | Syllables: CMU/pkg | figs/m2_simple_plots/m2_syllables_cmu_pkg_fixed_effort_and_global_trend.png |
| m2_simple | m2_syllables_pkg_fixed_effort_and_global_trend.png | M2 |  | Syllables: pkg | figs/m2_simple_plots/m2_syllables_pkg_fixed_effort_and_global_trend.png |
| m2_simple | m2_words_fixed_effort_and_global_trend.png | M2 |  | Words | figs/m2_simple_plots/m2_words_fixed_effort_and_global_trend.png |