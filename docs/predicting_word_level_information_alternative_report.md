# Alternative Report: Word-Level Information, Form Cost, and Context

Working draft, June 2026

## Purpose

This is a separate discussion report. It should not replace the first
supervisor-facing report.

The first supervisor report should stay focused on Route 1:

```text
At the utterance level, does total information, measured with sum_bits, change
with age after controlling production effort and repeated observations from the
same children?
```

This alternative report asks a different follow-up question:

```text
Inside an utterance, how is information distributed across individual words,
and how does that relate to word-form cost, contextual support, and development?
```

The distinction matters. Route 1 treats the utterance as the unit of analysis.
The word-level route treats word uses and word types as the units of analysis.
The two can speak to each other, but they should not be mixed in the first
supervisor report.

## Available Word-Level Quantity

The word-level scoring pass assigns Mistral surprisal mass back to lexical word
spans. For each word occurrence, the available quantities include:

- the word form and its position in the utterance;
- total surprisal assigned to that word, `word_sum_bits`;
- form-cost proxies such as characters and syllables;
- normalized outcomes such as bits per character and bits per syllable;
- context window, speaker group, child, age, and utterance identifiers;
- token-level details showing which Mistral subword tokens contributed to the
  word-level value.

The most useful interpretation is:

```text
word_sum_bits = how unpredictable this particular word use was in this
conversational and utterance-internal context.
```

This is not identical to semantic informativeness. It is model-based contextual
unpredictability at the word-use level.

## Five Models To Discuss

### Model 1: Word-Type Form Cost Versus Average Informativity

**Question.** Are longer or more effortful word forms more informative on
average?

This is the closest analogue to a Levshina-style law-of-abbreviation analysis.
For each word type, average word-level surprisal across all its observed uses,
then ask whether more informative words are longer or more complex forms.

Core type-level formulas:

```text
word_char_len ~ neg_log2_frequency
word_char_len ~ average_word_informativity_bits
word_char_len ~ neg_log2_frequency + average_word_informativity_bits

word_syllable_count ~ neg_log2_frequency
word_syllable_count ~ average_word_informativity_bits
word_syllable_count ~ neg_log2_frequency + average_word_informativity_bits
```

Best use:

- This is the cleanest "word form cost vs contextual informativity" model.
- It tells us whether costly forms are associated with higher average
  contextual information.
- It should be fit separately for child speech and caretaker speech, and
  separately by context window.

Main caveat:

- Word frequency and word informativity are closely related. The key model is
  the combined one, because it asks whether contextual informativity adds
  anything beyond frequency.

What would be interesting:

- Longer words have higher average contextual informativity even after
  frequency is controlled.
- The relation is stronger in child speech, or changes by developmental age bin.

### Model 2: Same-Word Developmental Informativity

**Question.** For the same frequent words, do the contexts in which children use
them become more or less informative over development?

This model controls word identity. That is the critical move. Without word
identity controls, a developmental effect could simply mean that older children
use different words. With word identity controls, the model asks whether the
same words are used in different contextual conditions across age.

Core occurrence/cell-level formula:

```text
word_sum_bits ~ age + child identity + context window + word identity
```

By-context version:

```text
word_sum_bits ~ age + child identity + word identity
```

fit separately for `k0`, `k1`, `k2`, and `k3`.

Best use:

- This is the strongest developmental word-level model.
- It asks whether children's usage contexts change for the same lexical items.
- It is a good complement to Route 1 because it can explain whether an
  utterance-level age effect is driven by new vocabulary or by changing use of
  familiar words.

Main caveat:

- It should be restricted to frequent words with enough observations. Rare
  words cannot support stable word fixed effects.

What would be interesting:

- Same-word `word_sum_bits` decreases with age under `k3`: familiar words are
  being used in increasingly predictable discourse contexts.
- Same-word `word_sum_bits` increases with age under `k0`: older children use
  the same words in more internally complex utterance positions without relying
  on discourse context.
- The `k0` and `k3` age effects diverge, suggesting development in contextual
  embedding rather than only lexical choice.

### Model 3: Word-Level Context Gain

**Question.** Which individual words become easier to predict when discourse
context is added, and does that context support change with age?

For the same word occurrence, define:

```text
word_context_gain_k3 = word_sum_bits_k0 - word_sum_bits_k3
```

The same can be computed for `k1` and `k2`.

Core formula:

```text
word_context_gain ~ age
                  + word form cost
                  + word position
                  + child identity
                  + word identity
```

Optional context-window version:

```text
word_context_gain ~ age * context window
                  + word form cost
                  + word position
                  + child identity
                  + word identity
```

Best use:

- This directly asks whether the conversational context helps predict specific
  words.
- It separates residual word information from context support.
- It is especially useful for the question: are children increasingly using
  words that are supported by the preceding conversational context?

Main caveat:

- The k0 and k3 word rows need to be paired carefully by utterance and
  word index. This is a derived table, not a raw scoring output.

What would be interesting:

- Context gain increases with age for the same words.
- Longer or more specific word forms have larger context gain, suggesting that
  costly forms are used when context makes them recoverable.
- Context gain is stronger for later words in the utterance than for the first
  word, because previous target words also become part of the predictive
  context.

### Model 4: Word-Form Cost Versus Residual Contextual Informativity

**Question.** Do costly word forms carry more residual information after
context is known, and does this relation change with age?

This is subtly different from Model 1. Model 1 is type-level: average
informativity of a word type. Model 4 is occurrence-level: whether a costly word
form is used in a high- or low-information position on a particular occasion.

Core formula:

```text
word_sum_bits ~ age
              + word form cost
              + age:word form cost
              + word frequency
              + word position
              + context window
              + child identity
```

Stronger frequent-word version:

```text
word_sum_bits ~ age
              + age:word form cost
              + word position
              + context window
              + child identity
              + word identity
```

Best use:

- This gets closest to the phrase "word form cost vs contextual informativity."
- It asks whether effortful forms are reserved for more informative word uses.
- The age interaction asks whether this calibration changes developmentally.

Main caveat:

- If word identity is included, stable word-form cost is mostly absorbed by
  word fixed effects. Then the age interaction should be interpreted as a
  developmental moderation check, not as a simple between-word length effect.

What would be interesting:

- A positive form-cost effect: longer or syllabically heavier words carry more
  word-level information.
- A negative age by form-cost interaction: older children may use costly words
  in more predictable contexts, possibly because those words become routinized
  or better supported by discourse.
- A positive age by form-cost interaction: older children may reserve costly
  words for increasingly informative lexical choices.

### Model 5: Utterance-Level Sum Bits From Word-Level Lexical Profile

**Question.** Can we explain the utterance-level Route 1 result by looking at
the words inside the utterance?

This is the bridge back to the first supervisor report. The outcome remains
utterance-level `sum_bits`, but the predictors summarize the lexical and
word-form profile of the utterance.

Important guardrail:

Do not predict `sum_bits` using the same utterance's raw word surprisal values
as predictors. That would be almost tautological, because utterance `sum_bits`
is the sum of token or word surprisal mass.

Instead, use word-level predictors that are not just the same outcome
re-expressed. For example:

- mean word length in characters;
- mean syllable count;
- maximum word-form cost in the utterance;
- proportion of rare words;
- expected lexical informativity of the word types, estimated from other rows;
- number or proportion of high-cost words;
- word-position profile, such as whether the costly words occur early or late.

Core formula:

```text
sum_bits ~ age
         + child word count
         + child identity
         + mean word form cost
         + max word form cost
         + rare-word share
         + expected lexical informativity
         + context window
```

Model-comparison version:

```text
Base Route 1:
sum_bits ~ age + child word count + child identity

Lexical-profile extension:
sum_bits ~ age + child word count + child identity
         + lexical-profile predictors
```

Best use:

- This keeps the first report's outcome, `sum_bits`, but tests whether the age
  effect is explained by changes in lexical composition.
- It can tell us whether older children's lower or higher conditional
  information is due to using different kinds of words.
- It is the best bridge between Route 1 and the word-level route.

Main caveat:

- Expected lexical informativity must be estimated out of sample or at least
  outside the target utterance. Otherwise the model leaks the outcome into the
  predictors.

What would be interesting:

- The Route 1 age effect shrinks after adding lexical-profile predictors. That
  would suggest that developmental change in utterance information is partly
  lexical-compositional.
- The age effect remains. That would suggest Route 1 is not just about which
  word types children use, but about how whole utterances are structured in
  context.

## Suggested Discussion Order

For a supervisor meeting, the cleanest order is:

1. Keep the first report focused on Route 1 and utterance-level `sum_bits`.
2. Present this word-level report as a follow-up, not as a competing main
   analysis.
3. Start with Model 1 because it is the cleanest form-cost/informativity
   question.
4. Move to Model 2 because it is the strongest developmental word-use model.
5. Use Model 3 to connect word-level information to discourse context.
6. Use Model 5 only after the Route 1 result is established, because it asks
   whether word-level lexical composition explains the utterance-level effect.

## What Not To Claim Yet

Do not claim that word-level information is "better" than utterance-level
information. It answers a different question.

Do not claim that lower surprisal is automatically better or worse. Lower
surprisal means more predictable under the model. In child language, that could
reflect better contextual integration, routinization, caregiver scaffolding, or
less novel content.

Do not use a same-utterance word surprisal decomposition as a predictor of
`sum_bits` and treat it as explanatory. That is mostly arithmetic.

Do not put this in the first supervisor report unless the supervisor explicitly
asks for the next phase. The first report should make the Route 1 utterance
level argument cleanly.

## Recommended Next Step

The best immediate follow-up is to run and summarize the word-level model suite
in this order:

1. Model 1: type-level form cost versus average informativity.
2. Model 2: same-word developmental informativity with word identity controls.
3. Model 3: word-level context gain, after pairing k0 and contextual word rows.
4. Model 5: utterance-level lexical-profile extension of Route 1.

That sequence would let us say:

```text
The first report asks whether utterance-level information changes at fixed
effort. The follow-up asks where that information lives inside the utterance:
in word form cost, lexical choice, word identity, or contextual support.
```
