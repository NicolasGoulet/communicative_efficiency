import math
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_supervisor_report_todo_plots import age_mid, summarize_age_bins  # noqa: E402


class SupervisorReportTodoPlotsTests(unittest.TestCase):
    def test_age_mid_parses_bins(self):
        self.assertEqual(age_mid("024-029"), 26.5)
        self.assertTrue(math.isnan(age_mid("bad")))

    def test_summarize_age_bins_writes_expected_columns(self):
        frame = pd.DataFrame(
            {
                "age_bin": ["006-023", "006-023", "024-029"],
                "nb_words": [1, 3, 4],
                "sum_bits": [10.0, 20.0, 30.0],
                "mean_bits_per_token": [5.0, 4.0, 3.0],
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            summary = summarize_age_bins(frame, Path(tmp))

        self.assertIn("nb_words_mean", summary.columns)
        self.assertIn("sum_bits_mean", summary.columns)
        self.assertIn("mean_bits_per_token_mean", summary.columns)
        self.assertEqual(summary.iloc[0]["age_bin"], "006-023")


if __name__ == "__main__":
    unittest.main()
