import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_effort_slice_audit_report import (
    effort_level_definitions,
    proposed_fixed_slices,
    run_effort_slice_audit,
)
from src.build_m1_m2_utterance_information_deep_dive import clean_modeling_rows
from src.fit_m1_m6_fixed_effort_slice_models import (
    build_fixed_effort_report_from_outputs,
    fit_and_plot_fixed_effort_slices,
    selected_fixed_values,
)
from tests.test_build_m1_m2_utterance_information_deep_dive import toy_route1_rows


class EffortSliceAuditAndFixedModelTests(unittest.TestCase):
    def test_effort_level_definitions_document_tertile_rules(self):
        frame = clean_modeling_rows(toy_route1_rows().iloc[:18])

        levels = effort_level_definitions(frame)

        self.assertEqual(set(levels["effort_level"]), {"low effort", "mid effort", "high effort"})
        self.assertTrue(levels["rule"].str.contains("p33|p66|fallback", regex=True).all())
        self.assertIn("Words", set(levels["effort_label"]))

    def test_proposed_fixed_slices_keeps_words_and_morphemes_one_to_twelve(self):
        frame = clean_modeling_rows(toy_route1_rows().iloc[:18])
        distribution = pd.DataFrame(
            [
                {
                    "effort_col": "nb_words",
                    "effort_label": "Words",
                    "effort_value": value,
                    "rows": 10,
                    "pct_rows": 0.1,
                    "n_children": 3,
                    "n_age_bins": 2,
                    "age_min": 18,
                    "age_max": 48,
                }
                for value in range(1, 13)
            ]
            + [
                {
                    "effort_col": "nb_morphemes",
                    "effort_label": "Morphemes",
                    "effort_value": value,
                    "rows": 10,
                    "pct_rows": 0.1,
                    "n_children": 3,
                    "n_age_bins": 2,
                    "age_min": 18,
                    "age_max": 48,
                }
                for value in range(1, 13)
            ]
        )

        proposals = proposed_fixed_slices(
            frame,
            distribution,
            min_rows=1,
            min_age_bins=1,
            min_children=1,
        )

        requested = proposals[proposals["proposal_set"].eq("requested_dense_1_12")]
        self.assertEqual(
            set(requested[requested["effort_col"].eq("nb_words")]["fixed_effort_value"]),
            set(range(1, 13)),
        )
        self.assertEqual(
            set(requested[requested["effort_col"].eq("nb_morphemes")]["fixed_effort_value"]),
            set(range(1, 13)),
        )

    def test_effort_slice_audit_writes_csv_and_report_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = clean_modeling_rows(toy_route1_rows().iloc[:18])

            outputs = run_effort_slice_audit(
                frame=frame,
                output_dir=root / "results",
                fig_dir=root / "figs",
                md_path=root / "audit.md",
                html_path=root / "audit.html",
                min_rows=1,
                min_age_bins=1,
                min_children=1,
            )

            self.assertTrue(outputs["proposals"].exists())
            self.assertTrue(outputs["html"].exists())
            text = outputs["md"].read_text(encoding="utf-8")
            self.assertIn("Effort Slice Audit", text)
            self.assertIn("word and morpheme slices", text.lower())

    def test_fixed_effort_model_stage_writes_selected_values_predictions_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "route1.csv"
            toy_route1_rows().to_csv(input_csv, index=False)
            proposal_csv = root / "proposals.csv"
            pd.DataFrame(
                [
                    {
                        "effort_col": "nb_words",
                        "effort_label": "Words",
                        "proposal_set": "requested_dense_1_12",
                        "fixed_effort_value": value,
                        "reason": "test",
                        "rows": 3,
                        "pct_rows": 0.1,
                        "n_children": 3,
                        "n_age_bins": 2,
                        "age_min": 18,
                        "age_max": 48,
                        "meets_support_rule": True,
                    }
                    for value in [1, 2, 3]
                ]
                + [
                    {
                        "effort_col": "nb_phonemes",
                        "effort_label": "Phonemes",
                        "proposal_set": "wide_low_median_high_p10_p50_p90",
                        "fixed_effort_value": value,
                        "reason": "test",
                        "rows": 3,
                        "pct_rows": 0.1,
                        "n_children": 3,
                        "n_age_bins": 2,
                        "age_min": 18,
                        "age_max": 48,
                        "meets_support_rule": True,
                    }
                    for value in [4, 8, 12]
                ]
            ).to_csv(proposal_csv, index=False)

            outputs = fit_and_plot_fixed_effort_slices(
                input_csv=input_csv,
                proposal_csv=proposal_csv,
                output_dir=root / "results",
                fig_dir=root / "figs",
                md_path=root / "fixed.md",
                html_path=root / "fixed.html",
                context_k="k3",
                chunksize=5,
                n_points=4,
                marginal_sample_size=12,
            )

            self.assertTrue(outputs["selected_values"].exists())
            self.assertTrue(outputs["marginal_predictions"].exists())
            self.assertTrue(outputs["predictions"].exists())
            self.assertTrue(outputs["html"].exists())
            marginal = pd.read_csv(outputs["marginal_predictions"])
            self.assertIn("standardization", marginal.columns)
            self.assertGreater(len(marginal), 0)
            predictions = pd.read_csv(outputs["predictions"])
            self.assertIn("fixed_effort_value", predictions.columns)
            self.assertIn("granular_primary", set(predictions["plot_group"]))
            self.assertIn("wide_anchors_p10_p50_p90", set(predictions["plot_group"]))

            report_only = build_fixed_effort_report_from_outputs(
                output_dir=root / "results",
                fig_dir=root / "figs",
                md_path=root / "fixed_report_only.md",
                html_path=root / "fixed_report_only.html",
            )
            self.assertTrue(report_only["html"].exists())


if __name__ == "__main__":
    unittest.main()
