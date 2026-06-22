import sys
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_supervisor_proposed_completion_report import (  # noqa: E402
    md_table,
    primary_slope_table,
    source_overview_table,
    weighted_mean,
)


class SupervisorProposedCompletionReportTests(unittest.TestCase):
    def test_weighted_mean_uses_row_counts(self):
        frame = pd.DataFrame({"mean_bits": [10.0, 20.0], "n": [1, 3]})

        self.assertAlmostEqual(weighted_mean(frame, "mean_bits"), 17.5)

    def test_source_overview_table_formats_weighted_source_summary(self):
        frame = pd.DataFrame(
            {
                "source_label": ["Real child", "Real child", "Random"],
                "n": [10, 30, 20],
                "mean_sum_bits_k0": [20.0, 40.0, 80.0],
                "mean_sum_bits_k3": [10.0, 30.0, 70.0],
                "mean_context_gain": [10.0, 10.0, 10.0],
                "mean_nb_words": [2.0, 4.0, 3.0],
            }
        )

        table = source_overview_table(frame)

        self.assertEqual(list(table["source"]), ["Real child", "Random"])
        self.assertEqual(table.loc[0, "rows"], "40")
        self.assertEqual(table.loc[0, "mean_k3"], "25.00")
        self.assertEqual(table.loc[1, "mean_k0"], "80.00")

    def test_primary_slope_table_orders_and_formats_controls(self):
        frame = pd.DataFrame(
            {
                "source_label": ["Random", "LSTM k3"],
                "common_model_id": ["M2", "M2"],
                "real_slope_bits_per_6_months": [-0.7, -0.7],
                "source_slope_bits_per_6_months": [1.0, -0.2],
                "source_minus_real_slope": [1.7, 0.5],
                "downward_lines": [0, 12],
                "total_lines": [12, 12],
            }
        )

        table = primary_slope_table(frame)

        self.assertEqual(list(table["comparison source"]), ["Random", "LSTM k3"])
        self.assertEqual(table.loc[0, "source downward lines"], "0/12")
        self.assertEqual(table.loc[1, "source slope"], "-0.200")

    def test_md_table_escapes_pipe_characters(self):
        table = md_table(pd.DataFrame({"a": ["x|y"]}), ["a"])

        self.assertIn("x\\|y", table)


if __name__ == "__main__":
    unittest.main()
