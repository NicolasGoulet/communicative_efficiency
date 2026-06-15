import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_m1_m6_results_interpretation_report import (
    build_results_interpretation_report,
    coefficient_direction_summary,
    format_p,
)
from src.fit_m1_m6_dual_effort_quick_models import DUAL_MODEL_SPECS


def write_toy_m1_m6_summary(root: Path) -> Path:
    """Write a tiny but schema-complete M1-M6 model summary fixture."""

    output_dir = root / "results"
    output_dir.mkdir()
    rows = []
    for spec in DUAL_MODEL_SPECS:
        for strategy in ["continuous", "effort_level"]:
            for effort_label, age_coef in [("Words", -0.12), ("Phonemes", -0.06)]:
                has_entropy = spec.model_id in {"M4", "M5", "M6"}
                has_age_effort = spec.model_id in {"M3", "M6"} and strategy == "continuous"
                has_age_entropy = spec.model_id in {"M5", "M6"}
                rows.append(
                    {
                        "model_id": spec.model_id,
                        "model_title": spec.model_title,
                        "question": spec.question,
                        "effort_strategy": strategy,
                        "effort_label": effort_label,
                        "formula": "sum_bits ~ age_c + effort_c",
                        "readable_formula": "sum_bits ~ age + effort",
                        "status": "fit",
                        "r2_observed_fitted": 0.62,
                        "age_coef": age_coef if strategy == "continuous" else 0.08,
                        "age_p": 0.001 if strategy == "continuous" else 0.02,
                        "effort_coef": 6.0,
                        "effort_p": 0.001,
                        "entropy_coef": -0.5 if has_entropy else "",
                        "entropy_p": 0.001 if has_entropy else "",
                        "age_effort_coef": 0.01 if has_age_effort else "",
                        "age_effort_p": 0.04 if has_age_effort else "",
                        "age_entropy_coef": 0.004 if has_age_entropy else "",
                        "age_entropy_p": 0.6 if has_age_entropy else "",
                    }
                )
    pd.DataFrame(rows).to_csv(output_dir / "dual_model_summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "rows": 100,
                "children": 4,
                "context_k": "k3",
                "fitted_model_rows": len(rows),
                "prediction_rows": 240,
            }
        ]
    ).to_csv(output_dir / "dual_model_audit.csv", index=False)
    return output_dir


class M1M6ResultsInterpretationReportTests(unittest.TestCase):
    def test_format_p_uses_compact_report_style(self):
        self.assertEqual(format_p(0.0002), "<.001")
        self.assertEqual(format_p(0.0421), "0.042")
        self.assertEqual(format_p("not-a-number"), "")

    def test_coefficient_direction_summary_counts_signs_and_significance(self):
        summary = pd.DataFrame(
            [
                {"model_id": "M2", "effort_strategy": "continuous", "age_coef": -0.1, "age_p": 0.01},
                {"model_id": "M2", "effort_strategy": "continuous", "age_coef": -0.2, "age_p": 0.2},
                {"model_id": "M2", "effort_strategy": "effort_level", "age_coef": 0.1, "age_p": 0.03},
            ]
        )

        out = coefficient_direction_summary(summary, coefficient="age_coef", p_col="age_p")

        continuous = out[out["effort_strategy"].eq("continuous")].iloc[0]
        grouped = out[out["effort_strategy"].eq("effort_level")].iloc[0]
        self.assertEqual(int(continuous["negative"]), 2)
        self.assertEqual(int(continuous["positive"]), 0)
        self.assertEqual(int(continuous["p<.05"]), 1)
        self.assertEqual(int(grouped["positive"]), 1)

    def test_build_results_interpretation_report_uses_existing_model_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = write_toy_m1_m6_summary(root)
            md_path = root / "interpretation.md"
            html_path = root / "interpretation.html"

            outputs = build_results_interpretation_report(
                output_dir=output_dir,
                md_path=md_path,
                html_path=html_path,
            )

            self.assertTrue(outputs["md"].exists())
            self.assertTrue(outputs["html"].exists())
            text = md_path.read_text(encoding="utf-8")
            self.assertIn("Interpretation Notes", text)
            self.assertIn("Main Takeaways", text)
            self.assertIn("Child identity is essential", text)
            self.assertIn("M2: age plus effort plus child identity", text)
            self.assertIn("M4: adding context entropy", text)
            self.assertIn("response-level context entropy", text)
            self.assertIn("Tal, Smith, Arnon, and Culbertson", text)
            self.assertIn("https://doi.org/10.1111/cogs.70202", text)


if __name__ == "__main__":
    unittest.main()
