# Optimality Checks

Baseline-based counterfactual checks for the original optimality question. These use scored generated alternatives that are already matched to the real child utterance.

Matching rule: same utterance id, same `k3` caretaker context, and exact same word count.

Technical direction: lower `k3` total bits means lower surprisal under the context. `context_gain = k0 sum_bits - k3 sum_bits`; positive real-minus-baseline gain means the real utterance benefits more from the context.

## Way 1: Same-Effort Percentile

For each real utterance, rank the real `k3` total bits among the seven matched baselines.

How obtained: each row uses the same child utterance id, same `k3` caretaker context, and exact same word count. Negative real-minus-baseline bits means the real utterance is less surprising than the matched baseline.

| comparison | matched rows | word mismatches | mean real-baseline k3 bits | median real-baseline k3 bits | mean real-baseline context gain | baseline higher k3 bits |
| --- | --- | --- | --- | --- | --- | --- |
| Real vs Random | 446,508 | 0 | -34.40 | -25.23 | 5.76 | 96.5% |
| Real vs Unigram | 446,508 | 0 | -15.12 | -11.39 | 4.27 | 83.6% |
| Real vs Bigram | 446,508 | 0 | -10.08 | -7.71 | 2.81 | 75.0% |
| Real vs Trigram | 446,508 | 0 | -6.96 | -4.49 | 1.75 | 66.3% |
| Real vs LSTM k3 | 446,508 | 0 | -1.71 | -1.54 | 2.24 | 56.5% |
| Real vs LSTM k4 | 446,508 | 0 | -1.80 | -1.57 | 2.14 | 56.6% |
| Real vs LSTM k5 | 446,508 | 0 | -1.80 | -1.61 | 2.16 | 56.8% |
| Real vs all seven baselines | 446,508 | 0 | -7.60 | -6.32 | 3.18 | 70.2% |

Plot note: the percentile panel shows where the real utterance falls among the seven baseline alternatives; the share panel shows how often baseline alternatives have higher `k3` bits; the gap panel shows real minus the median baseline.

<div class="figure-grid">
<figure class="centered">
<img src="../figs/june_25_optimality_checks/same_effort_percentile_by_age.png" alt="Same-context, same-word-count position among baseline alternatives.">
<figcaption>Same-context, same-word-count position among baseline alternatives.</figcaption>
</figure>
</div>

## Way 2: Effort-Information Frontier

Compare the real child effort-information curve to the envelope formed by the matched baseline sources.

This is descriptive: it groups by exact effort value and plots means. It does not control for age, child identity, or time; age-stratified/frontier models would be a separate follow-up.

Words are exact-matched by construction. Morphemes, syllables, and phonemes are measured effort dimensions of the same matched utterances, not additional matching constraints.

How obtained: rows are grouped by exact effort value. The real line is the mean real child value. The grey band is the range of baseline source means. The dashed line is the best baseline frontier: lowest total bits on the left, largest context-driven reduction on the right.

Plot direction: the right panel displays `k3 - k0` rather than `k0 - k3`, so larger context-driven reductions appear lower on the y-axis, matching the total-bits panel.

| effort unit | frontier metric | weighted mean | min exact-effort gap | max exact-effort gap | exact effort values |
| --- | --- | --- | --- | --- | --- |
| Words | Real minus lowest baseline total-bits frontier | -1.60 | -13.37 | -0.33 | 1-12 |
| Words | Real minus median baseline total bits | -6.81 | -39.95 | -2.21 | 1-12 |
| Words | Real minus highest baseline context-gain frontier | 1.74 | 1.30 | 3.25 | 1-12 |
| Words | Real minus median baseline context gain | 2.24 | 1.96 | 4.34 | 1-12 |
| Morphemes | Real minus lowest baseline total-bits frontier | -2.09 | -17.02 | -0.31 | 1-12 |
| Morphemes | Real minus median baseline total bits | -6.83 | -35.60 | -2.04 | 1-12 |
| Morphemes | Real minus highest baseline context-gain frontier | 1.76 | 1.24 | 2.85 | 1-12 |
| Morphemes | Real minus median baseline context gain | 2.22 | 1.60 | 4.09 | 1-12 |
| Syllables | Real minus lowest baseline total-bits frontier | -3.42 | -13.59 | -1.80 | 1-12 |
| Syllables | Real minus median baseline total bits | -6.51 | -25.64 | -2.70 | 1-12 |
| Syllables | Real minus highest baseline context-gain frontier | 1.66 | 0.62 | 3.15 | 1-12 |
| Syllables | Real minus median baseline context gain | 2.06 | 0.90 | 3.92 | 1-12 |
| Phonemes | Real minus lowest baseline total-bits frontier | -3.47 | -6.72 | -1.71 | 2-13 |
| Phonemes | Real minus median baseline total bits | -5.07 | -11.80 | -2.27 | 2-13 |
| Phonemes | Real minus highest baseline context-gain frontier | 1.23 | -1.13 | 2.32 | 2-13 |
| Phonemes | Real minus median baseline context gain | 1.65 | -0.07 | 2.68 | 2-13 |

<div class="figure-grid">
<figure>
<img src="../figs/june_25_optimality_checks/effort_information_frontier_nb_words.png" alt="Words effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.">
<figcaption>Words effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.</figcaption>
</figure>
<figure>
<img src="../figs/june_25_optimality_checks/effort_information_frontier_nb_morphemes.png" alt="Morphemes effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.">
<figcaption>Morphemes effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.</figcaption>
</figure>
<figure>
<img src="../figs/june_25_optimality_checks/effort_information_frontier_nb_syllables_cmu_or_pkg.png" alt="Syllables effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.">
<figcaption>Syllables effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.</figcaption>
</figure>
<figure>
<img src="../figs/june_25_optimality_checks/effort_information_frontier_nb_phonemes.png" alt="Phonemes effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.">
<figcaption>Phonemes effort frontier. The grey band is the range of baseline source means; dashed lines mark the best baseline frontier for each panel.</figcaption>
</figure>
</div>

## Way 3: Context-Gain Advantage

Compare how much the previous caretaker context reduces surprisal for the real child utterance versus each matched baseline.

How obtained: `context_gain = k0 sum_bits - k3 sum_bits`. Positive real-minus-baseline context gain means the same caretaker context reduces surprisal more for the real child utterance than for the generated alternative.

This repeats the context-gain column from Way 1, but shows it by age and baseline type.

<div class="figure-grid">
<figure class="centered">
<img src="../figs/june_25_optimality_checks/context_gain_advantage_by_age.png" alt="Real-minus-baseline context gain by age.">
<figcaption>Real-minus-baseline context gain by age.</figcaption>
</figure>
</div>

## Saved Artifacts

```text
results/june_25_optimality_checks/matched_pairwise_baseline_gaps.csv.gz
results/june_25_optimality_checks/baseline_set_position_by_utterance.csv.gz
results/june_25_optimality_checks/same_effort_baseline_summary.csv
results/june_25_optimality_checks/effort_frontier_by_exact_effort.csv
results/june_25_optimality_checks/effort_frontier_summary.csv
figs/june_25_optimality_checks/
```
