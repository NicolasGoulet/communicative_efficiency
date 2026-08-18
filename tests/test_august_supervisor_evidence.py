"""Focused tests for August dataset-evidence extraction."""

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
    _read_csv_strict,
    _select_one,
    build_sample_records,
    extract_datasets,
    load_frozen_configuration,
    verify_declared_inputs,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "august_supervisor_report_v1.json"


def _base_claim(
    *,
    claim_id: str,
    role: str,
    evidence_status: str,
    source_path: str,
    source_sha256: str,
    marker_path: str | None,
    marker_satisfied: bool,
    sample_role: str,
    sample_scope: str,
    numerical_result: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "claim_id": claim_id,
        "claim_role": role,
        "scientific_question": "Frozen fixture question",
        "sample": {
            "role": sample_role,
            "scope": sample_scope,
            "rows": 10 if evidence_status != "PENDING" else None,
            "children": 2,
            "sessions": None,
            "corpora": 1,
        },
        "scorer": {
            "model": "mistralai/Mistral-7B-v0.3",
            "tokenizer": "Mistral-7B-v0.3 tokenizer",
            "comparability_rule": "Fixture scorer namespace",
        },
        "estimand": {
            "name": "fixture estimand",
            "outcome": "real_k3_sum_bits",
            "formula_or_contrast": "outcome ~ age + effort + child",
            "controls": ["word effort", "child fixed effects"],
            "direction_convention": "Negative means more predictable",
        },
        "numerical_result": numerical_result,
        "evidence_status": evidence_status,
        "source": {
            "canonical_artifact": source_path,
            "source_sha256": source_sha256,
            "required_marker": {
                "path": marker_path,
                "expectation": (
                    "status=COMPLETE_WITH_RECORDED_FIT_STATUS and failed=0"
                    if marker_satisfied
                    else "word_mistral_nonpbm58 PASS/COMPLETE"
                ),
                "observed": (
                    "COMPLETE_WITH_RECORDED_FIT_STATUS; failed=0"
                    if marker_satisfied
                    else "BLOCKED: fixture production is unrun"
                ),
                "satisfied": marker_satisfied,
            },
        },
        "required_interpretation": "Fixture interpretation",
        "required_limitation": "Fixture limitation",
        "destination_section": "Fixture section",
        "figure_eligibility": "SUPPORTING" if role != "PENDING" else "NONE",
    }


def build_tiny_repository(root: Path) -> Path:
    """Create a self-contained two-result/one-blocker extraction fixture."""

    direct_path = (
        root
        / "results/current_scientific_synthesis/direct_primary_estimates.csv"
    )
    direct_path.parent.mkdir(parents=True)
    direct_path.write_text(
        "family,question,sample,scorer,model_id,term,estimate,ci_low,ci_high,evidence_status\n"
        "Route 1 direct,Contextual utterance surprisal at fixed word effort,PBM21 discovery,Mistral,P1_k3_contextual,age_c,-0.1312736684158741,-0.1791515408699646,-0.0833957959617836,supported_association\n",
        encoding="utf-8",
    )
    direct_marker_path = (
        root
        / "results/direct_surprisal_replication/mistral_full79/modular/models/model_manifest.json"
    )
    direct_marker_path.parent.mkdir(parents=True)
    direct_marker_path.write_text(
        json.dumps(
            {
                "status": "COMPLETE_WITH_RECORDED_FIT_STATUS",
                "failed": 0,
                "singular": 0,
                "nonconverged": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    word_path = (
        root
        / "results/word_cross_scorer_comparison/scientific_question_summary.csv"
    )
    word_path.parent.mkdir(parents=True)
    word_path.write_text(
        "question_id,question,scientific_role,common_direction,scorers,cluster_supported_scorers,bootstrap_available_scorers,bootstrap_supported_scorers,replication_status\n"
        "same_word_k0_age,Question,registered supporting,negative,3,3,3,3,direction_and_interval_robust\n"
        "same_word_k3_age,Question,registered supporting,negative,3,3,3,3,direction_and_interval_robust\n",
        encoding="utf-8",
    )
    word_marker_path = root / "results/word_cross_scorer_comparison/manifest.json"
    word_marker_path.write_text(
        json.dumps(
            {
                "status": "PASS",
                "scorers": ["Mistral", "Qwen3-14B", "TinyDialogues"],
                "artifacts": [
                    {
                        "path": "results/word_cross_scorer_comparison/scientific_question_summary.csv",
                        "sha256": sha256_file(word_path),
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    pending_path = root / "results/complete_analysis_machine_v1/preflight.json"
    pending_path.parent.mkdir(parents=True)
    pending_path.write_text(
        json.dumps(
            {
                "status": "REVIEW",
                "components": [
                    {
                        "component_id": "word_mistral_nonpbm58",
                        "status": "BLOCKED",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    direct = _base_claim(
        claim_id="DIRECT_PBM_MISTRAL_CONTEXTUAL",
        role="PROMOTED",
        evidence_status="SUPPORTED",
        source_path="results/current_scientific_synthesis/direct_primary_estimates.csv",
        source_sha256=sha256_file(direct_path),
        marker_path="results/direct_surprisal_replication/mistral_full79/modular/models/model_manifest.json",
        marker_satisfied=True,
        sample_role="PBM discovery",
        sample_scope="Fixture PBM discovery rows",
        numerical_result={
            "estimate": -0.131274,
            "unit": "bits per month",
            "interval": {
                "level": 0.95,
                "low": -0.179152,
                "high": -0.083396,
                "type": "child-clustered confidence interval",
            },
            "uncertainty_method": "WLS with child-clustered covariance",
        },
    )
    word = _base_claim(
        claim_id="WORD_CROSS_SCORER_PREDICTABILITY",
        role="SUPPORTING",
        evidence_status="SUPPORTED",
        source_path="results/word_cross_scorer_comparison/scientific_question_summary.csv",
        source_sha256=sha256_file(word_path),
        marker_path="results/word_cross_scorer_comparison/manifest.json",
        marker_satisfied=True,
        sample_role="PBM word-level scorer robustness",
        sample_scope="Fixture exact shared word occurrences",
        numerical_result=None,
    )
    word["sample"]["rows"] = 12
    word["sample"]["corpora"] = 3
    word["scorer"] = {
        "model": "Mistral-7B-v0.3, Qwen3-14B, and TinyDialogues fitted separately",
        "tokenizer": "Three separate tokenizer namespaces",
        "comparability_rule": "Directions only; never pool raw bits",
    }
    word["source"]["required_marker"]["expectation"] = "status=PASS"
    word["source"]["required_marker"]["observed"] = "PASS"
    pending = _base_claim(
        claim_id="WORD_NONPBM58_CONFIRMATION",
        role="PENDING",
        evidence_status="PENDING",
        source_path="results/complete_analysis_machine_v1/preflight.json",
        source_sha256=sha256_file(pending_path),
        marker_path="results/complete_analysis_machine_v1/preflight.json",
        marker_satisfied=False,
        sample_role="planned non-PBM word confirmation",
        sample_scope="Fixture planned confirmation",
        numerical_result=None,
    )
    pending["scorer"]["model"] = "planned Mistral-7B-v0.3 same-pass word scoring"

    config = {
        "schema_version": "1.0.0",
        "frozen_at": "2026-08-17",
        "source_commit": "fixture",
        "purpose": "Self-contained extraction fixture",
        "allowed_evidence_statuses": [
            "SUPPORTED",
            "QUALIFIED",
            "CONTRARY",
            "DESCRIPTIVE",
            "PENDING",
        ],
        "allowed_claim_roles": ["PROMOTED", "SUPPORTING", "EXCLUDED", "PENDING"],
        "allowed_figure_eligibility": ["PRIMARY", "SUPPORTING", "NONE"],
        "tokenizer_comparability_policy": "Never pool tokenizer scales",
        "page_contract": {},
        "locked_readings": [],
        "claims": [direct, word, pending],
        "blockers": [
            {
                "claim_id": "WORD_NONPBM58_CONFIRMATION",
                "status": "BLOCKED",
                "reason": "Fixture production has not run",
                "required_resolution": "Produce and audit the registered handoff",
            }
        ],
    }
    config_path = root / "configs/frozen.json"
    config_path.parent.mkdir()
    config_path.write_text(json.dumps(config, sort_keys=True) + "\n", encoding="utf-8")
    return config_path


class AugustSupervisorEvidenceTests(unittest.TestCase):
    def test_changed_declared_source_hash_fails_before_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "canonical.csv"
            marker = root / "audit.json"
            source.write_text("claim_id,estimate\nCLAIM_TEST,1\n", encoding="utf-8")
            marker.write_text('{"status":"PASS"}\n', encoding="utf-8")
            claim = {
                "claim_id": "CLAIM_TEST",
                "claim_role": "SUPPORTING",
                "evidence_status": "SUPPORTED",
                "source": {
                    "canonical_artifact": "canonical.csv",
                    "source_sha256": sha256_file(source),
                    "required_marker": {
                        "path": "audit.json",
                        "expectation": "status=PASS",
                        "observed": "PASS",
                        "satisfied": True,
                    },
                },
            }

            snapshot = verify_declared_inputs([claim], root)
            self.assertEqual(snapshot["canonical.csv"], sha256_file(source))

            source.write_text("claim_id,estimate\nCLAIM_TEST,2\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "changed source"):
                verify_declared_inputs([claim], root)

    def test_frozen_configuration_rejects_duplicate_claim_ids(self) -> None:
        config = load_frozen_configuration(CONFIG_PATH)
        duplicate = copy.deepcopy(config)
        duplicate["claims"].append(copy.deepcopy(duplicate["claims"][0]))
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "duplicate.json"
            path.write_text(json.dumps(duplicate), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "duplicate claim IDs"):
                load_frozen_configuration(path)

    def test_canonical_csv_schema_missingness_and_identity_are_strict(self) -> None:
        relative = (
            "results/current_scientific_synthesis/direct_primary_estimates.csv"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "source.csv"
            path.write_text("sample,scorer\nPBM21 discovery,Mistral\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "schema mismatch"):
                _read_csv_strict(path, relative)

            path.write_text(
                "family,question,sample,scorer,model_id,term,estimate,ci_low,ci_high,evidence_status\n"
                "Route 1 direct,Question,PBM21 discovery,Mistral,P1_k3_contextual,age_c,,-1,1,supported_association\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "unsupported missing values"):
                _read_csv_strict(path, relative)

        rows = [
            {"sample": "PBM21 discovery", "scorer": "Mistral"},
            {"sample": "PBM21 discovery", "scorer": "Mistral"},
        ]
        with self.assertRaisesRegex(ContractError, "ambiguous scorer/sample identity"):
            _select_one(
                rows,
                "CLAIM_TEST",
                sample="PBM21 discovery",
                scorer="Mistral",
            )

    def test_dataset_stage_is_deterministic_and_preserves_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = build_tiny_repository(root)
            output_dir = root / "results/august_supervisor_report"
            first = extract_datasets(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )
            first_registry = (output_dir / "sample_registry.csv").read_bytes()
            first_manifest = (output_dir / "dataset_manifest.json").read_bytes()
            second = extract_datasets(
                root=root,
                configuration_path=config_path,
                output_dir=output_dir,
            )

            self.assertEqual(first["status"], "PASS")
            self.assertEqual(first["row_counts"], {"sample_registry": 3})
            self.assertEqual(
                first["input_hashes_before"], first["input_hashes_after"]
            )
            self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])
            self.assertEqual(
                first_registry, (output_dir / "sample_registry.csv").read_bytes()
            )
            self.assertEqual(
                first_manifest, (output_dir / "dataset_manifest.json").read_bytes()
            )

            samples = read_registry_csv(output_dir / "sample_registry.csv", "sample")
            self.assertEqual(len(samples), 3)
            self.assertEqual(len({record["sample_id"] for record in samples}), 3)
            self.assertEqual(
                {record["audit_status"] for record in samples}, {"PASS", "BLOCKED"}
            )
            verified = verify_stage_manifest(
                output_dir / "dataset_manifest.json",
                root=root,
                expected_stage="datasets",
            )
            self.assertEqual(verified["status"], "PASS")

    def test_full_frozen_sample_registry_keeps_scientific_scopes_separate(self) -> None:
        config = load_frozen_configuration(CONFIG_PATH)
        hashes = {
            claim["source"]["required_marker"]["path"]: "0" * 64
            for claim in config["claims"]
            if claim["source"]["required_marker"]["path"] is not None
        }
        samples = build_sample_records(config, hashes)
        by_id = {record["sample_id"]: record for record in samples}
        self.assertEqual(len(samples), 31)
        self.assertEqual(
            by_id["SAMPLE_DIRECT_PBM_MISTRAL_CONTEXTUAL"]["scope"],
            "PBM_DISCOVERY",
        )
        self.assertEqual(
            by_id["SAMPLE_DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY"]["scope"],
            "NON_PBM_CONFIRMATION",
        )
        self.assertEqual(
            by_id["SAMPLE_WORD_CROSS_SCORER_PREDICTABILITY"]["scope"],
            "PBM_SCORER_ROBUSTNESS",
        )
        self.assertEqual(
            by_id["SAMPLE_HALL_RACE_CLASS_INTERACTION"]["scope"],
            "HALL_SNAPSHOT",
        )


if __name__ == "__main__":
    unittest.main()
