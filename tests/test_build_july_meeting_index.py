import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import build_july_meeting_index as builder
from src.july_formal_definitions import (
    FORMAL_DEFINITIONS_MARKDOWN,
    formal_definitions_html,
)


class JulyMeetingReportTests(unittest.TestCase):
    def test_formal_page_covers_implemented_quantity_boundaries(self):
        report = formal_definitions_html()

        required_phrases = [
            "Target-only accounting",
            "Context-only next-token uncertainty",
            "Miller&ndash;Madow",
            "bayes_bits_unnormalized",
            "Normalization caveat",
            "Developmentally constrained reference generators",
            "Regression estimands for communicative efficiency",
            "fixed effort",
            "not exact posterior surprisal",
            "Corrected cross-fitted score",
            "candidate_set_probability",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, report)

        self.assertIn("&alpha;=0.1", report)
        self.assertIn("Current supervisor model family (23)", report)
        self.assertIn("H</i><sub>next,i</sub>", report)

    def test_markdown_is_copyable_latex_and_states_bayes_identity(self):
        self.assertIn(r"p(u_i\mid c_i)=\frac{p(c_i\mid u_i)p(u_i)}{p(c_i)}", FORMAL_DEFINITIONS_MARKDOWN)
        self.assertIn(r"\widetilde I_{\mathrm{Bayes}}", FORMAL_DEFINITIONS_MARKDOWN)
        self.assertIn(r"\widehat H_{\mathrm{MM}}", FORMAL_DEFINITIONS_MARKDOWN)
        self.assertIn(r"\beta_NH_{\mathrm{next},i}^c", FORMAL_DEFINITIONS_MARKDOWN)
        self.assertNotRegex(FORMAL_DEFINITIONS_MARKDOWN, r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

    def test_index_promotes_formal_definitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = [
                builder.ReportPage(
                    "Formal Mathematical Definitions",
                    root / "definitions.html",
                    "Paper-ready mathematical notation.",
                )
            ]
            with (
                mock.patch.object(builder, "DOC_DIR", root),
                mock.patch.object(builder, "INDEX_HTML", root / "index.html"),
                mock.patch.object(builder, "PAGES", pages),
            ):
                builder.build_index()

            index = (root / "index.html").read_text(encoding="utf-8")
            self.assertIn("July Report", index)
            self.assertIn("Formal Mathematical Definitions", index)
            self.assertIn('href="definitions.html"', index)
            self.assertIn("Paper-ready mathematical notation.", index)

    def test_default_index_promotes_corrected_bayes_report(self):
        bayes_pages = [page for page in builder.PAGES if page.title == "Corrected Bayes-Derived PBM Results"]
        self.assertEqual(len(bayes_pages), 1)
        self.assertEqual(bayes_pages[0].path, Path("docs/corrected_pbm_bayes_report.html"))

    def test_default_index_promotes_direct_surprisal_explorer(self):
        explorer_pages = [
            page
            for page in builder.PAGES
            if page.title == "Interactive Direct-Surprisal Results Explorer"
        ]
        self.assertEqual(len(explorer_pages), 1)
        self.assertEqual(
            explorer_pages[0].path,
            Path("docs/direct_surprisal_results_explorer.html"),
        )

    def test_section_shell_builder_preserves_existing_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "existing.html"
            missing = root / "missing.html"
            definitions = root / "definitions.html"
            existing.write_text("manual report content", encoding="utf-8")
            pages = [
                builder.ReportPage("Existing", existing, ""),
                builder.ReportPage("Missing", missing, ""),
                builder.ReportPage("Formal Mathematical Definitions", definitions, ""),
            ]
            with (
                mock.patch.object(builder, "DOC_DIR", root),
                mock.patch.object(builder, "PAGES", pages),
                mock.patch.object(builder, "FORMAL_DEFINITIONS_HTML", definitions),
            ):
                builder.build_section_shells()

            self.assertEqual(existing.read_text(encoding="utf-8"), "manual report content")
            self.assertIn("<h1>Missing</h1>", missing.read_text(encoding="utf-8"))
            self.assertFalse(definitions.exists())

    def test_rendered_definition_links_are_local_and_present(self):
        report_path = Path("docs/july_meeting_definitions.html")
        report = report_path.read_text(encoding="utf-8")
        hrefs = re.findall(r'href="([^"]+)"', report)

        self.assertGreaterEqual(len(hrefs), 12)
        missing = []
        for href in hrefs:
            if href.startswith("#"):
                self.assertIn(f'id="{href[1:]}"', report)
            elif not (report_path.parent / href).exists():
                missing.append(href)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
