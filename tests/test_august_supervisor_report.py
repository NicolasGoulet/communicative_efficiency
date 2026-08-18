"""Focused tests for the integrated August supervisor report."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from src.august_supervisor.contracts import (
    ContractError,
    verify_stage_manifest,
)
from src.august_supervisor.render import build_supervisor_report
from src.august_supervisor.sections import (
    REQUIRED_SECTION_TITLES,
    build_report_sections,
    load_report_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "results" / "august_supervisor_report"
PLOT_DIR = INPUT_DIR / "plots"


class AugustSupervisorReportTests(unittest.TestCase):
    def test_report_refuses_a_changed_plot_manifest(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".august-report-test-", dir=ROOT
        ) as tmp:
            bad_manifest = Path(tmp) / "plot_manifest.json"
            shutil.copy2(PLOT_DIR / "plot_manifest.json", bad_manifest)
            payload = json.loads(bad_manifest.read_text(encoding="utf-8"))
            payload["manifest_sha256"] = "0" * 64
            bad_manifest.write_text(
                json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ContractError, "manifest payload changed"):
                load_report_evidence(
                    root=ROOT,
                    input_dir=INPUT_DIR,
                    plot_dir=PLOT_DIR,
                    plot_manifest_path=bad_manifest,
                )

    def test_sections_resolve_every_claim_and_keep_scopes_separate(self) -> None:
        evidence = load_report_evidence(
            root=ROOT, input_dir=INPUT_DIR, plot_dir=PLOT_DIR
        )
        sections = build_report_sections(evidence)

        self.assertEqual(
            tuple(section.title for section in sections), REQUIRED_SECTION_TITLES
        )
        resolved = {
            claim_id
            for section in sections
            for statement in section.statements
            for claim_id in statement.claim_ids
        }
        self.assertEqual(resolved, set(evidence.claims))
        self.assertEqual(
            {claim.classification for claim in evidence.claims.values()},
            {"SUPPORTED", "QUALIFIED", "CONTRARY", "DESCRIPTIVE", "PENDING"},
        )

        for section in sections:
            for statement in section.statements:
                for claim_id in statement.claim_ids:
                    self.assertIn(claim_id, evidence.claims)
                if re.search(r"\d", statement.text) or statement.status is not None:
                    self.assertTrue(statement.claim_ids, statement.text)
                    if statement.status is not None:
                        self.assertEqual(
                            {evidence.claims[item].classification for item in statement.claim_ids},
                            {statement.status},
                        )

        hall_sections = {
            section.title
            for section in sections
            for statement in section.statements
            if any(claim_id.startswith("HALL_") for claim_id in statement.claim_ids)
        }
        self.assertEqual(hall_sections, {"Hall: a separate historical snapshot"})

        fixed_effort = next(
            section
            for section in sections
            if section.title == "Utterance predictability at fixed effort"
        )
        fixed_claims = {
            claim_id
            for statement in fixed_effort.statements
            for claim_id in statement.claim_ids
        }
        self.assertIn("DIRECT_PBM_MISTRAL_CONTEXTUAL", fixed_claims)
        self.assertIn("DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY", fixed_claims)
        self.assertIn("DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP", fixed_claims)

    def test_outputs_have_guardrails_figures_sources_and_stable_bytes(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix=".august-report-test-", dir=ROOT
        ) as tmp:
            output_dir = Path(tmp)
            markdown_path = output_dir / "august_supervisor_report.md"
            html_path = output_dir / "august_supervisor_report.html"
            manifest_path = output_dir / "report_manifest.json"
            trace_path = output_dir / "report_trace.json"

            first = build_supervisor_report(
                root=ROOT,
                input_dir=INPUT_DIR,
                plot_dir=PLOT_DIR,
                markdown_path=markdown_path,
                html_path=html_path,
                manifest_path=manifest_path,
                trace_path=trace_path,
            )
            first_bytes = {
                path.name: path.read_bytes()
                for path in (markdown_path, html_path, manifest_path, trace_path)
            }
            second = build_supervisor_report(
                root=ROOT,
                input_dir=INPUT_DIR,
                plot_dir=PLOT_DIR,
                markdown_path=markdown_path,
                html_path=html_path,
                manifest_path=manifest_path,
                trace_path=trace_path,
            )

            self.assertEqual(first["status"], "PASS")
            self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])
            for path in (markdown_path, html_path, manifest_path, trace_path):
                self.assertEqual(first_bytes[path.name], path.read_bytes(), path.name)

            markdown = markdown_path.read_text(encoding="utf-8")
            html = html_path.read_text(encoding="utf-8")
            lower = markdown.lower()
            self.assertNotIn("route 1", lower)
            self.assertNotIn("route 2", lower)
            self.assertNotIn("surprisal is listener utility", lower)
            self.assertNotIn("hall is a causal", lower)
            self.assertIn("not confirmed", lower)
            self.assertIn("not listener utility", lower)
            self.assertIn("not semantic uncertainty", lower)
            self.assertIn("not a causal ses effect", lower)
            self.assertIn(
                "individual profiles do not establish one universal developmental law",
                lower,
            )
            for label in (
                "Supported",
                "Qualified",
                "Contrary",
                "Descriptive",
                "Pending",
            ):
                self.assertIn(f"**{label}.**", markdown)

            evidence = load_report_evidence(
                root=ROOT, input_dir=INPUT_DIR, plot_dir=PLOT_DIR
            )
            for figure in evidence.figures.values():
                relative = Path(
                    Path(figure.image_path).relative_to(".")
                    if figure.image_path.startswith("./")
                    else figure.image_path
                )
                expected = Path(
                    os.path.relpath(ROOT / relative, start=markdown_path.parent)
                ).as_posix()
                self.assertIn(f"]({expected})", markdown)
                self.assertIn(figure.alt_text, markdown)
                self.assertIn(f'src="{expected}"', html)

            ready_pages = [
                page for page in evidence.pages.values() if page.page_status == "READY"
            ]
            self.assertEqual(len(ready_pages), 8)
            for page in ready_pages:
                expected = Path(
                    os.path.relpath(
                        ROOT / page.output_path, start=markdown_path.parent
                    )
                ).as_posix()
                self.assertIn(f"]({expected})", markdown)
                self.assertIn(f'href="{expected}"', html)
                self.assertTrue((ROOT / page.output_path).is_file())

            self.assertTrue(html.startswith("<!doctype html>"))
            self.assertNotIn("data:image/", html)
            self.assertLess(len(html.encode("utf-8")), 150_000)
            manifest = verify_stage_manifest(
                manifest_path, root=ROOT, expected_stage="report"
            )
            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(manifest["upstream_manifests"][0]["stage_id"], "plots")
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            self.assertEqual(set(trace["resolved_claim_ids"]), set(evidence.claims))
            self.assertEqual(
                trace["pending_claim_ids"],
                sorted(
                    claim_id
                    for claim_id, claim in evidence.claims.items()
                    if claim.classification == "PENDING"
                ),
            )

    def test_report_module_has_no_analysis_or_plotting_dependencies(self) -> None:
        source = "\n".join(
            (ROOT / path).read_text(encoding="utf-8").lower()
            for path in (
                "src/august_supervisor/sections.py",
                "src/august_supervisor/render.py",
            )
        )
        for prohibited in (
            "statsmodels",
            "matplotlib",
            "seaborn",
            ".fit(",
            "effect_registry.csv",
            "sample_registry.csv",
            "model_inventory.csv",
        ):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
