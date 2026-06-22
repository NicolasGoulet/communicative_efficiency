import unittest
import re
import inspect

import pandas as pd

from src import build_route1_child_length_controlled_model_suite as suite


def synthetic_route1_rows() -> pd.DataFrame:
    rows = []
    for child_idx, child_id in enumerate(["c1", "c2"]):
        for session_idx in range(3):
            for context_k in ["k1", "k3"]:
                for effort in [1, 2, 3, 4]:
                    for repeat in range(2):
                        age = 24 + child_idx * 6 + session_idx * 2
                        rows.append(
                            {
                                "score_id": f"{child_id}-{session_idx}-{context_k}-{effort}-{repeat}",
                                "utterance_id": f"utt-{child_id}-{session_idx}-{context_k}-{effort}-{repeat}",
                                "dataset": "demo",
                                "child_id": child_id,
                                "session_id": f"s{session_idx}",
                                "age_months": str(age),
                                "age_bin": "024-029" if age < 30 else "030-035",
                                "role": "child",
                                "target_variant": "real",
                                "target_source": "real",
                                "context_k": context_k,
                                "context_text": "what is that ?" if repeat % 2 == 0 else "look there",
                                "context_entropy_bits": str(2.0 + 0.1 * effort),
                                "sum_bits": str(5.0 + effort * 2.0 - age * 0.05 + repeat * 0.1),
                                "nb_words": str(effort),
                                "nb_morphemes": str(effort),
                                "nb_syllables_cmu_or_pkg": str(effort),
                                "nb_syllables_pkg": str(effort),
                                "nb_phonemes": str(effort * 2),
                            }
                        )
    return pd.DataFrame(rows)


class ChildLengthControlledSuiteTests(unittest.TestCase):
    def test_every_formula_controls_target_effort(self):
        for formula in suite.FORMULAS:
            with self.subTest(formula=formula.formula_id):
                controls_effort = "effort_c" in formula.terms or "C(effort_value_int)" in formula.terms
                self.assertTrue(controls_effort)
                self.assertFalse(any(re.search(r"(?<!\*)\*(?!\*)", term) for term in formula.terms))

    def test_interaction_terms_keep_lower_order_terms(self):
        for formula in suite.FORMULAS:
            terms = set(formula.terms)
            for term in formula.terms:
                if ":" not in term:
                    continue
                with self.subTest(formula=formula.formula_id, term=term):
                    for part in term.split(":"):
                        self.assertIn(part, terms)

    def test_statsmodels_formula_adds_child_fixed_effects_only_when_requested(self):
        formula = suite.formula_lookup()["F01"]
        row_ols = suite.estimator_lookup()["row_ols_fe_cluster"]
        mixed = suite.estimator_lookup()["agg_mixed_random_intercept"]

        self.assertIn("C(child_id)", suite.statsmodels_formula(formula, row_ols))
        self.assertNotIn("C(child_id)", suite.statsmodels_formula(formula, mixed))

    def test_mlu_proof_formula_uses_exact_length_categories(self):
        formula = suite.formula_lookup()["F19"]
        estimator = suite.estimator_lookup()["row_ols_fe_cluster"]

        model_formula = suite.statsmodels_formula(formula, estimator)

        self.assertIn("C(effort_value_int)", model_formula)
        self.assertIn("age_c:C(effort_value_int)", model_formula)
        self.assertNotIn("effort_c", model_formula)

    def test_report_language_does_not_name_course_branding(self):
        self.assertNotIn("Advanced Data Analytics", inspect.getsource(suite))

    def test_prepare_analysis_frame_respects_context_specific_base(self):
        raw = synthetic_route1_rows()
        base = suite.build_child_base_frame(raw, "nb_words", "parent_context_nb_words")
        base_k3 = base[base["context_k"].astype(str).eq("k3")].copy()
        formula = suite.formula_lookup()["F02"]

        prepared, error = suite.prepare_analysis_frame(base_k3, formula, "aggregate")

        self.assertEqual("", error)
        self.assertGreater(len(prepared), 0)
        self.assertIn("route1_outcome", prepared.columns)
        self.assertIn("age_c", prepared.columns)
        self.assertIn("effort_c", prepared.columns)
        self.assertEqual(len(base_k3), int(prepared["n_source_rows"].sum()))

    def test_prediction_grid_is_fixed_effort_after_fit(self):
        raw = synthetic_route1_rows()
        base = suite.build_child_base_frame(raw, "nb_words", "parent_context_nb_words")
        base = base[base["context_k"].astype(str).eq("k3")].copy()
        formula = suite.formula_lookup()["F02"]
        estimator = suite.estimator_lookup()["row_ols_fe_cluster"]
        prepared, error = suite.prepare_analysis_frame(base, formula, "row")
        self.assertEqual("", error)
        model_formula = suite.statsmodels_formula(formula, estimator)
        result = suite.fit_model(prepared, model_formula, estimator)

        predictions = suite.fixed_prediction_grid(
            result,
            prepared,
            formula=formula,
            estimator=estimator,
            formula_text=model_formula,
            effort_col="nb_words",
            effort_label="Words",
            context_k="k3",
            n_points=8,
        )

        self.assertFalse(predictions.empty)
        self.assertGreaterEqual(predictions["fixed_effort_value"].nunique(), 2)
        self.assertTrue(predictions["predicted_sum_bits"].notna().any())


if __name__ == "__main__":
    unittest.main()
