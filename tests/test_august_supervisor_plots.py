"""Focused tests for frozen August supervisor-report figures."""

from __future__ import annotations

import copy
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.august_supervisor.contracts import (
    ContractError,
    read_registry_csv,
    sha256_file,
    verify_stage_manifest,
)
from src.august_supervisor.evidence import load_frozen_configuration
from src.august_supervisor.plots import (
    EXPECTED_OUTPUT_NAMES,
    FIGURE_SPECS,
    build_supervisor_plots,
    validate_plot_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "results" / "august_supervisor_report"
CONFIG_PATH = ROOT / "configs" / "august_supervisor_report_v1.json"


def _read_synthesis() -> list[dict[str, object]]:
    return [
        row
        for name in (
            "headline_findings.csv",
            "supporting_findings.csv",
            "coverage_and_limitations.csv",
        )
        for row in read_registry_csv(INPUT_DIR / name, "synthesis")
    ]


def _frozen_inputs() -> tuple[
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    return (
        load_frozen_configuration(CONFIG_PATH),
        read_registry_csv(INPUT_DIR / "effect_registry.csv", "effect"),
        read_registry_csv(INPUT_DIR / "model_inventory.csv", "model"),
        read_registry_csv(INPUT_DIR / "sample_registry.csv", "sample"),
        _read_synthesis(),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class AugustSupervisorPlotTests(unittest.TestCase):
    def test_plot_stage_validates_the_complete_input_manifest_chain(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".august-plot-test-", dir=ROOT) as tmp:
            temporary = Path(tmp)
            bad_manifest = temporary / "synthesis_manifest.json"
            shutil.copy2(INPUT_DIR / "synthesis_manifest.json", bad_manifest)
            record = json.loads(bad_manifest.read_text(encoding="utf-8"))
            record["manifest_sha256"] = "0" * 64
            bad_manifest.write_text(
                json.dumps(record, sort_keys=True) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ContractError, "manifest payload changed"):
                build_supervisor_plots(
                    root=ROOT,
                    input_dir=INPUT_DIR,
                    output_dir=temporary / "plots",
                    synthesis_manifest_path=bad_manifest,
                )

    def test_claim_contract_fails_closed(self) -> None:
        config, effects, models, samples, synthesis = _frozen_inputs()
        selected = FIGURE_SPECS[0].claim_ids[0]

        cases: list[tuple[str, list[dict[str, object]], str]] = []
        cases.append(
            (
                "missing",
                [row for row in effects if row["claim_id"] != selected],
                "effect claim coverage mismatch",
            )
        )
        extra = copy.deepcopy(effects)
        extra_row = copy.deepcopy(extra[0])
        extra_row["effect_id"] = "EFFECT_UNREGISTERED_EXTRA"
        extra_row["claim_id"] = "UNREGISTERED_EXTRA"
        extra.append(extra_row)
        cases.append(("extra", extra, "effect claim coverage mismatch"))
        duplicated = copy.deepcopy(effects)
        duplicated.append(copy.deepcopy(duplicated[0]))
        cases.append(("duplicated", duplicated, "duplicate unique key"))
        ineligible = copy.deepcopy(effects)
        next(row for row in ineligible if row["claim_id"] == selected)[
            "figure_eligibility"
        ] = "NONE"
        cases.append(("ineligible", ineligible, "figure eligibility drift"))
        reclassified = copy.deepcopy(effects)
        next(row for row in reclassified if row["claim_id"] == selected)[
            "evidence_status"
        ] = "QUALIFIED"
        cases.append(("reclassified", reclassified, "classification drift"))

        for label, changed, message in cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(ContractError, message):
                    validate_plot_evidence(
                        config=config,
                        effects=changed,
                        models=models,
                        samples=samples,
                        synthesis=synthesis,
                    )

    def test_outputs_are_fixed_traceable_accessible_and_deterministic(self) -> None:
        expected_claims = {
            spec.figure_id: list(spec.claim_ids) for spec in FIGURE_SPECS
        }
        with tempfile.TemporaryDirectory(prefix=".august-plot-test-", dir=ROOT) as tmp:
            output_dir = Path(tmp) / "plots"
            first = build_supervisor_plots(
                root=ROOT,
                input_dir=INPUT_DIR,
                output_dir=output_dir,
            )
            first_bytes = {
                name: (output_dir / name).read_bytes()
                for name in EXPECTED_OUTPUT_NAMES
            }
            second = build_supervisor_plots(
                root=ROOT,
                input_dir=INPUT_DIR,
                output_dir=output_dir,
            )

            self.assertEqual(first["status"], "PASS")
            self.assertEqual(first["figure_count"], 6)
            self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])
            self.assertEqual(
                sorted(path.name for path in output_dir.iterdir()),
                sorted(EXPECTED_OUTPUT_NAMES),
            )
            for name, payload in first_bytes.items():
                self.assertEqual(payload, (output_dir / name).read_bytes(), name)

            figures = _read_csv(output_dir / "figure_manifest.csv")
            self.assertEqual(
                [row["figure_id"] for row in figures],
                sorted(expected_claims),
            )
            effect_rows = _read_csv(INPUT_DIR / "effect_registry.csv")
            effects = {row["claim_id"]: row for row in effect_rows}
            for row in figures:
                claim_ids = json.loads(row["claim_ids"])
                effect_ids = json.loads(row["effect_ids"])
                self.assertEqual(claim_ids, sorted(expected_claims[row["figure_id"]]))
                self.assertEqual(
                    effect_ids,
                    sorted(effects[claim_id]["effect_id"] for claim_id in claim_ids),
                )
                self.assertGreaterEqual(len(row["caption"]), 80)
                self.assertGreaterEqual(len(row["alt_text"]), 80)
                self.assertTrue(json.loads(row["warnings"]))
                provenance = json.loads(row["upstream_provenance"])
                self.assertEqual(provenance["synthesis_manifest"]["stage_id"], "synthesis")
                self.assertEqual(provenance["model_results_manifest"]["stage_id"], "model-results")
                image_path = ROOT / row["image_path"]
                data_path = ROOT / row["plot_data_path"]
                self.assertEqual(sha256_file(image_path), row["image_sha256"])
                self.assertEqual(sha256_file(data_path), row["plot_data_sha256"])
                with Image.open(image_path) as image:
                    self.assertEqual(
                        image.size,
                        (int(row["width_px"]), int(row["height_px"])),
                    )

            numeric_rows = []
            word_rows = []
            for spec in FIGURE_SPECS:
                rows = _read_csv(output_dir / spec.plot_data_name)
                self.assertTrue(rows)
                self.assertEqual(
                    {row["claim_id"] for row in rows}, set(spec.claim_ids)
                )
                if spec.figure_id == "FIGURE_03_WORD_CROSS_SCORER_SIGNS":
                    word_rows = rows
                numeric_rows.extend(row for row in rows if row["estimate"])
            self.assertTrue(numeric_rows)
            for row in numeric_rows:
                source = effects[row["claim_id"]]
                self.assertEqual(row["estimate"], source["estimate"])
                self.assertEqual(row["ci_low"], source["ci_low"])
                self.assertEqual(row["ci_high"], source["ci_high"])
                self.assertEqual(row["effect_id"], source["effect_id"])
            self.assertEqual({row["estimate"] for row in word_rows}, {""})
            self.assertEqual(
                {row["scorer"] for row in word_rows if row["scorer"] != "MULTI_SCORER"},
                {"MISTRAL_7B_V03", "QWEN3_14B", "TINYDIALOGUES_SMOLLM2_135M"},
            )
            self.assertIn("mixed signs", {row["categorical_value"] for row in word_rows})

            manifest = verify_stage_manifest(
                output_dir / "plot_manifest.json",
                root=ROOT,
                expected_stage="plots",
            )
            artifact_paths = [item["path"] for item in manifest["artifacts"]]
            self.assertEqual(artifact_paths, sorted(artifact_paths))
            self.assertEqual(
                manifest["upstream_manifests"][0]["stage_id"], "synthesis"
            )

    def test_plot_module_has_no_model_fitting_dependencies(self) -> None:
        source = (ROOT / "src" / "august_supervisor" / "plots.py").read_text(
            encoding="utf-8"
        ).lower()
        self.assertNotIn("statsmodels", source)
        self.assertNotIn(".fit(", source)
        self.assertNotIn("lowess", source)


if __name__ == "__main__":
    unittest.main()
