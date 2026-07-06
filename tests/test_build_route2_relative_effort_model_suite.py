import sys
import unittest
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_route2_relative_effort_model_suite import (  # noqa: E402
    add_route2_relative_columns,
    fit_models,
    model_specs,
    mundlak_formula,
    session_aggregate_frame,
)


class Route2RelativeEffortModelSuiteTests(unittest.TestCase):
    def test_add_route2_relative_columns_computes_ratio_and_binary_outcomes(self):
        frame = toy_route2_frame().drop(columns=["child_words_ratio_to_generated_mean"])

        out = add_route2_relative_columns(frame)

        expected = out.loc[0, "nb_words"] / out.loc[0, "generated_expected_words"]
        self.assertAlmostEqual(out.loc[0, "child_words_ratio_to_generated_mean"], expected)
        self.assertTrue(set(out["child_shorter_than_generated_median"].unique()).issubset({0.0, 1.0}))
        self.assertTrue(set(out["child_longer_than_generated_p90"].unique()).issubset({0.0, 1.0}))

    def test_final_model_keeps_interaction_in_formula_not_required_columns(self):
        spec = next(s for s in model_specs() if s.model_id == "minus_gen_mean_r2m5_age_by_entropy")
        no_fallback = next(s for s in model_specs() if s.model_id == "minus_gen_mean_r2m5_age_by_entropy_no_fallback")

        self.assertIn("age_months_c:response_entropy_bits_c", spec.formula)
        self.assertNotIn("age_months_c:response_entropy_bits_c", spec.required_cols)
        self.assertFalse(spec.exclude_fallback)
        self.assertTrue(no_fallback.exclude_fallback)

    def test_mundlak_formula_uses_within_child_age_for_interaction(self):
        spec = next(s for s in model_specs() if s.model_id == "minus_gen_mean_r2m5_age_by_entropy")

        out = mundlak_formula(spec.formula)

        self.assertIn("age_within_child_c + child_mean_age_c", out)
        self.assertIn("age_within_child_c:response_entropy_bits_c", out)
        self.assertNotIn("C(child_id)", out)

    def test_session_aggregate_frame_keeps_child_session_level(self):
        frame = toy_route2_frame()
        spec = next(s for s in model_specs() if s.model_id == "minus_gen_mean_r2m4_full_controls")

        session = session_aggregate_frame(frame, spec)

        self.assertEqual(len(session), 32)
        self.assertIn("n_utterances", session.columns)
        self.assertIn("age_within_child_c", session.columns)
        self.assertIn("child_mean_age_c", session.columns)
        self.assertTrue((session["n_utterances"] == 2).all())

    def test_fit_models_includes_peer_review_estimator_checks(self):
        frame = toy_route2_frame()
        spec = next(s for s in model_specs() if s.model_id == "minus_gen_mean_r2m2_response_entropy")

        results = fit_models(frame, spec)
        summaries = pd.DataFrame([item[0] for item in results])

        self.assertIn("row_ols_child_fe_cluster", set(summaries["estimator_id"]))
        self.assertIn("session_gee_exchangeable", set(summaries["estimator_id"]))
        self.assertIn("session_mundlak_gee", set(summaries["estimator_id"]))
        self.assertIn("session_mixedlm_random_age", set(summaries["estimator_id"]))
        self.assertEqual(
            summaries[summaries["estimator_id"].eq("row_ols_child_fe_cluster")]["status"].iloc[0],
            "fit",
        )
        self.assertEqual(
            summaries[summaries["estimator_id"].eq("session_gee_exchangeable")]["status"].iloc[0],
            "fit",
        )


def toy_route2_frame() -> pd.DataFrame:
    rows = []
    for child_index, child_id in enumerate(["Ada", "Ben", "Cara", "Davi"]):
        for session in range(8):
            age = 18.0 + child_index * 2.0 + session * 2.0
            for utt in range(2):
                entropy = 1.0 + 0.1 * session + 0.04 * child_index
                context_words = 5.0 + session
                context_entropy = 2.0 + 0.04 * session + 0.02 * utt
                generated_mean = 2.2 + 0.035 * age + 0.35 * entropy + 0.06 * context_words
                child_words = generated_mean - 0.25 + 0.025 * age - 0.15 * entropy + 0.18 * utt
                generated_median = generated_mean + 0.05
                generated_p90 = generated_mean + 1.2
                rows.append(
                    {
                        "score_id": f"{child_id}-{session}-{utt}",
                        "utterance_id": f"u-{child_id}-{session}-{utt}",
                        "dataset": "Toy",
                        "child_id": child_id,
                        "session_id": str(session),
                        "age_months": age,
                        "age_bin": "006-023" if age < 24 else ("024-029" if age < 30 else "030-035"),
                        "target_utterance_clean": "toy words",
                        "nb_words": child_words,
                        "context_entropy_bits": context_entropy,
                        "route2_context_word_count": context_words,
                        "response_entropy_context_id": f"c-{child_id}-{session}",
                        "response_entropy_bits": entropy,
                        "response_entropy_empirical_bits": entropy - 0.05,
                        "response_unique_response_count": 10 + session,
                        "response_top_probability": 0.2,
                        "response_rejection_rate": 0.01,
                        "response_valid_selected_count": 100,
                        "response_invalid_selected_count": 0,
                        "generated_expected_words": generated_mean,
                        "generated_median_words": generated_median,
                        "generated_p90_words": generated_p90,
                        "generated_valid_sample_words_sd": 1.0,
                        "generated_valid_sample_words_iqr": 1.0,
                        "generated_valid_sample_words_probability_le_3": 0.5,
                        "generated_valid_sample_words_probability_gt_20": 0.0,
                        "generated_valid_word_count_entropy_bits": 1.2,
                        "child_words_minus_generated_mean": child_words - generated_mean,
                        "child_words_z_vs_generated": (child_words - generated_mean) / 1.0,
                        "child_words_percentile_in_generated_distribution": 0.35 + 0.02 * utt + 0.01 * session,
                        "child_words_ratio_to_generated_mean": child_words / generated_mean,
                        "child_shorter_than_generated_median": child_words < generated_median,
                        "child_longer_than_generated_p90": child_words > generated_p90,
                        "fallback_used_for_context": session == 0 and utt == 0 and child_index == 0,
                        "valid_sample_count": 100,
                    }
                )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    unittest.main()
