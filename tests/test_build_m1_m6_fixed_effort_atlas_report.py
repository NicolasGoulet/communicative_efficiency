import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.build_m1_m6_fixed_effort_atlas_report import (
    build_fixed_effort_atlas,
    effort_bin_definitions,
    fixed_slice_slopes,
)


class FixedEffortAtlasReportTests(unittest.TestCase):
    def test_effort_bin_definitions_use_requested_and_top_frequency_slices(self):
        selected = pd.DataFrame(
            [
                {
                    "effort_col": "nb_phonemes",
                    "effort_label": "Phonemes",
                    "proposal_set": "top_frequency_12",
                    "fixed_effort_value": value,
                }
                for value in [1, 2, 3, 4, 5, 7, 9, 11, 14, 18, 22, 30]
            ]
        )

        bins = effort_bin_definitions(selected)

        word_bins = bins[bins["effort_col"].eq("nb_words")]
        self.assertEqual(list(word_bins["atlas_bin"]), ["1-4", "5-8", "9-12"])
        self.assertEqual(word_bins.iloc[0]["fixed_values"], "1, 2, 3, 4")

        phoneme_bins = bins[bins["effort_col"].eq("nb_phonemes")]
        self.assertEqual(len(phoneme_bins), 3)
        self.assertEqual(list(phoneme_bins["n_fixed_values"]), [4, 4, 4])
        self.assertIn("30", phoneme_bins.iloc[-1]["fixed_values"])

    def test_fixed_slice_slopes_are_descriptive_age_trajectories(self):
        predictions = pd.DataFrame(
            {
                "model_id": ["M1", "M1", "M1", "M1"],
                "model_title": ["test", "test", "test", "test"],
                "effort_col": ["nb_words", "nb_words", "nb_words", "nb_words"],
                "effort_label": ["Words", "Words", "Words", "Words"],
                "fixed_effort_value": [1, 1, 2, 2],
                "age_months": [10, 20, 10, 20],
                "predicted_sum_bits": [30, 20, 10, 16],
                "pred_ci_low": [29, 19, 9, 15],
                "pred_ci_high": [31, 21, 11, 17],
            }
        )
        bin_defs = pd.DataFrame(
            {
                "effort_col": ["nb_words"],
                "effort_label": ["Words"],
                "atlas_bin": ["1-4"],
                "fixed_values": ["1, 2, 3, 4"],
            }
        )

        slopes = fixed_slice_slopes(predictions, bin_defs)

        one_word = slopes[slopes["fixed_effort_value"].eq(1)].iloc[0]
        two_words = slopes[slopes["fixed_effort_value"].eq(2)].iloc[0]
        self.assertLess(one_word["slope_bits_per_month"], 0)
        self.assertGreater(two_words["slope_bits_per_month"], 0)
        self.assertEqual(one_word["atlas_bin"], "1-4")

    def test_build_fixed_effort_atlas_writes_interpretable_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixed = root / "fixed"
            audit = root / "audit"
            out = root / "out"
            figs = root / "figs"
            source_figs = root / "source_figs"
            fixed.mkdir()
            audit.mkdir()
            source_figs.mkdir()

            summary_cols = [
                "model_id",
                "model_title",
                "question",
                "effort_label",
                "n_obs",
                "n_children",
                "r2_observed_fitted",
                "age_coef",
                "age_p",
                "effort_coef",
                "effort_p",
                "entropy_coef",
                "entropy_p",
                "age_effort_coef",
                "age_effort_p",
                "age_entropy_coef",
                "age_entropy_p",
                "effort_entropy_coef",
                "effort_entropy_p",
            ]
            pd.DataFrame(
                [
                    {
                        "model_id": "M1",
                        "model_title": "Pooled age and effort",
                        "question": "test question",
                        "effort_label": "Words",
                        "n_obs": 40,
                        "n_children": 3,
                        "r2_observed_fitted": 0.41,
                        "age_coef": -0.2,
                        "age_p": 0.01,
                        "effort_coef": 2.0,
                        "effort_p": 0.001,
                        "entropy_coef": np.nan,
                        "entropy_p": np.nan,
                        "age_effort_coef": np.nan,
                        "age_effort_p": np.nan,
                        "age_entropy_coef": np.nan,
                        "age_entropy_p": np.nan,
                        "effort_entropy_coef": np.nan,
                        "effort_entropy_p": np.nan,
                    }
                ],
                columns=summary_cols,
            ).to_csv(fixed / "fixed_effort_model_summary.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "effort_col": "nb_words",
                        "effort_label": "Words",
                        "proposal_set": "requested_dense_1_12",
                        "fixed_effort_value": value,
                    }
                    for value in range(1, 13)
                ]
                + [
                    {
                        "effort_col": "nb_phonemes",
                        "effort_label": "Phonemes",
                        "proposal_set": "top_frequency_12",
                        "fixed_effort_value": value,
                    }
                    for value in [1, 2, 3, 4, 5, 7, 9, 11, 14, 18, 22, 30]
                ]
            ).to_csv(fixed / "selected_fixed_effort_values.csv", index=False)
            prediction_rows = []
            for fixed_value in [1, 2, 3, 4]:
                for age in [10, 20, 30]:
                    prediction_rows.append(
                        {
                            "model_id": "M1",
                            "model_title": "Pooled age and effort",
                            "question": "test question",
                            "effort_col": "nb_words",
                            "effort_label": "Words",
                            "fixed_effort_value": fixed_value,
                            "age_months": age,
                            "predicted_sum_bits": 50 - age + fixed_value,
                            "pred_ci_low": 49 - age + fixed_value,
                            "pred_ci_high": 51 - age + fixed_value,
                        }
                    )
            pd.DataFrame(prediction_rows).to_csv(fixed / "fixed_effort_predictions.csv", index=False)
            distribution_rows = []
            for effort_col, effort_label in [("nb_words", "Words"), ("nb_phonemes", "Phonemes")]:
                for value in range(1, 13):
                    distribution_rows.append(
                        {
                            "effort_col": effort_col,
                            "effort_label": effort_label,
                            "effort_value": value,
                            "rows": 10,
                            "n_children": 3,
                            "n_age_bins": 2,
                        }
                    )
            pd.DataFrame(distribution_rows).to_csv(audit / "effort_value_distribution.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "effort_col": "nb_words",
                        "effort_label": "Words",
                        "age_bin": "006-023",
                        "effort_value": value,
                        "rows": 5,
                        "n_children": 2,
                    }
                    for value in range(1, 13)
                ]
            ).to_csv(audit / "effort_by_age_bin_distribution.csv", index=False)

            outputs = build_fixed_effort_atlas(
                fixed_output_dir=fixed,
                effort_audit_dir=audit,
                output_dir=out,
                fig_dir=figs,
                source_fig_dir=source_figs,
                md_path=root / "atlas.md",
                html_path=root / "atlas.html",
            )

            self.assertTrue(outputs["html"].exists())
            self.assertTrue(outputs["slopes"].exists())
            self.assertTrue(outputs["fit_summary"].exists())
            self.assertTrue(outputs["predictor_summary"].exists())
            text = outputs["md"].read_text(encoding="utf-8")
            self.assertIn("Exhaustive Fixed-Effort Atlas", text)
            self.assertIn("Table Column Guide", text)
            self.assertIn("Hottest Takeaways", text)
            self.assertIn("fixed-slice slope table", text)
            self.assertIn("shaded ribbon", text)


if __name__ == "__main__":
    unittest.main()
