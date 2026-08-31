from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_bidirectional_dyadic_efficiency_20260829 import (  # noqa: E402
    DEFAULT_CONTRACT,
    _joined_sql,
    estimate_dyadic_child_coefficients,
    validate_contract,
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class BidirectionalDyadicEfficiencyTests(unittest.TestCase):
    def test_contract_is_bounded_two_sided_and_pbm_is_not_a_prior(self) -> None:
        contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        validate_contract(contract)
        self.assertEqual(len(contract["estimands"]), 3)
        self.assertTrue(all(row["direction"] == "two_sided" for row in contract["estimands"]))
        self.assertIn("PBM estimates are not used as priors", contract["bayesian"]["prior_source"])
        self.assertLessEqual(contract["bayesian"]["maximum_total_cpu_hours"], 2)

        changed = copy.deepcopy(contract)
        changed["estimands"][2]["direction"] = "positive"
        with self.assertRaisesRegex(ValueError, "two-sided"):
            validate_contract(changed)

        validate_contract(contract, require_frozen=True)
        draft = copy.deepcopy(contract)
        draft["status"] = "draft_support_blind"
        with self.assertRaisesRegex(ValueError, "frozen_pre_fit"):
            validate_contract(draft, require_frozen=True)

    def test_exact_three_turn_join_and_within_session_decomposition(self) -> None:
        handoff_rows = []
        flag_rows = []
        child_rows = []
        adult_rows = []
        for index, (a0, child, a1, a0_k3, c_k3) in enumerate(
            [
                ("do you want milk?", "want milk.", "here it is.", 20.0, 12.0),
                ("what is that?", "a dog.", "yes a dog.", 30.0, 8.0),
            ],
            start=1,
        ):
            c_line = index * 10
            pair = f"pair-{index}"
            common = {
                "dataset": "Brown",
                "child_id": "Adam",
                "child_key": "Brown/Adam",
                "session_id": "1",
                "file": "Adam/test.cha",
            }
            handoff_rows.append(
                {
                    **common,
                    "response_pair_id": pair,
                    "sample_group": "pbm_discovery",
                    "age_months": "36",
                    "age_bin": "036-041",
                    "line_no": str(c_line),
                    "next_caregiver_line_no": str(c_line + 1),
                    "child_text": child,
                    "child_text_sha256": digest(child),
                    "target_text": a1,
                    "target_text_sha256": digest(a1),
                    "child_word_count": "2",
                    "response_word_count": "3",
                    "primary_eligible": "1",
                    "sensitivity_eligible": "1",
                    "previous_caretaker_question_type": "polar_question",
                    "child_question_type": "not_question",
                    "next_caregiver_question_type": "not_question",
                    "exact_imitation_candidate": "0",
                    "contained_imitation_candidate": "0",
                    "child_backchannel_candidate": "0",
                    "session_reading_candidate": "0",
                    "session_routine_candidate": "0",
                    "repair_sequence_candidate": "0",
                    "next_caregiver_clarification_candidate": "0",
                    "next_caregiver_acknowledgement_candidate": "1",
                }
            )
            flag_rows.append(
                {
                    "dataset": "Brown",
                    "child_id": "Adam",
                    "file": "Adam/test.cha",
                    "line_no": str(c_line),
                    "previous_main_line_no": str(c_line - 1),
                    "previous_main_speaker": "MOT",
                    "next_main_speaker": "MOT",
                    "previous_main_utterance_clean": a0,
                }
            )
            child_rows.append(
                {
                    **common,
                    "line_no": str(c_line),
                    "real_target_text_sha256": digest(child),
                    "c_score_words": 2,
                    "c_k0_bits": c_k3 + 4,
                    "c_k3_bits": c_k3,
                    "c_context_support_bits": 4.0,
                    "c_context_available_k3": 1,
                    "c_k0_tokens": 3,
                    "c_k3_tokens": 3,
                }
            )
            for line, text, score_words, k3 in (
                (c_line - 1, a0, 4, a0_k3),
                (c_line + 1, a1, 3, 15.0),
            ):
                adult_rows.append(
                    {
                        **common,
                        "line_no": str(line),
                        "speaker": "MOT",
                        "target_text": text,
                        "target_text_sha256": digest(text),
                        "score_words": score_words,
                        "k0_bits": k3 + 5,
                        "k3_bits": k3,
                        "context_support_bits": 5.0,
                        "context_available_k3": 1,
                        "k0_tokens": score_words + 1,
                        "k3_tokens": score_words + 1,
                    }
                )

        connection = duckdb.connect()
        connection.register("handoff", pd.DataFrame(handoff_rows))
        connection.register("flags", pd.DataFrame(flag_rows))
        connection.register("child_scores", pd.DataFrame(child_rows))
        connection.register("caregiver_scores", pd.DataFrame(adult_rows))
        joined = connection.execute(_joined_sql()).fetchdf()
        connection.close()
        self.assertEqual(len(joined), 2)
        self.assertTrue((joined[["a0_hash_matches", "c_hash_matches", "a1_hash_matches"]] == 1).all().all())
        self.assertTrue((joined[["c_words_match", "a1_words_match"]] == 1).all().all())
        self.assertTrue((joined.a1_words == joined.a1_handoff_words).all())
        self.assertAlmostEqual(joined.a0_k3_within.mean(), 0.0)
        self.assertAlmostEqual(joined.c_k3_within.mean(), 0.0)
        self.assertEqual(set(joined.a0_speaker), {"MOT"})

    def test_joint_child_summary_recovers_three_standardized_slopes(self) -> None:
        rng = __import__("numpy").random.default_rng(17)
        rows = []
        for session in range(8):
            age = (session - 4) / 2
            for row in range(50):
                a0 = rng.normal()
                child = rng.normal()
                logc = rng.normal()
                loga0 = rng.normal()
                rows.append({
                    "child_key": "Brown/Test",
                    "dataset": "Brown",
                    "child_session_key": f"Brown/Test/{session}",
                    "age_z": age,
                    "a0_k3_within_z": a0,
                    "c_k3_within_z": child,
                    "c_k3_z": 0.20 * a0 + 0.1 * logc + rng.normal(0, .2),
                    "logc_z": -0.12 * a0 + rng.normal(0, .2),
                    "loga1_z": -0.18 * child + 0.1 * a0 + rng.normal(0, .2),
                    "log1p_c_words": logc,
                    "log1p_a0_words": loga0,
                    "a0_k3_child_mean_z": 0.1,
                    "c_k3_child_mean_z": -0.1,
                })
        estimate, covariance, audit = estimate_dyadic_child_coefficients(pd.DataFrame(rows))
        self.assertAlmostEqual(estimate[0], 0.20, delta=0.05)
        self.assertAlmostEqual(estimate[1], -0.12, delta=0.05)
        self.assertAlmostEqual(estimate[2], -0.18, delta=0.05)
        self.assertTrue((__import__("numpy").linalg.eigvalsh(covariance) > 0).all())
        self.assertTrue(audit["shared_session_clustered_covariance"])


if __name__ == "__main__":
    unittest.main()
