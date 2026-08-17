from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.build_complete_analysis_machine import (
    build_synthesis,
    load_config,
    preflight,
    run_component_phase,
    run_phases,
)


class CompleteAnalysisMachineTests(unittest.TestCase):
    def test_repository_config_has_scientifically_separate_components(self) -> None:
        root = Path(__file__).parents[1]
        config = load_config(root / "configs" / "complete_analysis_machine_v1.json")
        ids = {item["component_id"] for item in config["components"]}
        self.assertTrue({"route1_model_atlas", "route2_response_space", "route2_relative_effort", "corrected_pbm_bayes", "direct_sustained_onset", "word_mistral_pbm", "word_qwen_pbm", "word_tinydialogues_pbm", "word_cross_scorer_pbm", "scientific_answer_synthesis", "word_mistral_nonpbm58"}.issubset(ids))
        blocked = next(item for item in config["components"] if item["component_id"] == "word_mistral_nonpbm58")
        self.assertIn("unrun", blocked["blocked_reason"])

    def test_preflight_reports_missing_inputs_without_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config.json"
            config_path.write_text(json.dumps({"components": [{"component_id": "x", "required_paths": ["missing"], "commands": {}}]}))
            report = preflight(load_config(config_path), root)
            self.assertEqual(report["status"], "REVIEW")
            self.assertEqual(report["components"][0]["status"], "BLOCKED")

    def test_command_manifest_resumes_only_with_expected_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir); run_root = root / "run"; artifact = root / "done.txt"
            config_path = root / "config.json"
            command = ["/usr/bin/touch", str(artifact)]
            config_path.write_text(json.dumps({"components": [{"component_id": "x", "commands": {"fit": [command]}, "expected_artifacts": {"fit": [str(artifact)]}}]}))
            config = load_config(config_path); component = config["components"][0]
            first = run_component_phase(component, "fit", config=config, repo_root=root, run_root=run_root)
            self.assertEqual(first["status"], "PASS")
            second = run_component_phase(component, "fit", config=config, repo_root=root, run_root=run_root)
            self.assertTrue(second["resumed_without_rerun"])
            artifact.write_text("replacement", encoding="utf-8")
            third = run_component_phase(component, "fit", config=config, repo_root=root, run_root=run_root)
            self.assertNotIn("resumed_without_rerun", third)

    def test_downstream_phase_is_blocked_after_failed_upstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "components": [
                            {
                                "component_id": "x",
                                "commands": {
                                    "fit": [["/usr/bin/false"]],
                                    "plots": [["/usr/bin/true"]],
                                },
                                "expected_artifacts": {
                                    "fit": ["fit.done"],
                                    "plots": ["plot.done"],
                                },
                            }
                        ]
                    }
                )
            )
            report = run_phases(
                load_config(config_path), root, root / "run", ["fit", "plots"]
            )
            statuses = [item["status"] for item in report["components"]]
            self.assertEqual(statuses, ["FAILED", "BLOCKED_UPSTREAM"])

    def test_same_phase_preflight_refreshes_after_prior_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = root / "first.done"
            second = root / "second.done"
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "components": [
                            {
                                "component_id": "producer",
                                "commands": {"reports": [["/usr/bin/touch", str(first)]]},
                                "expected_artifacts": {"reports": [str(first)]},
                            },
                            {
                                "component_id": "consumer",
                                "required_paths": [str(first)],
                                "commands": {"reports": [["/usr/bin/touch", str(second)]]},
                                "expected_artifacts": {"reports": [str(second)]},
                            },
                        ]
                    }
                )
            )
            report = run_phases(
                load_config(config_path), root, root / "run", ["reports"]
            )
            self.assertEqual([item["status"] for item in report["components"]], ["PASS", "PASS"])

    def test_synthesis_keeps_cross_scorer_guardrail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir); config_path = root / "config.json"
            config_path.write_text(json.dumps({"components": [{"component_id": "x", "family": "word", "sample": "PBM", "scorer": "two", "scientific_role": "robustness", "guardrail": "never pool raw bits", "commands": {}}], "synthesis_markdown": "index.md", "synthesis_html": "index.html"}))
            report = build_synthesis(load_config(config_path), root, root / "run")
            self.assertEqual(report["status"], "PASS")
            self.assertIn("never pool raw bits", (root / "index.md").read_text())


if __name__ == "__main__":
    unittest.main()
