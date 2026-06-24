# Real, Baseline, and Caretaker Regression Lines

Fixed-word `k3` regression-line comparisons. Tables report the plotted line slopes in bits per six months.

Shaded bands in the source figures are fitted-mean confidence bands where available.

## Overview Plots

Two compact ANCOVA-style views before the detailed source-by-source regression-line dump.

<div class="figure-grid">
<figure>
<img src="../figs/route1_exhaustive_ancova_gallery/child_sources_adjusted_sum_bits_k3_by_effort.png" alt="ANCOVA adjusted source trajectories: k3 sum bits by effort measure, controlling child identity and effort">
<figcaption>ANCOVA adjusted source trajectories: k3 sum bits by effort measure, controlling child identity and effort</figcaption>
</figure>
<figure>
<img src="../figs/route1_exhaustive_ancova_gallery/nb_words_sum_bits_k3_source_minus_real_gap_lines.png" alt="Words-controlled ANCOVA source-minus-real gaps: zero is the real-child fitted trajectory">
<figcaption>Words-controlled ANCOVA source-minus-real gaps: zero is the real-child fitted trajectory</figcaption>
</figure>
</div>

## M2: age + words + identity

| source | lines | mean slope / 6 mo | range / 6 mo | downward lines |
| --- | --- | --- | --- | --- |
| Real child | 12 | -0.735 | -0.735 to -0.735 | 12/12 |
| Random | 12 | 1.068 | 1.068 to 1.068 | 0/12 |
| Unigram | 12 | -0.125 | -0.125 to -0.125 | 12/12 |
| Bigram | 12 | -0.134 | -0.134 to -0.134 | 12/12 |
| Trigram | 12 | -0.092 | -0.092 to -0.092 | 12/12 |
| LSTM k3 | 12 | -0.279 | -0.279 to -0.279 | 12/12 |
| LSTM k4 | 12 | -0.351 | -0.351 to -0.351 | 12/12 |
| LSTM k5 | 12 | -0.363 | -0.363 to -0.363 | 12/12 |
| Caretaker | 12 | 0.172 | 0.172 to 0.172 | 0/12 |

<div class="figure-grid">
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m2_nb_words_fixed_effort_atlas.png" alt="Real child">
<figcaption>Real child</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m2_nb_words_fixed_effort_atlas.png" alt="Random">
<figcaption>Random</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m2_nb_words_fixed_effort_atlas.png" alt="Unigram">
<figcaption>Unigram</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m2_nb_words_fixed_effort_atlas.png" alt="Bigram">
<figcaption>Bigram</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m2_nb_words_fixed_effort_atlas.png" alt="Trigram">
<figcaption>Trigram</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m2_nb_words_fixed_effort_atlas.png" alt="LSTM k3">
<figcaption>LSTM k3</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m2_nb_words_fixed_effort_atlas.png" alt="LSTM k4">
<figcaption>LSTM k4</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m2_nb_words_fixed_effort_atlas.png" alt="LSTM k5">
<figcaption>LSTM k5</figcaption>
</figure>
<figure class="centered">
<img src="../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm2_nb_words_fixed_effort_atlas.png" alt="Caretaker">
<figcaption>Caretaker</figcaption>
</figure>
</div>

## M3: M2 plus age-by-words

| source | lines | mean slope / 6 mo | range / 6 mo | downward lines |
| --- | --- | --- | --- | --- |
| Real child | 12 | -0.817 | -0.942 to -0.692 | 12/12 |
| Random | 12 | 1.265 | 0.965 to 1.565 | 0/12 |
| Unigram | 12 | -0.754 | -1.713 to 0.205 | 10/12 |
| Bigram | 12 | -0.662 | -1.468 to 0.144 | 11/12 |
| Trigram | 12 | -0.354 | -0.754 to 0.045 | 11/12 |
| LSTM k3 | 12 | -0.744 | -1.453 to -0.035 | 12/12 |
| LSTM k4 | 12 | -0.879 | -1.685 to -0.073 | 12/12 |
| LSTM k5 | 12 | -0.816 | -1.507 to -0.125 | 12/12 |
| Caretaker | 12 | 0.192 | 0.132 to 0.252 | 0/12 |

<div class="figure-grid">
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m3_nb_words_fixed_effort_atlas.png" alt="Real child">
<figcaption>Real child</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m3_nb_words_fixed_effort_atlas.png" alt="Random">
<figcaption>Random</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m3_nb_words_fixed_effort_atlas.png" alt="Unigram">
<figcaption>Unigram</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m3_nb_words_fixed_effort_atlas.png" alt="Bigram">
<figcaption>Bigram</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m3_nb_words_fixed_effort_atlas.png" alt="Trigram">
<figcaption>Trigram</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m3_nb_words_fixed_effort_atlas.png" alt="LSTM k3">
<figcaption>LSTM k3</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m3_nb_words_fixed_effort_atlas.png" alt="LSTM k4">
<figcaption>LSTM k4</figcaption>
</figure>
<figure>
<img src="../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m3_nb_words_fixed_effort_atlas.png" alt="LSTM k5">
<figcaption>LSTM k5</figcaption>
</figure>
<figure class="centered">
<img src="../figs/route1_caretaker_corrected_fixed_effort_atlas/caretaker_k3_cm3_nb_words_fixed_effort_atlas.png" alt="Caretaker">
<figcaption>Caretaker</figcaption>
</figure>
</div>
