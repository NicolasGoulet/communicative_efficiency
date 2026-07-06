#!/usr/bin/env python3
"""Build the July Meeting index and blank section pages."""

from __future__ import annotations

import argparse
import html
from pathlib import Path


DOC_DIR = Path("docs")

INDEX_HTML = DOC_DIR / "july_meeting_index.html"

PAGES = [
    ("Used Data", DOC_DIR / "july_meeting_used_data.html"),
    ("Definitions", DOC_DIR / "july_meeting_definitions.html"),
    ("Predicting Utterance Informativeness", DOC_DIR / "july_meeting_predicting_utterance_informativeness.html"),
    ("Predicting Utterance Production Effort", DOC_DIR / "july_meeting_predicting_utterance_production_effort.html"),
    (
        "Developmental Trajectory of Communicative Efficiency",
        DOC_DIR / "july_meeting_developmental_trajectory_communicative_efficiency.html",
    ),
]

CSS = """
body { margin: 0; background: #eef2f1; color: #1e2528; font: 17px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 920px; margin: 48px auto; padding: 42px 48px; background: white; box-shadow: 0 18px 50px rgba(31, 45, 48, .12); }
h1 { margin-top: 0; border-bottom: 3px solid #2f6f73; padding-bottom: .35em; }
.links { display: grid; gap: 16px; margin-top: 28px; }
a.card { display: block; padding: 18px 20px; border: 1px solid #d9e0df; border-radius: 8px; color: inherit; text-decoration: none; background: #fafbfb; }
a.card:hover { border-color: #2f6f73; background: #f3f8f7; }
.title { font-weight: 700; font-size: 1.12rem; color: #2f6f73; }
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
            f'<a class="card" href="{html.escape(relative_doc_path(path), quote=True)}">'
            f'<div class="title">{html.escape(title)}</div>'
            "</a>"
        )
        for title, path in PAGES
    )
    body = "\n".join(["<h1>July Meeting</h1>", '<div class="links">', cards, "</div>"])
    INDEX_HTML.write_text(html_document(title="July Meeting", body=body), encoding="utf-8")


def build_blank_pages() -> None:
    """Build blank section shells with titles only."""

    DOC_DIR.mkdir(parents=True, exist_ok=True)
    for title, path in PAGES:
        body = f"<h1>{html.escape(title)}</h1>"
        path.write_text(html_document(title=title, body=body), encoding="utf-8")


def build_all() -> list[Path]:
    """Build all July Meeting files and return their paths."""

    build_blank_pages()
    build_index()
    return [INDEX_HTML, *[path for _, path in PAGES]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    for path in build_all():
        print(f"[OK] {path}")


if __name__ == "__main__":
    main()
