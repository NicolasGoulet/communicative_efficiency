import unittest

from src.build_supervisor_union_context_model import MODEL_ID, build_union_specs


class SupervisorUnionContextModelTests(unittest.TestCase):
    def test_union_spec_uses_both_context_controls_without_question_type(self):
        specs = build_union_specs(["nb_words"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.model_id, MODEL_ID)
        self.assertEqual(spec.effort_col, "nb_words")
        self.assertTrue(spec.needs_parent_context_effort)
        self.assertTrue(spec.needs_context_entropy)
        self.assertFalse(spec.needs_question_type)
        self.assertIn("age_c:effort_c", spec.statsmodels_formula)
        self.assertIn("parent_context_effort_c", spec.statsmodels_formula)
        self.assertIn("context_entropy_c", spec.statsmodels_formula)
        self.assertNotIn("question_type", spec.statsmodels_formula)


if __name__ == "__main__":
    unittest.main()
