"""Focused tests for frozen August model-result extraction."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.august_supervisor.contracts import (
    ContractError,
    read_registry_csv,
    verify_stage_manifest,
)
from src.august_supervisor.evidence import extract_datasets, load_frozen_configuration
from src.august_supervisor.model_results import (
    _model_variants,
    build_blocker_records,
    build_effect_records,
    extract_model_results,
)
from tests.test_august_supervisor_evidence import build_tiny_repository


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "august_supervisor_report_v1.json"


class AugustSupervisorModelResultTests(unittest.TestCase):
    def test_model_stage_has_complete_separate_claim_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = build_tiny_repository(root)
            output_dir = root / "results/august_supervisor_report"
            extract_datasets(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )
            first = extract_model_results(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )
            first_bytes = {
                name: (output_dir / name).read_bytes()
                for name in (
                    "effect_registry.csv",
                    "model_inventory.csv",
                    "declared_blockers.csv",
                    "model_results_manifest.json",
                )
            }
            second = extract_model_results(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )

            self.assertEqual(first["status"], "PASS")
            self.assertEqual(
                first["row_counts"],
                {
                    "effect_registry": 2,
                    "model_inventory": 4,
                    "declared_blockers": 1,
                },
            )
            self.assertEqual(
                first["input_hashes_before"], first["input_hashes_after"]
            )
            self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])
            for name, payload in first_bytes.items():
                self.assertEqual(payload, (output_dir / name).read_bytes(), name)

            effects = read_registry_csv(output_dir / "effect_registry.csv", "effect")
            models = read_registry_csv(output_dir / "model_inventory.csv", "model")
            blockers = read_registry_csv(
                output_dir / "declared_blockers.csv", "blocker"
            )
            config = load_frozen_configuration(config_path)
            self.assertEqual(
                {record["claim_id"] for record in effects}
                | {record["claim_id"] for record in blockers},
                {record["claim_id"] for record in config["claims"]},
            )
            self.assertFalse(
                {record["claim_id"] for record in effects}
                & {record["claim_id"] for record in blockers}
            )

            primary = next(
                record
                for record in effects
                if record["claim_id"] == "DIRECT_PBM_MISTRAL_CONTEXTUAL"
            )
            self.assertEqual(primary["estimate"], -0.131274)
            self.assertEqual(
                primary["source_sha256"],
                next(
                    claim["source"]["source_sha256"]
                    for claim in config["claims"]
                    if claim["claim_id"] == "DIRECT_PBM_MISTRAL_CONTEXTUAL"
                ),
            )
            self.assertIn("clustering_unit=child", primary["uncertainty_method"])

            word_models = [
                record
                for record in models
                if record["claim_id"] == "WORD_CROSS_SCORER_PREDICTABILITY"
            ]
            self.assertEqual(
                {record["scorer"] for record in word_models},
                {
                    "MISTRAL_7B_V03",
                    "QWEN3_14B",
                    "TINYDIALOGUES_SMOLLM2_135M",
                },
            )
            word_effect = next(
                record
                for record in effects
                if record["claim_id"] == "WORD_CROSS_SCORER_PREDICTABILITY"
            )
            self.assertIsNone(word_effect["model_id"])

            for model in models:
                self.assertIn("controls=", model["formula_or_contrast"])
                self.assertIn("convergence_warnings=", model["estimator"])

            manifest = verify_stage_manifest(
                output_dir / "model_results_manifest.json",
                root=root,
                expected_stage="model-results",
            )
            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(
                manifest["upstream_manifests"][0]["stage_id"], "datasets"
            )

    def test_changed_dataset_artifact_blocks_model_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = build_tiny_repository(root)
            output_dir = root / "results/august_supervisor_report"
            extract_datasets(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )
            with (output_dir / "sample_registry.csv").open(
                "a", encoding="utf-8"
            ) as handle:
                handle.write("changed\n")
            with self.assertRaisesRegex(ContractError, "changed stage artifact"):
                extract_model_results(
                    root=root,
                    configuration_path=config_path,
                    output_dir=output_dir,
                )

    def test_full_frozen_claim_coverage_and_word_scorers_are_locked(self) -> None:
        config = load_frozen_configuration(CONFIG_PATH)
        hashes = {
            claim["source"]["required_marker"]["path"]: "0" * 64
            for claim in config["claims"]
            if claim["source"]["required_marker"]["path"] is not None
        }
        models_by_claim = {}
        for claim in config["claims"]:
            if claim["evidence_status"] == "PENDING" or claim["claim_role"] == "EXCLUDED":
                continue
            models_by_claim[claim["claim_id"]] = [
                f"MODEL_{claim['claim_id']}_{index}"
                for index, _ in enumerate(_model_variants(claim), start=1)
            ]
        effects = build_effect_records(config, hashes, models_by_claim)
        blockers = build_blocker_records(config, hashes)
        self.assertEqual(len(effects), 26)
        self.assertEqual(len(blockers), 5)
        self.assertEqual(
            {record["claim_id"] for record in effects}
            | {record["claim_id"] for record in blockers},
            {claim["claim_id"] for claim in config["claims"]},
        )
        word_claim = next(
            claim
            for claim in config["claims"]
            if claim["claim_id"] == "WORD_CROSS_SCORER_PREDICTABILITY"
        )
        self.assertEqual(
            {scorer for _, scorer, _ in _model_variants(word_claim)},
            {
                "MISTRAL_7B_V03",
                "QWEN3_14B",
                "TINYDIALOGUES_SMOLLM2_135M",
            },
        )

    def test_extraction_modules_do_not_import_statsmodels(self) -> None:
        for relative in (
            "src/august_supervisor/evidence.py",
            "src/august_supervisor/model_results.py",
        ):
            self.assertNotIn("statsmodels", (ROOT / relative).read_text().lower())


if __name__ == "__main__":
    unittest.main()
