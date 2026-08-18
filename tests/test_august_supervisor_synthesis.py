"""Focused tests for deterministic August scientific synthesis."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.august_supervisor.contracts import (
    ContractError,
    read_registry_csv,
    sha256_file,
    verify_stage_manifest,
)
from src.august_supervisor.evidence import (
    extract_datasets,
    load_frozen_configuration,
)
from src.august_supervisor.model_results import (
    _model_variants,
    build_blocker_records,
    build_effect_records,
    extract_model_results,
)
from src.august_supervisor.synthesis import (
    build_synthesis_tables,
    synthesize,
)
from tests.test_august_supervisor_evidence import build_tiny_repository


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "august_supervisor_report_v1.json"


def _frozen_effects_and_blockers():
    config = load_frozen_configuration(CONFIG_PATH)
    hashes = {
        claim["source"]["required_marker"]["path"]: "0" * 64
        for claim in config["claims"]
        if claim["source"]["required_marker"]["path"] is not None
    }
    models_by_claim = {
        claim["claim_id"]: [
            f"MODEL_{claim['claim_id']}" + (f"_{suffix}" if suffix else "")
            for suffix, _, _ in _model_variants(claim)
        ]
        for claim in config["claims"]
        if claim["evidence_status"] != "PENDING"
        and claim["claim_role"] != "EXCLUDED"
    }
    return (
        config,
        build_effect_records(config, hashes, models_by_claim),
        build_blocker_records(config, hashes),
    )


class AugustSupervisorSynthesisTests(unittest.TestCase):
    def test_rule_based_classification_and_claim_links_preserve_frozen_readings(self) -> None:
        config, effects, blockers = _frozen_effects_and_blockers()
        tables = build_synthesis_tables(config, effects, blockers)
        records = [record for table in tables.values() for record in table]
        by_claim = {record["claim_id"]: record for record in records}

        self.assertEqual(
            {name: len(rows) for name, rows in tables.items()},
            {
                "headline_findings": 7,
                "supporting_findings": 16,
                "coverage_and_limitations": 8,
            },
        )
        self.assertEqual(
            set(by_claim), {claim["claim_id"] for claim in config["claims"]}
        )
        self.assertTrue(all(record["claim_id"] for record in records))
        self.assertTrue(all(record["finding"] for record in records))
        self.assertTrue(all(record["limitation"] for record in records))

        expected_statuses = {
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY": "QUALIFIED",
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP": "QUALIFIED",
            "DIRECT_PBM_MISTRAL_CONTEXT_GAIN": "CONTRARY",
            "DIRECT_PBM_TINY_CONTEXT_GAIN": "CONTRARY",
            "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN": "CONTRARY",
            "WORD_CROSS_SCORER_PREDICTABILITY": "SUPPORTED",
            "WORD_CONTEXT_GAIN_SCORER_DEPENDENT": "QUALIFIED",
            "ROUTE2_AGE_ENTROPY_INTERACTION": "CONTRARY",
            "RESPONSE_ENTROPY_SEMANTIC_CLAIM": "QUALIFIED",
            "ONSET_PBM_SUSTAINED": "QUALIFIED",
            "ONSET_NONPBM_SUSTAINED": "QUALIFIED",
            "BAYES_REAL_CANDIDATE_SET_PROBABILITY": "SUPPORTED",
            "HALL_RACE_CLASS_INTERACTION": "DESCRIPTIVE",
            "WORD_NONPBM58_CONFIRMATION": "PENDING",
            "LISTENER_UTILITY_OUTCOME": "PENDING",
            "CONVERSATIONAL_MANUAL_VALIDATION": "PENDING",
            "DECOUPLED_RESPONSE_CALIBRATION": "PENDING",
            "ALTERNATIVE_EFFORT_ONSET": "PENDING",
        }
        for claim_id, status in expected_statuses.items():
            with self.subTest(claim_id=claim_id):
                self.assertEqual(by_claim[claim_id]["classification"], status)

        context_gain = by_claim["DIRECT_PBM_MISTRAL_CONTEXT_GAIN"]
        self.assertEqual(context_gain["evidence_kind"], "EFFECT")
        self.assertEqual(
            context_gain["evidence_id"], "EFFECT_DIRECT_PBM_MISTRAL_CONTEXT_GAIN"
        )
        pending = by_claim["WORD_NONPBM58_CONFIRMATION"]
        self.assertEqual(pending["evidence_kind"], "BLOCKER")
        self.assertEqual(
            pending["evidence_id"], "BLOCKER_WORD_NONPBM58_CONFIRMATION"
        )

        locked_phrases = {
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY": (
                "not confirmed",
                "primary interval crosses zero",
            ),
            "DIRECT_PBM_MISTRAL_CONTEXT_GAIN": (
                "contrary",
                "context gain remains distinct",
            ),
            "WORD_CROSS_SCORER_PREDICTABILITY": (
                "all three scorer-specific fits",
                "not confirmation in the remaining 58 children",
            ),
            "RESPONSE_ENTROPY_SEMANTIC_CLAIM": (
                "exact-string response entropy",
                "not semantic uncertainty",
            ),
            "ONSET_NONPBM_SUSTAINED": (
                "not established",
                "simultaneous sustained rule",
            ),
            "BAYES_REAL_CANDIDATE_SET_PROBABILITY": (
                "within the supplied matched candidate set",
                "not a posterior over every possible utterance",
            ),
            "HALL_RACE_CLASS_INTERACTION": (
                "historical descriptive",
                "not a causal ses effect",
            ),
            "DECOUPLED_RESPONSE_CALIBRATION": (
                "measurement-limited",
                "as semantic or generator-independent",
            ),
        }
        for claim_id, (finding_phrase, limitation_phrase) in locked_phrases.items():
            with self.subTest(claim_id=claim_id):
                self.assertIn(finding_phrase, by_claim[claim_id]["finding"].lower())
                self.assertIn(
                    limitation_phrase, by_claim[claim_id]["limitation"].lower()
                )

        locked_claim_ids = {
            claim_id
            for reading in config["locked_readings"]
            for claim_id in reading["claim_ids"]
        }
        self.assertLessEqual(locked_claim_ids, set(by_claim))

    def test_classification_drift_from_frozen_configuration_fails_closed(self) -> None:
        config, effects, blockers = _frozen_effects_and_blockers()
        changed = copy.deepcopy(effects)
        record = next(
            item
            for item in changed
            if item["claim_id"] == "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY"
        )
        record["evidence_status"] = "SUPPORTED"
        with self.assertRaisesRegex(ContractError, "classification drift"):
            build_synthesis_tables(config, changed, blockers)

    def test_stage_outputs_are_deterministic_claim_complete_and_manifested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = build_tiny_repository(root)
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["page_contract"] = {
                "outputs": [
                    "docs/august_supervisor_index.html",
                    "docs/august_supervisor_report.md",
                    "docs/august_supervisor_report.html",
                ],
                "section_order": ["Fixture section", "Pending evidence and blockers"],
                "required_links": {
                    "fixture_resource": "docs/fixture_resource.html"
                },
                "render_from_frozen_artifacts_only": True,
                "allow_model_fitting": False,
                "allow_plot_generation": False,
                "figure_policy": "Fixture policy",
            }
            config_path.write_text(
                json.dumps(config, sort_keys=True) + "\n", encoding="utf-8"
            )
            resource = root / "docs/fixture_resource.html"
            resource.parent.mkdir(parents=True)
            resource.write_text("fixture\n", encoding="utf-8")
            output_dir = root / "results/august_supervisor_report"
            extract_datasets(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )
            extract_model_results(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )
            upstream_hash = sha256_file(output_dir / "model_results_manifest.json")

            first = synthesize(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )
            names = (
                "headline_findings.csv",
                "supporting_findings.csv",
                "coverage_and_limitations.csv",
                "page_registry.csv",
                "synthesis_manifest.json",
            )
            first_bytes = {name: (output_dir / name).read_bytes() for name in names}
            second = synthesize(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )

            self.assertEqual(first["status"], "PASS")
            self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])
            self.assertEqual(
                first["row_counts"],
                {
                    "headline_findings": 1,
                    "supporting_findings": 1,
                    "coverage_and_limitations": 1,
                    "page_registry": 4,
                },
            )
            for name, payload in first_bytes.items():
                self.assertEqual(payload, (output_dir / name).read_bytes(), name)
            self.assertEqual(
                upstream_hash, sha256_file(output_dir / "model_results_manifest.json")
            )

            headline = read_registry_csv(
                output_dir / "headline_findings.csv", "synthesis"
            )
            supporting = read_registry_csv(
                output_dir / "supporting_findings.csv", "synthesis"
            )
            limitations = read_registry_csv(
                output_dir / "coverage_and_limitations.csv", "synthesis"
            )
            self.assertEqual(
                {row["claim_id"] for row in headline + supporting + limitations},
                {
                    "DIRECT_PBM_MISTRAL_CONTEXTUAL",
                    "WORD_CROSS_SCORER_PREDICTABILITY",
                    "WORD_NONPBM58_CONFIRMATION",
                },
            )
            manifest = verify_stage_manifest(
                output_dir / "synthesis_manifest.json",
                root=root,
                expected_stage="synthesis",
            )
            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(
                manifest["upstream_manifests"][0]["stage_id"], "model-results"
            )

    def test_synthesis_source_does_not_import_fitting_or_plotting_libraries(self) -> None:
        source = (ROOT / "src/august_supervisor/synthesis.py").read_text().lower()
        self.assertNotIn("statsmodels", source)
        self.assertNotIn("matplotlib", source)


if __name__ == "__main__":
    unittest.main()
