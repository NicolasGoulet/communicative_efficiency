# Route 1: Real Children Versus Baselines, LSTMs, and Caretakers

This report systematically contrasts real child utterances with matched generated baselines, LSTM same-length baselines, and caretaker speech over the same developmental age bins.

The main quantities are:

- **No-context information:** `sum_bits` with `context_k = k0`.
- **With-context information:** `sum_bits` with `context_k = k3`, using the preceding three caretaker utterances.
- **Context gain:** `k0 sum_bits - k3 sum_bits`; positive values mean the preceding context made the target more predictable to the scoring model.
- **Source gap:** source `k3 sum_bits - real-child k3 sum_bits`; positive values mean the source is more unpredictable than the real child utterance under the same context.
- **Regression-line gap:** source model-predicted k3 bits minus real-child model-predicted k3 bits at the same fixed word count.

For random, n-gram, and LSTM conditions, comparisons are paired by the same original child utterance. Caretaker comparisons are not utterance-paired; they compare caretaker utterances from the same corpus/session age structure.

The regression-line layer uses the saved corrected fixed-effort Atlas predictions. The primary line plots use the identity-controlled fixed-effort model (`M2` for child sources, `CM2` for caretakers) at 2, 6, and 10 words. The slope-difference plot then asks whether the same downward or upward developmental tendency holds across richer model variants. A downward fixed-effort line means the model predicts fewer information bits at older ages for utterances of the same length.

## Overview

| source | rows | children | mean_k0 | mean_k3 | mean_gain |
| --- | --- | --- | --- | --- | --- |
| Bigram | 446508 | 21 | 54.54 | 43.55 | 10.99 |
| Caretaker | 668903 | 21 | 51.07 | 32.16 | 18.92 |
| LSTM k3 | 446508 | 21 | 44.65 | 33.06 | 11.60 |
| LSTM k4 | 446508 | 21 | 44.72 | 33.09 | 11.64 |
| LSTM k5 | 446508 | 21 | 44.76 | 33.08 | 11.69 |
| Random | 446508 | 21 | 83.29 | 75.20 | 8.09 |
| Real child | 446985 | 21 | 44.24 | 31.02 | 13.22 |
| Trigram | 446508 | 21 | 51.79 | 39.86 | 11.93 |
| Unigram | 446508 | 21 | 59.48 | 49.92 | 9.56 |


## Real vs Random

This section shows the no-context trajectory, the with-context trajectory, the context-gain trajectory, and the source-minus-real gap through age.

![Real vs Random k0 vs k3](../figs/route1_real_vs_controls_context_report/random_k0_vs_k3_age_means.png)

![Real vs Random with context](../figs/route1_real_vs_controls_context_report/random_k3_with_context_focus.png)

![Real vs Random context gain](../figs/route1_real_vs_controls_context_report/random_context_gain_by_age.png)

![Real vs Random gaps](../figs/route1_real_vs_controls_context_report/random_real_gap_by_age.png)

### Difference Models

For generated sources, `gap_k3` models ask whether the source-real contextual surprisal gap changes with age after child effort and child identity are controlled. `gain_gap` models ask whether the source benefits more or less from context than real children, and whether that difference changes with age.

| source | test | mean | age_slope | p | n |
| --- | --- | --- | --- | --- | --- |
| Random | gap_k3 | 34.402 | 0.302 | <.001 | 446508 |
| Random | gain_gap | -5.759 | 0.009 | 0.512 | 446508 |

### Fixed-Effort Regression Lines

These figures show model-based developmental lines at the same production effort. This is the layer that separates communicative-efficiency evidence from ordinary age-related growth in utterance length.

![Real vs Random fixed-effort regression lines](../figs/route1_real_vs_controls_context_report/random_m2_k3_fixed_word_regression_lines.png)

![Real vs Random fixed-effort regression gaps](../figs/route1_real_vs_controls_context_report/random_m2_k3_fixed_word_regression_gaps.png)

![Real vs Random model slope differences](../figs/route1_real_vs_controls_context_report/random_k3_word_model_slope_differences.png)

Primary fixed-effort slope read under M2/CM2: Random: source slope 1.068 vs real slope -0.735 bits per 6 months (source-real 1.803; real 12/12 downward lines, source 0/12).

Compact slope read: slopes are average bits per 6 months across the 12 fixed word-count lines. More negative values mean a stronger developmental decrease at fixed effort.

| source_label | model | real_slope_bits_per_6_months | source_slope_bits_per_6_months | source_minus_real_slope | real_line_directions | source_line_directions |
| --- | --- | --- | --- | --- | --- | --- |
| Random | M2: identity + effort | -0.735 | 1.068 | 1.803 | 12 down / 12 | 0 down / 12 |
| Random | M3: age x effort | -0.817 | 1.265 | 2.081 | 12 down / 12 | 0 down / 12 |
| Random | M4c: question type | -0.854 | 1.243 | 2.096 | 12 down / 12 | 0 down / 12 |
| Random | M5: context controls | -0.800 | 1.282 | 2.082 | 12 down / 12 | 0 down / 12 |
| Random | M6: context interactions | -0.802 | 1.303 | 2.105 | 12 down / 12 | 0 down / 12 |
| Random | M7: nonlinear age | -0.714 | 1.045 | 1.759 | 12 down / 12 | 0 down / 12 |
| Random | M11: age x parent effort | -0.766 | 1.292 | 2.058 | 12 down / 12 | 0 down / 12 |
| Random | M15: expanded interactions | -0.791 | 1.301 | 2.092 | 12 down / 12 | 0 down / 12 |

### Matched Examples

These are illustrative matched rows where the real child utterance has much lower with-context surprisal than the control utterance in the same preceding context. They are examples, not statistical tests.

| source_label | dataset | child_id | age_months | context | real_child_utterance | control_utterance | real_k3_bits | control_k3_bits | control_minus_real_k3 | real_context_gain | control_context_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Random | Providence | Alex | 37.6 | can't you sit still for two seconds? Alex you're gonna break those honey don't bang em. please. | don't don't drink the water don't don't drink the water don't don't drink the water don't don't drink the water don't d... | lane flipflop bobby's splendid cleaned supermarket baduper picture's belonged nuddy peas picture's hog mummige sweeties... | 68.93 | 1258.22 | 1189.29 | 3.75 | 9.31 |
| Random | Providence | William | 36.9 | yeah. we haven't done that. yay. | a b c d e f g h i j k l m n o p q r s s for q r s t u v w x y and z now I know my abcs next time won't you sing with me. | we'd punching deet ticktock donkeys pediatric paying climbers cwy weater drums bathios nocchio's salamanders coving lic... | 118.16 | 859.04 | 740.88 | 0.3 | 8.85 |
| Random | Brown | Adam | 43.2 | did I put that in there? yes. all set. | chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a... | napkins mummys battery nan cauldron glennis dodies turtle's nanna hoo copaz squigglies pentagon longs lugging polly's j... | 52.05 | 783.23 | 731.18 | 12.72 | 0.03 |
| Random | Manchester | Anne | 33.3 | you're too heavy. yeah. okay. | one two three four five six seven eight nine ten eleven twelve sixty forty eight nine ten eleven twelve thirty six fort... | groan genie crashed rouge ratty sw climbers righto likely dog's stack gumma uncle tattah chuff akbar jill's hopper myst... | 122.01 | 812.6 | 690.59 | 11.89 | 13.48 |
| Random | Providence | Naima | 34.6 | here you go. there's a puzzle piece. oh. | hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three... | yellowy head's washa burning goofy lizard's je carwen chewing fluff pumpkin's iceskating tapes crossed whacking lambcho... | 97.51 | 740.29 | 642.78 | 2.5 | 7.82 |


## Real vs Unigram

This section shows the no-context trajectory, the with-context trajectory, the context-gain trajectory, and the source-minus-real gap through age.

![Real vs Unigram k0 vs k3](../figs/route1_real_vs_controls_context_report/unigram_k0_vs_k3_age_means.png)

![Real vs Unigram with context](../figs/route1_real_vs_controls_context_report/unigram_k3_with_context_focus.png)

![Real vs Unigram context gain](../figs/route1_real_vs_controls_context_report/unigram_context_gain_by_age.png)

![Real vs Unigram gaps](../figs/route1_real_vs_controls_context_report/unigram_real_gap_by_age.png)

### Difference Models

For generated sources, `gap_k3` models ask whether the source-real contextual surprisal gap changes with age after child effort and child identity are controlled. `gain_gap` models ask whether the source benefits more or less from context than real children, and whether that difference changes with age.

| source | test | mean | age_slope | p | n |
| --- | --- | --- | --- | --- | --- |
| Unigram | gap_k3 | 15.119 | 0.103 | <.001 | 446508 |
| Unigram | gain_gap | -4.269 | 0.018 | 0.109 | 446508 |

### Fixed-Effort Regression Lines

These figures show model-based developmental lines at the same production effort. This is the layer that separates communicative-efficiency evidence from ordinary age-related growth in utterance length.

![Real vs Unigram fixed-effort regression lines](../figs/route1_real_vs_controls_context_report/unigram_m2_k3_fixed_word_regression_lines.png)

![Real vs Unigram fixed-effort regression gaps](../figs/route1_real_vs_controls_context_report/unigram_m2_k3_fixed_word_regression_gaps.png)

![Real vs Unigram model slope differences](../figs/route1_real_vs_controls_context_report/unigram_k3_word_model_slope_differences.png)

Primary fixed-effort slope read under M2/CM2: Unigram: source slope -0.125 vs real slope -0.735 bits per 6 months (source-real 0.610; real 12/12 downward lines, source 12/12).

Compact slope read: slopes are average bits per 6 months across the 12 fixed word-count lines. More negative values mean a stronger developmental decrease at fixed effort.

| source_label | model | real_slope_bits_per_6_months | source_slope_bits_per_6_months | source_minus_real_slope | real_line_directions | source_line_directions |
| --- | --- | --- | --- | --- | --- | --- |
| Unigram | M2: identity + effort | -0.735 | -0.125 | 0.610 | 12 down / 12 | 12 down / 12 |
| Unigram | M3: age x effort | -0.817 | -0.754 | 0.063 | 12 down / 12 | 10 down / 12 |
| Unigram | M4c: question type | -0.854 | -0.778 | 0.075 | 12 down / 12 | 10 down / 12 |
| Unigram | M5: context controls | -0.800 | -0.870 | -0.070 | 12 down / 12 | 11 down / 12 |
| Unigram | M6: context interactions | -0.802 | -0.846 | -0.044 | 12 down / 12 | 11 down / 12 |
| Unigram | M7: nonlinear age | -0.714 | -0.114 | 0.600 | 12 down / 12 | 12 down / 12 |
| Unigram | M11: age x parent effort | -0.766 | -0.872 | -0.106 | 12 down / 12 | 11 down / 12 |
| Unigram | M15: expanded interactions | -0.791 | -0.858 | -0.067 | 12 down / 12 | 11 down / 12 |

### Matched Examples

These are illustrative matched rows where the real child utterance has much lower with-context surprisal than the control utterance in the same preceding context. They are examples, not statistical tests.

| source_label | dataset | child_id | age_months | context | real_child_utterance | control_utterance | real_k3_bits | control_k3_bits | control_minus_real_k3 | real_context_gain | control_context_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Unigram | Providence | Alex | 37.6 | Alex you're gonna break those honey don't bang em. please. ooh I'm cold cold in here. | don't don't drink the water don't don't drink the water don't don't drink the water don't don't drink the water don't d... | no drop jump one taperecorder few in wanna camera wow green school open is underwear eye the paf spell on fit nose thre... | 62.5 | 693.96 | 631.46 | 9.51 | 11.84 |
| Unigram | Brown | Adam | 43.2 | did I put that in there? yes. all set. | chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a... | has roll is and have not huh spraying whoops what's fraser car a night no apples climb a tomato but done tissue bun a d... | 52.05 | 523.69 | 471.64 | 12.72 | 8.09 |
| Unigram | Providence | Naima | 34.6 | here you go. there's a puzzle piece. oh. | hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three... | like the oh what what will another gonna daddy bit yes popsicles in who three to on there stool what's commydit go blue... | 97.51 | 494.32 | 396.82 | 2.5 | 17.04 |
| Unigram | Providence | William | 36.9 | we haven't done the alphabet. yeah. we haven't done that. | a b c d e f g h i j k l m n o p q r s t u v w x y and z now I know my abcs next time won't you sing with me okay. | falling a inside brumm train it my i i yeah in bear choo track up the my home do lunch that doesn't this yeah those fri... | 82.14 | 470.83 | 388.69 | 12.42 | -3.63 |
| Unigram | Manchester | Anne | 33.3 | you're too heavy. yeah. okay. | one two three four five six seven eight nine ten eleven twelve sixty forty eight nine ten eleven twelve thirty six fort... | yeah like that what's he not what foggy to get way daddy get it a go birthday this play wants no it's and do about oh i... | 122.01 | 485.63 | 363.61 | 11.89 | 20.28 |


## Real vs Bigram

This section shows the no-context trajectory, the with-context trajectory, the context-gain trajectory, and the source-minus-real gap through age.

![Real vs Bigram k0 vs k3](../figs/route1_real_vs_controls_context_report/bigram_k0_vs_k3_age_means.png)

![Real vs Bigram with context](../figs/route1_real_vs_controls_context_report/bigram_k3_with_context_focus.png)

![Real vs Bigram context gain](../figs/route1_real_vs_controls_context_report/bigram_context_gain_by_age.png)

![Real vs Bigram gaps](../figs/route1_real_vs_controls_context_report/bigram_real_gap_by_age.png)

### Difference Models

For generated sources, `gap_k3` models ask whether the source-real contextual surprisal gap changes with age after child effort and child identity are controlled. `gain_gap` models ask whether the source benefits more or less from context than real children, and whether that difference changes with age.

| source | test | mean | age_slope | p | n |
| --- | --- | --- | --- | --- | --- |
| Bigram | gap_k3 | 10.082 | 0.102 | <.001 | 446508 |
| Bigram | gain_gap | -2.814 | 3.15e-04 | 0.982 | 446508 |

### Fixed-Effort Regression Lines

These figures show model-based developmental lines at the same production effort. This is the layer that separates communicative-efficiency evidence from ordinary age-related growth in utterance length.

![Real vs Bigram fixed-effort regression lines](../figs/route1_real_vs_controls_context_report/bigram_m2_k3_fixed_word_regression_lines.png)

![Real vs Bigram fixed-effort regression gaps](../figs/route1_real_vs_controls_context_report/bigram_m2_k3_fixed_word_regression_gaps.png)

![Real vs Bigram model slope differences](../figs/route1_real_vs_controls_context_report/bigram_k3_word_model_slope_differences.png)

Primary fixed-effort slope read under M2/CM2: Bigram: source slope -0.134 vs real slope -0.735 bits per 6 months (source-real 0.601; real 12/12 downward lines, source 12/12).

Compact slope read: slopes are average bits per 6 months across the 12 fixed word-count lines. More negative values mean a stronger developmental decrease at fixed effort.

| source_label | model | real_slope_bits_per_6_months | source_slope_bits_per_6_months | source_minus_real_slope | real_line_directions | source_line_directions |
| --- | --- | --- | --- | --- | --- | --- |
| Bigram | M2: identity + effort | -0.735 | -0.134 | 0.601 | 12 down / 12 | 12 down / 12 |
| Bigram | M3: age x effort | -0.817 | -0.662 | 0.154 | 12 down / 12 | 11 down / 12 |
| Bigram | M4c: question type | -0.854 | -0.690 | 0.164 | 12 down / 12 | 11 down / 12 |
| Bigram | M5: context controls | -0.800 | -0.751 | 0.049 | 12 down / 12 | 11 down / 12 |
| Bigram | M6: context interactions | -0.802 | -0.725 | 0.077 | 12 down / 12 | 11 down / 12 |
| Bigram | M7: nonlinear age | -0.714 | -0.130 | 0.584 | 12 down / 12 | 12 down / 12 |
| Bigram | M11: age x parent effort | -0.766 | -0.745 | 0.020 | 12 down / 12 | 11 down / 12 |
| Bigram | M15: expanded interactions | -0.791 | -0.731 | 0.060 | 12 down / 12 | 11 down / 12 |

### Matched Examples

These are illustrative matched rows where the real child utterance has much lower with-context surprisal than the control utterance in the same preceding context. They are examples, not statistical tests.

| source_label | dataset | child_id | age_months | context | real_child_utterance | control_utterance | real_k3_bits | control_k3_bits | control_minus_real_k3 | real_context_gain | control_context_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bigram | Providence | Alex | 37.6 | Alex you're gonna break those honey don't bang em. please. ooh I'm cold cold in here. | don't don't drink the water don't don't drink the water don't don't drink the water don't don't drink the water don't d... | doctor yeah red pepper pepper ah again what's the train bye doggie bird there yeah alice mommy read this is who who you... | 62.5 | 611.43 | 548.93 | 9.51 | 7.37 |
| Bigram | Brown | Adam | 43.2 | did I put that in there? yes. all set. | chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a... | and bump my baby ah catch him to stabilize it my shopping bag yet it's not broked another caterpillar not working littl... | 52.05 | 474.93 | 422.88 | 12.72 | 13.47 |
| Bigram | Providence | William | 36.9 | yeah. we haven't done that. yay. | a b c d e f g h i j k l m n o p q r s s for q r s t u v w x y and z now I know my abcs next time won't you sing with me. | flap flap book could put this tractor trailer shed no bees he's a star there that's green shoes and um raspberries and... | 118.16 | 412.26 | 294.11 | 0.3 | 9.92 |
| Bigram | Manchester | Anne | 33.3 | you're too heavy. yeah. okay. | one two three four five six seven eight nine ten eleven twelve sixty forty eight nine ten eleven twelve thirty six fort... | right yes i fell out here oh it yeah come with toys yes does sit here why it yeah it's a firefighter it i can't put on... | 122.01 | 408.95 | 286.94 | 11.89 | 17.05 |
| Bigram | Providence | Naima | 34.6 | here you go. there's a puzzle piece. oh. | hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three... | other one for my head banana go like that green i wanna come from i don't know get him up to mummy ow sit down i'm put... | 97.51 | 378.19 | 280.69 | 2.5 | 13.31 |


## Real vs Trigram

This section shows the no-context trajectory, the with-context trajectory, the context-gain trajectory, and the source-minus-real gap through age.

![Real vs Trigram k0 vs k3](../figs/route1_real_vs_controls_context_report/trigram_k0_vs_k3_age_means.png)

![Real vs Trigram with context](../figs/route1_real_vs_controls_context_report/trigram_k3_with_context_focus.png)

![Real vs Trigram context gain](../figs/route1_real_vs_controls_context_report/trigram_context_gain_by_age.png)

![Real vs Trigram gaps](../figs/route1_real_vs_controls_context_report/trigram_real_gap_by_age.png)

### Difference Models

For generated sources, `gap_k3` models ask whether the source-real contextual surprisal gap changes with age after child effort and child identity are controlled. `gain_gap` models ask whether the source benefits more or less from context than real children, and whether that difference changes with age.

| source | test | mean | age_slope | p | n |
| --- | --- | --- | --- | --- | --- |
| Trigram | gap_k3 | 6.964 | 0.109 | <.001 | 446508 |
| Trigram | gain_gap | -1.747 | -0.013 | 0.325 | 446508 |

### Fixed-Effort Regression Lines

These figures show model-based developmental lines at the same production effort. This is the layer that separates communicative-efficiency evidence from ordinary age-related growth in utterance length.

![Real vs Trigram fixed-effort regression lines](../figs/route1_real_vs_controls_context_report/trigram_m2_k3_fixed_word_regression_lines.png)

![Real vs Trigram fixed-effort regression gaps](../figs/route1_real_vs_controls_context_report/trigram_m2_k3_fixed_word_regression_gaps.png)

![Real vs Trigram model slope differences](../figs/route1_real_vs_controls_context_report/trigram_k3_word_model_slope_differences.png)

Primary fixed-effort slope read under M2/CM2: Trigram: source slope -0.092 vs real slope -0.735 bits per 6 months (source-real 0.643; real 12/12 downward lines, source 12/12).

Compact slope read: slopes are average bits per 6 months across the 12 fixed word-count lines. More negative values mean a stronger developmental decrease at fixed effort.

| source_label | model | real_slope_bits_per_6_months | source_slope_bits_per_6_months | source_minus_real_slope | real_line_directions | source_line_directions |
| --- | --- | --- | --- | --- | --- | --- |
| Trigram | M2: identity + effort | -0.735 | -0.092 | 0.643 | 12 down / 12 | 12 down / 12 |
| Trigram | M3: age x effort | -0.817 | -0.354 | 0.463 | 12 down / 12 | 11 down / 12 |
| Trigram | M4c: question type | -0.854 | -0.386 | 0.467 | 12 down / 12 | 11 down / 12 |
| Trigram | M5: context controls | -0.800 | -0.425 | 0.375 | 12 down / 12 | 11 down / 12 |
| Trigram | M6: context interactions | -0.802 | -0.389 | 0.413 | 12 down / 12 | 11 down / 12 |
| Trigram | M7: nonlinear age | -0.714 | -0.092 | 0.622 | 12 down / 12 | 12 down / 12 |
| Trigram | M11: age x parent effort | -0.766 | -0.413 | 0.352 | 12 down / 12 | 11 down / 12 |
| Trigram | M15: expanded interactions | -0.791 | -0.391 | 0.400 | 12 down / 12 | 11 down / 12 |

### Matched Examples

These are illustrative matched rows where the real child utterance has much lower with-context surprisal than the control utterance in the same preceding context. They are examples, not statistical tests.

| source_label | dataset | child_id | age_months | context | real_child_utterance | control_utterance | real_k3_bits | control_k3_bits | control_minus_real_k3 | real_context_gain | control_context_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Trigram | Providence | Alex | 37.6 | can't you sit still for two seconds? Alex you're gonna break those honey don't bang em. please. | don't don't drink the water don't don't drink the water don't don't drink the water don't don't drink the water don't d... | please i'm too little it's too heavy here re some crayons for you glue it now brumm warren look at live in barn mommy w... | 68.93 | 615.96 | 547.03 | 3.75 | 40.56 |
| Trigram | Brown | Adam | 43.2 | did I put that in there? yes. all set. | chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a... | daddy daddy daddy daddy daddy wanna build castle um i draw this for mummy that's line and go round my tape downstairs g... | 52.05 | 383.74 | 331.7 | 12.72 | 12.21 |
| Trigram | Providence | William | 36.9 | we haven't done the alphabet. yeah. we haven't done that. | a b c d e f g h i j k l m n o p q r s t u v w x y and z now I know my abcs next time won't you sing with me okay. | what mummy egg lid on there nice tiger come ditiduck story one more going get the door i making it now this come from i... | 82.14 | 413.72 | 331.58 | 12.42 | 5.1 |
| Trigram | Providence | Naima | 34.6 | here you go. there's a puzzle piece. oh. | hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three... | it's lemon no no you're a bird bird tweet tweet tweet tweet tweet tweet tweet tweet tweet what's that for the cows are... | 97.51 | 319.99 | 222.48 | 2.5 | 21.38 |
| Trigram | Providence | Lily | 43.8 | you got that extra piece. yeah two more. uh huh. | and then we put the the one in and then you put the one in and then we put the and then we put the other last one in. | clips i'll beat you my friend yeah play basketball camp okay i broke this more happy you you got another bit come from... | 95.31 | 305.03 | 209.72 | 28.82 | 24.31 |


## Real vs LSTMs

This section shows the no-context trajectory, the with-context trajectory, the context-gain trajectory, and the source-minus-real gap through age.

![Real vs LSTMs k0 vs k3](../figs/route1_real_vs_controls_context_report/lstm_k0_vs_k3_age_means.png)

![Real vs LSTMs with context](../figs/route1_real_vs_controls_context_report/lstm_k3_with_context_focus.png)

![Real vs LSTMs context gain](../figs/route1_real_vs_controls_context_report/lstm_context_gain_by_age.png)

![Real vs LSTMs gaps](../figs/route1_real_vs_controls_context_report/lstm_real_gap_by_age.png)

### Difference Models

For generated sources, `gap_k3` models ask whether the source-real contextual surprisal gap changes with age after child effort and child identity are controlled. `gain_gap` models ask whether the source benefits more or less from context than real children, and whether that difference changes with age.

| source | test | mean | age_slope | p | n |
| --- | --- | --- | --- | --- | --- |
| LSTM k3 | gap_k3 | 1.707 | 0.078 | 0.020 | 446508 |
| LSTM k3 | gain_gap | -2.241 | 0.026 | 0.028 | 446508 |
| LSTM k4 | gap_k3 | 1.798 | 0.066 | 0.066 | 446508 |
| LSTM k4 | gain_gap | -2.142 | 0.033 | 0.002 | 446508 |
| LSTM k5 | gap_k3 | 1.799 | 0.064 | 0.074 | 446508 |
| LSTM k5 | gain_gap | -2.159 | 0.033 | 0.003 | 446508 |

### Fixed-Effort Regression Lines

These figures show model-based developmental lines at the same production effort. This is the layer that separates communicative-efficiency evidence from ordinary age-related growth in utterance length.

![Real vs LSTMs fixed-effort regression lines](../figs/route1_real_vs_controls_context_report/lstm_m2_k3_fixed_word_regression_lines.png)

![Real vs LSTMs fixed-effort regression gaps](../figs/route1_real_vs_controls_context_report/lstm_m2_k3_fixed_word_regression_gaps.png)

![Real vs LSTMs model slope differences](../figs/route1_real_vs_controls_context_report/lstm_k3_word_model_slope_differences.png)

Primary fixed-effort slope read under M2/CM2: LSTM k3: source slope -0.279 vs real slope -0.735 bits per 6 months (source-real 0.456; real 12/12 downward lines, source 12/12). LSTM k4: source slope -0.351 vs real slope -0.735 bits per 6 months (source-real 0.384; real 12/12 downward lines, source 12/12). LSTM k5: source slope -0.363 vs real slope -0.735 bits per 6 months (source-real 0.372; real 12/12 downward lines, source 12/12).

Compact slope read: slopes are average bits per 6 months across the 12 fixed word-count lines. More negative values mean a stronger developmental decrease at fixed effort.

| source_label | model | real_slope_bits_per_6_months | source_slope_bits_per_6_months | source_minus_real_slope | real_line_directions | source_line_directions |
| --- | --- | --- | --- | --- | --- | --- |
| LSTM k3 | M2: identity + effort | -0.735 | -0.279 | 0.456 | 12 down / 12 | 12 down / 12 |
| LSTM k4 | M2: identity + effort | -0.735 | -0.351 | 0.384 | 12 down / 12 | 12 down / 12 |
| LSTM k5 | M2: identity + effort | -0.735 | -0.363 | 0.372 | 12 down / 12 | 12 down / 12 |
| LSTM k3 | M3: age x effort | -0.817 | -0.744 | 0.073 | 12 down / 12 | 12 down / 12 |
| LSTM k4 | M3: age x effort | -0.817 | -0.879 | -0.062 | 12 down / 12 | 12 down / 12 |
| LSTM k5 | M3: age x effort | -0.817 | -0.816 | 8.83e-04 | 12 down / 12 | 12 down / 12 |
| LSTM k3 | M4c: question type | -0.854 | -0.776 | 0.078 | 12 down / 12 | 12 down / 12 |
| LSTM k4 | M4c: question type | -0.854 | -0.913 | -0.059 | 12 down / 12 | 12 down / 12 |
| LSTM k5 | M4c: question type | -0.854 | -0.848 | 0.005 | 12 down / 12 | 12 down / 12 |
| LSTM k3 | M5: context controls | -0.800 | -0.862 | -0.062 | 12 down / 12 | 12 down / 12 |
| LSTM k4 | M5: context controls | -0.800 | -0.965 | -0.165 | 12 down / 12 | 12 down / 12 |
| LSTM k5 | M5: context controls | -0.800 | -0.923 | -0.123 | 12 down / 12 | 12 down / 12 |
| LSTM k3 | M6: context interactions | -0.802 | -0.841 | -0.039 | 12 down / 12 | 12 down / 12 |
| LSTM k4 | M6: context interactions | -0.802 | -0.950 | -0.148 | 12 down / 12 | 12 down / 12 |
| LSTM k5 | M6: context interactions | -0.802 | -0.908 | -0.106 | 12 down / 12 | 12 down / 12 |
| LSTM k3 | M7: nonlinear age | -0.714 | -0.261 | 0.453 | 12 down / 12 | 12 down / 12 |
| LSTM k4 | M7: nonlinear age | -0.714 | -0.327 | 0.387 | 12 down / 12 | 12 down / 12 |
| LSTM k5 | M7: nonlinear age | -0.714 | -0.340 | 0.374 | 12 down / 12 | 12 down / 12 |
| LSTM k3 | M11: age x parent effort | -0.766 | -0.857 | -0.092 | 12 down / 12 | 12 down / 12 |
| LSTM k4 | M11: age x parent effort | -0.766 | -0.973 | -0.207 | 12 down / 12 | 12 down / 12 |
| LSTM k5 | M11: age x parent effort | -0.766 | -0.921 | -0.156 | 12 down / 12 | 12 down / 12 |
| LSTM k3 | M15: expanded interactions | -0.791 | -0.845 | -0.054 | 12 down / 12 | 12 down / 12 |
| LSTM k4 | M15: expanded interactions | -0.791 | -0.968 | -0.177 | 12 down / 12 | 12 down / 12 |
| LSTM k5 | M15: expanded interactions | -0.791 | -0.914 | -0.123 | 12 down / 12 | 12 down / 12 |

### Matched Examples

These are illustrative matched rows where the real child utterance has much lower with-context surprisal than the control utterance in the same preceding context. They are examples, not statistical tests.

| source_label | dataset | child_id | age_months | context | real_child_utterance | control_utterance | real_k3_bits | control_k3_bits | control_minus_real_k3 | real_context_gain | control_context_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LSTM k3 | Providence | Alex | 37.6 | can't you sit still for two seconds? Alex you're gonna break those honey don't bang em. please. | don't don't drink the water don't don't drink the water don't don't drink the water don't don't drink the water don't d... | what have that noise too day mommy mommy to do this trick one this this like this or this one no this one this one this... | 68.93 | 470.34 | 401.41 | 3.75 | 23.26 |
| LSTM k3 | Brown | Adam | 43.2 | did I put that in there? yes. all set. | chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a... | i not going to find some milk milk mommy bear i have a drink of milk in there to eat you and a lunch for daddy to you c... | 52.05 | 300.83 | 248.78 | 12.72 | 5.78 |
| LSTM k3 | Brown | Eve | 18.0 | would you like your milk over there? that's a skunk. skunk. | paper pencil pencil pencil pencil pencil pencil pencil pencil paper paper pencil pencil pencil pencil pencil pencil pen... | more juice there juice back out car car there daddy in fraser too big up water paper out out the boat outside the water. | 62.76 | 233.86 | 171.1 | 15.23 | 23.92 |
| LSTM k3 | Providence | Naima | 34.6 | here you go. there's a puzzle piece. oh. | hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three... | um daddy lives to sleep at the top in the sky and the um um the orange and green bean and her and that's a purple and u... | 97.51 | 259.77 | 162.27 | 2.5 | 23.81 |
| LSTM k3 | Providence | William | 36.9 | we haven't done the alphabet. yeah. we haven't done that. | a b c d e f g h i j k l m n o p q r s t u v w x y and z now I know my abcs next time won't you sing with me okay. | a b one day a piece o e f g j j j j j j j j j k k k k k a little car don't don't know that we will want to put that ove... | 82.14 | 238.55 | 156.41 | 12.42 | 1.76 |
| LSTM k4 | Providence | Alex | 37.6 | can't you sit still for two seconds? Alex you're gonna break those honey don't bang em. please. | don't don't drink the water don't don't drink the water don't don't drink the water don't don't drink the water don't d... | see it with me daddy with it and it's it is a cat and this is um this is a black one white black white white triangle b... | 68.93 | 486.74 | 417.8 | 3.75 | 10.18 |
| LSTM k4 | Brown | Adam | 43.2 | did I put that in there? yes. all set. | chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a chug a... | yes please please please please please now a ball for warren while a lady with a drink the water don't don't don't spil... | 52.05 | 336.93 | 284.88 | 12.72 | 11.19 |
| LSTM k4 | Providence | Naima | 34.6 | here you go. there's a puzzle piece. oh. | hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three in a row hop up my ladies three... | there the neenaw is going to park on her on the floor then he didn't he says he's saying a a big present to you you're... | 97.51 | 303.71 | 206.2 | 2.5 | 24.41 |


## Real vs Caretakers

This section shows the no-context trajectory, the with-context trajectory, the context-gain trajectory, and the source-minus-real gap through age.

![Real vs Caretakers k0 vs k3](../figs/route1_real_vs_controls_context_report/caretaker_k0_vs_k3_age_means.png)

![Real vs Caretakers with context](../figs/route1_real_vs_controls_context_report/caretaker_k3_with_context_focus.png)

![Real vs Caretakers context gain](../figs/route1_real_vs_controls_context_report/caretaker_context_gain_by_age.png)

![Real vs Caretakers gaps](../figs/route1_real_vs_controls_context_report/caretaker_real_gap_by_age.png)

### Difference Models

For generated sources, `gap_k3` models ask whether the source-real contextual surprisal gap changes with age after child effort and child identity are controlled. `gain_gap` models ask whether the source benefits more or less from context than real children, and whether that difference changes with age.

| source | test | mean | age_slope | p | n |
| --- | --- | --- | --- | --- | --- |
| Caretaker | sum_bits_k3 | real 26.726; source 29.998 | source x age -0.033 | 0.327 | 1115888 |
| Caretaker | context_gain | real 13.607; source 19.410 | source x age -0.005 | 0.817 | 1115888 |

### Fixed-Effort Regression Lines

These figures show model-based developmental lines at the same production effort. This is the layer that separates communicative-efficiency evidence from ordinary age-related growth in utterance length.

![Real vs Caretakers fixed-effort regression lines](../figs/route1_real_vs_controls_context_report/caretaker_m2_k3_fixed_word_regression_lines.png)

![Real vs Caretakers fixed-effort regression gaps](../figs/route1_real_vs_controls_context_report/caretaker_m2_k3_fixed_word_regression_gaps.png)

![Real vs Caretakers model slope differences](../figs/route1_real_vs_controls_context_report/caretaker_k3_word_model_slope_differences.png)

Primary fixed-effort slope read under M2/CM2: Caretaker: source slope 0.172 vs real slope -0.735 bits per 6 months (source-real 0.907; real 12/12 downward lines, source 0/12).

Compact slope read: slopes are average bits per 6 months across the 12 fixed word-count lines. More negative values mean a stronger developmental decrease at fixed effort.

| source_label | model | real_slope_bits_per_6_months | source_slope_bits_per_6_months | source_minus_real_slope | real_line_directions | source_line_directions |
| --- | --- | --- | --- | --- | --- | --- |
| Caretaker | M2: identity + effort | -0.735 | 0.172 | 0.907 | 12 down / 12 | 0 down / 12 |
| Caretaker | M3: age x effort | -0.817 | 0.192 | 1.009 | 12 down / 12 | 0 down / 12 |
| Caretaker | M4c: question type | -0.854 | 0.174 | 1.027 | 12 down / 12 | 0 down / 12 |
| Caretaker | M5: context controls | -0.800 | 0.337 | 1.137 | 12 down / 12 | 0 down / 12 |
| Caretaker | M6: context interactions | -0.802 | 0.358 | 1.160 | 12 down / 12 | 0 down / 12 |

### Representative Context-Gain Examples

Caretaker utterances are not matched generated alternatives for the same child row, so examples are shown as representative high context-gain utterances for each source.

| source | dataset | child_id | age_months | context | utterance | k3_bits | context_gain | nb_words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Real child | Brown | Eve | 25.0 | we do:n't ha:ve a:ny gree:n bea:ns we will uhhuh. | we do:n't ha:ve a:ny gree:n bea:ns | 10.06 | 95.39 | 11 |
| Real child | Manchester | Becky | 26.5 | they're sitting on the um the. here you are. th-th-th↫there's one of them. | th-th-th↫there's one of them. | 12.38 | 92.96 | 7 |
| Real child | Providence | Lily | 29.2 | oh the barrette's gonna go into the store with the elephant? oh well that's nice. gonna ask him? | the barrette's gonn ask the elephant if he wants to go into the store with the elephant. | 51.62 | 88.09 | 17 |
| Caretaker | Providence | Lily | 27.6 | is that all? no that's not all I love you said mamma brown bear more than you love to catch this striped fish and this spotted fish. that's two fish said little brown bear. | right said mamma brown bear and I love you more than I love to rub my back against this tree and this tree and this tree mm that'... | 71.74 | 151.9 | 34 |
| Caretaker | Providence | Naima | 23.7 | Max waned red hot marshmallow squirters. for his earth worm cake so he wrote red hot marshmallow squirters on the list. he wrote it with a red crayon except he's a little bunny an... | he can't write he's a bunny but he's trying he's trying to write he wants to add red hot marshmallows squirters to the list so th... | 115.68 | 120.08 | 32 |
| Caretaker | Providence | William | 29.5 | down by the bay where the watermelons grow back to my home I dare not go for if I do my mother will say did ya ever see a fly wearing a tie down by the bay. down by the bay where... | down by the bay where the watermelons grow back to my home I dare not go for if I do my mother will say did ya ever see an apple... | 119.89 | 119.66 | 58 |


## Saved Artifacts

```text
results/route1_real_vs_controls_context_report/source_age_summary.csv
results/route1_real_vs_controls_context_report/paired_gap_summary.csv
results/route1_real_vs_controls_context_report/difference_model_summary.csv
results/route1_real_vs_controls_context_report/matched_examples.csv
results/route1_real_vs_controls_context_report/caretaker_examples.csv
results/route1_real_vs_controls_context_report/*_regression_line_predictions.csv
results/route1_real_vs_controls_context_report/*_regression_line_slopes.csv
results/route1_real_vs_controls_context_report/*_regression_line_slope_differences.csv
results/route1_real_vs_controls_context_report/*_regression_line_gaps.csv
figs/route1_real_vs_controls_context_report/
```
