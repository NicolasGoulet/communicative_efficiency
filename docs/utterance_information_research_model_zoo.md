# Expanded Internal Model Atlas

This is an internal modeling report, not the supervisor-facing document. Its job
is to make the central communicative-efficiency comparisons explicit before we
decide which results deserve promotion.

Direct target scores in this run come from **Mistral**. Any missing
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
| caretaker | caretaker | k0 | not_applicable_caretaker | 668903 |
| caretaker | caretaker | k1 | not_applicable_caretaker | 668903 |
| caretaker | caretaker | k2 | not_applicable_caretaker | 668903 |
| caretaker | caretaker | k3 | not_applicable_caretaker | 668903 |
| child | bigram | k0 | no_context_k0 | 446508 |
| child | bigram | k1 | empty_context | 2660 |
| child | bigram | k1 | matched | 442111 |
| child | bigram | k1 | missing_entropy | 1737 |
| child | bigram | k2 | empty_context | 2660 |
| child | bigram | k2 | matched | 440532 |
| child | bigram | k2 | matched_text_fallback | 923 |
| child | bigram | k2 | missing_entropy | 2393 |
| child | bigram | k3 | empty_context | 2660 |
| child | bigram | k3 | matched | 439259 |
| child | bigram | k3 | matched_text_fallback | 2154 |
| child | bigram | k3 | missing_entropy | 2435 |
| child | random | k0 | no_context_k0 | 446508 |
| child | random | k1 | empty_context | 2660 |
| child | random | k1 | matched | 442111 |
| child | random | k1 | missing_entropy | 1737 |
| child | random | k2 | empty_context | 2660 |
| child | random | k2 | matched | 440532 |
| child | random | k2 | matched_text_fallback | 923 |
| child | random | k2 | missing_entropy | 2393 |
| child | random | k3 | empty_context | 2660 |
| child | random | k3 | matched | 439259 |
| child | random | k3 | matched_text_fallback | 2154 |
| child | random | k3 | missing_entropy | 2435 |
| child | real | k0 | no_context_k0 | 446985 |
| child | real | k1 | empty_context | 2660 |
| child | real | k1 | matched | 442220 |
| child | real | k1 | missing_entropy | 2105 |
| child | real | k2 | empty_context | 2660 |
| child | real | k2 | matched | 440538 |
| child | real | k2 | matched_text_fallback | 923 |
| child | real | k2 | missing_entropy | 2864 |
| child | real | k3 | empty_context | 2660 |
| child | real | k3 | matched | 439259 |
| child | real | k3 | matched_text_fallback | 2154 |
| child | real | k3 | missing_entropy | 2912 |

Response-level entropy features present: `False`.

Response-level entropy is absent, but this scorer run includes next-token context entropy as a provisional context-predictability measure. This is not entropy over complete possible responses.

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

![Predictor correlations](../figs/utterance_information_research_model_zoo/exploratory_predictor_correlation.png)

## Model Family Manifest

This table is the audit trail for the zoo. A **family** is a scientific question
such as child-versus-baseline or context entropy predicting effort. A
**subvariant** is a true model change, usually replacing the effort definition
or the information-density unit. Alternate plots of the same fitted model are
diagnostic views, not subvariants.

| family_id | family_title | subvariant | model | question | formula | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Z1 | Information With Child Identity | effort: Words | Z1 Information | child FE | effort=Words | At the same words level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_words_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.6327 |
| Z1 | Information With Child Identity | effort: Morphemes | Z1 Information | child FE | effort=Morphemes | At the same morphemes level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_morphemes_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.6228 |
| Z1 | Information With Child Identity | effort: Syllables: CMU/pkg | Z1 Information | child FE | effort=Syllables: CMU/pkg | At the same syllables: cmu/pkg level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_syllables_cmu_or_pkg_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.6545 |
| Z1 | Information With Child Identity | effort: Syllables: pkg | Z1 Information | child FE | effort=Syllables: pkg | At the same syllables: pkg level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_syllables_pkg_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.6408 |
| Z1 | Information With Child Identity | effort: Phonemes | Z1 Information | child FE | effort=Phonemes | At the same phonemes level, does child total information change with age after child identity is controlled? | sum_bits ~ age_months_z + nb_phonemes_z + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.6596 |
| Z2 | Nonlinear Information Density | unit: Words | Z2 Information density | nonlinear age | unit=Words | Does information per words follow a nonlinear developmental trajectory? | bits_per_word ~ age_months_z + I(age_months_z ** 2) + log_nb_words + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.2741 |
| Z2 | Nonlinear Information Density | unit: Morphemes | Z2 Information density | nonlinear age | unit=Morphemes | Does information per morphemes follow a nonlinear developmental trajectory? | bits_per_morpheme ~ age_months_z + I(age_months_z ** 2) + log_nb_morphemes + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.3275 |
| Z2 | Nonlinear Information Density | unit: Syllables: CMU/pkg | Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | Does information per syllables: cmu/pkg follow a nonlinear developmental trajectory? | bits_per_syllable_cmu_or_pkg ~ age_months_z + I(age_months_z ** 2) + log_nb_syllables + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.3299 |
| Z2 | Nonlinear Information Density | unit: Syllables: pkg | Z2 Information density | nonlinear age | unit=Syllables: pkg | Does information per syllables: pkg follow a nonlinear developmental trajectory? | bits_per_syllable_pkg ~ age_months_z + I(age_months_z ** 2) + log_nb_syllables + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.2959 |
| Z2 | Nonlinear Information Density | unit: Phonemes | Z2 Information density | nonlinear age | unit=Phonemes | Does information per phonemes follow a nonlinear developmental trajectory? | bits_per_phoneme ~ age_months_z + I(age_months_z ** 2) + log_nb_phonemes + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.4168 |
| Z3 | Context Entropy Predicting Effort | effort: Words | Z3 Effort from context entropy | effort=Words | Do children produce more words after more uncertain caretaker contexts? | nb_words ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.1012 |
| Z3 | Context Entropy Predicting Effort | effort: Morphemes | Z3 Effort from context entropy | effort=Morphemes | Do children produce more morphemes after more uncertain caretaker contexts? | nb_morphemes ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.1013 |
| Z3 | Context Entropy Predicting Effort | effort: Syllables: CMU/pkg | Z3 Effort from context entropy | effort=Syllables: CMU/pkg | Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts? | nb_syllables_cmu_or_pkg ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.08609 |
| Z3 | Context Entropy Predicting Effort | effort: Syllables: pkg | Z3 Effort from context entropy | effort=Syllables: pkg | Do children produce more syllables: pkg after more uncertain caretaker contexts? | nb_syllables_pkg ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.08093 |
| Z3 | Context Entropy Predicting Effort | effort: Phonemes | Z3 Effort from context entropy | effort=Phonemes | Do children produce more phonemes after more uncertain caretaker contexts? | nb_phonemes ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.07936 |
| Z4 | Context Entropy Predicting Information | effort: Words | Z4 Information from context entropy | effort=Words | Is total child information related to context entropy after words is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_words_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | fit | 15342 | 21 | 0.161 |
| Z4 | Context Entropy Predicting Information | effort: Morphemes | Z4 Information from context entropy | effort=Morphemes | Is total child information related to context entropy after morphemes is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_morphemes_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | fit | 15342 | 21 | 0.2433 |
| Z4 | Context Entropy Predicting Information | effort: Syllables: CMU/pkg | Z4 Information from context entropy | effort=Syllables: CMU/pkg | Is total child information related to context entropy after syllables: cmu/pkg is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_syllables_cmu_or_pkg_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | fit | 15342 | 21 | 0.2055 |
| Z4 | Context Entropy Predicting Information | effort: Syllables: pkg | Z4 Information from context entropy | effort=Syllables: pkg | Is total child information related to context entropy after syllables: pkg is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_syllables_pkg_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | fit | 15342 | 21 | 0.2184 |
| Z4 | Context Entropy Predicting Information | effort: Phonemes | Z4 Information from context entropy | effort=Phonemes | Is total child information related to context entropy after phonemes is controlled? | sum_bits ~ age_months_z * context_entropy_bits_z + nb_phonemes_z + log_context_words_plus1 + C(context_k) | gee_gamma_log | fit | 15342 | 21 | 0.1679 |
| Z5 | Scoring Context Window Sensitivity | unit: Words | Z5 Context window sensitivity | unit=Words | Does the age trajectory of information per words change across k1/k2/k3 scoring windows? | bits_per_word ~ age_months_z * C(context_k) + log_nb_words | gee_gaussian | fit | 15342 | 21 | 0.3385 |
| Z5 | Scoring Context Window Sensitivity | unit: Morphemes | Z5 Context window sensitivity | unit=Morphemes | Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows? | bits_per_morpheme ~ age_months_z * C(context_k) + log_nb_morphemes | gee_gaussian | fit | 15342 | 21 | 0.3902 |
| Z5 | Scoring Context Window Sensitivity | unit: Syllables: CMU/pkg | Z5 Context window sensitivity | unit=Syllables: CMU/pkg | Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows? | bits_per_syllable_cmu_or_pkg ~ age_months_z * C(context_k) + log_nb_syllables | gee_gaussian | fit | 15342 | 21 | 0.4064 |
| Z5 | Scoring Context Window Sensitivity | unit: Syllables: pkg | Z5 Context window sensitivity | unit=Syllables: pkg | Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows? | bits_per_syllable_pkg ~ age_months_z * C(context_k) + log_nb_syllables | gee_gaussian | fit | 15342 | 21 | 0.3587 |
| Z5 | Scoring Context Window Sensitivity | unit: Phonemes | Z5 Context window sensitivity | unit=Phonemes | Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows? | bits_per_phoneme ~ age_months_z * C(context_k) + log_nb_phonemes | gee_gaussian | fit | 15342 | 21 | 0.4753 |
| Z6 | Question Type Predicting Effort | effort: Words | Z6 Question-type effort | effort=Words | Does caretaker question type modulate child words, and does that modulation change with age? | nb_words ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 15342 | 21 | 0.1018 |
| Z6 | Question Type Predicting Effort | effort: Morphemes | Z6 Question-type effort | effort=Morphemes | Does caretaker question type modulate child morphemes, and does that modulation change with age? | nb_morphemes ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 15342 | 21 | 0.1022 |
| Z6 | Question Type Predicting Effort | effort: Syllables: CMU/pkg | Z6 Question-type effort | effort=Syllables: CMU/pkg | Does caretaker question type modulate child syllables: cmu/pkg, and does that modulation change with age? | nb_syllables_cmu_or_pkg ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 15342 | 21 | 0.08694 |
| Z6 | Question Type Predicting Effort | effort: Syllables: pkg | Z6 Question-type effort | effort=Syllables: pkg | Does caretaker question type modulate child syllables: pkg, and does that modulation change with age? | nb_syllables_pkg ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 15342 | 21 | 0.08178 |
| Z6 | Question Type Predicting Effort | effort: Phonemes | Z6 Question-type effort | effort=Phonemes | Does caretaker question type modulate child phonemes, and does that modulation change with age? | nb_phonemes ~ age_months_z * C(context_question_type) + log_context_words_plus1 | gee_poisson | fit | 15342 | 21 | 0.08042 |
| Z7 | Real Children Versus All Matched Baselines | effort: Words | Z7 Baseline comparison | effort=Words | Do real child utterances differ from random/ngram baselines after controlling words? | sum_bits ~ age_months_z * C(target_variant) + nb_words_z | gee_gamma_log | fit | 18225 | 21 | 0.04299 |
| Z7 | Real Children Versus All Matched Baselines | effort: Morphemes | Z7 Baseline comparison | effort=Morphemes | Do real child utterances differ from random/ngram baselines after controlling morphemes? | sum_bits ~ age_months_z * C(target_variant) + nb_morphemes_z | gee_gamma_log | fit | 18225 | 21 | 0.03944 |
| Z7 | Real Children Versus All Matched Baselines | effort: Syllables: CMU/pkg | Z7 Baseline comparison | effort=Syllables: CMU/pkg | Do real child utterances differ from random/ngram baselines after controlling syllables: cmu/pkg? | sum_bits ~ age_months_z * C(target_variant) + nb_syllables_cmu_or_pkg_z | gee_gamma_log | fit | 18225 | 21 | 0.04555 |
| Z7 | Real Children Versus All Matched Baselines | effort: Syllables: pkg | Z7 Baseline comparison | effort=Syllables: pkg | Do real child utterances differ from random/ngram baselines after controlling syllables: pkg? | sum_bits ~ age_months_z * C(target_variant) + nb_syllables_pkg_z | gee_gamma_log | fit | 18225 | 21 | 0.04568 |
| Z7 | Real Children Versus All Matched Baselines | effort: Phonemes | Z7 Baseline comparison | effort=Phonemes | Do real child utterances differ from random/ngram baselines after controlling phonemes? | sum_bits ~ age_months_z * C(target_variant) + nb_phonemes_z | gee_gamma_log | fit | 18225 | 21 | 0.0377 |
| Z8 | Children Versus Caretakers | effort: Words | Z8 Child vs caretaker information | effort=Words | Do child and caretaker total-bit trajectories differ after controlling words? | sum_bits ~ age_months_z * C(speaker_group) + nb_words_z | gee_gamma_log | fit | 10075 | 21 | 0.1359 |
| Z8 | Children Versus Caretakers | effort: Morphemes | Z8 Child vs caretaker information | effort=Morphemes | Do child and caretaker total-bit trajectories differ after controlling morphemes? | sum_bits ~ age_months_z * C(speaker_group) + nb_morphemes_z | gee_gamma_log | fit | 10075 | 21 | 0.1649 |
| Z8 | Children Versus Caretakers | effort: Syllables: CMU/pkg | Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg? | sum_bits ~ age_months_z * C(speaker_group) + nb_syllables_cmu_or_pkg_z | gee_gamma_log | fit | 10075 | 21 | 0.1178 |
| Z8 | Children Versus Caretakers | effort: Syllables: pkg | Z8 Child vs caretaker information | effort=Syllables: pkg | Do child and caretaker total-bit trajectories differ after controlling syllables: pkg? | sum_bits ~ age_months_z * C(speaker_group) + nb_syllables_pkg_z | gee_gamma_log | fit | 10075 | 21 | 0.1329 |
| Z8 | Children Versus Caretakers | effort: Phonemes | Z8 Child vs caretaker information | effort=Phonemes | Do child and caretaker total-bit trajectories differ after controlling phonemes? | sum_bits ~ age_months_z * C(speaker_group) + nb_phonemes_z | gee_gamma_log | fit | 10075 | 21 | 0.08581 |
| Z9 | Information Per Effort Unit | unit: Words | Z9 Information per unit | unit=Words | Does information per words change with age after child identity is controlled? | bits_per_word ~ age_months_z + log_nb_words + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.2729 |
| Z9 | Information Per Effort Unit | unit: Morphemes | Z9 Information per unit | unit=Morphemes | Does information per morphemes change with age after child identity is controlled? | bits_per_morpheme ~ age_months_z + log_nb_morphemes + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.3266 |
| Z9 | Information Per Effort Unit | unit: Syllables: CMU/pkg | Z9 Information per unit | unit=Syllables: CMU/pkg | Does information per syllables: cmu/pkg change with age after child identity is controlled? | bits_per_syllable_cmu_or_pkg ~ age_months_z + log_nb_syllables + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.3298 |
| Z9 | Information Per Effort Unit | unit: Syllables: pkg | Z9 Information per unit | unit=Syllables: pkg | Does information per syllables: pkg change with age after child identity is controlled? | bits_per_syllable_pkg ~ age_months_z + log_nb_syllables + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.2959 |
| Z9 | Information Per Effort Unit | unit: Phonemes | Z9 Information per unit | unit=Phonemes | Does information per phonemes change with age after child identity is controlled? | bits_per_phoneme ~ age_months_z + log_nb_phonemes + C(child_id) | ols_cluster | fit | 5560 | 21 | 0.4164 |
| Z10 | Context Certainty Predicting Effort | effort: Words | Z10 Context certainty | effort=Words | Is child words lower when the model assigns high probability to the most likely next token? | nb_words ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.1013 |
| Z10 | Context Certainty Predicting Effort | effort: Morphemes | Z10 Context certainty | effort=Morphemes | Is child morphemes lower when the model assigns high probability to the most likely next token? | nb_morphemes ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.1014 |
| Z10 | Context Certainty Predicting Effort | effort: Syllables: CMU/pkg | Z10 Context certainty | effort=Syllables: CMU/pkg | Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token? | nb_syllables_cmu_or_pkg ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.08628 |
| Z10 | Context Certainty Predicting Effort | effort: Syllables: pkg | Z10 Context certainty | effort=Syllables: pkg | Is child syllables: pkg lower when the model assigns high probability to the most likely next token? | nb_syllables_pkg ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.0811 |
| Z10 | Context Certainty Predicting Effort | effort: Phonemes | Z10 Context certainty | effort=Phonemes | Is child phonemes lower when the model assigns high probability to the most likely next token? | nb_phonemes ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type) | gee_poisson | fit | 15342 | 21 | 0.07952 |
| Z11 | Real Minus Baseline Delta | main specification | Z11 Real-minus-baseline delta | no effort control | Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls? | delta_sum_bits ~ age_months_z * C(baseline_variant) + C(child_id) | ols_cluster | fit | 1786032 | 21 | 0.2801 |
| Z11 | Real Minus Baseline Delta | effort: Words | Z11 Real-minus-baseline delta | effort=Words | Does the real-child advantage or penalty relative to each baseline change with age after controlling words? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_words_z + C(child_id) | ols_cluster | fit | 1786032 | 21 | 0.5957 |
| Z11 | Real Minus Baseline Delta | effort: Morphemes | Z11 Real-minus-baseline delta | effort=Morphemes | Does the real-child advantage or penalty relative to each baseline change with age after controlling morphemes? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_morphemes_z + C(child_id) | ols_cluster | fit | 1786032 | 21 | 0.5671 |
| Z11 | Real Minus Baseline Delta | effort: Syllables: CMU/pkg | Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: cmu/pkg? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_syllables_cmu_or_pkg_z + C(child_id) | ols_cluster | fit | 1786032 | 21 | 0.5172 |
| Z11 | Real Minus Baseline Delta | effort: Syllables: pkg | Z11 Real-minus-baseline delta | effort=Syllables: pkg | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: pkg? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_syllables_pkg_z + C(child_id) | ols_cluster | fit | 1786032 | 21 | 0.5146 |
| Z11 | Real Minus Baseline Delta | effort: Phonemes | Z11 Real-minus-baseline delta | effort=Phonemes | Does the real-child advantage or penalty relative to each baseline change with age after controlling phonemes? | delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_phonemes_z + C(child_id) | ols_cluster | fit | 1786032 | 21 | 0.5125 |

## Omnibus Baseline Trajectories

These plots answer the first sanity question: how far are real child utterances
from increasingly structured baselines over developmental time?

**How to read this plot.** Each line is an age-bin mean for one target type.
This plot uses total utterance bits, so it is descriptive and still reflects
utterance-size differences.

![All baseline total bits](../figs/utterance_information_research_model_zoo/baseline_all_total_bits.png)

**How to read this plot.** This is the same baseline comparison after dividing
total bits by word count. It is a direct information-density view, but it only
controls word count, not phonemes, syllables, or morphemes.

![All baseline bits per word](../figs/utterance_information_research_model_zoo/baseline_all_bits_per_word.png)

Because the generated baselines are word-count matched but not necessarily
phoneme-, syllable-, or morpheme-matched, effort profiles are checked directly.

**How to read this plot.** Each panel checks whether real and generated
utterances differ in non-word effort units. The baselines are word-count
matched, but they can still differ in morphemes, syllables, and phonemes.

![Baseline effort profiles](../figs/utterance_information_research_model_zoo/baseline_effort_profiles_nonword_units.png)

Real-minus-baseline deltas:

| age_bin | baseline_variant | mean_delta | sem_delta | n_rows | outcome |
| --- | --- | --- | --- | --- | --- |
| 006-023 | bigram | -6.855 | 0.05659 | 62816 | delta_sum_bits |
| 006-023 | random | -22.59 | 0.08992 | 62816 | delta_sum_bits |
| 006-023 | trigram | -3.934 | 0.04875 | 62816 | delta_sum_bits |
| 006-023 | unigram | -10.84 | 0.06336 | 62816 | delta_sum_bits |
| 024-029 | bigram | -8.561 | 0.03642 | 162210 | delta_sum_bits |
| 024-029 | random | -28.62 | 0.06322 | 162210 | delta_sum_bits |
| 024-029 | trigram | -5.859 | 0.03336 | 162210 | delta_sum_bits |
| 024-029 | unigram | -12.83 | 0.0408 | 162210 | delta_sum_bits |
| 030-035 | bigram | -11.24 | 0.04261 | 142447 | delta_sum_bits |
| 030-035 | random | -37.84 | 0.08412 | 142447 | delta_sum_bits |
| 030-035 | trigram | -8.015 | 0.03916 | 142447 | delta_sum_bits |
| 030-035 | unigram | -16.53 | 0.04886 | 142447 | delta_sum_bits |
| 036-041 | bigram | -11.96 | 0.09249 | 37206 | delta_sum_bits |
| 036-041 | random | -43.96 | 0.1866 | 37206 | delta_sum_bits |
| 036-041 | trigram | -8.508 | 0.08589 | 37206 | delta_sum_bits |
| 036-041 | unigram | -18.22 | 0.106 | 37206 | delta_sum_bits |
| 042-047 | bigram | -16.1 | 0.1536 | 16345 | delta_sum_bits |
| 042-047 | random | -53.51 | 0.3171 | 16345 | delta_sum_bits |
| 042-047 | trigram | -11.76 | 0.1416 | 16345 | delta_sum_bits |
| 042-047 | unigram | -23.39 | 0.1779 | 16345 | delta_sum_bits |
| 048-053 | bigram | -13.86 | 0.1648 | 12909 | delta_sum_bits |
| 048-053 | random | -53.3 | 0.3402 | 12909 | delta_sum_bits |
| 048-053 | trigram | -9.577 | 0.1539 | 12909 | delta_sum_bits |
| 048-053 | unigram | -21.51 | 0.1886 | 12909 | delta_sum_bits |
| 054-059 | bigram | -15.15 | 0.193 | 10033 | delta_sum_bits |
| 054-059 | random | -56.46 | 0.4098 | 10033 | delta_sum_bits |
| 054-059 | trigram | -10.56 | 0.179 | 10033 | delta_sum_bits |
| 054-059 | unigram | -23.24 | 0.2215 | 10033 | delta_sum_bits |
| 060-065 | bigram | -16.64 | 0.3705 | 2542 | delta_sum_bits |
| 060-065 | random | -57.27 | 0.8188 | 2542 | delta_sum_bits |
| 060-065 | trigram | -12.6 | 0.3534 | 2542 | delta_sum_bits |
| 060-065 | unigram | -24.75 | 0.4486 | 2542 | delta_sum_bits |
| 006-023 | bigram | -2.855 | 0.02689 | 62816 | delta_bits_per_word |
| 006-023 | random | -10.6 | 0.02818 | 62816 | delta_bits_per_word |
| 006-023 | trigram | -1.599 | 0.02408 | 62816 | delta_bits_per_word |
| 006-023 | unigram | -4.701 | 0.02699 | 62816 | delta_bits_per_word |
| 024-029 | bigram | -3.321 | 0.01557 | 162210 | delta_bits_per_word |
| 024-029 | random | -11.82 | 0.01597 | 162210 | delta_bits_per_word |
| 024-029 | trigram | -2.223 | 0.0148 | 162210 | delta_bits_per_word |
| 024-029 | unigram | -5.02 | 0.01542 | 162210 | delta_bits_per_word |

## Explicit Comparison Models

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus random: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.8201 | Does the real-child minus random total-bit gap change with age after controlling words and child identity? |
| Child minus random: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.7682 | Does the real-child minus random total-bit gap change with age after controlling morphemes and child identity? |
| Child minus random: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.6907 | Does the real-child minus random total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus random: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.6816 | Does the real-child minus random total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus random: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.6821 | Does the real-child minus random total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs random | effort=Words | gee_gamma_log | fit | 7335 | 21 | 0.06001 | Do real child and random total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs random | effort=Morphemes | gee_gamma_log | fit | 7335 | 21 | 0.05988 | Do real child and random total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7335 | 21 | 0.07815 | Do real child and random total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs random | effort=Syllables: pkg | gee_gamma_log | fit | 7335 | 21 | 0.07777 | Do real child and random total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs random | effort=Phonemes | gee_gamma_log | fit | 7335 | 21 | 0.06471 | Do real child and random total-bit trajectories diverge over age when phonemes is controlled? |
| Child minus unigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.5427 | Does the real-child minus unigram total-bit gap change with age after controlling words and child identity? |
| Child minus unigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.5002 | Does the real-child minus unigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus unigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.4237 | Does the real-child minus unigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus unigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.4207 | Does the real-child minus unigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus unigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.417 | Does the real-child minus unigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs unigram | effort=Words | gee_gamma_log | fit | 7110 | 21 | 0.4043 | Do real child and unigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs unigram | effort=Morphemes | gee_gamma_log | fit | 7110 | 21 | 0.4059 | Do real child and unigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs unigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7110 | 21 | 0.3944 | Do real child and unigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs unigram | effort=Syllables: pkg | gee_gamma_log | fit | 7110 | 21 | 0.3268 | Do real child and unigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs unigram | effort=Phonemes | gee_gamma_log | fit | 7110 | 21 | 0.4353 | Do real child and unigram total-bit trajectories diverge over age when phonemes is controlled? |
| Child minus bigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.3481 | Does the real-child minus bigram total-bit gap change with age after controlling words and child identity? |
| Child minus bigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.3171 | Does the real-child minus bigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus bigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.257 | Does the real-child minus bigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus bigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.2558 | Does the real-child minus bigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus bigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.2521 | Does the real-child minus bigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs bigram | effort=Words | gee_gamma_log | fit | 7245 | 21 | 0.04255 | Do real child and bigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs bigram | effort=Morphemes | gee_gamma_log | fit | 7245 | 21 | 0.04124 | Do real child and bigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs bigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7245 | 21 | 0.04895 | Do real child and bigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs bigram | effort=Syllables: pkg | gee_gamma_log | fit | 7245 | 21 | 0.04731 | Do real child and bigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs bigram | effort=Phonemes | gee_gamma_log | fit | 7245 | 21 | 0.04161 | Do real child and bigram total-bit trajectories diverge over age when phonemes is controlled? |
| Child minus trigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.2282 | Does the real-child minus trigram total-bit gap change with age after controlling words and child identity? |
| Child minus trigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.2055 | Does the real-child minus trigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus trigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.1598 | Does the real-child minus trigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus trigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.1601 | Does the real-child minus trigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus trigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.1561 | Does the real-child minus trigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs trigram | effort=Words | gee_gamma_log | fit | 7335 | 21 | 0.3082 | Do real child and trigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs trigram | effort=Morphemes | gee_gamma_log | fit | 7335 | 21 | 0.3624 | Do real child and trigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs trigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7335 | 21 | 0.267 | Do real child and trigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs trigram | effort=Syllables: pkg | gee_gamma_log | fit | 7335 | 21 | 0.2538 | Do real child and trigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs trigram | effort=Phonemes | gee_gamma_log | fit | 7335 | 21 | 0.2716 | Do real child and trigram total-bit trajectories diverge over age when phonemes is controlled? |
| Child vs caretaker: total bits | effort=Words | gee_gamma_log | fit | 10075 | 21 | 0.1359 | Do child and caretaker total-bit trajectories differ after controlling words? |
| Child vs caretaker: total bits | effort=Morphemes | gee_gamma_log | fit | 10075 | 21 | 0.1649 | Do child and caretaker total-bit trajectories differ after controlling morphemes? |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 10075 | 21 | 0.1178 | Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg? |
| Child vs caretaker: total bits | effort=Syllables: pkg | gee_gamma_log | fit | 10075 | 21 | 0.1329 | Do child and caretaker total-bit trajectories differ after controlling syllables: pkg? |
| Child vs caretaker: total bits | effort=Phonemes | gee_gamma_log | fit | 10075 | 21 | 0.08581 | Do child and caretaker total-bit trajectories differ after controlling phonemes? |

**How to read this plot.** Each row is one child-vs-baseline or
child-vs-caretaker model, and each column is the effort measure controlled in
that version. This is a model-fit overview, not the substantive effect itself:
it shows whether the comparison model explains more or less variance depending
on how effort is controlled.

![Effort-controlled comparison model fit](../figs/utterance_information_research_model_zoo/effort_controlled_comparison_model_r2.png)

**How to read this plot.** Each point is an age-related coefficient from an
effort-controlled comparison model. Values to the right of zero mean the
age-related gap increases; values to the left mean it decreases. The same
comparison is repeated under words, morphemes, syllables, and phonemes as
separate effort controls.

![Effort-controlled comparison age coefficients](../figs/utterance_information_research_model_zoo/effort_controlled_comparison_age_coefficients.png)

Key comparison coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus random: total bits | effort=Words | C(child_id)[T.Alex] | -4.459 | 0.237 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Anne] | -5.789 | 0.3661 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Aran] | -5.245 | 0.3445 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Becky] | -5.847 | 0.2922 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Carl] | -3.45 | 0.4258 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Dominic] | -3.655 | 0.3308 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Ethan] | -5.62 | 0.5038 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Eve] | -1.525 | 0.5825 | 0.009 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Gail] | -4.097 | 0.3223 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Joel] | -4.968 | 0.3128 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.John] | -2.764 | 0.3271 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Lily] | -7.244 | 0.2791 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Liz] | -4.699 | 0.3585 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Naima] | -4.476 | 0.5143 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Nicole] | -3.742 | 0.2671 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Ruth] | -3.17 | 0.2917 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Sarah] | -0.3744 | 0.1752 | 0.033 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Violet] | -6.243 | 0.2956 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Warren] | -4.073 | 0.3844 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.William] | -5.725 | 0.2909 | <.001 |
| Child minus random: total bits | effort=Words | age_months_z | -2.479 | 0.2908 | <.001 |
| Child minus random: total bits | effort=Words | nb_words_z | -27.62 | 0.3054 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Alex] | -3.804 | 0.285 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Anne] | -4.482 | 0.4588 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Aran] | -4.972 | 0.4314 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Becky] | -4.593 | 0.3618 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Carl] | -1.717 | 0.5463 | 0.002 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -2.905 | 0.406 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Ethan] | -4.541 | 0.6404 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Eve] | -2.696 | 0.7272 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Gail] | -2.453 | 0.4054 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Joel] | -3.648 | 0.3885 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.John] | -1.576 | 0.4034 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Lily] | -6.713 | 0.3539 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Liz] | -3.826 | 0.4499 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Naima] | -2.99 | 0.6694 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Nicole] | -3.331 | 0.3111 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Ruth] | -3.778 | 0.3457 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Sarah] | -0.7145 | 0.2264 | 0.002 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Violet] | -5.943 | 0.3717 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Warren] | -3.309 | 0.4889 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.William] | -5.11 | 0.3574 | <.001 |
| Child minus random: total bits | effort=Morphemes | age_months_z | -2.526 | 0.3703 | <.001 |
| Child minus random: total bits | effort=Morphemes | nb_morphemes_z | -26.66 | 0.356 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Alex] | -4.612 | 0.4423 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Anne] | -7.666 | 0.7128 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Aran] | -8.64 | 0.6648 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Becky] | -7.427 | 0.5545 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Carl] | -5.644 | 0.8531 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Dominic] | -3.992 | 0.6435 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Ethan] | -7.221 | 1.026 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Eve] | -3.369 | 1.203 | 0.005 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Gail] | -4.883 | 0.6339 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Joel] | -5.498 | 0.6097 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.John] | -2.802 | 0.6385 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Lily] | -7.998 | 0.5696 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Liz] | -6.863 | 0.7016 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Naima] | -5.473 | 1.079 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Nicole] | -2.758 | 0.4747 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Ruth] | -2.916 | 0.5467 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Sarah] | 0.4751 | 0.3449 | 0.168 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Violet] | -8.235 | 0.5847 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.Warren] | -5.591 | 0.7805 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | C(child_id)[T.William] | -6.697 | 0.5601 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | age_months_z | -4.59 | 0.586 | <.001 |
| Child minus random: total bits | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | -24.7 | 0.4879 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Alex] | -3.626 | 0.4528 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Anne] | -6.207 | 0.7305 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Aran] | -7.921 | 0.674 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Becky] | -6.675 | 0.5631 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Carl] | -4.853 | 0.8644 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Dominic] | -3.238 | 0.6523 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Ethan] | -7.055 | 1.03 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Eve] | -2.988 | 1.212 | 0.014 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Gail] | -4.352 | 0.6404 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Joel] | -4.822 | 0.6177 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.John] | -2.139 | 0.6463 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Lily] | -7.779 | 0.5732 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Liz] | -6.009 | 0.7124 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Naima] | -5.653 | 1.082 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Nicole] | -1.416 | 0.4879 | 0.004 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Ruth] | -2.276 | 0.5541 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Sarah] | 0.9018 | 0.3441 | 0.009 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Violet] | -7.542 | 0.5942 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.Warren] | -4.712 | 0.794 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | C(child_id)[T.William] | -6.444 | 0.5633 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | age_months_z | -4.769 | 0.586 | <.001 |
| Child minus random: total bits | effort=Syllables: pkg | nb_syllables_pkg_z | -24.4 | 0.5067 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Alex] | -3.798 | 0.4846 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Anne] | -6.872 | 0.7696 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Aran] | -7.804 | 0.7168 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Becky] | -6.874 | 0.601 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Carl] | -4.526 | 0.9156 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Dominic] | -2.792 | 0.7019 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Ethan] | -5.923 | 1.098 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Eve] | -3.645 | 1.253 | 0.004 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Gail] | -3.905 | 0.6875 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Joel] | -5.122 | 0.6563 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.John] | -2.091 | 0.6911 | 0.002 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Lily] | -8.095 | 0.5989 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Liz] | -6.15 | 0.7552 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Naima] | -5.264 | 1.121 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Nicole] | -2.699 | 0.5155 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Ruth] | -3.741 | 0.5821 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Sarah] | -0.4839 | 0.3636 | 0.183 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Violet] | -8.192 | 0.6195 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.Warren] | -4.85 | 0.8316 | <.001 |
| Child minus random: total bits | effort=Phonemes | C(child_id)[T.William] | -6.839 | 0.5987 | <.001 |
| Child minus random: total bits | effort=Phonemes | age_months_z | -4.616 | 0.6076 | <.001 |
| Child minus random: total bits | effort=Phonemes | nb_phonemes_z | -24.49 | 0.4718 | <.001 |
| Trajectory interaction: child vs random | effort=Words | C(target_variant)[T.real] | -0.7411 | 0.02086 | <.001 |
| Trajectory interaction: child vs random | effort=Words | age_months_z | 0.04524 | 0.01325 | <.001 |
| Trajectory interaction: child vs random | effort=Words | age_months_z:C(target_variant)[T.real] | -0.07752 | 0.01868 | <.001 |
| Trajectory interaction: child vs random | effort=Words | nb_words_z | 0.5195 | 0.01584 | <.001 |
| Trajectory interaction: child vs random | effort=Morphemes | C(target_variant)[T.real] | -0.6462 | 0.02121 | <.001 |
| Trajectory interaction: child vs random | effort=Morphemes | age_months_z | 0.03594 | 0.01102 | 0.001 |
| Trajectory interaction: child vs random | effort=Morphemes | age_months_z:C(target_variant)[T.real] | -0.05441 | 0.01444 | <.001 |
| Trajectory interaction: child vs random | effort=Morphemes | nb_morphemes_z | 0.48 | 0.01465 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | C(target_variant)[T.real] | -0.5207 | 0.01974 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | age_months_z | 0.01219 | 0.01089 | 0.263 |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.real] | -0.001876 | 0.01269 | 0.882 |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.4669 | 0.01296 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: pkg | C(target_variant)[T.real] | -0.5325 | 0.02013 | <.001 |
| Trajectory interaction: child vs random | effort=Syllables: pkg | age_months_z | 0.01421 | 0.01168 | 0.223 |
| Trajectory interaction: child vs random | effort=Syllables: pkg | age_months_z:C(target_variant)[T.real] | -0.001107 | 0.01332 | 0.934 |
| Trajectory interaction: child vs random | effort=Syllables: pkg | nb_syllables_pkg_z | 0.4657 | 0.01302 | <.001 |
| Trajectory interaction: child vs random | effort=Phonemes | C(target_variant)[T.real] | -0.4685 | 0.0214 | <.001 |
| Trajectory interaction: child vs random | effort=Phonemes | age_months_z | 0.001399 | 0.01101 | 0.899 |
| Trajectory interaction: child vs random | effort=Phonemes | age_months_z:C(target_variant)[T.real] | 0.01344 | 0.01192 | 0.259 |
| Trajectory interaction: child vs random | effort=Phonemes | nb_phonemes_z | 0.4707 | 0.01316 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Alex] | -4.536 | 0.1559 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Anne] | -5.982 | 0.2555 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Aran] | -5.469 | 0.2511 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Becky] | -5.759 | 0.1976 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Carl] | -4.117 | 0.3161 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Dominic] | -3.72 | 0.2237 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Ethan] | -5.834 | 0.3778 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Eve] | -2.505 | 0.4588 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Gail] | -4.27 | 0.2229 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Joel] | -5.021 | 0.2128 | <.001 |

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

![Child versus random dashboard](../figs/utterance_information_research_model_zoo/child_vs_random_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus random: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.8201 | Does the real-child minus random total-bit gap change with age after controlling words and child identity? |
| Child minus random: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.7682 | Does the real-child minus random total-bit gap change with age after controlling morphemes and child identity? |
| Child minus random: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.6907 | Does the real-child minus random total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus random: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.6816 | Does the real-child minus random total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus random: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.6821 | Does the real-child minus random total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs random | effort=Words | gee_gamma_log | fit | 7335 | 21 | 0.06001 | Do real child and random total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs random | effort=Morphemes | gee_gamma_log | fit | 7335 | 21 | 0.05988 | Do real child and random total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs random | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7335 | 21 | 0.07815 | Do real child and random total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs random | effort=Syllables: pkg | gee_gamma_log | fit | 7335 | 21 | 0.07777 | Do real child and random total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs random | effort=Phonemes | gee_gamma_log | fit | 7335 | 21 | 0.06471 | Do real child and random total-bit trajectories diverge over age when phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus random: total bits | effort=Words | C(child_id)[T.Alex] | -4.459 | 0.237 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Anne] | -5.789 | 0.3661 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Aran] | -5.245 | 0.3445 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Becky] | -5.847 | 0.2922 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Carl] | -3.45 | 0.4258 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Dominic] | -3.655 | 0.3308 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Ethan] | -5.62 | 0.5038 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Eve] | -1.525 | 0.5825 | 0.009 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Gail] | -4.097 | 0.3223 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Joel] | -4.968 | 0.3128 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.John] | -2.764 | 0.3271 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Lily] | -7.244 | 0.2791 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Liz] | -4.699 | 0.3585 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Naima] | -4.476 | 0.5143 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Nicole] | -3.742 | 0.2671 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Ruth] | -3.17 | 0.2917 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Sarah] | -0.3744 | 0.1752 | 0.033 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Violet] | -6.243 | 0.2956 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.Warren] | -4.073 | 0.3844 | <.001 |
| Child minus random: total bits | effort=Words | C(child_id)[T.William] | -5.725 | 0.2909 | <.001 |
| Child minus random: total bits | effort=Words | age_months_z | -2.479 | 0.2908 | <.001 |
| Child minus random: total bits | effort=Words | nb_words_z | -27.62 | 0.3054 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Alex] | -3.804 | 0.285 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Anne] | -4.482 | 0.4588 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Aran] | -4.972 | 0.4314 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Becky] | -4.593 | 0.3618 | <.001 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Carl] | -1.717 | 0.5463 | 0.002 |
| Child minus random: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -2.905 | 0.406 | <.001 |
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

![Child versus unigram dashboard](../figs/utterance_information_research_model_zoo/child_vs_unigram_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus unigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.5427 | Does the real-child minus unigram total-bit gap change with age after controlling words and child identity? |
| Child minus unigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.5002 | Does the real-child minus unigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus unigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.4237 | Does the real-child minus unigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus unigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.4207 | Does the real-child minus unigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus unigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.417 | Does the real-child minus unigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs unigram | effort=Words | gee_gamma_log | fit | 7110 | 21 | 0.4043 | Do real child and unigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs unigram | effort=Morphemes | gee_gamma_log | fit | 7110 | 21 | 0.4059 | Do real child and unigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs unigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7110 | 21 | 0.3944 | Do real child and unigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs unigram | effort=Syllables: pkg | gee_gamma_log | fit | 7110 | 21 | 0.3268 | Do real child and unigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs unigram | effort=Phonemes | gee_gamma_log | fit | 7110 | 21 | 0.4353 | Do real child and unigram total-bit trajectories diverge over age when phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Alex] | -4.536 | 0.1559 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Anne] | -5.982 | 0.2555 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Aran] | -5.469 | 0.2511 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Becky] | -5.759 | 0.1976 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Carl] | -4.117 | 0.3161 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Dominic] | -3.72 | 0.2237 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Ethan] | -5.834 | 0.3778 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Eve] | -2.505 | 0.4588 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Gail] | -4.27 | 0.2229 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Joel] | -5.021 | 0.2128 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.John] | -3.012 | 0.2208 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Lily] | -7.507 | 0.2083 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Liz] | -4.751 | 0.2551 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Naima] | -5.392 | 0.4256 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Nicole] | -3.648 | 0.1755 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Ruth] | -3.236 | 0.1916 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Sarah] | -1.074 | 0.1696 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Violet] | -6.826 | 0.2181 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.Warren] | -4.314 | 0.29 | <.001 |
| Child minus unigram: total bits | effort=Words | C(child_id)[T.William] | -5.4 | 0.1973 | <.001 |
| Child minus unigram: total bits | effort=Words | age_months_z | -0.847 | 0.2436 | <.001 |
| Child minus unigram: total bits | effort=Words | nb_words_z | -13.3 | 0.3146 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Alex] | -4.198 | 0.1554 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Anne] | -5.353 | 0.2384 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Aran] | -5.349 | 0.2249 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Becky] | -5.145 | 0.1895 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Carl] | -3.31 | 0.288 | <.001 |
| Child minus unigram: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -3.345 | 0.2134 | <.001 |
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

![Child versus bigram dashboard](../figs/utterance_information_research_model_zoo/child_vs_bigram_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus bigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.3481 | Does the real-child minus bigram total-bit gap change with age after controlling words and child identity? |
| Child minus bigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.3171 | Does the real-child minus bigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus bigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.257 | Does the real-child minus bigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus bigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.2558 | Does the real-child minus bigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus bigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.2521 | Does the real-child minus bigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs bigram | effort=Words | gee_gamma_log | fit | 7245 | 21 | 0.04255 | Do real child and bigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs bigram | effort=Morphemes | gee_gamma_log | fit | 7245 | 21 | 0.04124 | Do real child and bigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs bigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7245 | 21 | 0.04895 | Do real child and bigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs bigram | effort=Syllables: pkg | gee_gamma_log | fit | 7245 | 21 | 0.04731 | Do real child and bigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs bigram | effort=Phonemes | gee_gamma_log | fit | 7245 | 21 | 0.04161 | Do real child and bigram total-bit trajectories diverge over age when phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Alex] | -4.132 | 0.1635 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Anne] | -5.84 | 0.2496 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Aran] | -5.245 | 0.2379 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Becky] | -5.593 | 0.1989 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Carl] | -3.81 | 0.2964 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Dominic] | -3.795 | 0.2252 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Ethan] | -5.548 | 0.3525 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Eve] | -2.592 | 0.4192 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Gail] | -4.253 | 0.2194 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Joel] | -4.787 | 0.2128 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.John] | -3.102 | 0.2227 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Lily] | -7.077 | 0.1948 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Liz] | -4.657 | 0.2456 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Naima] | -5.271 | 0.3835 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Nicole] | -3.678 | 0.1918 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Ruth] | -3.301 | 0.2015 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Sarah] | -1.069 | 0.1523 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Violet] | -6.647 | 0.2052 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.Warren] | -4.036 | 0.2697 | <.001 |
| Child minus bigram: total bits | effort=Words | C(child_id)[T.William] | -5.127 | 0.1979 | <.001 |
| Child minus bigram: total bits | effort=Words | age_months_z | -0.8349 | 0.2189 | <.001 |
| Child minus bigram: total bits | effort=Words | nb_words_z | -9.23 | 0.2957 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Alex] | -3.884 | 0.1649 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Anne] | -5.404 | 0.2436 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Aran] | -5.169 | 0.2264 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Becky] | -5.161 | 0.1967 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Carl] | -3.267 | 0.286 | <.001 |
| Child minus bigram: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -3.526 | 0.2224 | <.001 |
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

![Child versus trigram dashboard](../figs/utterance_information_research_model_zoo/child_vs_trigram_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child minus trigram: total bits | effort=Words | ols_cluster | fit | 446508 | 21 | 0.2282 | Does the real-child minus trigram total-bit gap change with age after controlling words and child identity? |
| Child minus trigram: total bits | effort=Morphemes | ols_cluster | fit | 446508 | 21 | 0.2055 | Does the real-child minus trigram total-bit gap change with age after controlling morphemes and child identity? |
| Child minus trigram: total bits | effort=Syllables: CMU/pkg | ols_cluster | fit | 446508 | 21 | 0.1598 | Does the real-child minus trigram total-bit gap change with age after controlling syllables: cmu/pkg and child identity? |
| Child minus trigram: total bits | effort=Syllables: pkg | ols_cluster | fit | 446508 | 21 | 0.1601 | Does the real-child minus trigram total-bit gap change with age after controlling syllables: pkg and child identity? |
| Child minus trigram: total bits | effort=Phonemes | ols_cluster | fit | 446508 | 21 | 0.1561 | Does the real-child minus trigram total-bit gap change with age after controlling phonemes and child identity? |
| Trajectory interaction: child vs trigram | effort=Words | gee_gamma_log | fit | 7335 | 21 | 0.3082 | Do real child and trigram total-bit trajectories diverge over age when words is controlled? |
| Trajectory interaction: child vs trigram | effort=Morphemes | gee_gamma_log | fit | 7335 | 21 | 0.3624 | Do real child and trigram total-bit trajectories diverge over age when morphemes is controlled? |
| Trajectory interaction: child vs trigram | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 7335 | 21 | 0.267 | Do real child and trigram total-bit trajectories diverge over age when syllables: cmu/pkg is controlled? |
| Trajectory interaction: child vs trigram | effort=Syllables: pkg | gee_gamma_log | fit | 7335 | 21 | 0.2538 | Do real child and trigram total-bit trajectories diverge over age when syllables: pkg is controlled? |
| Trajectory interaction: child vs trigram | effort=Phonemes | gee_gamma_log | fit | 7335 | 21 | 0.2716 | Do real child and trigram total-bit trajectories diverge over age when phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Alex] | -3.321 | 0.1544 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Anne] | -5.365 | 0.2141 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Aran] | -4.786 | 0.1953 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Becky] | -5.3 | 0.178 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Carl] | -3.255 | 0.2396 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Dominic] | -3.551 | 0.2014 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Ethan] | -4.195 | 0.2827 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Eve] | -2.29 | 0.327 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Gail] | -3.855 | 0.1903 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Joel] | -4.272 | 0.1886 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.John] | -2.902 | 0.1998 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Lily] | -5.667 | 0.1568 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Liz] | -4.378 | 0.2063 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Naima] | -3.925 | 0.2948 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Nicole] | -3.451 | 0.1911 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Ruth] | -2.753 | 0.191 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Sarah] | -0.8663 | 0.1232 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Violet] | -5.281 | 0.1667 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.Warren] | -3.425 | 0.2155 | <.001 |
| Child minus trigram: total bits | effort=Words | C(child_id)[T.William] | -4.514 | 0.1762 | <.001 |
| Child minus trigram: total bits | effort=Words | age_months_z | -0.892 | 0.1681 | <.001 |
| Child minus trigram: total bits | effort=Words | nb_words_z | -6.767 | 0.2654 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Alex] | -3.129 | 0.1715 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Anne] | -5.045 | 0.235 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Aran] | -4.735 | 0.2119 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Becky] | -4.978 | 0.1959 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Carl] | -2.869 | 0.2601 | <.001 |
| Child minus trigram: total bits | effort=Morphemes | C(child_id)[T.Dominic] | -3.347 | 0.2231 | <.001 |


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

![Child caretaker dashboard](../figs/utterance_information_research_model_zoo/child_vs_caretaker_dashboard.png)

Model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Child vs caretaker: total bits | effort=Words | gee_gamma_log | fit | 10075 | 21 | 0.1359 | Do child and caretaker total-bit trajectories differ after controlling words? |
| Child vs caretaker: total bits | effort=Morphemes | gee_gamma_log | fit | 10075 | 21 | 0.1649 | Do child and caretaker total-bit trajectories differ after controlling morphemes? |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 10075 | 21 | 0.1178 | Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg? |
| Child vs caretaker: total bits | effort=Syllables: pkg | gee_gamma_log | fit | 10075 | 21 | 0.1329 | Do child and caretaker total-bit trajectories differ after controlling syllables: pkg? |
| Child vs caretaker: total bits | effort=Phonemes | gee_gamma_log | fit | 10075 | 21 | 0.08581 | Do child and caretaker total-bit trajectories differ after controlling phonemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Child vs caretaker: total bits | effort=Words | C(speaker_group)[T.child] | -0.1164 | 0.01813 | <.001 |
| Child vs caretaker: total bits | effort=Words | age_months_z | 0.00237 | 0.008268 | 0.774 |
| Child vs caretaker: total bits | effort=Words | age_months_z:C(speaker_group)[T.child] | -0.04051 | 0.01374 | 0.003 |
| Child vs caretaker: total bits | effort=Words | nb_words_z | 0.4482 | 0.01476 | <.001 |
| Child vs caretaker: total bits | effort=Morphemes | C(speaker_group)[T.child] | -0.1139 | 0.01909 | <.001 |
| Child vs caretaker: total bits | effort=Morphemes | age_months_z | 0.00424 | 0.00806 | 0.599 |
| Child vs caretaker: total bits | effort=Morphemes | age_months_z:C(speaker_group)[T.child] | -0.04832 | 0.01412 | <.001 |
| Child vs caretaker: total bits | effort=Morphemes | nb_morphemes_z | 0.4493 | 0.01485 | <.001 |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | C(speaker_group)[T.child] | -0.119 | 0.01616 | <.001 |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | age_months_z | 0.004019 | 0.008309 | 0.629 |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | age_months_z:C(speaker_group)[T.child] | -0.03309 | 0.01293 | 0.010 |
| Child vs caretaker: total bits | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.4643 | 0.01569 | <.001 |
| Child vs caretaker: total bits | effort=Syllables: pkg | C(speaker_group)[T.child] | -0.1197 | 0.01612 | <.001 |
| Child vs caretaker: total bits | effort=Syllables: pkg | age_months_z | 0.004951 | 0.008147 | 0.543 |
| Child vs caretaker: total bits | effort=Syllables: pkg | age_months_z:C(speaker_group)[T.child] | -0.02977 | 0.01294 | 0.021 |
| Child vs caretaker: total bits | effort=Syllables: pkg | nb_syllables_pkg_z | 0.4575 | 0.01605 | <.001 |
| Child vs caretaker: total bits | effort=Phonemes | C(speaker_group)[T.child] | -0.1186 | 0.01713 | <.001 |
| Child vs caretaker: total bits | effort=Phonemes | age_months_z | 0.00183 | 0.007522 | 0.808 |
| Child vs caretaker: total bits | effort=Phonemes | age_months_z:C(speaker_group)[T.child] | -0.03036 | 0.01246 | 0.015 |
| Child vs caretaker: total bits | effort=Phonemes | nb_phonemes_z | 0.4696 | 0.01681 | <.001 |

## Context Predictability And Effort

**Question.** Given the preceding caretaker context, do children modulate their
production effort or information density? This is the analysis family closest
to the proposal that contextual predictability should help predict child
utterance length.

**How to read this plot.** The x-axis is next-token entropy of the preceding
caretaker context. A rising line would mean children use more words when the
model sees the context as less predictive.

![Context entropy and child words](../figs/utterance_information_research_model_zoo/context_entropy_child_words.png)

**How to read this plot.** This asks whether information density, not just
utterance length, varies with context entropy. A rising line means higher bits
per word in less predictable contexts.

![Context entropy and bits per word](../figs/utterance_information_research_model_zoo/context_entropy_bits_per_word.png)

**How to read this plot.** Lines compare child word count after different broad
caretaker context types. This is a conversational-control check: wh-questions,
yes/no questions, other questions, and non-questions can invite different
response lengths.

![Question type effort](../figs/utterance_information_research_model_zoo/question_type_child_words_by_age.png)

Context-model rows:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Morphemes | gee_poisson | fit | 15342 | 21 | 0.1014 | Is child morphemes lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Phonemes | gee_poisson | fit | 15342 | 21 | 0.07952 | Is child phonemes lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08628 | Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.0811 | Is child syllables: pkg lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Words | gee_poisson | fit | 15342 | 21 | 0.1013 | Is child words lower when the model assigns high probability to the most likely next token? |
| Z3 Effort from context entropy | effort=Morphemes | gee_poisson | fit | 15342 | 21 | 0.1013 | Do children produce more morphemes after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Phonemes | gee_poisson | fit | 15342 | 21 | 0.07936 | Do children produce more phonemes after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08609 | Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.08093 | Do children produce more syllables: pkg after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Words | gee_poisson | fit | 15342 | 21 | 0.1012 | Do children produce more words after more uncertain caretaker contexts? |
| Z4 Information from context entropy | effort=Morphemes | gee_gamma_log | fit | 15342 | 21 | 0.2433 | Is total child information related to context entropy after morphemes is controlled? |
| Z4 Information from context entropy | effort=Phonemes | gee_gamma_log | fit | 15342 | 21 | 0.1679 | Is total child information related to context entropy after phonemes is controlled? |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 15342 | 21 | 0.2055 | Is total child information related to context entropy after syllables: cmu/pkg is controlled? |
| Z4 Information from context entropy | effort=Syllables: pkg | gee_gamma_log | fit | 15342 | 21 | 0.2184 | Is total child information related to context entropy after syllables: pkg is controlled? |
| Z4 Information from context entropy | effort=Words | gee_gamma_log | fit | 15342 | 21 | 0.161 | Is total child information related to context entropy after words is controlled? |
| Z5 Context window sensitivity | unit=Morphemes | gee_gaussian | fit | 15342 | 21 | 0.3902 | Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Phonemes | gee_gaussian | fit | 15342 | 21 | 0.4753 | Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | gee_gaussian | fit | 15342 | 21 | 0.4064 | Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Syllables: pkg | gee_gaussian | fit | 15342 | 21 | 0.3587 | Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Words | gee_gaussian | fit | 15342 | 21 | 0.3385 | Does the age trajectory of information per words change across k1/k2/k3 scoring windows? |

Context-model key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Words | age_months_z | 0.2351 | 0.02375 | <.001 |
| Z3 Effort from context entropy | effort=Words | context_entropy_bits_z | 0.007438 | 0.007524 | 0.323 |
| Z3 Effort from context entropy | effort=Words | age_months_z:context_entropy_bits_z | 0.003663 | 0.006604 | 0.579 |
| Z3 Effort from context entropy | effort=Morphemes | age_months_z | 0.2471 | 0.02469 | <.001 |
| Z3 Effort from context entropy | effort=Morphemes | context_entropy_bits_z | 0.007266 | 0.007799 | 0.352 |
| Z3 Effort from context entropy | effort=Morphemes | age_months_z:context_entropy_bits_z | 0.001546 | 0.007373 | 0.834 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | age_months_z | 0.2145 | 0.02357 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | context_entropy_bits_z | 0.008152 | 0.008434 | 0.334 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | age_months_z:context_entropy_bits_z | 0.005645 | 0.006913 | 0.414 |
| Z3 Effort from context entropy | effort=Syllables: pkg | age_months_z | 0.2136 | 0.02298 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: pkg | context_entropy_bits_z | 0.009024 | 0.008338 | 0.279 |
| Z3 Effort from context entropy | effort=Syllables: pkg | age_months_z:context_entropy_bits_z | 0.004487 | 0.006893 | 0.515 |
| Z3 Effort from context entropy | effort=Phonemes | age_months_z | 0.2164 | 0.02318 | <.001 |
| Z3 Effort from context entropy | effort=Phonemes | context_entropy_bits_z | 0.009404 | 0.007451 | 0.207 |
| Z3 Effort from context entropy | effort=Phonemes | age_months_z:context_entropy_bits_z | 0.003942 | 0.006636 | 0.553 |
| Z4 Information from context entropy | effort=Words | age_months_z | -0.03453 | 0.01273 | 0.007 |
| Z4 Information from context entropy | effort=Words | context_entropy_bits_z | -0.006685 | 0.004108 | 0.104 |
| Z4 Information from context entropy | effort=Words | age_months_z:context_entropy_bits_z | 0.009242 | 0.002554 | <.001 |
| Z4 Information from context entropy | effort=Words | nb_words_z | 0.4113 | 0.01252 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | age_months_z | -0.04021 | 0.01454 | 0.006 |
| Z4 Information from context entropy | effort=Morphemes | context_entropy_bits_z | -0.005698 | 0.004166 | 0.171 |
| Z4 Information from context entropy | effort=Morphemes | age_months_z:context_entropy_bits_z | 0.01121 | 0.002546 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | age_months_z | -0.02269 | 0.01127 | 0.044 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | context_entropy_bits_z | -0.006615 | 0.004131 | 0.109 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | age_months_z:context_entropy_bits_z | 0.008573 | 0.002258 | <.001 |
| Z4 Information from context entropy | effort=Syllables: pkg | age_months_z | -0.01959 | 0.01115 | 0.079 |
| Z4 Information from context entropy | effort=Syllables: pkg | context_entropy_bits_z | -0.006926 | 0.003849 | 0.072 |
| Z4 Information from context entropy | effort=Syllables: pkg | age_months_z:context_entropy_bits_z | 0.009164 | 0.002262 | <.001 |
| Z4 Information from context entropy | effort=Phonemes | age_months_z | -0.02553 | 0.01153 | 0.027 |
| Z4 Information from context entropy | effort=Phonemes | context_entropy_bits_z | -0.006698 | 0.004023 | 0.096 |
| Z4 Information from context entropy | effort=Phonemes | age_months_z:context_entropy_bits_z | 0.009372 | 0.002538 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z | -0.7024 | 0.1211 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k2] | 0.3251 | 0.07897 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k3] | 0.4541 | 0.07391 | <.001 |
| Z5 Context window sensitivity | unit=Words | log_nb_words | -4.759 | 0.2063 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z | -0.6761 | 0.1099 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k2] | 0.3061 | 0.08208 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k3] | 0.4511 | 0.07041 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z | -0.3634 | 0.0791 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k2] | 0.2549 | 0.07061 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k3] | 0.3612 | 0.07187 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z | -0.3247 | 0.09531 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k2] | 0.2205 | 0.06706 | 0.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k3] | 0.3404 | 0.07184 | <.001 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z | -0.01887 | 0.03974 | 0.635 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k2] | 0.1091 | 0.03525 | 0.002 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k3] | 0.1976 | 0.03411 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z | 0.2211 | 0.02566 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.other question] | 0.03033 | 0.01022 | 0.003 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.wh-question] | 0.03774 | 0.01602 | 0.018 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.yes/no question] | 0.001659 | 0.02465 | 0.946 |
| Z6 Question-type effort | effort=Morphemes | age_months_z | 0.2304 | 0.0262 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.other question] | 0.03442 | 0.009922 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.wh-question] | 0.04586 | 0.01622 | 0.005 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.009962 | 0.02565 | 0.698 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z | 0.198 | 0.02498 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.other question] | 0.03582 | 0.01069 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.04145 | 0.01788 | 0.020 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.005949 | 0.02542 | 0.815 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z | 0.1971 | 0.02418 | <.001 |

Question-type counts:

| age_bin | context_question_type | rows |
| --- | --- | --- |
| 006-023 | not question | 1487 |
| 006-023 | other question | 1279 |
| 006-023 | wh-question | 248 |
| 006-023 | yes/no question | 301 |
| 024-029 | not question | 1890 |
| 024-029 | other question | 1666 |
| 024-029 | wh-question | 311 |
| 024-029 | yes/no question | 393 |
| 030-035 | not question | 1876 |
| 030-035 | other question | 1553 |
| 030-035 | wh-question | 250 |
| 030-035 | yes/no question | 331 |
| 036-041 | not question | 792 |
| 036-041 | other question | 585 |
| 036-041 | wh-question | 99 |
| 036-041 | yes/no question | 84 |
| 042-047 | not question | 489 |
| 042-047 | other question | 345 |
| 042-047 | wh-question | 85 |
| 042-047 | yes/no question | 56 |
| 048-053 | not question | 313 |
| 048-053 | other question | 242 |
| 048-053 | wh-question | 64 |
| 048-053 | yes/no question | 21 |
| 054-059 | not question | 180 |
| 054-059 | other question | 134 |
| 054-059 | wh-question | 45 |
| 054-059 | yes/no question | 31 |
| 060-065 | not question | 96 |
| 060-065 | other question | 58 |
| 060-065 | wh-question | 33 |
| 060-065 | yes/no question | 5 |

## Expanded Model Cards

These are broader models that test nonlinear age, context-window sensitivity,
phonological efficiency, baseline differences, child/caretaker contrasts, and
context-predictability logic. They are for triage, not final reporting.

## Z1: Information With Child Identity

**Question family.** Does total utterance information change with age after child identity and one effort measure are controlled?

**Why it is in the expanded atlas.** This is a sibling of M2 but kept in the expanded report because it repeats the child-identity analysis across every effort measure.

**How to read this plot.** The line is a visual age regression for real child total bits; dots are age-bin means. The fitted model also controls word count and child identity.

![Z1 plot](../figs/utterance_information_research_model_zoo/z1_information_child_fe_age.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 0 estimates are positive and 5 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 | effort: Words | ols_cluster | fit | 5560 | 21 | 0.6327 |
| Z1 | effort: Morphemes | ols_cluster | fit | 5560 | 21 | 0.6228 |
| Z1 | effort: Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.6545 |
| Z1 | effort: Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.6408 |
| Z1 | effort: Phonemes | ols_cluster | fit | 5560 | 21 | 0.6596 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Words | age_months_z | -0.8984 | 0.3166 | 0.005 |
| Z1 Information | child FE | effort=Words | nb_words_z | 12.91 | 0.3244 | <.001 |
| Z1 Information | child FE | effort=Morphemes | age_months_z | -1.035 | 0.3726 | 0.005 |
| Z1 Information | child FE | effort=Morphemes | nb_morphemes_z | 12.85 | 0.3558 | <.001 |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | age_months_z | -0.5158 | 0.2671 | 0.053 |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 13.09 | 0.3187 | <.001 |
| Z1 Information | child FE | effort=Syllables: pkg | age_months_z | -0.4091 | 0.2895 | 0.158 |
| Z1 Information | child FE | effort=Syllables: pkg | nb_syllables_pkg_z | 12.87 | 0.3705 | <.001 |
| Z1 Information | child FE | effort=Phonemes | age_months_z | -0.5649 | 0.2509 | 0.024 |
| Z1 Information | child FE | effort=Phonemes | nb_phonemes_z | 13.13 | 0.3823 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z1 coefficients](../figs/utterance_information_research_model_zoo/z1_family_coefficients.png)


### Z1.1: effort: Words

**Question asked by this subvariant.** At the same words level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_words_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Words | ols_cluster | fit | 5560 | 21 | 0.6327 | At the same words level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Words | age_months_z | -0.8984 | 0.3166 | 0.005 |
| Z1 Information | child FE | effort=Words | nb_words_z | 12.91 | 0.3244 | <.001 |
### Z1.2: effort: Morphemes

**Question asked by this subvariant.** At the same morphemes level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_morphemes_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Morphemes | ols_cluster | fit | 5560 | 21 | 0.6228 | At the same morphemes level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Morphemes | age_months_z | -1.035 | 0.3726 | 0.005 |
| Z1 Information | child FE | effort=Morphemes | nb_morphemes_z | 12.85 | 0.3558 | <.001 |
### Z1.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** At the same syllables: cmu/pkg level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_syllables_cmu_or_pkg_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.6545 | At the same syllables: cmu/pkg level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | age_months_z | -0.5158 | 0.2671 | 0.053 |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 13.09 | 0.3187 | <.001 |
### Z1.4: effort: Syllables: pkg

**Question asked by this subvariant.** At the same syllables: pkg level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_syllables_pkg_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.6408 | At the same syllables: pkg level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Syllables: pkg | age_months_z | -0.4091 | 0.2895 | 0.158 |
| Z1 Information | child FE | effort=Syllables: pkg | nb_syllables_pkg_z | 12.87 | 0.3705 | <.001 |
### Z1.5: effort: Phonemes

**Question asked by this subvariant.** At the same phonemes level, does child total information change with age after child identity is controlled?

**Formula.** `sum_bits ~ age_months_z + nb_phonemes_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Phonemes | ols_cluster | fit | 5560 | 21 | 0.6596 | At the same phonemes level, does child total information change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Phonemes | age_months_z | -0.5649 | 0.2509 | 0.024 |
| Z1 Information | child FE | effort=Phonemes | nb_phonemes_z | 13.13 | 0.3823 | <.001 |


## Z2: Nonlinear Information Density

**Question family.** Does information per unit of effort follow a curved developmental trajectory?

**Why it is in the expanded atlas.** M1-M4 use simple linear age terms; this asks whether a curved developmental trajectory is needed.

**How to read this plot.** The curve is a quadratic regression of bits per word over age. A curve rather than a straight line suggests nonlinear development.

![Z2 plot](../figs/utterance_information_research_model_zoo/z2_nonlinear_information_density.png)

**Compact result.** 5/5 subvariants fit cleanly. For `I(age_months_z ** 2)`, 4 estimates are positive and 1 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 | unit: Words | ols_cluster | fit | 5560 | 21 | 0.2741 |
| Z2 | unit: Morphemes | ols_cluster | fit | 5560 | 21 | 0.3275 |
| Z2 | unit: Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.3299 |
| Z2 | unit: Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.2959 |
| Z2 | unit: Phonemes | ols_cluster | fit | 5560 | 21 | 0.4168 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Words | age_months_z | -0.6511 | 0.2394 | 0.007 |
| Z2 Information density | nonlinear age | unit=Words | I(age_months_z ** 2) | 0.1582 | 0.08225 | 0.054 |
| Z2 Information density | nonlinear age | unit=Words | log_nb_words | -4.195 | 0.1867 | <.001 |
| Z2 Information density | nonlinear age | unit=Morphemes | age_months_z | -0.6281 | 0.2309 | 0.007 |
| Z2 Information density | nonlinear age | unit=Morphemes | I(age_months_z ** 2) | 0.138 | 0.07707 | 0.073 |
| Z2 Information density | nonlinear age | unit=Morphemes | log_nb_morphemes | -4.323 | 0.1818 | <.001 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | age_months_z | -0.199 | 0.1873 | 0.288 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | I(age_months_z ** 2) | 0.03156 | 0.07136 | 0.658 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | log_nb_syllables | -3.682 | 0.1565 | <.001 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | age_months_z | -0.1831 | 0.1948 | 0.347 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | I(age_months_z ** 2) | 0.02525 | 0.07186 | 0.725 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | log_nb_syllables | -3.559 | 0.1444 | <.001 |
| Z2 Information density | nonlinear age | unit=Phonemes | age_months_z | 0.07736 | 0.05956 | 0.194 |
| Z2 Information density | nonlinear age | unit=Phonemes | I(age_months_z ** 2) | -0.03386 | 0.0261 | 0.195 |
| Z2 Information density | nonlinear age | unit=Phonemes | log_nb_phonemes | -1.901 | 0.08463 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z2 coefficients](../figs/utterance_information_research_model_zoo/z2_family_coefficients.png)


### Z2.1: unit: Words

**Question asked by this subvariant.** Does information per words follow a nonlinear developmental trajectory?

**Formula.** `bits_per_word ~ age_months_z + I(age_months_z ** 2) + log_nb_words + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Words | ols_cluster | fit | 5560 | 21 | 0.2741 | Does information per words follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Words | age_months_z | -0.6511 | 0.2394 | 0.007 |
| Z2 Information density | nonlinear age | unit=Words | I(age_months_z ** 2) | 0.1582 | 0.08225 | 0.054 |
| Z2 Information density | nonlinear age | unit=Words | log_nb_words | -4.195 | 0.1867 | <.001 |
### Z2.2: unit: Morphemes

**Question asked by this subvariant.** Does information per morphemes follow a nonlinear developmental trajectory?

**Formula.** `bits_per_morpheme ~ age_months_z + I(age_months_z ** 2) + log_nb_morphemes + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Morphemes | ols_cluster | fit | 5560 | 21 | 0.3275 | Does information per morphemes follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Morphemes | age_months_z | -0.6281 | 0.2309 | 0.007 |
| Z2 Information density | nonlinear age | unit=Morphemes | I(age_months_z ** 2) | 0.138 | 0.07707 | 0.073 |
| Z2 Information density | nonlinear age | unit=Morphemes | log_nb_morphemes | -4.323 | 0.1818 | <.001 |
### Z2.3: unit: Syllables: CMU/pkg

**Question asked by this subvariant.** Does information per syllables: cmu/pkg follow a nonlinear developmental trajectory?

**Formula.** `bits_per_syllable_cmu_or_pkg ~ age_months_z + I(age_months_z ** 2) + log_nb_syllables + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.3299 | Does information per syllables: cmu/pkg follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | age_months_z | -0.199 | 0.1873 | 0.288 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | I(age_months_z ** 2) | 0.03156 | 0.07136 | 0.658 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | log_nb_syllables | -3.682 | 0.1565 | <.001 |
### Z2.4: unit: Syllables: pkg

**Question asked by this subvariant.** Does information per syllables: pkg follow a nonlinear developmental trajectory?

**Formula.** `bits_per_syllable_pkg ~ age_months_z + I(age_months_z ** 2) + log_nb_syllables + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.2959 | Does information per syllables: pkg follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | age_months_z | -0.1831 | 0.1948 | 0.347 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | I(age_months_z ** 2) | 0.02525 | 0.07186 | 0.725 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | log_nb_syllables | -3.559 | 0.1444 | <.001 |
### Z2.5: unit: Phonemes

**Question asked by this subvariant.** Does information per phonemes follow a nonlinear developmental trajectory?

**Formula.** `bits_per_phoneme ~ age_months_z + I(age_months_z ** 2) + log_nb_phonemes + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Phonemes | ols_cluster | fit | 5560 | 21 | 0.4168 | Does information per phonemes follow a nonlinear developmental trajectory? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z2 Information density | nonlinear age | unit=Phonemes | age_months_z | 0.07736 | 0.05956 | 0.194 |
| Z2 Information density | nonlinear age | unit=Phonemes | I(age_months_z ** 2) | -0.03386 | 0.0261 | 0.195 |
| Z2 Information density | nonlinear age | unit=Phonemes | log_nb_phonemes | -1.901 | 0.08463 | <.001 |


## Z3: Context Entropy Predicting Effort

**Question family.** Do children produce more effortful utterances after less predictable caretaker contexts?

**Why it is in the expanded atlas.** M4 introduces context entropy; this expanded version adds question type and context length in a GEE effort model.

**How to read this plot.** The regression line shows whether child word count rises or falls as next-token context entropy increases.

![Z3 plot](../figs/utterance_information_research_model_zoo/z3_context_entropy_effort.png)

**Compact result.** 5/5 subvariants fit cleanly. For `context_entropy_bits_z`, 5 estimates are positive and 0 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 | effort: Words | gee_poisson | fit | 15342 | 21 | 0.1012 |
| Z3 | effort: Morphemes | gee_poisson | fit | 15342 | 21 | 0.1013 |
| Z3 | effort: Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08609 |
| Z3 | effort: Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.08093 |
| Z3 | effort: Phonemes | gee_poisson | fit | 15342 | 21 | 0.07936 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Words | C(context_question_type)[T.other question] | -0.0938 | 0.02034 | <.001 |
| Z3 Effort from context entropy | effort=Words | C(context_question_type)[T.wh-question] | -0.05521 | 0.02792 | 0.048 |
| Z3 Effort from context entropy | effort=Words | C(context_question_type)[T.yes/no question] | -0.1219 | 0.02233 | <.001 |
| Z3 Effort from context entropy | effort=Words | age_months_z | 0.2351 | 0.02375 | <.001 |
| Z3 Effort from context entropy | effort=Words | context_entropy_bits_z | 0.007438 | 0.007524 | 0.323 |
| Z3 Effort from context entropy | effort=Words | age_months_z:context_entropy_bits_z | 0.003663 | 0.006604 | 0.579 |
| Z3 Effort from context entropy | effort=Words | log_context_words_plus1 | 0.02329 | 0.009889 | 0.019 |
| Z3 Effort from context entropy | effort=Morphemes | C(context_question_type)[T.other question] | -0.0897 | 0.01884 | <.001 |
| Z3 Effort from context entropy | effort=Morphemes | C(context_question_type)[T.wh-question] | -0.04965 | 0.02849 | 0.081 |
| Z3 Effort from context entropy | effort=Morphemes | C(context_question_type)[T.yes/no question] | -0.117 | 0.01953 | <.001 |
| Z3 Effort from context entropy | effort=Morphemes | age_months_z | 0.2471 | 0.02469 | <.001 |
| Z3 Effort from context entropy | effort=Morphemes | context_entropy_bits_z | 0.007266 | 0.007799 | 0.352 |
| Z3 Effort from context entropy | effort=Morphemes | age_months_z:context_entropy_bits_z | 0.001546 | 0.007373 | 0.834 |
| Z3 Effort from context entropy | effort=Morphemes | log_context_words_plus1 | 0.02254 | 0.01027 | 0.028 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | C(context_question_type)[T.other question] | -0.08732 | 0.01989 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | C(context_question_type)[T.wh-question] | -0.06117 | 0.02746 | 0.026 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | C(context_question_type)[T.yes/no question] | -0.1246 | 0.02255 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | age_months_z | 0.2145 | 0.02357 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | context_entropy_bits_z | 0.008152 | 0.008434 | 0.334 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | age_months_z:context_entropy_bits_z | 0.005645 | 0.006913 | 0.414 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | log_context_words_plus1 | 0.01253 | 0.009438 | 0.184 |
| Z3 Effort from context entropy | effort=Syllables: pkg | C(context_question_type)[T.other question] | -0.09373 | 0.01955 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: pkg | C(context_question_type)[T.wh-question] | -0.06471 | 0.02625 | 0.014 |
| Z3 Effort from context entropy | effort=Syllables: pkg | C(context_question_type)[T.yes/no question] | -0.1317 | 0.02366 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: pkg | age_months_z | 0.2136 | 0.02298 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z3 coefficients](../figs/utterance_information_research_model_zoo/z3_family_coefficients.png)


### Z3.1: effort: Words

**Question asked by this subvariant.** Do children produce more words after more uncertain caretaker contexts?

**Formula.** `nb_words ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Words | gee_poisson | fit | 15342 | 21 | 0.1012 | Do children produce more words after more uncertain caretaker contexts? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Words | C(context_question_type)[T.other question] | -0.0938 | 0.02034 | <.001 |
| Z3 Effort from context entropy | effort=Words | C(context_question_type)[T.wh-question] | -0.05521 | 0.02792 | 0.048 |
| Z3 Effort from context entropy | effort=Words | C(context_question_type)[T.yes/no question] | -0.1219 | 0.02233 | <.001 |
| Z3 Effort from context entropy | effort=Words | age_months_z | 0.2351 | 0.02375 | <.001 |
| Z3 Effort from context entropy | effort=Words | context_entropy_bits_z | 0.007438 | 0.007524 | 0.323 |
| Z3 Effort from context entropy | effort=Words | age_months_z:context_entropy_bits_z | 0.003663 | 0.006604 | 0.579 |
| Z3 Effort from context entropy | effort=Words | log_context_words_plus1 | 0.02329 | 0.009889 | 0.019 |
### Z3.2: effort: Morphemes

**Question asked by this subvariant.** Do children produce more morphemes after more uncertain caretaker contexts?

**Formula.** `nb_morphemes ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Morphemes | gee_poisson | fit | 15342 | 21 | 0.1013 | Do children produce more morphemes after more uncertain caretaker contexts? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Morphemes | C(context_question_type)[T.other question] | -0.0897 | 0.01884 | <.001 |
| Z3 Effort from context entropy | effort=Morphemes | C(context_question_type)[T.wh-question] | -0.04965 | 0.02849 | 0.081 |
| Z3 Effort from context entropy | effort=Morphemes | C(context_question_type)[T.yes/no question] | -0.117 | 0.01953 | <.001 |
| Z3 Effort from context entropy | effort=Morphemes | age_months_z | 0.2471 | 0.02469 | <.001 |
| Z3 Effort from context entropy | effort=Morphemes | context_entropy_bits_z | 0.007266 | 0.007799 | 0.352 |
| Z3 Effort from context entropy | effort=Morphemes | age_months_z:context_entropy_bits_z | 0.001546 | 0.007373 | 0.834 |
| Z3 Effort from context entropy | effort=Morphemes | log_context_words_plus1 | 0.02254 | 0.01027 | 0.028 |
### Z3.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts?

**Formula.** `nb_syllables_cmu_or_pkg ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08609 | Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | C(context_question_type)[T.other question] | -0.08732 | 0.01989 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | C(context_question_type)[T.wh-question] | -0.06117 | 0.02746 | 0.026 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | C(context_question_type)[T.yes/no question] | -0.1246 | 0.02255 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | age_months_z | 0.2145 | 0.02357 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | context_entropy_bits_z | 0.008152 | 0.008434 | 0.334 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | age_months_z:context_entropy_bits_z | 0.005645 | 0.006913 | 0.414 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | log_context_words_plus1 | 0.01253 | 0.009438 | 0.184 |
### Z3.4: effort: Syllables: pkg

**Question asked by this subvariant.** Do children produce more syllables: pkg after more uncertain caretaker contexts?

**Formula.** `nb_syllables_pkg ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.08093 | Do children produce more syllables: pkg after more uncertain caretaker contexts? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Syllables: pkg | C(context_question_type)[T.other question] | -0.09373 | 0.01955 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: pkg | C(context_question_type)[T.wh-question] | -0.06471 | 0.02625 | 0.014 |
| Z3 Effort from context entropy | effort=Syllables: pkg | C(context_question_type)[T.yes/no question] | -0.1317 | 0.02366 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: pkg | age_months_z | 0.2136 | 0.02298 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: pkg | context_entropy_bits_z | 0.009024 | 0.008338 | 0.279 |
| Z3 Effort from context entropy | effort=Syllables: pkg | age_months_z:context_entropy_bits_z | 0.004487 | 0.006893 | 0.515 |
| Z3 Effort from context entropy | effort=Syllables: pkg | log_context_words_plus1 | 0.01023 | 0.00971 | 0.292 |
### Z3.5: effort: Phonemes

**Question asked by this subvariant.** Do children produce more phonemes after more uncertain caretaker contexts?

**Formula.** `nb_phonemes ~ age_months_z * context_entropy_bits_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Phonemes | gee_poisson | fit | 15342 | 21 | 0.07936 | Do children produce more phonemes after more uncertain caretaker contexts? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z3 Effort from context entropy | effort=Phonemes | C(context_question_type)[T.other question] | -0.08796 | 0.02031 | <.001 |
| Z3 Effort from context entropy | effort=Phonemes | C(context_question_type)[T.wh-question] | -0.04758 | 0.02837 | 0.094 |
| Z3 Effort from context entropy | effort=Phonemes | C(context_question_type)[T.yes/no question] | -0.1228 | 0.02283 | <.001 |
| Z3 Effort from context entropy | effort=Phonemes | age_months_z | 0.2164 | 0.02318 | <.001 |
| Z3 Effort from context entropy | effort=Phonemes | context_entropy_bits_z | 0.009404 | 0.007451 | 0.207 |
| Z3 Effort from context entropy | effort=Phonemes | age_months_z:context_entropy_bits_z | 0.003942 | 0.006636 | 0.553 |
| Z3 Effort from context entropy | effort=Phonemes | log_context_words_plus1 | 0.006142 | 0.009283 | 0.508 |


## Z4: Context Entropy Predicting Information

**Question family.** Does contextual uncertainty predict the information carried by an utterance after effort is controlled?

**Why it is in the expanded atlas.** This tests context entropy as a direct predictor of total utterance information while controlling one effort measure at a time.

**How to read this plot.** The regression line is a descriptive view of total bits across contexts with lower versus higher next-token entropy. The fitted subvariants below add explicit effort controls.

![Z4 plot](../figs/utterance_information_research_model_zoo/z4_context_entropy_density.png)

**Compact result.** 5/5 subvariants fit cleanly. For `context_entropy_bits_z`, 0 estimates are positive and 5 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 | effort: Words | gee_gamma_log | fit | 15342 | 21 | 0.161 |
| Z4 | effort: Morphemes | gee_gamma_log | fit | 15342 | 21 | 0.2433 |
| Z4 | effort: Syllables: CMU/pkg | gee_gamma_log | fit | 15342 | 21 | 0.2055 |
| Z4 | effort: Syllables: pkg | gee_gamma_log | fit | 15342 | 21 | 0.2184 |
| Z4 | effort: Phonemes | gee_gamma_log | fit | 15342 | 21 | 0.1679 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Words | C(context_k)[T.k2] | -0.09103 | 0.01014 | <.001 |
| Z4 Information from context entropy | effort=Words | C(context_k)[T.k3] | -0.1381 | 0.01202 | <.001 |
| Z4 Information from context entropy | effort=Words | age_months_z | -0.03453 | 0.01273 | 0.007 |
| Z4 Information from context entropy | effort=Words | context_entropy_bits_z | -0.006685 | 0.004108 | 0.104 |
| Z4 Information from context entropy | effort=Words | age_months_z:context_entropy_bits_z | 0.009242 | 0.002554 | <.001 |
| Z4 Information from context entropy | effort=Words | nb_words_z | 0.4113 | 0.01252 | <.001 |
| Z4 Information from context entropy | effort=Words | log_context_words_plus1 | -0.01987 | 0.007861 | 0.011 |
| Z4 Information from context entropy | effort=Morphemes | C(context_k)[T.k2] | -0.09155 | 0.009813 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | C(context_k)[T.k3] | -0.1371 | 0.0121 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | age_months_z | -0.04021 | 0.01454 | 0.006 |
| Z4 Information from context entropy | effort=Morphemes | context_entropy_bits_z | -0.005698 | 0.004166 | 0.171 |
| Z4 Information from context entropy | effort=Morphemes | age_months_z:context_entropy_bits_z | 0.01121 | 0.002546 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | nb_morphemes_z | 0.4115 | 0.0128 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | log_context_words_plus1 | -0.02017 | 0.007444 | 0.007 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | C(context_k)[T.k2] | -0.09472 | 0.00854 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | C(context_k)[T.k3] | -0.1429 | 0.01151 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | age_months_z | -0.02269 | 0.01127 | 0.044 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | context_entropy_bits_z | -0.006615 | 0.004131 | 0.109 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | age_months_z:context_entropy_bits_z | 0.008573 | 0.002258 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.4242 | 0.0139 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | log_context_words_plus1 | -0.01421 | 0.007668 | 0.064 |
| Z4 Information from context entropy | effort=Syllables: pkg | C(context_k)[T.k2] | -0.09636 | 0.00864 | <.001 |
| Z4 Information from context entropy | effort=Syllables: pkg | C(context_k)[T.k3] | -0.1466 | 0.01097 | <.001 |
| Z4 Information from context entropy | effort=Syllables: pkg | age_months_z | -0.01959 | 0.01115 | 0.079 |
| Z4 Information from context entropy | effort=Syllables: pkg | context_entropy_bits_z | -0.006926 | 0.003849 | 0.072 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z4 coefficients](../figs/utterance_information_research_model_zoo/z4_family_coefficients.png)


### Z4.1: effort: Words

**Question asked by this subvariant.** Is total child information related to context entropy after words is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_words_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Words | gee_gamma_log | fit | 15342 | 21 | 0.161 | Is total child information related to context entropy after words is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Words | C(context_k)[T.k2] | -0.09103 | 0.01014 | <.001 |
| Z4 Information from context entropy | effort=Words | C(context_k)[T.k3] | -0.1381 | 0.01202 | <.001 |
| Z4 Information from context entropy | effort=Words | age_months_z | -0.03453 | 0.01273 | 0.007 |
| Z4 Information from context entropy | effort=Words | context_entropy_bits_z | -0.006685 | 0.004108 | 0.104 |
| Z4 Information from context entropy | effort=Words | age_months_z:context_entropy_bits_z | 0.009242 | 0.002554 | <.001 |
| Z4 Information from context entropy | effort=Words | nb_words_z | 0.4113 | 0.01252 | <.001 |
| Z4 Information from context entropy | effort=Words | log_context_words_plus1 | -0.01987 | 0.007861 | 0.011 |
### Z4.2: effort: Morphemes

**Question asked by this subvariant.** Is total child information related to context entropy after morphemes is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_morphemes_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Morphemes | gee_gamma_log | fit | 15342 | 21 | 0.2433 | Is total child information related to context entropy after morphemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Morphemes | C(context_k)[T.k2] | -0.09155 | 0.009813 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | C(context_k)[T.k3] | -0.1371 | 0.0121 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | age_months_z | -0.04021 | 0.01454 | 0.006 |
| Z4 Information from context entropy | effort=Morphemes | context_entropy_bits_z | -0.005698 | 0.004166 | 0.171 |
| Z4 Information from context entropy | effort=Morphemes | age_months_z:context_entropy_bits_z | 0.01121 | 0.002546 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | nb_morphemes_z | 0.4115 | 0.0128 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | log_context_words_plus1 | -0.02017 | 0.007444 | 0.007 |
### Z4.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Is total child information related to context entropy after syllables: cmu/pkg is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_syllables_cmu_or_pkg_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 15342 | 21 | 0.2055 | Is total child information related to context entropy after syllables: cmu/pkg is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | C(context_k)[T.k2] | -0.09472 | 0.00854 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | C(context_k)[T.k3] | -0.1429 | 0.01151 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | age_months_z | -0.02269 | 0.01127 | 0.044 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | context_entropy_bits_z | -0.006615 | 0.004131 | 0.109 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | age_months_z:context_entropy_bits_z | 0.008573 | 0.002258 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.4242 | 0.0139 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | log_context_words_plus1 | -0.01421 | 0.007668 | 0.064 |
### Z4.4: effort: Syllables: pkg

**Question asked by this subvariant.** Is total child information related to context entropy after syllables: pkg is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_syllables_pkg_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Syllables: pkg | gee_gamma_log | fit | 15342 | 21 | 0.2184 | Is total child information related to context entropy after syllables: pkg is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Syllables: pkg | C(context_k)[T.k2] | -0.09636 | 0.00864 | <.001 |
| Z4 Information from context entropy | effort=Syllables: pkg | C(context_k)[T.k3] | -0.1466 | 0.01097 | <.001 |
| Z4 Information from context entropy | effort=Syllables: pkg | age_months_z | -0.01959 | 0.01115 | 0.079 |
| Z4 Information from context entropy | effort=Syllables: pkg | context_entropy_bits_z | -0.006926 | 0.003849 | 0.072 |
| Z4 Information from context entropy | effort=Syllables: pkg | age_months_z:context_entropy_bits_z | 0.009164 | 0.002262 | <.001 |
| Z4 Information from context entropy | effort=Syllables: pkg | nb_syllables_pkg_z | 0.4164 | 0.01282 | <.001 |
| Z4 Information from context entropy | effort=Syllables: pkg | log_context_words_plus1 | -0.0109 | 0.007282 | 0.134 |
### Z4.5: effort: Phonemes

**Question asked by this subvariant.** Is total child information related to context entropy after phonemes is controlled?

**Formula.** `sum_bits ~ age_months_z * context_entropy_bits_z + nb_phonemes_z + log_context_words_plus1 + C(context_k)`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Phonemes | gee_gamma_log | fit | 15342 | 21 | 0.1679 | Is total child information related to context entropy after phonemes is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z4 Information from context entropy | effort=Phonemes | C(context_k)[T.k2] | -0.09713 | 0.007974 | <.001 |
| Z4 Information from context entropy | effort=Phonemes | C(context_k)[T.k3] | -0.1468 | 0.01263 | <.001 |
| Z4 Information from context entropy | effort=Phonemes | age_months_z | -0.02553 | 0.01153 | 0.027 |
| Z4 Information from context entropy | effort=Phonemes | context_entropy_bits_z | -0.006698 | 0.004023 | 0.096 |
| Z4 Information from context entropy | effort=Phonemes | age_months_z:context_entropy_bits_z | 0.009372 | 0.002538 | <.001 |
| Z4 Information from context entropy | effort=Phonemes | nb_phonemes_z | 0.4295 | 0.01436 | <.001 |
| Z4 Information from context entropy | effort=Phonemes | log_context_words_plus1 | -0.008622 | 0.007719 | 0.264 |


## Z5: Scoring Context Window Sensitivity

**Question family.** Do conclusions change when surprisal is scored with k1, k2, or k3 caretaker context windows?

**Why it is in the expanded atlas.** M1-M4 use k3 as the main condition; this asks whether the age trajectory changes under k1, k2, or k3 scoring.

**How to read this plot.** Lines compare bits per word by age under k1, k2, and k3 scoring. Separation means the amount of context used for scoring matters.

![Z5 plot](../figs/utterance_information_research_model_zoo/z5_context_window_sensitivity.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 0 estimates are positive and 5 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 | unit: Words | gee_gaussian | fit | 15342 | 21 | 0.3385 |
| Z5 | unit: Morphemes | gee_gaussian | fit | 15342 | 21 | 0.3902 |
| Z5 | unit: Syllables: CMU/pkg | gee_gaussian | fit | 15342 | 21 | 0.4064 |
| Z5 | unit: Syllables: pkg | gee_gaussian | fit | 15342 | 21 | 0.3587 |
| Z5 | unit: Phonemes | gee_gaussian | fit | 15342 | 21 | 0.4753 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Words | C(context_k)[T.k2] | -1.491 | 0.1016 | <.001 |
| Z5 Context window sensitivity | unit=Words | C(context_k)[T.k3] | -2.307 | 0.1233 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z | -0.7024 | 0.1211 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k2] | 0.3251 | 0.07897 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k3] | 0.4541 | 0.07391 | <.001 |
| Z5 Context window sensitivity | unit=Words | log_nb_words | -4.759 | 0.2063 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | C(context_k)[T.k2] | -1.402 | 0.1013 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | C(context_k)[T.k3] | -2.169 | 0.1229 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z | -0.6761 | 0.1099 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k2] | 0.3061 | 0.08208 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k3] | 0.4511 | 0.07041 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | log_nb_morphemes | -4.874 | 0.1927 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | C(context_k)[T.k2] | -1.282 | 0.08727 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | C(context_k)[T.k3] | -1.938 | 0.1073 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z | -0.3634 | 0.0791 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k2] | 0.2549 | 0.07061 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k3] | 0.3612 | 0.07187 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | log_nb_syllables | -4.263 | 0.181 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | C(context_k)[T.k2] | -1.2 | 0.07072 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | C(context_k)[T.k3] | -1.858 | 0.09426 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z | -0.3247 | 0.09531 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k2] | 0.2205 | 0.06706 | 0.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k3] | 0.3404 | 0.07184 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | log_nb_syllables | -4.092 | 0.1651 | <.001 |
| Z5 Context window sensitivity | unit=Phonemes | C(context_k)[T.k2] | -0.553 | 0.04324 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z5 coefficients](../figs/utterance_information_research_model_zoo/z5_family_coefficients.png)


### Z5.1: unit: Words

**Question asked by this subvariant.** Does the age trajectory of information per words change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_word ~ age_months_z * C(context_k) + log_nb_words`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Words | gee_gaussian | fit | 15342 | 21 | 0.3385 | Does the age trajectory of information per words change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Words | C(context_k)[T.k2] | -1.491 | 0.1016 | <.001 |
| Z5 Context window sensitivity | unit=Words | C(context_k)[T.k3] | -2.307 | 0.1233 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z | -0.7024 | 0.1211 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k2] | 0.3251 | 0.07897 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k3] | 0.4541 | 0.07391 | <.001 |
| Z5 Context window sensitivity | unit=Words | log_nb_words | -4.759 | 0.2063 | <.001 |
### Z5.2: unit: Morphemes

**Question asked by this subvariant.** Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_morpheme ~ age_months_z * C(context_k) + log_nb_morphemes`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Morphemes | gee_gaussian | fit | 15342 | 21 | 0.3902 | Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Morphemes | C(context_k)[T.k2] | -1.402 | 0.1013 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | C(context_k)[T.k3] | -2.169 | 0.1229 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z | -0.6761 | 0.1099 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k2] | 0.3061 | 0.08208 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k3] | 0.4511 | 0.07041 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | log_nb_morphemes | -4.874 | 0.1927 | <.001 |
### Z5.3: unit: Syllables: CMU/pkg

**Question asked by this subvariant.** Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_syllable_cmu_or_pkg ~ age_months_z * C(context_k) + log_nb_syllables`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | gee_gaussian | fit | 15342 | 21 | 0.4064 | Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | C(context_k)[T.k2] | -1.282 | 0.08727 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | C(context_k)[T.k3] | -1.938 | 0.1073 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z | -0.3634 | 0.0791 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k2] | 0.2549 | 0.07061 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k3] | 0.3612 | 0.07187 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | log_nb_syllables | -4.263 | 0.181 | <.001 |
### Z5.4: unit: Syllables: pkg

**Question asked by this subvariant.** Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_syllable_pkg ~ age_months_z * C(context_k) + log_nb_syllables`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Syllables: pkg | gee_gaussian | fit | 15342 | 21 | 0.3587 | Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Syllables: pkg | C(context_k)[T.k2] | -1.2 | 0.07072 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | C(context_k)[T.k3] | -1.858 | 0.09426 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z | -0.3247 | 0.09531 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k2] | 0.2205 | 0.06706 | 0.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k3] | 0.3404 | 0.07184 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | log_nb_syllables | -4.092 | 0.1651 | <.001 |
### Z5.5: unit: Phonemes

**Question asked by this subvariant.** Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows?

**Formula.** `bits_per_phoneme ~ age_months_z * C(context_k) + log_nb_phonemes`

**Estimator.** `gee_gaussian`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Phonemes | gee_gaussian | fit | 15342 | 21 | 0.4753 | Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z5 Context window sensitivity | unit=Phonemes | C(context_k)[T.k2] | -0.553 | 0.04324 | <.001 |
| Z5 Context window sensitivity | unit=Phonemes | C(context_k)[T.k3] | -0.8243 | 0.0499 | <.001 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z | -0.01887 | 0.03974 | 0.635 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k2] | 0.1091 | 0.03525 | 0.002 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k3] | 0.1976 | 0.03411 | <.001 |
| Z5 Context window sensitivity | unit=Phonemes | log_nb_phonemes | -2.283 | 0.1242 | <.001 |


## Z6: Question Type Predicting Effort

**Question family.** Does the type of preceding caretaker question predict how much effort the child produces?

**Why it is in the expanded atlas.** This adds a conversational-control variable: whether the preceding caretaker context is a wh-question, yes/no question, other question, or not a question.

**How to read this plot.** Lines compare mean child word count by age after different broad caretaker context types.

![Z6 plot](../figs/utterance_information_research_model_zoo/z6_question_type_effort.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 5 estimates are positive and 0 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 | effort: Words | gee_poisson | fit | 15342 | 21 | 0.1018 |
| Z6 | effort: Morphemes | gee_poisson | fit | 15342 | 21 | 0.1022 |
| Z6 | effort: Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08694 |
| Z6 | effort: Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.08178 |
| Z6 | effort: Phonemes | gee_poisson | fit | 15342 | 21 | 0.08042 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.other question] | -0.1042 | 0.02001 | <.001 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.wh-question] | -0.07694 | 0.02742 | 0.005 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.yes/no question] | -0.131 | 0.02404 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z | 0.2211 | 0.02566 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.other question] | 0.03033 | 0.01022 | 0.003 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.wh-question] | 0.03774 | 0.01602 | 0.018 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.yes/no question] | 0.001659 | 0.02465 | 0.946 |
| Z6 Question-type effort | effort=Words | log_context_words_plus1 | 0.02435 | 0.009193 | 0.008 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.other question] | -0.1016 | 0.01784 | <.001 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.wh-question] | -0.07505 | 0.02756 | 0.006 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.yes/no question] | -0.1271 | 0.02149 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z | 0.2304 | 0.0262 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.other question] | 0.03442 | 0.009922 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.wh-question] | 0.04586 | 0.01622 | 0.005 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.009962 | 0.02565 | 0.698 |
| Z6 Question-type effort | effort=Morphemes | log_context_words_plus1 | 0.02348 | 0.00965 | 0.015 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.other question] | -0.09869 | 0.01834 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.wh-question] | -0.08399 | 0.02513 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.yes/no question] | -0.1349 | 0.02377 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z | 0.198 | 0.02498 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.other question] | 0.03582 | 0.01069 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.04145 | 0.01788 | 0.020 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.005949 | 0.02542 | 0.815 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | log_context_words_plus1 | 0.01373 | 0.008896 | 0.123 |
| Z6 Question-type effort | effort=Syllables: pkg | C(context_question_type)[T.other question] | -0.105 | 0.01823 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z6 coefficients](../figs/utterance_information_research_model_zoo/z6_family_coefficients.png)


### Z6.1: effort: Words

**Question asked by this subvariant.** Does caretaker question type modulate child words, and does that modulation change with age?

**Formula.** `nb_words ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Words | gee_poisson | fit | 15342 | 21 | 0.1018 | Does caretaker question type modulate child words, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.other question] | -0.1042 | 0.02001 | <.001 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.wh-question] | -0.07694 | 0.02742 | 0.005 |
| Z6 Question-type effort | effort=Words | C(context_question_type)[T.yes/no question] | -0.131 | 0.02404 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z | 0.2211 | 0.02566 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.other question] | 0.03033 | 0.01022 | 0.003 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.wh-question] | 0.03774 | 0.01602 | 0.018 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.yes/no question] | 0.001659 | 0.02465 | 0.946 |
| Z6 Question-type effort | effort=Words | log_context_words_plus1 | 0.02435 | 0.009193 | 0.008 |
### Z6.2: effort: Morphemes

**Question asked by this subvariant.** Does caretaker question type modulate child morphemes, and does that modulation change with age?

**Formula.** `nb_morphemes ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Morphemes | gee_poisson | fit | 15342 | 21 | 0.1022 | Does caretaker question type modulate child morphemes, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.other question] | -0.1016 | 0.01784 | <.001 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.wh-question] | -0.07505 | 0.02756 | 0.006 |
| Z6 Question-type effort | effort=Morphemes | C(context_question_type)[T.yes/no question] | -0.1271 | 0.02149 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z | 0.2304 | 0.0262 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.other question] | 0.03442 | 0.009922 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.wh-question] | 0.04586 | 0.01622 | 0.005 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.009962 | 0.02565 | 0.698 |
| Z6 Question-type effort | effort=Morphemes | log_context_words_plus1 | 0.02348 | 0.00965 | 0.015 |
### Z6.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Does caretaker question type modulate child syllables: cmu/pkg, and does that modulation change with age?

**Formula.** `nb_syllables_cmu_or_pkg ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08694 | Does caretaker question type modulate child syllables: cmu/pkg, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.other question] | -0.09869 | 0.01834 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.wh-question] | -0.08399 | 0.02513 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | C(context_question_type)[T.yes/no question] | -0.1349 | 0.02377 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z | 0.198 | 0.02498 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.other question] | 0.03582 | 0.01069 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.04145 | 0.01788 | 0.020 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.005949 | 0.02542 | 0.815 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | log_context_words_plus1 | 0.01373 | 0.008896 | 0.123 |
### Z6.4: effort: Syllables: pkg

**Question asked by this subvariant.** Does caretaker question type modulate child syllables: pkg, and does that modulation change with age?

**Formula.** `nb_syllables_pkg ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.08178 | Does caretaker question type modulate child syllables: pkg, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Syllables: pkg | C(context_question_type)[T.other question] | -0.105 | 0.01823 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | C(context_question_type)[T.wh-question] | -0.08668 | 0.02488 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | C(context_question_type)[T.yes/no question] | -0.1429 | 0.025 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z | 0.1971 | 0.02418 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.other question] | 0.03513 | 0.0106 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.03973 | 0.01669 | 0.017 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.01614 | 0.02713 | 0.552 |
| Z6 Question-type effort | effort=Syllables: pkg | log_context_words_plus1 | 0.01137 | 0.009067 | 0.210 |
### Z6.5: effort: Phonemes

**Question asked by this subvariant.** Does caretaker question type modulate child phonemes, and does that modulation change with age?

**Formula.** `nb_phonemes ~ age_months_z * C(context_question_type) + log_context_words_plus1`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Phonemes | gee_poisson | fit | 15342 | 21 | 0.08042 | Does caretaker question type modulate child phonemes, and does that modulation change with age? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z6 Question-type effort | effort=Phonemes | C(context_question_type)[T.other question] | -0.1003 | 0.01849 | <.001 |
| Z6 Question-type effort | effort=Phonemes | C(context_question_type)[T.wh-question] | -0.07053 | 0.02774 | 0.011 |
| Z6 Question-type effort | effort=Phonemes | C(context_question_type)[T.yes/no question] | -0.1347 | 0.02346 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z | 0.1983 | 0.02454 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.other question] | 0.03889 | 0.01004 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.wh-question] | 0.04203 | 0.01768 | 0.017 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.01613 | 0.02527 | 0.523 |
| Z6 Question-type effort | effort=Phonemes | log_context_words_plus1 | 0.00729 | 0.008816 | 0.408 |


## Z7: Real Children Versus All Matched Baselines

**Question family.** Do real children differ from generated baselines after one effort measure is controlled?

**Why it is in the expanded atlas.** M1-M4 only analyze real child utterances; this model asks whether real children differ from random and n-gram baselines after controlling effort. Effort controls are kept separate.

**How to read this plot.** Lines compare real children and generated baselines over age. The plot is descriptive; the Z7 model table below is the effort-controlled comparison.

![Z7 plot](../figs/utterance_information_research_model_zoo/z7_baseline_comparison.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 4 estimates are positive and 1 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 | effort: Words | gee_gamma_log | fit | 18225 | 21 | 0.04299 |
| Z7 | effort: Morphemes | gee_gamma_log | fit | 18225 | 21 | 0.03944 |
| Z7 | effort: Syllables: CMU/pkg | gee_gamma_log | fit | 18225 | 21 | 0.04555 |
| Z7 | effort: Syllables: pkg | gee_gamma_log | fit | 18225 | 21 | 0.04568 |
| Z7 | effort: Phonemes | gee_gamma_log | fit | 18225 | 21 | 0.0377 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.random] | 0.4669 | 0.005083 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.real] | -0.2734 | 0.01862 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.trigram] | -0.08006 | 0.006758 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.unigram] | 0.1137 | 0.00579 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z | -0.003609 | 0.00546 | 0.509 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.random] | 0.05148 | 0.008967 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.real] | -0.02629 | 0.01233 | 0.033 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.trigram] | -0.002204 | 0.007195 | 0.759 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.unigram] | 0.01307 | 0.00668 | 0.050 |
| Z7 Baseline comparison | effort=Words | nb_words_z | 0.53 | 0.01655 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.random] | 0.3596 | 0.004942 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.real] | -0.2756 | 0.01835 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.trigram] | -0.08069 | 0.006021 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.unigram] | 0.1163 | 0.006456 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z | 0.01434 | 0.004918 | 0.004 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.random] | 0.01397 | 0.007368 | 0.058 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.real] | -0.03968 | 0.00953 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.trigram] | -0.01414 | 0.008065 | 0.080 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.unigram] | 0.008227 | 0.007597 | 0.279 |
| Z7 Baseline comparison | effort=Morphemes | nb_morphemes_z | 0.5237 | 0.01563 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.random] | 0.2142 | 0.007133 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.real] | -0.277 | 0.01899 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.trigram] | -0.0849 | 0.006118 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.unigram] | 0.1103 | 0.0046 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z | 0.0302 | 0.005328 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z7 coefficients](../figs/utterance_information_research_model_zoo/z7_family_coefficients.png)


### Z7.1: effort: Words

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling words?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_words_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Words | gee_gamma_log | fit | 18225 | 21 | 0.04299 | Do real child utterances differ from random/ngram baselines after controlling words? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.random] | 0.4669 | 0.005083 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.real] | -0.2734 | 0.01862 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.trigram] | -0.08006 | 0.006758 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.unigram] | 0.1137 | 0.00579 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z | -0.003609 | 0.00546 | 0.509 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.random] | 0.05148 | 0.008967 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.real] | -0.02629 | 0.01233 | 0.033 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.trigram] | -0.002204 | 0.007195 | 0.759 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.unigram] | 0.01307 | 0.00668 | 0.050 |
| Z7 Baseline comparison | effort=Words | nb_words_z | 0.53 | 0.01655 | <.001 |
### Z7.2: effort: Morphemes

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling morphemes?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_morphemes_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Morphemes | gee_gamma_log | fit | 18225 | 21 | 0.03944 | Do real child utterances differ from random/ngram baselines after controlling morphemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.random] | 0.3596 | 0.004942 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.real] | -0.2756 | 0.01835 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.trigram] | -0.08069 | 0.006021 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.unigram] | 0.1163 | 0.006456 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z | 0.01434 | 0.004918 | 0.004 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.random] | 0.01397 | 0.007368 | 0.058 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.real] | -0.03968 | 0.00953 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.trigram] | -0.01414 | 0.008065 | 0.080 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.unigram] | 0.008227 | 0.007597 | 0.279 |
| Z7 Baseline comparison | effort=Morphemes | nb_morphemes_z | 0.5237 | 0.01563 | <.001 |
### Z7.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling syllables: cmu/pkg?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_syllables_cmu_or_pkg_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 18225 | 21 | 0.04555 | Do real child utterances differ from random/ngram baselines after controlling syllables: cmu/pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.random] | 0.2142 | 0.007133 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.real] | -0.277 | 0.01899 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.trigram] | -0.0849 | 0.006118 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.unigram] | 0.1103 | 0.0046 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z | 0.0302 | 0.005328 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.random] | -0.03165 | 0.006751 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.real] | -0.02775 | 0.01179 | 0.019 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.trigram] | -0.003292 | 0.006539 | 0.615 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | age_months_z:C(target_variant)[T.unigram] | 0.01168 | 0.005538 | 0.035 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.5347 | 0.01556 | <.001 |
### Z7.4: effort: Syllables: pkg

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling syllables: pkg?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_syllables_pkg_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Syllables: pkg | gee_gamma_log | fit | 18225 | 21 | 0.04568 | Do real child utterances differ from random/ngram baselines after controlling syllables: pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.random] | 0.2304 | 0.006525 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.real] | -0.2762 | 0.01935 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.trigram] | -0.08142 | 0.005529 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | C(target_variant)[T.unigram] | 0.1122 | 0.004663 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z | 0.03248 | 0.005544 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.random] | -0.02967 | 0.006892 | <.001 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.real] | -0.02539 | 0.01172 | 0.030 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.trigram] | -0.001698 | 0.006529 | 0.795 |
| Z7 Baseline comparison | effort=Syllables: pkg | age_months_z:C(target_variant)[T.unigram] | 0.01212 | 0.006135 | 0.048 |
| Z7 Baseline comparison | effort=Syllables: pkg | nb_syllables_pkg_z | 0.5273 | 0.0149 | <.001 |
### Z7.5: effort: Phonemes

**Question asked by this subvariant.** Do real child utterances differ from random/ngram baselines after controlling phonemes?

**Formula.** `sum_bits ~ age_months_z * C(target_variant) + nb_phonemes_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Phonemes | gee_gamma_log | fit | 18225 | 21 | 0.0377 | Do real child utterances differ from random/ngram baselines after controlling phonemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.random] | 0.1505 | 0.008237 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.real] | -0.2788 | 0.02007 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.trigram] | -0.08568 | 0.006203 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | C(target_variant)[T.unigram] | 0.1051 | 0.005753 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z | 0.03534 | 0.004867 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.random] | -0.04859 | 0.007555 | <.001 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.real] | -0.02706 | 0.01073 | 0.012 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.trigram] | -0.006164 | 0.007458 | 0.409 |
| Z7 Baseline comparison | effort=Phonemes | age_months_z:C(target_variant)[T.unigram] | 0.01018 | 0.006446 | 0.114 |
| Z7 Baseline comparison | effort=Phonemes | nb_phonemes_z | 0.5476 | 0.01535 | <.001 |


## Z8: Children Versus Caretakers

**Question family.** Do children and caretakers show different age-linked information trajectories after effort is controlled?

**Why it is in the expanded atlas.** M1-M4 are child-only; this compares child and caretaker trajectories over child age.

**How to read this plot.** Lines compare child and caretaker bits per word. This is not row-matched, so read it as a speaker-group trajectory contrast.

![Z8 plot](../figs/utterance_information_research_model_zoo/z8_child_caretaker_density.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 5 estimates are positive and 0 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 | effort: Words | gee_gamma_log | fit | 10075 | 21 | 0.1359 |
| Z8 | effort: Morphemes | gee_gamma_log | fit | 10075 | 21 | 0.1649 |
| Z8 | effort: Syllables: CMU/pkg | gee_gamma_log | fit | 10075 | 21 | 0.1178 |
| Z8 | effort: Syllables: pkg | gee_gamma_log | fit | 10075 | 21 | 0.1329 |
| Z8 | effort: Phonemes | gee_gamma_log | fit | 10075 | 21 | 0.08581 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Words | C(speaker_group)[T.child] | -0.1164 | 0.01813 | <.001 |
| Z8 Child vs caretaker information | effort=Words | age_months_z | 0.00237 | 0.008268 | 0.774 |
| Z8 Child vs caretaker information | effort=Words | age_months_z:C(speaker_group)[T.child] | -0.04051 | 0.01374 | 0.003 |
| Z8 Child vs caretaker information | effort=Words | nb_words_z | 0.4482 | 0.01476 | <.001 |
| Z8 Child vs caretaker information | effort=Morphemes | C(speaker_group)[T.child] | -0.1139 | 0.01909 | <.001 |
| Z8 Child vs caretaker information | effort=Morphemes | age_months_z | 0.00424 | 0.00806 | 0.599 |
| Z8 Child vs caretaker information | effort=Morphemes | age_months_z:C(speaker_group)[T.child] | -0.04832 | 0.01412 | <.001 |
| Z8 Child vs caretaker information | effort=Morphemes | nb_morphemes_z | 0.4493 | 0.01485 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | C(speaker_group)[T.child] | -0.119 | 0.01616 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | age_months_z | 0.004019 | 0.008309 | 0.629 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | age_months_z:C(speaker_group)[T.child] | -0.03309 | 0.01293 | 0.010 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.4643 | 0.01569 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | C(speaker_group)[T.child] | -0.1197 | 0.01612 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | age_months_z | 0.004951 | 0.008147 | 0.543 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | age_months_z:C(speaker_group)[T.child] | -0.02977 | 0.01294 | 0.021 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | nb_syllables_pkg_z | 0.4575 | 0.01605 | <.001 |
| Z8 Child vs caretaker information | effort=Phonemes | C(speaker_group)[T.child] | -0.1186 | 0.01713 | <.001 |
| Z8 Child vs caretaker information | effort=Phonemes | age_months_z | 0.00183 | 0.007522 | 0.808 |
| Z8 Child vs caretaker information | effort=Phonemes | age_months_z:C(speaker_group)[T.child] | -0.03036 | 0.01246 | 0.015 |
| Z8 Child vs caretaker information | effort=Phonemes | nb_phonemes_z | 0.4696 | 0.01681 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z8 coefficients](../figs/utterance_information_research_model_zoo/z8_family_coefficients.png)


### Z8.1: effort: Words

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling words?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_words_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Words | gee_gamma_log | fit | 10075 | 21 | 0.1359 | Do child and caretaker total-bit trajectories differ after controlling words? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Words | C(speaker_group)[T.child] | -0.1164 | 0.01813 | <.001 |
| Z8 Child vs caretaker information | effort=Words | age_months_z | 0.00237 | 0.008268 | 0.774 |
| Z8 Child vs caretaker information | effort=Words | age_months_z:C(speaker_group)[T.child] | -0.04051 | 0.01374 | 0.003 |
| Z8 Child vs caretaker information | effort=Words | nb_words_z | 0.4482 | 0.01476 | <.001 |
### Z8.2: effort: Morphemes

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling morphemes?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_morphemes_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Morphemes | gee_gamma_log | fit | 10075 | 21 | 0.1649 | Do child and caretaker total-bit trajectories differ after controlling morphemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Morphemes | C(speaker_group)[T.child] | -0.1139 | 0.01909 | <.001 |
| Z8 Child vs caretaker information | effort=Morphemes | age_months_z | 0.00424 | 0.00806 | 0.599 |
| Z8 Child vs caretaker information | effort=Morphemes | age_months_z:C(speaker_group)[T.child] | -0.04832 | 0.01412 | <.001 |
| Z8 Child vs caretaker information | effort=Morphemes | nb_morphemes_z | 0.4493 | 0.01485 | <.001 |
### Z8.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_syllables_cmu_or_pkg_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 10075 | 21 | 0.1178 | Do child and caretaker total-bit trajectories differ after controlling syllables: cmu/pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | C(speaker_group)[T.child] | -0.119 | 0.01616 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | age_months_z | 0.004019 | 0.008309 | 0.629 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | age_months_z:C(speaker_group)[T.child] | -0.03309 | 0.01293 | 0.010 |
| Z8 Child vs caretaker information | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | 0.4643 | 0.01569 | <.001 |
### Z8.4: effort: Syllables: pkg

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling syllables: pkg?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_syllables_pkg_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Syllables: pkg | gee_gamma_log | fit | 10075 | 21 | 0.1329 | Do child and caretaker total-bit trajectories differ after controlling syllables: pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Syllables: pkg | C(speaker_group)[T.child] | -0.1197 | 0.01612 | <.001 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | age_months_z | 0.004951 | 0.008147 | 0.543 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | age_months_z:C(speaker_group)[T.child] | -0.02977 | 0.01294 | 0.021 |
| Z8 Child vs caretaker information | effort=Syllables: pkg | nb_syllables_pkg_z | 0.4575 | 0.01605 | <.001 |
### Z8.5: effort: Phonemes

**Question asked by this subvariant.** Do child and caretaker total-bit trajectories differ after controlling phonemes?

**Formula.** `sum_bits ~ age_months_z * C(speaker_group) + nb_phonemes_z`

**Estimator.** `gee_gamma_log`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Phonemes | gee_gamma_log | fit | 10075 | 21 | 0.08581 | Do child and caretaker total-bit trajectories differ after controlling phonemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z8 Child vs caretaker information | effort=Phonemes | C(speaker_group)[T.child] | -0.1186 | 0.01713 | <.001 |
| Z8 Child vs caretaker information | effort=Phonemes | age_months_z | 0.00183 | 0.007522 | 0.808 |
| Z8 Child vs caretaker information | effort=Phonemes | age_months_z:C(speaker_group)[T.child] | -0.03036 | 0.01246 | 0.015 |
| Z8 Child vs caretaker information | effort=Phonemes | nb_phonemes_z | 0.4696 | 0.01681 | <.001 |


## Z9: Information Per Effort Unit

**Question family.** Does information per effort unit change with age when the effort unit itself is the outcome denominator?

**Why it is in the expanded atlas.** M1-M4 control effort as a predictor; this complementary family treats information per effort unit as the outcome.

**How to read this plot.** The regression line shows the phoneme-denominated version of this family. The fitted subvariants below repeat the density model for every effort unit.

![Z9 plot](../figs/utterance_information_research_model_zoo/z9_phonological_efficiency.png)

**Compact result.** 5/5 subvariants fit cleanly. For `age_months_z`, 1 estimates are positive and 4 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 | unit: Words | ols_cluster | fit | 5560 | 21 | 0.2729 |
| Z9 | unit: Morphemes | ols_cluster | fit | 5560 | 21 | 0.3266 |
| Z9 | unit: Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.3298 |
| Z9 | unit: Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.2959 |
| Z9 | unit: Phonemes | ols_cluster | fit | 5560 | 21 | 0.4164 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Words | age_months_z | -0.4747 | 0.1437 | <.001 |
| Z9 Information per unit | unit=Words | log_nb_words | -4.24 | 0.1828 | <.001 |
| Z9 Information per unit | unit=Morphemes | age_months_z | -0.4743 | 0.1375 | <.001 |
| Z9 Information per unit | unit=Morphemes | log_nb_morphemes | -4.359 | 0.1787 | <.001 |
| Z9 Information per unit | unit=Syllables: CMU/pkg | age_months_z | -0.1645 | 0.1097 | 0.134 |
| Z9 Information per unit | unit=Syllables: CMU/pkg | log_nb_syllables | -3.689 | 0.1564 | <.001 |
| Z9 Information per unit | unit=Syllables: pkg | age_months_z | -0.1555 | 0.123 | 0.206 |
| Z9 Information per unit | unit=Syllables: pkg | log_nb_syllables | -3.564 | 0.1443 | <.001 |
| Z9 Information per unit | unit=Phonemes | age_months_z | 0.04061 | 0.04585 | 0.376 |
| Z9 Information per unit | unit=Phonemes | log_nb_phonemes | -1.895 | 0.08266 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z9 coefficients](../figs/utterance_information_research_model_zoo/z9_family_coefficients.png)


### Z9.1: unit: Words

**Question asked by this subvariant.** Does information per words change with age after child identity is controlled?

**Formula.** `bits_per_word ~ age_months_z + log_nb_words + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Words | ols_cluster | fit | 5560 | 21 | 0.2729 | Does information per words change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Words | age_months_z | -0.4747 | 0.1437 | <.001 |
| Z9 Information per unit | unit=Words | log_nb_words | -4.24 | 0.1828 | <.001 |
### Z9.2: unit: Morphemes

**Question asked by this subvariant.** Does information per morphemes change with age after child identity is controlled?

**Formula.** `bits_per_morpheme ~ age_months_z + log_nb_morphemes + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Morphemes | ols_cluster | fit | 5560 | 21 | 0.3266 | Does information per morphemes change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Morphemes | age_months_z | -0.4743 | 0.1375 | <.001 |
| Z9 Information per unit | unit=Morphemes | log_nb_morphemes | -4.359 | 0.1787 | <.001 |
### Z9.3: unit: Syllables: CMU/pkg

**Question asked by this subvariant.** Does information per syllables: cmu/pkg change with age after child identity is controlled?

**Formula.** `bits_per_syllable_cmu_or_pkg ~ age_months_z + log_nb_syllables + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.3298 | Does information per syllables: cmu/pkg change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Syllables: CMU/pkg | age_months_z | -0.1645 | 0.1097 | 0.134 |
| Z9 Information per unit | unit=Syllables: CMU/pkg | log_nb_syllables | -3.689 | 0.1564 | <.001 |
### Z9.4: unit: Syllables: pkg

**Question asked by this subvariant.** Does information per syllables: pkg change with age after child identity is controlled?

**Formula.** `bits_per_syllable_pkg ~ age_months_z + log_nb_syllables + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.2959 | Does information per syllables: pkg change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Syllables: pkg | age_months_z | -0.1555 | 0.123 | 0.206 |
| Z9 Information per unit | unit=Syllables: pkg | log_nb_syllables | -3.564 | 0.1443 | <.001 |
### Z9.5: unit: Phonemes

**Question asked by this subvariant.** Does information per phonemes change with age after child identity is controlled?

**Formula.** `bits_per_phoneme ~ age_months_z + log_nb_phonemes + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Phonemes | ols_cluster | fit | 5560 | 21 | 0.4164 | Does information per phonemes change with age after child identity is controlled? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z9 Information per unit | unit=Phonemes | age_months_z | 0.04061 | 0.04585 | 0.376 |
| Z9 Information per unit | unit=Phonemes | log_nb_phonemes | -1.895 | 0.08266 | <.001 |


## Z10: Context Certainty Predicting Effort

**Question family.** Do children produce less effort when the model is more certain about the next token after the context?

**Why it is in the expanded atlas.** This is the inverse of the entropy framing: it uses the probability of the most likely next token as a context-certainty predictor.

**How to read this plot.** The regression line shows whether child word count changes when the model is more certain about the next token.

![Z10 plot](../figs/utterance_information_research_model_zoo/z10_context_certainty_effort.png)

**Compact result.** 5/5 subvariants fit cleanly. For `context_next_top1_prob_z`, 0 estimates are positive and 5 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 | effort: Words | gee_poisson | fit | 15342 | 21 | 0.1013 |
| Z10 | effort: Morphemes | gee_poisson | fit | 15342 | 21 | 0.1014 |
| Z10 | effort: Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08628 |
| Z10 | effort: Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.0811 |
| Z10 | effort: Phonemes | gee_poisson | fit | 15342 | 21 | 0.07952 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Words | C(context_question_type)[T.other question] | -0.09166 | 0.02062 | <.001 |
| Z10 Context certainty | effort=Words | C(context_question_type)[T.wh-question] | -0.05302 | 0.02817 | 0.060 |
| Z10 Context certainty | effort=Words | C(context_question_type)[T.yes/no question] | -0.1191 | 0.023 | <.001 |
| Z10 Context certainty | effort=Words | age_months_z | 0.2348 | 0.02386 | <.001 |
| Z10 Context certainty | effort=Words | context_next_top1_prob_z | -0.01087 | 0.007739 | 0.160 |
| Z10 Context certainty | effort=Words | age_months_z:context_next_top1_prob_z | 0.0009407 | 0.007572 | 0.901 |
| Z10 Context certainty | effort=Words | log_context_words_plus1 | 0.02031 | 0.01183 | 0.086 |
| Z10 Context certainty | effort=Morphemes | C(context_question_type)[T.other question] | -0.08751 | 0.01902 | <.001 |
| Z10 Context certainty | effort=Morphemes | C(context_question_type)[T.wh-question] | -0.04733 | 0.02874 | 0.100 |
| Z10 Context certainty | effort=Morphemes | C(context_question_type)[T.yes/no question] | -0.1138 | 0.02031 | <.001 |
| Z10 Context certainty | effort=Morphemes | age_months_z | 0.2468 | 0.02479 | <.001 |
| Z10 Context certainty | effort=Morphemes | context_next_top1_prob_z | -0.01132 | 0.008148 | 0.165 |
| Z10 Context certainty | effort=Morphemes | age_months_z:context_next_top1_prob_z | 0.002911 | 0.008075 | 0.718 |
| Z10 Context certainty | effort=Morphemes | log_context_words_plus1 | 0.01951 | 0.01234 | 0.114 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | C(context_question_type)[T.other question] | -0.08399 | 0.02012 | <.001 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | C(context_question_type)[T.wh-question] | -0.05712 | 0.02731 | 0.036 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | C(context_question_type)[T.yes/no question] | -0.1198 | 0.02327 | <.001 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | age_months_z | 0.2141 | 0.02364 | <.001 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | context_next_top1_prob_z | -0.01416 | 0.008078 | 0.080 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | age_months_z:context_next_top1_prob_z | 0.0004394 | 0.007414 | 0.953 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | log_context_words_plus1 | 0.008461 | 0.01136 | 0.456 |
| Z10 Context certainty | effort=Syllables: pkg | C(context_question_type)[T.other question] | -0.09059 | 0.01978 | <.001 |
| Z10 Context certainty | effort=Syllables: pkg | C(context_question_type)[T.wh-question] | -0.06107 | 0.02611 | 0.019 |
| Z10 Context certainty | effort=Syllables: pkg | C(context_question_type)[T.yes/no question] | -0.1272 | 0.02473 | <.001 |
| Z10 Context certainty | effort=Syllables: pkg | age_months_z | 0.2132 | 0.02306 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z10 coefficients](../figs/utterance_information_research_model_zoo/z10_family_coefficients.png)


### Z10.1: effort: Words

**Question asked by this subvariant.** Is child words lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_words ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Words | gee_poisson | fit | 15342 | 21 | 0.1013 | Is child words lower when the model assigns high probability to the most likely next token? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Words | C(context_question_type)[T.other question] | -0.09166 | 0.02062 | <.001 |
| Z10 Context certainty | effort=Words | C(context_question_type)[T.wh-question] | -0.05302 | 0.02817 | 0.060 |
| Z10 Context certainty | effort=Words | C(context_question_type)[T.yes/no question] | -0.1191 | 0.023 | <.001 |
| Z10 Context certainty | effort=Words | age_months_z | 0.2348 | 0.02386 | <.001 |
| Z10 Context certainty | effort=Words | context_next_top1_prob_z | -0.01087 | 0.007739 | 0.160 |
| Z10 Context certainty | effort=Words | age_months_z:context_next_top1_prob_z | 0.0009407 | 0.007572 | 0.901 |
| Z10 Context certainty | effort=Words | log_context_words_plus1 | 0.02031 | 0.01183 | 0.086 |
### Z10.2: effort: Morphemes

**Question asked by this subvariant.** Is child morphemes lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_morphemes ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Morphemes | gee_poisson | fit | 15342 | 21 | 0.1014 | Is child morphemes lower when the model assigns high probability to the most likely next token? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Morphemes | C(context_question_type)[T.other question] | -0.08751 | 0.01902 | <.001 |
| Z10 Context certainty | effort=Morphemes | C(context_question_type)[T.wh-question] | -0.04733 | 0.02874 | 0.100 |
| Z10 Context certainty | effort=Morphemes | C(context_question_type)[T.yes/no question] | -0.1138 | 0.02031 | <.001 |
| Z10 Context certainty | effort=Morphemes | age_months_z | 0.2468 | 0.02479 | <.001 |
| Z10 Context certainty | effort=Morphemes | context_next_top1_prob_z | -0.01132 | 0.008148 | 0.165 |
| Z10 Context certainty | effort=Morphemes | age_months_z:context_next_top1_prob_z | 0.002911 | 0.008075 | 0.718 |
| Z10 Context certainty | effort=Morphemes | log_context_words_plus1 | 0.01951 | 0.01234 | 0.114 |
### Z10.3: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_syllables_cmu_or_pkg ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08628 | Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Syllables: CMU/pkg | C(context_question_type)[T.other question] | -0.08399 | 0.02012 | <.001 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | C(context_question_type)[T.wh-question] | -0.05712 | 0.02731 | 0.036 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | C(context_question_type)[T.yes/no question] | -0.1198 | 0.02327 | <.001 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | age_months_z | 0.2141 | 0.02364 | <.001 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | context_next_top1_prob_z | -0.01416 | 0.008078 | 0.080 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | age_months_z:context_next_top1_prob_z | 0.0004394 | 0.007414 | 0.953 |
| Z10 Context certainty | effort=Syllables: CMU/pkg | log_context_words_plus1 | 0.008461 | 0.01136 | 0.456 |
### Z10.4: effort: Syllables: pkg

**Question asked by this subvariant.** Is child syllables: pkg lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_syllables_pkg ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.0811 | Is child syllables: pkg lower when the model assigns high probability to the most likely next token? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Syllables: pkg | C(context_question_type)[T.other question] | -0.09059 | 0.01978 | <.001 |
| Z10 Context certainty | effort=Syllables: pkg | C(context_question_type)[T.wh-question] | -0.06107 | 0.02611 | 0.019 |
| Z10 Context certainty | effort=Syllables: pkg | C(context_question_type)[T.yes/no question] | -0.1272 | 0.02473 | <.001 |
| Z10 Context certainty | effort=Syllables: pkg | age_months_z | 0.2132 | 0.02306 | <.001 |
| Z10 Context certainty | effort=Syllables: pkg | context_next_top1_prob_z | -0.01439 | 0.008117 | 0.076 |
| Z10 Context certainty | effort=Syllables: pkg | age_months_z:context_next_top1_prob_z | 0.001352 | 0.007245 | 0.852 |
| Z10 Context certainty | effort=Syllables: pkg | log_context_words_plus1 | 0.006179 | 0.01168 | 0.597 |
### Z10.5: effort: Phonemes

**Question asked by this subvariant.** Is child phonemes lower when the model assigns high probability to the most likely next token?

**Formula.** `nb_phonemes ~ age_months_z * context_next_top1_prob_z + log_context_words_plus1 + C(context_question_type)`

**Estimator.** `gee_poisson`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Phonemes | gee_poisson | fit | 15342 | 21 | 0.07952 | Is child phonemes lower when the model assigns high probability to the most likely next token? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z10 Context certainty | effort=Phonemes | C(context_question_type)[T.other question] | -0.0851 | 0.0205 | <.001 |
| Z10 Context certainty | effort=Phonemes | C(context_question_type)[T.wh-question] | -0.04441 | 0.02805 | 0.113 |
| Z10 Context certainty | effort=Phonemes | C(context_question_type)[T.yes/no question] | -0.1189 | 0.02342 | <.001 |
| Z10 Context certainty | effort=Phonemes | age_months_z | 0.216 | 0.02328 | <.001 |
| Z10 Context certainty | effort=Phonemes | context_next_top1_prob_z | -0.01386 | 0.007541 | 0.066 |
| Z10 Context certainty | effort=Phonemes | age_months_z:context_next_top1_prob_z | 0.001283 | 0.007025 | 0.855 |
| Z10 Context certainty | effort=Phonemes | log_context_words_plus1 | 0.00227 | 0.01099 | 0.836 |


## Z11: Real Minus Baseline Delta

**Question family.** Does the row-matched real-minus-baseline information gap change with age after effort is controlled?

**Why it is in the expanded atlas.** This is the most direct baseline-difference analysis and is row-matched rather than child-only. Effort controls are fitted one at a time.

**How to read this plot.** Lines below zero mean real child utterances have lower total bits than the baseline; movement over age means the gap changes developmentally.

![Z11 plot](../figs/utterance_information_research_model_zoo/z11_real_minus_baseline_delta.png)

**Compact result.** 6/6 subvariants fit cleanly. For `age_months_z`, 2 estimates are positive and 4 are negative across fitted subvariants.

Subvariants in this family:

| family_id | subvariant | estimator | status | n_obs | n_children | r2_or_observed_fitted_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 | main specification | ols_cluster | fit | 1786032 | 21 | 0.2801 |
| Z11 | effort: Words | ols_cluster | fit | 1786032 | 21 | 0.5957 |
| Z11 | effort: Morphemes | ols_cluster | fit | 1786032 | 21 | 0.5671 |
| Z11 | effort: Syllables: CMU/pkg | ols_cluster | fit | 1786032 | 21 | 0.5172 |
| Z11 | effort: Syllables: pkg | ols_cluster | fit | 1786032 | 21 | 0.5146 |
| Z11 | effort: Phonemes | ols_cluster | fit | 1786032 | 21 | 0.5125 |

Family key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z | -4.7 | 0.4812 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z | 0.5478 | 0.2685 | 0.041 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | nb_words_z | -14.23 | 0.2695 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z | 0.4825 | 0.2841 | 0.089 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | nb_morphemes_z | -13.63 | 0.2605 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |


**How to read this coefficient plot.** Each point is a key coefficient from one
subvariant in this family. Horizontal bars are approximate 95% intervals. If a
bar crosses zero, the direction is uncertain in that subvariant; if the same
term points the same way across subvariants, that pattern is more stable.

![Z11 coefficients](../figs/utterance_information_research_model_zoo/z11_family_coefficients.png)


### Z11.1: main specification

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | no effort control | ols_cluster | fit | 1786032 | 21 | 0.2801 | Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z | -4.7 | 0.4812 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | no effort control | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
### Z11.2: effort: Words

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling words?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_words_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Words | ols_cluster | fit | 1786032 | 21 | 0.5957 | Does the real-child advantage or penalty relative to each baseline change with age after controlling words? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z | 0.5478 | 0.2685 | 0.041 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
| Z11 Real-minus-baseline delta | effort=Words | nb_words_z | -14.23 | 0.2695 | <.001 |
### Z11.3: effort: Morphemes

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling morphemes?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_morphemes_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Morphemes | ols_cluster | fit | 1786032 | 21 | 0.5671 | Does the real-child advantage or penalty relative to each baseline change with age after controlling morphemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z | 0.4825 | 0.2841 | 0.089 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
| Z11 Real-minus-baseline delta | effort=Morphemes | nb_morphemes_z | -13.63 | 0.2605 | <.001 |
### Z11.4: effort: Syllables: CMU/pkg

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: cmu/pkg?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_syllables_cmu_or_pkg_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | ols_cluster | fit | 1786032 | 21 | 0.5172 | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: cmu/pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | age_months_z | -0.6949 | 0.3339 | 0.037 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | nb_syllables_cmu_or_pkg_z | -12.25 | 0.3448 | <.001 |
### Z11.5: effort: Syllables: pkg

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: pkg?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_syllables_pkg_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | ols_cluster | fit | 1786032 | 21 | 0.5146 | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: pkg? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | age_months_z | -0.7727 | 0.3337 | 0.021 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | nb_syllables_pkg_z | -12.13 | 0.3556 | <.001 |
### Z11.6: effort: Phonemes

**Question asked by this subvariant.** Does the real-child advantage or penalty relative to each baseline change with age after controlling phonemes?

**Formula.** `delta_sum_bits ~ age_months_z * C(baseline_variant) + nb_phonemes_z + C(child_id)`

**Estimator.** `ols_cluster`. For `ols_cluster`, the fitted line is the same as OLS, but standard errors and p-values are clustered by child. For GEE models, rows are grouped by child to account for repeated utterances.

Subvariant fit:

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Phonemes | ols_cluster | fit | 1786032 | 21 | 0.5125 | Does the real-child advantage or penalty relative to each baseline change with age after controlling phonemes? |

Key coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z11 Real-minus-baseline delta | effort=Phonemes | C(baseline_variant)[T.random] | -24.32 | 1.058 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | C(baseline_variant)[T.trigram] | 3.118 | 0.2149 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | C(baseline_variant)[T.unigram] | -5.037 | 0.2489 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | age_months_z | -0.7161 | 0.3137 | 0.022 |
| Z11 Real-minus-baseline delta | effort=Phonemes | age_months_z:C(baseline_variant)[T.random] | -6.626 | 0.9256 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | age_months_z:C(baseline_variant)[T.trigram] | 0.4686 | 0.1315 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | age_months_z:C(baseline_variant)[T.unigram] | -1.086 | 0.1829 | <.001 |
| Z11 Real-minus-baseline delta | effort=Phonemes | nb_phonemes_z | -12.12 | 0.3414 | <.001 |



## Compact Model Zoo Summary

| model | family | status | n_obs | n_children | r2_or_observed_fitted_r2 | question |
| --- | --- | --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Morphemes | ols_cluster | fit | 5560 | 21 | 0.6228 | At the same morphemes level, does child total information change with age after child identity is controlled? |
| Z1 Information | child FE | effort=Phonemes | ols_cluster | fit | 5560 | 21 | 0.6596 | At the same phonemes level, does child total information change with age after child identity is controlled? |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.6545 | At the same syllables: cmu/pkg level, does child total information change with age after child identity is controlled? |
| Z1 Information | child FE | effort=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.6408 | At the same syllables: pkg level, does child total information change with age after child identity is controlled? |
| Z1 Information | child FE | effort=Words | ols_cluster | fit | 5560 | 21 | 0.6327 | At the same words level, does child total information change with age after child identity is controlled? |
| Z10 Context certainty | effort=Morphemes | gee_poisson | fit | 15342 | 21 | 0.1014 | Is child morphemes lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Phonemes | gee_poisson | fit | 15342 | 21 | 0.07952 | Is child phonemes lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08628 | Is child syllables: cmu/pkg lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.0811 | Is child syllables: pkg lower when the model assigns high probability to the most likely next token? |
| Z10 Context certainty | effort=Words | gee_poisson | fit | 15342 | 21 | 0.1013 | Is child words lower when the model assigns high probability to the most likely next token? |
| Z11 Real-minus-baseline delta | effort=Morphemes | ols_cluster | fit | 1786032 | 21 | 0.5671 | Does the real-child advantage or penalty relative to each baseline change with age after controlling morphemes? |
| Z11 Real-minus-baseline delta | effort=Phonemes | ols_cluster | fit | 1786032 | 21 | 0.5125 | Does the real-child advantage or penalty relative to each baseline change with age after controlling phonemes? |
| Z11 Real-minus-baseline delta | effort=Syllables: CMU/pkg | ols_cluster | fit | 1786032 | 21 | 0.5172 | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: cmu/pkg? |
| Z11 Real-minus-baseline delta | effort=Syllables: pkg | ols_cluster | fit | 1786032 | 21 | 0.5146 | Does the real-child advantage or penalty relative to each baseline change with age after controlling syllables: pkg? |
| Z11 Real-minus-baseline delta | effort=Words | ols_cluster | fit | 1786032 | 21 | 0.5957 | Does the real-child advantage or penalty relative to each baseline change with age after controlling words? |
| Z11 Real-minus-baseline delta | no effort control | ols_cluster | fit | 1786032 | 21 | 0.2801 | Does the real-child advantage or penalty relative to each baseline change with age before adding effort controls? |
| Z2 Information density | nonlinear age | unit=Morphemes | ols_cluster | fit | 5560 | 21 | 0.3275 | Does information per morphemes follow a nonlinear developmental trajectory? |
| Z2 Information density | nonlinear age | unit=Phonemes | ols_cluster | fit | 5560 | 21 | 0.4168 | Does information per phonemes follow a nonlinear developmental trajectory? |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | ols_cluster | fit | 5560 | 21 | 0.3299 | Does information per syllables: cmu/pkg follow a nonlinear developmental trajectory? |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | ols_cluster | fit | 5560 | 21 | 0.2959 | Does information per syllables: pkg follow a nonlinear developmental trajectory? |
| Z2 Information density | nonlinear age | unit=Words | ols_cluster | fit | 5560 | 21 | 0.2741 | Does information per words follow a nonlinear developmental trajectory? |
| Z3 Effort from context entropy | effort=Morphemes | gee_poisson | fit | 15342 | 21 | 0.1013 | Do children produce more morphemes after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Phonemes | gee_poisson | fit | 15342 | 21 | 0.07936 | Do children produce more phonemes after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | gee_poisson | fit | 15342 | 21 | 0.08609 | Do children produce more syllables: cmu/pkg after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Syllables: pkg | gee_poisson | fit | 15342 | 21 | 0.08093 | Do children produce more syllables: pkg after more uncertain caretaker contexts? |
| Z3 Effort from context entropy | effort=Words | gee_poisson | fit | 15342 | 21 | 0.1012 | Do children produce more words after more uncertain caretaker contexts? |
| Z4 Information from context entropy | effort=Morphemes | gee_gamma_log | fit | 15342 | 21 | 0.2433 | Is total child information related to context entropy after morphemes is controlled? |
| Z4 Information from context entropy | effort=Phonemes | gee_gamma_log | fit | 15342 | 21 | 0.1679 | Is total child information related to context entropy after phonemes is controlled? |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | gee_gamma_log | fit | 15342 | 21 | 0.2055 | Is total child information related to context entropy after syllables: cmu/pkg is controlled? |
| Z4 Information from context entropy | effort=Syllables: pkg | gee_gamma_log | fit | 15342 | 21 | 0.2184 | Is total child information related to context entropy after syllables: pkg is controlled? |
| Z4 Information from context entropy | effort=Words | gee_gamma_log | fit | 15342 | 21 | 0.161 | Is total child information related to context entropy after words is controlled? |
| Z5 Context window sensitivity | unit=Morphemes | gee_gaussian | fit | 15342 | 21 | 0.3902 | Does the age trajectory of information per morphemes change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Phonemes | gee_gaussian | fit | 15342 | 21 | 0.4753 | Does the age trajectory of information per phonemes change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | gee_gaussian | fit | 15342 | 21 | 0.4064 | Does the age trajectory of information per syllables: cmu/pkg change across k1/k2/k3 scoring windows? |
| Z5 Context window sensitivity | unit=Syllables: pkg | gee_gaussian | fit | 15342 | 21 | 0.3587 | Does the age trajectory of information per syllables: pkg change across k1/k2/k3 scoring windows? |

Selected coefficients:

| model | term | estimate | std_error | p_value |
| --- | --- | --- | --- | --- |
| Z1 Information | child FE | effort=Words | age_months_z | -0.8984 | 0.3166 | 0.005 |
| Z1 Information | child FE | effort=Words | nb_words_z | 12.91 | 0.3244 | <.001 |
| Z1 Information | child FE | effort=Morphemes | age_months_z | -1.035 | 0.3726 | 0.005 |
| Z1 Information | child FE | effort=Syllables: CMU/pkg | age_months_z | -0.5158 | 0.2671 | 0.053 |
| Z1 Information | child FE | effort=Syllables: pkg | age_months_z | -0.4091 | 0.2895 | 0.158 |
| Z1 Information | child FE | effort=Phonemes | age_months_z | -0.5649 | 0.2509 | 0.024 |
| Z2 Information density | nonlinear age | unit=Words | age_months_z | -0.6511 | 0.2394 | 0.007 |
| Z2 Information density | nonlinear age | unit=Words | log_nb_words | -4.195 | 0.1867 | <.001 |
| Z2 Information density | nonlinear age | unit=Morphemes | age_months_z | -0.6281 | 0.2309 | 0.007 |
| Z2 Information density | nonlinear age | unit=Syllables: CMU/pkg | age_months_z | -0.199 | 0.1873 | 0.288 |
| Z2 Information density | nonlinear age | unit=Syllables: pkg | age_months_z | -0.1831 | 0.1948 | 0.347 |
| Z2 Information density | nonlinear age | unit=Phonemes | age_months_z | 0.07736 | 0.05956 | 0.194 |
| Z3 Effort from context entropy | effort=Words | age_months_z | 0.2351 | 0.02375 | <.001 |
| Z3 Effort from context entropy | effort=Words | context_entropy_bits_z | 0.007438 | 0.007524 | 0.323 |
| Z3 Effort from context entropy | effort=Words | age_months_z:context_entropy_bits_z | 0.003663 | 0.006604 | 0.579 |
| Z3 Effort from context entropy | effort=Morphemes | age_months_z | 0.2471 | 0.02469 | <.001 |
| Z3 Effort from context entropy | effort=Morphemes | context_entropy_bits_z | 0.007266 | 0.007799 | 0.352 |
| Z3 Effort from context entropy | effort=Morphemes | age_months_z:context_entropy_bits_z | 0.001546 | 0.007373 | 0.834 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | age_months_z | 0.2145 | 0.02357 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | context_entropy_bits_z | 0.008152 | 0.008434 | 0.334 |
| Z3 Effort from context entropy | effort=Syllables: CMU/pkg | age_months_z:context_entropy_bits_z | 0.005645 | 0.006913 | 0.414 |
| Z3 Effort from context entropy | effort=Syllables: pkg | age_months_z | 0.2136 | 0.02298 | <.001 |
| Z3 Effort from context entropy | effort=Syllables: pkg | context_entropy_bits_z | 0.009024 | 0.008338 | 0.279 |
| Z3 Effort from context entropy | effort=Syllables: pkg | age_months_z:context_entropy_bits_z | 0.004487 | 0.006893 | 0.515 |
| Z3 Effort from context entropy | effort=Phonemes | age_months_z | 0.2164 | 0.02318 | <.001 |
| Z3 Effort from context entropy | effort=Phonemes | context_entropy_bits_z | 0.009404 | 0.007451 | 0.207 |
| Z3 Effort from context entropy | effort=Phonemes | age_months_z:context_entropy_bits_z | 0.003942 | 0.006636 | 0.553 |
| Z4 Information from context entropy | effort=Words | age_months_z | -0.03453 | 0.01273 | 0.007 |
| Z4 Information from context entropy | effort=Words | context_entropy_bits_z | -0.006685 | 0.004108 | 0.104 |
| Z4 Information from context entropy | effort=Words | age_months_z:context_entropy_bits_z | 0.009242 | 0.002554 | <.001 |
| Z4 Information from context entropy | effort=Words | nb_words_z | 0.4113 | 0.01252 | <.001 |
| Z4 Information from context entropy | effort=Morphemes | age_months_z | -0.04021 | 0.01454 | 0.006 |
| Z4 Information from context entropy | effort=Morphemes | context_entropy_bits_z | -0.005698 | 0.004166 | 0.171 |
| Z4 Information from context entropy | effort=Morphemes | age_months_z:context_entropy_bits_z | 0.01121 | 0.002546 | <.001 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | age_months_z | -0.02269 | 0.01127 | 0.044 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | context_entropy_bits_z | -0.006615 | 0.004131 | 0.109 |
| Z4 Information from context entropy | effort=Syllables: CMU/pkg | age_months_z:context_entropy_bits_z | 0.008573 | 0.002258 | <.001 |
| Z4 Information from context entropy | effort=Syllables: pkg | age_months_z | -0.01959 | 0.01115 | 0.079 |
| Z4 Information from context entropy | effort=Syllables: pkg | context_entropy_bits_z | -0.006926 | 0.003849 | 0.072 |
| Z4 Information from context entropy | effort=Syllables: pkg | age_months_z:context_entropy_bits_z | 0.009164 | 0.002262 | <.001 |
| Z4 Information from context entropy | effort=Phonemes | age_months_z | -0.02553 | 0.01153 | 0.027 |
| Z4 Information from context entropy | effort=Phonemes | context_entropy_bits_z | -0.006698 | 0.004023 | 0.096 |
| Z4 Information from context entropy | effort=Phonemes | age_months_z:context_entropy_bits_z | 0.009372 | 0.002538 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z | -0.7024 | 0.1211 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k2] | 0.3251 | 0.07897 | <.001 |
| Z5 Context window sensitivity | unit=Words | age_months_z:C(context_k)[T.k3] | 0.4541 | 0.07391 | <.001 |
| Z5 Context window sensitivity | unit=Words | log_nb_words | -4.759 | 0.2063 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z | -0.6761 | 0.1099 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k2] | 0.3061 | 0.08208 | <.001 |
| Z5 Context window sensitivity | unit=Morphemes | age_months_z:C(context_k)[T.k3] | 0.4511 | 0.07041 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z | -0.3634 | 0.0791 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k2] | 0.2549 | 0.07061 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: CMU/pkg | age_months_z:C(context_k)[T.k3] | 0.3612 | 0.07187 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z | -0.3247 | 0.09531 | <.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k2] | 0.2205 | 0.06706 | 0.001 |
| Z5 Context window sensitivity | unit=Syllables: pkg | age_months_z:C(context_k)[T.k3] | 0.3404 | 0.07184 | <.001 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z | -0.01887 | 0.03974 | 0.635 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k2] | 0.1091 | 0.03525 | 0.002 |
| Z5 Context window sensitivity | unit=Phonemes | age_months_z:C(context_k)[T.k3] | 0.1976 | 0.03411 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z | 0.2211 | 0.02566 | <.001 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.other question] | 0.03033 | 0.01022 | 0.003 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.wh-question] | 0.03774 | 0.01602 | 0.018 |
| Z6 Question-type effort | effort=Words | age_months_z:C(context_question_type)[T.yes/no question] | 0.001659 | 0.02465 | 0.946 |
| Z6 Question-type effort | effort=Morphemes | age_months_z | 0.2304 | 0.0262 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.other question] | 0.03442 | 0.009922 | <.001 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.wh-question] | 0.04586 | 0.01622 | 0.005 |
| Z6 Question-type effort | effort=Morphemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.009962 | 0.02565 | 0.698 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z | 0.198 | 0.02498 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.other question] | 0.03582 | 0.01069 | <.001 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.04145 | 0.01788 | 0.020 |
| Z6 Question-type effort | effort=Syllables: CMU/pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.005949 | 0.02542 | 0.815 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z | 0.1971 | 0.02418 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.other question] | 0.03513 | 0.0106 | <.001 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.wh-question] | 0.03973 | 0.01669 | 0.017 |
| Z6 Question-type effort | effort=Syllables: pkg | age_months_z:C(context_question_type)[T.yes/no question] | 0.01614 | 0.02713 | 0.552 |
| Z6 Question-type effort | effort=Phonemes | age_months_z | 0.1983 | 0.02454 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.other question] | 0.03889 | 0.01004 | <.001 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.wh-question] | 0.04203 | 0.01768 | 0.017 |
| Z6 Question-type effort | effort=Phonemes | age_months_z:C(context_question_type)[T.yes/no question] | 0.01613 | 0.02527 | 0.523 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.random] | 0.4669 | 0.005083 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.real] | -0.2734 | 0.01862 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.trigram] | -0.08006 | 0.006758 | <.001 |
| Z7 Baseline comparison | effort=Words | C(target_variant)[T.unigram] | 0.1137 | 0.00579 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z | -0.003609 | 0.00546 | 0.509 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.random] | 0.05148 | 0.008967 | <.001 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.real] | -0.02629 | 0.01233 | 0.033 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.trigram] | -0.002204 | 0.007195 | 0.759 |
| Z7 Baseline comparison | effort=Words | age_months_z:C(target_variant)[T.unigram] | 0.01307 | 0.00668 | 0.050 |
| Z7 Baseline comparison | effort=Words | nb_words_z | 0.53 | 0.01655 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.random] | 0.3596 | 0.004942 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.real] | -0.2756 | 0.01835 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.trigram] | -0.08069 | 0.006021 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | C(target_variant)[T.unigram] | 0.1163 | 0.006456 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z | 0.01434 | 0.004918 | 0.004 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.random] | 0.01397 | 0.007368 | 0.058 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.real] | -0.03968 | 0.00953 | <.001 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.trigram] | -0.01414 | 0.008065 | 0.080 |
| Z7 Baseline comparison | effort=Morphemes | age_months_z:C(target_variant)[T.unigram] | 0.008227 | 0.007597 | 0.279 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.random] | 0.2142 | 0.007133 | <.001 |
| Z7 Baseline comparison | effort=Syllables: CMU/pkg | C(target_variant)[T.real] | -0.277 | 0.01899 | <.001 |

**How to read this plot.** Each point is a selected coefficient from one of the
expanded atlas models. Positive values mean the coefficient increases the
outcome; negative values mean it decreases the outcome. Coefficients from
different model families are not always on exactly the same interpretive scale,
so use this as a map of candidates rather than as the final comparison.

![Key coefficients](../figs/utterance_information_research_model_zoo/model_zoo_key_coefficients.png)

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

- `results/utterance_information_research_model_zoo/model_zoo_summary.csv`
- `results/utterance_information_research_model_zoo/model_zoo_coefficients.csv`
- `results/utterance_information_research_model_zoo/comparison_model_summary.csv`
- `results/utterance_information_research_model_zoo/comparison_model_coefficients.csv`
- `results/utterance_information_research_model_zoo/baseline_delta_table.csv.gz`
- `results/utterance_information_research_model_zoo/baseline_trends.csv.gz`
- `results/utterance_information_research_model_zoo/role_trends.csv.gz`
- `results/utterance_information_research_model_zoo/derived_predictor_dictionary.csv`
