from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = ROOT / "docs" / "august_supervisor_workflow"
PROMPT_NAMES = [
    "00_bootstrap.md",
    "01_evidence_freeze.md",
    "02_contracts.md",
    "03_extract_results.md",
    "04_synthesis.md",
    "05_plots.md",
    "06_report.md",
    "07_landing_page.md",
    "08_red_team.md",
    "09_remediation.md",
    "10_final_integration.md",
]


class AugustSupervisorWorkflowDocumentationTests(unittest.TestCase):
    def test_manifest_and_operator_guide_define_the_complete_order(self) -> None:
        manifest_path = WORKFLOW_ROOT / "workflow_manifest.json"
        guide_path = WORKFLOW_ROOT / "README.md"
        self.assertTrue(manifest_path.is_file())
        self.assertTrue(guide_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stage_ids = [stage["stage_id"] for stage in manifest["stages"]]
        self.assertEqual(stage_ids, [name.split("_", 1)[0] for name in PROMPT_NAMES])
        self.assertEqual(manifest["branch"], "agent/august-supervisor-report-v1")
        self.assertTrue(manifest["shared_physical_worktree"])
        self.assertEqual(manifest["completion_marker"], "AUGUST_REPORT_COMPLETE_AND_AUDITED")

        guide = guide_path.read_text(encoding="utf-8")
        for prompt_name in PROMPT_NAMES:
            self.assertIn(f"prompts/{prompt_name}", guide)
        self.assertIn("exactly one new task", guide)
        self.assertIn("Replace `EXPECTED_SHA`", guide)
        self.assertIn("Do not start the next", guide)
        self.assertIn("repeat prompt 08", guide)

    def test_every_prompt_is_copy_ready_and_preserves_handoff_safety(self) -> None:
        prompt_root = WORKFLOW_ROOT / "prompts"
        for index, name in enumerate(PROMPT_NAMES):
            with self.subTest(prompt=name):
                path = prompt_root / name
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                self.assertIn("shared physical worktree", text)
                self.assertIn("Do not spawn agents", text)
                self.assertIn("git status --short --branch", text)
                self.assertIn("Explicit file allowlist", text)
                self.assertIn("Never use `git add .`", text)
                self.assertIn("test-driven", text.lower())
                self.assertIn("STAGE_PASS", text)
                self.assertIn("clean worktree", text)
                self.assertIn("Do not invent, refit, select, or reinterpret results", text)
                self.assertIn("claim ID", text)
                self.assertIn("PBM discovery", text)
                self.assertIn("Hall", text)
                if index > 0:
                    self.assertIn("EXPECTED_SHA", text)

    def test_stage_isolation_and_audit_loop_are_explicit(self) -> None:
        plot_prompt = (WORKFLOW_ROOT / "prompts" / "05_plots.md").read_text(encoding="utf-8")
        report_prompt = (WORKFLOW_ROOT / "prompts" / "06_report.md").read_text(encoding="utf-8")
        red_team = (WORKFLOW_ROOT / "prompts" / "08_red_team.md").read_text(encoding="utf-8")
        remediation = (WORKFLOW_ROOT / "prompts" / "09_remediation.md").read_text(encoding="utf-8")
        integration = (WORKFLOW_ROOT / "prompts" / "10_final_integration.md").read_text(encoding="utf-8")

        self.assertIn("Do not import statsmodels", plot_prompt)
        self.assertIn("Do not read raw scored trees", plot_prompt)
        self.assertIn("Do not fit models", report_prompt)
        self.assertIn("Do not create plots", report_prompt)
        self.assertIn("Do not edit report product files", red_team)
        self.assertIn("AUDIT_FAIL", red_team)
        self.assertIn("repeat prompt 08", remediation)
        self.assertIn("two report-only rebuilds", integration)
        self.assertIn("AUGUST_REPORT_COMPLETE_AND_AUDITED", integration)

    def test_project_compass_links_the_workflow_without_duplicating_it(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/august_supervisor_workflow/README.md", agents)
        self.assertIn("strict numbered order", agents)
        self.assertIn("one shared physical worktree", agents)


if __name__ == "__main__":
    unittest.main()
