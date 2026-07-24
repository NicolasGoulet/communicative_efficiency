import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_direct_surprisal_results_explorer import build_explorer


class DirectSurprisalResultsExplorerTests(unittest.TestCase):
    def test_builds_filterable_model_and_child_explorer_from_saved_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            models = root / "models.csv"
            coefficients = root / "coefficients.csv"
            coverage = root / "coverage.csv"
            profiles = root / "profiles.csv"
            paired_slopes = root / "paired_slopes.csv"
            paired_quadratic = root / "paired_quadratic.csv"
            paired_rankings = root / "paired_rankings.csv"
            output = root / "docs" / "explorer.html"
            plot = root / "figures" / "child.png"
            plot.parent.mkdir(parents=True)
            plot.write_bytes(b"png fixture")

            pd.DataFrame(
                [
                    {
                        "scope": "pbm_discovery",
                        "model_id": "P1_k3_contextual",
                        "tier": "primary",
                        "outcome": "real_k3_sum_bits",
                        "estimator": "exact_cell_wls_child_cluster",
                        "formula": "outcome_mean ~ age_c + C(word_count_exact_top12) + C(child_key)",
                        "source_rows": 120,
                        "design_cells": 24,
                        "children": 2,
                        "corpora": 1,
                        "age_term": "age_c",
                        "age_estimate": -0.2,
                        "age_std_error": 0.05,
                        "age_ci_low": -0.3,
                        "age_ci_high": -0.1,
                        "age_p_value": 0.01,
                        "r_squared": 0.8,
                        "aic": 100,
                        "fit_status": "PASS",
                        "warnings": "",
                        "role": "child",
                        "trim_low": None,
                        "trim_high": None,
                        "weighting_note": None,
                        "protocol_result": "expected_direction_interval_excludes_zero",
                    }
                ]
            ).to_csv(models, index=False)
            pd.DataFrame(
                [
                    {
                        "scope": "pbm_discovery",
                        "model_id": "P1_k3_contextual",
                        "tier": "primary",
                        "outcome": "real_k3_sum_bits",
                        "estimator": "exact_cell_wls_child_cluster",
                        "formula": "outcome_mean ~ age_c + C(word_count_exact_top12) + C(child_key)",
                        "term": "age_c",
                        "estimate": -0.2,
                        "std_error": 0.05,
                        "ci_low": -0.3,
                        "ci_high": -0.1,
                        "p_value": 0.01,
                        "role": "child",
                    }
                ]
            ).to_csv(coefficients, index=False)
            pd.DataFrame(
                [{"model_family": "Primary models", "status": "complete", "reason": "fixture"}]
            ).to_csv(coverage, index=False)
            pd.DataFrame(
                [
                    {
                        "scope": "pbm_discovery",
                        "dataset": "Brown",
                        "child_id": "Adam",
                        "child_key": "Brown/Adam",
                        "plot": str(plot),
                        "trajectory_points": 4,
                        "utterances": 120,
                        "slope_supported": 1,
                    }
                ]
            ).to_csv(profiles, index=False)
            pd.DataFrame(
                [
                    {
                        "outcome": "real_k3_sum_bits",
                        "label": "Contextual target (k3)",
                        "paired_rows": 120,
                        "children": 2,
                        "slope_tiny": -0.2,
                        "slope_mistral": -0.1,
                        "slope_difference_left_minus_right": -0.1,
                        "difference_ci_low": -0.15,
                        "difference_ci_high": -0.05,
                        "bootstrap_reps": 2,
                    },
                    {
                        "outcome": "real_k0_sum_bits",
                        "label": "Unconditional target (k0)",
                        "paired_rows": 120,
                        "children": 2,
                        "slope_tiny": -0.25,
                        "slope_mistral": -0.15,
                        "slope_difference_left_minus_right": -0.1,
                        "difference_ci_low": -0.16,
                        "difference_ci_high": -0.04,
                        "bootstrap_reps": 2,
                    },
                    {
                        "outcome": "real_context_gain_k3",
                        "label": "Context support (k3)",
                        "paired_rows": 120,
                        "children": 2,
                        "slope_tiny": -0.05,
                        "slope_mistral": -0.05,
                        "slope_difference_left_minus_right": 0.0,
                        "difference_ci_low": -0.02,
                        "difference_ci_high": 0.02,
                        "bootstrap_reps": 2,
                    },
                ]
            ).to_csv(paired_slopes, index=False)
            pd.DataFrame(
                [{"outcome": "real_k3_sum_bits", "quadratic_tiny": 0.0, "quadratic_mistral": 0.0}]
            ).to_csv(paired_quadratic, index=False)
            ranking_rows = []
            for scorer in ["tiny", "mistral"]:
                for rank, candidate in enumerate(["trigram", "bigram", "unigram", "random"], 1):
                    ranking_rows.append(
                        {
                            "scorer": scorer,
                            "age_bin": "006-023",
                            "candidate": candidate,
                            "predictability_rank_within_scorer_age": rank,
                        }
                    )
            pd.DataFrame(ranking_rows).to_csv(paired_rankings, index=False)

            audit = build_explorer(
                tiny_models=models,
                tiny_coefficients=coefficients,
                tiny_coverage=coverage,
                tiny_profiles=profiles,
                mistral_models=models,
                mistral_coefficients=coefficients,
                mistral_coverage=coverage,
                mistral_profiles=profiles,
                paired_slopes=paired_slopes,
                paired_quadratic=paired_quadratic,
                paired_rankings=paired_rankings,
                output=output,
            )

            page = output.read_text(encoding="utf-8")
            self.assertEqual(audit["models"], 2)
            self.assertEqual(audit["profiles"], 2)
            self.assertIn("Model explorer", page)
            self.assertIn("See the actual model", page)
            self.assertIn("P1_k3_contextual", page)
            self.assertIn("Brown/Adam", page)
            self.assertIn("const APP_DATA=", page)
            self.assertNotIn("<table", page)


if __name__ == "__main__":
    unittest.main()
