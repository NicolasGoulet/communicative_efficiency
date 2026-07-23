import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_paired_direct_surprisal_comparison import build_pair
from src.build_paired_direct_surprisal_visual_analysis import (
    run_models,
    run_plots,
    run_report,
)
from tests.test_build_paired_direct_surprisal_comparison import paired_fixture


class PairedDirectSurprisalVisualAnalysisTests(unittest.TestCase):
    def test_stages_write_expanded_models_plots_and_short_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tiny_path = root / "tiny.csv.gz"
            mistral_path = root / "mistral.csv.gz"
            paired_path = root / "paired.csv.gz"
            output_dir = root / "models"
            fig_dir = root / "figures"
            report_md = root / "paired_visual.md"
            report_html = root / "paired_visual.html"
            paired_fixture("tiny", 0.5).to_csv(tiny_path, index=False)
            paired_fixture("mistral", 1.0).to_csv(mistral_path, index=False)
            paired, mismatches, _, _ = build_pair(
                tiny_path,
                mistral_path,
                left_suffix="tiny",
                right_suffix="mistral",
            )
            self.assertTrue(mismatches.empty)
            paired.to_csv(paired_path, index=False, compression="gzip")

            model_manifest = run_models(
                paired_wide=paired_path,
                output_dir=output_dir,
                left_suffix="tiny",
                right_suffix="mistral",
                reps=2,
                seed=17,
            )
            plot_manifest = run_plots(output_dir=output_dir, fig_dir=fig_dir)
            report_manifest = run_report(
                output_dir=output_dir,
                fig_dir=fig_dir,
                report_md=report_md,
                report_html=report_html,
            )

            self.assertEqual(model_manifest["outcomes"], 11)
            slopes = pd.read_csv(output_dir / "paired_all_outcome_slopes.csv")
            self.assertEqual(len(slopes), 11)
            quadratic = pd.read_csv(output_dir / "paired_quadratic_age_comparison.csv")
            self.assertEqual(len(quadratic), 3)
            rankings = pd.read_csv(output_dir / "paired_candidate_rankings.csv")
            self.assertEqual(set(rankings["candidate"]), {"random", "unigram", "bigram", "trigram"})
            self.assertEqual(plot_manifest["plots"], 7)
            self.assertEqual(plot_manifest["missing"], 0)
            self.assertEqual(report_manifest["status"], "COMPLETE")
            self.assertTrue(report_md.exists())
            self.assertTrue(report_html.exists())
            self.assertIn("Visual Comparison", report_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
