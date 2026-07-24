"""Paper-ready formal definitions for the July supervisor report.

The HTML is deliberately self-contained: it uses no remote fonts, JavaScript,
or math-rendering service, so the definitions remain readable when opened
offline or printed to PDF.  The companion Markdown keeps copyable LaTeX source
for later use in a manuscript.
"""

from __future__ import annotations

import html
from pathlib import Path


FORMAL_DEFINITIONS_MD_PATH = Path("docs/july_meeting_formal_mathematical_definitions.md")


FORMAL_DEFINITIONS_MARKDOWN = r"""# Formal Mathematical Definitions

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
"""


FORMAL_CSS = r"""
:root {
  --ink: #182326;
  --muted: #58666a;
  --teal: #1f6669;
  --teal-dark: #154d50;
  --teal-pale: #eaf3f2;
  --line: #d8e2e0;
  --paper: #fffefd;
  --canvas: #e8efed;
  --warm: #f8f5ef;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--canvas);
  color: var(--ink);
  font: 17px/1.64 Georgia, "Times New Roman", serif;
  text-rendering: optimizeLegibility;
}
main {
  max-width: 1080px;
  margin: 36px auto 72px;
  padding: 0 76px 76px;
  background: var(--paper);
  box-shadow: 0 22px 70px rgba(24, 44, 46, .14);
}
.hero {
  margin: 0 -76px 42px;
  padding: 54px 76px 48px;
  color: white;
  background: linear-gradient(135deg, #153f43 0%, #226b6e 72%, #327d78 100%);
}
.eyebrow, .section-kicker {
  margin: 0 0 12px;
  font: 700 .76rem/1.3 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: .14em;
  text-transform: uppercase;
}
.eyebrow { color: #cfe7e4; }
h1, h2, h3, .sans {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
h1 {
  max-width: 820px;
  margin: 0;
  font-size: clamp(2.35rem, 5vw, 4rem);
  line-height: 1.03;
  letter-spacing: -.045em;
}
.hero .dek {
  max-width: 800px;
  margin: 22px 0 0;
  color: #edf8f6;
  font-size: 1.13rem;
  line-height: 1.55;
}
.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 22px;
  margin-top: 24px;
  color: #cfe7e4;
  font: 600 .84rem/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.top-links { display: flex; gap: 16px; margin-bottom: 22px; }
.top-links a {
  color: #dff1ef;
  font: 650 .84rem/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  text-decoration: none;
  border-bottom: 1px solid rgba(255,255,255,.5);
}
.abstract {
  margin: 0 0 38px;
  padding: 23px 26px;
  border-left: 4px solid var(--teal);
  background: var(--teal-pale);
}
.abstract strong {
  display: block;
  margin-bottom: 6px;
  color: var(--teal-dark);
  font: 750 .78rem/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: .11em;
  text-transform: uppercase;
}
.abstract p { margin: 0; }
.contents {
  margin: 0 0 50px;
  padding: 24px 26px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: #fbfcfb;
}
.contents h2 { margin: 0 0 14px; border: 0; font-size: 1rem; }
.contents ol {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px 28px;
  margin: 0;
  padding-left: 1.35rem;
}
.contents a { color: var(--teal-dark); text-decoration: none; }
section { scroll-margin-top: 24px; margin-top: 58px; }
h2 {
  margin: 0 0 22px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--teal);
  color: var(--teal-dark);
  font-size: 1.65rem;
  line-height: 1.2;
  letter-spacing: -.018em;
}
h3 {
  margin: 34px 0 10px;
  color: #263b3d;
  font-size: 1.08rem;
  line-height: 1.3;
}
p { margin: 10px 0 16px; }
.notation-grid, .distinction-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.term {
  padding: 15px 17px;
  border: 1px solid var(--line);
  background: #fcfdfc;
}
.term b {
  display: block;
  margin-bottom: 4px;
  color: var(--teal-dark);
  font-family: "Latin Modern Math", "Cambria Math", Georgia, serif;
  font-size: 1.04rem;
}
.term span { color: var(--muted); font-size: .93rem; }
.equation-card {
  position: relative;
  margin: 19px 0 20px;
  padding: 20px 58px 20px 24px;
  border: 1px solid #cadad7;
  border-left: 4px solid var(--teal);
  background: #fbfdfc;
  break-inside: avoid;
}
.eq {
  overflow-x: auto;
  color: #10191b;
  font-family: "Latin Modern Math", "STIX Two Math", "Cambria Math", Georgia, serif;
  font-size: 1.16rem;
  line-height: 1.85;
  text-align: center;
  white-space: nowrap;
}
.eq.multiline { white-space: normal; text-align: left; padding-left: 4%; }
.eqno {
  position: absolute;
  top: 50%;
  right: 17px;
  transform: translateY(-50%);
  color: var(--muted);
  font: 500 .88rem/1.2 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.where {
  margin: -5px 0 26px;
  color: var(--muted);
  font-size: .95rem;
}
.where b { color: var(--ink); }
.callout {
  margin: 22px 0;
  padding: 17px 20px;
  border: 1px solid #e2ddd0;
  background: var(--warm);
}
.callout strong {
  color: #624e26;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
code {
  padding: .08em .3em;
  border-radius: 3px;
  color: #244f52;
  background: #edf3f2;
  font: .88em/1.4 ui-monospace, SFMono-Regular, Consolas, monospace;
}
table {
  width: 100%;
  margin: 22px 0;
  border-collapse: collapse;
  font-size: .9rem;
  line-height: 1.45;
}
th {
  padding: 10px 11px;
  color: white;
  background: var(--teal-dark);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  text-align: left;
}
td { padding: 10px 11px; border-bottom: 1px solid var(--line); vertical-align: top; }
tr:nth-child(even) td { background: #f7faf9; }
.model-table td:first-child { width: 7%; font-weight: 700; color: var(--teal-dark); }
.model-table td:nth-child(2) { width: 54%; font-family: "Latin Modern Math", "Cambria Math", Georgia, serif; }
.small { color: var(--muted); font-size: .89rem; }
.boundary {
  margin-top: 60px;
  padding: 25px 27px;
  color: #f4fbfa;
  background: #173f42;
  break-inside: avoid;
}
.boundary h2 { margin-top: 0; color: white; border-color: #72aaa7; }
.boundary p:last-child { margin-bottom: 0; }
.footer {
  margin-top: 44px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font: .8rem/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
sub, sup { line-height: 0; }
@media (max-width: 760px) {
  main { margin: 0; padding: 0 22px 46px; }
  .hero { margin: 0 -22px 32px; padding: 34px 22px; }
  .contents ol, .notation-grid, .distinction-grid { grid-template-columns: 1fr; }
  .equation-card { padding-left: 14px; padding-right: 42px; }
  .eq { text-align: left; font-size: 1rem; }
}
@media print {
  @page { size: A4; margin: 16mm 15mm 18mm; }
  body { background: white; font-size: 10.6pt; }
  main { max-width: none; margin: 0; padding: 0; box-shadow: none; }
  .hero { margin: 0 0 12mm; padding: 13mm 14mm 12mm; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .top-links, .contents { display: none; }
  section { margin-top: 10mm; }
  h2 { font-size: 15pt; }
  h2, h3 { break-after: avoid; }
  .equation-card, .callout, table, .term { break-inside: avoid; }
  .boundary { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
}
"""


def _equation(number: int | str, formula: str, *, multiline: bool = False) -> str:
    """Return a numbered, accessible display-equation block."""

    class_name = "eq multiline" if multiline else "eq"
    return (
        '<div class="equation-card" role="math">'
        f'<div class="{class_name}">{formula}</div>'
        f'<span class="eqno">({html.escape(str(number))})</span>'
        "</div>"
    )


def _where(items: str) -> str:
    return f'<p class="where"><b>Terms.</b> {items}</p>'


def formal_definitions_body() -> str:
    """Return the formal-definitions report body."""

    eq = _equation
    return f"""
<header class="hero">
  <nav class="top-links" aria-label="Report navigation">
    <a href="july_meeting_index.html">&#8592; July report</a>
    <a href="july_meeting_formal_mathematical_definitions.md">Markdown / LaTeX source</a>
  </nav>
  <p class="eyebrow">July report &middot; methods reference</p>
  <h1>Formal Mathematical Definitions</h1>
  <p class="dek">A unified notation for utterance information, contextual uncertainty,
  Bayes information, production effort, reference generators, and the statistical
  estimands used to study communicative efficiency.</p>
  <div class="hero-meta"><span>Current implemented definitions</span><span>Logarithms base 2</span><span>Information in bits</span></div>
</header>

<aside class="abstract">
  <strong>Scope</strong>
  <p>This page distinguishes four quantities that are conceptually related but
  mathematically different: target-utterance information, context-only
  uncertainty, sampled response-space uncertainty, and the legacy and corrected
  Bayes-derived scores. The notation below follows the computations used in the
  present analysis pipeline.</p>
</aside>

<nav class="contents" aria-label="Contents">
  <h2>Contents</h2>
  <ol>
    <li><a href="#notation">Units and notation</a></li>
    <li><a href="#surprisal">Target surprisal</a></li>
    <li><a href="#context-entropy">Context-only uncertainty</a></li>
    <li><a href="#response-entropy">Full-response entropy</a></li>
    <li><a href="#bayes">Bayes information</a></li>
    <li><a href="#effort">Production effort</a></li>
    <li><a href="#generators">Reference generators</a></li>
    <li><a href="#models">Efficiency estimands</a></li>
    <li><a href="#secondary">Secondary complexity</a></li>
    <li><a href="#boundary">Interpretation boundary</a></li>
  </ol>
</nav>

<section id="notation">
  <p class="section-kicker">01 &middot; Observation level</p>
  <h2>Units and notation</h2>
  <p>For child-utterance observation <i>i</i>, let
  <i>c</i><sub>i</sub><sup>(k)</sup> denote the preceding caretaker context at
  window <i>k</i>, and let
  <i>u</i><sub>i</sub>=(<i>x</i><sub>i1</sub>,&hellip;,<i>x</i><sub>iT<sub>i</sub></sub>)
  denote the target child utterance represented as scoring-model tokens.</p>
  <div class="notation-grid">
    <div class="term"><b>i</b><span>One target-utterance observation.</span></div>
    <div class="term"><b>k &isin; {{0,1,2,3}}</b><span>Context window: none, or the most recent one, two, or three caretaker utterances.</span></div>
    <div class="term"><b>x<sub>it</sub></b><span>The <i>t</i>th tokenizer token of the target utterance.</span></div>
    <div class="term"><b>T<sub>i</sub></b><span>Number of evaluated target tokenizer tokens; not an orthographic word count.</span></div>
    <div class="term"><b>p<sub>&theta;</sub></b><span>The common causal language model used to score observed and generated strings.</span></div>
    <div class="term"><b>E<sub>iq</sub></b><span>Production effort for unit <i>q</i>: words, morphemes, syllables, or phonemes.</span></div>
  </div>
  <div class="callout"><strong>Units.</strong> All logarithms on this page are base 2 unless
  explicitly marked <i>ln</i>. Surprisal and entropy are therefore measured in bits.</div>
</section>

<section id="surprisal">
  <p class="section-kicker">02 &middot; Observed target</p>
  <h2>Target surprisal and utterance information</h2>
  <h3>Token surprisal</h3>
  {eq(1, '<i>s</i><sub>it</sub><sup>(k)</sup> = &minus;log<sub>2</sub> <i>p</i><sub>&theta;</sub>(<i>x</i><sub>it</sub> &mid; <i>c</i><sub>i</sub><sup>(k)</sup>, <i>x</i><sub>i,&lt;t</sub>)')}
  {_where('<i>p</i><sub>&theta;</sub> is the scorer probability; <i>x</i><sub>i,&lt;t</sub> is the already observed target prefix. Higher surprisal means that the observed token was less predictable. Log-softmax outputs in natural units are divided by ln 2.')}

  <h3>Total utterance information</h3>
  {eq(2, '<i>I</i><sub>&theta;</sub><sup>(k)</sup>(<i>u</i><sub>i</sub>) = &sum;<sub>t=1</sub><sup>T<sub>i</sub></sup> <i>s</i><sub>it</sub><sup>(k)</sup> = &minus;log<sub>2</sub> &prod;<sub>t=1</sub><sup>T<sub>i</sub></sup> <i>p</i><sub>&theta;</sub>(<i>x</i><sub>it</sub> &mid; <i>c</i><sub>i</sub><sup>(k)</sup>, <i>x</i><sub>i,&lt;t</sub>)')}
  {_where('This is <code>sum_bits</code>. The product is the causal probability of the target sequence under the scorer.')}
  <div class="callout"><strong>Target-only accounting.</strong> Context tokens condition
  the predictions but never enter the target sum. Only tokenizer tokens whose
  character offsets overlap the target span are evaluated.</div>

  <h3>Mean information per evaluated token</h3>
  {eq(3, '<span style="text-decoration:overline"><i>I</i></span><sub>i,tok</sub><sup>(k)</sup> = <i>I</i><sub>&theta;</sub><sup>(k)</sup>(<i>u</i><sub>i</sub>) / <i>T</i><sub>i</sub>, &nbsp; <i>T</i><sub>i</sub> &gt; 0')}
  {_where('This is <code>mean_bits_per_token</code>. It is descriptive; the primary fixed-effort models retain total information as the outcome.')}

  <h3>Information gained from context</h3>
  {eq(4, '<i>G</i><sub>i</sub><sup>(k)</sup> = <i>I</i><sub>&theta;</sub><sup>(0)</sup>(<i>u</i><sub>i</sub>) &minus; <i>I</i><sub>&theta;</sub><sup>(k)</sup>(<i>u</i><sub>i</sub>)')}
  {_where('Positive <i>G</i><sub>i</sub><sup>(k)</sup> means the specified caretaker context made the observed utterance more predictable than the no-context score; a negative value means it increased surprisal.')}
</section>

<section id="context-entropy">
  <p class="section-kicker">03 &middot; Prompt state</p>
  <h2>Context-only next-token uncertainty</h2>
  <p>Let <i>V</i><sub>&theta;</sub> be the scorer tokenizer vocabulary. The target
  utterance is not shown when this feature is computed.</p>
  {eq(5, '<i>H</i><sub>next</sub>(<i>c</i><sub>i</sub><sup>(k)</sup>) = &minus;&sum;<sub>v&isin;V<sub>&theta;</sub></sub> <i>p</i><sub>&theta;</sub>(<i>v</i>&mid;<i>c</i><sub>i</sub><sup>(k)</sup>) log<sub>2</sub> <i>p</i><sub>&theta;</sub>(<i>v</i>&mid;<i>c</i><sub>i</sub><sup>(k)</sup>)')}
  {_where('<i>v</i> ranges over every possible next tokenizer token. Higher entropy means the model distributes probability over more alternatives.')}
  {eq(6, '<i>p</i><sub>max</sub>(<i>c</i>) = max<sub>v&isin;V<sub>&theta;</sub></sub> <i>p</i><sub>&theta;</sub>(<i>v</i>&mid;<i>c</i>), &nbsp;&nbsp; <i>I</i><sub>max</sub>(<i>c</i>) = &minus;log<sub>2</sub> <i>p</i><sub>max</sub>(<i>c</i>)')}
  <div class="callout"><strong>Interpretive boundary.</strong> This is the
  uncertainty of one next token after the context. It is neither the surprisal
  of the observed child response nor the entropy of complete possible responses.</div>
</section>

<section id="response-entropy">
  <p class="section-kicker">04 &middot; Sampled response space</p>
  <h2>Full-response entropy</h2>
  <p>For context <i>c</i><sub>i</sub>, suppose <i>M</i><sub>i</sub> valid sampled
  responses collapse to <i>K</i><sub>i</sub> distinct normalized response types.
  If type <i>j</i> appears <i>n</i><sub>ij</sub> times,</p>
  {eq(7, '<i>p&#770;</i><sub>ij</sub> = <i>n</i><sub>ij</sub> / <i>M</i><sub>i</sub>, &nbsp;&nbsp; &sum;<sub>j=1</sub><sup>K<sub>i</sub></sup> <i>n</i><sub>ij</sub> = <i>M</i><sub>i</sub>')}
  {eq(8, '<i>H&#770;</i><sub>resp</sub>(<i>c</i><sub>i</sub>) = &minus;&sum;<sub>j=1</sub><sup>K<sub>i</sub></sup> <i>p&#770;</i><sub>ij</sub> log<sub>2</sub> <i>p&#770;</i><sub>ij</sub>')}
  {_where('This plug-in estimator is the Shannon entropy of the empirical distribution over complete normalized response strings.')}
  {eq(9, '<i>H&#770;</i><sub>MM</sub>(<i>c</i><sub>i</sub>) = <i>H&#770;</i><sub>resp</sub>(<i>c</i><sub>i</sub>) + (<i>K</i><sub>i</sub>&minus;1) / (2<i>M</i><sub>i</sub> ln 2)')}
  {_where('The Miller&ndash;Madow term reduces the leading small-sample downward bias. The primary feature uses valid normalized responses; invalid or empty generations are audited separately.')}
</section>

<section id="bayes">
  <p class="section-kicker">05 &middot; Prior and context evidence</p>
  <h2>Bayes identity and corrected candidate-set score</h2>
  {eq(10, '<i>p</i>(<i>u</i><sub>i</sub>&mid;<i>c</i><sub>i</sub>) = <i>p</i>(<i>c</i><sub>i</sub>&mid;<i>u</i><sub>i</sub>) <i>p</i>(<i>u</i><sub>i</sub>) / <i>p</i>(<i>c</i><sub>i</sub>)')}
  <p>Taking negative base-2 logarithms converts Bayes' rule into an additive
  information decomposition:</p>
  {eq(11, '<i>I</i><sub>Bayes</sub>(<i>u</i><sub>i</sub>&mid;<i>c</i><sub>i</sub>) = &minus;log<sub>2</sub><i>p</i>(<i>u</i><sub>i</sub>) &minus; log<sub>2</sub><i>p</i>(<i>c</i><sub>i</sub>&mid;<i>u</i><sub>i</sub>) + log<sub>2</sub><i>p</i>(<i>c</i><sub>i</sub>)')}
  {_where('The three terms are utterance prior information, context-given-utterance information, and the context-evidence normalizer.')}
  <p>The archived first pilot estimated the first two terms:</p>
  {eq(12, '<span style="font-size:1.14em">Ĩ</span><sub>Bayes</sub>(<i>u</i><sub>i</sub>,<i>c</i><sub>i</sub>) = <i>I</i><sub>prior</sub>(<i>u</i><sub>i</sub>) + <i>I</i><sub>context&mid;utterance</sub>(<i>c</i><sub>i</sub>&mid;<i>u</i><sub>i</sub>)')}
  {_where('<i>I</i><sub>prior</sub>(<i>u</i>)=&minus;log<sub>2</sub><i>p&#770;</i>(<i>u</i>) and <i>I</i><sub>context&mid;utterance</sub>(<i>c</i>&mid;<i>u</i>)=&minus;log<sub>2</sub><i>p&#770;</i>(<i>c</i>&mid;<i>u</i>).')}
  {eq(13, '<i>I</i><sub>Bayes</sub>(<i>u</i><sub>i</sub>&mid;<i>c</i><sub>i</sub>) = <span style="font-size:1.14em">Ĩ</span><sub>Bayes</sub>(<i>u</i><sub>i</sub>,<i>c</i><sub>i</sub>) + log<sub>2</sub><i>p</i>(<i>c</i><sub>i</sub>)')}
  <div class="callout"><strong>Normalization caveat &mdash; archived pilot only.</strong> The legacy
  <code>bayes_bits_unnormalized</code> value omits log<sub>2</sub><i>p</i>(<i>c</i>),
  was trained on overlapping PBM rows, and used a reverse trigram whose candidate
  conditioning reached only the first context token. It is not exact posterior surprisal
  and should not support substantive claims.</div>

  <h3>Corrected cross-fitted score</h3>
  <p>The corrected PBM estimator holds out the entire evaluated corpus and
  trains additively by age. Its whole-utterance/whole-context contrastive term
  estimates a context likelihood ratio:</p>
  {eq('14a', '<i>E&#770;</i><sub>i</sub> &asymp; log<sub>2</sub>[ <i>p</i>(<i>c</i><sub>i</sub>&mid;<i>u</i><sub>i</sub>,<i>a</i><sub>i</sub>) / <i>p</i>(<i>c</i><sub>i</sub>&mid;<i>a</i><sub>i</sub>) ]')}
  {eq('14b', '<i>S</i><sub>i</sub>(<i>u</i>) = log<sub>2</sub><i>p&#770;</i>(<i>u</i>&mid;<i>a</i><sub>i</sub>) + <i>E&#770;</i>(<i>c</i><sub>i</sub>,<i>u</i>,<i>a</i><sub>i</sub>)')}
  <p>For the available real/random/unigram/bigram/trigram set
  <i>A</i><sub>i</sub>,</p>
  {eq('14c', '<i>q</i><sub>A<sub>i</sub></sub>(<i>u</i>&mid;<i>c</i><sub>i</sub>,<i>a</i><sub>i</sub>) = 2<sup><i>S</i><sub>i</sub>(<i>u</i>)</sup> / &sum;<sub><i>v</i>&isin;<i>A</i><sub>i</sub></sub>2<sup><i>S</i><sub>i</sub>(<i>v</i>)</sup>, &nbsp; <i>I</i><sub>A<sub>i</sub></sub>=&minus;log<sub>2</sub><i>q</i><sub>A<sub>i</sub></sub>')}
  {_where('<code>candidate_set_probability</code> is normalized only over the supplied candidate set. <code>candidate_set_bayes_bits</code> is its surprisal. Neither is a posterior over every possible utterance. The contrastive <i>E&#770;</i> is learned from matched versus shuffled pairs and is not a literal neural sequence likelihood.')}

  <h3>Cross-fitted word prior</h3>
  {eq('14d', '<span style="text-decoration:overline"><i>p</i></span>(<i>w</i>&mid;<i>h</i>) = [<i>N</i>(<i>h</i>,<i>w</i>)+&alpha;] / [<i>N</i>(<i>h</i>)+&alpha;|<i>V</i>|], &nbsp;&nbsp; &alpha;=0.1')}
  {_where('<i>h</i> is word history, <i>N</i> denotes non-held-out training counts, and |<i>V</i>| includes an explicit unknown-token state. The order is three with progressive backoff and end-of-sequence. A target age bin uses only its own and preceding bins.')}
  <p><a href="corrected_pbm_bayes_report.html">Open the corrected PBM results and validation report.</a></p>
</section>

<section id="effort">
  <p class="section-kicker">06 &middot; Production cost</p>
  <h2>Production effort and information density</h2>
  {eq(15, '<i>E</i><sub>iq</sub> = &sum;<sub>&ell;=1</sub><sup>L<sub>i</sub></sup> <i>e</i><sub>q</sub>(<i>w</i><sub>i&ell;</sub>), &nbsp;&nbsp; <i>q</i> &isin; {{word, morpheme, syllable, phoneme}}')}
  <table>
    <thead><tr><th>Effort unit</th><th>Implemented contribution <i>e</i><sub>q</sub>(<i>w</i>)</th></tr></thead>
    <tbody>
      <tr><td>Words</td><td>One per orthographic word token; punctuation-only material is excluded.</td></tr>
      <tr><td>Morphemes</td><td>A surface-form base count plus recognized clitic and suffix contributions.</td></tr>
      <tr><td>Syllables</td><td>Dictionary pronunciation count when available, with a syllabification fallback.</td></tr>
      <tr><td>Phonemes</td><td>Dictionary pronunciation count when available, with a grapheme-to-phoneme fallback.</td></tr>
    </tbody>
  </table>
  {eq(16, '<i>D</i><sub>iq</sub><sup>(k)</sup> = <i>I</i><sub>&theta;</sub><sup>(k)</sup>(<i>u</i><sub>i</sub>) / <i>E</i><sub>iq</sub>, &nbsp;&nbsp; <i>E</i><sub>iq</sub> &gt; 0')}
  {_where('Information density is bits per measured effort unit. It is a descriptive normalization, not the primary regression definition of efficiency.')}

  <h3>Expected effort in a sampled response distribution</h3>
  {eq(17, '<div><span style="text-decoration:overline"><i>E</i></span><sub>iq</sub><sup>gen</sup> = (1/<i>M</i><sub>i</sub>) &sum;<sub>m=1</sub><sup>M<sub>i</sub></sup> <i>E</i><sub>q</sub>(<i>r</i><sub>im</sub>)</div><div><i>s</i><sub>E,iq</sub><sup>gen</sup> = &radic;[ &sum;<sub>m=1</sub><sup>M<sub>i</sub></sup>(<i>E</i><sub>q</sub>(<i>r</i><sub>im</sub>)&minus;<span style="text-decoration:overline"><i>E</i></span><sub>iq</sub><sup>gen</sup>)<sup>2</sup> / (<i>M</i><sub>i</sub>&minus;1) ]</div>', multiline=True)}
  {_where('<i>r</i><sub>im</sub> is sampled response <i>m</i>. The standard deviation uses the sample denominator <i>M</i><sub>i</sub>&minus;1.')}
  {eq(18, '<i>R</i><sub>iq</sub>=<i>E</i><sub>iq</sub>&minus;<span style="text-decoration:overline"><i>E</i></span><sub>iq</sub><sup>gen</sup>, &nbsp; <i>Z</i><sub>iq</sub>=<i>R</i><sub>iq</sub>/<i>s</i><sub>E,iq</sub><sup>gen</sup>, &nbsp; <i>P</i><sub>iq</sub>=[#(<i>E</i><sup>gen</sup>&lt;<i>E</i><sub>iq</sub>)+&frac12;#(<i>E</i><sup>gen</sup>=<i>E</i><sub>iq</sub>)]/<i>M</i><sub>i</sub>')}
  {_where('<i>R</i> is the real-minus-expected residual, <i>Z</i> is defined when generated standard deviation is positive, and <i>P</i> is the tie-aware midrank percentile.')}
</section>

<section id="generators">
  <p class="section-kicker">07 &middot; Counterfactual controls</p>
  <h2>Developmentally constrained reference generators</h2>
  <p>For additive age bin <i>b</i>, the training sample contains the current bin
  and every earlier bin. Let <i>V</i><sub>b</sub> be its word vocabulary.</p>
  {eq(19, '<i>q</i><sub>uniform,b</sub>(<i>w</i>)=1/|<i>V</i><sub>b</sub>|, &nbsp;&nbsp; <i>q</i><sub>uni,b</sub>(<i>w</i>)=<i>N</i><sub>b</sub>(<i>w</i>)/&sum;<sub>v&isin;V<sub>b</sub></sub><i>N</i><sub>b</sub>(<i>v</i>)')}
  {eq(20, '<i>q</i><sub>n,b</sub>(<i>w</i>&mid;<i>h</i>)=<i>N</i><sub>b</sub>(<i>h</i>,<i>w</i>)/<i>N</i><sub>b</sub>(<i>h</i>)')}
  {_where('Trigrams back off to bigrams and then unigrams when a history is unavailable. The initial generated word is conditioned on the tail of the caretaker context.')}
  {eq(21, '<i>q</i><sub>&phi;</sub>(<i>u</i><sub>i</sub>&mid;<i>c</i><sub>i</sub>)=&prod;<sub>&ell;=1</sub><sup>L<sub>i</sub></sup><i>q</i><sub>&phi;</sub>(<i>w</i><sub>i&ell;</sub>&mid;<i>c</i><sub>i</sub>,<i>w</i><sub>i,&lt;&ell;</sub>), &nbsp;&nbsp; &#8466;(&phi;)=&minus;&sum;<sub>i,&ell;</sub>ln <i>q</i><sub>&phi;</sub>(<i>w</i><sub>i&ell;</sub>&mid;<i>c</i><sub>i</sub>,<i>w</i><sub>i,&lt;&ell;</sub>)')}
  {_where('This is the LSTM generator factorization and training cross-entropy. Generator probabilities are not reported as Mistral information: all generated and observed strings are subsequently scored with the common <i>p</i><sub>&theta;</sub>.')}
  <div class="callout"><strong>Matched developmental information.</strong>
  Random, unigram, bigram, trigram, and additive LSTM controls learn only from
  the current age bin and earlier bins. Matched-length variants generate the
  same orthographic word count as the paired real utterance.</div>
  {eq(22, '&Delta;<i>I</i><sub>i</sub> = <i>I</i><sub>&theta;</sub>(<i>b</i><sub>i</sub>&mid;<i>c</i><sub>i</sub>) &minus; <i>I</i><sub>&theta;</sub>(<i>u</i><sub>i</sub>&mid;<i>c</i><sub>i</sub>)')}
  {_where('<i>b</i><sub>i</sub> is a paired generated control. Positive &Delta;<i>I</i><sub>i</sub> means the control is more surprising than the observed child utterance under the same scorer.')}
</section>

<section id="models">
  <p class="section-kicker">08 &middot; Inferential target</p>
  <h2>Regression estimands for communicative efficiency</h2>
  <p>Let <i>a</i><sub>i</sub> be age in months, <i>E</i><sub>i</sub> selected
  target effort, <i>P</i><sub>i</sub> preceding caretaker effort,
  <i>H</i><sub>i</sub> context-only next-token entropy, and <i>j</i>(<i>i</i>)
  child identity. Continuous predictors are mean-centered:
  <i>z</i><sub>i</sub><sup>c</sup>=<i>z</i><sub>i</sub>&minus;<span style="text-decoration:overline"><i>z</i></span>.</p>
  <table class="model-table">
    <caption class="small" style="text-align:left;margin-bottom:8px">Current supervisor model family (23)</caption>
    <thead><tr><th>Model</th><th>Implemented linear predictor</th><th>Scientific role</th></tr></thead>
    <tbody>
      <tr><td>M1</td><td><i>I</i><sub>i</sub>=&beta;<sub>0</sub>+&beta;<sub>a</sub><i>a</i><sub>i</sub><sup>c</sup>+&beta;<sub>E</sub><i>E</i><sub>i</sub><sup>c</sup>+&epsilon;<sub>i</sub></td><td>Age and target effort, pooling children.</td></tr>
      <tr><td>M2</td><td>M1 + &gamma;<sub>j(i)</sub></td><td>Adds a fixed intercept for each child.</td></tr>
      <tr><td>M3</td><td>M2 + &beta;<sub>aE</sub><i>a</i><sub>i</sub><sup>c</sup><i>E</i><sub>i</sub><sup>c</sup></td><td>Allows the age slope to vary with effort.</td></tr>
      <tr><td>M4</td><td>M3 + &beta;<sub>P</sub><i>P</i><sub>i</sub><sup>c</sup>+&beta;<sub>H</sub><i>H</i><sub>i</sub><sup>c</sup></td><td>Adds both current context controls.</td></tr>
    </tbody>
  </table>
  <p class="small"><i>I</i><sub>i</sub> is total target surprisal;
  &gamma;<sub>j(i)</sub> is the child fixed intercept; &epsilon;<sub>i</sub> is
  residual variation. Models use ordinary least squares with uncertainty
  clustered by child.</p>

  <h3>Coefficient meanings</h3>
  <div class="notation-grid">
    <div class="term"><b>&beta;<sub>a</sub></b><span>Age slope at mean effort (bits per month), conditional on included controls.</span></div>
    <div class="term"><b>&beta;<sub>E</sub></b><span>Effort slope at mean age (bits per additional effort unit).</span></div>
    <div class="term"><b>&beta;<sub>aE</sub></b><span>Change in the age slope per additional effort unit, equivalently change in the effort slope per month.</span></div>
    <div class="term"><b>&beta;<sub>P</sub>, &beta;<sub>H</sub></b><span>Adjusted associations of caretaker amount and prompt-state uncertainty with target information.</span></div>
  </div>
  <h3>Fixed-effort developmental estimand</h3>
  {eq('24a', '<i>m</i>(<i>a</i>;<i>e</i>,<i>p</i>,<i>h</i>,<i>j</i>) = E[<i>I</i><sub>i</sub> &mid; <i>a</i><sub>i</sub>=<i>a</i>, <i>E</i><sub>i</sub>=<i>e</i>, <i>P</i><sub>i</sub>=<i>p</i>, <i>H</i><sub>i</sub>=<i>h</i>, <i>j</i>(<i>i</i>)=<i>j</i>]')}
  {eq('24b', '&part;<i>m</i>/&part;<i>a</i> = &beta;<sub>a</sub> + &beta;<sub>aE</sub><i>E</i><sub>i</sub><sup>c</sup>')}
  {_where('The headline question is whether expected target information changes with age while measured production effort and contextual controls are held fixed. A negative slope means less surprisal at the same measured effort; it is not by itself a claim about communicative success or a universal scalar efficiency score.')}

  <h3>Response-space model</h3>
  {eq(25, '<i>Y</i><sub>i</sub>=&beta;<sub>0</sub>+&beta;<sub>a</sub><i>a</i><sub>i</sub><sup>c</sup>+&beta;<sub>R</sub><i>H</i><sub>MM,i</sub><sup>c</sup>+&beta;<sub>aR</sub><i>a</i><sub>i</sub><sup>c</sup><i>H</i><sub>MM,i</sub><sup>c</sup>+&beta;<sub>G</sub><span style="text-decoration:overline"><i>E</i></span><sub>i,words</sub><sup>gen,c</sup>+&beta;<sub>C</sub><i>C</i><sub>i</sub><sup>c</sup>+&beta;<sub>N</sub><i>H</i><sub>next,i</sub><sup>c</sup>+&gamma;<sub>j(i)</sub>+&epsilon;<sub>i</sub>')}
  {_where('<i>Y</i><sub>i</sub> is a real-versus-generated relative-effort outcome, <span style="text-decoration:overline"><i>E</i></span><sub>i,words</sub><sup>gen</sup> is expected generated response word count, <i>C</i><sub>i</sub> is context word count, and <i>H</i><sub>next,i</sub> adjusts for prompt-state uncertainty. Continuous outcomes use OLS; binary outcomes use a binomial generalized linear model. This is a separate estimand from target surprisal.')}
</section>

<section id="secondary">
  <p class="section-kicker">09 &middot; Descriptive complexity</p>
  <h2>Secondary complexity summaries</h2>
  {eq(26, 'TTR = <i>V</i>/<i>N</i>, &nbsp;&nbsp; MLU<sub>words</sub> = (total word tokens)/(number of utterances)')}
  {_where('<i>N</i> is the word-token count and <i>V</i> the distinct word-type count. TTR is sample-size sensitive and remains descriptive unless token budgets are controlled. MLU is average utterance length, not an information measure.')}
</section>

<section id="boundary" class="boundary">
  <p class="section-kicker">10 &middot; Reporting rule</p>
  <h2>Interpretation boundary</h2>
  <p><b>Observed target information</b> asks how surprising the produced
  utterance was. <b>Next-token context entropy</b> asks how uncertain the model
  was before seeing a response. <b>Full-response entropy</b> asks how diverse a
  sampled set of complete possible responses was. <b>Corrected candidate-set
  Bayes surprisal</b> combines an out-of-corpus age-conditioned prior with
  contrastive context evidence and normalizes only over the supplied five-way
  candidate set. <b>Information density</b>
  divides information by measured effort, whereas the main developmental
  estimand compares predicted information at fixed effort.</p>
  <p>These quantities can support a common theory of communicative efficiency,
  but they remain mathematically distinct and should retain separate names in
  the paper.</p>
</section>

<footer class="footer">Formal definitions for the July supervisor report. The
companion Markdown file contains copyable LaTeX versions of the equations.</footer>
"""


def formal_definitions_html() -> str:
    """Return the complete standalone formal-definitions HTML document."""

    title = "Formal Mathematical Definitions | July Report"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Formal definitions for communicative-efficiency analyses.">
<title>{html.escape(title)}</title>
<style>{FORMAL_CSS}</style>
</head>
<body>
<main>
{formal_definitions_body()}
</main>
</body>
</html>
"""
