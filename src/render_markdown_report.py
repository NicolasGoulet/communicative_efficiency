"""Render a lightweight project Markdown report to standalone HTML.

This intentionally avoids extra dependencies on this laptop. It supports the
Markdown features used by the project reports: headings, paragraphs, tables,
lists, blockquotes, fenced code blocks, images, links, bold text, and inline
code.
"""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import re
from pathlib import Path


REPORT_CSS = """
:root {
  color-scheme: light;
  --ink: #1e2528;
  --muted: #5e686d;
  --line: #d9e0df;
  --paper: #ffffff;
  --soft: #f5f7f6;
  --accent: #2f6f73;
  --accent2: #c76f2c;
}
body {
  margin: 0;
  background: #eef2f1;
  color: var(--ink);
  font: 16px/1.58 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
main {
  max-width: 980px;
  margin: 34px auto 56px;
  padding: 48px 58px;
  background: var(--paper);
  box-shadow: 0 18px 50px rgba(31, 45, 48, 0.12);
}
h1, h2, h3, h4 {
  line-height: 1.18;
  margin: 1.6em 0 0.55em;
}
h1 {
  margin-top: 0;
  font-size: 2.25rem;
  border-bottom: 3px solid var(--accent);
  padding-bottom: 0.45em;
}
h2 {
  font-size: 1.55rem;
  color: var(--accent);
}
h3 {
  font-size: 1.18rem;
}
p {
  margin: 0.75em 0;
}
a {
  color: var(--accent);
}
blockquote {
  border-left: 4px solid var(--accent2);
  margin: 1.1em 0;
  padding: 0.05em 1.1em;
  color: var(--muted);
  background: #fff8f2;
}
code {
  background: var(--soft);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 0.08em 0.3em;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 0.92em;
}
pre {
  background: #f5f7f6;
  color: var(--ink);
  border: 1px solid var(--line);
  padding: 1em;
  overflow-x: auto;
  border-radius: 7px;
}
pre code {
  background: transparent;
  border: 0;
  padding: 0;
  color: inherit;
}
table {
  border-collapse: collapse;
  width: 100%;
  margin: 1.15em 0 1.45em;
  font-size: 0.95em;
}
th, td {
  border: 1px solid var(--line);
  padding: 0.54em 0.68em;
  vertical-align: top;
}
th {
  background: #e7efed;
  text-align: left;
}
tr:nth-child(even) td {
  background: #fafbfb;
}
img {
  max-width: 100%;
  display: block;
  margin: 1.1em auto 0.45em;
}
ul, ol {
  padding-left: 1.4em;
}
.caption {
  color: var(--muted);
  font-size: 0.92em;
  margin-top: -0.15em;
}
@media print {
  body {
    background: white;
  }
  main {
    box-shadow: none;
    margin: 0;
    max-width: none;
    padding: 28px;
  }
}
"""


def render_inline(text: str) -> str:
    """Render simple inline Markdown."""

    placeholders: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        placeholders.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\x00{len(placeholders) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash_code, text)
    text = html.escape(text)
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda match: (
            f'<img src="{html.escape(match.group(2), quote=True)}" '
            f'alt="{html.escape(match.group(1), quote=True)}">'
        ),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: (
            f'<a href="{html.escape(match.group(2), quote=True)}">'
            f"{match.group(1)}</a>"
        ),
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)

    for i, value in enumerate(placeholders):
        text = text.replace(f"\x00{i}\x00", value)
    return text


def is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_table(lines: list[str]) -> str:
    header = split_table_row(lines[0])
    body = [split_table_row(line) for line in lines[2:]]
    out = ["<table>", "<thead><tr>"]
    out.extend(f"<th>{render_inline(cell)}</th>" for cell in header)
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in body:
        out.append("<tr>")
        out.extend(f"<td>{render_inline(cell)}</td>" for cell in row)
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def markdown_to_html(markdown: str) -> str:
    """Convert the subset of Markdown used by these reports to HTML."""

    lines = markdown.splitlines()
    html_lines: list[str] = []
    paragraph: list[str] = []
    list_stack: str | None = None
    in_code = False
    code_lines: list[str] = []
    i = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            html_lines.append(f"<p>{render_inline(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_stack
        if list_stack:
            html_lines.append(f"</{list_stack}>")
            list_stack = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                html_lines.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                in_code = False
            else:
                flush_paragraph()
                close_list()
                in_code = True
                code_lines = []
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            flush_paragraph()
            close_list()
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            html_lines.append(render_table(table_lines))
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            html_lines.append(f"<h{level}>{render_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image:
            flush_paragraph()
            close_list()
            html_lines.append(render_inline(stripped))
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            html_lines.append(f"<blockquote><p>{render_inline(stripped.lstrip('> '))}</p></blockquote>")
            i += 1
            continue

        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if unordered or ordered:
            flush_paragraph()
            desired = "ul" if unordered else "ol"
            if list_stack != desired:
                close_list()
                html_lines.append(f"<{desired}>")
                list_stack = desired
            item = (unordered or ordered).group(1)
            html_lines.append(f"<li>{render_inline(item)}</li>")
            i += 1
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    close_list()
    if in_code:
        html_lines.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")

    return "\n".join(html_lines)


def embed_image_sources(html_text: str, *, base_dir: Path) -> str:
    """Replace local image src attributes with data URIs."""

    def replace(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        raw_src = html.unescape(src)
        if raw_src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        image_path = (base_dir / raw_src).resolve()
        if not image_path.exists() or not image_path.is_file():
            return match.group(0)
        mime = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        data_uri = f"data:{mime};base64,{encoded}"
        return f'{prefix}{html.escape(data_uri, quote=True)}{suffix}'

    return re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)("[^>]*>)', replace, html_text)


def render_markdown_file(input_md: Path, output_html: Path, title: str | None = None, *, embed_images: bool = False) -> None:
    markdown = input_md.read_text(encoding="utf-8")
    body = markdown_to_html(markdown)
    if title is None:
        first_heading = next(
            (line.lstrip("#").strip() for line in markdown.splitlines() if line.startswith("# ")),
            input_md.stem,
        )
        title = first_heading
    html_text = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{html.escape(title)}</title>",
            f"<style>{REPORT_CSS}</style>",
            "</head>",
            "<body>",
            "<main>",
            body,
            "</main>",
            "</body>",
            "</html>",
        ]
    )
    if embed_images:
        html_text = embed_image_sources(html_text, base_dir=output_html.parent)
    output_html.write_text(html_text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a project Markdown report to HTML.")
    parser.add_argument("input_md", type=Path)
    parser.add_argument("output_html", type=Path)
    parser.add_argument("--title", default=None)
    parser.add_argument("--embed-images", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_markdown_file(args.input_md, args.output_html, args.title, embed_images=args.embed_images)
    print(f"[OK] Wrote {args.output_html}")


if __name__ == "__main__":
    main()
