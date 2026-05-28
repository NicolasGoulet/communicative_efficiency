## General Introduction

This document describes the use of large language models thus far in this project.

Large language models are used here as scoring models. They are not necessarily the models that generated the utterances. Instead, they assign probabilities to utterances, which allows us to compute their surprisal.

In this project, I score both real child utterances and their model-generated utterances counterpart, in addition to caretakers utterances (father and mother). The same scoring procedure is therefore used for the following:

- the original cleaned utterances;
- caretakers cleaned utterances
- the random-model utterances;
- the unigram-model utterances;
- the bigram-model utterances.
- the trigram-model utterances;
- the LSTM-model utterances.

The goal is to measure how surprising each utterance is under a chosen language model.

## Computing Surprisal

Surprisal measures how unexpected a token is according to a language model.

For a token $x_i$, surprisal is defined as:

$$
S(x_i) = -\log_2 P(x_i \mid x_{<i})
$$

where $x_{<i}$ represents the tokens that come before $x_i$.

For a full utterance $x_{1:n}$, the total surprisal is:

$$
S(x_{1:n})
=
\sum_{i=1}^{n}
-\log_2 P(x_i \mid x_{<i})
$$

The mean surprisal per token is:

$$
\bar{S}(x_{1:n})
=
\frac{1}{n}
\sum_{i=1}^{n}
-\log_2 P(x_i \mid x_{<i})
$$

In the output files, this corresponds to:

- `sum_bits`: the total surprisal of the utterance;
- `mean_bits_per_token`: the average surprisal per token;
- `n_eval_tokens`: the number of tokens scored.

## Scoring Without Context

Without context, the model only sees the target utterance:

$$
x_{1:n} = (x_1, x_2, \dots, x_n)
$$

Each token is scored using only the previous tokens in the same utterance:

$$
P(x_i \mid x_{<i})
$$

So the surprisal is:

$$
S_{\text{no-context}}(x_{1:n})
=
\sum_{i=1}^{n}
-\log_2 P(x_i \mid x_{<i})
$$

## Scoring With Context

With context, the model receives previous conversational material before the target utterance.

Let $c$ be the context and $x_{1:n}$ be the target utterance.

The model input is:

$$
(c, x_1, x_2, \dots, x_n)
$$

However, only the target utterance is scored. The context is used only to condition the model.

The surprisal with context is:

$$
S_{\text{context}}(x_{1:n} \mid c)
=
\sum_{i=1}^{n}
-\log_2 P(x_i \mid c, x_{<i})
$$


## Choosing a Model for Scoring

To chose a model to score utterances, we screened a couple of smaller LLMs TODO.

## Choosing a Model for Generating Utterances

The frequentist generation baselines are random, unigram, bigram, and trigram.
These are useful controls, but even the trigram model only uses a short
hand-built context.

`src/generate_lstm_utterances.py` adds a word-level LSTM generation baseline.
The default architecture is now `seq2seq_lstm`, an encoder-decoder model:

```text
encoder input: caretaker context tokens
decoder input: <bos> + child utterance prefix
decoder target: child utterance tokens
```

This directly represents the idea "given recent caretaker speech, generate the
child response." The encoder receives only the configurable caretaker context,
and the decoder is trained to produce the child utterance.

The older `causal_lstm` architecture is still available for comparison. It
trains examples shaped as:

```text
caretaker context tokens + <bos> -> child utterance tokens
```

In the `causal_lstm` case, the training loss is masked over the caretaker
context tokens. This means the context conditions the LSTM hidden state, but
the model is only trained to predict the child utterance.

The LSTM generator now has two length modes:

- `--generation_length_mode same_as_child`: the default matched-effort control.
  Generation samples exactly the same number of word tokens as the real child
  utterance. This makes the LSTM directly comparable to the random, unigram,
  bigram, and trigram controls that are also matched to child utterance length.
- `--generation_length_mode free_until_eos`: the model samples until it emits
  `<eos>` or reaches `--max_generated_tokens`. This lets the LSTM choose an
  answer length from the caretaker context, which is useful for comparing model
  communicative effort against children rather than holding effort fixed.

The script is deliberately configurable because this baseline is experimental.
Important flags include:

- `--context_utterances`: number of previous caretaker utterances used.
- `--max_context_tokens`: maximum number of context tokens retained from those utterances.
- `--architecture`: `seq2seq_lstm` by default, or `causal_lstm` for the prefix-style comparison.
- `--max_train_examples`: optional cap on the number of training examples.
- `--max_generate_rows_per_child`: optional cap on generated rows per child.
- `--generation_length_mode`: `same_as_child` for matched-length controls, or
  `free_until_eos` for model-chosen answer length.
- `--max_generated_tokens`, `--min_generated_tokens`: caps for free-length
  generation.
- `--embedding_dim`, `--hidden_dim`, `--num_layers`, `--dropout`: model size.
- `--temperature`, `--top_k`: sampling behavior.

Actual training/generation requires PyTorch. PyTorch is now listed in the
project dependencies so the encoder-decoder LSTM can be trained through `uv`.
