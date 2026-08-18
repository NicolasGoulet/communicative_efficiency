"""Focused tests for the August supervisor consultation landing page."""

from __future__ import annotations

import html
import re
import tempfile
import unittest
from pathlib import Path

from src.august_supervisor.contracts import ContractError, sha256_file
from src.august_supervisor.index import (
    ARCHIVE_DESTINATIONS,
    EXECUTIVE_CARD_SPECS,
    FEATURED_FIGURE_ID,
    REQUIRED_DESTINATIONS,
    STATUS_DEFINITIONS,
    audit_local_references,
    build_supervisor_index,
    load_index_evidence,
    validate_page_registry,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "results" / "august_supervisor_report"
PLOT_DIR = INPUT_DIR / "plots"


def _hrefs(source: str) -> list[tuple[str, str]]:
    return [
        (href, re.sub(r"<[^>]+>", "", label).strip())
        for href, label in re.findall(
            r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', source, flags=re.DOTALL
        )
    ]


class AugustSupervisorIndexTests(unittest.TestCase):
    def _build(self, directory: Path) -> tuple[Path, dict[str, object]]:
        output = directory / "nested" / "august_supervisor_index.html"
        result = build_supervisor_index(
            root=ROOT,
            input_dir=INPUT_DIR,
            plot_dir=PLOT_DIR,
            html_path=output,
        )
        return output, result

    def test_page_registry_validation_rejects_destination_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".august-index-test-", dir=ROOT) as tmp:
            registry = Path(tmp) / "page_registry.csv"
            source = (INPUT_DIR / "page_registry.csv").read_text(encoding="utf-8")
            registry.write_text(
                source.replace(
                    "docs/direct_surprisal_results_explorer.html",
                    "docs/not_the_frozen_explorer.html",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "page registry destination drift"):
                validate_page_registry(registry, root=ROOT)

    def test_required_destinations_are_registry_driven_and_archives_are_separate(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".august-index-test-", dir=ROOT) as tmp:
            output, result = self._build(Path(tmp))
            source = output.read_text(encoding="utf-8")
            hrefs = _hrefs(source)
            resolved = {
                (output.parent / href.split("#", 1)[0]).resolve()
                for href, _ in hrefs
                if href and not href.startswith("#")
            }
            expected = {
                (ROOT / path).resolve()
                for path in (*REQUIRED_DESTINATIONS.values(), *ARCHIVE_DESTINATIONS.values())
            }
            self.assertLessEqual(expected, resolved)
            self.assertEqual(result["current_destination_count"], len(REQUIRED_DESTINATIONS))
            self.assertIn('<section id="current-resources"', source)
            self.assertIn('<section id="archives"', source)
            archives = source.split('<section id="archives"', 1)[1].split(
                "</section>", 1
            )[0]
            current = source.split('<section id="current-resources"', 1)[1].split(
                "</section>", 1
            )[0]
            for path in ARCHIVE_DESTINATIONS.values():
                name = Path(path).name
                self.assertIn(name, archives)
                self.assertNotIn(name, current)
            for href, label in hrefs:
                self.assertNotIn(label.lower(), {"here", "click here", "read more"})

    def test_all_relative_links_and_fragments_resolve(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".august-index-test-", dir=ROOT) as tmp:
            output, result = self._build(Path(tmp))
            audit = audit_local_references(output, root=ROOT)
            self.assertEqual(audit, result["link_audit"])
            self.assertGreaterEqual(audit["local_link_count"], 12)
            self.assertGreaterEqual(audit["fragment_count"], 3)
            source = output.read_text(encoding="utf-8")
            output.write_text(
                source.replace('href="#current-resources"', 'href="#missing-fragment"', 1),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "missing HTML fragment"):
                audit_local_references(output, root=ROOT)

    def test_featured_image_is_hash_locked_and_accessible(self) -> None:
        evidence = load_index_evidence(
            root=ROOT, input_dir=INPUT_DIR, plot_dir=PLOT_DIR
        )
        figure = evidence.report.figures[FEATURED_FIGURE_ID]
        self.assertEqual(sha256_file(ROOT / figure.image_path), figure.image_sha256)
        with tempfile.TemporaryDirectory(prefix=".august-index-test-", dir=ROOT) as tmp:
            output, result = self._build(Path(tmp))
            source = output.read_text(encoding="utf-8")
            self.assertEqual(result["link_audit"]["image_count"], 1)
            self.assertIn(f'alt="{html.escape(figure.alt_text, quote=True)}"', source)
            self.assertNotIn("data:image/", source)
            with self.assertRaisesRegex(ContractError, "image hash verification failed"):
                audit_local_references(
                    output,
                    root=ROOT,
                    expected_image_hashes={figure.image_path: "0" * 64},
                )

    def test_status_vocabulary_and_five_cards_resolve_to_frozen_claims(self) -> None:
        evidence = load_index_evidence(
            root=ROOT, input_dir=INPUT_DIR, plot_dir=PLOT_DIR
        )
        self.assertEqual(
            tuple(status for status, _, _ in STATUS_DEFINITIONS),
            ("SUPPORTED", "QUALIFIED", "CONTRARY", "DESCRIPTIVE", "PENDING"),
        )
        self.assertEqual(len(EXECUTIVE_CARD_SPECS), 5)
        self.assertEqual(
            {spec.status for spec in EXECUTIVE_CARD_SPECS},
            {"SUPPORTED", "QUALIFIED", "CONTRARY", "DESCRIPTIVE", "PENDING"},
        )
        for spec in EXECUTIVE_CARD_SPECS:
            self.assertIn(spec.claim_id, evidence.report.claims)
            self.assertEqual(
                evidence.report.claims[spec.claim_id].classification, spec.status
            )

        with tempfile.TemporaryDirectory(prefix=".august-index-test-", dir=ROOT) as tmp:
            output, _ = self._build(Path(tmp))
            source = output.read_text(encoding="utf-8")
            cards = re.findall(
                r'<article class="result-card [^"]+" data-status="([A-Z]+)" '
                r'data-claim-id="([A-Z0-9_]+)">',
                source,
            )
            self.assertEqual(len(cards), 5)
            self.assertEqual(set(cards), {(spec.status, spec.claim_id) for spec in EXECUTIVE_CARD_SPECS})
            for _, label, definition in STATUS_DEFINITIONS:
                self.assertIn(html.escape(label), source)
                self.assertIn(html.escape(definition), source)

    def test_html_is_deterministic_and_not_an_empty_shell(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".august-index-test-", dir=ROOT) as tmp:
            output, first = self._build(Path(tmp))
            first_bytes = output.read_bytes()
            _, second = self._build(Path(tmp))
            self.assertEqual(first_bytes, output.read_bytes())
            self.assertEqual(first["page_sha256"], second["page_sha256"])
            source = output.read_text(encoding="utf-8")
            self.assertTrue(source.startswith("<!doctype html>"))
            self.assertIn('<main id="main-content"', source)
            self.assertIn('class="skip-link"', source)
            self.assertIn(":focus-visible", source)
            self.assertIn("@media (max-width: 720px)", source)
            self.assertIn('role="note"', source)
            self.assertGreater(len(re.sub(r"<[^>]+>", " ", source).split()), 250)
            self.assertLess(len(first_bytes), 100_000)

    def test_index_module_has_no_analysis_or_plotting_dependencies(self) -> None:
        source = (ROOT / "src/august_supervisor/index.py").read_text(
            encoding="utf-8"
        ).lower()
        for prohibited in ("statsmodels", "matplotlib", "seaborn", ".fit("):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
