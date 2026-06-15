# Interpretation Notes: M1-M6 Utterance Information Results

This document interprets the compact M1-M6 results in
`docs/utterance_information_m1_m6_quick_share.html`. It is separate from the
supervisor-facing report and is meant as a thinking document: what the current
models suggest, what they do not yet establish, and how they connect to the
communicative-efficiency questions motivating the project.

The current run used 446,985 real child utterance rows, 21 children, context window `k3`, and produced 60 fitted model rows.

## Scientific Question

The project is about communicative efficiency in child language: how children
package information while managing the amount of linguistic material they
produce. The current M1-M6 analyses focus on the **informativeness side** of
that question:

```text
Given a child utterance and its preceding caretaker context, does total
utterance surprisal change with age after controlling production effort?
```

Here, total information is `sum_bits`; effort is operationalized separately as
words, surface morphemes, two syllable estimates, and phonemes.

This is close to the first question Professor Xu articulated: whether children
optimize informativeness in their speech when utterance length or effort is
constrained. It is **not yet** the full second question: whether context
predictability causes children to shorten or lengthen their utterances. That
second question needs models where effort itself is the outcome, preferably
using response-level context entropy sampled from possible model responses.

## Main Takeaways

1. **Child identity is essential.** M1 pools children and gives weak or positive
   age patterns. M2 adds child identity and the continuous-effort versions show
   negative age effects across all five effort controls.

2. **The safest current result is the continuous-effort child-adjusted pattern.**
   In M2, M4, M5, and M6, the continuous-effort versions generally show that
   older children have lower predicted total bits for utterances with the same
   modeled effort.

3. **Low/mid/high effort groups are useful diagnostics, but not a replacement
   for exact effort control.** The effort-level models often reverse the M2-M5
   age direction. This likely happens because a low/mid/high group is coarse:
   utterances inside the same category can still differ substantially in exact
   words, morphemes, syllables, or phonemes.

4. **Current next-token context entropy behaves unexpectedly.** In M4-M6, the
   context-entropy coefficient is negative across all effort versions. This
   means that higher next-token entropy is associated with lower total child
   utterance bits after controls. This should not be overinterpreted as the
   final contextual-information result because this feature only measures
   uncertainty about the next token, not uncertainty over complete possible
   responses.

5. **The age-by-context interaction is weak in the continuous models.** M5 and
   M6 do not show a stable continuous-effort age-by-context-entropy interaction.
   This suggests that the current next-token entropy feature is not yet giving
   the developmental interaction that the larger efficiency hypothesis needs.

6. **M6 supports the broad robustness of the downward child-adjusted
   continuous-effort trend.** Even after adding multiple interactions, the
   continuous M6 age coefficients remain negative across all effort units,
   though not every one is significant.

## Results At A Glance

Age-effect signs by model and effort strategy:

| model | effort_strategy | coefficient | negative | positive | p<.05 | tested_effort_versions | coef_min | coef_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | continuous | age_coef | 0 | 5 | 2 | 5 | 0.0003087 | 0.06904 |
| M1 | effort_level | age_coef | 0 | 5 | 5 | 5 | 0.1334 | 0.1672 |
| M2 | continuous | age_coef | 5 | 0 | 5 | 5 | -0.1355 | -0.04846 |
| M2 | effort_level | age_coef | 0 | 5 | 5 | 5 | 0.07177 | 0.117 |
| M3 | continuous | age_coef | 5 | 0 | 4 | 5 | -0.1362 | -0.05214 |
| M3 | effort_level | age_coef | 5 | 0 | 3 | 5 | -0.07701 | -0.05571 |
| M4 | continuous | age_coef | 5 | 0 | 5 | 5 | -0.1401 | -0.04803 |
| M4 | effort_level | age_coef | 0 | 5 | 5 | 5 | 0.07374 | 0.1197 |
| M5 | continuous | age_coef | 5 | 0 | 5 | 5 | -0.1406 | -0.04848 |
| M5 | effort_level | age_coef | 0 | 5 | 5 | 5 | 0.07276 | 0.1181 |
| M6 | continuous | age_coef | 5 | 0 | 4 | 5 | -0.1417 | -0.05233 |
| M6 | effort_level | age_coef | 5 | 0 | 4 | 5 | -0.08116 | -0.05867 |

Context-entropy signs in the context models:

| model | effort_strategy | coefficient | negative | positive | p<.05 | tested_effort_versions | coef_min | coef_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4 | continuous | entropy_coef | 5 | 0 | 5 | 5 | -0.5814 | -0.4716 |
| M4 | effort_level | entropy_coef | 5 | 0 | 5 | 5 | -0.5842 | -0.4785 |
| M5 | continuous | entropy_coef | 5 | 0 | 5 | 5 | -0.5805 | -0.4704 |
| M5 | effort_level | entropy_coef | 5 | 0 | 5 | 5 | -0.5823 | -0.4758 |
| M6 | continuous | entropy_coef | 5 | 0 | 5 | 5 | -0.5854 | -0.4729 |
| M6 | effort_level | entropy_coef | 5 | 0 | 5 | 5 | -0.3802 | -0.3338 |

Interaction summaries:

| model | effort_strategy | coefficient | negative | positive | p<.05 | tested_effort_versions | coef_min | coef_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M3 | continuous | age_effort_coef | 1 | 4 | 1 | 5 | -0.003787 | 0.009859 |
| M3 | effort_level | age_effort_coef | 0 | 0 | 0 | 0 |  |  |
| M6 | continuous | age_effort_coef | 1 | 4 | 1 | 5 | -0.002441 | 0.01209 |
| M6 | effort_level | age_effort_coef | 0 | 0 | 0 | 0 |  |  |

| model | effort_strategy | coefficient | negative | positive | p<.05 | tested_effort_versions | coef_min | coef_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M5 | continuous | age_entropy_coef | 0 | 5 | 0 | 5 | 0.003946 | 0.006141 |
| M5 | effort_level | age_entropy_coef | 0 | 5 | 2 | 5 | 0.008078 | 0.01404 |
| M6 | continuous | age_entropy_coef | 0 | 5 | 0 | 5 | 0.005176 | 0.009103 |
| M6 | effort_level | age_entropy_coef | 0 | 5 | 0 | 5 | 0.002937 | 0.008538 |

## Model-by-Model Interpretation

### M1: pooled age plus effort

M1 asks the simplest question: if all child utterances are pooled together, does
age predict total bits after effort is controlled? The answer is not the one we
should treat as developmental evidence. The pooled continuous models are weak
or positive, and the effort-level versions are positive. This is exactly why M1
is useful: it shows the danger of ignoring which children contribute data at
which ages.

Interpretation: M1 is a baseline sanity check, not the primary model.

### M2: age plus effort plus child identity

M2 is the first serious developmental model in this set. It asks whether age
predicts total bits after controlling effort and giving each child their own
baseline.

The continuous-effort M2 versions are the clearest result: age coefficients are
negative for words, morphemes, both syllable estimates, and phonemes. This means
that, for the same modeled amount of linguistic material, older children
produce utterances that Mistral finds more predictable in context.

Compact M2 continuous-effort results:

| effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | 0.6259 | -0.1225 | <.001 | 6.367 | <.001 |  |  |  |  |  |  |
| Morphemes | 0.6131 | -0.1355 | <.001 | 5.489 | <.001 |  |  |  |  |  |  |
| Syllables: CMU/pkg | 0.6459 | -0.06326 | 0.018 | 5.236 | <.001 |  |  |  |  |  |  |
| Syllables: pkg | 0.6296 | -0.04846 | 0.049 | 4.831 | <.001 |  |  |  |  |  |  |
| Phonemes | 0.6443 | -0.06486 | 0.013 | 2.084 | <.001 |  |  |  |  |  |  |

Interpretation: this is consistent with a developmental shift toward more
contextually predictable, conventional, or efficiently recoverable utterances.
It should not be phrased as "children communicate less information" without the
effort and context caveats.

### M3: age by effort

M3 asks whether the relation between effort and total bits changes with age.
The continuous interaction term is not robust across effort units. The only
continuous age-by-effort interaction below p<.05 is:

```text
Syllables: pkg (0.00986)
```

Interpretation: there is not strong evidence yet that the information gained
per additional unit of effort changes systematically with age. The larger
developmental effect seems to be the age effect after effort control, not a
stable age-by-effort interaction.

### M4: adding context entropy

M4 adds current context entropy to the M2 structure. The intended question is
whether context predictability helps explain total utterance information after
age, effort, and child identity are controlled.

The continuous M4 models keep the M2 age pattern: age remains negative across
all effort units. Context entropy is also negative across all effort units.

Compact M4 continuous-effort results:

| effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | 0.6266 | -0.1269 | <.001 | 6.367 | <.001 | -0.4716 | <.001 |  |  |  |  |
| Morphemes | 0.6136 | -0.1401 | <.001 | 5.488 | <.001 | -0.5123 | <.001 |  |  |  |  |
| Syllables: CMU/pkg | 0.6468 | -0.06446 | 0.013 | 5.234 | <.001 | -0.5398 | <.001 |  |  |  |  |
| Syllables: pkg | 0.6304 | -0.04803 | 0.038 | 4.828 | <.001 | -0.541 | <.001 |  |  |  |  |
| Phonemes | 0.6453 | -0.06517 | 0.013 | 2.084 | <.001 | -0.5814 | <.001 |  |  |  |  |

Interpretation: the downward child-adjusted age pattern is not explained away
by the current next-token entropy feature. However, the entropy coefficient
itself is not straightforward. If this were a perfect measure of response-level
context uncertainty, one might expect higher entropy to predict higher
utterance information or more effort. Instead, the negative coefficient tells
us that this next-token entropy feature is probably capturing something more
local and should be treated as provisional.

### M5: age by context entropy

M5 tests whether the context-entropy association changes over development. In
the continuous-effort versions, the age-by-context interaction is not
significant for any effort unit:

```text
none
```

Compact M5 continuous-effort results:

| effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | 0.6266 | -0.1276 | <.001 | 6.367 | <.001 | -0.4704 | <.001 |  |  | 0.006141 | 0.284 |
| Morphemes | 0.6136 | -0.1406 | <.001 | 5.488 | <.001 | -0.5113 | <.001 |  |  | 0.004709 | 0.339 |
| Syllables: CMU/pkg | 0.6468 | -0.06492 | 0.015 | 5.234 | <.001 | -0.5391 | <.001 |  |  | 0.003955 | 0.478 |
| Syllables: pkg | 0.6304 | -0.04848 | 0.042 | 4.829 | <.001 | -0.5403 | <.001 |  |  | 0.003946 | 0.481 |
| Phonemes | 0.6453 | -0.06571 | 0.014 | 2.084 | <.001 | -0.5805 | <.001 |  |  | 0.00465 | 0.407 |

Interpretation: with the current next-token entropy feature, we do not yet have
strong evidence that the context-information relation changes with age. This is
a key reason to build the response-level entropy feature discussed after the
meeting.

### M6: interaction-rich stress test

M6 asks whether the main conclusions survive a more flexible model with
age-by-effort, age-by-context, and effort-by-context interactions. This is not
the cleanest primary model, but it is useful as a stress test.

Compact M6 continuous-effort results:

| effort_label | r2_observed_fitted | age_coef | age_p | effort_coef | effort_p | entropy_coef | entropy_p | age_effort_coef | age_effort_p | age_entropy_coef | age_entropy_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Words | 0.6266 | -0.1273 | <.001 | 6.376 | <.001 | -0.4729 | <.001 | -0.002441 | 0.726 | 0.009085 | 0.111 |
| Morphemes | 0.6137 | -0.1417 | <.001 | 5.479 | <.001 | -0.5165 | <.001 | 0.003897 | 0.575 | 0.009103 | 0.070 |
| Syllables: CMU/pkg | 0.6469 | -0.0679 | 0.016 | 5.213 | <.001 | -0.5431 | <.001 | 0.009024 | 0.154 | 0.00658 | 0.202 |
| Syllables: pkg | 0.6307 | -0.05233 | 0.053 | 4.799 | <.001 | -0.5436 | <.001 | 0.01209 | 0.017 | 0.005176 | 0.277 |
| Phonemes | 0.6455 | -0.06846 | 0.019 | 2.076 | <.001 | -0.5854 | <.001 | 0.003548 | 0.200 | 0.00833 | 0.086 |

Interpretation: the continuous-effort M6 models still show negative age
coefficients across all five effort measures. This supports the robustness of
the child-adjusted continuous-effort result. At the same time, the interaction
terms are not stable enough to carry the central scientific claim.

## How This Relates To Communicative Efficiency

The current results speak to one side of communicative efficiency: the
information associated with the produced utterance once production effort is
controlled. The strongest current pattern is:

```text
older age + same modeled effort + same child baseline
    -> lower predicted total surprisal
```

Scientifically, this can be interpreted in several compatible ways:

- older children may produce utterances that are more conventional or expected
  in local conversational context;
- older children may rely more on context, producing utterances that carry less
  model-surprisal per controlled unit of surface material;
- the Mistral scorer may find older children's forms easier to predict because
  they are more adult-like or less noisy;
- the result is not, by itself, proof that children are "more efficient,"
  because efficiency depends on both information and effort in relation to
  communicative need.

The experimental work on communicative efficiency in children motivates asking
whether children become more adult-like in adapting message length to the
communicative situation. The learner-directed speech literature also reminds us
that more redundancy can be efficient when the listener or context requires it.
Therefore, lower or higher surprisal is not automatically good or bad; it has
to be interpreted relative to effort, context, and communicative recoverability.

The current M1-M6 results should therefore be framed as:

```text
evidence for developmental change in utterance-level information after effort
control, with child identity controlled
```

not yet as:

```text
complete evidence that children optimize production effort based on contextual
predictability
```

## What This Suggests For The Next Analyses

1. Keep the continuous-effort child-adjusted models as the primary
   utterance-information evidence.

2. Treat low/mid/high effort-group models as robustness checks and visual
   diagnostics, not as the main effort control.

3. Use the next-token context entropy results only provisionally. They are
   useful because they show that adding a context-predictability feature does
   not remove the age effect, but they are not the final answer to the
   contextual-efficiency question.

4. Build response-level context entropy from sampled possible responses. This
   better matches the supervisor discussion: given a caretaker context, how
   many plausible complete responses does the model see?

5. Add models where effort is the outcome:

```text
effort ~ age + response_entropy + context_length + question_type + child identity
```

This directly tests the production-effort prediction: children should produce
longer or more effortful utterances when the context leaves more uncertainty
about the appropriate response.

6. Compare children against baselines and caretakers after effort control. The
   current M1-M6 report is about real child utterances only; the broader
   efficiency interpretation needs child-vs-baseline and child-vs-caretaker
   comparisons.

## Literature Anchors

- Tal, Smith, Arnon, and Culbertson (2023) motivate the developmental question:
  communicative-efficiency behavior is present in young children and becomes
  more adult-like with age.
- Tal, Grossman, Rohde, and Arnon (2023) motivate the effort/redundancy side:
  speakers can efficiently produce more linguistic material when listeners are
  learners or comprehension difficulty is higher.
- Wang, Yu, and Shao (2026) motivate interaction-style models: efficient form
  choice can be shaped jointly by multiple surprisal sources, so context,
  effort, and age interactions are theoretically meaningful.
- The current response-level entropy note in this repo formalizes the next
  project step: sample possible full responses from a model and estimate the
  entropy of the response distribution.

## References

- Tal, S., Smith, K., Arnon, I., & Culbertson, J. (2023). Communicative
  efficiency is present in young children and becomes more adult-like with age.
  Proceedings of the Annual Meeting of the Cognitive Science Society, 45.
  https://escholarship.org/uc/item/7mm0z6fk
- Tal, S., Grossman, E., Rohde, H., & Arnon, I. (2023). Speakers use more
  redundant references with language learners: Evidence for
  communicatively-efficient referential choice. Journal of Memory and Language,
  128, 104378. https://doi.org/10.1016/j.jml.2022.104378
- Wang, G., Yu, M., & Shao, B. (2026). Efficient Communication in Word
  Formation: How Syntactic and Lexical Surprisal Jointly Shape English
  Conversion Over the Past Century. Cognitive Science.
  https://doi.org/10.1111/cogs.70202
