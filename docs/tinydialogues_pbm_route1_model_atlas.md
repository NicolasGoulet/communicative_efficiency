# TinyDialogues PBM Expanded Model Atlas

This is an internal modeling report, not the supervisor-facing document. Its job
is to make the central communicative-efficiency comparisons explicit before we
decide which results deserve promotion.

Direct target scores in this run come from **TinyDialogues**. Any missing
scorer-specific predictor family is recorded as unavailable rather than being
silently borrowed from another scorer.

## Workflow Separation

The analysis and report generation are deliberately decoupled.

| stage | what it does | rerun when |
| --- | --- | --- |
| extract | Reads the large long table once and writes bounded samples plus full aggregate summaries. | The scored utterance table, row filters, or sampling logic changes. |
| model | Fits zoo models and regenerates plots from saved bounded samples. | A formula, model family, plot, or comparison specification changes. |
| report | Builds Markdown/HTML from existing CSV and figure outputs only. | Only wording, section order, or display formatting changes. |

Current commands:

- Re-extract samples and refit everything: `uv run python src/build_route1_model_report_suite.py --stage analysis`
- Refit models and plots from saved samples only: `uv run python src/build_route1_model_report_suite.py --stage model`
- Rebuild Markdown/HTML only: `uv run python src/build_route1_model_report_suite.py --stage report`

## How To Read Model Tables

| column | meaning |
| --- | --- |
| model | Unique fitted model/subvariant name. |
| formula | Statsmodels formula used to fit that subvariant. |
| family | Estimator class, e.g. OLS with child-clustered SE or GEE with a specified response family. |
| status | `fit` if the model converged; otherwise the recorded failure or empty-data reason. |
| n_obs | Number of modeled rows used by that subvariant. |
| n_children | Number of distinct child IDs contributing rows, when defined. |
| r2_or_observed_fitted_r2 | OLS R2 when available; otherwise squared correlation between observed and fitted values. |
| estimate | Coefficient estimate on the model's scale. Log-link models are on the log expected-outcome scale. |
| std_error | Standard error; clustered or GEE robust where that estimator is used. |
| p_value | Wald-style p-value supplied by the fitted statsmodels object. |

## Scientific Map

| comparison | scientific question | matched design |
| --- | --- | --- |
| child vs random | Do children differ from utterances sampled uniformly from the age-bin vocabulary? | same child row, same context window, same word count |
| child vs unigram | Do children differ from a frequency-only language baseline? | same child row, same context window, same word count |
| child vs bigram | Do children differ from a local one-step sequence baseline seeded by the caretaker context? | same child row, same context window, same word count |
| child vs trigram | Do children differ from a local two-step sequence baseline seeded by the caretaker context? | same child row, same context window, same word count |
| child vs caretaker | Are children moving toward caretaker-like information density and effort? | not row-matched; comparisons control word count and cluster by child where possible |

## Data Used

The descriptive trajectory plots use full age-bin aggregates from the available
k3 scored rows. The more flexible exploratory models use bounded samples where
needed so the report can be regenerated quickly. Real-minus-baseline delta
models use row-matched child rows, so their interpretation is tighter than the
child-versus-caretaker comparison.

Extraction counts:

| dataset | role | target_variant | context_k | rows |
| --- | --- | --- | --- | --- |
| Brown | caretaker | caretaker | k0 | 64206 |
| Brown | caretaker | caretaker | k1 | 64206 |
| Brown | caretaker | caretaker | k2 | 64206 |
| Brown | caretaker | caretaker | k3 | 64206 |
| Brown | child | bigram | k0 | 92555 |
| Brown | child | bigram | k1 | 92555 |
| Brown | child | bigram | k2 | 92555 |
| Brown | child | bigram | k3 | 92555 |
| Brown | child | random | k0 | 92555 |
| Brown | child | random | k1 | 92555 |
| Brown | child | random | k2 | 92555 |
| Brown | child | random | k3 | 92555 |
| Brown | child | real | k0 | 92555 |
| Brown | child | real | k1 | 92555 |
| Brown | child | real | k2 | 92555 |
| Brown | child | real | k3 | 92555 |
| Brown | child | trigram | k0 | 92555 |
| Brown | child | trigram | k1 | 92555 |
| Brown | child | trigram | k2 | 92555 |
| Brown | child | trigram | k3 | 92555 |
| Brown | child | unigram | k0 | 92555 |
| Brown | child | unigram | k1 | 92555 |
| Brown | child | unigram | k2 | 92555 |
| Brown | child | unigram | k3 | 92555 |
| Manchester | caretaker | caretaker | k0 | 342246 |
| Manchester | caretaker | caretaker | k1 | 342246 |
| Manchester | caretaker | caretaker | k2 | 342246 |
| Manchester | caretaker | caretaker | k3 | 342246 |
| Manchester | child | bigram | k0 | 232614 |
| Manchester | child | bigram | k1 | 232614 |

Context entropy status:

| role | target_variant | context_k | context_entropy_join_status | rows |
| --- | --- | --- | --- | --- |
| caretaker | caretaker | k0 |  | 668903 |
| caretaker | caretaker | k1 |  | 668903 |
| caretaker | caretaker | k2 |  | 668903 |
| caretaker | caretaker | k3 |  | 668903 |
| child | bigram | k0 |  | 446508 |
| child | bigram | k1 |  | 446508 |
| child | bigram | k2 |  | 446508 |
| child | bigram | k3 |  | 446508 |
| child | random | k0 |  | 446508 |
| child | random | k1 |  | 446508 |
| child | random | k2 |  | 446508 |
| child | random | k3 |  | 446508 |
| child | real | k0 |  | 446508 |
| child | real | k1 |  | 446508 |
| child | real | k2 |  | 446508 |
| child | real | k3 |  | 446508 |
| child | trigram | k0 |  | 446508 |
| child | trigram | k1 |  | 446508 |
| child | trigram | k2 |  | 446508 |
| child | trigram | k3 |  | 446508 |
| child | unigram | k0 |  | 446508 |
| child | unigram | k1 |  | 446508 |
| child | unigram | k2 |  | 446508 |
| child | unigram | k3 |  | 446508 |

Response-level entropy features present: `False`.

This scorer run includes neither response-level entropy nor scorer-specific next-token entropy/top-k certainty features. The Z3/Z4/Z10 families are therefore explicitly unavailable; no predictor from another scorer is substituted.

## Derived Predictors

| predictor | meaning |
| --- | --- |
| context_entropy_bits | Scorer-specific next-token entropy after the preceding caretaker context. |
| context_next_top1_prob | Probability assigned to the single most likely next token after the caretaker context. |
| context_word_count | Surface word count of the preceding caretaker context window. |
| context_question_type | Rule-based classification of the caretaker context as wh-question, yes/no question, other question, or not question. |
| baseline deltas | Real child bits minus matched random/unigram/bigram/trigram bits for the same utterance row and context. |
| age_after_24 / age_after_36 | Piecewise age transforms available for future nonlinear models. |
| any_effort_fallback | Whether any syllable/phoneme effort count needed an automatic fallback. |

**How to read this plot.** Each cell is a Pearson correlation between two
predictors. Darker positive cells mean two predictors rise together; darker
negative cells mean one tends to fall when the other rises. This is a warning
system for model design, not a result about development.

![Predictor correlations](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/exploratory_predictor_correlation.png)

## Model Family Manifest

This table is the audit trail for the zoo. A **family** is a scientific question
such as child-versus-baseline or context entropy predicting effort. A
**subvariant** is a true model change, usually replacing the effort definition
or the information-density unit. Alternate plots of the same fitted model are
diagnostic views, not subvariants.

| family_id | family_title | subvariant | model | question | formula | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Z1 | Information With Child Identity | effort: Words | Z1 Information | child FE | effort=Words | At the same words level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_words_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.5714 |
| Z1 | Information With Child Identity | effort: Morphemes | Z1 Information | child FE | effort=Morphemes | At the same morphemes level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_morphemes_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.5501 |
| Z1 | Information With Child Identity | effort: Syllables: CMU/pkg | Z1 Information | child FE | effort=Syllables: CMU/pkg | At the same syllables: cmu/pkg level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_syllables_cmu_or_pkg_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.6253 |
| Z1 | Information With Child Identity | effort: Syllables: pkg | Z1 Information | child FE | effort=Syllables: pkg | At the same syllables: pkg level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_syllables_pkg_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.5975 |
| Z1 | Information With Child Identity | effort: Phonemes | Z1 Information | child FE | effort=Phonemes | At the same phonemes level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_phonemes_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.6147 |
| Z2 | Nonlinear Information Density | unit: Words | Z2 Information density | nonlinear age | unit=Words | Does information per words follow a nonlinear developmental trajectory? | bits_per_word ~ age_months_z + I(age_months_z ** 2) + log_nb_words + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.3771 |
| Z2 | Nonlinear Information Density | unit: Morphemes | Z2 Information density | nonlinear age | unit=Morphemes | Does information per morphemes follow a nonlinear developmental trajectory? | bits_per_morpheme ~ age_months_z + I(age_months_z ** 2) + log_nb_morphemes + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.4343 |
| Z2 | Nonlinear Information Density | unit: Syllables: CMU/pkg | Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | Does information per syllables: cmu/pkg follow a nonlinear developmental trajectory? | bits_per_syllable_cmu_or_pkg ~ age_months_z + I(age_months_z ** 2) + log_nb_syllables + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.4981 |
| Z2 | Nonlinear Information Density | unit: Syllables: pkg | Z2 Information density | nonlinear age | unit=Syllables: pkg | Does information per syllables: pkg follow a nonlinear developmental trajectory? | bits_per_syllable_pkg ~ age_months_z + I(age_months_z ** 2) + log_nb_syllables + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.4414 |
| Z2 | Nonlinear Information Density | unit: Phonemes | Z2 Information density | nonlinear age | unit=Phonemes | Does information per phonemes follow a nonlinear developmental trajectory? | bits_per_phoneme ~ age_months_z + I(age_months_z ** 2) + log_nb_phonemes + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.5489 |
| Z3 | Context Entropy Predicting Effort | effort: Words | Z3 Effort from context entropy | effort=Words | Do children produce more words after more uncertain caretaker contexts? | nb_words ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z3 | Context Entropy Predicting Effort | effort: Morphemes | Z3 Effort from context entropy | effort=Morphemes | Do children produce more morphemes after more uncertain caretaker contexts? | nb_morphemes ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z3 | Context Entropy Predicting Effort | effort: Syllables: CMU/pkg | Z3 Effort from context entropy | effort=Syllables: CMU/pkg | Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts? | nb_syllables_cmu_or_pkg ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z3 | Context Entropy Predicting Effort | effort: Syllables: pkg | Z3 Effort from context entropy | effort=Syllables: pkg | Do children produce more syllables: pkg after more uncertain caretaker contexts? | nb_syllables_pkg ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z3 | Context Entropy Predicting Effort | effort: Phonemes | Z3 Effort from context entropy | effort=Phonemes | Do children produce more phonemes after more uncertain caretaker contexts? | nb_phonemes ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z4 | Context Entropy Predicting Information | effort: Words | Z4 Information from context entropy | effort=Words | Is total child information related to context entropy after words is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_words_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | empty data |  |  |  |
| Z4 | Context Entropy Predicting Information | effort: Morphemes | Z4 Information from context entropy | effort=Morphemes | Is total child information related to context entropy after morphemes is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_morphemes_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | empty data |  |  |  |
| Z4 | Context Entropy Predicting Information | effort: Syllables: CMU/pkg | Z4 Information from context entropy | effort=Syllables: CMU/pkg | Is total child information related to context entropy after syllables: cmu/pkg is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_syllables_cmu_or_pkg_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | empty data |  |  |  |
| Z4 | Context Entropy Predicting Information | effort: Syllables: pkg | Z4 Information from context entropy | effort=Syllables: pkg | Is total child information related to context entropy after syllables: pkg is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_syllables_pkg_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | empty data |  |  |  |
| Z4 | Context Entropy Predicting Information | effort: Phonemes | Z4 Information from context entropy | effort=Phonemes | Is total child information related to context entropy after phonemes is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_phonemes_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | empty data |  |  |  |
| Z5 | Scoring Context Window Sensitivity | unit: Words | Z5 Context window sensitivity | unit=Words | Does the age trajectory of information per words change across k1/k2/k3 scoring windows? | bits_per_word ~ age_months_z * C(context_k) + log_nb_words | gee_gaussian | fit | 1.554e+04 | 21 | 0.3709 |
| Z5 | Scoring Context Window Sensitivity | unit: Morphemes | Z5 Context window sensitivity | unit=Morphemes | Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows? | bits_per_morpheme ~ age_months_z * C(context_k) + log_nb_morphemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.4357 |
| Z5 | Scoring Context Window Sensitivity | unit: Syllables: CMU/pkg | Z5 Context window sensitivity | unit=Syllables: CMU/pkg | Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows? | bits_per_syllable_cmu_or_pkg ~ age_months_z * C(context_k) + log_nb_syllables | gee_gaussian | fit | 1.554e+04 | 21 | 0.4784 |
| Z5 | Scoring Context Window Sensitivity | unit: Syllables: pkg | Z5 Context window sensitivity | unit=Syllables: pkg | Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows? | bits_per_syllable_pkg ~ age_months_z * C(context_k) + log_nb_syllables | gee_gaussian | fit | 1.554e+04 | 21 | 0.4246 |
| Z5 | Scoring Context Window Sensitivity | unit: Phonemes | Z5 Context window sensitivity | unit=Phonemes | Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows? | bits_per_phoneme ~ age_months_z * C(context_k) + log_nb_phonemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.5317 |
| Z6 | Question Type Predicting Effort | effort: Words | Z6 Question-type effort | effort=Words | Does caretaker question type modulate child words, and does that modulation change with age? | nb_words ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 1.554e+04 | 21 | 0.1003 |
| Z6 | Question Type Predicting Effort | effort: Morphemes | Z6 Question-type effort | effort=Morphemes | Does caretaker question type modulate child morphemes, and does that modulation change with age? | nb_morphemes ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 1.554e+04 | 21 | 0.09977 |
| Z6 | Question Type Predicting Effort | effort: Syllables: CMU/pkg | Z6 Question-type effort | effort=Syllables: CMU/pkg | Does caretaker question type modulate child syllables: cmu/pkg, and does that modulation change with age? | nb_syllables_cmu_or_pkg ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 1.554e+04 | 21 | 0.08597 |
| Z6 | Question Type Predicting Effort | effort: Syllables: pkg | Z6 Question-type effort | effort=Syllables: pkg | Does caretaker question type modulate child syllables: pkg, and does that modulation change with age? | nb_syllables_pkg ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 1.554e+04 | 21 | 0.07985 |
| Z6 | Question Type Predicting Effort | effort: Phonemes | Z6 Question-type effort | effort=Phonemes | Does caretaker question type modulate child phonemes, and does that modulation change with age? | nb_phonemes ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 1.554e+04 | 21 | 0.08059 |
| Z7 | Real Children Versus All Matched Baselines | effort: Words | Z7 Baseline comparison | effort=Words | Do real child utterances differ from random/ngram baselines after controlling words? | sum_bits ~ age_months_z * C(target_variant) + nb_words_z | gee_gamma_log | fit | 1.822e+04 | 21 | 0.06457 |
| Z7 | Real Children Versus All Matched Baselines | effort: Morphemes | Z7 Baseline comparison | effort=Morphemes | Do real child utterances differ from random/ngram baselines after controlling morphemes? | sum_bits ~ age_months_z * C(target_variant) + nb_morphemes_z | gee_gamma_log | fit | 1.822e+04 | 21 | 0.05524 |
| Z7 | Real Children Versus All Matched Baselines | effort: Syllables: CMU/pkg | Z7 Baseline comparison | effort=Syllables: CMU/pkg | Do real child utterances differ from random/ngram baselines after controlling syllables: cmu/pkg? | sum_bits ~ age_months_z * C(target_variant) + nb_syllables_cmu_or_pkg_z | gee_gamma_log | fit | 1.822e+04 | 21 | 0.04919 |
| Z7 | Real Children Versus All Matched Baselines | effort: Syllables: pkg | Z7 Baseline comparison | effort=Syllables: pkg | Do real child utterances differ from random/ngram baselines after controlling syllables: pkg? | sum_bits ~ age_months_z * C(target_variant) + nb_syllables_pkg_z | gee_gamma_log | fit | 1.822e+04 | 21 | 0.0508 |
| Z7 | Real Children Versus All Matched Baselines | effort: Phonemes | Z7 Baseline comparison | effort=Phonemes | Do real child utterances differ from random/ngram baselines after controlling phonemes? | sum_bits ~ age_months_z * C(target_variant) + nb_phonemes_z | gee_gamma_log | fit | 1.822e+04 | 21 | 0.04584 |
| Z8 | Children Versus Caretakers | effort: Words | Z8 Child vs caretaker information | effort=Words | Do child and caretaker total-bit trajectories differ after controlling words? | sum_bits ~ age_months_z * C(speaker_group) + nb_words_z | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2249 |
| Z8 | Children Versus Caretakers | effort: Morphemes | Z8 Child vs caretaker information | effort=Morphemes | Do child and caretaker total-bit trajectories differ after controlling morphemes? | sum_bits ~ age_months_z * C(speaker_group) + nb_morphemes_z | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2677 |
| Z8 | Children Versus Caretakers | effort: Syllables: CMU/pkg | Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg? | sum_bits ~ age_months_z * C(speaker_group) + nb_syllables_cmu_or_pkg_z | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2018 |
| Z8 | Children Versus Caretakers | effort: Syllables: pkg | Z8 Child vs caretaker information | effort=Syllables: pkg | Do child and caretaker total-bit trajectories differ after controlling syllables: pkg? | sum_bits ~ age_months_z * C(speaker_group) + nb_syllables_pkg_z | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2295 |
| Z8 | Children Versus Caretakers | effort: Phonemes | Z8 Child vs caretaker information | effort=Phonemes | Do child and caretaker total-bit trajectories differ after controlling phonemes? | sum_bits ~ age_months_z * C(speaker_group) + nb_phonemes_z | gee_gamma_log | fit | 1.008e+04 | 21 | 0.1667 |
| Z9 | Information Per Effort Unit | unit: Words | Z9 Information per unit | unit=Words | Does information per words change with age after child identity is controlled? | bits_per_word ~ age_months_z + log_nb_words + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.377 |
| Z9 | Information Per Effort Unit | unit: Morphemes | Z9 Information per unit | unit=Morphemes | Does information per morphemes change with age after child identity is controlled? | bits_per_morpheme ~ age_months_z + log_nb_morphemes + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.4342 |
| Z9 | Information Per Effort Unit | unit: Syllables: CMU/pkg | Z9 Information per unit | unit=Syllables: CMU/pkg | Does information per syllables: cmu/pkg change with age after child identity is controlled? | bits_per_syllable_cmu_or_pkg ~ age_months_z + log_nb_syllables + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.498 |
| Z9 | Information Per Effort Unit | unit: Syllables: pkg | Z9 Information per unit | unit=Syllables: pkg | Does information per syllables: pkg change with age after child identity is controlled? | bits_per_syllable_pkg ~ age_months_z + log_nb_syllables + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.4413 |
| Z9 | Information Per Effort Unit | unit: Phonemes | Z9 Information per unit | unit=Phonemes | Does information per phonemes change with age after child identity is controlled? | bits_per_phoneme ~ age_months_z + log_nb_phonemes + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.5476 |
| Z10 | Context Certainty Predicting Effort | effort: Words | Z10 Context certainty | effort=Words | Is child words lower when the model assigns high probability to the most likely next token? | nb_words ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z10 | Context Certainty Predicting Effort | effort: Morphemes | Z10 Context certainty | effort=Morphemes | Is child morphemes lower when the model assigns high probability to the most likely next token? | nb_morphemes ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z10 | Context Certainty Predicting Effort | effort: Syllables: CMU/pkg | Z10 Context certainty | effort=Syllables: CMU/pkg | Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token? | nb_syllables_cmu_or_pkg ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z10 | Context Certainty Predicting Effort | effort: Syllables: pkg | Z10 Context certainty | effort=Syllables: pkg | Is child syllables: pkg lower when the model assigns high probability to the most likely next token? | nb_syllables_pkg ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z10 | Context Certainty Predicting Effort | effort: Phonemes | Z10 Context certainty | effort=Phonemes | Is child phonemes lower when the model assigns high probability to the most likely next token? | nb_phonemes ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | empty data |  |  |  |
| Z11 | Real Minus Baseline Delta | main specification | Z11 Real-minus-baseline delta | no effort control | Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls? | delta_sum_bits ~ age_months_z * C(baseline_variant) + C(child_id) | ols_cluster | fit | 1.786e+06 | 21 | 0.2807 |
| Z11 | Real Minus Baseline Delta | effort: Words | Z11 Real-minus-baseline delta | effort=Words | Does the real-child advantage or penalty relative to each baseline change with age after controlling words? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_words_z + C(child_id) | ols_cluster | fit | 1.786e+06 | 21 | 0.4911 |
| Z11 | Real Minus Baseline Delta | effort: Morphemes | Z11 Real-minus-baseline delta | effort=Morphemes | Does the real-child advantage or penalty relative to each baseline change with age after controlling morphemes? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_morphemes_z + C(child_id) | ols_cluster | fit | 1.786e+06 | 21 | 0.4761 |
| Z11 | Real Minus Baseline Delta | effort: Syllables: CMU/pkg | Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: cmu/pkg? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_syllables_cmu_or_pkg_z + C(child_id) | ols_cluster | fit | 1.786e+06 | 21 | 0.4212 |
| Z11 | Real Minus Baseline Delta | effort: Syllables: pkg | Z11 Real-minus-baseline delta | effort=Syllables: pkg | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: pkg? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_syllables_pkg_z + C(child_id) | ols_cluster | fit | 1.786e+06 | 21 | 0.4215 |
| Z11 | Real Minus Baseline Delta | effort: Phonemes | Z11 Real-minus-baseline delta | effort=Phonemes | Does the real-child advantage or penalty relative to each baseline change with age after controlling phonemes? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_phonemes_z + C(child_id) | ols_cluster | fit | 1.786e+06 | 21 | 0.4203 |

## Omnibus Baseline Trajectories

These plots answer the first sanity question: how far are real child utterances
from increasingly structured baselines over developmental time?

**How to read this plot.** Each line is an age-bin mean for one target type.
This plot uses total utterance bits, so it is descriptive and still reflects
utterance-size differences.

![All baseline total bits](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/baseline_all_total_bits.png)

**How to read this plot.** This is the same baseline comparison after dividing
total bits by word count. It is a direct information-density view, but it only
controls word count, not phonemes, syllables, or morphemes.

![All baseline bits per word](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/baseline_all_bits_per_word.png)

Because the generated baselines are word-count matched but not necessarily
phoneme-, syllable-, or morpheme-matched, effort profiles are checked directly.

**How to read this plot.** Each panel checks whether real and generated
utterances differ in non-word effort units. The baselines are word-count
matched, but they can still differ in morphemes, syllables, and phonemes.

![Baseline effort profiles](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/baseline_effort_profiles_nonword_units.png)

Real-minus-baseline deltas:

| age_bin | baseline_variant | mean_delta | sem_delta | n_rows | outcome |
| --- | --- | --- | --- | --- | --- |
| 006-023 | bigram | -3.944 | 0.07479 | 62816 | delta_sum_bits |
| 006-023 | random | -20.88 | 0.1121 | 62816 | delta_sum_bits |
| 006-023 | trigram | -2.374 | 0.06685 | 62816 | delta_sum_bits |
| 006-023 | unigram | -5.616 | 0.07453 | 62816 | delta_sum_bits |
| 024-029 | bigram | -6.869 | 0.04856 | 162210 | delta_sum_bits |
| 024-029 | random | -35.24 | 0.09301 | 162210 | delta_sum_bits |
| 024-029 | trigram | -5.172 | 0.04625 | 162210 | delta_sum_bits |
| 024-029 | unigram | -9.391 | 0.04908 | 162210 | delta_sum_bits |
| 030-035 | bigram | -9.569 | 0.05832 | 142447 | delta_sum_bits |
| 030-035 | random | -49.56 | 0.1299 | 142447 | delta_sum_bits |
| 030-035 | trigram | -7.397 | 0.05704 | 142447 | delta_sum_bits |
| 030-035 | unigram | -13.17 | 0.05999 | 142447 | delta_sum_bits |
| 036-041 | bigram | -9.418 | 0.1218 | 37206 | delta_sum_bits |
| 036-041 | random | -59.78 | 0.2819 | 37206 | delta_sum_bits |
| 036-041 | trigram | -7.117 | 0.119 | 37206 | delta_sum_bits |
| 036-041 | unigram | -13.99 | 0.1232 | 37206 | delta_sum_bits |
| 042-047 | bigram | -12.85 | 0.2042 | 16345 | delta_sum_bits |
| 042-047 | random | -73.17 | 0.4945 | 16345 | delta_sum_bits |
| 042-047 | trigram | -10.18 | 0.2028 | 16345 | delta_sum_bits |
| 042-047 | unigram | -18.62 | 0.213 | 16345 | delta_sum_bits |
| 048-053 | bigram | -11.27 | 0.2383 | 12909 | delta_sum_bits |
| 048-053 | random | -75.95 | 0.5364 | 12909 | delta_sum_bits |
| 048-053 | trigram | -8.439 | 0.2341 | 12909 | delta_sum_bits |
| 048-053 | unigram | -17.38 | 0.2334 | 12909 | delta_sum_bits |
| 054-059 | bigram | -12.28 | 0.2802 | 10033 | delta_sum_bits |
| 054-059 | random | -80.91 | 0.6598 | 10033 | delta_sum_bits |
| 054-059 | trigram | -9.041 | 0.2735 | 10033 | delta_sum_bits |
| 054-059 | unigram | -18.58 | 0.2788 | 10033 | delta_sum_bits |
| 060-065 | bigram | -14.47 | 0.5266 | 2542 | delta_sum_bits |
| 060-065 | random | -81.5 | 1.317 | 2542 | delta_sum_bits |
| 060-065 | trigram | -11.43 | 0.4975 | 2542 | delta_sum_bits |
| 060-065 | unigram | -21.05 | 0.5446 | 2542 | delta_sum_bits |
| 006-023 | bigram | -1.357 | 0.0324 | 62816 | delta_bits_per_word |
| 006-023 | random | -9.49 | 0.04247 | 62816 | delta_bits_per_word |
| 006-023 | trigram | -0.7704 | 0.02878 | 62816 | delta_bits_per_word |
| 006-023 | unigram | -2.045 | 0.03297 | 62816 | delta_bits_per_word |
| 024-029 | bigram | -2.144 | 0.01945 | 162210 | delta_bits_per_word |
| 024-029 | random | -13.82 | 0.02637 | 162210 | delta_bits_per_word |
| 024-029 | trigram | -1.534 | 0.01839 | 162210 | delta_bits_per_word |
| 024-029 | unigram | -3.045 | 0.01927 | 162210 | delta_bits_per_word |

## Explicit Comparison Models

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus random: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.7157 | Does the real-child minus random total-bit gap change with age after controlling words and child identity? |
| Child minus random: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.6786 | Does the real-child minus random total-bit gap change with age after controlling morphemes and child identity? |
| Child minus random: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.589 | Does the real-child minus random total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus random: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.5835 | Does the real-child minus random total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus random: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.5846 | Does the real-child minus random total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs random | effort=Words | gee_gamma_log | fit | 7335 | 21 | 0.07032 | Do real child and random total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs random | effort=Morphemes | gee_gamma_log | fit | 7335 | 21 | 0.07087 | Do real child and random total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7335 | 21 | 0.07428 | Do real child and random total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs random | effort=Syllables: pkg | gee_gamma_log | fit | 7335 | 21 | 0.07508 | Do real child and random total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs random | effort=Phonemes | gee_gamma_log | fit | 7335 | 21 | 0.0691 | Do real child and random total-bit trajectories diverge over age when phonemes is controlled? |
| Child minus unigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.3108 | Does the real-child minus unigram total-bit gap change with age after controlling words and child identity? |
| Child minus unigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.2915 | Does the real-child minus unigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus unigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.2036 | Does the real-child minus unigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus unigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.2062 | Does the real-child minus unigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus unigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.2037 | Does the real-child minus unigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs unigram | effort=Words | gee_gamma_log | fit | 7110 | 21 | 0.4738 | Do real child and unigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs unigram | effort=Morphemes | gee_gamma_log | fit | 7110 | 21 | 0.4597 | Do real child and unigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs unigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7110 | 21 | 0.3767 | Do real child and unigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs unigram | effort=Syllables: pkg | gee_gamma_log | fit | 7110 | 21 | 0.3323 | Do real child and unigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs unigram | effort=Phonemes | gee_gamma_log | fit | 7110 | 21 | 0.4157 | Do real child and unigram total-bit trajectories diverge over age when phonemes is controlled? |
| Child minus bigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.1769 | Does the real-child minus bigram total-bit gap change with age after controlling words and child identity? |
| Child minus bigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.1654 | Does the real-child minus bigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus bigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.105 | Does the real-child minus bigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus bigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.1073 | Does the real-child minus bigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus bigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.1051 | Does the real-child minus bigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs bigram | effort=Words | gee_gamma_log | fit | 7245 | 21 | 0.1201 | Do real child and bigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs bigram | effort=Morphemes | gee_gamma_log | fit | 7245 | 21 | 0.1123 | Do real child and bigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs bigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7245 | 21 | 0.1211 | Do real child and bigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs bigram | effort=Syllables: pkg | gee_gamma_log | fit | 7245 | 21 | 0.1208 | Do real child and bigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs bigram | effort=Phonemes | gee_gamma_log | fit | 7245 | 21 | 0.1188 | Do real child and bigram total-bit trajectories diverge over age when phonemes is controlled? |
| Child minus trigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.1309 | Does the real-child minus trigram total-bit gap change with age after controlling words and child identity? |
| Child minus trigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.121 | Does the real-child minus trigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus trigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.07438 | Does the real-child minus trigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus trigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.07647 | Does the real-child minus trigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus trigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.07417 | Does the real-child minus trigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs trigram | effort=Words | gee_gamma_log | fit | 7335 | 21 | 0.4105 | Do real child and trigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs trigram | effort=Morphemes | gee_gamma_log | fit | 7335 | 21 | 0.4147 | Do real child and trigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs trigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7335 | 21 | 0.4014 | Do real child and trigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs trigram | effort=Syllables: pkg | gee_gamma_log | fit | 7335 | 21 | 0.3547 | Do real child and trigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs trigram | effort=Phonemes | gee_gamma_log | fit | 7335 | 21 | 0.38 | Do real child and trigram total-bit trajectories diverge over age when phonemes is controlled? |
| Child vs caretaker: total bits | effort=Words | gee_gamma_log | fit | 10075 | 21 | 0.2249 | Do child and caretaker total-bit trajectories differ after controlling words? |
| Child vs caretaker: total bits | effort=Morphemes | gee_gamma_log | fit | 10075 | 21 | 0.2677 | Do child and caretaker total-bit trajectories differ after controlling morphemes? |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 10075 | 21 | 0.2018 | Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg? |
| Child vs caretaker: total bits | effort=Syllables: pkg | gee_gamma_log | fit | 10075 | 21 | 0.2295 | Do child and caretaker total-bit trajectories differ after controlling syllables: pkg? |
| Child vs caretaker: total bits | effort=Phonemes | gee_gamma_log | fit | 10075 | 21 | 0.1667 | Do child and caretaker total-bit trajectories differ after controlling phonemes? |

**How to read this plot.** Each row is one child-vs-baseline or
child-vs-caretaker model, and each column is the effort measure controlled in
that version. This is a model-fit overview, not the substantive effect itself:
it shows whether the comparison model explains more or less variance depending
on how effort is controlled.

![Effort-controlled comparison model fit](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/effort_controlled_comparison_model_r2.png)

**How to read this plot.** Each point is an age-related coefficient from an
effort-controlled comparison model. Values to the right of zero mean the
age-related gap increases; values to the left mean it decreases. The same
comparison is repeated under words, morphemes, syllables, and phonemes as
separate effort controls.

![Effort-controlled comparison age coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/effort_controlled_comparison_age_coefficients.png)

Key comparison coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus random: total bits | effort=Words | C(child_id)[T.Alex] | -3.979 | 0.69 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Anne] | -5.665 | 1.096 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Aran] | -6.543 | 1.034 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Becky] | -7.242 | 0.8686 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Carl] | -3.453 | 1.276 | 0.007 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Dominic] | -3.74 | 0.9831 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Ethan] | -3.646 | 1.508 | 0.016 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Eve] | 1.934 | 1.726 | 0.263 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Gail] | -5.286 | 0.9639 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Joel] | -4.373 | 0.9316 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.John] | -4.474 | 0.9716 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Lily] | -4.819 | 0.8357 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Liz] | -6.412 | 1.076 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Naima] | -1.286 | 1.497 | 0.391 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Nicole] | -2.751 | 0.7449 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Ruth] | -4.596 | 0.8477 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Sarah] | 2.27 | 0.4421 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Violet] | -4.919 | 0.8862 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Warren] | -4.792 | 1.149 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.William] | -4.75 | 0.8655 | <.001 |
| Child minus random: total bits | effort=Words | age_months_z | -5.793 | 0.8418 | <.001 |
| Child minus random: total bits | effort=Words | nb_words_z | -38.56 | 0.6028 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Alex] | -3.109 | 0.741 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Anne] | -3.841 | 1.244 | 0.002 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Aran] | -6.14 | 1.177 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Becky] | -5.512 | 0.9706 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Carl] | -0.979 | 1.494 | 0.512 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -2.723 | 1.085 | 0.012 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Ethan] | -2.075 | 1.752 | 0.236 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Eve] | 0.4042 | 1.987 | 0.839 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Gail] | -2.993 | 1.099 | 0.006 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Joel] | -2.548 | 1.045 | 0.015 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.John] | -2.842 | 1.08 | 0.008 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Lily] | -4.043 | 0.9677 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Liz] | -5.183 | 1.224 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Naima] | 0.9467 | 1.81 | 0.601 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Nicole] | -2.266 | 0.7592 | 0.003 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Ruth] | -5.514 | 0.8822 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Sarah] | 1.691 | 0.5574 | 0.002 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Violet] | -4.474 | 1.016 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Warren] | -3.672 | 1.337 | 0.006 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.William] | -3.915 | 0.9567 | <.001 |
| Child minus random: total bits | effort=Morphemes | age_months_z | -5.772 | 1.001 | <.001 |
| Child minus random: total bits | effort=Morphemes | nb_morphemes_z | -37.45 | 0.7019 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Alex] | -4.029 | 1.018 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Anne] | -8.202 | 1.626 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Aran] | -11.25 | 1.511 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Becky] | -9.309 | 1.272 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Carl] | -6.577 | 1.924 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Dominic] | -4.09 | 1.472 | 0.005 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Ethan] | -6.013 | 2.307 | 0.009 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Eve] | -0.9478 | 2.674 | 0.723 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Gail] | -6.312 | 1.446 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Joel] | -5.011 | 1.394 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.John] | -4.411 | 1.461 | 0.003 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Lily] | -5.939 | 1.281 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Liz] | -9.388 | 1.596 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Naima] | -3.103 | 2.368 | 0.190 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Nicole] | -1.117 | 1.094 | 0.307 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Ruth] | -4.047 | 1.258 | 0.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Sarah] | 3.75 | 0.7159 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Violet] | -7.721 | 1.322 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Warren] | -7.017 | 1.753 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.William] | -5.992 | 1.283 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | age_months_z | -8.959 | 1.289 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | -33.82 | 0.9327 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Alex] | -2.694 | 1.034 | 0.009 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Anne] | -6.209 | 1.649 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Aran] | -10.27 | 1.516 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Becky] | -8.291 | 1.282 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Carl] | -5.486 | 1.928 | 0.004 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Dominic] | -3.069 | 1.48 | 0.038 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Ethan] | -5.771 | 2.29 | 0.012 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Eve] | -0.3922 | 2.66 | 0.883 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Gail] | -5.591 | 1.448 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Joel] | -4.095 | 1.401 | 0.003 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.John] | -3.515 | 1.467 | 0.017 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Lily] | -5.633 | 1.275 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Liz] | -8.221 | 1.605 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Naima] | -3.305 | 2.341 | 0.158 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Nicole] | 0.6966 | 1.119 | 0.534 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Ruth] | -3.189 | 1.267 | 0.012 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Sarah] | 4.304 | 0.6999 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Violet] | -6.768 | 1.328 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Warren] | -5.8 | 1.76 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.William] | -5.656 | 1.281 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | age_months_z | -9.181 | 1.272 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | nb_syllables_pkg_z | -33.47 | 0.9462 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Alex] | -2.937 | 1.075 | 0.006 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Anne] | -7.124 | 1.69 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Aran] | -10.11 | 1.567 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Becky] | -8.57 | 1.329 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Carl] | -5.033 | 1.988 | 0.011 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Dominic] | -2.461 | 1.545 | 0.111 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Ethan] | -4.211 | 2.377 | 0.076 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Eve] | -1.281 | 2.696 | 0.635 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Gail] | -4.98 | 1.508 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Joel] | -4.511 | 1.446 | 0.002 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.John] | -3.453 | 1.522 | 0.023 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Lily] | -6.063 | 1.3 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Liz] | -8.416 | 1.654 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Naima] | -2.753 | 2.387 | 0.249 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Nicole] | -1.075 | 1.153 | 0.352 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Ruth] | -5.209 | 1.296 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Sarah] | 2.389 | 0.7446 | 0.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Violet] | -7.659 | 1.351 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Warren] | -5.983 | 1.8 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.William] | -6.203 | 1.323 | <.001 |
| Child minus random: total bits | effort=Phonemes | age_months_z | -8.962 | 1.296 | <.001 |
| Child minus random: total bits | effort=Phonemes | nb_phonemes_z | -33.62 | 0.9331 | <.001 |
| Trajectory interaction: child vs random | effort=Words | C(target_variant)[T.real] | -0.6668 | 0.01483 | <.001 |
| Trajectory interaction: child vs random | effort=Words | age_months_z | 0.08213 | 0.01255 | <.001 |
| Trajectory interaction: child vs random | effort=Words | age_months_z:C(target_variant)[T.real] | -0.1155 | 0.01971 | <.001 |
| Trajectory interaction: child vs random | effort=Words | nb_words_z | 0.5103 | 0.01528 | <.001 |
| Trajectory interaction: child vs random | effort=Morphemes | C(target_variant)[T.real] | -0.5825 | 0.01525 | <.001 |
| Trajectory interaction: child vs random | effort=Morphemes | age_months_z | 0.0666 | 0.01055 | <.001 |
| Trajectory interaction: child vs random | effort=Morphemes | age_months_z:C(target_variant)[T.real] | -0.08781 | 0.01608 | <.001 |
| Trajectory interaction: child vs random | effort=Morphemes | nb_morphemes_z | 0.4755 | 0.01411 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | C(target_variant)[T.real] | -0.4344 | 0.01128 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | age_months_z | 0.036 | 0.01056 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.real] | -0.03123 | 0.01339 | 0.020 |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.4697 | 0.01329 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: pkg | C(target_variant)[T.real] | -0.4521 | 0.01183 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: pkg | age_months_z | 0.04111 | 0.01049 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: pkg | age_months_z:C(target_variant)[T.real] | -0.03591 | 0.0132 | 0.006 |
| Trajectory interaction: child vs random | effort=Syllables: pkg | nb_syllables_pkg_z | 0.4671 | 0.01342 | <.001 |
| Trajectory interaction: child vs random | effort=Phonemes | C(target_variant)[T.real] | -0.3929 | 0.01235 | <.001 |
| Trajectory interaction: child vs random | effort=Phonemes | age_months_z | 0.02393 | 0.0104 | 0.021 |
| Trajectory interaction: child vs random | effort=Phonemes | age_months_z:C(target_variant)[T.real] | -0.01612 | 0.01218 | 0.186 |
| Trajectory interaction: child vs random | effort=Phonemes | nb_phonemes_z | 0.4724 | 0.01308 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Alex] | -4.383 | 0.3786 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Anne] | -6.226 | 0.5046 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Aran] | -6.845 | 0.4419 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Becky] | -6.985 | 0.4294 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Carl] | -5.425 | 0.5317 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Dominic] | -3.859 | 0.4861 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Ethan] | -5.291 | 0.6201 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Eve] | -1.391 | 0.6752 | 0.039 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Gail] | -5.257 | 0.4518 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Joel] | -4.52 | 0.4533 | <.001 |

## Child Versus Random

**Question.** Does the real child utterance differ from the random baseline,
and does that gap change over development?

**Design.** This is the cleanest comparison in the current report: each
generated baseline utterance is matched to the same child utterance, same
preceding caretaker context, and same word count. The dashboard therefore shows
both raw trajectories and real-minus-baseline deltas. The fitted models below
then repeat the comparison with each effort measure controlled separately, so
the inference is not word-only.

**How to read this plot.** The top row compares real child and random
trajectories. The bottom row plots real-minus-baseline differences, so zero
means no gap and a changing line means the gap changes with age.

![Child versus random dashboard](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/child_vs_random_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus random: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.7157 | Does the real-child minus random total-bit gap change with age after controlling words and child identity? |
| Child minus random: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.6786 | Does the real-child minus random total-bit gap change with age after controlling morphemes and child identity? |
| Child minus random: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.589 | Does the real-child minus random total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus random: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.5835 | Does the real-child minus random total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus random: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.5846 | Does the real-child minus random total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs random | effort=Words | gee_gamma_log | fit | 7335 | 21 | 0.07032 | Do real child and random total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs random | effort=Morphemes | gee_gamma_log | fit | 7335 | 21 | 0.07087 | Do real child and random total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7335 | 21 | 0.07428 | Do real child and random total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs random | effort=Syllables: pkg | gee_gamma_log | fit | 7335 | 21 | 0.07508 | Do real child and random total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs random | effort=Phonemes | gee_gamma_log | fit | 7335 | 21 | 0.0691 | Do real child and random total-bit trajectories diverge over age when phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus random: total bits | effort=Words | C(child_id)[T.Alex] | -3.979 | 0.69 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Anne] | -5.665 | 1.096 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Aran] | -6.543 | 1.034 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Becky] | -7.242 | 0.8686 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Carl] | -3.453 | 1.276 | 0.007 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Dominic] | -3.74 | 0.9831 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Ethan] | -3.646 | 1.508 | 0.016 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Eve] | 1.934 | 1.726 | 0.263 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Gail] | -5.286 | 0.9639 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Joel] | -4.373 | 0.9316 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.John] | -4.474 | 0.9716 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Lily] | -4.819 | 0.8357 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Liz] | -6.412 | 1.076 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Naima] | -1.286 | 1.497 | 0.391 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Nicole] | -2.751 | 0.7449 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Ruth] | -4.596 | 0.8477 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Sarah] | 2.27 | 0.4421 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Violet] | -4.919 | 0.8862 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Warren] | -4.792 | 1.149 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.William] | -4.75 | 0.8655 | <.001 |
| Child minus random: total bits | effort=Words | age_months_z | -5.793 | 0.8418 | <.001 |
| Child minus random: total bits | effort=Words | nb_words_z | -38.56 | 0.6028 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Alex] | -3.109 | 0.741 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Anne] | -3.841 | 1.244 | 0.002 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Aran] | -6.14 | 1.177 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Becky] | -5.512 | 0.9706 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Carl] | -0.979 | 1.494 | 0.512 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -2.723 | 1.085 | 0.012 |
## Child Versus Unigram

**Question.** Does the real child utterance differ from the unigram baseline,
and does that gap change over development?

**Design.** This is the cleanest comparison in the current report: each
generated baseline utterance is matched to the same child utterance, same
preceding caretaker context, and same word count. The dashboard therefore shows
both raw trajectories and real-minus-baseline deltas. The fitted models below
then repeat the comparison with each effort measure controlled separately, so
the inference is not word-only.

**How to read this plot.** The top row compares real child and unigram
trajectories. The bottom row plots real-minus-baseline differences, so zero
means no gap and a changing line means the gap changes with age.

![Child versus unigram dashboard](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/child_vs_unigram_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus unigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.3108 | Does the real-child minus unigram total-bit gap change with age after controlling words and child identity? |
| Child minus unigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.2915 | Does the real-child minus unigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus unigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.2036 | Does the real-child minus unigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus unigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.2062 | Does the real-child minus unigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus unigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.2037 | Does the real-child minus unigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs unigram | effort=Words | gee_gamma_log | fit | 7110 | 21 | 0.4738 | Do real child and unigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs unigram | effort=Morphemes | gee_gamma_log | fit | 7110 | 21 | 0.4597 | Do real child and unigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs unigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7110 | 21 | 0.3767 | Do real child and unigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs unigram | effort=Syllables: pkg | gee_gamma_log | fit | 7110 | 21 | 0.3323 | Do real child and unigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs unigram | effort=Phonemes | gee_gamma_log | fit | 7110 | 21 | 0.4157 | Do real child and unigram total-bit trajectories diverge over age when phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Alex] | -4.383 | 0.3786 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Anne] | -6.226 | 0.5046 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Aran] | -6.845 | 0.4419 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Becky] | -6.985 | 0.4294 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Carl] | -5.425 | 0.5317 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Dominic] | -3.859 | 0.4861 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Ethan] | -5.291 | 0.6201 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Eve] | -1.391 | 0.6752 | 0.039 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Gail] | -5.257 | 0.4518 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Joel] | -4.52 | 0.4533 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.John] | -4.678 | 0.4828 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Lily] | -5.314 | 0.3458 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Liz] | -6.466 | 0.4781 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Naima] | -4.368 | 0.5707 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Nicole] | -2.301 | 0.4681 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Ruth] | -4.488 | 0.4686 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Sarah] | 0.7223 | 0.212 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Violet] | -6.595 | 0.3724 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Warren] | -5.616 | 0.4693 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.William] | -4.823 | 0.4244 | <.001 |
| Child minus unigram: total bits | effort=Words | age_months_z | -1.57 | 0.3204 | <.001 |
| Child minus unigram: total bits | effort=Words | nb_words_z | -11.94 | 0.4963 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Alex] | -4.101 | 0.3606 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Anne] | -5.661 | 0.4869 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Aran] | -6.727 | 0.4319 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Becky] | -6.443 | 0.4102 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Carl] | -4.674 | 0.5188 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -3.536 | 0.468 | <.001 |
## Child Versus Bigram

**Question.** Does the real child utterance differ from the bigram baseline,
and does that gap change over development?

**Design.** This is the cleanest comparison in the current report: each
generated baseline utterance is matched to the same child utterance, same
preceding caretaker context, and same word count. The dashboard therefore shows
both raw trajectories and real-minus-baseline deltas. The fitted models below
then repeat the comparison with each effort measure controlled separately, so
the inference is not word-only.

**How to read this plot.** The top row compares real child and bigram
trajectories. The bottom row plots real-minus-baseline differences, so zero
means no gap and a changing line means the gap changes with age.

![Child versus bigram dashboard](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/child_vs_bigram_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus bigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.1769 | Does the real-child minus bigram total-bit gap change with age after controlling words and child identity? |
| Child minus bigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.1654 | Does the real-child minus bigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus bigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.105 | Does the real-child minus bigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus bigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.1073 | Does the real-child minus bigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus bigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.1051 | Does the real-child minus bigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs bigram | effort=Words | gee_gamma_log | fit | 7245 | 21 | 0.1201 | Do real child and bigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs bigram | effort=Morphemes | gee_gamma_log | fit | 7245 | 21 | 0.1123 | Do real child and bigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs bigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7245 | 21 | 0.1211 | Do real child and bigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs bigram | effort=Syllables: pkg | gee_gamma_log | fit | 7245 | 21 | 0.1208 | Do real child and bigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs bigram | effort=Phonemes | gee_gamma_log | fit | 7245 | 21 | 0.1188 | Do real child and bigram total-bit trajectories diverge over age when phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Alex] | -4.191 | 0.3655 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Anne] | -5.962 | 0.4609 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Aran] | -6.494 | 0.3928 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Becky] | -6.862 | 0.4021 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Carl] | -5.275 | 0.468 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Dominic] | -3.741 | 0.4551 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Ethan] | -5.288 | 0.5431 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Eve] | -1.735 | 0.582 | 0.003 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Gail] | -5.145 | 0.4155 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Joel] | -4.6 | 0.4222 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.John] | -4.753 | 0.4528 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Lily] | -5.483 | 0.3035 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Liz] | -6.215 | 0.4312 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Naima] | -4.748 | 0.4931 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Nicole] | -2.137 | 0.4669 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Ruth] | -4.534 | 0.4533 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Sarah] | 0.4391 | 0.2135 | 0.040 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Violet] | -6.329 | 0.3288 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Warren] | -5.424 | 0.4099 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.William] | -4.618 | 0.3962 | <.001 |
| Child minus bigram: total bits | effort=Words | age_months_z | -1.175 | 0.278 | <.001 |
| Child minus bigram: total bits | effort=Words | nb_words_z | -8.773 | 0.5419 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Alex] | -3.979 | 0.3464 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Anne] | -5.547 | 0.4365 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Aran] | -6.409 | 0.378 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Becky] | -6.463 | 0.3778 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Carl] | -4.728 | 0.4447 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -3.501 | 0.4339 | <.001 |
## Child Versus Trigram

**Question.** Does the real child utterance differ from the trigram baseline,
and does that gap change over development?

**Design.** This is the cleanest comparison in the current report: each
generated baseline utterance is matched to the same child utterance, same
preceding caretaker context, and same word count. The dashboard therefore shows
both raw trajectories and real-minus-baseline deltas. The fitted models below
then repeat the comparison with each effort measure controlled separately, so
the inference is not word-only.

**How to read this plot.** The top row compares real child and trigram
trajectories. The bottom row plots real-minus-baseline differences, so zero
means no gap and a changing line means the gap changes with age.

![Child versus trigram dashboard](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/child_vs_trigram_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus trigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.1309 | Does the real-child minus trigram total-bit gap change with age after controlling words and child identity? |
| Child minus trigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.121 | Does the real-child minus trigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus trigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.07438 | Does the real-child minus trigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus trigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.07647 | Does the real-child minus trigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus trigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.07417 | Does the real-child minus trigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs trigram | effort=Words | gee_gamma_log | fit | 7335 | 21 | 0.4105 | Do real child and trigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs trigram | effort=Morphemes | gee_gamma_log | fit | 7335 | 21 | 0.4147 | Do real child and trigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs trigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7335 | 21 | 0.4014 | Do real child and trigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs trigram | effort=Syllables: pkg | gee_gamma_log | fit | 7335 | 21 | 0.3547 | Do real child and trigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs trigram | effort=Phonemes | gee_gamma_log | fit | 7335 | 21 | 0.38 | Do real child and trigram total-bit trajectories diverge over age when phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Alex] | -3.727 | 0.3279 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Anne] | -5.69 | 0.3941 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Aran] | -5.459 | 0.3259 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Becky] | -6.192 | 0.3517 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Carl] | -4.349 | 0.3837 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Dominic] | -3.243 | 0.3981 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Ethan] | -3.855 | 0.4425 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Eve] | -1.376 | 0.4628 | 0.003 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Gail] | -4.747 | 0.3575 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Joel] | -4.053 | 0.3676 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.John] | -4.142 | 0.3967 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Lily] | -4.746 | 0.248 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Liz] | -5.754 | 0.3637 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Naima] | -3.887 | 0.3905 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Nicole] | -2.225 | 0.4287 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Ruth] | -3.997 | 0.4073 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Sarah] | 0.1067 | 0.1934 | 0.581 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Violet] | -5.487 | 0.2707 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Warren] | -4.6 | 0.3327 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.William] | -4.113 | 0.3458 | <.001 |
| Child minus trigram: total bits | effort=Words | age_months_z | -0.9484 | 0.2209 | <.001 |
| Child minus trigram: total bits | effort=Words | nb_words_z | -7.266 | 0.5189 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Alex] | -3.543 | 0.3219 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Anne] | -5.347 | 0.3879 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Aran] | -5.393 | 0.3293 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Becky] | -5.856 | 0.3423 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Carl] | -3.908 | 0.3799 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -3.039 | 0.3947 | <.001 |


## Children Versus Caretakers

**Question.** Are children becoming more caretaker-like in information density,
or are child and caretaker trajectories governed by different constraints?

**Design.** This comparison is not row-matched. The fitted comparison models
repeat the child/caretaker contrast with each effort measure controlled
separately and cluster by child where the model family allows it, but this
should still be interpreted as a speaker-group developmental contrast rather
than a matched baseline test.

**How to read this plot.** The panels compare child and caretaker trajectories
over the child's age. Because this is not row-matched, the plot is useful for a
broad developmental contrast, not for claiming that a specific child response
is more or less efficient than its caretaker context.

![Child caretaker dashboard](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/child_vs_caretaker_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child vs caretaker: total bits | effort=Words | gee_gamma_log | fit | 10075 | 21 | 0.2249 | Do child and caretaker total-bit trajectories differ after controlling words? |
| Child vs caretaker: total bits | effort=Morphemes | gee_gamma_log | fit | 10075 | 21 | 0.2677 | Do child and caretaker total-bit trajectories differ after controlling morphemes? |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 10075 | 21 | 0.2018 | Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg? |
| Child vs caretaker: total bits | effort=Syllables: pkg | gee_gamma_log | fit | 10075 | 21 | 0.2295 | Do child and caretaker total-bit trajectories differ after controlling syllables: pkg? |
| Child vs caretaker: total bits | effort=Phonemes | gee_gamma_log | fit | 10075 | 21 | 0.1667 | Do child and caretaker total-bit trajectories differ after controlling phonemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child vs caretaker: total bits | effort=Words | C(speaker_group)[T.child] | -0.2244 | 0.02004 | <.001 |
| Child vs caretaker: total bits | effort=Words | age_months_z | -0.002654 | 0.009121 | 0.771 |
| Child vs caretaker: total bits | effort=Words | age_months_z:C(speaker_group)[T.child] | -0.03271 | 0.01172 | 0.005 |
| Child vs caretaker: total bits | effort=Words | nb_words_z | 0.4257 | 0.01071 | <.001 |
| Child vs caretaker: total bits | effort=Morphemes | C(speaker_group)[T.child] | -0.2226 | 0.02119 | <.001 |
| Child vs caretaker: total bits | effort=Morphemes | age_months_z | -0.0006609 | 0.01006 | 0.948 |
| Child vs caretaker: total bits | effort=Morphemes | age_months_z:C(speaker_group)[T.child] | -0.03875 | 0.01294 | 0.003 |
| Child vs caretaker: total bits | effort=Morphemes | nb_morphemes_z | 0.4214 | 0.01147 | <.001 |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | C(speaker_group)[T.child] | -0.2264 | 0.01765 | <.001 |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | age_months_z | -0.000575 | 0.007658 | 0.940 |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | age_months_z:C(speaker_group)[T.child] | -0.02956 | 0.01113 | 0.008 |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.451 | 0.01343 | <.001 |
| Child vs caretaker: total bits | effort=Syllables: pkg | C(speaker_group)[T.child] | -0.2264 | 0.01759 | <.001 |
| Child vs caretaker: total bits | effort=Syllables: pkg | age_months_z | -0.0005973 | 0.008215 | 0.942 |
| Child vs caretaker: total bits | effort=Syllables: pkg | age_months_z:C(speaker_group)[T.child] | -0.02551 | 0.0115 | 0.027 |
| Child vs caretaker: total bits | effort=Syllables: pkg | nb_syllables_pkg_z | 0.442 | 0.01364 | <.001 |
| Child vs caretaker: total bits | effort=Phonemes | C(speaker_group)[T.child] | -0.2247 | 0.01864 | <.001 |
| Child vs caretaker: total bits | effort=Phonemes | age_months_z | -0.002917 | 0.007963 | 0.714 |
| Child vs caretaker: total bits | effort=Phonemes | age_months_z:C(speaker_group)[T.child] | -0.02458 | 0.01107 | 0.026 |
| Child vs caretaker: total bits | effort=Phonemes | nb_phonemes_z | 0.4479 | 0.01399 | <.001 |

## Context Predictability And Effort

**Question.** Given the preceding caretaker context, do children modulate their
production effort or information density? This is the analysis family closest
to the proposal that contextual predictability should help predict child
utterance length.

**How to read this plot.** The x-axis is next-token entropy of the preceding
caretaker context. A rising line would mean children use more words when the
model sees the context as less predictive.

_Figure unavailable in this scorer run: Context entropy and child words._

**How to read this plot.** This asks whether information density, not just
utterance length, varies with context entropy. A rising line means higher bits
per word in less predictable contexts.

_Figure unavailable in this scorer run: Context entropy and bits per word._

**How to read this plot.** Lines compare child word count after different broad
caretaker context types. This is a conversational-control check: wh-questions,
yes/no questions, other questions, and non-questions can invite different
response lengths.

![Question type effort](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/question_type_child_words_by_age.png)

Context-model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Morphemes | gee_poisson | empty data |  |  |  | Is child morphemes lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Phonemes | gee_poisson | empty data |  |  |  | Is child phonemes lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Syllables: CMU/pkg | gee_poisson | empty data |  |  |  | Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Syllables: pkg | gee_poisson | empty data |  |  |  | Is child syllables: pkg lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Words | gee_poisson | empty data |  |  |  | Is child words lower when the model assigns high probability to the most likely next token? |
| Z3 Effort from context entropy | effort=Morphemes | gee_poisson | empty data |  |  |  | Do children produce more morphemes after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Phonemes | gee_poisson | empty data |  |  |  | Do children produce more phonemes after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | gee_poisson | empty data |  |  |  | Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Syllables: pkg | gee_poisson | empty data |  |  |  | Do children produce more syllables: pkg after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Words | gee_poisson | empty data |  |  |  | Do children produce more words after more uncertain caretaker contexts? |
| Z4 Information from context entropy | effort=Morphemes | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after morphemes is controlled? |
| Z4 Information from context entropy | effort=Phonemes | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after phonemes is controlled? |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after syllables: cmu/pkg is controlled? |
| Z4 Information from context entropy | effort=Syllables: pkg | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after syllables: pkg is controlled? |
| Z4 Information from context entropy | effort=Words | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after words is controlled? |
| Z5 Context window sensitivity | unit=Morphemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.4357 | Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Phonemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.5317 | Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | gee_gaussian | fit | 1.554e+04 | 21 | 0.4784 | Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Syllables: pkg | gee_gaussian | fit | 1.554e+04 | 21 | 0.4246 | Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Words | gee_gaussian | fit | 1.554e+04 | 21 | 0.3709 | Does the age trajectory of information per words change across k1/k2/k3 scoring windows? |

Context-model key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Words | age_months_z | -0.5332 | 0.1481 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k2] | 0.01662 | 0.0772 | 0.830 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k3] | 0.09349 | 0.05632 | 0.097 |
| Z5 Context window sensitivity | unit=Words | log_nb_words | -7.016 | 0.3224 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z | -0.4767 | 0.128 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k2] | 0.01553 | 0.07765 | 0.841 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k3] | 0.09443 | 0.05444 | 0.083 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z | -0.2511 | 0.07393 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k2] | 0.04583 | 0.0416 | 0.271 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k3] | 0.1059 | 0.03819 | 0.006 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z | -0.1877 | 0.09432 | 0.047 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k2] | -0.008937 | 0.04689 | 0.849 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k3] | 0.09467 | 0.05597 | 0.091 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z | 0.1306 | 0.06134 | 0.033 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k2] | 0.04539 | 0.03126 | 0.146 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k3] | 0.06966 | 0.02648 | 0.009 |
| Z6 Question-type effort | effort=Words | age_months_z | 0.1662 | 0.02665 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.not question] | 0.04538 | 0.01797 | 0.012 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.other question] | 0.08947 | 0.01921 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.wh-question] | 0.07435 | 0.0225 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.yes/no question] | 0.04097 | 0.02741 | 0.135 |
| Z6 Question-type effort | effort=Morphemes | age_months_z | 0.1743 | 0.02871 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.not question] | 0.04737 | 0.02012 | 0.019 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.other question] | 0.09663 | 0.02071 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.wh-question] | 0.07984 | 0.02642 | 0.003 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.05767 | 0.02886 | 0.046 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z | 0.1326 | 0.0238 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.not question] | 0.06296 | 0.01621 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.other question] | 0.1028 | 0.01965 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.09024 | 0.02861 | 0.002 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.05351 | 0.03197 | 0.094 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z | 0.1309 | 0.02231 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.not question] | 0.05947 | 0.01781 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.other question] | 0.1055 | 0.01982 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.08825 | 0.03135 | 0.005 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.05722 | 0.03049 | 0.060 |
| Z6 Question-type effort | effort=Phonemes | age_months_z | 0.1447 | 0.02387 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.not question] | 0.05202 | 0.01743 | 0.003 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.other question] | 0.09632 | 0.02064 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.wh-question] | 0.07858 | 0.02723 | 0.004 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.05078 | 0.02914 | 0.081 |

Question-type counts:

| age_bin | context_question_type | rows |
| --- | --- | --- |
| 006-023 | empty/no context | 3 |
| 006-023 | not question | 1475 |
| 006-023 | other question | 1285 |
| 006-023 | wh-question | 247 |
| 006-023 | yes/no question | 305 |
| 024-029 | empty/no context | 6 |
| 024-029 | not question | 1833 |
| 024-029 | other question | 1697 |
| 024-029 | wh-question | 291 |
| 024-029 | yes/no question | 433 |
| 030-035 | empty/no context | 29 |
| 030-035 | not question | 1851 |
| 030-035 | other question | 1576 |
| 030-035 | wh-question | 233 |
| 030-035 | yes/no question | 321 |
| 036-041 | empty/no context | 4 |
| 036-041 | not question | 803 |
| 036-041 | other question | 574 |
| 036-041 | wh-question | 91 |
| 036-041 | yes/no question | 88 |
| 042-047 | empty/no context | 7 |
| 042-047 | not question | 493 |
| 042-047 | other question | 336 |
| 042-047 | wh-question | 92 |
| 042-047 | yes/no question | 47 |
| 048-053 | empty/no context | 14 |
| 048-053 | not question | 306 |
| 048-053 | other question | 239 |
| 048-053 | wh-question | 58 |
| 048-053 | yes/no question | 23 |
| 054-059 | empty/no context | 17 |
| 054-059 | not question | 176 |
| 054-059 | other question | 122 |
| 054-059 | wh-question | 42 |
| 054-059 | yes/no question | 33 |
| 060-065 | empty/no context | 12 |
| 060-065 | not question | 168 |
| 060-065 | other question | 149 |
| 060-065 | wh-question | 41 |
| 060-065 | yes/no question | 20 |

## Expanded Model Cards

These are broader models that test nonlinear age, context-window sensitivity,
phonological efficiency, baseline differences, child/caretaker contrasts, and
context-predictability logic. They are for triage, not final reporting.

## Z1: Information With Child Identity

**Question family.** Does total utterance information change with age after child identity and one effort measure are controlled?

**Why it is in the expanded atlas.** This is a sibling of M2 but kept in the expanded report because it repeats the child-identity analysis across every effort measure.

**How to read this plot.** The line is a visual age regression for real child total bits; dots are age-bin means. The fitted model also controls word count and child identity.

![Z1 plot](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z1_information_child_fe_age.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 0 estimates are positive and 5 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 | effort: Words | ols_cluster | fit | 5560 | 21 | 0.5714 |
| Z1 | effort: Morphemes | ols_cluster | fit | 5560 | 21 | 0.5501 |
| Z1 | effort: Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.6253 |
| Z1 | effort: Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.5975 |
| Z1 | effort: Phonemes | ols_cluster | fit | 5560 | 21 | 0.6147 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Words | age_months_z | -1.559 | 0.5609 | 0.005 |
| Z1 Information | child FE | effort=Words | nb_words_z | 17.08 | 0.5952 | <.001 |
| Z1 Information | child FE | effort=Morphemes | age_months_z | -1.687 | 0.6765 | 0.013 |
| Z1 Information | child FE | effort=Morphemes | nb_morphemes_z | 16.81 | 0.5931 | <.001 |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | age_months_z | -1.246 | 0.4876 | 0.011 |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 17.89 | 0.4905 | <.001 |
| Z1 Information | child FE | effort=Syllables: pkg | age_months_z | -1.038 | 0.5447 | 0.057 |
| Z1 Information | child FE | effort=Syllables: pkg | nb_syllables_pkg_z | 17.36 | 0.5552 | <.001 |
| Z1 Information | child FE | effort=Phonemes | age_months_z | -1.223 | 0.4781 | 0.011 |
| Z1 Information | child FE | effort=Phonemes | nb_phonemes_z | 17.7 | 0.4931 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z1 coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z1_family_coefficients.png)


### Z1.1: effort: Words

**Question asked by this subvariant.** At the same words level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_words_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Words | ols_cluster | fit | 5560 | 21 | 0.5714 | At the same words level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Words | age_months_z | -1.559 | 0.5609 | 0.005 |
| Z1 Information | child FE | effort=Words | nb_words_z | 17.08 | 0.5952 | <.001 |
### Z1.2: effort: Morphemes

**Question asked by this subvariant.** At the same morphemes level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_morphemes_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Morphemes | ols_cluster | fit | 5560 | 21 | 0.5501 | At the same morphemes level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Morphemes | age_months_z | -1.687 | 0.6765 | 0.013 |
| Z1 Information | child FE | effort=Morphemes | nb_morphemes_z | 16.81 | 0.5931 | <.001 |
### Z1.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** At the same syllables: cmu/pkg level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_syllables_cmu_or_pkg_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.6253 | At the same syllables: cmu/pkg level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | age_months_z | -1.246 | 0.4876 | 0.011 |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 17.89 | 0.4905 | <.001 |
### Z1.4: effort: Syllables: pkg

**Question asked by this subvariant.** At the same syllables: pkg level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_syllables_pkg_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.5975 | At the same syllables: pkg level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Syllables: pkg | age_months_z | -1.038 | 0.5447 | 0.057 |
| Z1 Information | child FE | effort=Syllables: pkg | nb_syllables_pkg_z | 17.36 | 0.5552 | <.001 |
### Z1.5: effort: Phonemes

**Question asked by this subvariant.** At the same phonemes level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_phonemes_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Phonemes | ols_cluster | fit | 5560 | 21 | 0.6147 | At the same phonemes level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Phonemes | age_months_z | -1.223 | 0.4781 | 0.011 |
| Z1 Information | child FE | effort=Phonemes | nb_phonemes_z | 17.7 | 0.4931 | <.001 |


## Z2: Nonlinear Information Density

**Question family.** Does information per unit of effort follow a curved developmental trajectory?

**Why it is in the expanded atlas.** M1-M4 use simple linear age terms; this asks whether a curved developmental trajectory is needed.

**How to read this plot.** The curve is a quadratic regression of bits per word over age. A curve rather than a straight line suggests nonlinear development.

![Z2 plot](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z2_nonlinear_information_density.png)

**Compact result.** 5/5 subvariants fit cleanly. For `I(age_months_z ** 2)`, 2 estimates are positive and 3 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 | unit: Words | ols_cluster | fit | 5560 | 21 | 0.3771 |
| Z2 | unit: Morphemes | ols_cluster | fit | 5560 | 21 | 0.4343 |
| Z2 | unit: Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.4981 |
| Z2 | unit: Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.4414 |
| Z2 | unit: Phonemes | ols_cluster | fit | 5560 | 21 | 0.5489 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Words | age_months_z | -0.3338 | 0.2225 | 0.134 |
| Z2 Information density | nonlinear age | unit=Words | I(age_months_z ** 2) | 0.07854 | 0.08214 | 0.339 |
| Z2 Information density | nonlinear age | unit=Words | log_nb_words | -7.421 | 0.3297 | <.001 |
| Z2 Information density | nonlinear age | unit=Morphemes | age_months_z | -0.2145 | 0.2067 | 0.299 |
| Z2 Information density | nonlinear age | unit=Morphemes | I(age_months_z ** 2) | 0.04072 | 0.07323 | 0.578 |
| Z2 Information density | nonlinear age | unit=Morphemes | log_nb_morphemes | -7.614 | 0.2994 | <.001 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | age_months_z | 0.05576 | 0.1719 | 0.746 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | I(age_months_z ** 2) | -0.04936 | 0.06482 | 0.446 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | log_nb_syllables | -6.39 | 0.2405 | <.001 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | age_months_z | 0.08572 | 0.1966 | 0.663 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | I(age_months_z ** 2) | -0.06342 | 0.07411 | 0.392 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | log_nb_syllables | -6.175 | 0.2323 | <.001 |
| Z2 Information density | nonlinear age | unit=Phonemes | age_months_z | 0.3395 | 0.06051 | <.001 |
| Z2 Information density | nonlinear age | unit=Phonemes | I(age_months_z ** 2) | -0.1004 | 0.0201 | <.001 |
| Z2 Information density | nonlinear age | unit=Phonemes | log_nb_phonemes | -3.48 | 0.1715 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z2 coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z2_family_coefficients.png)


### Z2.1: unit: Words

**Question asked by this subvariant.** Does information per words follow a nonlinear developmental trajectory?

**Formula.** `bits_per_word ~ age_months_z + I(age_months_z ** 2) + log_nb_words + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Words | ols_cluster | fit | 5560 | 21 | 0.3771 | Does information per words follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Words | age_months_z | -0.3338 | 0.2225 | 0.134 |
| Z2 Information density | nonlinear age | unit=Words | I(age_months_z ** 2) | 0.07854 | 0.08214 | 0.339 |
| Z2 Information density | nonlinear age | unit=Words | log_nb_words | -7.421 | 0.3297 | <.001 |
### Z2.2: unit: Morphemes

**Question asked by this subvariant.** Does information per morphemes follow a nonlinear developmental trajectory?

**Formula.** `bits_per_morpheme ~ age_months_z + I(age_months_z ** 2) + log_nb_morphemes + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Morphemes | ols_cluster | fit | 5560 | 21 | 0.4343 | Does information per morphemes follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Morphemes | age_months_z | -0.2145 | 0.2067 | 0.299 |
| Z2 Information density | nonlinear age | unit=Morphemes | I(age_months_z ** 2) | 0.04072 | 0.07323 | 0.578 |
| Z2 Information density | nonlinear age | unit=Morphemes | log_nb_morphemes | -7.614 | 0.2994 | <.001 |
### Z2.3: unit: Syllables: CMU/pkg

**Question asked by this subvariant.** Does information per syllables: cmu/pkg follow a nonlinear developmental trajectory?

**Formula.** `bits_per_syllable_cmu_or_pkg ~ age_months_z + I(age_months_z ** 2) + log_nb_syllables + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.4981 | Does information per syllables: cmu/pkg follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | age_months_z | 0.05576 | 0.1719 | 0.746 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | I(age_months_z ** 2) | -0.04936 | 0.06482 | 0.446 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | log_nb_syllables | -6.39 | 0.2405 | <.001 |
### Z2.4: unit: Syllables: pkg

**Question asked by this subvariant.** Does information per syllables: pkg follow a nonlinear developmental trajectory?

**Formula.** `bits_per_syllable_pkg ~ age_months_z + I(age_months_z ** 2) + log_nb_syllables + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.4414 | Does information per syllables: pkg follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | age_months_z | 0.08572 | 0.1966 | 0.663 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | I(age_months_z ** 2) | -0.06342 | 0.07411 | 0.392 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | log_nb_syllables | -6.175 | 0.2323 | <.001 |
### Z2.5: unit: Phonemes

**Question asked by this subvariant.** Does information per phonemes follow a nonlinear developmental trajectory?

**Formula.** `bits_per_phoneme ~ age_months_z + I(age_months_z ** 2) + log_nb_phonemes + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Phonemes | ols_cluster | fit | 5560 | 21 | 0.5489 | Does information per phonemes follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Phonemes | age_months_z | 0.3395 | 0.06051 | <.001 |
| Z2 Information density | nonlinear age | unit=Phonemes | I(age_months_z ** 2) | -0.1004 | 0.0201 | <.001 |
| Z2 Information density | nonlinear age | unit=Phonemes | log_nb_phonemes | -3.48 | 0.1715 | <.001 |


## Z3: Context Entropy Predicting Effort

**Question family.** Do children produce more effortful utterances after less predictable caretaker contexts?

**Why it is in the expanded atlas.** M4 introduces context entropy; this expanded version adds question type and context length in a GEE effort model.

**How to read this plot.** The regression line shows whether child word count rises or falls as next-token context entropy increases.

_Figure unavailable in this scorer run: Z3 plot._

**Compact result.** No subvariant fit cleanly in the current build. Status counts: `{'empty data': 5}`.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 | effort: Words | gee_poisson | empty data |  |  |  |
| Z3 | effort: Morphemes | gee_poisson | empty data |  |  |  |
| Z3 | effort: Syllables: CMU/pkg | gee_poisson | empty data |  |  |  |
| Z3 | effort: Syllables: pkg | gee_poisson | empty data |  |  |  |
| Z3 | effort: Phonemes | gee_poisson | empty data |  |  |  |

Family key coefficients:

_No rows._



### Z3.1: effort: Words

**Question asked by this subvariant.** Do children produce more words after more uncertain caretaker contexts?

**Formula.** `nb_words ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Words | gee_poisson | empty data |  |  |  | Do children produce more words after more uncertain caretaker contexts? |

Key coefficients:

_No rows._
### Z3.2: effort: Morphemes

**Question asked by this subvariant.** Do children produce more morphemes after more uncertain caretaker contexts?

**Formula.** `nb_morphemes ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Morphemes | gee_poisson | empty data |  |  |  | Do children produce more morphemes after more uncertain caretaker contexts? |

Key coefficients:

_No rows._
### Z3.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts?

**Formula.** `nb_syllables_cmu_or_pkg ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | gee_poisson | empty data |  |  |  | Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts? |

Key coefficients:

_No rows._
### Z3.4: effort: Syllables: pkg

**Question asked by this subvariant.** Do children produce more syllables: pkg after more uncertain caretaker contexts?

**Formula.** `nb_syllables_pkg ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Syllables: pkg | gee_poisson | empty data |  |  |  | Do children produce more syllables: pkg after more uncertain caretaker contexts? |

Key coefficients:

_No rows._
### Z3.5: effort: Phonemes

**Question asked by this subvariant.** Do children produce more phonemes after more uncertain caretaker contexts?

**Formula.** `nb_phonemes ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Phonemes | gee_poisson | empty data |  |  |  | Do children produce more phonemes after more uncertain caretaker contexts? |

Key coefficients:

_No rows._


## Z4: Context Entropy Predicting Information

**Question family.** Does contextual uncertainty predict the information carried by an utterance after effort is controlled?

**Why it is in the expanded atlas.** This tests context entropy as a direct predictor of total utterance information while controlling one effort measure at a time.

**How to read this plot.** The regression line is a descriptive view of total bits across contexts with lower versus higher next-token entropy. The fitted subvariants below add explicit effort controls.

_Figure unavailable in this scorer run: Z4 plot._

**Compact result.** No subvariant fit cleanly in the current build. Status counts: `{'empty data': 5}`.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 | effort: Words | gee_gamma_log | empty data |  |  |  |
| Z4 | effort: Morphemes | gee_gamma_log | empty data |  |  |  |
| Z4 | effort: Syllables: CMU/pkg | gee_gamma_log | empty data |  |  |  |
| Z4 | effort: Syllables: pkg | gee_gamma_log | empty data |  |  |  |
| Z4 | effort: Phonemes | gee_gamma_log | empty data |  |  |  |

Family key coefficients:

_No rows._



### Z4.1: effort: Words

**Question asked by this subvariant.** Is total child information related to context entropy after words is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_words_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Words | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after words is controlled? |

Key coefficients:

_No rows._
### Z4.2: effort: Morphemes

**Question asked by this subvariant.** Is total child information related to context entropy after morphemes is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_morphemes_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Morphemes | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after morphemes is controlled? |

Key coefficients:

_No rows._
### Z4.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Is total child information related to context entropy after syllables: cmu/pkg is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_syllables_cmu_or_pkg_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after syllables: cmu/pkg is controlled? |

Key coefficients:

_No rows._
### Z4.4: effort: Syllables: pkg

**Question asked by this subvariant.** Is total child information related to context entropy after syllables: pkg is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_syllables_pkg_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Syllables: pkg | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after syllables: pkg is controlled? |

Key coefficients:

_No rows._
### Z4.5: effort: Phonemes

**Question asked by this subvariant.** Is total child information related to context entropy after phonemes is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_phonemes_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Phonemes | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after phonemes is controlled? |

Key coefficients:

_No rows._


## Z5: Scoring Context Window Sensitivity

**Question family.** Do conclusions change when surprisal is scored with k1, k2, or k3 caretaker context windows?

**Why it is in the expanded atlas.** M1-M4 use k3 as the main condition; this asks whether the age trajectory changes under k1, k2, or k3 scoring.

**How to read this plot.** Lines compare bits per word by age under k1, k2, and k3 scoring. Separation means the amount of context used for scoring matters.

![Z5 plot](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z5_context_window_sensitivity.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 1 estimates are positive and 4 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 | unit: Words | gee_gaussian | fit | 1.554e+04 | 21 | 0.3709 |
| Z5 | unit: Morphemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.4357 |
| Z5 | unit: Syllables: CMU/pkg | gee_gaussian | fit | 1.554e+04 | 21 | 0.4784 |
| Z5 | unit: Syllables: pkg | gee_gaussian | fit | 1.554e+04 | 21 | 0.4246 |
| Z5 | unit: Phonemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.5317 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Words | C(context_k)[T.k2] | 0.02366 | 0.1087 | 0.828 |
| Z5 Context window sensitivity | unit=Words | C(context_k)[T.k3] | -0.06355 | 0.08509 | 0.455 |
| Z5 Context window sensitivity | unit=Words | age_months_z | -0.5332 | 0.1481 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k2] | 0.01662 | 0.0772 | 0.830 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k3] | 0.09349 | 0.05632 | 0.097 |
| Z5 Context window sensitivity | unit=Words | log_nb_words | -7.016 | 0.3224 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | C(context_k)[T.k2] | 0.07358 | 0.1101 | 0.504 |
| Z5 Context window sensitivity | unit=Morphemes | C(context_k)[T.k3] | 0.006628 | 0.09078 | 0.942 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z | -0.4767 | 0.128 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k2] | 0.01553 | 0.07765 | 0.841 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k3] | 0.09443 | 0.05444 | 0.083 |
| Z5 Context window sensitivity | unit=Morphemes | log_nb_morphemes | -7.185 | 0.2848 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | C(context_k)[T.k2] | 0.03254 | 0.06628 | 0.624 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | C(context_k)[T.k3] | -0.02633 | 0.05417 | 0.627 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z | -0.2511 | 0.07393 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k2] | 0.04583 | 0.0416 | 0.271 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k3] | 0.1059 | 0.03819 | 0.006 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | log_nb_syllables | -6.138 | 0.2598 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | C(context_k)[T.k2] | 0.0498 | 0.06786 | 0.463 |
| Z5 Context window sensitivity | unit=Syllables: pkg | C(context_k)[T.k3] | 0.04908 | 0.06611 | 0.458 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z | -0.1877 | 0.09432 | 0.047 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k2] | -0.008937 | 0.04689 | 0.849 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k3] | 0.09467 | 0.05597 | 0.091 |
| Z5 Context window sensitivity | unit=Syllables: pkg | log_nb_syllables | -5.923 | 0.2523 | <.001 |
| Z5 Context window sensitivity | unit=Phonemes | C(context_k)[T.k2] | 0.03553 | 0.03871 | 0.359 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z5 coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z5_family_coefficients.png)


### Z5.1: unit: Words

**Question asked by this subvariant.** Does the age trajectory of information per words change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_word ~ age_months_z * C(context_k) + log_nb_words`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Words | gee_gaussian | fit | 1.554e+04 | 21 | 0.3709 | Does the age trajectory of information per words change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Words | C(context_k)[T.k2] | 0.02366 | 0.1087 | 0.828 |
| Z5 Context window sensitivity | unit=Words | C(context_k)[T.k3] | -0.06355 | 0.08509 | 0.455 |
| Z5 Context window sensitivity | unit=Words | age_months_z | -0.5332 | 0.1481 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k2] | 0.01662 | 0.0772 | 0.830 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k3] | 0.09349 | 0.05632 | 0.097 |
| Z5 Context window sensitivity | unit=Words | log_nb_words | -7.016 | 0.3224 | <.001 |
### Z5.2: unit: Morphemes

**Question asked by this subvariant.** Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_morpheme ~ age_months_z * C(context_k) + log_nb_morphemes`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Morphemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.4357 | Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Morphemes | C(context_k)[T.k2] | 0.07358 | 0.1101 | 0.504 |
| Z5 Context window sensitivity | unit=Morphemes | C(context_k)[T.k3] | 0.006628 | 0.09078 | 0.942 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z | -0.4767 | 0.128 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k2] | 0.01553 | 0.07765 | 0.841 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k3] | 0.09443 | 0.05444 | 0.083 |
| Z5 Context window sensitivity | unit=Morphemes | log_nb_morphemes | -7.185 | 0.2848 | <.001 |
### Z5.3: unit: Syllables: CMU/pkg

**Question asked by this subvariant.** Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_syllable_cmu_or_pkg ~ age_months_z * C(context_k) + log_nb_syllables`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | gee_gaussian | fit | 1.554e+04 | 21 | 0.4784 | Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | C(context_k)[T.k2] | 0.03254 | 0.06628 | 0.624 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | C(context_k)[T.k3] | -0.02633 | 0.05417 | 0.627 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z | -0.2511 | 0.07393 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k2] | 0.04583 | 0.0416 | 0.271 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k3] | 0.1059 | 0.03819 | 0.006 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | log_nb_syllables | -6.138 | 0.2598 | <.001 |
### Z5.4: unit: Syllables: pkg

**Question asked by this subvariant.** Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_syllable_pkg ~ age_months_z * C(context_k) + log_nb_syllables`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Syllables: pkg | gee_gaussian | fit | 1.554e+04 | 21 | 0.4246 | Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Syllables: pkg | C(context_k)[T.k2] | 0.0498 | 0.06786 | 0.463 |
| Z5 Context window sensitivity | unit=Syllables: pkg | C(context_k)[T.k3] | 0.04908 | 0.06611 | 0.458 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z | -0.1877 | 0.09432 | 0.047 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k2] | -0.008937 | 0.04689 | 0.849 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k3] | 0.09467 | 0.05597 | 0.091 |
| Z5 Context window sensitivity | unit=Syllables: pkg | log_nb_syllables | -5.923 | 0.2523 | <.001 |
### Z5.5: unit: Phonemes

**Question asked by this subvariant.** Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_phoneme ~ age_months_z * C(context_k) + log_nb_phonemes`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Phonemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.5317 | Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Phonemes | C(context_k)[T.k2] | 0.03553 | 0.03871 | 0.359 |
| Z5 Context window sensitivity | unit=Phonemes | C(context_k)[T.k3] | 0.03048 | 0.03389 | 0.368 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z | 0.1306 | 0.06134 | 0.033 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k2] | 0.04539 | 0.03126 | 0.146 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k3] | 0.06966 | 0.02648 | 0.009 |
| Z5 Context window sensitivity | unit=Phonemes | log_nb_phonemes | -3.454 | 0.1858 | <.001 |


## Z6: Question Type Predicting Effort

**Question family.** Does the type of preceding caretaker question predict how much effort the child produces?

**Why it is in the expanded atlas.** This adds a conversational-control variable: whether the preceding caretaker context is a wh-question, yes/no question, other question, or not a question.

**How to read this plot.** Lines compare mean child word count by age after different broad caretaker context types.

![Z6 plot](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z6_question_type_effort.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 5 estimates are positive and 0 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 | effort: Words | gee_poisson | fit | 1.554e+04 | 21 | 0.1003 |
| Z6 | effort: Morphemes | gee_poisson | fit | 1.554e+04 | 21 | 0.09977 |
| Z6 | effort: Syllables: CMU/pkg | gee_poisson | fit | 1.554e+04 | 21 | 0.08597 |
| Z6 | effort: Syllables: pkg | gee_poisson | fit | 1.554e+04 | 21 | 0.07985 |
| Z6 | effort: Phonemes | gee_poisson | fit | 1.554e+04 | 21 | 0.08059 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.not question] | -0.00196 | 0.05469 | 0.971 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.other question] | -0.1108 | 0.05943 | 0.062 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.wh-question] | -0.06508 | 0.0656 | 0.321 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.yes/no question] | -0.1389 | 0.06058 | 0.022 |
| Z6 Question-type effort | effort=Words | age_months_z | 0.1662 | 0.02665 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.not question] | 0.04538 | 0.01797 | 0.012 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.other question] | 0.08947 | 0.01921 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.wh-question] | 0.07435 | 0.0225 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.yes/no question] | 0.04097 | 0.02741 | 0.135 |
| Z6 Question-type effort | effort=Words | log_context_words_plus1 | 0.01597 | 0.009242 | 0.084 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.not question] | 0.0115 | 0.06002 | 0.848 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.other question] | -0.09212 | 0.06241 | 0.140 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.wh-question] | -0.03699 | 0.0731 | 0.613 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.yes/no question] | -0.1254 | 0.06443 | 0.052 |
| Z6 Question-type effort | effort=Morphemes | age_months_z | 0.1743 | 0.02871 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.not question] | 0.04737 | 0.02012 | 0.019 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.other question] | 0.09663 | 0.02071 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.wh-question] | 0.07984 | 0.02642 | 0.003 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.05767 | 0.02886 | 0.046 |
| Z6 Question-type effort | effort=Morphemes | log_context_words_plus1 | 0.01101 | 0.009392 | 0.241 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.not question] | -0.003837 | 0.06095 | 0.950 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.other question] | -0.1048 | 0.06603 | 0.112 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.wh-question] | -0.06285 | 0.07262 | 0.387 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.yes/no question] | -0.1461 | 0.06711 | 0.029 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z | 0.1326 | 0.0238 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z6 coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z6_family_coefficients.png)


### Z6.1: effort: Words

**Question asked by this subvariant.** Does caretaker question type modulate child words, and does that modulation change with age?

**Formula.** `nb_words ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Words | gee_poisson | fit | 1.554e+04 | 21 | 0.1003 | Does caretaker question type modulate child words, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.not question] | -0.00196 | 0.05469 | 0.971 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.other question] | -0.1108 | 0.05943 | 0.062 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.wh-question] | -0.06508 | 0.0656 | 0.321 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.yes/no question] | -0.1389 | 0.06058 | 0.022 |
| Z6 Question-type effort | effort=Words | age_months_z | 0.1662 | 0.02665 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.not question] | 0.04538 | 0.01797 | 0.012 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.other question] | 0.08947 | 0.01921 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.wh-question] | 0.07435 | 0.0225 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.yes/no question] | 0.04097 | 0.02741 | 0.135 |
| Z6 Question-type effort | effort=Words | log_context_words_plus1 | 0.01597 | 0.009242 | 0.084 |
### Z6.2: effort: Morphemes

**Question asked by this subvariant.** Does caretaker question type modulate child morphemes, and does that modulation change with age?

**Formula.** `nb_morphemes ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Morphemes | gee_poisson | fit | 1.554e+04 | 21 | 0.09977 | Does caretaker question type modulate child morphemes, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.not question] | 0.0115 | 0.06002 | 0.848 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.other question] | -0.09212 | 0.06241 | 0.140 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.wh-question] | -0.03699 | 0.0731 | 0.613 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.yes/no question] | -0.1254 | 0.06443 | 0.052 |
| Z6 Question-type effort | effort=Morphemes | age_months_z | 0.1743 | 0.02871 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.not question] | 0.04737 | 0.02012 | 0.019 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.other question] | 0.09663 | 0.02071 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.wh-question] | 0.07984 | 0.02642 | 0.003 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.05767 | 0.02886 | 0.046 |
| Z6 Question-type effort | effort=Morphemes | log_context_words_plus1 | 0.01101 | 0.009392 | 0.241 |
### Z6.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Does caretaker question type modulate child syllables: cmu/pkg, and does that modulation change with age?

**Formula.** `nb_syllables_cmu_or_pkg ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | gee_poisson | fit | 1.554e+04 | 21 | 0.08597 | Does caretaker question type modulate child syllables: cmu/pkg, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.not question] | -0.003837 | 0.06095 | 0.950 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.other question] | -0.1048 | 0.06603 | 0.112 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.wh-question] | -0.06285 | 0.07262 | 0.387 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.yes/no question] | -0.1461 | 0.06711 | 0.029 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z | 0.1326 | 0.0238 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.not question] | 0.06296 | 0.01621 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.other question] | 0.1028 | 0.01965 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.09024 | 0.02861 | 0.002 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.05351 | 0.03197 | 0.094 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | log_context_words_plus1 | 0.008226 | 0.008566 | 0.337 |
### Z6.4: effort: Syllables: pkg

**Question asked by this subvariant.** Does caretaker question type modulate child syllables: pkg, and does that modulation change with age?

**Formula.** `nb_syllables_pkg ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Syllables: pkg | gee_poisson | fit | 1.554e+04 | 21 | 0.07985 | Does caretaker question type modulate child syllables: pkg, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Syllables: pkg | C(context_question_type)[T.not question] | -0.00649 | 0.05785 | 0.911 |
| Z6 Question-type effort | effort=Syllables: pkg | C(context_question_type)[T.other question] | -0.113 | 0.06537 | 0.084 |
| Z6 Question-type effort | effort=Syllables: pkg | C(context_question_type)[T.wh-question] | -0.07202 | 0.06603 | 0.275 |
| Z6 Question-type effort | effort=Syllables: pkg | C(context_question_type)[T.yes/no question] | -0.1584 | 0.06821 | 0.020 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z | 0.1309 | 0.02231 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.not question] | 0.05947 | 0.01781 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.other question] | 0.1055 | 0.01982 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.08825 | 0.03135 | 0.005 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.05722 | 0.03049 | 0.060 |
| Z6 Question-type effort | effort=Syllables: pkg | log_context_words_plus1 | 0.009573 | 0.009141 | 0.295 |
### Z6.5: effort: Phonemes

**Question asked by this subvariant.** Does caretaker question type modulate child phonemes, and does that modulation change with age?

**Formula.** `nb_phonemes ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Phonemes | gee_poisson | fit | 1.554e+04 | 21 | 0.08059 | Does caretaker question type modulate child phonemes, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Phonemes | C(context_question_type)[T.not question] | 0.03553 | 0.05933 | 0.549 |
| Z6 Question-type effort | effort=Phonemes | C(context_question_type)[T.other question] | -0.06159 | 0.06514 | 0.344 |
| Z6 Question-type effort | effort=Phonemes | C(context_question_type)[T.wh-question] | -0.0138 | 0.06894 | 0.841 |
| Z6 Question-type effort | effort=Phonemes | C(context_question_type)[T.yes/no question] | -0.117 | 0.06627 | 0.077 |
| Z6 Question-type effort | effort=Phonemes | age_months_z | 0.1447 | 0.02387 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.not question] | 0.05202 | 0.01743 | 0.003 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.other question] | 0.09632 | 0.02064 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.wh-question] | 0.07858 | 0.02723 | 0.004 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.05078 | 0.02914 | 0.081 |
| Z6 Question-type effort | effort=Phonemes | log_context_words_plus1 | 0.001832 | 0.008365 | 0.827 |


## Z7: Real Children Versus All Matched Baselines

**Question family.** Do real children differ from generated baselines after one effort measure is controlled?

**Why it is in the expanded atlas.** M1-M4 only analyze real child utterances; this model asks whether real children differ from random and n-gram baselines after controlling effort. Effort controls are kept separate.

**How to read this plot.** Lines compare real children and generated baselines over age. The plot is descriptive; the Z7 model table below is the effort-controlled comparison.

![Z7 plot](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z7_baseline_comparison.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 3 estimates are positive and 2 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 | effort: Words | gee_gamma_log | fit | 1.822e+04 | 21 | 0.06457 |
| Z7 | effort: Morphemes | gee_gamma_log | fit | 1.822e+04 | 21 | 0.05524 |
| Z7 | effort: Syllables: CMU/pkg | gee_gamma_log | fit | 1.822e+04 | 21 | 0.04919 |
| Z7 | effort: Syllables: pkg | gee_gamma_log | fit | 1.822e+04 | 21 | 0.0508 |
| Z7 | effort: Phonemes | gee_gamma_log | fit | 1.822e+04 | 21 | 0.04584 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.random] | 0.5207 | 0.007824 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.real] | -0.1458 | 0.01066 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.trigram] | -0.02854 | 0.006141 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.unigram] | 0.06534 | 0.0062 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z | -0.01157 | 0.006551 | 0.077 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.random] | 0.09264 | 0.01144 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.real] | -0.0225 | 0.00967 | 0.020 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.trigram] | 0.0009037 | 0.006511 | 0.890 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.unigram] | 0.005271 | 0.007331 | 0.472 |
| Z7 Baseline comparison | effort=Words | nb_words_z | 0.5118 | 0.01427 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.random] | 0.4274 | 0.005753 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.real] | -0.1479 | 0.0126 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.trigram] | -0.02843 | 0.006791 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.unigram] | 0.06253 | 0.006589 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z | -0.001994 | 0.007827 | 0.799 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.random] | 0.06113 | 0.008959 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.real] | -0.02564 | 0.01234 | 0.038 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.trigram] | -0.001882 | 0.006334 | 0.766 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.unigram] | 0.004854 | 0.005719 | 0.396 |
| Z7 Baseline comparison | effort=Morphemes | nb_morphemes_z | 0.5008 | 0.01353 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.random] | 0.25 | 0.007439 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.real] | -0.1564 | 0.01219 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.trigram] | -0.03687 | 0.005426 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.unigram] | 0.06164 | 0.006035 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z | 0.02355 | 0.008887 | 0.008 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z7 coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z7_family_coefficients.png)


### Z7.1: effort: Words

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling words?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_words_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Words | gee_gamma_log | fit | 1.822e+04 | 21 | 0.06457 | Do real child utterances differ from random/ngram baselines after controlling words? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.random] | 0.5207 | 0.007824 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.real] | -0.1458 | 0.01066 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.trigram] | -0.02854 | 0.006141 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.unigram] | 0.06534 | 0.0062 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z | -0.01157 | 0.006551 | 0.077 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.random] | 0.09264 | 0.01144 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.real] | -0.0225 | 0.00967 | 0.020 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.trigram] | 0.0009037 | 0.006511 | 0.890 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.unigram] | 0.005271 | 0.007331 | 0.472 |
| Z7 Baseline comparison | effort=Words | nb_words_z | 0.5118 | 0.01427 | <.001 |
### Z7.2: effort: Morphemes

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling morphemes?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_morphemes_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Morphemes | gee_gamma_log | fit | 1.822e+04 | 21 | 0.05524 | Do real child utterances differ from random/ngram baselines after controlling morphemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.random] | 0.4274 | 0.005753 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.real] | -0.1479 | 0.0126 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.trigram] | -0.02843 | 0.006791 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.unigram] | 0.06253 | 0.006589 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z | -0.001994 | 0.007827 | 0.799 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.random] | 0.06113 | 0.008959 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.real] | -0.02564 | 0.01234 | 0.038 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.trigram] | -0.001882 | 0.006334 | 0.766 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.unigram] | 0.004854 | 0.005719 | 0.396 |
| Z7 Baseline comparison | effort=Morphemes | nb_morphemes_z | 0.5008 | 0.01353 | <.001 |
### Z7.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling syllables: cmu/pkg?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_syllables_cmu_or_pkg_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 1.822e+04 | 21 | 0.04919 | Do real child utterances differ from random/ngram baselines after controlling syllables: cmu/pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.random] | 0.25 | 0.007439 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.real] | -0.1564 | 0.01219 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.trigram] | -0.03687 | 0.005426 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.unigram] | 0.06164 | 0.006035 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z | 0.02355 | 0.008887 | 0.008 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.random] | -0.005045 | 0.01162 | 0.664 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.real] | -0.03037 | 0.01273 | 0.017 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.trigram] | -0.003304 | 0.009711 | 0.734 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.unigram] | 0.004881 | 0.006263 | 0.436 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.5295 | 0.01396 | <.001 |
### Z7.4: effort: Syllables: pkg

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling syllables: pkg?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_syllables_pkg_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Syllables: pkg | gee_gamma_log | fit | 1.822e+04 | 21 | 0.0508 | Do real child utterances differ from random/ngram baselines after controlling syllables: pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.random] | 0.2713 | 0.007433 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.real] | -0.1569 | 0.01239 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.trigram] | -0.03703 | 0.00622 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.unigram] | 0.06285 | 0.005963 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z | 0.02377 | 0.00864 | 0.006 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.random] | 0.001796 | 0.011 | 0.870 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.real] | -0.02916 | 0.01186 | 0.014 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.trigram] | -0.005993 | 0.007863 | 0.446 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.unigram] | 0.006736 | 0.006775 | 0.320 |
| Z7 Baseline comparison | effort=Syllables: pkg | nb_syllables_pkg_z | 0.5201 | 0.01313 | <.001 |
### Z7.5: effort: Phonemes

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling phonemes?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_phonemes_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Phonemes | gee_gamma_log | fit | 1.822e+04 | 21 | 0.04584 | Do real child utterances differ from random/ngram baselines after controlling phonemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.random] | 0.1996 | 0.008109 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.real] | -0.1609 | 0.01368 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.trigram] | -0.0341 | 0.004978 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.unigram] | 0.06057 | 0.006053 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z | 0.02338 | 0.009172 | 0.011 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.random] | -0.01463 | 0.01 | 0.144 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.real] | -0.02391 | 0.01316 | 0.069 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.trigram] | 0.00222 | 0.006725 | 0.741 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.unigram] | 0.005785 | 0.00695 | 0.405 |
| Z7 Baseline comparison | effort=Phonemes | nb_phonemes_z | 0.5329 | 0.01366 | <.001 |


## Z8: Children Versus Caretakers

**Question family.** Do children and caretakers show different age-linked information trajectories after effort is controlled?

**Why it is in the expanded atlas.** M1-M4 are child-only; this compares child and caretaker trajectories over child age.

**How to read this plot.** Lines compare child and caretaker bits per word. This is not row-matched, so read it as a speaker-group trajectory contrast.

![Z8 plot](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z8_child_caretaker_density.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 0 estimates are positive and 5 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 | effort: Words | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2249 |
| Z8 | effort: Morphemes | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2677 |
| Z8 | effort: Syllables: CMU/pkg | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2018 |
| Z8 | effort: Syllables: pkg | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2295 |
| Z8 | effort: Phonemes | gee_gamma_log | fit | 1.008e+04 | 21 | 0.1667 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Words | C(speaker_group)[T.child] | -0.2244 | 0.02004 | <.001 |
| Z8 Child vs caretaker information | effort=Words | age_months_z | -0.002654 | 0.009121 | 0.771 |
| Z8 Child vs caretaker information | effort=Words | age_months_z:C(speaker_group)[T.child] | -0.03271 | 0.01172 | 0.005 |
| Z8 Child vs caretaker information | effort=Words | nb_words_z | 0.4257 | 0.01071 | <.001 |
| Z8 Child vs caretaker information | effort=Morphemes | C(speaker_group)[T.child] | -0.2226 | 0.02119 | <.001 |
| Z8 Child vs caretaker information | effort=Morphemes | age_months_z | -0.0006609 | 0.01006 | 0.948 |
| Z8 Child vs caretaker information | effort=Morphemes | age_months_z:C(speaker_group)[T.child] | -0.03875 | 0.01294 | 0.003 |
| Z8 Child vs caretaker information | effort=Morphemes | nb_morphemes_z | 0.4214 | 0.01147 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | C(speaker_group)[T.child] | -0.2264 | 0.01765 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | age_months_z | -0.000575 | 0.007658 | 0.940 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | age_months_z:C(speaker_group)[T.child] | -0.02956 | 0.01113 | 0.008 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.451 | 0.01343 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | C(speaker_group)[T.child] | -0.2264 | 0.01759 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | age_months_z | -0.0005973 | 0.008215 | 0.942 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | age_months_z:C(speaker_group)[T.child] | -0.02551 | 0.0115 | 0.027 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | nb_syllables_pkg_z | 0.442 | 0.01364 | <.001 |
| Z8 Child vs caretaker information | effort=Phonemes | C(speaker_group)[T.child] | -0.2247 | 0.01864 | <.001 |
| Z8 Child vs caretaker information | effort=Phonemes | age_months_z | -0.002917 | 0.007963 | 0.714 |
| Z8 Child vs caretaker information | effort=Phonemes | age_months_z:C(speaker_group)[T.child] | -0.02458 | 0.01107 | 0.026 |
| Z8 Child vs caretaker information | effort=Phonemes | nb_phonemes_z | 0.4479 | 0.01399 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z8 coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z8_family_coefficients.png)


### Z8.1: effort: Words

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling words?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_words_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Words | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2249 | Do child and caretaker total-bit trajectories differ after controlling words? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Words | C(speaker_group)[T.child] | -0.2244 | 0.02004 | <.001 |
| Z8 Child vs caretaker information | effort=Words | age_months_z | -0.002654 | 0.009121 | 0.771 |
| Z8 Child vs caretaker information | effort=Words | age_months_z:C(speaker_group)[T.child] | -0.03271 | 0.01172 | 0.005 |
| Z8 Child vs caretaker information | effort=Words | nb_words_z | 0.4257 | 0.01071 | <.001 |
### Z8.2: effort: Morphemes

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling morphemes?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_morphemes_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Morphemes | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2677 | Do child and caretaker total-bit trajectories differ after controlling morphemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Morphemes | C(speaker_group)[T.child] | -0.2226 | 0.02119 | <.001 |
| Z8 Child vs caretaker information | effort=Morphemes | age_months_z | -0.0006609 | 0.01006 | 0.948 |
| Z8 Child vs caretaker information | effort=Morphemes | age_months_z:C(speaker_group)[T.child] | -0.03875 | 0.01294 | 0.003 |
| Z8 Child vs caretaker information | effort=Morphemes | nb_morphemes_z | 0.4214 | 0.01147 | <.001 |
### Z8.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_syllables_cmu_or_pkg_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2018 | Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | C(speaker_group)[T.child] | -0.2264 | 0.01765 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | age_months_z | -0.000575 | 0.007658 | 0.940 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | age_months_z:C(speaker_group)[T.child] | -0.02956 | 0.01113 | 0.008 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.451 | 0.01343 | <.001 |
### Z8.4: effort: Syllables: pkg

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling syllables: pkg?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_syllables_pkg_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Syllables: pkg | gee_gamma_log | fit | 1.008e+04 | 21 | 0.2295 | Do child and caretaker total-bit trajectories differ after controlling syllables: pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Syllables: pkg | C(speaker_group)[T.child] | -0.2264 | 0.01759 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | age_months_z | -0.0005973 | 0.008215 | 0.942 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | age_months_z:C(speaker_group)[T.child] | -0.02551 | 0.0115 | 0.027 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | nb_syllables_pkg_z | 0.442 | 0.01364 | <.001 |
### Z8.5: effort: Phonemes

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling phonemes?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_phonemes_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Phonemes | gee_gamma_log | fit | 1.008e+04 | 21 | 0.1667 | Do child and caretaker total-bit trajectories differ after controlling phonemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Phonemes | C(speaker_group)[T.child] | -0.2247 | 0.01864 | <.001 |
| Z8 Child vs caretaker information | effort=Phonemes | age_months_z | -0.002917 | 0.007963 | 0.714 |
| Z8 Child vs caretaker information | effort=Phonemes | age_months_z:C(speaker_group)[T.child] | -0.02458 | 0.01107 | 0.026 |
| Z8 Child vs caretaker information | effort=Phonemes | nb_phonemes_z | 0.4479 | 0.01399 | <.001 |


## Z9: Information Per Effort Unit

**Question family.** Does information per effort unit change with age when the effort unit itself is the outcome denominator?

**Why it is in the expanded atlas.** M1-M4 control effort as a predictor; this complementary family treats information per effort unit as the outcome.

**How to read this plot.** The regression line shows the phoneme-denominated version of this family. The fitted subvariants below repeat the density model for every effort unit.

![Z9 plot](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z9_phonological_efficiency.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 3 estimates are positive and 2 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 | unit: Words | ols_cluster | fit | 5560 | 21 | 0.377 |
| Z9 | unit: Morphemes | ols_cluster | fit | 5560 | 21 | 0.4342 |
| Z9 | unit: Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.498 |
| Z9 | unit: Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.4413 |
| Z9 | unit: Phonemes | ols_cluster | fit | 5560 | 21 | 0.5476 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Words | age_months_z | -0.247 | 0.1664 | 0.138 |
| Z9 Information per unit | unit=Words | log_nb_words | -7.443 | 0.332 | <.001 |
| Z9 Information per unit | unit=Morphemes | age_months_z | -0.1695 | 0.1681 | 0.313 |
| Z9 Information per unit | unit=Morphemes | log_nb_morphemes | -7.624 | 0.3008 | <.001 |
| Z9 Information per unit | unit=Syllables: CMU/pkg | age_months_z | 0.002281 | 0.137 | 0.987 |
| Z9 Information per unit | unit=Syllables: CMU/pkg | log_nb_syllables | -6.379 | 0.2443 | <.001 |
| Z9 Information per unit | unit=Syllables: pkg | age_months_z | 0.017 | 0.1679 | 0.919 |
| Z9 Information per unit | unit=Syllables: pkg | log_nb_syllables | -6.162 | 0.2363 | <.001 |
| Z9 Information per unit | unit=Phonemes | age_months_z | 0.2315 | 0.08839 | 0.009 |
| Z9 Information per unit | unit=Phonemes | log_nb_phonemes | -3.462 | 0.172 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z9 coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z9_family_coefficients.png)


### Z9.1: unit: Words

**Question asked by this subvariant.** Does information per words change with age after child identity is controlled?

**Formula.** `bits_per_word ~ age_months_z + log_nb_words + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Words | ols_cluster | fit | 5560 | 21 | 0.377 | Does information per words change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Words | age_months_z | -0.247 | 0.1664 | 0.138 |
| Z9 Information per unit | unit=Words | log_nb_words | -7.443 | 0.332 | <.001 |
### Z9.2: unit: Morphemes

**Question asked by this subvariant.** Does information per morphemes change with age after child identity is controlled?

**Formula.** `bits_per_morpheme ~ age_months_z + log_nb_morphemes + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Morphemes | ols_cluster | fit | 5560 | 21 | 0.4342 | Does information per morphemes change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Morphemes | age_months_z | -0.1695 | 0.1681 | 0.313 |
| Z9 Information per unit | unit=Morphemes | log_nb_morphemes | -7.624 | 0.3008 | <.001 |
### Z9.3: unit: Syllables: CMU/pkg

**Question asked by this subvariant.** Does information per syllables: cmu/pkg change with age after child identity is controlled?

**Formula.** `bits_per_syllable_cmu_or_pkg ~ age_months_z + log_nb_syllables + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.498 | Does information per syllables: cmu/pkg change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Syllables: CMU/pkg | age_months_z | 0.002281 | 0.137 | 0.987 |
| Z9 Information per unit | unit=Syllables: CMU/pkg | log_nb_syllables | -6.379 | 0.2443 | <.001 |
### Z9.4: unit: Syllables: pkg

**Question asked by this subvariant.** Does information per syllables: pkg change with age after child identity is controlled?

**Formula.** `bits_per_syllable_pkg ~ age_months_z + log_nb_syllables + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.4413 | Does information per syllables: pkg change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Syllables: pkg | age_months_z | 0.017 | 0.1679 | 0.919 |
| Z9 Information per unit | unit=Syllables: pkg | log_nb_syllables | -6.162 | 0.2363 | <.001 |
### Z9.5: unit: Phonemes

**Question asked by this subvariant.** Does information per phonemes change with age after child identity is controlled?

**Formula.** `bits_per_phoneme ~ age_months_z + log_nb_phonemes + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Phonemes | ols_cluster | fit | 5560 | 21 | 0.5476 | Does information per phonemes change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Phonemes | age_months_z | 0.2315 | 0.08839 | 0.009 |
| Z9 Information per unit | unit=Phonemes | log_nb_phonemes | -3.462 | 0.172 | <.001 |


## Z10: Context Certainty Predicting Effort

**Question family.** Do children produce less effort when the model is more certain about the next token after the context?

**Why it is in the expanded atlas.** This is the inverse of the entropy framing: it uses the probability of the most likely next token as a context-certainty predictor.

**How to read this plot.** The regression line shows whether child word count changes when the model is more certain about the next token.

_Figure unavailable in this scorer run: Z10 plot._

**Compact result.** No subvariant fit cleanly in the current build. Status counts: `{'empty data': 5}`.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 | effort: Words | gee_poisson | empty data |  |  |  |
| Z10 | effort: Morphemes | gee_poisson | empty data |  |  |  |
| Z10 | effort: Syllables: CMU/pkg | gee_poisson | empty data |  |  |  |
| Z10 | effort: Syllables: pkg | gee_poisson | empty data |  |  |  |
| Z10 | effort: Phonemes | gee_poisson | empty data |  |  |  |

Family key coefficients:

_No rows._



### Z10.1: effort: Words

**Question asked by this subvariant.** Is child words lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_words ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Words | gee_poisson | empty data |  |  |  | Is child words lower when the model assigns high probability to the most likely next token? |

Key coefficients:

_No rows._
### Z10.2: effort: Morphemes

**Question asked by this subvariant.** Is child morphemes lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_morphemes ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Morphemes | gee_poisson | empty data |  |  |  | Is child morphemes lower when the model assigns high probability to the most likely next token? |

Key coefficients:

_No rows._
### Z10.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_syllables_cmu_or_pkg ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Syllables: CMU/pkg | gee_poisson | empty data |  |  |  | Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token? |

Key coefficients:

_No rows._
### Z10.4: effort: Syllables: pkg

**Question asked by this subvariant.** Is child syllables: pkg lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_syllables_pkg ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Syllables: pkg | gee_poisson | empty data |  |  |  | Is child syllables: pkg lower when the model assigns high probability to the most likely next token? |

Key coefficients:

_No rows._
### Z10.5: effort: Phonemes

**Question asked by this subvariant.** Is child phonemes lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_phonemes ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Phonemes | gee_poisson | empty data |  |  |  | Is child phonemes lower when the model assigns high probability to the most likely next token? |

Key coefficients:

_No rows._


## Z11: Real Minus Baseline Delta

**Question family.** Does the row-matched real-minus-baseline information gap change with age after effort is controlled?

**Why it is in the expanded atlas.** This is the most direct baseline-difference analysis and is row-matched rather than child-only. Effort controls are fitted one at a time.

**How to read this plot.** Lines below zero mean real child utterances have lower total bits than the baseline; movement over age means the gap changes developmentally.

![Z11 plot](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z11_real_minus_baseline_delta.png)

**Compact result.** 6/6 subvariants fit cleanly. For `age_months_z`, 2 estimates are positive and 4 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 | main specification | ols_cluster | fit | 1.786e+06 | 21 | 0.2807 |
| Z11 | effort: Words | ols_cluster | fit | 1.786e+06 | 21 | 0.4911 |
| Z11 | effort: Morphemes | ols_cluster | fit | 1.786e+06 | 21 | 0.4761 |
| Z11 | effort: Syllables: CMU/pkg | ols_cluster | fit | 1.786e+06 | 21 | 0.4212 |
| Z11 | effort: Syllables: pkg | ols_cluster | fit | 1.786e+06 | 21 | 0.4215 |
| Z11 | effort: Phonemes | ols_cluster | fit | 1.786e+06 | 21 | 0.4203 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z | -5.092 | 0.688 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z | 1.042 | 0.3763 | 0.006 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | nb_words_z | -16.64 | 0.4168 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z | 1.029 | 0.4177 | 0.014 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | nb_morphemes_z | -16.09 | 0.364 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z11 coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/z11_family_coefficients.png)


### Z11.1: main specification

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | no effort control | ols_cluster | fit | 1.786e+06 | 21 | 0.2807 | Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z | -5.092 | 0.688 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
### Z11.2: effort: Words

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling words?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_words_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Words | ols_cluster | fit | 1.786e+06 | 21 | 0.4911 | Does the real-child advantage or penalty relative to each baseline change with age after controlling words? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z | 1.042 | 0.3763 | 0.006 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | nb_words_z | -16.64 | 0.4168 | <.001 |
### Z11.3: effort: Morphemes

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling morphemes?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_morphemes_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Morphemes | ols_cluster | fit | 1.786e+06 | 21 | 0.4761 | Does the real-child advantage or penalty relative to each baseline change with age after controlling morphemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z | 1.029 | 0.4177 | 0.014 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | nb_morphemes_z | -16.09 | 0.364 | <.001 |
### Z11.4: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: cmu/pkg?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_syllables_cmu_or_pkg_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | ols_cluster | fit | 1.786e+06 | 21 | 0.4212 | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: cmu/pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | age_months_z | -0.6796 | 0.5156 | 0.188 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | -13.5 | 0.5121 | <.001 |
### Z11.5: effort: Syllables: pkg

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: pkg?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_syllables_pkg_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | ols_cluster | fit | 1.786e+06 | 21 | 0.4215 | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | age_months_z | -0.7358 | 0.5112 | 0.150 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | nb_syllables_pkg_z | -13.46 | 0.5238 | <.001 |
### Z11.6: effort: Phonemes

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling phonemes?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_phonemes_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Phonemes | ols_cluster | fit | 1.786e+06 | 21 | 0.4203 | Does the real-child advantage or penalty relative to each baseline change with age after controlling phonemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Phonemes | C(baseline_variant)[T.random] | -35.65 | 1.608 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | C(baseline_variant)[T.trigram] | 1.991 | 0.1392 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | C(baseline_variant)[T.unigram] | -3.247 | 0.1718 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | age_months_z | -0.6729 | 0.4893 | 0.169 |
| Z11 Real-minus-baseline delta | effort=Phonemes | age_months_z:C(baseline_variant)[T.random] | -12.85 | 1.555 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | age_months_z:C(baseline_variant)[T.trigram] | 0.4172 | 0.1217 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | age_months_z:C(baseline_variant)[T.unigram] | -1.225 | 0.1689 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | nb_phonemes_z | -13.45 | 0.5241 | <.001 |



## Compact Model Zoo Summary

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Morphemes | ols_cluster | fit | 5560 | 21 | 0.5501 | At the same morphemes level, does child total information change with age after child identity is controlled? |
| Z1 Information | child FE | effort=Phonemes | ols_cluster | fit | 5560 | 21 | 0.6147 | At the same phonemes level, does child total information change with age after child identity is controlled? |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.6253 | At the same syllables: cmu/pkg level, does child total information change with age after child identity is controlled? |
| Z1 Information | child FE | effort=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.5975 | At the same syllables: pkg level, does child total information change with age after child identity is controlled? |
| Z1 Information | child FE | effort=Words | ols_cluster | fit | 5560 | 21 | 0.5714 | At the same words level, does child total information change with age after child identity is controlled? |
| Z10 Context certainty | effort=Morphemes | gee_poisson | empty data |  |  |  | Is child morphemes lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Phonemes | gee_poisson | empty data |  |  |  | Is child phonemes lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Syllables: CMU/pkg | gee_poisson | empty data |  |  |  | Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Syllables: pkg | gee_poisson | empty data |  |  |  | Is child syllables: pkg lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Words | gee_poisson | empty data |  |  |  | Is child words lower when the model assigns high probability to the most likely next token? |
| Z11 Real-minus-baseline delta | effort=Morphemes | ols_cluster | fit | 1.786e+06 | 21 | 0.4761 | Does the real-child advantage or penalty relative to each baseline change with age after controlling morphemes? |
| Z11 Real-minus-baseline delta | effort=Phonemes | ols_cluster | fit | 1.786e+06 | 21 | 0.4203 | Does the real-child advantage or penalty relative to each baseline change with age after controlling phonemes? |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | ols_cluster | fit | 1.786e+06 | 21 | 0.4212 | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: cmu/pkg? |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | ols_cluster | fit | 1.786e+06 | 21 | 0.4215 | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: pkg? |
| Z11 Real-minus-baseline delta | effort=Words | ols_cluster | fit | 1.786e+06 | 21 | 0.4911 | Does the real-child advantage or penalty relative to each baseline change with age after controlling words? |
| Z11 Real-minus-baseline delta | no effort control | ols_cluster | fit | 1.786e+06 | 21 | 0.2807 | Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls? |
| Z2 Information density | nonlinear age | unit=Morphemes | ols_cluster | fit | 5560 | 21 | 0.4343 | Does information per morphemes follow a nonlinear developmental trajectory? |
| Z2 Information density | nonlinear age | unit=Phonemes | ols_cluster | fit | 5560 | 21 | 0.5489 | Does information per phonemes follow a nonlinear developmental trajectory? |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.4981 | Does information per syllables: cmu/pkg follow a nonlinear developmental trajectory? |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.4414 | Does information per syllables: pkg follow a nonlinear developmental trajectory? |
| Z2 Information density | nonlinear age | unit=Words | ols_cluster | fit | 5560 | 21 | 0.3771 | Does information per words follow a nonlinear developmental trajectory? |
| Z3 Effort from context entropy | effort=Morphemes | gee_poisson | empty data |  |  |  | Do children produce more morphemes after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Phonemes | gee_poisson | empty data |  |  |  | Do children produce more phonemes after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | gee_poisson | empty data |  |  |  | Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Syllables: pkg | gee_poisson | empty data |  |  |  | Do children produce more syllables: pkg after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Words | gee_poisson | empty data |  |  |  | Do children produce more words after more uncertain caretaker contexts? |
| Z4 Information from context entropy | effort=Morphemes | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after morphemes is controlled? |
| Z4 Information from context entropy | effort=Phonemes | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after phonemes is controlled? |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after syllables: cmu/pkg is controlled? |
| Z4 Information from context entropy | effort=Syllables: pkg | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after syllables: pkg is controlled? |
| Z4 Information from context entropy | effort=Words | gee_gamma_log | empty data |  |  |  | Is total child information related to context entropy after words is controlled? |
| Z5 Context window sensitivity | unit=Morphemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.4357 | Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Phonemes | gee_gaussian | fit | 1.554e+04 | 21 | 0.5317 | Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | gee_gaussian | fit | 1.554e+04 | 21 | 0.4784 | Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Syllables: pkg | gee_gaussian | fit | 1.554e+04 | 21 | 0.4246 | Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows? |

Selected coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Words | age_months_z | -1.559 | 0.5609 | 0.005 |
| Z1 Information | child FE | effort=Words | nb_words_z | 17.08 | 0.5952 | <.001 |
| Z1 Information | child FE | effort=Morphemes | age_months_z | -1.687 | 0.6765 | 0.013 |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | age_months_z | -1.246 | 0.4876 | 0.011 |
| Z1 Information | child FE | effort=Syllables: pkg | age_months_z | -1.038 | 0.5447 | 0.057 |
| Z1 Information | child FE | effort=Phonemes | age_months_z | -1.223 | 0.4781 | 0.011 |
| Z2 Information density | nonlinear age | unit=Words | age_months_z | -0.3338 | 0.2225 | 0.134 |
| Z2 Information density | nonlinear age | unit=Words | log_nb_words | -7.421 | 0.3297 | <.001 |
| Z2 Information density | nonlinear age | unit=Morphemes | age_months_z | -0.2145 | 0.2067 | 0.299 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | age_months_z | 0.05576 | 0.1719 | 0.746 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | age_months_z | 0.08572 | 0.1966 | 0.663 |
| Z2 Information density | nonlinear age | unit=Phonemes | age_months_z | 0.3395 | 0.06051 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z | -0.5332 | 0.1481 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k2] | 0.01662 | 0.0772 | 0.830 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k3] | 0.09349 | 0.05632 | 0.097 |
| Z5 Context window sensitivity | unit=Words | log_nb_words | -7.016 | 0.3224 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z | -0.4767 | 0.128 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k2] | 0.01553 | 0.07765 | 0.841 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k3] | 0.09443 | 0.05444 | 0.083 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z | -0.2511 | 0.07393 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k2] | 0.04583 | 0.0416 | 0.271 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k3] | 0.1059 | 0.03819 | 0.006 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z | -0.1877 | 0.09432 | 0.047 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k2] | -0.008937 | 0.04689 | 0.849 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k3] | 0.09467 | 0.05597 | 0.091 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z | 0.1306 | 0.06134 | 0.033 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k2] | 0.04539 | 0.03126 | 0.146 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k3] | 0.06966 | 0.02648 | 0.009 |
| Z6 Question-type effort | effort=Words | age_months_z | 0.1662 | 0.02665 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.not question] | 0.04538 | 0.01797 | 0.012 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.other question] | 0.08947 | 0.01921 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.wh-question] | 0.07435 | 0.0225 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.yes/no question] | 0.04097 | 0.02741 | 0.135 |
| Z6 Question-type effort | effort=Morphemes | age_months_z | 0.1743 | 0.02871 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.not question] | 0.04737 | 0.02012 | 0.019 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.other question] | 0.09663 | 0.02071 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.wh-question] | 0.07984 | 0.02642 | 0.003 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.05767 | 0.02886 | 0.046 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z | 0.1326 | 0.0238 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.not question] | 0.06296 | 0.01621 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.other question] | 0.1028 | 0.01965 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.09024 | 0.02861 | 0.002 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.05351 | 0.03197 | 0.094 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z | 0.1309 | 0.02231 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.not question] | 0.05947 | 0.01781 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.other question] | 0.1055 | 0.01982 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.08825 | 0.03135 | 0.005 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.05722 | 0.03049 | 0.060 |
| Z6 Question-type effort | effort=Phonemes | age_months_z | 0.1447 | 0.02387 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.not question] | 0.05202 | 0.01743 | 0.003 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.other question] | 0.09632 | 0.02064 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.wh-question] | 0.07858 | 0.02723 | 0.004 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.05078 | 0.02914 | 0.081 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.random] | 0.5207 | 0.007824 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.real] | -0.1458 | 0.01066 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.trigram] | -0.02854 | 0.006141 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.unigram] | 0.06534 | 0.0062 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z | -0.01157 | 0.006551 | 0.077 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.random] | 0.09264 | 0.01144 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.real] | -0.0225 | 0.00967 | 0.020 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.trigram] | 0.0009037 | 0.006511 | 0.890 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.unigram] | 0.005271 | 0.007331 | 0.472 |
| Z7 Baseline comparison | effort=Words | nb_words_z | 0.5118 | 0.01427 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.random] | 0.4274 | 0.005753 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.real] | -0.1479 | 0.0126 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.trigram] | -0.02843 | 0.006791 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.unigram] | 0.06253 | 0.006589 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z | -0.001994 | 0.007827 | 0.799 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.random] | 0.06113 | 0.008959 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.real] | -0.02564 | 0.01234 | 0.038 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.trigram] | -0.001882 | 0.006334 | 0.766 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.unigram] | 0.004854 | 0.005719 | 0.396 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.random] | 0.25 | 0.007439 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.real] | -0.1564 | 0.01219 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.trigram] | -0.03687 | 0.005426 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.unigram] | 0.06164 | 0.006035 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z | 0.02355 | 0.008887 | 0.008 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.random] | -0.005045 | 0.01162 | 0.664 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.real] | -0.03037 | 0.01273 | 0.017 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.trigram] | -0.003304 | 0.009711 | 0.734 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.unigram] | 0.004881 | 0.006263 | 0.436 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.random] | 0.2713 | 0.007433 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.real] | -0.1569 | 0.01239 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.trigram] | -0.03703 | 0.00622 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.unigram] | 0.06285 | 0.005963 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z | 0.02377 | 0.00864 | 0.006 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.random] | 0.001796 | 0.011 | 0.870 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.real] | -0.02916 | 0.01186 | 0.014 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.trigram] | -0.005993 | 0.007863 | 0.446 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.unigram] | 0.006736 | 0.006775 | 0.320 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.random] | 0.1996 | 0.008109 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.real] | -0.1609 | 0.01368 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.trigram] | -0.0341 | 0.004978 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.unigram] | 0.06057 | 0.006053 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z | 0.02338 | 0.009172 | 0.011 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.random] | -0.01463 | 0.01 | 0.144 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.real] | -0.02391 | 0.01316 | 0.069 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.trigram] | 0.00222 | 0.006725 | 0.741 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.unigram] | 0.005785 | 0.00695 | 0.405 |
| Z8 Child vs caretaker information | effort=Words | C(speaker_group)[T.child] | -0.2244 | 0.02004 | <.001 |

**How to read this plot.** Each point is a selected coefficient from one of the
expanded atlas models. Positive values mean the coefficient increases the
outcome; negative values mean it decreases the outcome. Coefficients from
different model families are not always on exactly the same interpretive scale,
so use this as a map of candidates rather than as the final comparison.

![Key coefficients](../figs/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/model_zoo_key_coefficients.png)

## What This Report Suggests Checking Next

- Response-level context entropy from sampled full responses should replace or
  complement next-token entropy once available.
- Final models should keep effort measures separate instead of combining highly
  collinear word, morpheme, syllable, and phoneme counts.
- The strongest baseline claims should come from row-matched real-minus-baseline
  deltas, especially child versus trigram.
- Child-versus-caretaker analyses are useful but should not be described as
  matched controls.
- Mixed-effect or GEE specifications should be retained as sensitivity checks
  because child trajectories are not exchangeable independent rows.

## Output Files

- `results/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/model_zoo_summary.csv`
- `results/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/model_zoo_coefficients.csv`
- `results/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/comparison_model_summary.csv`
- `results/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/comparison_model_coefficients.csv`
- `results/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/baseline_delta_table.csv.gz`
- `results/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/baseline_trends.csv.gz`
- `results/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/role_trends.csv.gz`
- `results/direct_surprisal_replication/tinydialogues_pbm/route1_model_atlas/derived_predictor_dictionary.csv`
