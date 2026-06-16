import tempfile
import unittest
from pathlib import Path

import pandas as pd

import src.build_m1_m6_super_atlas_report as builder


class M1M6SuperAtlasReportTests(unittest.TestCase):
    def test_infer_model_ids_handles_context_variants_and_joint_figures(self):
        self.assertEqual(builder.infer_model_ids("k3_m6es_nb_words_fixed_effort_atlas.png"), ["M6"])
        self.assertEqual(builder.infer_model_ids("m5_m6_saturated_selected_coefficients.png"), ["M5", "M6"])
        self.assertEqual(builder.infer_model_ids("m1_m2_age_coefficients_by_effort.png"), ["M1", "M2"])
        self.assertEqual(builder.infer_model_ids("k1_cf3_nb_words_fixed_effort_atlas.png"), [])

    def test_collect_figure_inventory_records_source_model_context_and_effort(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            figs = root / "figs"
            figs.mkdir()
            (figs / "k3_m4e_nb_words_fixed_effort_atlas.png").write_bytes(b"fake")
            (figs / "notes.txt").write_text("skip", encoding="utf-8")

            inventory = builder.collect_figure_inventory(
                [("context", "Context figures", figs)]
            )

            self.assertEqual(len(inventory), 1)
            row = inventory.iloc[0]
            self.assertEqual(row["models"], "M4")
            self.assertEqual(row["context_k"], "k3")
            self.assertEqual(row["effort_label"], "Words")

    def test_build_super_atlas_report_writes_interpretive_scaffold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            deep = root / "deep"
            dual = root / "dual"
            fixed = root / "fixed"
            atlas = root / "atlas"
            context = root / "context"
            context_fixed = root / "context_fixed"
            robust = root / "robust"
            for path in [deep, dual, fixed, atlas, context, context_fixed, robust]:
                path.mkdir()

            figs_deep = root / "figs_deep"
            figs_context = root / "figs_context"
            figs_adjunct = root / "figs_adjunct"
            for path in [figs_deep, figs_context, figs_adjunct]:
                path.mkdir()
            (figs_deep / "m1_ols_adjusted_age_lines.png").write_bytes(b"fake")
            (figs_context / "k3_m4e_nb_words_fixed_effort_atlas.png").write_bytes(b"fake")
            (figs_adjunct / "k2_cf1_nb_words_fixed_effort_atlas.png").write_bytes(b"fake")

            pd.DataFrame(
                [
                    {
                        "approach_id": "M1",
                        "model_family_label": "OLS",
                        "fit_type": "ols",
                        "effect_scale": "additive bits",
                        "effort_label": "Words",
                        "readable_formula": "sum_bits ~ age + effort",
                        "status": "fit",
                        "n_obs": 20,
                        "n_children": 3,
                        "r2_observed_fitted": 0.5,
                        "age_coef": -0.1,
                        "age_p": 0.01,
                        "effort_coef": 5.0,
                        "effort_p": 0.001,
                        "age_effort_coef": "",
                        "age_effort_p": "",
                    }
                ]
            ).to_csv(deep / "expanded_model_family_summary.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "model_id": "M2",
                        "effort_strategy": "continuous",
                        "effort_label": "Words",
                        "readable_formula": "sum_bits ~ age + effort + child identity",
                        "status": "fit",
                        "n_obs": 20,
                        "n_children": 3,
                        "r2_observed_fitted": 0.6,
                        "age_coef": -0.2,
                        "age_p": 0.02,
                        "effort_coef": 4.0,
                        "effort_p": 0.001,
                        "entropy_coef": "",
                        "entropy_p": "",
                        "age_effort_coef": "",
                        "age_effort_p": "",
                        "age_entropy_coef": "",
                        "age_entropy_p": "",
                    }
                ]
            ).to_csv(dual / "dual_model_summary.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "model_id": "M2",
                        "effort_label": "Words",
                        "slope_bits_per_month": -0.2,
                    }
                ]
            ).to_csv(atlas / "atlas_fixed_slice_slopes.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "context_k": "k3",
                        "model_id": "M4E",
                        "model_family": "M4",
                        "context_variant": "entropy",
                        "effort_label": "Words",
                        "estimator": "linear OLS",
                        "library": "statsmodels.formula.api.ols",
                        "covariance": "child-cluster robust SE via cov_type='cluster'",
                        "n_obs": 20,
                        "n_children": 3,
                        "r2_observed_fitted": 0.7,
                        "age_coef": -0.3,
                        "age_p": 0.03,
                        "target_effort_coef": 4.0,
                        "target_effort_p": 0.001,
                        "context_entropy_coef": -0.4,
                        "context_entropy_p": 0.04,
                    }
                ]
            ).to_csv(context / "context_m1_m6_model_summary.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "context_k": "k3",
                        "model_id": "M4E",
                        "model_family": "M4",
                        "effort_label": "Words",
                        "slope_bits_per_month": -0.3,
                    }
                ]
            ).to_csv(context / "context_m1_m6_slice_slopes.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "model_id": "M2",
                        "context_k": "k3",
                        "robustness_method": "balanced_bootstrap",
                        "observed_age_coef": -0.2,
                        "observed_outside_null_95": True,
                        "same_sign_share": 0.9,
                        "two_sided_permutation_p": 0.02,
                    }
                ]
            ).to_csv(robust / "age_scrambling_robustness_summary.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "context_k": "k2",
                        "model_id": "CF1",
                        "model_label": "Entropy only",
                        "effort_label": "Words",
                        "formula": "sum_bits ~ age + effort + context_entropy",
                        "n_obs": 20,
                        "n_children": 3,
                        "r2_observed_fitted": 0.65,
                        "age_coef": -0.25,
                        "age_p": 0.03,
                        "context_entropy_coef": -0.4,
                        "context_entropy_p": 0.04,
                        "status": "fit",
                    }
                ]
            ).to_csv(context_fixed / "context_fixed_effort_model_summary.csv", index=False)

            old_values = {
                "DEEP_DIVE_DIR": builder.DEEP_DIVE_DIR,
                "DUAL_DIR": builder.DUAL_DIR,
                "FIXED_SLICE_DIR": builder.FIXED_SLICE_DIR,
                "FIXED_ATLAS_DIR": builder.FIXED_ATLAS_DIR,
                "CONTEXT_M1_M6_DIR": builder.CONTEXT_M1_M6_DIR,
                "CONTEXT_FIXED_DIR": builder.CONTEXT_FIXED_DIR,
                "ROBUSTNESS_DIR": builder.ROBUSTNESS_DIR,
                "FIGURE_SOURCES": builder.FIGURE_SOURCES,
                "ARTIFACTS": builder.ARTIFACTS,
            }
            try:
                builder.DEEP_DIVE_DIR = deep
                builder.DUAL_DIR = dual
                builder.FIXED_SLICE_DIR = fixed
                builder.FIXED_ATLAS_DIR = atlas
                builder.CONTEXT_M1_M6_DIR = context
                builder.CONTEXT_FIXED_DIR = context_fixed
                builder.ROBUSTNESS_DIR = robust
                builder.FIGURE_SOURCES = [
                    ("deep_dive", "Deep figures", figs_deep),
                    ("context_m1_m6", "Context figures", figs_context),
                    ("context_adjunct", "Context adjunct", figs_adjunct),
                ]
                builder.ARTIFACTS = [
                    ("expanded", "Expanded", deep / "expanded_model_family_summary.csv"),
                    ("dual", "Dual", dual / "dual_model_summary.csv"),
                    ("context", "Context", context / "context_m1_m6_model_summary.csv"),
                ]

                outputs = builder.build_super_atlas_report(
                    output_dir=root / "out",
                    fig_dir=root / "overview_figs",
                    md_path=root / "docs" / "super.md",
                    html_path=root / "docs" / "super.html",
                )
            finally:
                for name, value in old_values.items():
                    setattr(builder, name, value)

            self.assertTrue(outputs["html"].exists())
            text = outputs["md"].read_text(encoding="utf-8")
            self.assertIn("Estimator And Library Guide", text)
            self.assertIn("MixedLM random child intercept/slope", text)
            self.assertIn("statsmodels.formula.api.ols", text)
            self.assertIn("Scientific meaning", text)
            self.assertIn("All Plots For M1", text)
            self.assertNotIn("TODO", text)


if __name__ == "__main__":
    unittest.main()
