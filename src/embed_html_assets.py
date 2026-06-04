#!/usr/bin/env python3
"""Embed local image assets into an existing HTML report.

The local and embedded reports are intentionally generated from the same HTML.
This script only rewrites image ``src`` attributes that point to local files,
turning them into data URIs so the HTML can be emailed as one heavy file.
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
from pathlib import Path
from typing import Sequence
from urllib.parse import unquote, urlparse


IMG_SRC_RE = re.compile(r'(<img\b[^>]*\bsrc=")([^"]+)(")', re.IGNORECASE)


def is_embeddable_local_src(src: str) -> bool:
    """Return whether an HTML image src should be embedded."""

    parsed = urlparse(src)
    return parsed.scheme in {"", "file"} and not src.startswith("data:")


def resolve_src(src: str, html_path: Path) -> Path:
    """Resolve one image src relative to the HTML file."""

    parsed = urlparse(src)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    return (html_path.parent / unquote(parsed.path)).resolve()


def image_data_uri(path: Path) -> str:
    """Return a base64 data URI for one image file."""

    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def embed_html_assets(input_html: Path, output_html: Path) -> tuple[int, list[Path]]:
    """Embed local image references from input_html into output_html."""

    source = input_html.read_text(encoding="utf-8")
    embedded_paths: list[Path] = []

    def replace(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        if not is_embeddable_local_src(src):
            return match.group(0)
        image_path = resolve_src(src, input_html)
        if not image_path.exists():
            raise FileNotFoundError(f"Image referenced by {input_html} does not exist: {src}")
        embedded_paths.append(image_path)
        return f"{prefix}{image_data_uri(image_path)}{suffix}"

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(IMG_SRC_RE.sub(replace, source), encoding="utf-8")
    return len(embedded_paths), embedded_paths


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_html", type=Path)
    parser.add_argument("output_html", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    count, paths = embed_html_assets(args.input_html, args.output_html)
    print(f"[OK] Wrote {args.output_html}")
    print(f"[OK] Embedded images: {count}")
    for path in paths:
        print(f"  - {path}")


if __name__ == "__main__":
    main()
