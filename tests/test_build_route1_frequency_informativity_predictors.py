import math
import sys
import unittest
from collections import Counter
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_route1_frequency_informativity_predictors import (  # noqa: E402
    ReferenceCounts,
    score_phone_bigrams,
    score_unigrams,
    strip_stress,
    text_units,
)


class Route1FrequencyInformativityPredictorTests(unittest.TestCase):
    def test_strip_stress_removes_arpabet_digits(self):
        self.assertEqual(strip_stress("AH0"), "AH")
        self.assertEqual(strip_stress("B"), "B")

    def test_text_units_returns_words_and_phones(self):
        tokens, phones = text_units("big drum")

        self.assertEqual(tokens, ("big", "drum"))
        self.assertGreaterEqual(len(phones), 2)

    def test_score_unigrams_returns_sum_and_mean_bits(self):
        total_bits, mean_bits = score_unigrams(("a", "b"), Counter({"a": 3, "b": 1}))

        self.assertTrue(math.isfinite(total_bits))
        self.assertAlmostEqual(mean_bits, total_bits / 2)

    def test_score_phone_bigrams_uses_start_symbol(self):
        counts = ReferenceCounts(
            word_counts=Counter(),
            phone_counts=Counter({"B": 2, "IH": 2}),
            phone_bigram_counts=Counter({("<s>", "B"): 2, ("B", "IH"): 2}),
            phone_prev_counts=Counter({"<s>": 2, "B": 2}),
            utterance_counts=Counter(),
            row_count=2,
        )

        total_bits, mean_bits = score_phone_bigrams(("B", "IH"), counts)

        self.assertTrue(math.isfinite(total_bits))
        self.assertAlmostEqual(mean_bits, total_bits / 2)


if __name__ == "__main__":
    unittest.main()
