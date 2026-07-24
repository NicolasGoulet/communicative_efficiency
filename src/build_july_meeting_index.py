#!/usr/bin/env python3
"""Build the July supervisor-report index and section pages."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
from pathlib import Path

try:  # Support both ``python src/...`` and package imports in tests.
    from .july_formal_definitions import (
        FORMAL_DEFINITIONS_MARKDOWN,
        FORMAL_DEFINITIONS_MD_PATH,
        formal_definitions_html,
    )
except ImportError:  # pragma: no cover - exercised by the script entry point
    from july_formal_definitions import (
        FORMAL_DEFINITIONS_MARKDOWN,
        FORMAL_DEFINITIONS_MD_PATH,
        formal_definitions_html,
    )


DOC_DIR = Path("docs")

INDEX_HTML = DOC_DIR / "july_meeting_index.html"
FORMAL_DEFINITIONS_HTML = DOC_DIR / "july_meeting_definitions.html"


@dataclass(frozen=True)
class ReportPage:
    """One page on the July report landing screen."""

    title: str
    path: Path
    description: str

PAGES = [
    ReportPage(
        "Interactive Direct-Surprisal Results Explorer",
        DOC_DIR / "direct_surprisal_results_explorer.html",
        "Start here: filter the fitted models, inspect exact formulas and interpretations, enlarge plots, and find any child's trajectory.",
    ),
    ReportPage(
        "Used Data",
        DOC_DIR / "july_meeting_used_data.html",
        "Corpora, participants, longitudinal coverage, and analysis samples.",
    ),
    ReportPage(
        "Formal Mathematical Definitions",
        FORMAL_DEFINITIONS_HTML,
        "Paper-ready notation for surprisal, entropy, Bayes information, effort, baselines, and efficiency estimands.",
    ),
    ReportPage(
        "Corrected Bayes-Derived PBM Results",
        DOC_DIR / "corrected_pbm_bayes_report.html",
        "Leave-corpus-out, age-additive candidate scoring with validated context evidence and comparison to direct Mistral surprisal.",
    ),
    ReportPage(
        "Predicting Utterance Informativeness",
        DOC_DIR / "july_meeting_predicting_utterance_informativeness.html",
        "Developmental models of total utterance information at fixed production effort.",
    ),
    ReportPage(
        "Predicting Utterance Production Effort",
        DOC_DIR / "july_meeting_predicting_utterance_production_effort.html",
        "Production effort relative to the distribution of contextually plausible responses.",
    ),
    ReportPage(
        "Developmental Trajectory of Communicative Efficiency",
        DOC_DIR / "july_meeting_developmental_trajectory_communicative_efficiency.html",
        "Synthesis of informativeness, production effort, and developmental change.",
    ),
]

CSS = """
body { margin: 0; background: #eef2f1; color: #1e2528; font: 17px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 920px; margin: 48px auto; padding: 42px 48px; background: white; box-shadow: 0 18px 50px rgba(31, 45, 48, .12); }
h1 { margin-top: 0; border-bottom: 3px solid #2f6f73; padding-bottom: .35em; }
.intro { color: #536267; max-width: 740px; }
.links { display: grid; gap: 16px; margin-top: 32px; }
a.card { display: block; padding: 20px 22px; border: 1px solid #d9e0df; border-radius: 8px; color: inherit; text-decoration: none; background: #fafbfb; }
a.card:hover { border-color: #2f6f73; background: #f3f8f7; }
.title { font-weight: 700; font-size: 1.12rem; color: #2f6f73; }
.description { margin-top: 5px; color: #5b696d; font-size: .95rem; }
"""


def relative_doc_path(path: Path) -> str:
    """Return a POSIX path from the docs directory."""

    return path.relative_to(DOC_DIR).as_posix()


def html_document(*, title: str, body: str) -> str:
    """Return a complete styled HTML document."""

    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escaped_title}</title>
<style>{CSS}</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def build_index() -> None:
    """Build the July Meeting landing page."""

    DOC_DIR.mkdir(parents=True, exist_ok=True)
    cards = "\n".join(
        (
            f'<a class="card" href="{html.escape(relative_doc_path(page.path), quote=True)}">'
            f'<div class="title">{html.escape(page.title)}</div>'
            f'<div class="description">{html.escape(page.description)}</div>'
            "</a>"
        )
        for page in PAGES
    )
    body = "\n".join(
        [
            "<h1>July Report</h1>",
            '<p class="intro">Supervisor-facing materials on communicative efficiency in child language use.</p>',
            '<div class="links">',
            cards,
            "</div>",
        ]
    )
    INDEX_HTML.write_text(html_document(title="July Report", body=body), encoding="utf-8")


def build_section_shells() -> None:
    """Create missing section shells without overwriting report content."""

    DOC_DIR.mkdir(parents=True, exist_ok=True)
    for page in PAGES:
        if page.path == FORMAL_DEFINITIONS_HTML or page.path.exists():
            continue
        body = f"<h1>{html.escape(page.title)}</h1>"
        page.path.write_text(html_document(title=page.title, body=body), encoding="utf-8")


def build_formal_definitions() -> list[Path]:
    """Write the paper-ready HTML and copyable Markdown definitions."""

    DOC_DIR.mkdir(parents=True, exist_ok=True)
    FORMAL_DEFINITIONS_HTML.write_text(formal_definitions_html(), encoding="utf-8")
    FORMAL_DEFINITIONS_MD_PATH.write_text(FORMAL_DEFINITIONS_MARKDOWN, encoding="utf-8")
    return [FORMAL_DEFINITIONS_HTML, FORMAL_DEFINITIONS_MD_PATH]


def build_all() -> list[Path]:
    """Build all July Meeting files and return their paths."""

    build_section_shells()
    definition_paths = build_formal_definitions()
    build_index()
    other_pages = [page.path for page in PAGES if page.path != FORMAL_DEFINITIONS_HTML]
    return [INDEX_HTML, *definition_paths, *other_pages]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    for path in build_all():
        print(f"[OK] {path}")


if __name__ == "__main__":
    main()
