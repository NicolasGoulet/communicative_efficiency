from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_corrected_pbm_bayes_report import build_report


class CorrectedPbmBayesReportTests(unittest.TestCase):
    def test_builds_report_from_crossfit_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bayes_csv = root / "bayes.csv.gz"
            direct_csv = root / "direct.csv.gz"
            audit_json = root / "audit.json"
            sources = ["real", "random", "unigram", "bigram", "trigram"]
            bayes_rows = []
            direct_rows = []
            for row_index in range(3):
                scores = {"real": -3.0, "random": -9.0, "unigram": -6.0, "bigram": -5.0, "trigram": -4.0}
                weights = {source: 2 ** score for source, score in scores.items()}
                denominator = sum(weights.values())
                for source_index, source in enumerate(sources):
                    probability = weights[source] / denominator
                    bayes_rows.append(
                        {
                            "row_uid": f"r{row_index}",
                            "source_model": source,
                            "dataset": "Brown",
                            "child_id": "Adam",
                            "age_months": 20 + row_index,
                            "age_bin": "006-023",
                            "log2_p_u_crossfit": scores[source] - 0.2,
                            "context_log2_evidence_crossfit": 0.2 if source == "real" else 0.0,
                            "bayes_log2_score_crossfit": scores[source],
                            "candidate_set_probability": probability,
                            "candidate_set_bayes_bits": -math_log2(probability),
                            "candidate_set_rank": source_index + 1,
                            "candidate_set_size": 5,
                            "utterance_token_count": 2,
                            "context_token_count": 4,
                        }
                    )
                    direct_rows.append(
                        {
                            "row_uid": f"r{row_index}",
                            "source_model": source,
                            "mistral_sum_bits": 3.0 + source_index,
                            "mistral_bits_per_token": 1.5 + source_index / 2,
                        }
                    )
            pd.DataFrame(bayes_rows).to_csv(bayes_csv, index=False)
            pd.DataFrame(direct_rows).to_csv(direct_csv, index=False)
            audit_json.write_text(
                json.dumps(
                    {
                        "row_count": len(bayes_rows),
                        "estimator": "unit-crossfit",
                        "normalization_scope": "candidate_set_within_row",
                        "output_sha256": "unit",
                        "all_context_validation_pass": True,
                        "folds": [
                            {
                                "heldout_dataset": "Brown",
                                "matched_vs_shuffled_validation_n": 30,
                                "matched_context_pairwise_accuracy": 0.6,
                                "matched_minus_shuffled_context_evidence_mean_bits": 0.2,
                                "context_validation_pass": True,
                                "training_rows_total": 100,
                                "rows_excluded_heldout_dataset": 3,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = build_report(
                bayes_csv=bayes_csv,
                audit_json=audit_json,
                direct_csv=direct_csv,
                output_dir=root / "results",
                fig_dir=root / "figs",
                doc_md=root / "report.md",
                doc_html=None,
            )
            report = (root / "report.md").read_text(encoding="utf-8")
            self.assertEqual(result["row_count"], 15)
            self.assertIn("Corrected Cross-Fitted Bayes-Derived PBM Report", report)
            self.assertIn("alternative Bayes-derived candidate scorer", report)
            self.assertTrue((root / "results" / "paired_gap_summary.csv").exists())
            self.assertTrue((root / "figs" / "heldout_context_validation.png").exists())


def math_log2(value: float) -> float:
    import math

    return math.log2(value)


if __name__ == "__main__":
    unittest.main()
