import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_existing_scored_baseline_efficiency_cloud import (  # noqa: E402
    add_plot_columns,
    age_bin_midpoint,
    accumulate_summary,
    finalize_summary,
    response_entropy_edges,
    summarize_chunk,
)


class ExistingScoredBaselineEfficiencyCloudTests(unittest.TestCase):
    def test_age_bin_midpoint(self):
        self.assertEqual(age_bin_midpoint("006-023"), 14.5)
        self.assertEqual(age_bin_midpoint("024-029"), 26.5)
        self.assertTrue(np.isnan(age_bin_midpoint("missing")))

    def test_response_entropy_edges_make_ordered_bins(self):
        edges, labels = response_entropy_edges(pd.Series([1, 2, 3, 4, 5, 6, 7, 8]))

        self.assertEqual(len(edges) - 1, len(labels))
        self.assertEqual(labels, ["low", "mid-low", "mid-high", "high"])
        self.assertTrue(np.isneginf(edges[0]))
        self.assertTrue(np.isposinf(edges[-1]))

    def test_add_plot_columns_labels_sources_and_entropy_bins(self):
        frame = pd.DataFrame(
            {
                "target_variant": ["real", "lstm_additive_k3_same_length"],
                "age_bin": ["006-023", "024-029"],
                "nb_words": [2, 14],
                "response_entropy_bits": [1.5, 7.5],
            }
        )
        edges, labels = response_entropy_edges(pd.Series([1, 2, 3, 4, 5, 6, 7, 8]))

        out = add_plot_columns(frame, edges, labels)

        self.assertEqual(out.loc[0, "source_label"], "Real child")
        self.assertEqual(out.loc[1, "source_label"], "LSTM k3")
        self.assertEqual(out.loc[0, "nb_words_bucket"], "2")
        self.assertEqual(out.loc[1, "nb_words_bucket"], "13+")
        self.assertEqual(out.loc[0, "age_bin_mid"], 14.5)
        self.assertIn(out.loc[0, "response_entropy_bin"], labels)

    def test_summarize_accumulate_finalize(self):
        frame = pd.DataFrame(
            {
                "target_variant": ["real", "real", "random"],
                "source_label": ["Real child", "Real child", "Random"],
                "age_bin": ["006-023", "006-023", "006-023"],
                "age_bin_mid": [14.5, 14.5, 14.5],
                "sum_bits": [10.0, 20.0, 30.0],
                "nb_words": [1.0, 3.0, 5.0],
            }
        )
        group_cols = ["target_variant", "source_label", "age_bin", "age_bin_mid"]

        first = summarize_chunk(frame.iloc[:2], group_cols, ["sum_bits", "nb_words"])
        second = summarize_chunk(frame.iloc[2:], group_cols, ["sum_bits", "nb_words"])
        accumulated = accumulate_summary(first, second, group_cols)
        out = finalize_summary(accumulated, group_cols, ["sum_bits", "nb_words"])

        real = out[out["source_label"].eq("Real child")].iloc[0]
        random = out[out["source_label"].eq("Random")].iloc[0]
        self.assertEqual(real["n"], 2)
        self.assertEqual(random["n"], 1)
        self.assertAlmostEqual(real["mean_sum_bits"], 15.0)
        self.assertAlmostEqual(real["mean_nb_words"], 2.0)
        self.assertAlmostEqual(random["mean_sum_bits"], 30.0)


if __name__ == "__main__":
    unittest.main()
