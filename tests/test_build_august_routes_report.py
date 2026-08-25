import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_august_routes_report import (
    assert_protected_unchanged,
    fit_effort_only_diagnostic,
    protected_hashes,
    require_status,
    route1_ladder,
    route2_final_ladder,
    route2_model_implied_lines,
    word_effect_table,
    word_model_implied_lines,
    write_report,
    write_report_site,
)


class AugustRoutesReportTests(unittest.TestCase):
    def test_route1_ladder_keeps_adjusted_and_repeated_measure_models(self):
        summary = pd.DataFrame(
            [
                {
                    "scope": "pbm_discovery",
                    "model_id": model_id,
                    "estimator": estimator,
                    "age_term": age_term,
                    "age_estimate": estimate,
                    "age_ci_low": estimate - 0.1,
                    "age_ci_high": estimate + 0.1,
                    "age_p_value": 0.01,
                    "fit_status": "PASS",
                    "children": 21,
                    "source_rows": 100,
                }
                for model_id, estimator, age_term, estimate in [
                    ("P1_k3_contextual", "exact_cell_wls_child_cluster", "age_c", -0.20),
                    ("P1_k3_contextual_quadratic", "exact_cell_wls_child_cluster", "age_c", -0.24),
                    ("P1_k3_contextual_mundlak", "mundlak_wls_child_cluster", "age_within", -0.21),
                    ("P1_k3_contextual_gee", "exact_cell_gee_child_cluster", "age_c", -0.22),
                ]
            ]
        )

        ladder = route1_ladder(summary, scorer="Mistral", scope="pbm_discovery")

        self.assertEqual(
            ladder["model"].tolist(),
            ["Linear child-adjusted", "Nonlinear age", "Within/between child", "Repeated-measures GEE"],
        )
        self.assertIn("child fixed effects", ladder.iloc[0]["adjustment"])
        self.assertIn("within-child age", ladder.iloc[2]["adjustment"])
        self.assertIn("exchangeable", ladder.iloc[3]["adjustment"])

    def test_effort_only_diagnostic_produces_fitted_lines_and_intervals(self):
        rows = []
        for child in ["A", "B"]:
            for age in [18.0, 24.0, 30.0, 36.0]:
                for words in ["1", "2", "4"]:
                    rows.append(
                        {
                            "dataset": "PBM",
                            "child_key": child,
                            "age_months": age,
                            "age_c": age - 27.0,
                            "word_count_exact_top12": words,
                            "outcome_mean": 8.0 - 0.2 * age + 5.0 * int(words),
                            "row_count": 10,
                        }
                    )
        summary, grid = fit_effort_only_diagnostic(pd.DataFrame(rows))

        self.assertAlmostEqual(summary["age_estimate"], -0.2, places=8)
        self.assertEqual(set(grid["word_count_exact_top12"]), {"1", "2", "4"})
        self.assertTrue((grid["ci_low"] <= grid["predicted_mean"]).all())
        self.assertTrue((grid["predicted_mean"] <= grid["ci_high"]).all())

    def test_route2_model_implied_lines_include_gee_mundlak_and_mixed(self):
        terms = {
            "row_ols_child_fe_cluster": ("age_months_c", "age_months_c:response_entropy_bits_c"),
            "session_gee_exchangeable": ("age_months_c", "age_months_c:response_entropy_bits_c"),
            "session_mundlak_gee": (
                "age_within_child_c",
                "age_within_child_c:response_entropy_bits_c",
            ),
            "session_mixedlm_random_age": (
                "age_months_c",
                "age_months_c:response_entropy_bits_c",
            ),
        }
        rows = []
        for index, (estimator, (age_term, interaction_term)) in enumerate(terms.items()):
            rows.extend(
                [
                    {
                        "model_id": "percentile_in_gen_distribution_r2m5_age_by_entropy",
                        "estimator_id": estimator,
                        "term": age_term,
                        "estimate": 0.01 + index * 0.001,
                    },
                    {
                        "model_id": "percentile_in_gen_distribution_r2m5_age_by_entropy",
                        "estimator_id": estimator,
                        "term": interaction_term,
                        "estimate": -0.002,
                    },
                ]
            )
        reference_grid = pd.DataFrame(
            {
                "age_months": [20.0, 40.0, 20.0, 40.0],
                "age_months_c": [-10.0, 10.0, -10.0, 10.0],
                "response_entropy_level": [3.0, 3.0, 6.0, 6.0],
                "response_entropy_bits_c": [-1.0, -1.0, 2.0, 2.0],
            }
        )

        lines = route2_model_implied_lines(pd.DataFrame(rows), reference_grid, points=5)

        self.assertEqual(set(lines["estimator_id"]), set(terms))
        self.assertEqual(set(lines["response_entropy_level"]), {3.0, 6.0})
        self.assertTrue({"Session GEE", "Within/between-child GEE", "Mixed model"}.issubset(lines["model"]))

    def test_word_lines_keep_scorers_separate_and_use_bootstrap_bands(self):
        effects = pd.DataFrame(
            [
                {
                    "question_id": question,
                    "question": question,
                    "scorer": scorer,
                    "estimate": estimate,
                    "ci_low": estimate - 0.01,
                    "ci_high": estimate + 0.01,
                    "bootstrap_ci_low": estimate - 0.02,
                    "bootstrap_ci_high": estimate + 0.02,
                }
                for scorer, estimate in [
                    ("Mistral", -0.03),
                    ("Qwen3-14B", -0.02),
                    ("TinyDialogues", -0.04),
                ]
                for question in ["same_word_k0_age", "same_word_k3_age", "context_gain_age"]
            ]
        )

        lines = word_model_implied_lines(effects, reference_age=36.0, points=7)

        self.assertEqual(set(lines["scorer"]), {"Mistral", "Qwen3-14B", "TinyDialogues"})
        self.assertTrue(np.allclose(lines.loc[lines["age_months"].eq(36), "predicted_change"], 0.0))
        self.assertTrue((lines["ci_low"] <= lines["predicted_change"]).all())
        self.assertTrue((lines["predicted_change"] <= lines["ci_high"]).all())

    def test_route2_final_ladder_includes_mixed_model(self):
        coefficients = pd.DataFrame(
            [
                {
                    "model_id": "minus_gen_mean_r2m5_age_by_entropy",
                    "estimator_id": estimator,
                    "term": term,
                    "estimate": estimate,
                    "conf_low": estimate - 0.01,
                    "conf_high": estimate + 0.01,
                    "p_value": 0.01,
                }
                for estimator, term, estimate in [
                    ("row_ols_child_fe_cluster", "age_months_c", 0.09),
                    ("session_gee_exchangeable", "age_months_c", 0.08),
                    ("session_mundlak_gee", "age_within_child_c", 0.08),
                    ("session_mixedlm_random_age", "age_months_c", 0.10),
                ]
            ]
        )

        ladder = route2_final_ladder(coefficients, term_role="age")

        self.assertEqual(len(ladder), 4)
        self.assertIn("Mixed model", set(ladder["model"]))
        self.assertIn("random child intercept and age slope", " ".join(ladder["adjustment"]))

    def test_word_table_documents_fixed_effects(self):
        effects = pd.DataFrame(
            [
                {
                    "scorer": scorer,
                    "question_id": "same_word_k3_age",
                    "model_id": "same_word_k3_primary",
                    "estimate": estimate,
                    "ci_low": estimate - 0.01,
                    "ci_high": estimate + 0.01,
                    "bootstrap_ci_low": estimate - 0.02,
                    "bootstrap_ci_high": estimate + 0.02,
                }
                for scorer, estimate in [
                    ("Mistral", -0.03),
                    ("Qwen3-14B", -0.02),
                    ("TinyDialogues", -0.04),
                ]
            ]
        )

        table = word_effect_table(effects)

        self.assertEqual(table["scorer"].tolist(), ["Mistral", "Qwen3-14B", "TinyDialogues"])
        self.assertTrue(table["adjustment"].str.contains("child and word fixed effects").all())
        self.assertTrue(table["adjustment"].str.contains("child bootstrap").all())

    def test_status_gate_refuses_nonpass_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps({"status": "FAIL"}), encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "expected PASS"):
                require_status(path, key="status", expected="PASS")

    def test_protected_hash_check_detects_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            protected = root / "old_report.md"
            protected.write_text("original", encoding="utf-8")
            before = protected_hashes([protected])
            protected.write_text("changed", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "protected audited artifact changed"):
                assert_protected_unchanged(before)

    def test_report_uses_july_model_sequence_and_regression_line_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "report.md"
            figure_names = [
                "route1_raw",
                "route1_simple",
                "route1_primary",
                "route1_complex",
                "route2_raw",
                "route2_primary",
                "route2_complex",
                "word_descriptive",
                "word_primary",
                "word_nonlinear",
            ]
            figures = {}
            for name in figure_names:
                path = root / f"{name}.png"
                path.write_bytes(b"placeholder")
                figures[name] = path
            route_row = {
                "model": "Repeated-measures GEE",
                "adjustment": "grouped by child",
                "estimate": -0.1,
                "ci_low": -0.2,
                "ci_high": -0.01,
                "p_value": 0.01,
            }
            simple = pd.DataFrame(
                [{"sample": "PBM", "age_estimate": -0.05, "ci_low": -0.08, "ci_high": -0.02}]
            )
            word_row = {
                "scorer": "Mistral",
                "question": "Same-word contextual age",
                "estimate": -0.03,
                "ci_low": -0.04,
                "ci_high": -0.02,
                "bootstrap_ci_low": -0.05,
                "bootstrap_ci_high": -0.01,
                "adjustment": "child and word fixed effects; child bootstrap",
            }

            write_report(
                report,
                figures=figures,
                simple_models=simple,
                route1_tables={"Mistral PBM discovery": pd.DataFrame([route_row])},
                route2_age=pd.DataFrame([route_row]),
                route2_interaction=pd.DataFrame([route_row]),
                word_table=pd.DataFrame([word_row]),
            )
            text = report.read_text(encoding="utf-8")

        for heading in ["### Model 0", "### Model 1", "### Model 2", "### Model 3"]:
            self.assertIn(heading, text)
        self.assertGreaterEqual(text.count("regression line"), 4)
        self.assertIn("PBM discovery", text)
        self.assertIn("non-PBM confirmation", text)
        self.assertIn("GEE", text)
        self.assertIn("mixed-effects", text)
        self.assertIn("Original audited August package", text)

    def test_report_site_separates_data_route1_route2_and_word_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "report.md"
            figure_names = [
                "data_age_coverage",
                "route1_raw",
                "route1_simple",
                "route1_primary",
                "route1_complex",
                "route2_raw",
                "route2_primary",
                "route2_complex",
                "word_descriptive",
                "word_primary",
                "word_nonlinear",
            ]
            figures = {}
            for name in figure_names:
                path = root / f"{name}.png"
                path.write_bytes(b"placeholder")
                figures[name] = path
            route_row = {
                "model": "Repeated-measures GEE",
                "adjustment": "grouped by child",
                "estimate": -0.1,
                "ci_low": -0.2,
                "ci_high": -0.01,
                "p_value": 0.01,
            }
            simple = pd.DataFrame(
                [{"sample": "PBM", "age_estimate": -0.05, "ci_low": -0.08, "ci_high": -0.02}]
            )
            word_row = {
                "scorer": "Mistral",
                "question": "Same-word contextual age",
                "estimate": -0.03,
                "ci_low": -0.04,
                "ci_high": -0.02,
                "bootstrap_ci_low": -0.05,
                "bootstrap_ci_high": -0.01,
                "adjustment": "child and word fixed effects; child bootstrap",
            }
            sample_table = pd.DataFrame(
                [
                    {
                        "analysis": "Route 1",
                        "sample": "PBM discovery",
                        "analysis_rows": 444325,
                        "children": 21,
                        "role": "discovery",
                    },
                    {
                        "analysis": "Word level",
                        "sample": "PBM shared occurrences",
                        "analysis_rows": 1032963,
                        "children": 21,
                        "role": "scorer robustness",
                    },
                ]
            )

            pages = write_report_site(
                report,
                figures=figures,
                sample_table=sample_table,
                simple_models=simple,
                route1_tables={"Mistral PBM discovery": pd.DataFrame([route_row])},
                route2_age=pd.DataFrame([route_row]),
                route2_interaction=pd.DataFrame([route_row]),
                word_table=pd.DataFrame([word_row]),
            )

            self.assertEqual(
                set(pages),
                {"data", "route1", "route2", "word_level"},
            )
            for path in pages.values():
                self.assertTrue(path.exists())
                page_text = path.read_text(encoding="utf-8")
                self.assertIn("Data overview", page_text)
                self.assertIn("Route 1", page_text)
                self.assertIn("Route 2", page_text)
                self.assertIn("Word level", page_text)

            data_text = pages["data"].read_text(encoding="utf-8")
            route1_text = pages["route1"].read_text(encoding="utf-8")
            route2_text = pages["route2"].read_text(encoding="utf-8")
            word_text = pages["word_level"].read_text(encoding="utf-8")

        self.assertIn("Data and analysis overview", data_text)
        self.assertIn("Developmental coverage", data_text)
        self.assertIn("PBM discovery", data_text)
        self.assertIn("Model 0", route1_text)
        self.assertIn("Model 3", route1_text)
        self.assertNotIn("## Word-level results", route1_text)
        self.assertIn("Model 0", route2_text)
        self.assertIn("mixed", route2_text.lower())
        self.assertNotIn("## Route 1 results", route2_text)
        self.assertIn("same word", word_text.lower())
        self.assertIn("child and word", word_text.lower())
        self.assertNotIn("## Route 2 results", word_text)


if __name__ == "__main__":
    unittest.main()
