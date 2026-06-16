import tempfile
import unittest
from pathlib import Path

import pandas as pd

import src.build_m1_m6_interpreted_atlas_report as builder


class M1M6InterpretedAtlasReportTests(unittest.TestCase):
    def test_build_interpreted_outputs_include_email_context_and_companion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            deep = root / "deep"
            dual = root / "dual"
            fixed_atlas = root / "fixed_atlas"
            context = root / "context"
            context_fixed = root / "context_fixed"
            robust = root / "robust"
            for path in [deep, dual, fixed_atlas, context, context_fixed, robust]:
                path.mkdir()

            figs_m2 = root / "figs_m2"
            figs_context = root / "figs_context"
            figs_adjunct = root / "figs_adjunct"
            for path in [figs_m2, figs_context, figs_adjunct]:
                path.mkdir()
            (figs_m2 / "m2_words_fixed_effort_and_global_trend.png").write_bytes(b"fake")
            (figs_context / "k3_m4e_nb_words_fixed_effort_atlas.png").write_bytes(b"fake")
            (figs_adjunct / "k2_cf1_nb_words_fixed_effort_atlas.png").write_bytes(b"fake")

            pd.DataFrame(
                [
                    {
                        "approach_id": "M2",
                        "model_family_label": "OLS + child FE",
                        "fit_type": "ols_cluster",
                        "effect_scale": "additive bits",
                        "effort_label": "Words",
                        "readable_formula": "sum_bits ~ age + effort + child identity",
                        "status": "fit",
                        "n_obs": 20,
                        "n_children": 3,
                        "r2_observed_fitted": 0.55,
                        "age_coef": -0.1,
                        "age_p": 0.01,
                        "effort_coef": 4.0,
                        "effort_p": 0.001,
                    }
                ]
            ).to_csv(deep / "expanded_model_family_summary.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "model_id": model_id,
                        "effort_strategy": "continuous",
                        "effort_label": "Words",
                        "readable_formula": "sum_bits ~ age + effort",
                        "status": "fit",
                        "n_obs": 20,
                        "n_children": 3,
                        "r2_observed_fitted": 0.6,
                        "age_coef": -0.2,
                        "age_p": 0.02,
                        "effort_coef": 4.0,
                        "effort_p": 0.001,
                    }
                    for model_id in builder.atlas.MODEL_ORDER
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
            ).to_csv(fixed_atlas / "atlas_fixed_slice_slopes.csv", index=False)
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

            email_text = (
                "Hi Nicolas, Eva,\n\n"
                "Communicative efficiency is present in young children and becomes more adult-like with age.\n\n"
                "2) Given context, do children optimize utterance length (or production effort) in their speech?"
            )
            email_path = root / "project_email.md"
            email_path.write_text(
                "# Project Motivation / Recent Email Context\n\n```text\n" + email_text + "\n```\n",
                encoding="utf-8",
            )

            old_email = builder.PROJECT_EMAIL_CONTEXT
            old_values = {
                "DEEP_DIVE_DIR": builder.atlas.DEEP_DIVE_DIR,
                "DUAL_DIR": builder.atlas.DUAL_DIR,
                "FIXED_ATLAS_DIR": builder.atlas.FIXED_ATLAS_DIR,
                "CONTEXT_M1_M6_DIR": builder.atlas.CONTEXT_M1_M6_DIR,
                "CONTEXT_FIXED_DIR": builder.atlas.CONTEXT_FIXED_DIR,
                "ROBUSTNESS_DIR": builder.atlas.ROBUSTNESS_DIR,
                "FIGURE_SOURCES": builder.atlas.FIGURE_SOURCES,
                "ARTIFACTS": builder.atlas.ARTIFACTS,
            }
            try:
                builder.PROJECT_EMAIL_CONTEXT = email_path
                builder.atlas.DEEP_DIVE_DIR = deep
                builder.atlas.DUAL_DIR = dual
                builder.atlas.FIXED_ATLAS_DIR = fixed_atlas
                builder.atlas.CONTEXT_M1_M6_DIR = context
                builder.atlas.CONTEXT_FIXED_DIR = context_fixed
                builder.atlas.ROBUSTNESS_DIR = robust
                builder.atlas.FIGURE_SOURCES = [
                    ("fixed_atlas", "Fixed atlas", figs_m2),
                    ("context_m1_m6", "Context M1-M6", figs_context),
                    ("context_adjunct", "Context adjunct", figs_adjunct),
                ]
                builder.atlas.ARTIFACTS = [
                    ("expanded", "Expanded", deep / "expanded_model_family_summary.csv"),
                    ("dual", "Dual", dual / "dual_model_summary.csv"),
                    ("context", "Context", context / "context_m1_m6_model_summary.csv"),
                    ("robustness", "Robustness", robust / "age_scrambling_robustness_summary.csv"),
                ]

                outputs = builder.build_interpreted_outputs(
                    output_dir=root / "out",
                    interpreted_md=root / "docs" / "interpreted.md",
                    interpreted_html=root / "docs" / "interpreted.html",
                    companion_md=root / "docs" / "companion.md",
                    companion_html=root / "docs" / "companion.html",
                )
            finally:
                builder.PROJECT_EMAIL_CONTEXT = old_email
                for name, value in old_values.items():
                    setattr(builder.atlas, name, value)

            self.assertTrue(outputs["interpreted_html"].exists())
            self.assertTrue(outputs["companion_html"].exists())
            interpreted = outputs["interpreted_md"].read_text(encoding="utf-8")
            companion = outputs["companion_md"].read_text(encoding="utf-8")
            audit = pd.read_csv(outputs["image_audit"])

            self.assertIn("Project Motivation / Recent Email Context", interpreted)
            self.assertIn(email_text, interpreted)
            self.assertIn("Route 1 evidence", interpreted)
            self.assertIn("Route 2 question", interpreted)
            self.assertIn("Is Child Identity Control Too Strong?", interpreted)
            self.assertIn("statsmodels.formula.api.ols", companion)
            self.assertIn("production_effort ~ age + response_entropy", companion)
            self.assertGreaterEqual(len(audit), 3)
            self.assertTrue(audit["exists"].all())
            self.assertNotIn("PASTE THE WHOLE EMAIL", interpreted)


if __name__ == "__main__":
    unittest.main()
