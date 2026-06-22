import math
import sys
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_route1_exhaustive_ancova_gallery import (  # noqa: E402
    age_bin_mid,
    fdr_bh,
    md_table,
    split_csv,
    strongest_gap_summary,
)


class Route1ExhaustiveAncovaGalleryTests(unittest.TestCase):
    def test_age_bin_mid_uses_numeric_bounds(self):
        self.assertAlmostEqual(age_bin_mid("024-029"), 26.5)
        self.assertTrue(math.isnan(age_bin_mid("bad")))

    def test_fdr_bh_is_monotone_for_sorted_p_values(self):
        adjusted = fdr_bh([0.001, 0.02, 0.03, 0.8])

        self.assertEqual(len(adjusted), 4)
        self.assertLessEqual(adjusted[0], adjusted[1])
        self.assertLessEqual(adjusted[1], adjusted[2])
        self.assertLessEqual(adjusted[2], adjusted[3])
        self.assertAlmostEqual(adjusted[0], 0.004)

    def test_split_csv_ignores_empty_parts(self):
        self.assertEqual(split_csv("nb_words, nb_phonemes,,"), ["nb_words", "nb_phonemes"])

    def test_md_table_escapes_pipes(self):
        text = md_table(pd.DataFrame({"a": ["x|y"]}))

        self.assertIn("x\\|y", text)

    def test_strongest_gap_summary_selects_largest_absolute_gap(self):
        frame = pd.DataFrame(
            {
                "source_label": ["Random", "Random"],
                "effort_label": ["Words", "Words"],
                "outcome_label": ["With-context information", "With-context information"],
                "age_bin": ["024-029", "030-035"],
                "source_minus_real": [1.0, -5.0],
                "real_adjusted_mean": [10.0, 20.0],
                "source_adjusted_mean": [11.0, 15.0],
            }
        )

        summary = strongest_gap_summary(frame)

        self.assertEqual(summary.iloc[0]["age bin"], "030-035")
        self.assertEqual(summary.iloc[0]["source-real"], "-5.00")


if __name__ == "__main__":
    unittest.main()
