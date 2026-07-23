import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_direct_surprisal_modular_analysis import (
    run_dataset_stage,
    run_model_stage,
    run_plot_stage,
    run_report_stage,
)
from tests.test_build_direct_surprisal_model_suite import toy_wide_rows


class DirectSurprisalModularAnalysisTests(unittest.TestCase):
    def test_stages_are_independent_and_write_visual_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_wide = root / "toy.csv.gz"
            prepared = root / "prepared"
            models = root / "models"
            figures = root / "figures"
            report_md = root / "visual.md"
            report_html = root / "visual.html"
            gallery_md = root / "gallery.md"
            gallery_html = root / "gallery.html"
            toy_wide_rows().to_csv(input_wide, index=False)

            dataset_manifest = run_dataset_stage(
                input_wide=input_wide,
                caretaker_wide=None,
                prepared_dir=prepared,
                scorer_label="Toy scorer",
            )

            self.assertEqual(dataset_manifest["status"], "COMPLETE")
            self.assertTrue((prepared / "design_cell_manifest.csv").exists())
            self.assertFalse(models.exists())

            model_manifest = run_model_stage(
                prepared_dir=prepared,
                model_dir=models,
                bootstrap_reps=2,
                permutation_reps=2,
                seed=77,
                include_mixed=False,
            )

            self.assertEqual(model_manifest["failed"], 0)
            self.assertFalse(figures.exists())
            summaries = pd.read_csv(models / "model_summaries.csv")
            self.assertTrue(summaries["model_id"].str.contains("linear_word_effort").any())
            bootstrap = pd.read_csv(models / "child_bootstrap_summary.csv")
            self.assertTrue(bootstrap["model_id"].str.startswith("B1_").any())

            plot_manifest = run_plot_stage(
                prepared_dir=prepared,
                model_dir=models,
                fig_dir=figures,
            )
            self.assertEqual(plot_manifest["missing"], 0)
            self.assertTrue((figures / "headline_primary_age_slopes.png").exists())
            self.assertTrue((models / "model_coverage.csv").exists())

            report_manifest = run_report_stage(
                prepared_dir=prepared,
                model_dir=models,
                fig_dir=figures,
                report_md=report_md,
                report_html=report_html,
                gallery_md=gallery_md,
                gallery_html=gallery_html,
                scorer_label="Toy scorer",
            )
            self.assertEqual(report_manifest["status"], "COMPLETE")
            self.assertTrue(report_html.exists())
            self.assertTrue(gallery_html.exists())
            table_separator_lines = [
                line for line in report_md.read_text().splitlines() if line.startswith("| ---")
            ]
            self.assertEqual(len(table_separator_lines), 1)


if __name__ == "__main__":
    unittest.main()
