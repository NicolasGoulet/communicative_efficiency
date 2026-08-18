"""Render the integrated August supervisor report from frozen manifests only."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

from src.render_markdown_report import render_markdown_file

from .contracts import (
    ContractError,
    atomic_write_json,
    sha256_file,
    verify_stage_manifest,
    write_stage_manifest,
)
from .sections import (
    DEFAULT_INPUT_DIR,
    DEFAULT_PLOT_DIR,
    ReportEvidence,
    ReportSection,
    build_report_sections,
    load_report_evidence,
)


DEFAULT_MARKDOWN_PATH = Path("docs/august_supervisor_report.md")
DEFAULT_HTML_PATH = Path("docs/august_supervisor_report.html")
DEFAULT_MANIFEST_PATH = DEFAULT_INPUT_DIR / "report_manifest.json"
DEFAULT_TRACE_PATH = DEFAULT_INPUT_DIR / "report_trace.json"

STATUS_DEFINITIONS = (
    ("Supported", "The frozen estimate and uncertainty support the registered reading."),
    ("Qualified", "The direction or scoped association is informative, but a stated gate limits promotion."),
    ("Contrary", "The result runs opposite to the preregistered or frozen directional prediction."),
    ("Descriptive", "The comparison is explicitly non-causal and outside longitudinal confirmation."),
    ("Pending", "The required evidence or validation has not yet been completed."),
)


def _rooted(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ContractError(f"report output is outside repository root: {path}") from error
    return resolved


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as error:
        raise ContractError(f"report path is outside repository root: {path}") from error


def _relative_link(target: Path, report_parent: Path) -> str:
    return Path(os.path.relpath(target, start=report_parent)).as_posix()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _render_figure(
    evidence: ReportEvidence, figure_id: str, *, report_parent: Path
) -> list[str]:
    figure = evidence.figures[figure_id]
    image_path = evidence.root / figure.image_path
    link = _relative_link(image_path, report_parent)
    return [
        f"![{figure.alt_text}]({link})",
        "",
        f"*Figure caption.* {figure.caption}",
    ]


def _render_sources(
    evidence: ReportEvidence,
    page_ids: tuple[str, ...],
    *,
    report_parent: Path,
) -> list[str]:
    if not page_ids:
        return []
    pages = sorted(
        (evidence.pages[page_id] for page_id in page_ids),
        key=lambda page: (page.display_order, page.page_id),
    )
    lines = ["### Technical companions", ""]
    for page in pages:
        target = evidence.root / page.output_path
        lines.append(
            f"- [{page.title}]({_relative_link(target, report_parent)})"
        )
        lines.append("")
    if lines[-1] == "":
        lines.pop()
    return lines


def render_report_markdown(
    evidence: ReportEvidence,
    sections: tuple[ReportSection, ...],
    *,
    markdown_path: Path,
) -> str:
    """Return deterministic, supervisor-facing Markdown."""

    lines = [
        "# August 2026 supervisor report",
        "",
        (
            "This report integrates the frozen longitudinal, word-level, generated-"
            "reference, corrected candidate-set Bayes, response-uncertainty, onset, "
            "and Hall evidence. It states the estimand and evidence status for each "
            "claim and leaves missing analyses pending."
        ),
        "",
    ]
    for section_index, section in enumerate(sections):
        lines.extend([f"## {section.title}", "", section.lead, ""])
        if section_index == 0:
            lines.extend(
                [
                    "| Evidence label | Meaning in this report |",
                    "|---|---|",
                    *(
                        f"| {label} | {definition} |"
                        for label, definition in STATUS_DEFINITIONS
                    ),
                    "",
                ]
            )
        for statement in section.statements:
            label = statement.status.title()
            lines.extend([f"**{label}.** {statement.text}", ""])
        for figure_id in section.figure_ids:
            lines.extend(_render_figure(evidence, figure_id, report_parent=markdown_path.parent))
            lines.append("")
        source_lines = _render_sources(
            evidence, section.source_page_ids, report_parent=markdown_path.parent
        )
        if source_lines:
            lines.extend(source_lines)
            lines.append("")

    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def _input_snapshot(evidence: ReportEvidence) -> dict[str, str]:
    paths = (
        evidence.input_dir / "headline_findings.csv",
        evidence.input_dir / "supporting_findings.csv",
        evidence.input_dir / "coverage_and_limitations.csv",
        evidence.input_dir / "page_registry.csv",
        evidence.input_dir / "synthesis_manifest.json",
        evidence.plot_dir / "figure_manifest.csv",
        evidence.plot_manifest_path,
    )
    return dict(
        sorted(
            (
                _relative_to_root(path, evidence.root),
                sha256_file(path),
            )
            for path in paths
        )
    )


def _trace_payload(
    evidence: ReportEvidence,
    sections: tuple[ReportSection, ...],
    *,
    markdown_path: Path,
    html_path: Path,
    input_hashes: dict[str, str],
) -> dict[str, Any]:
    section_records = []
    for section in sections:
        claim_ids = sorted(
            {
                claim_id
                for statement in section.statements
                for claim_id in statement.claim_ids
            }
        )
        statuses = sorted(
            {statement.status for statement in section.statements}
        )
        section_records.append(
            {
                "section_id": section.section_id,
                "title": section.title,
                "claim_ids": claim_ids,
                "statuses": statuses,
                "figure_ids": list(section.figure_ids),
                "source_page_ids": list(section.source_page_ids),
            }
        )
    return {
        "schema_version": "1.0.0",
        "stage_id": "report",
        "status": "PASS",
        "input_hashes": input_hashes,
        "resolved_claim_ids": sorted(evidence.claims),
        "pending_claim_ids": sorted(
            claim_id
            for claim_id, claim in evidence.claims.items()
            if claim.classification == "PENDING"
        ),
        "figure_ids": sorted(evidence.figures),
        "source_page_ids": sorted(
            page_id
            for page_id, page in evidence.pages.items()
            if page.page_status == "READY"
        ),
        "sections": section_records,
        "outputs": {
            "markdown": {
                "path": _relative_to_root(markdown_path, evidence.root),
                "sha256": sha256_file(markdown_path),
            },
            "html": {
                "path": _relative_to_root(html_path, evidence.root),
                "sha256": sha256_file(html_path),
            },
        },
    }


def build_supervisor_report(
    *,
    root: Path | str,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
    plot_dir: Path | str = DEFAULT_PLOT_DIR,
    markdown_path: Path | str = DEFAULT_MARKDOWN_PATH,
    html_path: Path | str = DEFAULT_HTML_PATH,
    manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
    trace_path: Path | str = DEFAULT_TRACE_PATH,
    plot_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build Markdown, lightweight HTML, trace, and chained PASS manifest."""

    base = Path(root).resolve()
    markdown_file = _rooted(markdown_path, base)
    html_file = _rooted(html_path, base)
    manifest_file = _rooted(manifest_path, base)
    trace_file = _rooted(trace_path, base)
    outputs = (markdown_file, html_file, trace_file, manifest_file)
    if len(outputs) != len(set(outputs)):
        raise ContractError("report output paths must be distinct")

    evidence = load_report_evidence(
        root=base,
        input_dir=input_dir,
        plot_dir=plot_dir,
        plot_manifest_path=plot_manifest_path,
    )
    before = _input_snapshot(evidence)
    sections = build_report_sections(evidence)
    markdown = render_report_markdown(
        evidence, sections, markdown_path=markdown_file
    )
    _atomic_write_text(markdown_file, markdown)

    html_file.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{html_file.name}.", suffix=".html", dir=html_file.parent
    )
    os.close(descriptor)
    temporary_html = Path(temporary_name)
    try:
        render_markdown_file(
            markdown_file,
            temporary_html,
            title="August 2026 Supervisor Report",
            embed_images=False,
        )
        os.replace(temporary_html, html_file)
    finally:
        temporary_html.unlink(missing_ok=True)

    after = _input_snapshot(evidence)
    if before != after:
        raise ContractError("frozen report inputs changed during rendering")

    trace = _trace_payload(
        evidence,
        sections,
        markdown_path=markdown_file,
        html_path=html_file,
        input_hashes=before,
    )
    atomic_write_json(trace_file, trace)
    manifest = write_stage_manifest(
        manifest_file,
        stage_id="report",
        artifact_paths=[markdown_file, html_file, trace_file],
        upstream_manifest_paths=[evidence.plot_manifest_path],
        root=base,
    )
    verify_stage_manifest(manifest_file, root=base, expected_stage="report")

    artifact_paths = (markdown_file, html_file, trace_file, manifest_file)
    return {
        "status": "PASS",
        "stage": "report",
        "section_count": len(sections),
        "claim_count": len(evidence.claims),
        "figure_count": len(evidence.figures),
        "source_link_count": sum(
            page.page_status == "READY" for page in evidence.pages.values()
        ),
        "pending_claim_ids": trace["pending_claim_ids"],
        "artifact_sha256": {
            _relative_to_root(path, base): sha256_file(path)
            for path in sorted(artifact_paths)
        },
        "manifest": manifest,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--plot-dir", type=Path, default=DEFAULT_PLOT_DIR)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE_PATH)
    parser.add_argument("--plot-manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = build_supervisor_report(
        root=args.root,
        input_dir=args.input_dir,
        plot_dir=args.plot_dir,
        markdown_path=args.markdown,
        html_path=args.html,
        manifest_path=args.manifest,
        trace_path=args.trace,
        plot_manifest_path=args.plot_manifest,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
