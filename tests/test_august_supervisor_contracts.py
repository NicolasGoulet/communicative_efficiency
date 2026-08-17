"""Tests for the reusable August supervisor-report contracts."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.august_supervisor.contracts import (
    CONTRACT_VERSION,
    ContractError,
    SCHEMAS,
    atomic_write_csv,
    atomic_write_json,
    canonical_json_bytes,
    read_json_strict,
    read_registry_csv,
    resolve_claim,
    sha256_bytes,
    sha256_file,
    validate_records,
    validate_registry_bundle,
    verify_evidence_sources,
    verify_stage_manifest,
    write_stage_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "august_supervisor"


class AugustSupervisorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_bundle = read_json_strict(FIXTURE_ROOT / "registry_bundle.json")

    def test_all_eight_record_schemas_are_versioned(self) -> None:
        self.assertEqual(CONTRACT_VERSION, "1.0.0")
        self.assertEqual(
            set(SCHEMAS),
            {
                "sample",
                "effect",
                "model",
                "blocker",
                "synthesis",
                "page",
                "figure",
                "stage_manifest",
            },
        )
        for schema in SCHEMAS.values():
            self.assertEqual(schema.version, CONTRACT_VERSION)
            self.assertIn("schema_version", schema.column_names)

    def test_tiny_fixture_covers_frozen_scopes_statuses_and_scorers(self) -> None:
        bundle = validate_registry_bundle(self.fixture_bundle)
        verify_evidence_sources(bundle, ROOT)

        self.assertTrue(
            {
                "PBM_DISCOVERY",
                "NON_PBM_CONFIRMATION",
                "PBM_SCORER_ROBUSTNESS",
                "HALL_SNAPSHOT",
                "PBM_RESPONSE_SPACE",
                "PENDING_EVIDENCE",
            }.issubset({record["scope"] for record in bundle["sample"]})
        )
        self.assertTrue(
            {"MISTRAL_7B_V03", "TINYDIALOGUES_SMOLLM2_135M", "QWEN3_14B"}.issubset(
                {record["scorer"] for record in bundle["model"]}
            )
        )
        self.assertTrue(
            {"SUPPORTED", "QUALIFIED", "CONTRARY", "DESCRIPTIVE"}.issubset(
                {record["evidence_status"] for record in bundle["effect"]}
            )
        )
        self.assertEqual(bundle["blocker"][0]["blocker_status"], "BLOCKED")

    def test_fixture_values_are_copied_from_the_frozen_claim_registry(self) -> None:
        frozen = read_json_strict(ROOT / "configs" / "august_supervisor_report_v1.json")
        claims = {record["claim_id"]: record for record in frozen["claims"]}
        fixture = read_json_strict(FIXTURE_ROOT / "audited_evidence.json")
        for claim_id, observed in fixture.items():
            with self.subTest(claim_id=claim_id):
                claim = claims[claim_id]
                self.assertEqual(observed["status"], claim["evidence_status"])
                numerical = claim["numerical_result"]
                if numerical is None:
                    self.assertIsNone(observed["estimate"])
                    continue
                self.assertEqual(observed["estimate"], numerical["estimate"])
                self.assertEqual(
                    observed["interval"],
                    [numerical["interval"]["low"], numerical["interval"]["high"]],
                )

    def test_required_columns_types_enums_and_uniqueness_are_strict(self) -> None:
        sample = copy.deepcopy(self.fixture_bundle["sample"][0])

        missing = copy.deepcopy(sample)
        del missing["description"]
        with self.assertRaisesRegex(ContractError, "missing required columns"):
            validate_records("sample", [missing])

        wrong_type = copy.deepcopy(sample)
        wrong_type["rows"] = "444325"
        with self.assertRaisesRegex(ContractError, "rows must be int"):
            validate_records("sample", [wrong_type])

        wrong_enum = copy.deepcopy(sample)
        wrong_enum["scope"] = "ALL_CHILDREN_POOLED"
        with self.assertRaisesRegex(ContractError, "invalid value"):
            validate_records("sample", [wrong_enum])

        duplicate = copy.deepcopy(sample)
        with self.assertRaisesRegex(ContractError, "duplicate unique key"):
            validate_records("sample", [sample, duplicate])

    def test_foreign_keys_and_classifications_cannot_drift(self) -> None:
        bad_foreign_key = copy.deepcopy(self.fixture_bundle)
        bad_foreign_key["effect"][0]["sample_id"] = "SAMPLE_DOES_NOT_EXIST"
        with self.assertRaisesRegex(ContractError, "has no sample.sample_id"):
            validate_registry_bundle(bad_foreign_key)

        changed_classification = copy.deepcopy(self.fixture_bundle)
        changed_classification["synthesis"][0]["classification"] = "QUALIFIED"
        with self.assertRaisesRegex(ContractError, "changes upstream classification"):
            validate_registry_bundle(changed_classification)

        changed_eligibility = copy.deepcopy(self.fixture_bundle)
        changed_eligibility["figure"][0]["eligibility"] = "SUPPORTING"
        with self.assertRaisesRegex(ContractError, "changes figure eligibility"):
            validate_registry_bundle(changed_eligibility)

        missing_synthesis = copy.deepcopy(self.fixture_bundle)
        missing_synthesis["synthesis"].pop()
        with self.assertRaisesRegex(ContractError, "synthesis claim coverage mismatch"):
            validate_registry_bundle(missing_synthesis)

    def test_claim_resolution_fails_when_missing_duplicate_or_ambiguous(self) -> None:
        effects = self.fixture_bundle["effect"]
        blockers = self.fixture_bundle["blocker"]
        resolved = resolve_claim(
            "DIRECT_PBM_MISTRAL_CONTEXTUAL", effects=effects, blockers=blockers
        )
        self.assertEqual(resolved["effect_id"], "EFFECT_PBM_CONTEXTUAL")

        with self.assertRaisesRegex(ContractError, "missing evidence"):
            resolve_claim("MISSING_CLAIM", effects=effects, blockers=blockers)
        with self.assertRaisesRegex(ContractError, "ambiguous evidence"):
            resolve_claim(
                "DIRECT_PBM_MISTRAL_CONTEXTUAL",
                effects=effects + [copy.deepcopy(effects[0])],
                blockers=blockers,
            )

        ambiguous_bundle = copy.deepcopy(self.fixture_bundle)
        ambiguous_bundle["blocker"][0]["claim_id"] = "DIRECT_PBM_MISTRAL_CONTEXTUAL"
        with self.assertRaisesRegex(ContractError, "ambiguous claim IDs"):
            validate_registry_bundle(ambiguous_bundle)

    def test_canonical_json_hash_and_atomic_json_are_deterministic(self) -> None:
        left = {"z": [3, 2, 1], "a": {"second": 2, "first": 1}}
        right = {"a": {"first": 1, "second": 2}, "z": [3, 2, 1]}
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))
        self.assertEqual(
            sha256_bytes(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "first.json"
            second = Path(tmpdir) / "second.json"
            atomic_write_json(first, left)
            atomic_write_json(second, right)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(read_json_strict(first), left)

            duplicate = Path(tmpdir) / "duplicate.json"
            duplicate.write_text('{"claim_id":"A","claim_id":"B"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "duplicate JSON key"):
                read_json_strict(duplicate)

    def test_atomic_csv_is_sorted_and_round_trips_exact_schema(self) -> None:
        expected = validate_records("sample", self.fixture_bundle["sample"])
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "first.csv"
            second = Path(tmpdir) / "second.csv"
            atomic_write_csv(first, "sample", reversed(expected))
            atomic_write_csv(second, "sample", expected)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(read_registry_csv(first, "sample"), expected)

            bad_header = Path(tmpdir) / "bad.csv"
            bad_header.write_text("sample_id,sample_id\nA,B\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "duplicate CSV headers"):
                read_registry_csv(bad_header, "sample")

    def test_changed_or_missing_evidence_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "evidence.json"
            marker = root / "AUDIT_PASS"
            source.write_text('{"status":"PASS"}\n', encoding="utf-8")
            marker.write_text("PASS\n", encoding="utf-8")
            sample = copy.deepcopy(self.fixture_bundle["sample"][0])
            sample.update(
                {
                    "source_artifact": "evidence.json",
                    "source_sha256": sha256_file(source),
                    "audit_marker": "AUDIT_PASS",
                    "audit_marker_sha256": sha256_file(marker),
                }
            )
            verify_evidence_sources({"sample": [sample]}, root)

            source.write_text('{"status":"CHANGED"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "changed source"):
                verify_evidence_sources({"sample": [sample]}, root)
            source.unlink()
            with self.assertRaisesRegex(ContractError, "missing source"):
                verify_evidence_sources({"sample": [sample]}, root)

    def test_manifest_chain_detects_changes_and_requires_upstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifacts = root / "artifacts"
            manifests = root / "manifests"
            artifacts.mkdir()
            dataset = artifacts / "sample_registry.csv"
            dataset.write_text("sample_id\nSAMPLE_PBM\n", encoding="utf-8")
            dataset_manifest = manifests / "datasets.json"
            write_stage_manifest(
                dataset_manifest,
                stage_id="datasets",
                artifact_paths=[dataset],
                upstream_manifest_paths=[],
                root=root,
            )

            models = artifacts / "model_inventory.csv"
            models.write_text("model_id\nMODEL_PBM\n", encoding="utf-8")
            model_manifest = manifests / "model-results.json"
            write_stage_manifest(
                model_manifest,
                stage_id="model-results",
                artifact_paths=[models],
                upstream_manifest_paths=[dataset_manifest],
                root=root,
            )
            verified = verify_stage_manifest(
                model_manifest, root=root, expected_stage="model-results"
            )
            self.assertEqual(verified["upstream_manifests"][0]["stage_id"], "datasets")

            synthesis = artifacts / "synthesis.csv"
            synthesis.write_text("claim_id\nCLAIM\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "requires exactly one"):
                write_stage_manifest(
                    manifests / "synthesis-missing-upstream.json",
                    stage_id="synthesis",
                    artifact_paths=[synthesis],
                    upstream_manifest_paths=[],
                    root=root,
                )

            dataset.write_text("sample_id\nREPLACED\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "changed stage artifact"):
                verify_stage_manifest(model_manifest, root=root)

    def test_later_stage_cannot_claim_or_replace_upstream_products(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact = root / "sample_registry.csv"
            artifact.write_text("sample_id\nSAMPLE_PBM\n", encoding="utf-8")
            upstream = root / "datasets.json"
            write_stage_manifest(
                upstream,
                stage_id="datasets",
                artifact_paths=[artifact],
                upstream_manifest_paths=[],
                root=root,
            )
            with self.assertRaisesRegex(ContractError, "replace upstream product"):
                write_stage_manifest(
                    root / "model-results.json",
                    stage_id="model-results",
                    artifact_paths=[artifact],
                    upstream_manifest_paths=[upstream],
                    root=root,
                )

    def test_stage_manifest_locks_the_frozen_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            configuration = root / "frozen.json"
            artifact = root / "sample_registry.csv"
            configuration.write_text('{"schema_version":"1.0.0"}\n', encoding="utf-8")
            artifact.write_text("sample_id\nSAMPLE_PBM\n", encoding="utf-8")
            manifest = root / "datasets.json"
            write_stage_manifest(
                manifest,
                stage_id="datasets",
                artifact_paths=[artifact],
                upstream_manifest_paths=[],
                root=root,
                configuration_path=configuration,
            )
            verify_stage_manifest(manifest, root=root)
            configuration.write_text('{"schema_version":"CHANGED"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "changed stage configuration"):
                verify_stage_manifest(manifest, root=root)


if __name__ == "__main__":
    unittest.main()
