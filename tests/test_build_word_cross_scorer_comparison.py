from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path

import pandas as pd

from src.build_word_cross_scorer_comparison import compare


class WordCrossScorerComparisonTests(unittest.TestCase):
    def test_comparison_forbids_raw_magnitude_pooling(self) -> None:
        source = (Path(__file__).parents[1] / "src" / "build_word_cross_scorer_comparison.py").read_text()
        self.assertIn("Raw coefficient magnitudes are not", source)
        self.assertIn("child-level sign agreement", source)
        self.assertIn("PBM is one discovery sample", source)

    def test_two_scorer_synthetic_comparison_writes_audited_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scorers = []
            for index, label in enumerate(("Mistral", "Qwen")):
                analysis = root / label
                (analysis / "models").mkdir(parents=True)
                (analysis / "features").mkdir()
                pd.DataFrame(
                    [
                        {
                            "model_id": "same_word_k3_primary",
                            "term": "age_c",
                            "estimate": -.1 - index * .01,
                            "ci_low": -.2,
                            "ci_high": -.01,
                            "bootstrap_ci_low": -.22,
                            "bootstrap_ci_high": -.02,
                        },
                        {
                            "model_id": "context_gain_k3_primary",
                            "term": "age_c",
                            "estimate": -.03 if index == 0 else .01,
                            "ci_low": -.05 if index == 0 else -.02,
                            "ci_high": -.01 if index == 0 else .04,
                            "bootstrap_ci_low": -.06 if index == 0 else -.03,
                            "bootstrap_ci_high": -.01 if index == 0 else .05,
                        },
                    ]
                ).to_csv(analysis / "models" / "coefficients.csv", index=False)
                pd.DataFrame([
                    {"level": "child", "unit": "Brown/Adam", "outcome": "word_sum_bits_k3", "age_slope": -.1},
                    {"level": "child", "unit": "Brown/Eve", "outcome": "word_sum_bits_k3", "age_slope": .1 if index else -.1},
                ]).to_csv(analysis / "models" / "unit_slopes.csv", index=False)
                (analysis / "features" / "feature_manifest.json").write_text(json.dumps({"status": "PASS", "rows": 20, "lexical_eligible_rows": 18, "primary_rows": 15, "children": 2, "corpora": 1, "primary_occurrence_identity_sha256": "same-identities"}))
                (analysis / "models" / "model_manifest.json").write_text(
                    json.dumps({"status": "PASS", "registry_sha256": "same-registry"})
                )
                (analysis / "audit_all.json").write_text(
                    json.dumps({"status": "PASS"})
                )
                scorers.append((label, analysis))
            report = compare(scorers, root / "out", root / "figs", root / "report.md", root / "report.html")
            self.assertEqual(report["status"], "PASS")
            self.assertTrue((root / "out" / "child_slope_sign_concordance.csv").is_file())
            question_summary = pd.read_csv(
                root / "out" / "scientific_question_summary.csv"
            ).set_index("question_id")
            self.assertEqual(
                question_summary.loc["same_word_k3_age", "replication_status"],
                "direction_and_interval_robust",
            )
            self.assertEqual(
                question_summary.loc["context_gain_age", "replication_status"],
                "scorer_dependent",
            )
            self.assertTrue((root / "report.html").is_file())
            self.assertIn(
                "Question-by-question evidence",
                (root / "report.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(report["registry_sha256"], "same-registry")

    def test_mismatched_registry_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scorers = []
            for label, registry in (("Mistral", "a"), ("Qwen", "b")):
                analysis = root / label
                (analysis / "models").mkdir(parents=True)
                (analysis / "features").mkdir()
                pd.DataFrame([{"model_id": "same_word_k3_primary", "term": "age_c", "estimate": -0.1, "ci_low": -0.2, "ci_high": -0.01}]).to_csv(analysis / "models" / "coefficients.csv", index=False)
                pd.DataFrame([{"level": "child", "unit": "Brown/Adam", "outcome": "word_sum_bits_k3", "age_slope": -0.1}]).to_csv(analysis / "models" / "unit_slopes.csv", index=False)
                (analysis / "features" / "feature_manifest.json").write_text(json.dumps({"status": "PASS", "rows": 1, "lexical_eligible_rows": 1, "primary_rows": 1, "children": 1, "corpora": 1, "primary_occurrence_identity_sha256": "same-identities"}))
                (analysis / "models" / "model_manifest.json").write_text(json.dumps({"status": "PASS", "registry_sha256": registry}))
                (analysis / "audit_all.json").write_text(json.dumps({"status": "PASS"}))
                scorers.append((label, analysis))
            with self.assertRaisesRegex(RuntimeError, "registry hash"):
                compare(scorers, root / "out", root / "figs", root / "report.md", root / "report.html")


if __name__ == "__main__":
    unittest.main()
