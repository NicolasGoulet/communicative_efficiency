# Formal Mathematical Definitions

*July report · methods reference*

This page fixes the notation for the quantities used in the current analyses.
It distinguishes four objects that should not be treated as synonyms:
target-utterance information, context-only uncertainty, sampled response-space
uncertainty, and the legacy and corrected Bayes-derived scores. All logarithms
are base 2 unless stated otherwise, so information is measured in **bits**.

## 1. Units and notation

For observation $i$, let

$$
c_i^{(k)} = \text{the preceding caretaker context at window }k,
\qquad
u_i=(x_{i1},\ldots,x_{iT_i}) = \text{the target child utterance}.
$$

Here $x_{it}$ is a language-model tokenizer token and $T_i$ is the number
of evaluated target tokens. The context windows are $k=0,1,2,3$: $k=0$
contains no preceding caretaker utterance, while $k=1,2,3$ contain the most
recent one, two, or three caretaker utterances. Tokenizer-token count $T_i$
is not the same as the word, morpheme, syllable, or phoneme counts used as
production-effort measures.

## 2. Target surprisal and utterance information

### Token surprisal

$$
s_{it}^{(k)}
=-\log_2 p_\theta\!\left(x_{it}\mid c_i^{(k)},x_{i,<t}\right).
\tag{1}
$$

$p_\theta$ is the probability assigned by the scoring language model;
$x_{i,<t}$ is the already observed part of the target. A high value means the
observed token was less predictable to the model. The scorer obtains
probabilities with a log-softmax and converts natural-log units to bits by
dividing by $\ln 2$.

### Total utterance information

$$
I_\theta^{(k)}(u_i)
=\sum_{t=1}^{T_i}s_{it}^{(k)}
=-\log_2\prod_{t=1}^{T_i}
p_\theta\!\left(x_{it}\mid c_i^{(k)},x_{i,<t}\right).
\tag{2}
$$

This is the implemented `sum_bits` measure. Only tokenizer tokens that overlap
the target span enter the sum: context tokens condition the prediction but are
never counted as target information.

### Mean information per evaluated token

$$
\bar I_{i,\mathrm{tok}}^{(k)}
=\frac{I_\theta^{(k)}(u_i)}{T_i},\qquad T_i>0.
\tag{3}
$$

This is `mean_bits_per_token`. It is useful descriptively, but the main
fixed-effort models use total utterance information as the outcome.

### Information gained from context

$$
G_i^{(k)}=I_\theta^{(0)}(u_i)-I_\theta^{(k)}(u_i).
\tag{4}
$$

Positive $G_i^{(k)}$ means the caretaker context made the observed child
utterance more predictable than the no-context score. Negative values mean the
specified context increased its surprisal.

## 3. Context-only uncertainty

Let $V_\theta$ be the scoring model's tokenizer vocabulary and let
$p_\theta(v\mid c_i^{(k)})$ be its next-token distribution after seeing only
the context. The target utterance is not shown to the model when this feature
is computed.

$$
H_{\mathrm{next}}\!\left(c_i^{(k)}\right)
=-\sum_{v\in V_\theta}p_\theta(v\mid c_i^{(k)})
\log_2 p_\theta(v\mid c_i^{(k)}).
\tag{5}
$$

Higher entropy means that the model spreads probability over more possible
next tokens. The accompanying top-one probability and its information are

$$
p_{\max}(c)=\max_{v\in V_\theta}p_\theta(v\mid c),
\qquad I_{\max}(c)=-\log_2 p_{\max}(c).
\tag{6}
$$

Next-token entropy is a property of the prompt state; it is not the surprisal
of the subsequently observed utterance and not the entropy of complete
possible responses.

## 4. Full-response entropy

Suppose $M_i$ valid responses are sampled for context $c_i$, normalized in
the same way, and collapse to $K_i$ distinct response types. If type $j$
appears $n_{ij}$ times, its empirical probability is

$$
\widehat p_{ij}=\frac{n_{ij}}{M_i},
\qquad \sum_{j=1}^{K_i}n_{ij}=M_i.
\tag{7}
$$

The plug-in response entropy is

$$
\widehat H_{\mathrm{resp}}(c_i)
=-\sum_{j=1}^{K_i}\widehat p_{ij}\log_2\widehat p_{ij}.
\tag{8}
$$

The primary response-space feature uses the Miller–Madow correction,

$$
\widehat H_{\mathrm{MM}}(c_i)
=\widehat H_{\mathrm{resp}}(c_i)
+\frac{K_i-1}{2M_i\ln 2}.
\tag{9}
$$

The correction reduces the leading small-sample downward bias of the plug-in
entropy. Invalid or empty generations are audited separately; the primary
quantity is calculated from valid normalized responses.

## 5. Bayes identity and corrected candidate-set score

Bayes' rule gives the exact identity

$$
p(u_i\mid c_i)=\frac{p(c_i\mid u_i)p(u_i)}{p(c_i)}.
\tag{10}
$$

Taking negative base-2 logarithms yields

$$
I_{\mathrm{Bayes}}(u_i\mid c_i)
=-\log_2p(u_i)-\log_2p(c_i\mid u_i)+\log_2p(c_i).
\tag{11}
$$

The archived first pilot estimated the prior and likelihood terms but not the
context-evidence term:

$$
\widetilde I_{\mathrm{Bayes}}(u_i,c_i)
=\underbrace{-\log_2\widehat p(u_i)}_{I_{\mathrm{prior}}(u_i)}
+\underbrace{-\log_2\widehat p(c_i\mid u_i)}_{I_{\mathrm{context}\mid\mathrm{utterance}}(c_i\mid u_i)}.
\tag{12}
$$

Therefore

$$
I_{\mathrm{Bayes}}(u_i\mid c_i)
=\widetilde I_{\mathrm{Bayes}}(u_i,c_i)+\log_2p(c_i).
\tag{13}
$$

The tilde is substantive: the legacy `bayes_bits_unnormalized` value is an
unnormalized decomposition, not an exact posterior surprisal. It also used
overlapping PBM training/evaluation rows and a reverse trigram whose utterance
conditioning was limited to the final utterance word and first context token.
It is retained only as an archived methods pilot.

### Corrected cross-fitted score

The corrected PBM estimator holds out the entire evaluated corpus and trains
additively by age. It estimates an utterance prior and a contrastive context
evidence term,

$$
\widehat E_i
\approx
\log_2\frac{p(c_i\mid u_i,a_i)}{p(c_i\mid a_i)}.
\tag{14a}
$$

The combined Bayes-derived score is

$$
S_i(u)=\log_2\widehat p(u\mid a_i)+\widehat E(c_i,u,a_i).
\tag{14b}
$$

For the available candidate set $A_i$—real, random, unigram, bigram, and
trigram—the score is normalized as

$$
q_{A_i}(u\mid c_i,a_i)
=\frac{2^{S_i(u)}}{\sum_{v\in A_i}2^{S_i(v)}},
\qquad
I_{A_i}(u\mid c_i,a_i)=-\log_2q_{A_i}(u\mid c_i,a_i).
\tag{14c}
$$

Thus `candidate_set_probability` is a genuine probability over the supplied
candidate set and `candidate_set_bayes_bits` is its surprisal. Neither is a
posterior probability over every possible utterance. The contrastive
$\widehat E$ uses hashed whole-utterance/whole-context features learned from
matched versus age- and corpus-matched shuffled pairs; it is not a literal
neural sequence estimate of $p(c\mid u,a)$.

The cross-fitted word prior uses add-$\alpha$ smoothing with an explicit
unknown-token state,

$$
\widehat p(w\mid h)
=\frac{N(h,w)+\alpha}{N(h)+\alpha|V|},
\qquad \alpha=0.1,
\tag{14d}
$$

where $h$ is the available word history, $N(h,w)$ and $N(h)$ are training
counts, and $|V|$ is vocabulary size. The order is $n=3$, with progressive
backoff to shorter histories and an end-of-sequence event. The candidate's age
bin uses only its own and preceding age bins from the non-held-out corpora.

## 6. Production effort and information density

For effort unit $q\in\{\text{word, morpheme, syllable, phoneme}\}$, let

$$
E_{iq}=\sum_{\ell=1}^{L_i}e_q(w_{i\ell}),
\tag{15}
$$

where $w_{i\ell}$ is an orthographic word and $e_q(w)$ is its contribution
in unit $q$. For words, $e_q(w)=1$. Morphemes are a surface-form heuristic
that counts a base plus recognized clitic and suffix contributions. Syllables
use dictionary pronunciations when available and a syllabification fallback
otherwise. Phonemes use dictionary pronunciations with a grapheme-to-phoneme
fallback. Punctuation-only material does not count as a word.

Information density in effort unit $q$ is

$$
D_{iq}^{(k)}=\frac{I_\theta^{(k)}(u_i)}{E_{iq}},
\qquad E_{iq}>0.
\tag{16}
$$

This ratio answers “bits per unit produced.” It is a descriptive normalization;
it is not the primary regression definition of communicative efficiency.

For generated responses $r_{im}$, expected effort and sample variation are

$$
\overline E_{iq}^{\mathrm{gen}}
=\frac{1}{M_i}\sum_{m=1}^{M_i}E_q(r_{im}),
\qquad
s_{E,iq}^{\mathrm{gen}}
=\sqrt{\frac{1}{M_i-1}\sum_{m=1}^{M_i}
\left(E_q(r_{im})-\overline E_{iq}^{\mathrm{gen}}\right)^2}.
\tag{17}
$$

A real utterance can then be located relative to the generated response
distribution with a residual $R_{iq}=E_{iq}-\overline E_{iq}^{\mathrm{gen}}$,
a standardized score $Z_{iq}=R_{iq}/s_{E,iq}^{\mathrm{gen}}$ when the standard
deviation is positive, or a midrank percentile

$$
P_{iq}=\frac{\#\{m:E_q(r_{im})<E_{iq}\}
+\tfrac12\#\{m:E_q(r_{im})=E_{iq}\}}{M_i}.
\tag{18}
$$

## 7. Developmentally constrained reference generators

For additive age bin $b$, training data contain the current bin and every
earlier bin. With vocabulary $V_b$, the reference distributions are

$$
q_{\mathrm{uniform},b}(w)=\frac{1}{|V_b|},\qquad
q_{\mathrm{uni},b}(w)=\frac{N_b(w)}{\sum_{v\in V_b}N_b(v)},
\tag{19}
$$

and, for word history $h$,

$$
q_{n,b}(w\mid h)=\frac{N_b(h,w)}{N_b(h)}.
\tag{20}
$$

Trigram generation backs off to bigram and then unigram probabilities when a
history is unavailable. The first generated word is conditioned on the tail of
the caretaker context. Matched-length random, unigram, bigram, trigram, and
same-length LSTM controls generate the same number of orthographic words as the
paired real utterance.

The LSTM reference model factorizes its generator probability as

$$
q_\phi(u_i\mid c_i)=\prod_{\ell=1}^{L_i}
q_\phi(w_{i\ell}\mid c_i,w_{i,<\ell}),
\qquad
\mathcal L(\phi)=-\sum_{i,\ell}\ln q_\phi(w_{i\ell}\mid c_i,w_{i,<\ell}).
\tag{21}
$$

This cross-entropy trains the generator. It is not the reported Mistral
information value: generated and real strings are subsequently evaluated by
the same scoring model $p_\theta$.

For a paired generated control $b_i$, define

$$
\Delta I_i=I_\theta(b_i\mid c_i)-I_\theta(u_i\mid c_i).
\tag{22}
$$

Positive $\Delta I_i$ means the generated control carries more surprisal
under the common scorer than the observed child utterance.

## 8. Regression estimands for communicative efficiency

Let $a_i$ be age in months, $E_i$ a selected effort measure, $P_i$
preceding caretaker effort, $H_i$ context-only next-token entropy, and
$j(i)$ the child. Continuous predictors are mean-centered:
$z_i^c=z_i-\overline z$.

The current supervisor sequence is

$$
\begin{aligned}
\text{M1:}\quad I_i
&=\beta_0+\beta_a a_i^c+\beta_EE_i^c+\varepsilon_i,\\
\text{M2:}\quad I_i
&=\beta_0+\beta_a a_i^c+\beta_EE_i^c+\gamma_{j(i)}+\varepsilon_i,\\
\text{M3:}\quad I_i
&=\beta_0+\beta_a a_i^c+\beta_EE_i^c
+\beta_{aE}a_i^cE_i^c+\gamma_{j(i)}+\varepsilon_i,\\
\text{M4:}\quad I_i
&=\beta_0+\beta_a a_i^c+\beta_EE_i^c
+\beta_{aE}a_i^cE_i^c+\beta_PP_i^c+\beta_HH_i^c
+\gamma_{j(i)}+\varepsilon_i.
\end{aligned}
\tag{23}
$$

$I_i$ is total target surprisal; $\gamma_{j(i)}$ is a child-specific fixed
intercept; and $\varepsilon_i$ is residual variation. These are ordinary
least-squares models with uncertainty clustered by child. The coefficients
$\beta_a$, $\beta_E$, and $\beta_{aE}$ describe, respectively, the age
slope at mean effort, the effort slope at mean age, and how either slope changes
with the other predictor. $\beta_P$ and $\beta_H$ adjust for preceding
caretaker amount and prompt-state uncertainty.

The paper-facing efficiency estimand is the predicted age trajectory at fixed
effort and fixed controls,

$$
m(a;e,p,h,j)=
\mathbb E[I_i\mid a_i=a,E_i=e,P_i=p,H_i=h,j(i)=j],
\qquad
\frac{\partial m}{\partial a}=\beta_a+\beta_{aE}E_i^c.
\tag{24}
$$

Thus the main question is whether expected information changes with age when
the amount of produced material is held constant. A negative age slope means
less surprisal is required for the same measured production effort; it is not,
by itself, a claim about communicative success or a universal scalar efficiency
score.

For response-space analyses, one implemented fixed-effect specification is

$$
Y_i=\beta_0+\beta_a a_i^c+\beta_RH_{\mathrm{MM},i}^c
+\beta_{aR}a_i^cH_{\mathrm{MM},i}^c
+\beta_G\overline E_{i,\mathrm{words}}^{\mathrm{gen},c}
+\beta_CC_i^c+\beta_NH_{\mathrm{next},i}^c
+\gamma_{j(i)}+\varepsilon_i,
\tag{25}
$$

where $Y_i$ is a real-versus-generated relative-effort outcome,
$\overline E_{i,\mathrm{words}}^{\mathrm{gen}}$ is expected generated response
word count, and
$C_i$ is context word count. $H_{\mathrm{next},i}$ adjusts for next-token
prompt-state uncertainty. Continuous outcomes use OLS; binary outcomes use a
binomial generalized linear model. These response-space models answer a
different question from target-surprisal models and should be reported
separately.

## 9. Secondary complexity summaries

For a collection of utterances containing $N$ word tokens and $V$ distinct
word types,

$$
\mathrm{TTR}=\frac{V}{N},
\qquad
\mathrm{MLU}_{\mathrm{words}}
=\frac{\text{total word tokens}}{\text{number of utterances}}.
\tag{26}
$$

Type-token ratio is sample-size sensitive and is therefore descriptive unless
the comparison controls the token budget. MLU describes average utterance
length; it is not itself an information measure.

## Interpretation boundary

| Quantity | Target observed? | Probability space | Primary interpretation |
|---|---:|---|---|
| $I_\theta(u\mid c)$ | Yes | Scorer tokenizer tokens | Information in the observed target |
| $H_{\mathrm{next}}(c)$ | No | Next tokenizer token | Prompt-state uncertainty |
| $H_{\mathrm{MM}}(c)$ | No | Sampled complete response types | Diversity of plausible responses |
| $\widetilde I_{\mathrm{Bayes}}(u,c)$ | Yes | Legacy word $n$-gram prior and likelihood | Archived unnormalized pilot |
| $I_A(u\mid c,a)$ | Yes | Cross-fitted five-candidate set | Bayes-derived candidate-set surprisal |
| $D_{iq}=I_i/E_{iq}$ | Yes | Information divided by effort | Descriptive information density |
| $m(a;e,\cdot)$ | Yes | Regression prediction | Development at fixed measured effort |

The quantities can support a common theory of communicative efficiency, but
they remain mathematically distinct and should retain separate names in the
paper.
