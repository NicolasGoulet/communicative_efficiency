from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_scientific_answer_synthesis import build_scientific_synthesis


class ScientificAnswerSynthesisTests(unittest.TestCase):
    def test_saved_results_are_separated_and_interpreted_without_refitting(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tiny = root / "tiny.csv"
            mistral = root / "mistral.csv"
            route2 = root / "route2.csv"
            word = root / "word.csv"
            onset = root / "onset.json"

            pd.DataFrame(
                [
                    {
                        "scope": "pbm_discovery",
                        "model_id": model_id,
                        "term": "age_c",
                        "estimate": estimate,
                        "ci_low": low,
                        "ci_high": high,
                    }
                    for model_id, estimate, low, high in (
                        ("P1_k3_contextual", -0.2, -0.3, -0.1),
                        ("P2_k0_unconditional", -0.25, -0.35, -0.15),
                        ("P3_k3_context_gain", -0.05, -0.08, -0.02),
                    )
                ]
            ).to_csv(tiny, index=False)
            pd.DataFrame(
                [
                    {
                        "scope": scope,
                        "model_id": model_id,
                        "term": "age_c",
                        "estimate": estimate,
                        "ci_low": low,
                        "ci_high": high,
                    }
                    for scope, model_id, estimate, low, high in (
                        ("pbm_discovery", "P1_k3_contextual", -0.13, -0.18, -0.08),
                        ("pbm_discovery", "P2_k0_unconditional", -0.16, -0.21, -0.11),
                        ("pbm_discovery", "P3_k3_context_gain", -0.03, -0.05, -0.01),
                        ("non_pbm_confirmation", "P1_k3_contextual", -0.06, -0.13, 0.01),
                        ("non_pbm_confirmation", "P2_k0_unconditional", -0.09, -0.14, -0.03),
                        ("non_pbm_confirmation", "P3_k3_context_gain", -0.03, -0.05, -0.01),
                    )
                ]
            ).to_csv(mistral, index=False)
            pd.DataFrame(
                [
                    {
                        "model_id": model_id,
                        "estimator_id": "session_gee_exchangeable",
                        "outcome": outcome,
                        "term": term,
                        "estimate": estimate,
                        "conf_low": low,
                        "conf_high": high,
                        "p_value": 0.01,
                    }
                    for model_id, outcome, term, estimate, low, high in (
                        (
                            "minus_gen_mean_r2m5_age_by_entropy",
                            "child_words_minus_generated_mean",
                            "age_months_c",
                            0.09,
                            0.07,
                            0.11,
                        ),
                        (
                            "minus_gen_mean_r2m5_age_by_entropy",
                            "child_words_minus_generated_mean",
                            "age_months_c:response_entropy_bits_c",
                            -0.02,
                            -0.04,
                            -0.01,
                        ),
                        (
                            "percentile_in_gen_distribution_r2m5_age_by_entropy",
                            "child_words_percentile_in_generated_distribution",
                            "age_months_c",
                            0.01,
                            0.005,
                            0.02,
                        ),
                        (
                            "percentile_in_gen_distribution_r2m5_age_by_entropy",
                            "child_words_percentile_in_generated_distribution",
                            "age_months_c:response_entropy_bits_c",
                            -0.003,
                            -0.005,
                            -0.001,
                        ),
                    )
                ]
            ).to_csv(route2, index=False)
            pd.DataFrame(
                [
                    {
                        "question_id": "same_word_k3_age",
                        "question": "Does contextual surprisal for the same word decrease with age?",
                        "common_direction": "negative",
                        "cluster_supported_scorers": 3,
                        "scorers": 3,
                        "bootstrap_supported_scorers": 3,
                        "bootstrap_available_scorers": 3,
                        "replication_status": "direction_and_interval_robust",
                    },
                    {
                        "question_id": "context_gain_age",
                        "question": "Does word-level context gain change with age?",
                        "common_direction": "mixed",
                        "cluster_supported_scorers": 1,
                        "scorers": 3,
                        "bootstrap_supported_scorers": 1,
                        "bootstrap_available_scorers": 3,
                        "replication_status": "scorer_dependent",
                    },
                ]
            ).to_csv(word, index=False)
            onset.write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "scopes": [
                            {"scope": "pbm_discovery", "sustained_onset": "not_established"},
                            {"scope": "non_pbm_confirmation", "sustained_onset": "not_established"},
                        ],
                    }
                )
            )

            report = build_scientific_synthesis(
                tiny_direct_path=tiny,
                mistral_direct_path=mistral,
                route2_path=route2,
                word_summary_path=word,
                onset_audit_path=onset,
                output_dir=root / "out",
                figure_path=root / "fig.png",
                report_md=root / "report.md",
                report_html=root / "report.html",
                inventory_rows=[{"family": "test", "fitted_variants": 7, "status": "PASS"}],
            )

            self.assertEqual(report["status"], "PASS")
            direct = pd.read_csv(root / "out" / "direct_primary_estimates.csv")
            non_pbm_p1 = direct[
                direct["sample"].eq("non-PBM58 confirmation")
                & direct["model_id"].eq("P1_k3_contextual")
            ].iloc[0]
            self.assertEqual(
                non_pbm_p1["evidence_status"],
                "direction_consistent_not_confirmed",
            )
            non_pbm_p3 = direct[
                direct["sample"].eq("non-PBM58 confirmation")
                & direct["model_id"].eq("P3_k3_context_gain")
            ].iloc[0]
            self.assertEqual(
                non_pbm_p3["evidence_status"], "contrary_to_registered_direction"
            )
            markdown = (root / "report.md").read_text(encoding="utf-8")
            self.assertIn("7 fitted variants", markdown)
            self.assertIn("weaker in higher-entropy contexts", markdown)
            self.assertIn("does not meet the frozen confirmation criterion", markdown)
            self.assertIn("not established", markdown)
            self.assertTrue((root / "report.html").is_file())
            self.assertTrue((root / "fig.png").is_file())


if __name__ == "__main__":
    unittest.main()
