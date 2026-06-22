import sys
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_route1_real_vs_controls_context_report import (
    compare_child_source,
    paired_gap_summary,
    prediction_gap_lines,
    primary_slope_takeaway,
    relative_to_doc,
    select_examples,
    slope_difference_summary,
    wide_from_long,
)


class Route1RealVsControlsContextReportTests(unittest.TestCase):
    def test_wide_from_long_computes_context_gain(self):
        long = pd.DataFrame(
            {
                "utterance_id": ["u1", "u1", "u2", "u2"],
                "dataset": ["D"] * 4,
                "child_id": ["Ada"] * 4,
                "session_id": ["s1"] * 4,
                "age_months": [24.0] * 4,
                "age_bin": ["024-029"] * 4,
                "role": ["child"] * 4,
                "target_variant": ["real"] * 4,
                "nb_words": [3, 3, 4, 4],
                "context_k": ["k0", "k3", "k0", "k3"],
                "sum_bits": [30.0, 20.0, 40.0, 25.0],
            }
        )

        wide = wide_from_long(long)

        self.assertEqual(len(wide), 2)
        first = wide.sort_values("utterance_id").iloc[0]
        self.assertEqual(first["sum_bits_k0"], 30.0)
        self.assertEqual(first["sum_bits_k3"], 20.0)
        self.assertEqual(first["context_gain"], 10.0)
        self.assertEqual(first["source_label"], "Real child")

    def test_compare_child_source_and_summary_use_paired_utterance_gaps(self):
        real = pd.DataFrame(
            {
                "utterance_id": ["u1", "u2"],
                "dataset": ["D", "D"],
                "child_id": ["Ada", "Ada"],
                "session_id": ["s1", "s1"],
                "age_months": [24.0, 24.0],
                "age_bin": ["024-029", "024-029"],
                "nb_words": [3, 4],
                "sum_bits_k0": [30.0, 40.0],
                "sum_bits_k3": [20.0, 25.0],
                "context_gain": [10.0, 15.0],
            }
        )
        control = pd.DataFrame(
            {
                "utterance_id": ["u1", "u2"],
                "sum_bits_k0": [45.0, 50.0],
                "sum_bits_k3": [33.0, 31.0],
                "context_gain": [12.0, 19.0],
                "nb_words": [3, 4],
                "source": ["random", "random"],
                "source_label": ["Random", "Random"],
            }
        )

        comp = compare_child_source(real, control)
        summary = paired_gap_summary(comp)

        self.assertEqual(list(comp["gap_k3"]), [13.0, 6.0])
        self.assertEqual(list(comp["gain_gap"]), [2.0, 4.0])
        self.assertAlmostEqual(float(summary.loc[0, "mean_gap_k3"]), 9.5)
        self.assertAlmostEqual(float(summary.loc[0, "mean_gain_gap"]), 3.0)

    def test_select_examples_keeps_positive_high_gap_rows(self):
        comp = pd.DataFrame(
            {
                "utterance_id": ["u1", "u2", "u3"],
                "child_id": ["Ada", "Ada", "Ben"],
                "age_bin": ["024-029", "024-029", "030-035"],
                "gap_k3": [5.0, 25.0, -1.0],
                "real_context_gain": [0.0, 4.0, 100.0],
                "source": ["random", "random", "random"],
            }
        )

        chosen = select_examples(comp, "random", 5)

        self.assertEqual(list(chosen["utterance_id"]), ["u2"])
        self.assertTrue((chosen["gap_k3"] > 0).all())

    def test_relative_to_doc_uses_report_relative_paths(self):
        rel = relative_to_doc(
            Path("figs/route1_real_vs_controls_context_report/random.png"),
            Path("docs/route1_real_vs_controls_context_report.md"),
        )

        self.assertEqual(rel, "../figs/route1_real_vs_controls_context_report/random.png")

    def test_slope_difference_summary_compares_source_to_real(self):
        slopes = pd.DataFrame(
            {
                "source": ["real", "real", "random", "random"],
                "source_label": ["Real child", "Real child", "Random", "Random"],
                "common_model_id": ["M2", "M2", "M2", "M2"],
                "common_model_label": ["identity + effort"] * 4,
                "slope_bits_per_6_months": [-1.0, -2.0, 1.0, 3.0],
                "direction": ["downward", "downward", "upward", "upward"],
            }
        )

        summary = slope_difference_summary(slopes, ["random"])
        takeaway = primary_slope_takeaway(summary)

        self.assertAlmostEqual(float(summary.loc[0, "real_slope_bits_per_6_months"]), -1.5)
        self.assertAlmostEqual(float(summary.loc[0, "source_slope_bits_per_6_months"]), 2.0)
        self.assertAlmostEqual(float(summary.loc[0, "source_minus_real_slope"]), 3.5)
        self.assertIn("real 2/2 downward lines, source 0/2", takeaway)

    def test_prediction_gap_lines_interpolates_source_minus_real(self):
        predictions = pd.DataFrame(
            {
                "source": ["real", "real", "random", "random"],
                "source_label": ["Real child", "Real child", "Random", "Random"],
                "age_months": [20.0, 30.0, 20.0, 30.0],
                "fixed_effort_value": [2, 2, 2, 2],
                "predicted_sum_bits": [10.0, 8.0, 20.0, 23.0],
            }
        )

        gaps = prediction_gap_lines(predictions, ["random"])

        self.assertEqual(list(gaps["predicted_gap"]), [10.0, 15.0])


if __name__ == "__main__":
    unittest.main()
