# All-79 Model × Length × Age Information Atlas

The analysis unit is now exactly the requested cell: **one information value per model, exact utterance length, and child-age bin**. The 2D figure reproduces the earlier fixed-effort design, and the 3D figure contains the same complete grid in one view.

## Main fixed-length 2D figure

- x-axis: child age in months.
- y-axis: mean contextual Mistral k3 total surprisal.
- rows: observed child, Qwen, random, unigram, bigram, and trigram models.
- columns: exact lengths 1–4, 5–8, and 9–12, matching the earlier atlas.
- each colored line: one exact cleaned-word length.
- points: raw average for that model × length × age bin.
- lines and ribbons: adjusted regression prediction and child-clustered 95% confidence interval.
- y-scales are shared within each model row so each length trajectory remains readable; the 3D figure below supplies the common cross-model scale.

![Model by exact-length age atlas](../figs/full79_information_effort_clouds/model_length_age_fixed_effort_atlas.png)

## Regression specification and checks

The primary model is fit separately for every source on all eligible child-age-length cells:

`mean k3 total bits ~ continuous age + exact length + child identity`

Fits use opportunity-weighted WLS and child-clustered covariance. The plotted fixed-length slices are predictions from the full fit; they are not twelve separately selected regressions. Separate registered checks add quadratic age, categorical age bins, age-by-length interactions, a bits/token outcome, and a source-balanced joint age-by-model fit.

![Linear versus nonlinear fixed-length predictions](../figs/full79_information_effort_clouds/model_length_age_nonlinear_check.png)

![Length-controlled regression coefficients](../figs/full79_information_effort_clouds/model_length_age_regression_coefficients.png)

Primary adjusted age slopes in total bits per month:

| model | bits_per_month | ci_low_bits_per_month | ci_high_bits_per_month | p_value | children | weighted_rows | r_squared |
| --- | --- | --- | --- | --- | --- | --- | --- |
| observed_child | -0.08116 | -0.1367 | -0.02559 | 0.0042 | 79 | 1116465 | 0.9442 |
| qwen | 0.02515 | 0.0176 | 0.0327 | 6.716e-11 | 79 | 111528138 | 0.9698 |
| random | 0.1847 | 0.1124 | 0.2569 | 5.428e-07 | 79 | 1116465 | 0.9967 |
| unigram | -0.03824 | -0.05716 | -0.01932 | 7.467e-05 | 79 | 1116465 | 0.9956 |
| bigram | -0.04452 | -0.06892 | -0.02012 | 0.0003481 | 79 | 1116461 | 0.9919 |
| trigram | -0.04105 | -0.06467 | -0.01744 | 0.0006548 | 79 | 1116463 | 0.9878 |

Bits-per-token sensitivity slopes:

| model | bits_per_token_per_month | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- |
| observed_child | -0.01871 | -0.03311 | -0.004318 | 0.01084 |
| qwen | 0.005997 | 0.003843 | 0.008151 | 4.849e-08 |
| random | -0.001848 | -0.004412 | 0.0007158 | 0.1577 |
| unigram | 0.001701 | -0.0008137 | 0.004215 | 0.1849 |
| bigram | -2.294e-05 | -0.002419 | 0.002373 | 0.985 |
| trigram | -0.00169 | -0.005496 | 0.002116 | 0.3841 |

Quadratic-age terms:

| source | term | estimate | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- | --- |
| observed_child | age_c | -1.016 | -1.512 | -0.5207 | 5.847e-05 |
| observed_child | age_c2 | 0.5045 | 0.1732 | 0.8358 | 0.002842 |
| qwen | age_c | 0.3056 | 0.2042 | 0.4071 | 3.558e-09 |
| qwen | age_c2 | -0.06731 | -0.1398 | 0.00516 | 0.0687 |
| random | age_c | 2.282 | 1.972 | 2.591 | 2.639e-47 |
| random | age_c2 | -0.7848 | -0.8875 | -0.6821 | 1.051e-50 |
| unigram | age_c | -0.4735 | -0.5897 | -0.3572 | 1.457e-15 |
| unigram | age_c2 | 0.1739 | 0.1079 | 0.2399 | 2.402e-07 |
| bigram | age_c | -0.5452 | -0.7485 | -0.3418 | 1.483e-07 |
| bigram | age_c2 | 0.1301 | 0.02601 | 0.2341 | 0.01429 |
| trigram | age_c | -0.5003 | -0.7376 | -0.263 | 3.593e-05 |
| trigram | age_c2 | 0.09096 | -0.03946 | 0.2214 | 0.1716 |

Joint age-by-model terms from the source-balanced comparison (observed child is the reference model):

| term | estimate | ci_low | ci_high | p_value |
| --- | --- | --- | --- | --- |
| age_c | -0.9818 | -1.295 | -0.6687 | 7.989e-10 |
| age_c:C(source, Treatment(reference='observed_child'))[T.bigram] | 0.3497 | -0.02652 | 0.7259 | 0.06849 |
| age_c:C(source, Treatment(reference='observed_child'))[T.qwen] | 1.235 | 0.8567 | 1.614 | 1.624e-10 |
| age_c:C(source, Treatment(reference='observed_child'))[T.random] | 3.386 | 2.638 | 4.133 | 6.636e-19 |
| age_c:C(source, Treatment(reference='observed_child'))[T.trigram] | 0.4711 | 0.1338 | 0.8083 | 0.006188 |
| age_c:C(source, Treatment(reference='observed_child'))[T.unigram] | 0.4996 | 0.1036 | 0.8955 | 0.0134 |

Registered model suite:

| source | specification | outcome | formula | cells | children |
| --- | --- | --- | --- | --- | --- |
| observed_child | primary_linear_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| observed_child | quadratic_age_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + age_c2 + C(word_count) + C(child_key) | 23518 | 79 |
| observed_child | age_bin_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ C(age_bin, Treatment(reference='006-023')) + C(word_count) + C(child_key) | 23518 | 79 |
| observed_child | age_by_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c * C(word_count) + C(child_key) | 23518 | 79 |
| observed_child | bits_per_token_linear_exact_length_child_fe | mean_k3_bits_per_token | mean_k3_bits_per_token ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| qwen | primary_linear_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + C(word_count) + C(child_key) | 29880 | 79 |
| qwen | quadratic_age_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + age_c2 + C(word_count) + C(child_key) | 29880 | 79 |
| qwen | age_bin_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ C(age_bin, Treatment(reference='006-023')) + C(word_count) + C(child_key) | 29880 | 79 |
| qwen | age_by_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c * C(word_count) + C(child_key) | 29880 | 79 |
| qwen | bits_per_token_linear_exact_length_child_fe | mean_k3_bits_per_token | mean_k3_bits_per_token ~ age_c + C(word_count) + C(child_key) | 29880 | 79 |
| random | primary_linear_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| random | quadratic_age_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + age_c2 + C(word_count) + C(child_key) | 23518 | 79 |
| random | age_bin_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ C(age_bin, Treatment(reference='006-023')) + C(word_count) + C(child_key) | 23518 | 79 |
| random | age_by_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c * C(word_count) + C(child_key) | 23518 | 79 |
| random | bits_per_token_linear_exact_length_child_fe | mean_k3_bits_per_token | mean_k3_bits_per_token ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| unigram | primary_linear_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| unigram | quadratic_age_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + age_c2 + C(word_count) + C(child_key) | 23518 | 79 |
| unigram | age_bin_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ C(age_bin, Treatment(reference='006-023')) + C(word_count) + C(child_key) | 23518 | 79 |
| unigram | age_by_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c * C(word_count) + C(child_key) | 23518 | 79 |
| unigram | bits_per_token_linear_exact_length_child_fe | mean_k3_bits_per_token | mean_k3_bits_per_token ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| bigram | primary_linear_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| bigram | quadratic_age_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + age_c2 + C(word_count) + C(child_key) | 23518 | 79 |
| bigram | age_bin_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ C(age_bin, Treatment(reference='006-023')) + C(word_count) + C(child_key) | 23518 | 79 |
| bigram | age_by_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c * C(word_count) + C(child_key) | 23518 | 79 |
| bigram | bits_per_token_linear_exact_length_child_fe | mean_k3_bits_per_token | mean_k3_bits_per_token ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| trigram | primary_linear_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| trigram | quadratic_age_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c + age_c2 + C(word_count) + C(child_key) | 23518 | 79 |
| trigram | age_bin_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ C(age_bin, Treatment(reference='006-023')) + C(word_count) + C(child_key) | 23518 | 79 |
| trigram | age_by_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c * C(word_count) + C(child_key) | 23518 | 79 |
| trigram | bits_per_token_linear_exact_length_child_fe | mean_k3_bits_per_token | mean_k3_bits_per_token ~ age_c + C(word_count) + C(child_key) | 23518 | 79 |
| all_sources | joint_age_by_model_exact_length_child_fe | mean_k3_sum_bits | mean_k3_sum_bits ~ age_c * C(source, Treatment(reference='observed_child')) + C(source, Treatment(reference='observed_child')) * C(word_count) + C(child_key) | 147470 | 79 |

## All information in one 3D plot

Every point below is one raw `model × exact length × age-bin` average. Lines connect age values at the same model and length; adjusted regression lines are superimposed with greater opacity.

![Complete model-length-age 3D atlas](../figs/full79_information_effort_clouds/model_length_age_all_models_3d.png)

[Open the filterable rotating 3D version](../figs/full79_information_effort_clouds/model_length_age_all_models_3d.html)

## Coverage

The frozen plotting grid contains **576 unique cells**: 6 models × 12 exact lengths × 8 age bins. The underlying audit covers **64,552,400 Qwen responses**, **645,524 contexts**, **1,122,396 observed opportunities**, **79 children**, and **13 corpora**.

| source | candidate_rows | utterances | children | corpora | nonfinite_k3 | nonfinite_k0 |
| --- | --- | --- | --- | --- | --- | --- |
| bigram | 1122396 | 1122396 | 79 | 13 | 4 | 4 |
| observed_child | 1122396 | 1122396 | 79 | 13 | 0 | 0 |
| qwen | 1122396 | 1122396 | 79 | 13 | 0 | 0 |
| random | 1122396 | 1122396 | 79 | 13 | 0 | 0 |
| trigram | 1122396 | 1122396 | 79 | 13 | 2 | 2 |
| unigram | 1122396 | 1122396 | 79 | 13 | 0 | 0 |

![Complete length distributions](../figs/full79_information_effort_clouds/length_distributions_by_age_bin.png)

The longest accepted Qwen response contains **96 cleaned words**, but the fixed-effort atlas deliberately restricts its comparable slices to exact lengths 1–12, matching the earlier plots.

## LSTM gate

The audited full-79 additive same-length LSTM score handoff is still absent, so it is not drawn as though complete. The six available models are fully analyzed; the completion state remains `CORE_CLOUDS_COMPLETE_LSTM_PENDING`.

Gate status: `ABSENT_PENDING`.

## Interpretation boundaries

- Lower Mistral surprisal means greater scorer predictability, not more Shannon information transmitted.
- Exact length is controlled in the regressions; longer utterances are not compared to shorter utterances as though total bits were length-free.
- Qwen is a free-length generated reference; random and n-gram candidates do not preserve the child's intended meaning.
- Regression lines describe adjusted observational associations. They do not establish semantic utility, a Pareto frontier, or optimization.
- All 79 children are pooled; these are not split discovery/confirmation estimates.
