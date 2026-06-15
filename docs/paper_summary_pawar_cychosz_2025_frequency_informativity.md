# Paper Summary: Pawar and Cychosz 2025, Frequency and Informativity

Created: 2026-06-15

Source PDF:

```text
papers/Frequency and informativity.pdf
```

Paper:

```text
Pawar, A., & Cychosz, M. (2025).
Frequency and informativity of phonological input directed to children in the
first four years of life.
Proceedings of the Annual Meeting of the Cognitive Science Society, 47(0).
https://escholarship.org/uc/item/8jr9s9x6
```

## Why This Paper Matters For This Project

This paper is directly relevant because it uses CHILDES caregiver speech to ask
an information-theoretic developmental question: does child-directed speech
change its redundancy/informativity as children age?

The paper is not about Mistral, utterance-level surprisal, or child production.
It is about phonological input from caregivers. Still, its design is highly
useful for our project because it gives a concrete template for:

- age-binned CHILDES analyses;
- stabilizing information-theoretic estimates with bootstrap samples;
- equalizing sample size across age bins;
- using scrambling controls to check whether apparent developmental
  trajectories are artifacts of bin structure or sampling;
- separating frequency from informativity.

Most important correction for future agents: the paper does **not** take 100
utterances from each age bin. It takes 100 bootstrap samples per age bin, where
each sample contains 81,000 phones, while preserving full utterance lines so
that an utterance is not split mid-sample.

## One-Sentence Summary

Using more than 7.5 million phones from North American English caregiver speech
in CHILDES, Pawar and Cychosz find that phonological informativity in
child-directed speech increases from early infancy through toddlerhood and then
levels off, while the relative frequency of individual phones remains much more
stable.

## Research Questions

The paper asks:

1. How does the phonological structure of child-directed speech change across
   the first four years of childhood?
2. What is the relationship between phone frequency and phone informativity?
3. Does the relationship between frequency and informativity change across
   developmental time?

The broader theoretical framing is communicative efficiency: caregivers may
adjust the redundancy or information density of speech to match the child's
developing processing abilities.

## Data

The data are caregiver utterances from CHILDES.

Inclusion criteria:

- North American English;
- caregiver speech directed to typically developing children;
- child age approximately 3 to 45 months;
- naturalistic or semi-naturalistic speech;
- not book reading;
- transcripts available at the word level;
- corpora from the last 25 years.

Corpora:

| Corpus | Age range in months | Unique children |
|---|---:|---:|
| Brent/Siskind | 6-15 | 17 |
| Newman/Ratner | 7-24 | 121 |
| Providence | 12-36 | 6 |
| Rollins | 3-30 | 54 |
| VanKleeck | 36-48 | 20 |

Age bins are 6-month bins:

```text
3-8, 9-14, 15-20, 21-26, 27-32, 33-38, 39-44
```

Reason for 6-month bins:

- enough unique children per bin;
- enough data for stable phonological estimates;
- still fine-grained enough to track developmental change.

Important caveat:

Children can contribute to multiple age bins if they appear longitudinally.

## Data Preparation

The authors:

1. scraped transcripts with `childespy`, using the `childes-db` infrastructure;
2. filtered to caregiver speech only;
3. removed CHILDES transcription codes indicating non-speech sounds;
4. converted word-level transcripts to phones with Montreal Forced Aligner
   English G2P tools;
5. used the MFA English dictionary first;
6. used the rule-based G2P model for words not covered by the dictionary;
7. manually inspected the remaining out-of-vocabulary forms;
8. removed proper nouns and non-verbal expressions such as `muah` and `huh`;
9. corrected some non-standard allophonic outputs to standard American English
   representations.

Their motivation for re-phonemicizing even already phonemicized corpora was to
keep the phonemic transcription uniform across corpora.

## Information-Theoretic Measures

The paper computes two phone-level measures in bits.

### Relative Frequency

For phone `X`:

```text
relative_frequency(X) = -log2(count(X) / total_phone_count)
```

Because of the negative log:

- lower value means more frequent phone;
- higher value means less frequent phone.

The authors also describe this as non-contextual phonemic surprisal.

### Predictability

For phone `X` in context `C`:

```text
predictability(X, C) = -log2(count(X in context C) / count(context C))
```

The context is defined within the word:

```text
context of a phone = all preceding phones in the same word
```

Example logic:

If `[kaet]` appears 99 times and `[kaep]` appears once, and no other word begins
with `[kae]`, then:

```text
predictability([p] | [kae]) = -log2(0.01) = 6.64 bits
predictability([t] | [kae]) = -log2(0.99) = 0.01 bits
```

So `[p]` is more informative in that context.

### Informativity

Informativity averages predictability across the contexts where a phone occurs.

For phone `X`:

```text
informativity(X) = sum_C P(C | X) * predictability(X, C)
```

where:

```text
P(C | X) = count(X in context C) / count(X)
```

Interpretation:

- higher informativity means the phone is harder to predict in the contexts
  where it occurs;
- lower informativity means the phone is more redundant or predictable.

## The Key Sampling Method

This is the part most relevant to our project.

The authors wanted developmental effects to reflect age, not differences in how
much data was available in each age bin. They therefore used a quantitative
stability criterion to choose a fixed sample size for all age bins.

For each age bin:

1. They sampled phones while preserving complete utterance lines.
2. They did not break an utterance line in the middle while sampling.
3. They considered sample sizes from 3,000 to 300,000 phones, in increments of
   3,000.
4. At each sample size, they computed mean relative frequency and mean
   informativity.
5. They calculated the rolling standard deviation of these mean values using a
   sliding window of 10 samples.
6. They recorded the first sample size where both mean frequency and mean
   informativity had rolling standard deviation below 0.01.
7. They repeated this for every age bin.
8. They took the largest required minimum across age bins as the shared
   standard sample size.

The selected standard sample size was:

```text
81,000 phones per sample
```

Then, for the actual analysis:

```text
100 bootstrap samples per age bin
81,000 phones per sample
sampling with replacement
```

This means each plotted point/sample in their Figures 2 and 3 is not an
utterance. It is the average measure from one 81,000-phone bootstrap sample.

Their approach is inspired by Tal et al. 2024.

## Main Statistical Analyses

The authors treat child age categorically because the data are binned into
6-month intervals.

They use:

- one-way ANOVAs for the effect of age bin on relative frequency;
- one-way ANOVAs for the effect of age bin on informativity;
- Bonferroni-corrected pairwise comparisons between consecutive age bins;
- Pearson correlations between average phone relative frequency and average
  phone informativity within each age bin;
- two scrambling analyses to test whether developmental trajectories are
  artifacts of binning or sampling.

## Main Results

### Informativity Changes Strongly With Age

The effect of age on phonological informativity is strong:

```text
F(6) = 929
p < .001
partial eta squared = 0.89
```

Informativity increases from early infancy through toddlerhood and then levels
off in the preschool years.

Reported bin means for informativity:

| Age bin | Mean informativity |
|---|---:|
| 3-8 | 3.268 |
| 9-14 | 3.328 |
| 15-20 | 3.382 |
| 21-26 | 3.395 |
| 27-32 | 3.412 |
| 33-38 | 3.431 |
| 39-44 | 3.391 |

Bonferroni-corrected pairwise comparisons indicate significant differences
between consecutive bins from 3-8 through 33-38 months. The final preschool
period is described as a leveling-off period.

Interpretation:

```text
Phones in caregiver speech become less predictable in their within-word
contexts as children age.
```

In the paper's language, child-directed speech becomes less redundant and more
informative as children's processing capacities develop.

### Relative Frequency Is Much More Stable

The ANOVA for relative frequency is statistically significant:

```text
F(6) = 25
p < .001
partial eta squared = 0.18
```

But the effect is much smaller and less developmentally systematic than
informativity.

Reported bin means for relative frequency:

| Age bin | Mean relative frequency |
|---|---:|
| 3-8 | 6.294 |
| 9-14 | 6.282 |
| 15-20 | 6.294 |
| 21-26 | 6.297 |
| 27-32 | 6.284 |
| 33-38 | 6.280 |
| 39-44 | 6.277 |

Interpretation:

```text
The identity/frequency distribution of phones is relatively stable, but the
contexts in which phones occur become less predictable.
```

This distinction is important: the paper argues that the developmental change is
not simply that caregivers use different phones, but that phonological sequences
become less redundant in context.

## Scrambling Analyses

The scrambling analyses are the part we can most directly borrow.

The authors worry that the observed developmental trend might be an artifact of
which corpora, children, or samples happen to occur in each age bin. They
therefore run two controls.

### Scrambling Analysis 1: Preserve Group Structure, Shuffle Age Labels

They preserve the group structure:

```text
100 samples per original age bin stay together as a group
```

Then they randomly reassign age labels to those groups.

Example:

```text
the whole group originally from 3-8 months might be relabeled 33-38 months
```

The samples remain grouped, but the age-bin labels are scrambled.

Result:

- the consistent developmental trajectory disappears;
- age can still be statistically significant, but the direction alternates and
  no longer shows a meaningful monotonic developmental pattern.

Interpretation:

```text
The original increasing trajectory depends on the true ordering of child age.
```

### Scrambling Analysis 2: Shuffle Age Labels At The Individual Sample Level

They randomly reassign age labels to each individual sample independently.

Example:

```text
two samples originally from 15-20 months can be reassigned to different bins
```

Result:

```text
relative frequency: F(6) = 0.41, p = 0.87, partial eta squared = 0.004
informativity:      F(6) = 0.87, p = 0.52, partial eta squared = 0.008
```

Interpretation:

```text
When age labels are fully broken, age no longer predicts the measures.
```

Together, the two scrambling analyses support the claim that the observed
informativity trajectory reflects genuine age-related differences rather than
random variation due to sampling or bin composition.

## Frequency-Informativity Relationship

The paper also measures the correlation between average phone relative
frequency and average phone informativity within each age bin.

Across bins:

```text
mean Pearson r = 0.23
SD = 0.13
```

The relationship is significant or marginal in the first four consecutive age
bins:

```text
3-8, 9-14, 15-20, 21-26 months
```

It is no longer significant in older bins.

The authors compare this to adult-directed speech, where Cohen Priva and Jaeger
2018 estimated a stronger relationship around:

```text
r = 0.5
```

Interpretation:

```text
Frequency and informativity are related but not interchangeable.
```

This matters for us because utterance length, word frequency, Mistral surprisal,
and contextual predictability may also be correlated but not identical. We
should not collapse them into one variable without checking.

## Interpretation

The paper argues that caregiver speech becomes phonologically less redundant as
children age.

Possible developmental story:

1. Early in life, more redundant phonological input may help children establish
   phonological categories and phonotactic expectations.
2. As children mature, caregivers introduce more diverse lexical and
   phonological structures.
3. Individual phones therefore become harder to predict from their preceding
   within-word context.
4. This may reflect implicit tuning of input complexity to children's changing
   processing abilities.

The authors connect this to Tal et al. 2024, which found decreasing lexical
redundancy in infant-directed speech as infants aged.

## Limitations

Important limitations for our use:

- The paper studies caregiver speech, not child speech.
- The paper studies phones, not words or utterances.
- The paper studies within-word phonological context, not discourse context.
- The paper uses an idealized phonemic representation, not acoustic duration or
  reduction.
- The paper removes non-verbal expressions such as `muah` and `huh`, whereas in
  our project we explicitly care about non-standard child forms and fillers.
- The paper's informativity measure is not the same as response-space entropy.
- Their bootstrap units are phone samples drawn from corpus data, not LLM
  generations.

## How We Can Leverage This Paper

Yes, we can leverage this paper. The best parts to borrow are not the exact
phone-level formulas, but the stability and scrambling logic.

### 1. Use A Stability Criterion For Number Of LLM Samples

We currently discuss sampling:

```text
M = 100 model responses per context per temperature
```

Instead of treating 100 as arbitrary, we can adapt Pawar and Cychosz's sample
size logic.

For a response-entropy pilot:

```text
M in {10, 25, 50, 75, 100, 150, 200}
```

For each `M`, context window, and temperature:

1. sample responses;
2. compute response entropy;
3. repeat across seeds or split samples into repeated batches;
4. compute the variability of entropy estimates;
5. choose the smallest `M` where entropy estimates stabilize.

Possible stability criteria:

```text
rolling SD of entropy < threshold
split-half rank correlation > 0.90
mean absolute entropy difference between M and M+25 below threshold
regression coefficient direction stable across M
```

This is directly analogous to their choice of 81,000 phones.

### 2. Use Equalized Bootstrap Samples For Age-Bin Plots

The paper equalizes the amount of data per age bin before making age-bin
comparisons.

For our project, we can do the same for descriptive plots and robustness checks:

```text
same number of contexts or utterances per age bin
same number of bootstrap samples per age bin
same context-window distribution per age bin where possible
```

This matters because some age bins have many more utterances than others.

For final mixed models, we may still use all data with child/corpus controls.
But for descriptive developmental trajectories, equalized bootstrap plots are a
stronger way to show that a trend is not just driven by high-density bins.

### 3. Preserve Complete Interaction Units

They explicitly avoid breaking utterance lines while sampling phones.

For us, the equivalent rule should be:

```text
Do not break context-target interaction units.
```

If sampling rows for pilots or bootstraps, preserve:

- child id;
- dataset;
- age bin;
- context window text;
- target utterance;
- row provenance.

For generated response entropy, the context string is the sampling unit. The
response samples should be tied back to exactly that context string and its
provenance.

### 4. Add Scrambling Controls To Route 1

We can adapt both scrambling analyses.

#### Group-Level Age-Bin Scrambling

For age trajectory plots:

1. build bootstrap samples within true age bins;
2. preserve each bin's sample group;
3. randomly reassign age-bin labels to whole groups;
4. rerun the age trajectory analysis.

Expected result if developmental trajectory is real:

```text
true age labels show an interpretable developmental trend;
group-scrambled labels destroy or disorder the trend.
```

#### Sample-Level Age Scrambling

For each bootstrap sample or context sample:

1. randomly reassign age-bin labels independently;
2. rerun the model;
3. check whether the age effect disappears.

Expected result if age effect is real:

```text
true labels: age effect present;
sample-scrambled labels: age effect absent or negligible.
```

#### Context-Response Link Scrambling

This is especially relevant for response-space entropy.

After computing response entropy for contexts:

```text
shuffle response_entropy across contexts within the same age_bin and context_k
```

Then rerun:

```text
target_effort ~ age + response_entropy + controls
```

Expected result if response entropy is meaningful:

```text
true context-entropy pairing predicts effort better than shuffled pairing.
```

This is not in Pawar and Cychosz directly, but it follows their scrambling
logic.

### 5. Use Bootstrap Samples For Confidence Intervals

Their figures are not raw-row means. They show distributions over 100 bootstrap
samples per age bin.

For our reports, we can make analogous plots:

```text
100 bootstrap samples per age bin
compute mean sum_bits, mean effort, mean response_entropy, or model slopes
plot distribution across bootstrap samples
```

This would be much stronger than plotting only raw means, especially when age
bins have unequal numbers of utterances.

### 6. Separate Frequency, Effort, And Informativity

Their paper stresses that frequency and informativity are correlated but not the
same.

For us, analogous variables include:

- target effort;
- target frequency or lexical familiarity;
- target utterance surprisal;
- context next-token entropy;
- response-space entropy;
- expected sampled response length.

We should check collinearity, but we should not assume these measures are
interchangeable.

## Concrete Proposed Additions To Our Pipeline

Future agents can implement the following, inspired by this paper.

### A. Response-Entropy Sample-Size Pilot

Goal:

```text
Choose M samples per context scientifically instead of arbitrarily.
```

Inputs:

- stratified context manifest;
- context_k in `{k1, k2, k3}`;
- temperatures, for example `{0.3, 0.5, 0.7, 1.0, 1.3, 1.6}`;
- repeated seeds;
- M grid `{10, 25, 50, 75, 100, 150, 200}`.

Outputs:

- entropy stability table;
- split-half reliability table;
- rank-correlation matrix by M and temperature;
- recommended M.

### B. Age-Bin Equalized Bootstrap Report

Goal:

```text
Show developmental trajectories are not artifacts of uneven data density.
```

For each age bin:

1. sample the same number of utterances or contexts;
2. repeat 100 times;
3. compute mean outcomes and predictors;
4. plot distributions by age bin.

Candidate outcomes:

- mean Mistral bits;
- bits per word;
- bits per morpheme;
- effort counts;
- response-space entropy;
- expected sampled response length.

### C. Scrambling-Control Report

Goal:

```text
Show that age and context effects depend on true age/context structure.
```

Controls:

1. group-level age-bin label shuffle;
2. sample-level age-bin label shuffle;
3. context-entropy shuffle within age bin and context window;
4. target utterance shuffle within child/session as a more aggressive control.

Outputs:

- true model slope versus scrambled slope distributions;
- permutation p-values;
- age trajectory plots for true and scrambled labels;
- model performance comparison.

## What Not To Copy Blindly

Do not copy these parts without adapting them:

- Their sample size is phones, not utterances.
- Their standard sample size of 81,000 phones does not map directly to our
  utterance-level or response-entropy analyses.
- Their 100 samples are bootstrap samples, not LLM generations.
- Their context is within-word phonological context, not discourse context.
- Their removal of fillers/non-verbal expressions does not match our decision
  to keep many CHILDES special forms and fillers.
- Their ANOVA approach is fine for their binned bootstrap design, but our
  child-level longitudinal models likely need child/corpus controls or mixed /
  clustered models.

## Short Answer To The User's Specific Question

Could we leverage the paper's 100-sample and scrambling method?

Yes, absolutely, but with a correction:

```text
They did not sample 100 utterances.
They drew 100 bootstrap samples per age bin, each containing 81,000 phones,
and then used scrambling controls to test whether the age trajectory survived
only under true age structure.
```

For our project, the analogous design would be:

```text
100 bootstrap samples per age bin/context window,
or 100 generated responses per context/temperature,
plus stability checks and scrambling controls.
```

The strongest direct borrowing is:

```text
Before committing to M=100 sampled LLM responses, run a sample-size stability
pilot and justify M using an empirical stability threshold, exactly like they
justified 81,000 phones per sample.
```

The second strongest borrowing is:

```text
After fitting developmental models, run age-label and context-link scrambling
controls to show that the developmental/contextual effects disappear when the
relevant structure is broken.
```

## Agentic Checklist

When a future agent uses this paper, it should:

1. cite it as a CHILDES information-theoretic developmental precedent;
2. remember it is caregiver input, not child output;
3. remember it is phone-level, not utterance-level;
4. use its bootstrap/sample-size logic to justify response-entropy sample count;
5. use its scrambling controls as inspiration for age/context permutation
   controls;
6. not claim that our response-space entropy is the same as their
   informativity;
7. not claim that they sampled 100 utterances;
8. consider adding an equalized age-bin bootstrap report before presenting age
   trajectories to supervisors.

