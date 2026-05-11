## General Introduction

This document describes the use of large language models thus far in this project.

Large language models are used here as scoring models. They are not necessarily the models that generated the utterances. Instead, they assign probabilities to utterances, which allows us to compute their surprisal.

In this project, I score both real child utterances and their model-generated utterances counterpart, in addition to caretakers utterances (father and mother). The same scoring procedure is therefore used for the following : 

- the original cleaned utterances;
- caretakers cleaned utterances
- the random-model utterances;
- the unigram-model utterances;
- the bigram-model utterances.

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