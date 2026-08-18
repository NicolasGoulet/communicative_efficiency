"""Contract tests for the frozen August supervisor-report evidence map."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "august_supervisor_report_v1.json"
SPEC_PATH = ROOT / "docs" / "august_supervisor_report_spec.md"


class AugustSupervisorReportSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.spec_text = SPEC_PATH.read_text(encoding="utf-8")

    def test_top_level_schema_and_frozen_source(self) -> None:
        self.assertEqual(self.config["schema_version"], "1.0.0")
        self.assertEqual(
            self.config["source_commit"],
            "ced13d9d81de7469a35080ed78daac2bd5d24cb6",
        )
        self.assertEqual(
            self.config["allowed_evidence_statuses"],
            ["SUPPORTED", "QUALIFIED", "CONTRARY", "DESCRIPTIVE", "PENDING"],
        )
        self.assertEqual(
            self.config["allowed_claim_roles"],
            ["PROMOTED", "SUPPORTING", "EXCLUDED", "PENDING"],
        )
        self.assertEqual(
            self.config["allowed_figure_eligibility"],
            ["PRIMARY", "SUPPORTING", "NONE"],
        )
        self.assertGreaterEqual(len(self.config["claims"]), 20)

    def test_page_contract_is_complete_and_links_are_frozen(self) -> None:
        page_contract = self.config["page_contract"]
        self.assertEqual(
            page_contract["outputs"],
            [
                "docs/august_supervisor_index.html",
                "docs/august_supervisor_report.md",
                "docs/august_supervisor_report.html",
            ],
        )
        expected_links = {
            "direct_results_explorer": "docs/direct_surprisal_results_explorer.html",
            "word_cross_scorer_comparison": "docs/word_cross_scorer_comparison.html",
            "hall_snapshot": "docs/hall_snapshot_mistral_analysis.html",
            "corrected_bayes": "docs/corrected_pbm_bayes_report.html",
            "sustained_onset": "docs/direct_surprisal_onset_confirmation.html",
            "child_trajectories": "docs/paired_tinydialogues_mistral_child_trajectories.html",
            "formal_definitions": "docs/july_meeting_definitions.html",
            "technical_analysis_inventory": "docs/complete_analysis_machine_index.html",
        }
        self.assertEqual(page_contract["required_links"], expected_links)
        self.assertTrue(page_contract["render_from_frozen_artifacts_only"])
        self.assertFalse(page_contract["allow_model_fitting"])
        self.assertFalse(page_contract["allow_plot_generation"])

    def test_claim_schema_is_complete_and_ids_are_stable(self) -> None:
        statuses = set(self.config["allowed_evidence_statuses"])
        roles = set(self.config["allowed_claim_roles"])
        figure_values = set(self.config["allowed_figure_eligibility"])
        required_claim_keys = {
            "claim_id",
            "claim_role",
            "scientific_question",
            "sample",
            "scorer",
            "estimand",
            "numerical_result",
            "evidence_status",
            "source",
            "required_interpretation",
            "required_limitation",
            "destination_section",
            "figure_eligibility",
        }
        ids: list[str] = []
        seen_statuses: set[str] = set()
        seen_roles: set[str] = set()

        for claim in self.config["claims"]:
            self.assertTrue(required_claim_keys.issubset(claim), claim.get("claim_id"))
            claim_id = claim["claim_id"]
            ids.append(claim_id)
            self.assertRegex(claim_id, r"^[A-Z][A-Z0-9_]+$")
            self.assertIn(claim["claim_role"], roles)
            self.assertIn(claim["evidence_status"], statuses)
            self.assertIn(claim["figure_eligibility"], figure_values)
            seen_statuses.add(claim["evidence_status"])
            seen_roles.add(claim["claim_role"])

            self.assertTrue(
                {"role", "scope", "rows", "children", "sessions", "corpora"}.issubset(
                    claim["sample"]
                ),
                claim_id,
            )
            self.assertTrue(
                {"model", "tokenizer", "comparability_rule"}.issubset(claim["scorer"]),
                claim_id,
            )
            self.assertTrue(
                {
                    "name",
                    "outcome",
                    "formula_or_contrast",
                    "controls",
                    "direction_convention",
                }.issubset(claim["estimand"]),
                claim_id,
            )
            self.assertTrue(
                {"canonical_artifact", "source_sha256", "required_marker"}.issubset(
                    claim["source"]
                ),
                claim_id,
            )
            self.assertRegex(claim["source"]["source_sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(
                {"path", "expectation", "observed", "satisfied"}.issubset(
                    claim["source"]["required_marker"]
                ),
                claim_id,
            )
            if claim["numerical_result"] is not None:
                self.assertTrue(
                    {"estimate", "unit", "interval", "uncertainty_method"}.issubset(
                        claim["numerical_result"]
                    ),
                    claim_id,
                )
                interval = claim["numerical_result"]["interval"]
                self.assertTrue(
                    interval is None
                    or {"level", "low", "high", "type"}.issubset(interval),
                    claim_id,
                )

        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(seen_statuses, statuses)
        self.assertEqual(seen_roles, roles)

    def test_required_scientific_statuses_are_locked(self) -> None:
        claims = {claim["claim_id"]: claim for claim in self.config["claims"]}
        expected = {
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY": "QUALIFIED",
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP": "QUALIFIED",
            "DIRECT_PBM_MISTRAL_CONTEXT_GAIN": "CONTRARY",
            "DIRECT_PBM_TINY_CONTEXT_GAIN": "CONTRARY",
            "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN": "CONTRARY",
            "ONSET_PBM_SUSTAINED": "QUALIFIED",
            "ONSET_NONPBM_SUSTAINED": "QUALIFIED",
            "HALL_RACE_CLASS_INTERACTION": "DESCRIPTIVE",
            "WORD_NONPBM58_CONFIRMATION": "PENDING",
            "LISTENER_UTILITY_OUTCOME": "PENDING",
            "CONVERSATIONAL_MANUAL_VALIDATION": "PENDING",
            "DECOUPLED_RESPONSE_CALIBRATION": "PENDING",
            "ALTERNATIVE_EFFORT_ONSET": "PENDING",
        }
        self.assertTrue(set(expected).issubset(claims))
        for claim_id, status in expected.items():
            self.assertEqual(claims[claim_id]["evidence_status"], status)

        self.assertEqual(
            claims["DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY"]["numerical_result"][
                "interval"
            ]["high"],
            0.007303,
        )
        self.assertIn(
            "sensitivity",
            claims["DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP"][
                "required_interpretation"
            ].lower(),
        )
        self.assertIn(
            "not replace",
            claims["DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP"][
                "required_limitation"
            ].lower(),
        )
        self.assertIn(
            "individual profiles do not establish one universal developmental law",
            claims["DIRECT_PBM_MISTRAL_CONTEXTUAL"]["required_limitation"].lower(),
        )
        self.assertIn(
            "individual profiles do not establish one universal developmental law",
            self.spec_text.lower(),
        )

    def test_all_required_locked_readings_are_present(self) -> None:
        required = {
            "NONPBM_CONTEXTUAL_QUALIFIED",
            "NONPBM_BOOTSTRAP_SENSITIVITY",
            "CONTEXT_GAIN_CONTRARY",
            "PBM_CROSS_SCORER_ROBUSTNESS",
            "TOKENIZER_MAGNITUDES_NOT_POOLED",
            "SUSTAINED_ONSET_NOT_ESTABLISHED",
            "EXACT_STRING_ENTROPY_LIMIT",
            "GENERATED_CANDIDATES_MEANING_LIMIT",
            "BAYES_FINITE_CANDIDATE_SET",
            "HALL_SEPARATE_DESCRIPTIVE",
            "WORD_NONPBM58_PENDING",
            "LISTENER_UTILITY_PENDING",
            "CONVERSATIONAL_VALIDATION_PENDING",
            "DECOUPLED_RESPONSE_CALIBRATION_PENDING",
            "ALTERNATIVE_EFFORT_ONSET_PENDING",
        }
        readings = {item["reading_id"]: item for item in self.config["locked_readings"]}
        self.assertEqual(set(readings), required)
        for reading_id, reading in readings.items():
            self.assertTrue(reading["text"].strip(), reading_id)
            self.assertTrue(reading["claim_ids"], reading_id)

    def test_blockers_are_explicit_and_unsatisfied(self) -> None:
        expected_blockers = {
            "WORD_NONPBM58_CONFIRMATION",
            "LISTENER_UTILITY_OUTCOME",
            "CONVERSATIONAL_MANUAL_VALIDATION",
            "DECOUPLED_RESPONSE_CALIBRATION",
            "ALTERNATIVE_EFFORT_ONSET",
        }
        blockers = {item["claim_id"]: item for item in self.config["blockers"]}
        self.assertEqual(set(blockers), expected_blockers)
        for claim_id, blocker in blockers.items():
            self.assertEqual(blocker["status"], "BLOCKED")
            self.assertTrue(blocker["reason"].strip(), claim_id)
            self.assertTrue(blocker["required_resolution"].strip(), claim_id)

    def test_human_spec_covers_every_claim_and_reading(self) -> None:
        self.assertIn("# August supervisor report v1: frozen evidence contract", self.spec_text)
        for status in self.config["allowed_evidence_statuses"]:
            self.assertRegex(self.spec_text, rf"\b{re.escape(status)}\b")
        for claim in self.config["claims"]:
            self.assertIn(f"`{claim['claim_id']}`", self.spec_text)
        for reading in self.config["locked_readings"]:
            self.assertIn(f"`{reading['reading_id']}`", self.spec_text)


if __name__ == "__main__":
    unittest.main()
