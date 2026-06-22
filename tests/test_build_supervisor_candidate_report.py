import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_supervisor_candidate_report import figure_guide, write_report


class SupervisorCandidateReportTests(unittest.TestCase):
    def test_figure_guide_has_interpretive_parts(self):
        guide = "\n".join(
            figure_guide(
                shows="a fitted line",
                read="left means lower",
                means="the result is inspectable",
                caution="this is not causal",
            )
        )

        self.assertIn("What the figure shows", guide)
        self.assertIn("How to read it", guide)
        self.assertIn("What it means here", guide)
        self.assertIn("Do not overclaim", guide)

    def test_write_report_adds_guides_for_all_promoted_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc_path = root / "candidate.md"
            output_dir = root / "out"
            output_dir.mkdir()
            figures = {
                "route_map": root / "route_map.png",
                "source_slopes": root / "source_slopes.png",
                "r2_importance": root / "r2.png",
                "heldout_regression": root / "heldout_lines.png",
                "heldout_calibration": root / "calibration.png",
                "correlations": root / "corr.png",
            }
            for path in figures.values():
                path.write_text("placeholder", encoding="utf-8")

            write_report(
                doc_path=doc_path,
                figures=figures,
                model_cards_frame=pd.DataFrame(
                    [{"model": "M2", "question": "Does age remain?", "formula": "sum_bits ~ age + effort + C(child_id)", "plain-language role": "Primary controlled line."}]
                ),
                importance_table=pd.DataFrame(
                    [{"model": "M2", "what changed": "child identity", "R2": "0.62", "delta R2 vs M2": "0", "age effect": "-0.12", "effort effect": "6.37"}]
                ),
                effect_table=pd.DataFrame(
                    [{"arrow": "age down", "effect": "older children lower at fixed effort", "number": "-0.12"}]
                ),
                output_dir=output_dir,
            )

            report = doc_path.read_text(encoding="utf-8")

        self.assertGreaterEqual(report.count("**What the figure shows:**"), 6)
        self.assertIn("bars left of zero mean predicted `sum_bits` goes down", report)
        self.assertIn("black points are actual heldout child month-by-band means", report)
        self.assertIn("raw Pearson correlations", report)


if __name__ == "__main__":
    unittest.main()
