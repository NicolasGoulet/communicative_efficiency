from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.build_scorer_performance_comparison import (
    bootstrap_mean,
    summarize_overall,
)


class ScorerPerformanceComparisonTests(unittest.TestCase):
    def test_bootstrap_is_deterministic_and_contains_observed_mean(self) -> None:
        values = np.array([1.0, 2.0, 3.0, 4.0])
        first = bootstrap_mean(values, reps=2_000, seed=41)
        second = bootstrap_mean(values, reps=2_000, seed=41)
        reordered = bootstrap_mean(values[::-1], reps=2_000, seed=41)

        self.assertEqual(first, second)
        self.assertEqual(first, reordered)
        self.assertLess(first[0], values.mean())
        self.assertGreater(first[1], values.mean())

    def test_cross_tokenizer_rank_uses_bpc_not_bits_per_model_token(self) -> None:
        rows = []
        specifications = {
            "Mistral-7B": (2.0, 1.0),
            "Qwen3-14B": (1.5, 5.0),
            "TinyDialogues-135M": (2.5, 0.5),
        }
        for model, (bpc, bpt) in specifications.items():
            for child_index, corpus in enumerate(("Brown", "Manchester")):
                characters = 100 + child_index * 10
                words = 20 + child_index
                tokens = 25 + child_index
                rows.append(
                    {
                        "domain": "child_utterance",
                        "condition": "k3",
                        "model": model,
                        "dataset": corpus,
                        "child_key": f"{corpus}/child",
                        "n_items": 10,
                        "total_bits": bpc * characters,
                        "total_characters": characters,
                        "total_words": words,
                        "total_model_tokens": tokens,
                        "micro_bpc": bpc,
                        "micro_bpw": bpc * characters / words,
                        "micro_bpt": bpt,
                        "model_tokens_per_word": tokens / words,
                        "macro_bpc": bpc,
                        "median_bpc": bpc,
                    }
                )

        summary = summarize_overall(pd.DataFrame(rows), reps=1_000, seed=7)
        ranked = summary.sort_values("bpc_rank")

        self.assertEqual(
            ranked.model.tolist(),
            ["Qwen3-14B", "Mistral-7B", "TinyDialogues-135M"],
        )
        self.assertEqual(ranked.bpc_rank.tolist(), [1.0, 2.0, 3.0])
        self.assertEqual(
            summary.loc[summary.model == "TinyDialogues-135M", "child_balanced_bpt_diagnostic"].item(),
            0.5,
        )


if __name__ == "__main__":
    unittest.main()
