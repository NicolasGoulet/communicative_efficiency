# Direct-Surprisal Sustained-Onset Confirmation

This report applies the onset rule frozen on 21 July 2026 to the real-child
Mistral k3 exact/top-coded word-effort design cells. The reference category is
`006-023`. Uncertainty is produced by resampling children and using a
simultaneous 95% max-absolute-studentized-deviation band across the seven
post-reference contrasts.

## Result

- PBM discovery sustained onset: `not_established`.
- Non-PBM confirmation sustained onset: `not_established`.
- Confirmation bootstrap fits: `1000` / `1000`.
- A confirmation bin is eligible for the rule only with at least five children
  and three corpora.

![Simultaneous child-bootstrap onset bands](../figs/direct_surprisal_onset_confirmation/age_bin_simultaneous_bands.png)

| scope | age_bin | estimate_vs_006_023 | simultaneous_ci_low | simultaneous_ci_high | children | corpora | adequately_supported |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pbm_discovery | 024-029 | -0.897 | -1.806 | 0.012 | 21.000 | 3.000 | 1.000 |
| pbm_discovery | 030-035 | -2.031 | -3.180 | -0.882 | 20.000 | 3.000 | 1.000 |
| pbm_discovery | 036-041 | -1.934 | -4.315 | 0.446 | 8.000 | 3.000 | 1.000 |
| pbm_discovery | 042-047 | -4.215 | -8.413 | -0.017 | 5.000 | 2.000 | 0.000 |
| pbm_discovery | 048-053 | -2.647 | -5.187 | -0.108 | 3.000 | 2.000 | 0.000 |
| pbm_discovery | 054-059 | -3.275 | -6.551 | 0.000 | 2.000 | 1.000 | 0.000 |
| pbm_discovery | 060-065 | -5.378 | -11.218 | 0.462 | 2.000 | 1.000 | 0.000 |
| non_pbm_confirmation | 024-029 | 0.413 | -1.216 | 2.043 | 50.000 | 10.000 | 1.000 |
| non_pbm_confirmation | 030-035 | -1.158 | -2.977 | 0.662 | 50.000 | 10.000 | 1.000 |
| non_pbm_confirmation | 036-041 | -1.603 | -3.203 | -0.003 | 53.000 | 9.000 | 1.000 |
| non_pbm_confirmation | 042-047 | -1.639 | -3.350 | 0.071 | 35.000 | 8.000 | 1.000 |
| non_pbm_confirmation | 048-053 | -1.398 | -3.062 | 0.267 | 12.000 | 4.000 | 1.000 |
| non_pbm_confirmation | 054-059 | -1.308 | -3.127 | 0.511 | 18.000 | 6.000 | 1.000 |
| non_pbm_confirmation | 060-065 | -2.418 | -4.947 | 0.111 | 7.000 | 5.000 | 1.000 |

## Interpretation

An onset is not the first nominally significant coefficient. It is the first
adequately supported post-reference bin whose upper simultaneous band is below
zero and for which every later adequately supported bin also remains below
zero. If the confirmation result is `not_established`, the prior PBM statement
that the first row-level decrease appears by 24–29 months remains exploratory
and must not be promoted as a replicated developmental onset.

These bands use the frozen lexical-word effort definition. Full-79 validated
morpheme, syllable, and phoneme controls are not yet available, so this report
does not satisfy that separate alternative-effort validation requirement.
