import tempfile
import unittest
from pathlib import Path
import sys

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from src.build_response_space_analysis_suite import (
    age_bin_midpoint,
    fit_repeated_measure_models,
    model_specs,
    mundlak_formula,
    session_aggregate_frame,
    write_predictor_exports,
)


class ResponseSpaceAnalysisSuiteTests(unittest.TestCase):
    def test_age_bin_midpoint(self):
        self.assertEqual(age_bin_midpoint("024-029"), 26.5)
        self.assertEqual(age_bin_midpoint("006-023"), 14.5)

    def test_mundlak_formula_uses_within_child_age_for_interaction(self):
        formula = (
            "sum_bits ~ age_months_c + nb_words_c + response_entropy_bits_c + "
            "age_months_c:response_entropy_bits_c + C(child_id)"
        )

        out = mundlak_formula(formula)

        self.assertIn("age_within_child_c + child_mean_age_c", out)
        self.assertIn("age_within_child_c:response_entropy_bits_c", out)
        self.assertNotIn("C(child_id)", out)

    def test_session_aggregate_frame_keeps_child_session_level(self):
        frame = toy_response_space_frame()
        spec = next(s for s in model_specs() if s.model_id == "route2_nb_words_effort_choice")

        session = session_aggregate_frame(frame, spec)

        self.assertEqual(len(session), 32)
        self.assertIn("n_utterances", session.columns)
        self.assertIn("age_within_child_c", session.columns)
        self.assertIn("child_mean_age_c", session.columns)
        self.assertTrue((session["n_utterances"] == 2).all())

    def test_repeated_measure_models_include_session_estimators(self):
        frame = toy_response_space_frame()
        spec = next(s for s in model_specs() if s.model_id == "route2_nb_words_effort_choice")

        results = fit_repeated_measure_models(frame, spec)
        summaries = pd.DataFrame([item[0] for item in results])

        self.assertIn("row_ols_child_fe_cluster", set(summaries["estimator_id"]))
        self.assertIn("session_gee_exchangeable", set(summaries["estimator_id"]))
        self.assertIn("session_mundlak_gee", set(summaries["estimator_id"]))
        self.assertIn("session_mixedlm_random_age", set(summaries["estimator_id"]))
        self.assertTrue(summaries[summaries["estimator_id"].eq("session_gee_exchangeable")]["status"].iloc[0] == "fit")

    def test_predictor_exports_are_context_and_utterance_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = toy_response_space_frame()
            paths = write_predictor_exports(frame, root)

            context = pd.read_csv(paths["context_predictors"])
            utterance = pd.read_csv(paths["utterance_predictors"])
            enriched = pd.read_csv(paths["route1_real_child_enriched"])

            self.assertEqual(len(context), frame["response_entropy_context_id"].nunique())
            self.assertEqual(len(utterance), frame["score_id"].nunique())
            self.assertIn("sum_bits", enriched.columns)
            self.assertIn("response_entropy_bits", enriched.columns)


def toy_response_space_frame() -> pd.DataFrame:
    rows = []
    for child_index, child_id in enumerate(["Ada", "Ben", "Cara", "Davi"]):
        for session in range(8):
            age = 20 + child_index * 2 + session * 2
            for utt in range(2):
                entropy = 1.0 + 0.1 * session + 0.05 * child_index
                expected = 2.0 + 0.05 * age + 0.1 * utt
                words = 1.0 + 0.07 * age + 0.5 * entropy + 0.2 * utt
                rows.append(
                    {
                        "score_id": f"{child_id}-{session}-{utt}",
                        "utterance_id": f"u-{child_id}-{session}-{utt}",
                        "dataset": "Toy",
                        "child_id": child_id,
                        "session_id": str(session),
                        "age_months": float(age),
                        "age_bin": "024-029" if age < 30 else "030-035",
                        "target_utterance_clean": "toy words",
                        "nb_words": words,
                        "nb_morphemes": words + 0.4,
                        "nb_syllables_pkg": words + 0.8,
                        "nb_phonemes": words * 3.0,
                        "sum_bits": 8.0 + 1.8 * words - 0.2 * age + entropy,
                        "mean_bits_per_token": 3.0 + 0.1 * entropy,
                        "context_entropy_bits": 2.0 + 0.03 * session,
                        "route2_context_word_count": 5 + session,
                        "response_entropy_context_id": f"c-{child_id}-{session}",
                        "response_entropy_bits": entropy,
                        "response_entropy_empirical_bits": entropy - 0.05,
                        "response_unique_response_count": 10 + session,
                        "response_top_probability": 0.2,
                        "response_rejection_rate": 0.01,
                        "response_valid_selected_count": 100,
                        "response_invalid_selected_count": 0,
                        "generated_expected_words": expected,
                        "generated_median_words": expected,
                        "generated_p90_words": expected + 2,
                        "generated_valid_sample_words_sd": 1.0,
                        "generated_valid_sample_words_iqr": 1.0,
                        "generated_valid_sample_words_probability_le_3": 0.5,
                        "generated_valid_sample_words_probability_gt_20": 0.0,
                        "generated_valid_word_count_entropy_bits": 1.2,
                        "child_words_minus_generated_mean": words - expected,
                        "child_words_z_vs_generated": words - expected,
                        "child_words_percentile_in_generated_distribution": 0.5,
                        "child_words_cdf_lt_generated_distribution": 0.4,
                        "child_words_cdf_le_generated_distribution": 0.6,
                        "child_shorter_than_generated_median": words < expected,
                        "child_longer_than_generated_p90": words > expected + 2,
                        "fallback_used_for_context": False,
                        "valid_sample_count": 100,
                    }
                )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    unittest.main()
