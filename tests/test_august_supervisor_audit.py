"""Adversarial tests for the independent August supervisor-package audit."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from src.august_supervisor.audit import (
    BLOCKING_SEVERITIES,
    audit_claim_reconciliation,
    audit_deterministic_renders,
    audit_html_package,
    audit_manifest_hashes,
    audit_number_formatting,
    audit_scientific_language,
    run_independent_audit,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "results" / "august_supervisor_report"
PLOT_DIR = INPUT_DIR / "plots"
CONFIGURATION = ROOT / "configs" / "august_supervisor_report_v1.json"
REPORT_MARKDOWN = ROOT / "docs" / "august_supervisor_report.md"
REPORT_HTML = ROOT / "docs" / "august_supervisor_report.html"
INDEX_HTML = ROOT / "docs" / "august_supervisor_index.html"


def _codes(findings: list[dict[str, object]]) -> set[str]:
    return {str(finding["code"]) for finding in findings}


def _blocking(findings: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        finding
        for finding in findings
        if str(finding["severity"]) in BLOCKING_SEVERITIES
    ]


class AugustSupervisorAuditTests(unittest.TestCase):
    def test_claim_source_reconciliation_traces_every_registered_claim(self) -> None:
        findings, summary = audit_claim_reconciliation(
            root=ROOT,
            configuration_path=CONFIGURATION,
            input_dir=INPUT_DIR,
            plot_dir=PLOT_DIR,
        )
        self.assertEqual(_blocking(findings), [], findings)
        self.assertEqual(summary["claim_count"], 31)
        self.assertEqual(summary["synthesis_claim_count"], 31)
        self.assertEqual(summary["report_trace_claim_count"], 31)
        self.assertEqual(summary["figure_count"], 6)
        self.assertGreater(summary["numeric_plot_row_count"], 10)
        self.assertEqual(summary["source_hash_mismatch_count"], 0)

    def test_claim_reconciliation_detects_a_changed_registered_estimate(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".august-audit-claim-", dir=ROOT
        ) as tmp:
            copied = Path(tmp) / "inputs"
            shutil.copytree(INPUT_DIR, copied)
            effect_path = copied / "effect_registry.csv"
            source = effect_path.read_text(encoding="utf-8")
            effect_path.write_text(
                source.replace("-0.131274", "-0.231274", 1), encoding="utf-8"
            )
            findings, _ = audit_claim_reconciliation(
                root=ROOT,
                configuration_path=CONFIGURATION,
                input_dir=copied,
                plot_dir=copied / "plots",
                report_trace_path=INPUT_DIR / "report_trace.json",
            )
            self.assertIn("CLAIM_EFFECT_NUMBER_MISMATCH", _codes(findings))

    def test_number_formatting_is_claim_locked_and_rejects_drift(self) -> None:
        findings, summary = audit_number_formatting(
            root=ROOT,
            configuration_path=CONFIGURATION,
            markdown_path=REPORT_MARKDOWN,
            html_path=REPORT_HTML,
            index_path=INDEX_HTML,
        )
        self.assertEqual(_blocking(findings), [], findings)
        self.assertGreaterEqual(summary["locked_display_count"], 7)

        with tempfile.TemporaryDirectory(
            prefix=".august-audit-number-", dir=ROOT
        ) as tmp:
            changed = Path(tmp) / "report.md"
            changed.write_text(
                REPORT_MARKDOWN.read_text(encoding="utf-8").replace(
                    "43.7%", "43.70%", 1
                ),
                encoding="utf-8",
            )
            findings, _ = audit_number_formatting(
                root=ROOT,
                configuration_path=CONFIGURATION,
                markdown_path=changed,
                html_path=REPORT_HTML,
                index_path=INDEX_HTML,
            )
            self.assertIn("NUMBER_FORMAT_DRIFT", _codes(findings))

    def test_manifest_hash_audit_rejects_a_changed_manifest(self) -> None:
        findings, summary = audit_manifest_hashes(
            root=ROOT, report_manifest_path=INPUT_DIR / "report_manifest.json"
        )
        self.assertEqual(_blocking(findings), [], findings)
        self.assertEqual(
            summary["verified_stage_chain"],
            ["datasets", "model-results", "synthesis", "plots", "report"],
        )

        with tempfile.TemporaryDirectory(
            prefix=".august-audit-manifest-", dir=ROOT
        ) as tmp:
            changed = Path(tmp) / "report_manifest.json"
            payload = json.loads(
                (INPUT_DIR / "report_manifest.json").read_text(encoding="utf-8")
            )
            payload["manifest_sha256"] = "0" * 64
            changed.write_text(
                json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
            )
            findings, _ = audit_manifest_hashes(
                root=ROOT, report_manifest_path=changed
            )
            self.assertIn("MANIFEST_HASH_MISMATCH", _codes(findings))

    def test_local_links_images_fragments_and_accessibility_are_checked(self) -> None:
        findings, summary = audit_html_package(
            root=ROOT,
            html_paths=(REPORT_HTML, INDEX_HTML),
            figure_manifest_path=PLOT_DIR / "figure_manifest.csv",
        )
        self.assertEqual(_blocking(findings), [], findings)
        self.assertEqual(summary["html_document_count"], 2)
        self.assertGreater(summary["local_reference_count"], 20)
        self.assertEqual(summary["missing_target_count"], 0)
        self.assertEqual(summary["empty_alt_count"], 0)

        with tempfile.TemporaryDirectory(
            prefix=".august-audit-html-", dir=ROOT
        ) as tmp:
            page = Path(tmp) / "page.html"
            page.write_text(
                "<!doctype html><html lang=\"en\"><head>"
                "<meta name=\"viewport\" content=\"width=device-width\">"
                "<title>Audit fixture</title></head><body>"
                "<main><h1 id=\"present\">Fixture</h1>"
                "<a href=\"#absent\">Broken fragment</a></main></body></html>",
                encoding="utf-8",
            )
            findings, _ = audit_html_package(
                root=ROOT, html_paths=(page,), figure_manifest_path=None
            )
            self.assertIn("HTML_MISSING_FRAGMENT", _codes(findings))

    def test_prohibited_language_and_all_scientific_guardrails_are_audited(self) -> None:
        findings, summary = audit_scientific_language(
            root=ROOT,
            configuration_path=CONFIGURATION,
            report_path=REPORT_MARKDOWN,
            index_path=INDEX_HTML,
            trajectory_path=(
                ROOT
                / "docs"
                / "paired_tinydialogues_mistral_child_trajectories.html"
            ),
        )
        self.assertEqual(summary["guardrail_count"], 8)
        self.assertEqual(
            _codes(findings) - {"TRAJECTORY_HETEROGENEITY_MISSING"}, set()
        )

        with tempfile.TemporaryDirectory(
            prefix=".august-audit-language-", dir=ROOT
        ) as tmp:
            bad = Path(tmp) / "report.md"
            bad.write_text(
                REPORT_MARKDOWN.read_text(encoding="utf-8")
                + "\nHall proves a causal SES deficit.\nRoute 1 is optimal.\n",
                encoding="utf-8",
            )
            findings, _ = audit_scientific_language(
                root=ROOT,
                configuration_path=CONFIGURATION,
                report_path=bad,
                index_path=INDEX_HTML,
                trajectory_path=(
                    ROOT
                    / "docs"
                    / "paired_tinydialogues_mistral_child_trajectories.html"
                ),
            )
            self.assertIn("PROHIBITED_CAUSAL_HALL_LANGUAGE", _codes(findings))
            self.assertIn("PROHIBITED_INTERNAL_LABEL", _codes(findings))

            stripped_report = Path(tmp) / "stripped_report.md"
            stripped_index = Path(tmp) / "stripped_index.html"
            stripped_trajectory = Path(tmp) / "stripped_trajectory.html"
            strip_pattern = re.compile(
                r"heterogen|var(?:y|ies|iation)\s+(?:across|among)\s+"
                r"(?:children|individual)|(?:not|no)\s+(?:one\s+)?universal\s+"
                r"developmental",
                flags=re.IGNORECASE,
            )
            for source, destination in (
                (REPORT_MARKDOWN, stripped_report),
                (INDEX_HTML, stripped_index),
                (
                    ROOT
                    / "docs"
                    / "paired_tinydialogues_mistral_child_trajectories.html",
                    stripped_trajectory,
                ),
            ):
                destination.write_text(
                    strip_pattern.sub(
                        "removed guardrail", source.read_text(encoding="utf-8")
                    ),
                    encoding="utf-8",
                )
            findings, _ = audit_scientific_language(
                root=ROOT,
                configuration_path=CONFIGURATION,
                report_path=stripped_report,
                index_path=stripped_index,
                trajectory_path=stripped_trajectory,
            )
            self.assertIn("TRAJECTORY_HETEROGENEITY_MISSING", _codes(findings))

    def test_two_deterministic_render_hashes_match_frozen_products(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".august-audit-render-", dir=ROOT
        ) as tmp:
            findings, summary = audit_deterministic_renders(
                root=ROOT,
                output_dir=Path(tmp),
                input_dir=INPUT_DIR,
                plot_dir=PLOT_DIR,
                markdown_path=REPORT_MARKDOWN,
                html_path=REPORT_HTML,
                index_path=INDEX_HTML,
            )
            self.assertEqual(_blocking(findings), [], findings)
            self.assertEqual(len(summary["render_runs"]), 2)
            self.assertEqual(
                summary["render_runs"][0]["bundle_sha256"],
                summary["render_runs"][1]["bundle_sha256"],
            )
            self.assertTrue(summary["matches_frozen_products"])

    def test_machine_report_has_required_finding_fields_and_allowlists(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".august-audit-output-", dir=ROOT
        ) as tmp:
            result = run_independent_audit(
                root=ROOT,
                output_dir=Path(tmp),
                include_browser_renders=False,
                allowed_dirty_paths=(
                    "src/august_supervisor/audit.py",
                    "tests/test_august_supervisor_audit.py",
                ),
            )
            self.assertIn(result["verdict"], {"AUDIT_PASS", "AUDIT_FAIL"})
            report_path = Path(tmp) / "audit_report.json"
            findings_path = Path(tmp) / "findings.json"
            self.assertTrue(report_path.is_file())
            self.assertTrue(findings_path.is_file())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            findings = json.loads(findings_path.read_text(encoding="utf-8"))
            self.assertEqual(report["verdict"], result["verdict"])
            self.assertEqual(report["findings_sha256"], result["findings_sha256"])
            required = {
                "severity",
                "code",
                "claim_id",
                "file",
                "evidence",
                "required_action",
                "remediation_file_allowlist",
            }
            for finding in findings:
                self.assertEqual(set(finding), required)
                self.assertIsInstance(finding["remediation_file_allowlist"], list)
                if finding["severity"] in BLOCKING_SEVERITIES:
                    self.assertTrue(finding["remediation_file_allowlist"])

    def test_audit_module_cannot_fit_models_or_generate_plots(self) -> None:
        source = (ROOT / "src" / "august_supervisor" / "audit.py").read_text(
            encoding="utf-8"
        ).lower()
        for prohibited in (
            "statsmodels",
            "matplotlib",
            "seaborn",
            "from .plots import",
            ".fit(",
        ):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
