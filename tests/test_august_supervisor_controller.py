from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.august_supervisor.contracts import (
    ContractError,
    sha256_file,
    write_stage_manifest,
)
from src.build_august_supervisor_report import (
    COMPLETION_MARKER,
    STAGES,
    collect_product_hashes,
    run_controller,
    validate_completion_gate,
    validate_stage_dependencies,
    write_completion_marker,
)


ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _manifest_chain(root: Path) -> None:
    results = root / "results" / "august_supervisor_report"
    plots = results / "plots"
    config = root / "configs" / "august_supervisor_report_v1.json"
    _write(config, "{}\n")

    sample = results / "sample_registry.csv"
    _write(sample, "sample\n")
    dataset = results / "dataset_manifest.json"
    write_stage_manifest(
        dataset,
        stage_id="datasets",
        artifact_paths=[sample],
        upstream_manifest_paths=[],
        root=root,
        configuration_path=config,
    )

    effects = results / "effect_registry.csv"
    _write(effects, "effect\n")
    model = results / "model_results_manifest.json"
    write_stage_manifest(
        model,
        stage_id="model-results",
        artifact_paths=[effects],
        upstream_manifest_paths=[dataset],
        root=root,
        configuration_path=config,
    )

    synthesis_table = results / "headline_findings.csv"
    _write(synthesis_table, "finding\n")
    synthesis = results / "synthesis_manifest.json"
    write_stage_manifest(
        synthesis,
        stage_id="synthesis",
        artifact_paths=[synthesis_table],
        upstream_manifest_paths=[model],
        root=root,
        configuration_path=config,
    )

    figure = plots / "figure.png"
    _write(figure, "png fixture\n")
    plot = plots / "plot_manifest.json"
    write_stage_manifest(
        plot,
        stage_id="plots",
        artifact_paths=[figure],
        upstream_manifest_paths=[synthesis],
        root=root,
        configuration_path=config,
    )

    markdown = root / "docs" / "august_supervisor_report.md"
    html = root / "docs" / "august_supervisor_report.html"
    trace = results / "report_trace.json"
    index = root / "docs" / "august_supervisor_index.html"
    _write(markdown, "# report\n")
    _write(html, "<html>report</html>\n")
    _write(trace, "{}\n")
    _write(index, "<html>index</html>\n")
    write_stage_manifest(
        results / "report_manifest.json",
        stage_id="report",
        artifact_paths=[markdown, html, trace],
        upstream_manifest_paths=[plot],
        root=root,
    )


def _initialize_completion_fixture(root: Path) -> None:
    _git(root, "init", "-b", "agent/august-supervisor-report-v1")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test User")
    _write(root / ".gitignore", "results/\n")
    _manifest_chain(root)
    _git(root, "add", ".gitignore", "configs", "docs")
    _git(root, "commit", "-m", "fixture")

    commit = _git(root, "rev-parse", "HEAD")
    audit = root / "results" / "august_supervisor_report" / "audit"
    findings = audit / "findings.json"
    _write(findings, "[]\n")
    required_checks = (
        "claim_reconciliation",
        "number_formatting",
        "manifest_hashes",
        "html_package",
        "scientific_language",
        "deterministic_renders",
        "git_hygiene",
        "browser_renders",
    )
    report = {
        "schema_version": "1.0.0",
        "stage_id": "audit",
        "verdict": "AUDIT_PASS",
        "audited_commit": commit,
        "branch": "agent/august-supervisor-report-v1",
        "finding_count": 0,
        "blocking_finding_count": 0,
        "findings_path": "results/august_supervisor_report/audit/findings.json",
        "findings_sha256": sha256_file(findings),
        "checks": {
            name: {"finding_count": 0, "blocking_finding_count": 0, "summary": {}}
            for name in required_checks
        },
        "independence_boundary": {
            "models_recomputed": False,
            "report_products_edited": False,
            "final_completion_marker_created": False,
        },
    }
    report_path = audit / "audit_report.json"
    _write(report_path, json.dumps(report, sort_keys=True) + "\n")
    _write(
        audit / "AUDIT_PASS",
        "AUDIT_PASS\n"
        f"audit_report_sha256={sha256_file(report_path)}\n"
        f"findings_sha256={sha256_file(findings)}\n",
    )


class AugustSupervisorControllerTests(unittest.TestCase):
    def test_script_entrypoint_is_directly_invocable(self) -> None:
        result = subprocess.run(
            (
                sys.executable,
                str(ROOT / "src" / "build_august_supervisor_report.py"),
                "--help",
            ),
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--stage", result.stdout)

    def test_stage_names_are_fixed_and_invalid_names_fail_closed(self) -> None:
        self.assertEqual(
            STAGES,
            (
                "datasets",
                "model-results",
                "synthesis",
                "plots",
                "report",
                "index",
                "audit",
            ),
        )
        with self.assertRaisesRegex(ValueError, "invalid stage"):
            run_controller(root=ROOT, stage="not-a-stage")

    def test_all_dispatches_each_stage_once_in_dependency_order(self) -> None:
        with patch(
            "src.build_august_supervisor_report.run_stage",
            side_effect=lambda *, stage, **_: {"stage": stage, "status": "PASS"},
        ) as mocked:
            result = run_controller(
                root=ROOT,
                stage="all",
                include_browser_renders=False,
            )
        self.assertEqual([item["stage"] for item in result["stages"]], list(STAGES))
        self.assertEqual(
            [call.kwargs["stage"] for call in mocked.call_args_list], list(STAGES)
        )

    def test_missing_and_stale_manifests_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaisesRegex(ContractError, "missing stage manifest"):
                validate_stage_dependencies(root=root, stage="model-results")

            _manifest_chain(root)
            dataset = root / "results" / "august_supervisor_report" / "dataset_manifest.json"
            dataset.write_text(dataset.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "changed upstream manifest"):
                validate_stage_dependencies(root=root, stage="synthesis")

    def test_changed_input_hash_is_refused_before_downstream_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _manifest_chain(root)
            sample = root / "results" / "august_supervisor_report" / "sample_registry.csv"
            _write(sample, "changed\n")
            with self.assertRaisesRegex(ContractError, "changed stage artifact"):
                validate_stage_dependencies(root=root, stage="model-results")

    def test_completion_gate_requires_current_audit_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _initialize_completion_fixture(root)
            marker = root / "results" / "august_supervisor_report" / "audit" / "AUDIT_PASS"
            marker.unlink()
            with self.assertRaisesRegex(ContractError, "AUDIT_PASS"):
                validate_completion_gate(root=root)

    def test_completion_gate_refuses_dirty_or_incomplete_products(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _initialize_completion_fixture(root)
            report = root / "docs" / "august_supervisor_report.md"
            report.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "clean worktree"):
                validate_completion_gate(root=root)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _initialize_completion_fixture(root)
            (root / "docs" / "august_supervisor_index.html").unlink()
            _git(root, "add", "docs/august_supervisor_index.html")
            _git(root, "commit", "-m", "remove incomplete product")
            with self.assertRaisesRegex(ContractError, "missing product"):
                validate_completion_gate(root=root)

    def test_completion_marker_records_commit_audit_products_tests_and_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _initialize_completion_fixture(root)
            test_summary = {
                "focused": {"command": "python -m unittest focused", "tests": 7, "failures": 0},
                "full": {"command": "python -m unittest discover", "tests": 500, "failures": 0},
            }
            result = write_completion_marker(
                root=root,
                test_summary=test_summary,
                timestamp="2026-08-18T16:00:00+00:00",
            )
            marker = root / COMPLETION_MARKER
            payload = json.loads(marker.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "AUGUST_REPORT_COMPLETE_AND_AUDITED")
            self.assertEqual(payload["commit"], _git(root, "rev-parse", "HEAD"))
            self.assertEqual(payload["test_summary"], test_summary)
            self.assertEqual(payload["created_at_utc"], "2026-08-18T16:00:00+00:00")
            self.assertEqual(payload["audit"]["verdict"], "AUDIT_PASS")
            self.assertIn("docs/august_supervisor_report.md", payload["product_hashes"])
            self.assertEqual(result["marker_sha256"], sha256_file(marker))
            self.assertEqual(payload["product_hashes"], collect_product_hashes(root=root))

    def test_controller_source_contains_no_modeling_or_plotting_logic(self) -> None:
        source = (ROOT / "src" / "build_august_supervisor_report.py").read_text(
            encoding="utf-8"
        ).lower()
        for prohibited in ("statsmodels", "matplotlib", "seaborn", ".fit(", "plt."):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
