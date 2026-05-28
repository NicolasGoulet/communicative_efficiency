## General Introduction 

This document describes the various frequentist models I am using to generate utterances.

All language models are trained using pre-determined k-month age bins. The
current default is 6 months.

The general idea is as follow : 

0. Use the preprocessed utterances from the raw CHAT format (the preprocessing in described in TODO.md). 
1. Chose a k size (the number of months to consider)
2. Group utterances from every used CHILDES dataset depending on k. For example, if k=6, all utterances between 12-17, 18-23 etc form individual bins from which vocabularies are built. 
3. Inside each individual bin, raw counts are collected.
4. The final dictionary for each bin is additive: it contains that bin plus all
previous bins in the same scope.
5. Then, for each given utterance, we build an utterance of the same length using a frequentist model.

This can be written as follows.

Let $k$ be the size of the age bin in months. Let $\mathcal{U}$ be the set of all preprocessed utterances, and let $a(u)$ be the age in months associated with utterance $u$.

For each bin \(j\), I group utterances according to age:

$$
B_j^{(k)}
=
\{u \in \mathcal{U} : jk \leq a(u) < (j+1)k\}
$$

Each bin therefore contains all utterances whose age falls inside the same \(k\)-month interval.

Then, I collect all tokens from the utterances in that bin:

$$
T_j^{(k)}
=
\mathrm{tokens}(B_j^{(k)})
$$

The vocabulary of the bin is the set of unique tokens appearing in that bin:

$$
V_j^{(k)}
=
\{w : w \in T_j^{(k)}\}
$$

For each word \(w\), I count how many times it appears in the bin:

$$
c_j^{(k)}(w)
=
\sum_{t \in T_j^{(k)}}
\mathbf{1}(t = w)
$$

The non-additive dictionary for the bin is then:

$$
D_j^{(k)}
=
\{(w, c_j^{(k)}(w)) : w \in V_j^{(k)}\}
$$

The dictionary actually written for bin \(j\) is cumulative:

$$
\tilde{D}_j^{(k)}
=
\sum_{i \leq j} D_i^{(k)}
$$

In other words, for each \(k\)-month age bin, the written vocabulary and count
dictionary include the current bin and all earlier bins.

## Random Language

This model assigns the same probability to every word in the vocabulary.

For a given age bin, let the vocabulary be:

$$
V = \{w_1, w_2, \dots, w_n\}
$$

where $n$ is the number of unique words in the vocabulary.

The random language model ignores word frequencies. This means that every word in $V$ has the same probability of being sampled:

$$
P(w_i) = \frac{1}{n}
$$

Equivalently, since $n = |V|$, we can write:

$$
P(w) = \frac{1}{|V|}
$$

for every word $w \in V$.

To generate an utterance of length $L$, the model samples $L$ words independently from the vocabulary:

$$
\hat{x}_1, \hat{x}_2, \dots, \hat{x}_L \sim \mathrm{Uniform}(V)
$$

In other words, each generated word $\hat{x}_i$ is sampled as:

$$
\hat{x}_i \sim \mathrm{Uniform}(V)
$$

for $i = 1, 2, \dots, L$.

This model only uses the vocabulary of the age bin. It does not use word frequencies, and it does not use word order.

## Unigram

This is a regular unigram model. It does not consider a context window.

Unlike the random language model, the unigram model does use word frequencies. Words that appear more often in the vocabulary of a given age bin are more likely to be sampled.

For a given age bin, let the vocabulary be:

$$
V = \{w_1, w_2, \dots, w_n\}
$$

For each word $w \in V$, let $c(w)$ be the number of times that word appears in the bin.

The total number of word tokens in the bin is:

$$
N = \sum_{v \in V} c(v)
$$

The unigram probability of a word $w$ is then:

$$
P(w) = \frac{c(w)}{N}
$$

Equivalently:

$$
P(w) = \frac{c(w)}{\sum_{v \in V} c(v)}
$$

To generate an utterance of length $L$, the model samples $L$ words independently from this probability distribution:

$$
\hat{x}_i \sim P(w)
$$

for $i = 1, 2, \dots, L$.

This means that frequent words are more likely to appear in the generated utterance, but each word is still sampled independently. The model does not consider the previous word, the next word, or any larger context.

## Bigram

The bigram model has context window size 1.

This means that the model only looks at the immediately previous word when sampling the next word.

For a given age bin, let the vocabulary be:

$$
V = \{w_1, w_2, \dots, w_n\}
$$

For two words $u$ and $v$, let $c(u,v)$ be the number of times word $v$ appears
immediately after word $u$ in the bin. For child utterances, the first child
word also receives context from the most recent prior caretaker utterance in
the same session. If the caretaker utterance ends with \(p_1\) and the child
utterance is \(c_1, c_2, c_3\), the observed bigrams are:

$$
(p_1,c_1), (c_1,c_2), (c_2,c_3)
$$

The bigram probability is:

$$
P(v \mid u) =
\frac{c(u,v)}
{\sum_{v' \in V} c(u,v')}
$$

where $u$ is the previous word and $v$ is the next word.

To generate an utterance of length $L$, the first word is sampled from the last
word of the most recent prior caretaker utterance when that context exists:

$$
\hat{x}_1 \sim P(w \mid p_1)
$$

Every following word is sampled from the bigram distribution of the previous
generated word.

If the previous word has no observed bigram distribution, the model backs off to the unigram model:

$$
\hat{x}_i \sim P_{\text{unigram}}(w)
$$

This model therefore uses simple word-order information: it learns which words tend to follow which other words. However, it only remembers one previous word.

## Trigram

The trigram model has context window size 2.

For a caretaker utterance ending in \(p_2, p_1\) and a child utterance
\(c_1, c_2, c_3\), the observed trigrams are:

$$
(p_2,p_1,c_1), (p_1,c_1,c_2), (c_1,c_2,c_3)
$$

If the previous caretaker utterance has only one token, the first trigram is not
invented; counting starts with \((p_1,c_1,c_2)\) when the child utterance is long
enough.

The conditional probability is:

$$
P(w_3 \mid w_1,w_2)
=
\frac{c(w_1,w_2,w_3)}
{\sum_{v \in V} c(w_1,w_2,v)}
$$

Generation uses the same boundary logic. The first generated word can condition
on \(p_2,p_1\), the second on \(p_1,\hat{x}_1\), and later words on the two most
recent generated words. If a trigram context is unseen, generation backs off to
the bigram model; if the bigram context is also unseen, it backs off to the
unigram model.

## Generated CSV Output

`src/add_random_and_unigram_utterances.py` writes one sibling file per child
folder:

```text
data/preprocessed_data/<DATASET>/<CHILD>/chi.ngram_generated.csv
```

The output keeps all original `chi.csv` rows and appends generated utterance
columns. The generated files use an explicit fixed column order and deliberately
omit `utt_id_role`, because it is not needed for scoring and was easy to confuse
with the main `utt_id` in spreadsheet views. For 6-month bins, the generated
columns are:

- `random_model_utterance_bin6`
- `unigram_model_utterance_bin6`
- `bigram_model_utterance_bin6`
- `trigram_model_utterance_bin6`

The output also includes explicit context-debugging columns:

- `caretaker_context_p2`: second-to-last token of the most recent prior
  caretaker utterance, when available.
- `caretaker_context_p1`: last token of the most recent prior caretaker
  utterance, when available.
- `caretaker_context_last_two`: the readable `p2 p1` pair.

These columns expose the exact boundary context used by bigram and trigram
generation for each child row. They are blank for rows without usable child
tokens, rows without usable age, or rows with no prior caretaker context in the
same session.
