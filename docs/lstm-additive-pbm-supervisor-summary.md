# PBM Additive LSTM Baseline Summary

Date: 2026-05-28

This note summarizes the PBM LSTM utterance-generation run and the design
choices behind it. It is intended as a supervisor-facing explanation, not just
an implementation log.

## Purpose

The project already has matched-length generated baselines from random,
unigram, bigram, and trigram models. The LSTM baseline adds a stronger neural
generator while staying much smaller and more controlled than a pretrained LLM.

Question:

```text
Given recent caretaker speech, what child-like utterance would a small
recurrent model generate?
```

The generated utterances are later scored for surprisal in the same way as the
real child utterances and the random/unigram/bigram/trigram baselines.

## Relation To N-Gram Baselines

The n-gram baselines use a finite-context Markov approximation. For a word
sequence \(w_{1:T}\), the chain rule gives:

\[
P(w_{1:T}) = \prod_{t=1}^{T} P(w_t \mid w_{1:t-1})
\]

An n-gram language model approximates this as:

\[
P(w_{1:T}) \approx \prod_{t=1}^{T} P(w_t \mid w_{t-n+1:t-1})
\]

The random/unigram/bigram/trigram baselines differ in how much local word
history they use, but they remain frequency-based. In this repository, their
age dictionaries are additive: the first bin is `006-023`, then later bins add
successive 6-month windows.

For the PBM LSTM run, we preserved the same additive-information logic:

```text
target bin 006-023 -> train on 006-023
target bin 024-029 -> train on 006-029
target bin 030-035 -> train on 006-035
...
target bin 060-065 -> train on 006-065
```

This avoids letting the LSTM use older-child language to generate earlier-child
utterances.

## LSTM Model

The model is a word-level encoder-decoder LSTM. It is not pretrained.

The encoder receives bounded prior caretaker context:

\[
h^{enc}, c^{enc} = \operatorname{LSTM}_{enc}(x^{ctx}_{1:m})
\]

The decoder generates the child utterance autoregressively:

\[
h_t, c_t = \operatorname{LSTM}_{dec}(E(y_{t-1}), h_{t-1}, c_{t-1})
\]

\[
P(y_t \mid y_{<t}, x^{ctx}_{1:m}) =
\operatorname{softmax}(W h_t + b)
\]

Training minimizes child-token cross-entropy with teacher forcing:

\[
\mathcal{L} =
-\sum_{t=1}^{T} \log P(y_t^{gold} \mid y_{<t}^{gold}, x^{ctx}_{1:m})
\]

where \(x^{ctx}_{1:m}\) is the previous caretaker context and
\(y_{1:T}\) is the child utterance.

## Context Windows

We trained separate context-window conditions:

```text
k=3: previous 3 caretaker utterances
k=4: previous 4 caretaker utterances
k=5: previous 5 caretaker utterances
```

Each context is capped at 60 word tokens. This gives the model a fair chance to
use short local conversational episodes while preventing unbounded transcript
history.

This choice is distinct from scoring context. In generation, context is the
input used to produce a synthetic child utterance. In surprisal scoring, context
is the conditioning text used to score an already chosen target utterance.

## Length Control

The main PBM run generated same-length outputs only:

```text
lstm_additive_k3_same_length_utterance
lstm_additive_k4_same_length_utterance
lstm_additive_k5_same_length_utterance
```

For each real child utterance, the generated utterance has the same number of
word tokens. If the child utterance has length \(T\), decoding is forced to
produce \(T\) lexical tokens:

\[
|\hat{y}_{1:T}| = |y_{1:T}|
\]

This makes the LSTM baseline comparable to the random/unigram/bigram/trigram
controls, which are also matched for word-count effort.

## Scoring Context Contract

The LSTM context window used to generate an utterance is not the same object as
the context window used later for surprisal scoring.

For scoring, every target utterance must remain paired with the exact
row-matched scoring contexts:

```text
context_k1, context_k2, context_k3
```

This applies to real child utterances, generated child-like baselines, and
caretaker utterances. In practice:

- `chi.surprisal_scoring_with_lstm_additive.csv` contains the real child
  utterance, the random/unigram/bigram/trigram baselines, the LSTM generated
  columns, and the same row's `context_k1`, `context_k2`, and `context_k3`.
- `caretakers.surprisal_scoring.csv` contains caretaker target utterances with
  their own matched `context_k1`, `context_k2`, and `context_k3`.
- The generated LSTM utterances should be scored under the same scoring context
  rows as the real child utterance they replace, so effort-controlled generated
  baselines and real child utterances are compared under matched conversational
  information.

Formally, for a target column \(u^{(m)}_i\), where \(m\) may be the real child
utterance or one generated baseline, scoring should estimate:

\[
S_{i,k}^{(m)} = - \log P_{\mathrm{score}}(u_i^{(m)} \mid c_{i,k})
\]

where \(c_{i,k}\) is the row-matched scoring context from `context_k1`,
`context_k2`, or `context_k3`. Generated utterances should not be scored using
contexts from other rows or using the generation-time LSTM context window as if
it were the scorer context.

## Input And Output Vocabularies

The LSTM uses a shared token vocabulary internally so that the encoder can read
caretaker context words and the decoder can represent child utterance words in
one embedding space. However, generation is constrained by a child-side output
vocabulary.

For each additive age-bin model:

```text
shared model vocabulary = caretaker context tokens + child target tokens
allowed generated output vocabulary = child target tokens only
```

Thus, caretaker-only words can help condition the model as input context, but
they cannot be sampled as generated child baseline words unless they have also
appeared in child utterances in the cumulative training data for that age bin.

This preserves the scientific interpretation of the generated baseline:

```text
parents provide context; children define the output lexicon
```

The run manifest records both `vocab_size` and `child_output_vocab_size` for
each context-window/age-bin model.

## Data Scope

This run used only:

```text
Brown
Manchester
Providence
```

Reason: PBM is the subset already used in earlier baseline work, and the
supervisor asked not to scale the experiment prematurely. The PBM subset is
large enough for a small LSTM:

```text
21 child folders
446,508 generated child rows per LSTM context condition
```

## Run Output

Run directory:

```text
results/lstm_baselines/pbm_additive_merged_006_023_k3_k4_k5_same_length/
```

Per-child sibling files:

```text
chi.lstm_additive_generated.csv
chi.shared_caretaker_contexts.with_lstm_additive.csv
chi.surprisal_scoring_with_lstm_additive.csv
```

Run-level diagnostics include:

```text
model_run_manifest.csv
training_summary.csv
generation_summary.csv
generation_diagnostics.csv
generation_samples.csv
plots/*.png
plots/*.pdf
```

Each age-bin/context model also has:

```text
model.pt
vocab.json
config.json
training_summary.csv
batch_training_log.csv
```

## Verification

Validation after the run:

```text
generated files: 21
child rows checked: 519,803
generated rows per LSTM column: 446,508
same-length mismatches: 0
context-with-LSTM files: 21
scoring-with-LSTM files: 21
scoring rows: 446,985
```

The generated same-length columns are ready to be sent to the surprisal scoring
pipeline.

## Next Possible Steps

- Score the three LSTM same-length columns with the same surprisal model and
  merge them into the PBM baseline comparison.
- Compare developmental curves for random, unigram, bigram, trigram,
  `lstm_additive_k3`, `lstm_additive_k4`, `lstm_additive_k5`, and real child
  utterances.
- Optionally run a separate free-length LSTM generation pass to study whether
  the model chooses child-like utterance lengths from context.
- Optionally add a held-out-corpus design later if the goal shifts from
  baseline generation to out-of-sample generalization.
