import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from build_utterance_informativity_analysis import (  # noqa: E402
    AGE_BINS,
    build_recurring_type_table,
    canonicalize_role_frame,
    fit_frequency_informativity_coupling,
    fit_standardized_outcome,
    run_audit_stage,
    run_models_stage,
    run_report_stage,
)


class UtteranceInformativityAnalysisTests(unittest.TestCase):
    def test_canonicalizes_child_rows_and_requires_real_k3_context(self) -> None:
        frame = pd.DataFrame(
            {
                "dataset": ["Brown", "Wells"],
                "child_key": ["Brown/Adam", "Wells/Abigail"],
                "sample_group": ["pbm_discovery", "non_pbm_confirmation"],
                "session_id": ["a", "b"],
                "age_months": [24.0, 36.0],
                "age_bin": ["024-029", "036-041"],
                "utterance_id": ["u1", "u2"],
                "real_target_text": ["I want it.", "missing context"],
                "real_target_text_sha256": ["h1", "h2"],
                "real_nb_words": [3, 2],
                "real_k0_sum_bits": [30.0, 20.0],
                "real_k0_mean_bits_per_token": [6.0, 5.0],
                "real_k0_n_eval_tokens": [5, 4],
                "real_k3_sum_bits": [18.0, 15.0],
                "real_k3_mean_bits_per_token": [3.6, 3.75],
                "real_k3_n_eval_tokens": [5, 4],
                "real_context_gain_k3": [12.0, 5.0],
                "context_available_k3": [1, 0],
            }
        )

        result = canonicalize_role_frame(frame, "child")

        self.assertEqual(len(result), 1)
        row = result.iloc[0]
        self.assertEqual(row["role"], "child")
        self.assertEqual(row["words_top12"], 3)
        self.assertAlmostEqual(row["context_gain_density"], 2.4)
        self.assertEqual(row["analysis_scope"], "pbm_discovery")

    def test_recurring_type_table_enforces_cross_child_and_corpus_support(self) -> None:
        rows = []
        for index in range(12):
            rows.append(
                {
                    "role": "child",
                    "target_hash": "common",
                    "target_text": "I don't know.",
                    "child_key": f"child-{index % 6}",
                    "dataset": f"corpus-{index % 3}",
                    "age_bin": AGE_BINS[index % len(AGE_BINS)],
                    "words": 3,
                    "k0_total": 30.0,
                    "k3_total": 18.0 + index / 10,
                    "context_gain_total": 12.0 - index / 10,
                    "k0_density": 6.0,
                    "k3_density": 3.6 + index / 100,
                    "context_gain_density": 2.4 - index / 100,
                }
            )
        rows.extend(
            {
                "role": "child",
                "target_hash": "single-child",
                "target_text": "yes.",
                "child_key": "only-one",
                "dataset": "corpus-0",
                "age_bin": "024-029",
                "words": 1,
                "k0_total": 10.0,
                "k3_total": 5.0,
                "context_gain_total": 5.0,
                "k0_density": 5.0,
                "k3_density": 2.5,
                "context_gain_density": 2.5,
            }
            for _ in range(12)
        )
        result = build_recurring_type_table(
            pd.DataFrame(rows), min_occurrences=10, min_children=5, min_corpora=3
        )

        self.assertEqual(result["target_hash"].tolist(), ["common"])
        self.assertEqual(int(result.iloc[0]["occurrences"]), 12)
        self.assertTrue(math.isfinite(result.iloc[0]["empirical_frequency_bits"]))

    @staticmethod
    def synthetic_cells() -> pd.DataFrame:
        rows = []
        children = [f"child-{index}" for index in range(8)]
        for child_index, child in enumerate(children):
            scope = "pbm_discovery" if child_index < 4 else "non_pbm_confirmation"
            for age_index, age_bin in enumerate(AGE_BINS):
                for words in (1, 2, 4):
                    for k0_density in (3.0, 6.0, 9.0):
                        age = 20.0 + 6.0 * age_index
                        k3_density = 1.0 + 0.7 * k0_density + 0.03 * age_index * k0_density
                        rows.append(
                            {
                                "role": "child",
                                "dataset": "Brown" if scope == "pbm_discovery" else "Wells",
                                "child_key": child,
                                "analysis_scope": scope,
                                "age_bin": age_bin,
                                "age_mean": age,
                                "words_top12": words,
                                "n": 10,
                                "k0_total_mean": k0_density * words,
                                "k3_total_mean": k3_density * words,
                                "context_gain_total_mean": (k0_density - k3_density) * words,
                                "k0_density_mean": k0_density,
                                "k3_density_mean": k3_density,
                                "context_gain_density_mean": k0_density - k3_density,
                            }
                        )
        return pd.DataFrame(rows)

    def test_standardization_returns_all_age_bins_and_finite_uncertainty(self) -> None:
        cells = self.synthetic_cells()
        registry, estimates = fit_standardized_outcome(
            cells,
            role="child",
            scope="all79_descriptive",
            outcome="k3_total_mean",
        )

        self.assertEqual(registry["status"], "PASS")
        self.assertEqual(estimates["age_bin"].tolist(), AGE_BINS)
        self.assertTrue(np.isfinite(estimates[["estimate", "std_error", "ci_low", "ci_high"]]).all().all())

    def test_frequency_informativity_model_recovers_positive_age_coupling(self) -> None:
        cells = self.synthetic_cells()
        registry, coefficients, contrasts = fit_frequency_informativity_coupling(
            cells,
            role="child",
            scope="all79_descriptive",
        )

        interaction = coefficients.loc[
            coefficients["term"].eq("age_c:k0_density_mean"), "estimate"
        ].iloc[0]
        self.assertEqual(registry["status"], "PASS")
        self.assertGreater(interaction, 0)
        self.assertEqual(contrasts["age_bin"].tolist(), AGE_BINS)

    def test_saved_cell_pipeline_writes_audited_completion_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "results"
            datasets = output / "datasets"
            datasets.mkdir(parents=True)
            cells = self.synthetic_cells()
            caretaker = cells.copy()
            caretaker["role"] = "caretaker"
            pd.concat([cells, caretaker], ignore_index=True).to_csv(
                datasets / "model_cells.csv.gz", index=False
            )
            recurring = pd.DataFrame(
                {
                    "role": ["child", "caretaker"],
                    "target_hash": ["child-common", "caretaker-common"],
                    "target_text": ["I don't know.", "do you know?"],
                    "occurrences": [120, 140],
                    "children": [12, 12],
                    "corpora": [3, 3],
                    "age_bins": [8, 8],
                    "word_count": [3, 3],
                    "mean_k0_total_bits": [30.0, 31.0],
                    "mean_k3_total_bits": [18.0, 19.0],
                    "mean_context_support_bits": [12.0, 12.0],
                    "mean_k0_bits_per_token": [6.0, 6.2],
                    "mean_k3_bits_per_token": [3.6, 3.8],
                    "mean_context_support_bits_per_token": [2.4, 2.4],
                    "reference_role_rows": [1000, 1000],
                    "empirical_frequency_bits": [3.0, 2.8],
                    "definition": ["fixture", "fixture"],
                }
            )
            recurring.to_csv(datasets / "recurrent_utterance_types.csv.gz", index=False)
            (datasets / "dataset_manifest.json").write_text(
                '{"stage":"datasets","audit":{"status":"PASS","roles":["child","caretaker"]}}\n',
                encoding="utf-8",
            )
            (datasets / "dataset_audit.json").write_text(
                '{"status":"PASS","role_audits":['
                '{"role":"child","eligible_rows":1000,"density_pair_rows":990,"density_pair_excluded":10},'
                '{"role":"caretaker","eligible_rows":1000,"density_pair_rows":995,"density_pair_excluded":5}'
                ']}\n',
                encoding="utf-8",
            )
            route1 = root / "route1.csv"
            pd.DataFrame(
                {
                    "scope": ["all79_descriptive"] * 6,
                    "model_id": [
                        "P1_k3_contextual",
                        "P2_k0_unconditional",
                        "P3_k3_context_gain",
                        "C1_caretaker_k3_contextual",
                        "C2_caretaker_k0_unconditional",
                        "C3_caretaker_k3_context_gain",
                    ],
                    "fit_status": ["PASS"] * 6,
                }
            ).to_csv(route1, index=False)
            route2 = root / "route2.csv"
            pd.DataFrame(
                {
                    "analysis_scope": ["all79"] * 4,
                    "model_id": [
                        "m1_length_primary",
                        "m2_length_qwen_reference",
                        "m4_effort_percentile",
                        "m5_exact_length_k3_gap",
                    ],
                    "status": ["PASS"] * 4,
                }
            ).to_csv(route2, index=False)
            report_md = root / "report.md"
            report_html = root / "report.html"

            run_models_stage(output, route1, route2)
            run_report_stage(output, report_md, report_html)
            audit = run_audit_stage(output, report_md, report_html)

            self.assertEqual(audit["status"], "PASS")
            self.assertTrue((output / "UTTERANCE_INFORMATIVITY_COMPLETE_AND_AUDITED").exists())
            self.assertIn("Route 1", report_md.read_text(encoding="utf-8"))
            self.assertIn("Route 2", report_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
