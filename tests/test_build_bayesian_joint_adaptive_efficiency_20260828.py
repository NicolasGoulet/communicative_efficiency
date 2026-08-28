import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from build_bayesian_joint_adaptive_efficiency_20260828 import (  # noqa: E402
    DEFAULT_CONTRACT,
    audit_fit_diagnostics,
    estimate_child_coefficients,
    render_scientific_report,
    validate_contract,
)


def synthetic_child(*, sessions: int = 8, rows_per_session: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(71)
    rows = []
    for session in range(sessions):
        age_z = -1.75 + 0.5 * session
        for row in range(rows_per_session):
            entropy_z = rng.normal()
            context_z = rng.normal()
            word_count = str(1 + row % 4)
            k3 = 25.0 - 0.6 * age_z + 1.2 * int(word_count) + rng.normal(0, 0.8)
            log_effort = (
                1.0
                + 0.04 * age_z
                + 0.08 * entropy_z
                - 0.025 * age_z * entropy_z
                + 0.03 * context_z
                + rng.normal(0, 0.08)
            )
            child_words = max(1, int(round(np.expm1(log_effort))))
            rows.append(
                {
                    "utterance_id": f"u-{session}-{row}",
                    "child_key": "Brown/Test",
                    "dataset": "Brown",
                    "session_id": session,
                    "age_z": age_z,
                    "word_count_top12": word_count,
                    "k3_bits": k3,
                    "child_words": child_words,
                    "entropy_z": entropy_z,
                    "context_words_z": context_z,
                }
            )
    return pd.DataFrame(rows)


class FocusedBayesianJointTests(unittest.TestCase):
    def test_contract_keeps_corpus_nuisance_and_never_uses_pbm_as_prior(self):
        contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        validate_contract(contract)
        self.assertEqual(contract["joint_model"]["family"], "trivariate_normal_measurement_error")
        self.assertEqual(contract["eligibility"]["expected_included_children"], 78)
        self.assertIn("PBM estimates are not used as priors", contract["priors"]["source"])
        self.assertNotIn("sample_scopes", contract)

        changed = copy.deepcopy(contract)
        changed["estimands"][1]["direction"] = "negative"
        with self.assertRaisesRegex(ValueError, "H1"):
            validate_contract(changed)

    def test_shared_session_clustered_estimates_recover_three_estimands(self):
        estimate, covariance, audit = estimate_child_coefficients(synthetic_child())
        self.assertEqual(estimate.shape, (3,))
        self.assertEqual(covariance.shape, (3, 3))
        self.assertTrue(np.all(np.linalg.eigvalsh(covariance) > 0))
        self.assertAlmostEqual(estimate[0], -0.6, delta=0.12)
        self.assertGreater(estimate[1], 0.02)
        self.assertLess(estimate[2], -0.005)
        self.assertEqual(audit["clusters"], 8)
        self.assertTrue(audit["shared_cross_equation_covariance"])

    def test_child_estimation_fails_closed_for_too_few_sessions_or_duplicate_rows(self):
        with self.assertRaisesRegex(ValueError, "sessions"):
            estimate_child_coefficients(synthetic_child(sessions=3))
        duplicated = pd.concat([synthetic_child(), synthetic_child().iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            estimate_child_coefficients(duplicated)

    def test_diagnostics_fail_on_divergence_or_missing_influence_corpus(self):
        diagnostics = pd.DataFrame(
            [{
                "fit_id": "regularizing",
                "rhat_max": 1.001,
                "ess_bulk_min": 600,
                "ess_tail_min": 500,
                "divergences": 0,
                "treedepth_saturated": 0,
                "energy_bfmi_min": 0.8,
            }, {
                "fit_id": "wide_sensitivity",
                "rhat_max": 1.002,
                "ess_bulk_min": 550,
                "ess_tail_min": 450,
                "divergences": 0,
                "treedepth_saturated": 0,
                "energy_bfmi_min": 0.7,
            }]
        )
        influence = pd.DataFrame({"omitted_corpus": [f"c{i}" for i in range(13)]})
        audit = audit_fit_diagnostics(diagnostics, influence, expected_corpora=13)
        self.assertEqual(audit["status"], "PASS")

        broken = diagnostics.copy()
        broken.loc[0, "divergences"] = 1
        self.assertEqual(
            audit_fit_diagnostics(broken, influence, expected_corpora=13)["status"],
            "FAIL",
        )
        self.assertEqual(
            audit_fit_diagnostics(diagnostics, influence.iloc[:-1], expected_corpora=13)["status"],
            "FAIL",
        )

    def test_report_renderer_consumes_saved_summaries_without_fitting(self):
        payload = {
            "status": "PASS",
            "children": 78,
            "corpora": 13,
            "hypotheses": [
                {"hypothesis": "H1", "label": "Demand-sensitive effort", "estimate": 0.03, "q025": 0.01, "q975": 0.05, "probability_direction": 0.99, "probability_rope": 0.02},
                {"hypothesis": "H2", "label": "Developmental calibration", "estimate": -0.01, "q025": -0.02, "q975": 0.00, "probability_direction": 0.50, "probability_rope": 0.20},
                {"hypothesis": "H3", "label": "Fixed-effort predictability", "estimate": -0.5, "q025": -0.8, "q975": -0.2, "probability_direction": 0.999, "probability_rope": 0.10},
                {"hypothesis": "H4", "label": "Coordinated development", "estimate": -0.3, "q025": -0.7, "q975": 0.2, "probability_direction": 0.85, "probability_rope": 0.15},
            ],
            "age_contrasts": [],
            "prior_sensitivity": "stable",
            "influence_summary": "stable",
            "runtime_minutes": 2.0,
            "guardrails": ["Not listener utility."],
        }
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "report.md"
            with mock.patch("subprocess.run", side_effect=AssertionError("must not fit")):
                render_scientific_report(payload, target)
            text = target.read_text(encoding="utf-8")
            self.assertIn("H1", text)
            self.assertIn("Not listener utility", text)
            self.assertNotIn("children optimize", text.lower())


if __name__ == "__main__":
    unittest.main()
