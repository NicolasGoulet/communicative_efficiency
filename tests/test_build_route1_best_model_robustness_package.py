import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_route1_best_model_robustness_package import (
    CORE_FORMULAS,
    ESTIMATOR_SPECS,
    assign_effort_band,
    build_estimator_coverage,
    build_key_term_relation_summary,
    one_line_effect_sentences,
    parent_context_word_count,
    prepare_model_frame,
)
from build_route1_formula_permutation_estimator_report import (
    CORE_FORMULAS as PERMUTATION_CORE_FORMULAS,
    ESTIMATOR_SPECS as PERMUTATION_ESTIMATOR_SPECS,
    exact_row_level_atlas_model,
)


class Route1BestModelRobustnessPackageTests(unittest.TestCase):
    def test_core_formulas_cover_requested_models_and_keep_lower_order_terms(self):
        formulas = {formula.model_id: formula for formula in CORE_FORMULAS}

        self.assertEqual(
            set(formulas),
            {
                "M2",
                "M3",
                "M4c",
                "M5",
                "M5_no_question",
                "M5_age_effort_no_question",
                "M5_age_effort_question",
                "M5_parent_reaction_no_question",
                "M5_parent_reaction_question",
                "M15",
            },
        )
        self.assertIn("age_c + effort_c + age_c:effort_c", formulas["M3"].fe_formula)
        self.assertIn("age_c + effort_c + age_c:effort_c", formulas["M15"].fe_formula)
        self.assertNotIn("*", formulas["M3"].fe_formula)
        self.assertNotIn("*", formulas["M15"].fe_formula)
        self.assertNotIn("C(question_type)", formulas["M5_no_question"].fe_formula)
        self.assertIn("C(question_type)", formulas["M5"].fe_formula)
        self.assertIn("age_c:effort_c", formulas["M5_age_effort_no_question"].fe_formula)
        self.assertIn("age_c:effort_c", formulas["M5_age_effort_question"].fe_formula)
        self.assertNotIn("C(question_type)", formulas["M5_age_effort_no_question"].fe_formula)
        self.assertIn("C(question_type)", formulas["M5_age_effort_question"].fe_formula)
        self.assertIn("age_c:parent_context_effort_c", formulas["M5_parent_reaction_no_question"].fe_formula)
        self.assertIn("effort_c:parent_context_effort_c", formulas["M5_parent_reaction_question"].fe_formula)
        self.assertIn("context_entropy_c", formulas["M15"].fe_formula)
        self.assertIn("parent_context_effort_c", formulas["M15"].fe_formula)
        self.assertIn("C(question_type)", formulas["M15"].fe_formula)
        self.assertIn("age_c:context_entropy_c", formulas["M15"].fe_formula)
        self.assertIn("effort_c:parent_context_effort_c", formulas["M15"].fe_formula)

    def test_estimator_specs_cover_requested_families(self):
        labels = {spec.label for spec in ESTIMATOR_SPECS}

        self.assertIn("OLS + child fixed effects + clustered SE", labels)
        self.assertIn("GEE Gaussian, clustered by child", labels)
        self.assertIn("GEE Gamma/log, clustered by child", labels)
        self.assertIn("GLM Gaussian", labels)
        self.assertIn("GLM Gamma/log", labels)
        self.assertIn("MixedLM random child intercept", labels)
        self.assertIn("MixedLM random child age slope", labels)

    def test_effort_and_context_helpers_are_stable(self):
        self.assertEqual(assign_effort_band(1), "1-4")
        self.assertEqual(assign_effort_band(8), "5-8")
        self.assertEqual(assign_effort_band(12), "9-12")
        self.assertEqual(assign_effort_band(13), "13+")
        self.assertEqual(parent_context_word_count("do you want the red cup?"), 6)

    def test_prepare_model_frame_centers_predictors_for_context_formula(self):
        formula = {item.model_id: item for item in CORE_FORMULAS}["M5"]
        frame = pd.DataFrame(
            {
                "mean_sum_bits": [10.0, 12.0, 14.0, 15.0],
                "age_months": [24.0, 30.0, 36.0, 42.0],
                "mean_effort": [2.0, 3.0, 4.0, 5.0],
                "mean_context_entropy": [5.0, 6.0, 7.0, 8.0],
                "mean_parent_context_effort": [2.0, 2.0, 3.0, 4.0],
                "question_type": ["not question", "wh-question", "not question", "yes/no question"],
                "child_id": ["Ada", "Ada", "Ben", "Ben"],
            }
        )

        model_frame = prepare_model_frame(frame, formula)

        self.assertAlmostEqual(float(model_frame["age_c"].mean()), 0.0)
        self.assertAlmostEqual(float(model_frame["effort_c"].mean()), 0.0)
        self.assertAlmostEqual(float(model_frame["context_entropy_c"].mean()), 0.0)
        self.assertAlmostEqual(float(model_frame["parent_context_effort_c"].mean()), 0.0)

    def test_estimator_coverage_marks_formula_estimator_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            rows = []
            for formula in CORE_FORMULAS:
                for estimator in ESTIMATOR_SPECS:
                    rows.append(
                        {
                            "model_id": formula.model_id,
                            "estimator_id": estimator.estimator_id,
                            "status": "fit",
                        }
                    )
            summary = pd.DataFrame(rows)

            coverage = build_estimator_coverage(summary, output_dir)
            coverage_path_exists = (output_dir / "estimator_family_coverage.csv").exists()

        grid = coverage[coverage["model_id"].isin({formula.model_id for formula in CORE_FORMULAS})]
        self.assertEqual(len(grid), len(CORE_FORMULAS) * len(ESTIMATOR_SPECS))
        self.assertTrue((grid["status"] == "fit in aggregate package").all())
        self.assertTrue(coverage_path_exists)

    def test_key_term_relation_summary_records_parent_context_interactions(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            summary = pd.DataFrame(
                [
                    {
                        "model_id": "M5_parent_reaction_question",
                        "model_label": "Parent-context reaction model with question type",
                        "estimator_label": "OLS + child fixed effects + clustered SE",
                        "effect_scale": "additive bits",
                        "status": "fit",
                        "age_coef": -0.1,
                        "age_p": 0.01,
                        "effort_parent_context_effort_coef": 0.2,
                        "effort_parent_context_effort_p": 0.02,
                    }
                ]
            )

            relation = build_key_term_relation_summary(summary, output_dir)
            relation_path_exists = (output_dir / "aggregate_key_term_relation_summary.csv").exists()

        self.assertTrue(relation_path_exists)
        self.assertIn("Age at session", set(relation["term"]))
        self.assertIn("Child effort x parent context effort", set(relation["term"]))
        self.assertTrue(relation["relation_to_sum_bits"].str.contains("sum_bits").all())

    def test_one_line_effect_sentences_cover_promoted_interpretations(self):
        summary = pd.DataFrame(
            [
                {
                    "model_id": "M3",
                    "estimator_id": "ols_fe_cluster",
                    "status": "fit",
                    "age_effort_coef": -0.01,
                    "age_effort_p": 0.2,
                },
                {
                    "model_id": "M4c",
                    "estimator_id": "ols_fe_cluster",
                    "status": "fit",
                    "age_coef": -0.11,
                    "age_p": 0.001,
                },
                {
                    "model_id": "M5",
                    "estimator_id": "ols_fe_cluster",
                    "status": "fit",
                    "age_coef": -0.12,
                    "age_p": 0.001,
                    "effort_coef": 6.1,
                    "effort_p": 0.001,
                    "context_entropy_coef": -0.4,
                    "context_entropy_p": 0.01,
                },
            ]
        )

        effects = one_line_effect_sentences(summary)

        self.assertEqual(
            set(effects["effect"]),
            {
                "Age down arrow",
                "Effort up arrow",
                "Age x effort",
                "Context entropy",
                "Question type",
                "Caretaker contrast",
                "Heldout prediction",
            },
        )
        self.assertTrue(effects["sentence"].str.contains("fixed").any())

    def test_formula_permutation_grid_preserves_core_controls_and_lower_terms(self):
        self.assertEqual(len(PERMUTATION_CORE_FORMULAS), 36)

        for formula in PERMUTATION_CORE_FORMULAS:
            self.assertIn("age_c", formula.fe_formula)
            self.assertIn("effort_c", formula.fe_formula)
            self.assertIn("C(child_id)", formula.fe_formula)
            self.assertNotIn("*", formula.fe_formula)
            if "age_c:context_entropy_c" in formula.fe_formula:
                self.assertIn("context_entropy_c", formula.fe_formula)
            if "age_c:parent_context_effort_c" in formula.fe_formula:
                self.assertIn("parent_context_effort_c", formula.fe_formula)
            if "age_c:effort_c" in formula.fe_formula:
                self.assertIn("age_c + effort_c", formula.fe_formula)

        gee_specs = {
            spec.estimator_id: spec
            for spec in PERMUTATION_ESTIMATOR_SPECS
            if spec.estimator_id.startswith("gee_")
        }
        self.assertTrue(gee_specs)
        self.assertTrue(all(spec.uses_child_fixed_effects for spec in gee_specs.values()))
        self.assertTrue(all("C(child_id)" in spec.dependence for spec in gee_specs.values()))

    def test_formula_permutation_exact_row_level_atlas_mapping(self):
        self.assertEqual(exact_row_level_atlas_model("F01"), "M2")
        self.assertEqual(exact_row_level_atlas_model("F02"), "M3")
        self.assertEqual(exact_row_level_atlas_model("F04"), "M4c")
        self.assertEqual(exact_row_level_atlas_model("F07"), "M4a")
        self.assertEqual(exact_row_level_atlas_model("F33"), "M5")
        self.assertIsNone(exact_row_level_atlas_model("F12"))


if __name__ == "__main__":
    unittest.main()
