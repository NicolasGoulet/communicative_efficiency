import unittest

from src import build_supervisor_formula_estimator_sensitivity as sens


class SupervisorFormulaEstimatorSensitivityTests(unittest.TestCase):
    def test_four_current_supervisor_formulas_are_defined(self):
        self.assertEqual([item.spec.formula_id for item in sens.SUPERVISOR_FORMULAS], ["M1", "M2", "M3", "M4"])
        self.assertFalse(sens.SUPERVISOR_FORMULAS[0].child_identity)
        self.assertTrue(all(item.child_identity for item in sens.SUPERVISOR_FORMULAS[1:]))

    def test_m4_formula_has_context_controls_without_question_type(self):
        m4 = next(item for item in sens.SUPERVISOR_FORMULAS if item.spec.formula_id == "M4")
        row_estimator = next(item for item in sens.CHILD_IDENTITY_ESTIMATORS if item.estimator_id == "row_ols_fe_cluster")

        formula = sens.statsmodels_formula(m4, row_estimator)

        self.assertIn("parent_context_effort_c", formula)
        self.assertIn("context_entropy_c", formula)
        self.assertIn("age_c:effort_c", formula)
        self.assertIn("C(child_id)", formula)
        self.assertNotIn("question_type", formula)

    def test_mixed_model_adapts_child_identity_without_fixed_child_dummies(self):
        m3 = next(item for item in sens.SUPERVISOR_FORMULAS if item.spec.formula_id == "M3")
        mixed = next(item for item in sens.CHILD_IDENTITY_ESTIMATORS if item.estimator_id == "age_word_mixed_random_intercept")

        formula = sens.statsmodels_formula(m3, mixed)

        self.assertIn("age_c:effort_c", formula)
        self.assertNotIn("C(child_id)", formula)
        self.assertEqual(mixed.random_effects, "1")
        self.assertIn("random child intercept", sens.adaptation_note(m3, mixed))

    def test_m1_estimator_plan_does_not_add_child_fixed_effects(self):
        m1 = next(item for item in sens.SUPERVISOR_FORMULAS if item.spec.formula_id == "M1")

        for estimator in sens.M1_ESTIMATORS:
            with self.subTest(estimator=estimator.estimator_id):
                formula = sens.statsmodels_formula(m1, estimator)
                self.assertNotIn("C(child_id)", formula)

    def test_no_estimator_uses_session_variance_component(self):
        for estimator in (*sens.M1_ESTIMATORS, *sens.CHILD_IDENTITY_ESTIMATORS):
            with self.subTest(estimator=estimator.estimator_id):
                self.assertFalse(estimator.session_variance_component)
                self.assertNotIn("session", estimator.estimator_id)


if __name__ == "__main__":
    unittest.main()
