# Promotion Plan

This page is the decision layer: what should move into the clean July supervisor-facing pages, and what should stay as working evidence for now.

## What To Promote

| candidate | promote_now | why | caveat |
| --- | --- | --- | --- |
| CE onset map | Yes | Directly answers when the signal appears. | Add child bootstrap before treating it as final. |
| Fixed-word-count age-bin model | Yes | Matches the earlier Route 1 downward-trend model family. | State that the child-age aggregate sensitivity changes the weighting. |
| Paired real-vs-trigram gap | Yes | Same context and same generated-baseline family; easy to explain. | Use as comparison evidence, not as a full causal claim. |
| Bayes decomposition | Maybe | Scientifically useful alternative to direct Mistral surprisal. | Label as unnormalized until p(c) is estimated or explicitly conditioned away. |
| Complexity metrics | Yes | They answer the supervisor concern that we returned to the initial project formulation. | Use as controls/descriptors, not as replacement CE outcomes. |

## Immediate Next Steps

| step | reason |
| --- | --- |
| Bootstrap onset table by child | Protects against pseudo-replication and reviewer criticism. |
| Repeat onset with morpheme, syllable, and phoneme controls | Checks whether timing survives alternative effort definitions. |
| Move one curated onset figure into the July developmental page | Keeps the supervisor-facing report readable. |
| Keep Bayes as a working/additional analysis until wording is locked | The decomposition is useful, but still needs careful normalizer language. |

## Suggested Supervisor-Facing Structure

1. Put the onset map and fixed-word-count age-bin model in `Developmental Trajectory of Communicative Efficiency`.
2. Put the Bayes decomposition as a short "alternative information formulation" subsection in `Predicting Utterance Informativeness`.
3. Put MLU, syllable/phoneme proxies, vocabulary size, and TTR in `Predicting Utterance Production Effort`.
4. Keep implementation details, repo paths, and Mila logistics out of the supervisor-facing pages.
