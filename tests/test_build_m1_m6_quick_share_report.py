import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_m1_m6_quick_share_report import build_quick_share_report
from src.fit_m1_m6_dual_effort_quick_models import (
    DUAL_MODEL_SPECS,
    fit_and_plot_dual_effort_models,
)
from tests.test_build_m1_m2_utterance_information_deep_dive import toy_route1_rows


def write_toy_outputs(root: Path) -> tuple[Path, Path]:
    output_dir = root / "results"
    fig_dir = root / "figs"
    output_dir.mkdir()
    fig_dir.mkdir()
    rows = []
    for spec in DUAL_MODEL_SPECS:
        for strategy in ["continuous", "effort_level"]:
            for effort, age_coef in [
                ("Words", -1.0),
                ("Morphemes", -0.8),
                ("Syllables: CMU/pkg", -0.6),
                ("Syllables: pkg", -0.7),
                ("Phonemes", -0.5),
            ]:
                rows.append(
                    {
                        "model_id": spec.model_id,
                        "model_title": spec.model_title,
                        "question": spec.question,
                        "effort_strategy": strategy,
                        "effort_label": effort,
                        "formula": "sum_bits ~ age_c + effort_c",
                        "readable_formula": "sum_bits ~ age + effort"
                        if strategy == "continuous"
                        else "sum_bits ~ age + effort_level",
                        "status": "fit",
                        "r2_observed_fitted": 0.5,
                        "age_coef": age_coef,
                        "age_p": 0.01,
                        "effort_coef": 7.0 if strategy == "continuous" else "",
                        "effort_p": 0.001 if strategy == "continuous" else "",
                        "entropy_coef": 0.2 if spec.model_id in {"M4", "M5", "M6"} else "",
                        "entropy_p": 0.02 if spec.model_id in {"M4", "M5", "M6"} else "",
                        "age_effort_coef": -0.1 if spec.model_id in {"M3", "M6"} else "",
                        "age_effort_p": 0.04 if spec.model_id in {"M3", "M6"} else "",
                        "age_entropy_coef": -0.05 if spec.model_id in {"M5", "M6"} else "",
                        "age_entropy_p": 0.05 if spec.model_id in {"M5", "M6"} else "",
                    }
                )
    pd.DataFrame(rows).to_csv(output_dir / "dual_model_summary.csv", index=False)
    pd.DataFrame(
        [{"rows": 18, "children": 3, "fitted_model_rows": len(rows), "prediction_rows": 1200}]
    ).to_csv(output_dir / "dual_model_audit.csv", index=False)
    for name in [f"{spec.model_id.lower()}_dual_effort_predictions.png" for spec in DUAL_MODEL_SPECS]:
        (fig_dir / name).write_bytes(b"fake image")
    return output_dir, fig_dir


class M1M6QuickShareReportTests(unittest.TestCase):
    def test_dual_effort_analysis_writes_expected_model_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "route1.csv"
            output_dir = root / "results"
            fig_dir = root / "figs"
            toy_route1_rows().to_csv(input_csv, index=False)

            outputs = fit_and_plot_dual_effort_models(
                input_csv=input_csv,
                output_dir=output_dir,
                fig_dir=fig_dir,
                context_k="k3",
                chunksize=4,
            )

            self.assertTrue(outputs["summary"].exists())
            summary = pd.read_csv(outputs["summary"])
            self.assertEqual(set(summary["model_id"]), {spec.model_id for spec in DUAL_MODEL_SPECS})
            self.assertEqual(set(summary["effort_strategy"]), {"continuous", "effort_level"})
            self.assertEqual(len(summary), 6 * 5 * 2)
            self.assertTrue(summary["readable_formula"].str.contains("effort_level").any())
            self.assertTrue(summary["readable_formula"].str.contains("effort").any())
            self.assertTrue(outputs["predictions"].exists())
            self.assertTrue((fig_dir / "m1_dual_effort_predictions.png").exists())
            self.assertTrue((fig_dir / "m6_dual_effort_predictions.png").exists())

    def test_build_quick_share_report_uses_existing_outputs_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir, fig_dir = write_toy_outputs(root)
            md_path = root / "quick.md"
            html_path = root / "quick.html"

            outputs = build_quick_share_report(
                output_dir=output_dir,
                fig_dir=fig_dir,
                md_path=md_path,
                html_path=html_path,
            )

            self.assertTrue(outputs["md"].exists())
            self.assertTrue(outputs["html"].exists())
            text = md_path.read_text(encoding="utf-8")
            self.assertIn("Quick Share", text)
            self.assertIn("What Changed In This Version", text)
            self.assertIn("M1: Pooled age and effort", text)
            self.assertIn("M2: Age and effort with child identity", text)
            self.assertIn("M3: Age by effort", text)
            self.assertIn("M4: Context entropy added", text)
            self.assertIn("M5: Age by context entropy", text)
            self.assertIn("M6: Interaction-rich exploratory model", text)
            self.assertIn("How to read the plot", text)
            self.assertIn("continuous", text)
            self.assertIn("effort_level", text)
            self.assertIn("m1_dual_effort_predictions.png", text)
            self.assertIn("m6_dual_effort_predictions.png", text)


if __name__ == "__main__":
    unittest.main()
