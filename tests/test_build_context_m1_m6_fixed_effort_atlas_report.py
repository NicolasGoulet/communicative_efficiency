import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_context_m1_m6_fixed_effort_atlas_report import (
    MODEL_SPECS,
    model_formula_table,
    run_analysis,
    run_report,
)
from tests.test_build_context_fixed_effort_atlas_report import toy_context_frame


class ContextM1M6FixedEffortAtlasTests(unittest.TestCase):
    def test_model_specs_cover_m1_to_m6_context_variants_and_formulas(self):
        table = model_formula_table()

        self.assertTrue({"M1", "M2", "M3", "M4", "M5", "M6"}.issubset(set(table["model_family"])))
        self.assertIn("M4ES", set(table["model_id"]))
        self.assertIn("M6ES", set(table["model_id"]))
        self.assertTrue(any("context_entropy_c" in formula for formula in table["formula"]))
        self.assertTrue(any("context_size_c" in formula for formula in table["formula"]))
        self.assertTrue(all(spec.formula for spec in MODEL_SPECS))

    def test_context_m1_m6_analysis_and_report_write_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context_out = root / "context"
            out = root / "results"
            figs = root / "figs"
            docs = root / "docs"
            context_out.mkdir()
            toy_context_frame("k0").to_csv(context_out / "route1_real_child_context_measures_k0.csv.gz", index=False)
            toy_context_frame("k1").to_csv(context_out / "route1_real_child_context_measures_k1.csv.gz", index=False)

            outputs = run_analysis(
                context_output_dir=context_out,
                output_dir=out,
                fig_dir=figs,
                context_ks=("k0", "k1"),
                n_points=6,
            )
            report = run_report(
                output_dir=out,
                fig_dir=figs,
                md_path=docs / "m1_m6_context.md",
                html_path=docs / "m1_m6_context.html",
            )

            self.assertTrue(outputs["audit"].exists())
            self.assertTrue(outputs["predictions"].exists())
            self.assertTrue(report["html"].exists())
            summary = pd.read_csv(outputs["summary"])
            self.assertIn("M1", set(summary["model_id"]))
            self.assertIn("M6ES", set(summary["model_id"]))
            text = report["md"].read_text(encoding="utf-8")
            self.assertIn("M1-M6 Context Fixed-Effort Atlas", text)
            self.assertIn("Model Formulas", text)
            self.assertIn("1-4", text)
            self.assertIn("Formula:", text)


if __name__ == "__main__":
    unittest.main()
