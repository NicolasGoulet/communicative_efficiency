from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.build_direct_surprisal_onset_confirmation import AGE_ORDER, fit_bootstrap_bands


class DirectSurprisalOnsetConfirmationTests(unittest.TestCase):
    def synthetic_cells(self, sustained: bool = True) -> pd.DataFrame:
        rng = np.random.default_rng(4)
        rows = []
        for corpus in range(3):
            for child in range(2):
                child_key = f"Corpus{corpus}/Child{child}"
                child_offset = rng.normal(0, 0.2)
                child_slope = -0.8 + rng.normal(0, 0.08)
                for age_index, age_bin in enumerate(AGE_ORDER):
                    effect = 0.0 if age_index == 0 else (child_slope * age_index if sustained else rng.normal(0, 0.1))
                    for words in ("1", "2", "3"):
                        rows.append(
                            {
                                "dataset": f"Corpus{corpus}",
                                "child_key": child_key,
                                "age_months": 20 + age_index * 6,
                                "age_bin": age_bin,
                                "word_count_exact_top12": words,
                                "outcome_mean": 10 + child_offset + 2 * int(words) + effect,
                                "row_count": 10,
                            }
                        )
        return pd.DataFrame(rows)

    def test_sustained_negative_pattern_establishes_first_post_reference_bin(self) -> None:
        contrasts, draws, audit = fit_bootstrap_bands(
            self.synthetic_cells(sustained=True), reps=100, seed=7
        )
        self.assertEqual(audit["sustained_onset"], "024-029")
        self.assertEqual(len(draws), 100)
        self.assertTrue((contrasts["simultaneous_ci_high"] < 0).all())
        self.assertTrue((contrasts["adequately_supported"] == 1).all())

    def test_support_gate_prevents_onset(self) -> None:
        frame = self.synthetic_cells(sustained=True)
        frame = frame[frame["child_key"].str.startswith("Corpus0/")].copy()
        _, _, audit = fit_bootstrap_bands(frame, reps=60, seed=8)
        self.assertEqual(audit["sustained_onset"], "not_established")


if __name__ == "__main__":
    unittest.main()
