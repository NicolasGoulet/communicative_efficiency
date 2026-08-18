"""Build the August supervisor landing page from frozen report registries.

This stage is deliberately a renderer and navigation audit.  It reads the
hash-chained report inputs, resolves every executive result through a frozen
claim ID, and neither fits models nor creates figures.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import unquote, urlsplit

from .contracts import (
    ContractError,
    read_registry_csv,
    sha256_file,
    verify_stage_manifest,
)
from .sections import (
    DEFAULT_INPUT_DIR,
    DEFAULT_PLOT_DIR,
    PageRecord,
    ReportEvidence,
    load_report_evidence,
)


DEFAULT_HTML_PATH = Path("docs/august_supervisor_index.html")
DEFAULT_REPORT_MANIFEST_PATH = DEFAULT_INPUT_DIR / "report_manifest.json"
FEATURED_FIGURE_ID = "FIGURE_01_FIXED_EFFORT_PREDICTABILITY"


@dataclass(frozen=True)
class RegistryExpectation:
    page_id: str
    page_kind: str
    output_path: str
    page_status: str
    display_order: int


EXPECTED_PAGE_REGISTRY = (
    RegistryExpectation(
        "PAGE_OUTPUT_DOCS_AUGUST_SUPERVISOR_INDEX_HTML",
        "LANDING",
        "docs/august_supervisor_index.html",
        "PLANNED",
        0,
    ),
    RegistryExpectation(
        "PAGE_OUTPUT_DOCS_AUGUST_SUPERVISOR_REPORT_MD",
        "REPORT",
        "docs/august_supervisor_report.md",
        "PLANNED",
        1,
    ),
    RegistryExpectation(
        "PAGE_OUTPUT_DOCS_AUGUST_SUPERVISOR_REPORT_HTML",
        "REPORT",
        "docs/august_supervisor_report.html",
        "PLANNED",
        2,
    ),
    RegistryExpectation(
        "PAGE_RESOURCE_DIRECT_RESULTS_EXPLORER",
        "TECHNICAL_RESOURCE",
        "docs/direct_surprisal_results_explorer.html",
        "READY",
        3,
    ),
    RegistryExpectation(
        "PAGE_RESOURCE_WORD_CROSS_SCORER_COMPARISON",
        "TECHNICAL_RESOURCE",
        "docs/word_cross_scorer_comparison.html",
        "READY",
        4,
    ),
    RegistryExpectation(
        "PAGE_RESOURCE_HALL_SNAPSHOT",
        "TECHNICAL_RESOURCE",
        "docs/hall_snapshot_mistral_analysis.html",
        "READY",
        5,
    ),
    RegistryExpectation(
        "PAGE_RESOURCE_CORRECTED_BAYES",
        "TECHNICAL_RESOURCE",
        "docs/corrected_pbm_bayes_report.html",
        "READY",
        6,
    ),
    RegistryExpectation(
        "PAGE_RESOURCE_SUSTAINED_ONSET",
        "TECHNICAL_RESOURCE",
        "docs/direct_surprisal_onset_confirmation.html",
        "READY",
        7,
    ),
    RegistryExpectation(
        "PAGE_RESOURCE_CHILD_TRAJECTORIES",
        "TECHNICAL_RESOURCE",
        "docs/paired_tinydialogues_mistral_child_trajectories.html",
        "READY",
        8,
    ),
    RegistryExpectation(
        "PAGE_RESOURCE_FORMAL_DEFINITIONS",
        "TECHNICAL_RESOURCE",
        "docs/july_meeting_definitions.html",
        "READY",
        9,
    ),
    RegistryExpectation(
        "PAGE_RESOURCE_TECHNICAL_ANALYSIS_INVENTORY",
        "TECHNICAL_RESOURCE",
        "docs/complete_analysis_machine_index.html",
        "READY",
        10,
    ),
)


REQUIRED_DESTINATIONS = {
    "integrated_august_report": "docs/august_supervisor_report.html",
    "copy_ready_report_source": "docs/august_supervisor_report.md",
    "direct_results_explorer": "docs/direct_surprisal_results_explorer.html",
    "word_cross_scorer_report": "docs/word_cross_scorer_comparison.html",
    "hall_report": "docs/hall_snapshot_mistral_analysis.html",
    "corrected_bayes_report": "docs/corrected_pbm_bayes_report.html",
    "onset_report": "docs/direct_surprisal_onset_confirmation.html",
    "individual_trajectories": "docs/paired_tinydialogues_mistral_child_trajectories.html",
    "formal_definitions": "docs/july_meeting_definitions.html",
    "evidence_inventory": "docs/complete_analysis_machine_index.html",
}


ARCHIVE_DESTINATIONS = {
    "june_meeting_archive": "docs/june_25th_meeting_index.html",
    "july_meeting_archive": "docs/july_meeting_index.html",
}


STATUS_DEFINITIONS = (
    (
        "SUPPORTED",
        "Completed / supported",
        "The analysis is complete and the frozen evidence supports the registered reading.",
    ),
    (
        "QUALIFIED",
        "Qualified",
        "The result is informative, but a stated gate limits its interpretation or promotion.",
    ),
    (
        "CONTRARY",
        "Contrary",
        "The observed direction runs opposite to the registered prediction.",
    ),
    (
        "DESCRIPTIVE",
        "Descriptive",
        "The comparison is explicitly non-causal and separate from longitudinal confirmation.",
    ),
    (
        "PENDING",
        "Pending",
        "The required evidence or validation is not yet complete.",
    ),
)


@dataclass(frozen=True)
class ExecutiveCardSpec:
    status: str
    title: str
    claim_id: str
    destination_page_id: str


EXECUTIVE_CARD_SPECS = (
    ExecutiveCardSpec(
        "SUPPORTED",
        "PBM discovery: predictability at fixed effort",
        "DIRECT_PBM_MISTRAL_CONTEXTUAL",
        "PAGE_RESOURCE_DIRECT_RESULTS_EXPLORER",
    ),
    ExecutiveCardSpec(
        "QUALIFIED",
        "Non-PBM confirmation: direction, not confirmation",
        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
        "PAGE_OUTPUT_DOCS_AUGUST_SUPERVISOR_REPORT_HTML",
    ),
    ExecutiveCardSpec(
        "CONTRARY",
        "Context gain: opposite to the registered direction",
        "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN",
        "PAGE_OUTPUT_DOCS_AUGUST_SUPERVISOR_REPORT_HTML",
    ),
    ExecutiveCardSpec(
        "DESCRIPTIVE",
        "Hall: a separate historical snapshot",
        "HALL_RACE_CLASS_INTERACTION",
        "PAGE_RESOURCE_HALL_SNAPSHOT",
    ),
    ExecutiveCardSpec(
        "PENDING",
        "Listener-relevant utility remains unvalidated",
        "LISTENER_UTILITY_OUTCOME",
        "PAGE_OUTPUT_DOCS_AUGUST_SUPERVISOR_REPORT_HTML",
    ),
)


RESOURCE_PRESENTATION = {
    "integrated_august_report": (
        "Integrated August supervisor report",
        "Open the current scientific synthesis with claim-level caveats and figures.",
    ),
    "copy_ready_report_source": (
        "Copy-ready report source",
        "Open the Markdown version of the integrated August report.",
    ),
    "direct_results_explorer": (
        "Direct-results explorer",
        "Open the saved-model explorer and individual direct-score profiles.",
    ),
    "word_cross_scorer_report": (
        "Word-level cross-scorer report",
        "Open the separate Mistral, Qwen3-14B, and TinyDialogues comparison.",
    ),
    "hall_report": (
        "Hall historical snapshot report",
        "Open the separate cross-sectional and domain-sensitivity analysis.",
    ),
    "corrected_bayes_report": (
        "Corrected candidate-set Bayes report",
        "Open the cross-fitted finite-candidate-set decomposition and validation.",
    ),
    "onset_report": (
        "Sustained-onset report",
        "Open the frozen simultaneous-band onset analysis.",
    ),
    "individual_trajectories": (
        "Individual child trajectories",
        "Open the paired TinyDialogues–Mistral child-level trajectory gallery.",
    ),
    "formal_definitions": (
        "Formal definitions",
        "Open the mathematical definitions used across the report package.",
    ),
    "evidence_inventory": (
        "Evidence inventory",
        "Open the technical analysis inventory and its status/guardrail map.",
    ),
}


@dataclass(frozen=True)
class IndexEvidence:
    root: Path
    input_dir: Path
    report_manifest_path: Path
    report_manifest: Mapping[str, Any]
    report: ReportEvidence
    pages: Mapping[str, PageRecord]


def _rooted(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ContractError(f"index path is outside repository root: {path}") from error
    return resolved


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as error:
        raise ContractError(f"index path is outside repository root: {path}") from error


def _relative_link(target: Path, parent: Path) -> str:
    return Path(os.path.relpath(target, start=parent)).as_posix()


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


def validate_page_registry(
    registry_path: Path | str, *, root: Path | str
) -> dict[str, PageRecord]:
    """Validate the exact frozen page registry used by the landing page."""

    base = Path(root).resolve()
    path = _rooted(registry_path, base)
    rows = read_registry_csv(path, "page")
    expected = {item.page_id: item for item in EXPECTED_PAGE_REGISTRY}
    observed = {row["page_id"]: row for row in rows}
    if set(observed) != set(expected):
        raise ContractError(
            "page registry coverage drift; "
            f"missing={sorted(set(expected) - set(observed))}, "
            f"extra={sorted(set(observed) - set(expected))}"
        )

    pages: dict[str, PageRecord] = {}
    source_hashes = {row["source_manifest_sha256"] for row in rows}
    if len(source_hashes) != 1:
        raise ContractError("page registry has inconsistent source manifests")
    for page_id, item in expected.items():
        row = observed[page_id]
        frozen_fields = {
            "page_kind": item.page_kind,
            "output_path": item.output_path,
            "page_status": item.page_status,
            "display_order": item.display_order,
            "source_stage_id": "model-results",
        }
        changed = {
            key: (value, row[key])
            for key, value in frozen_fields.items()
            if row[key] != value
        }
        if changed:
            raise ContractError(
                f"page registry destination drift for {page_id}: {changed}"
            )
        target = _rooted(row["output_path"], base)
        if page_id != "PAGE_OUTPUT_DOCS_AUGUST_SUPERVISOR_INDEX_HTML" and not target.is_file():
            raise ContractError(f"required landing-page destination is missing: {row['output_path']}")
        pages[page_id] = PageRecord(
            page_id=page_id,
            title=row["title"],
            output_path=row["output_path"],
            page_status=row["page_status"],
            display_order=row["display_order"],
        )
    return dict(sorted(pages.items()))


def load_index_evidence(
    *,
    root: Path | str,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
    plot_dir: Path | str = DEFAULT_PLOT_DIR,
    report_manifest_path: Path | str | None = None,
) -> IndexEvidence:
    """Load and verify the complete frozen input boundary for the index stage."""

    base = Path(root).resolve()
    inputs = _rooted(input_dir, base)
    report_manifest_file = _rooted(
        inputs / "report_manifest.json"
        if report_manifest_path is None
        else report_manifest_path,
        base,
    )
    report_manifest = verify_stage_manifest(
        report_manifest_file, root=base, expected_stage="report"
    )
    expected_report_artifacts = {
        "docs/august_supervisor_report.html",
        "docs/august_supervisor_report.md",
        "results/august_supervisor_report/report_trace.json",
    }
    observed_report_artifacts = {
        artifact["path"] for artifact in report_manifest["artifacts"]
    }
    if observed_report_artifacts != expected_report_artifacts:
        raise ContractError(
            "report manifest artifact coverage drift; "
            f"expected={sorted(expected_report_artifacts)}, "
            f"observed={sorted(observed_report_artifacts)}"
        )

    pages = validate_page_registry(inputs / "page_registry.csv", root=base)
    report = load_report_evidence(
        root=base,
        input_dir=inputs,
        plot_dir=plot_dir,
    )
    if pages != report.pages:
        raise ContractError("page registry changed between index validation reads")

    registry_paths = {page.output_path for page in pages.values()}
    missing = set(REQUIRED_DESTINATIONS.values()) - registry_paths
    if missing:
        raise ContractError(f"required current destinations are absent from page registry: {sorted(missing)}")
    for path in ARCHIVE_DESTINATIONS.values():
        if not _rooted(path, base).is_file():
            raise ContractError(f"required archive destination is missing: {path}")

    if FEATURED_FIGURE_ID not in report.figures:
        raise ContractError(f"featured index figure is missing: {FEATURED_FIGURE_ID}")
    for spec in EXECUTIVE_CARD_SPECS:
        claim = report.claims.get(spec.claim_id)
        if claim is None:
            raise ContractError(f"executive card has unresolved claim ID: {spec.claim_id}")
        if claim.classification != spec.status:
            raise ContractError(
                f"executive card status drift for {spec.claim_id}: "
                f"expected {spec.status}, observed {claim.classification}"
            )
        if spec.destination_page_id not in pages:
            raise ContractError(
                f"executive card has unresolved destination: {spec.destination_page_id}"
            )

    return IndexEvidence(
        root=base,
        input_dir=inputs,
        report_manifest_path=report_manifest_file,
        report_manifest=report_manifest,
        report=report,
        pages=pages,
    )


class _ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.images: list[tuple[str, str]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids.add(element_id)
        if tag == "a" and attributes.get("href") is not None:
            self.links.append(attributes["href"] or "")
        if tag == "img" and attributes.get("src") is not None:
            self.images.append(
                (attributes["src"] or "", attributes.get("alt") or "")
            )


def _parse_html(path: Path) -> _ReferenceParser:
    parser = _ReferenceParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def _local_target(
    reference: str, *, source_path: Path, root: Path
) -> tuple[Path, str]:
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc:
        raise ContractError(f"reference is not local: {reference}")
    raw_path = unquote(parsed.path)
    if raw_path.startswith("/"):
        target = (root / raw_path.lstrip("/")).resolve()
    elif raw_path:
        target = (source_path.parent / raw_path).resolve()
    else:
        target = source_path.resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ContractError(f"local reference escapes repository root: {reference}") from error
    return target, unquote(parsed.fragment)


def audit_local_references(
    html_path: Path | str,
    *,
    root: Path | str,
    expected_image_hashes: Mapping[str, str] | None = None,
) -> dict[str, int]:
    """Validate every local link, image, and fragment in one HTML artifact."""

    base = Path(root).resolve()
    source_path = _rooted(html_path, base)
    if not source_path.is_file():
        raise ContractError(f"missing HTML artifact for link audit: {source_path}")
    parsed_source = _parse_html(source_path)
    fragment_cache: dict[Path, set[str]] = {source_path: parsed_source.ids}
    local_links = 0
    fragments = 0
    checked_paths: set[Path] = set()
    for reference in parsed_source.links:
        split = urlsplit(reference)
        if split.scheme in {"http", "https", "mailto"} or split.netloc:
            continue
        target, fragment = _local_target(reference, source_path=source_path, root=base)
        local_links += 1
        checked_paths.add(target)
        if not target.is_file():
            raise ContractError(f"missing local link target: {reference}")
        if fragment:
            fragments += 1
            if target.suffix.lower() not in {".html", ".htm"}:
                raise ContractError(f"fragment target is not HTML: {reference}")
            if target not in fragment_cache:
                fragment_cache[target] = _parse_html(target).ids
            if fragment not in fragment_cache[target]:
                raise ContractError(f"missing HTML fragment: {reference}")

    normalized_expected = {
        _rooted(path, base): digest
        for path, digest in (expected_image_hashes or {}).items()
    }
    observed_images: set[Path] = set()
    for reference, alt_text in parsed_source.images:
        if not alt_text.strip():
            raise ContractError(f"landing-page image has empty alt text: {reference}")
        target, fragment = _local_target(reference, source_path=source_path, root=base)
        if fragment:
            raise ContractError(f"image reference contains a fragment: {reference}")
        if not target.is_file():
            raise ContractError(f"missing landing-page image: {reference}")
        checked_paths.add(target)
        observed_images.add(target)
        expected_hash = normalized_expected.get(target)
        if expected_image_hashes is not None and (
            expected_hash is None or sha256_file(target) != expected_hash
        ):
            raise ContractError(f"image hash verification failed: {reference}")
    if expected_image_hashes is not None and observed_images != set(normalized_expected):
        raise ContractError("image hash verification failed: featured image coverage drift")

    return {
        "local_link_count": local_links,
        "image_count": len(parsed_source.images),
        "fragment_count": fragments,
        "unique_local_target_count": len(checked_paths),
    }


def _page_by_path(evidence: IndexEvidence, output_path: str) -> PageRecord:
    matches = [page for page in evidence.pages.values() if page.output_path == output_path]
    if len(matches) != 1:
        raise ContractError(f"destination does not resolve uniquely in page registry: {output_path}")
    return matches[0]


def _snapshot(evidence: IndexEvidence) -> dict[str, str]:
    paths = {
        evidence.input_dir / "page_registry.csv",
        evidence.input_dir / "headline_findings.csv",
        evidence.input_dir / "supporting_findings.csv",
        evidence.input_dir / "coverage_and_limitations.csv",
        evidence.input_dir / "synthesis_manifest.json",
        evidence.report.plot_dir / "figure_manifest.csv",
        evidence.report.plot_manifest_path,
        evidence.report_manifest_path,
        *(_rooted(path, evidence.root) for path in REQUIRED_DESTINATIONS.values()),
        *(_rooted(path, evidence.root) for path in ARCHIVE_DESTINATIONS.values()),
    }
    return {
        _relative_to_root(path, evidence.root): sha256_file(path)
        for path in sorted(paths)
    }


def render_index_html(evidence: IndexEvidence, *, html_path: Path) -> str:
    """Return deterministic, accessible HTML resolved from frozen evidence."""

    escape = html.escape
    page_parent = html_path.parent
    labels = {status: (label, definition) for status, label, definition in STATUS_DEFINITIONS}
    integrated = _page_by_path(
        evidence, REQUIRED_DESTINATIONS["integrated_august_report"]
    )
    integrated_href = _relative_link(
        evidence.root / integrated.output_path, page_parent
    )

    legend_items = "\n".join(
        (
            f'<li class="legend-item status-{status.lower()}">'
            f'<strong>{escape(label)}</strong><span>{escape(definition)}</span></li>'
        )
        for status, label, definition in STATUS_DEFINITIONS
    )

    cards: list[str] = []
    for spec in EXECUTIVE_CARD_SPECS:
        claim = evidence.report.claims[spec.claim_id]
        destination = evidence.pages[spec.destination_page_id]
        href = _relative_link(evidence.root / destination.output_path, page_parent)
        label, _ = labels[spec.status]
        cards.append(
            "\n".join(
                [
                    (
                        f'<article class="result-card status-{spec.status.lower()}" '
                        f'data-status="{spec.status}" data-claim-id="{spec.claim_id}">'
                    ),
                    f'<p class="status-label">{escape(label)}</p>',
                    f'<h3>{escape(spec.title)}</h3>',
                    f'<p>{escape(claim.finding)}</p>',
                    (
                        '<p class="warning" role="note"><strong>Interpretation limit.</strong> '
                        f'{escape(claim.limitation)}</p>'
                    ),
                    f'<a class="card-link" href="{escape(href, quote=True)}">Open {escape(destination.title)}</a>',
                    "</article>",
                ]
            )
        )
    card_html = "\n".join(cards)

    resources: list[str] = []
    for key, output_path in REQUIRED_DESTINATIONS.items():
        page = _page_by_path(evidence, output_path)
        title, description = RESOURCE_PRESENTATION[key]
        href = _relative_link(evidence.root / page.output_path, page_parent)
        resources.append(
            "\n".join(
                [
                    '<li class="resource-card">',
                    f'<h3>{escape(title)}</h3>',
                    f'<p>{escape(description)}</p>',
                    f'<a href="{escape(href, quote=True)}">Open {escape(title)}</a>',
                    "</li>",
                ]
            )
        )
    resource_html = "\n".join(resources)

    figure = evidence.report.figures[FEATURED_FIGURE_ID]
    figure_href = _relative_link(evidence.root / figure.image_path, page_parent)
    figure_claims = " ".join(figure.claim_ids)

    archive_labels = {
        "june_meeting_archive": "Archive: June 25 meeting package",
        "july_meeting_archive": "Archive: July meeting package",
    }
    archives = "\n".join(
        (
            '<li><a href="{}">{}</a></li>'.format(
                escape(
                    _relative_link(evidence.root / path, page_parent), quote=True
                ),
                escape(archive_labels[key]),
            )
        )
        for key, path in ARCHIVE_DESTINATIONS.items()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>August 2026 Supervisor Report</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172522;
      --muted: #50625d;
      --paper: #f7f5ef;
      --surface: #fffdf8;
      --line: #cad3ce;
      --accent: #155f63;
      --supported: #17633a;
      --qualified: #8a5b00;
      --contrary: #9a352d;
      --descriptive: #5555a4;
      --pending: #5c6268;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; color: var(--ink); background: var(--paper); line-height: 1.62; }}
    a {{ color: var(--accent); text-underline-offset: .18em; text-decoration-thickness: .09em; }}
    a:hover {{ text-decoration-thickness: .16em; }}
    a:focus-visible {{ outline: 3px solid #f0a202; outline-offset: 4px; border-radius: 2px; }}
    .skip-link {{ position: absolute; left: 1rem; top: -5rem; z-index: 20; padding: .7rem 1rem; background: #fff; color: #000; }}
    .skip-link:focus {{ top: 1rem; }}
    .site-header {{ background: #123b3d; color: #fff; }}
    .header-inner, main, footer {{ width: min(1160px, calc(100% - 2rem)); margin-inline: auto; }}
    .header-inner {{ display: flex; align-items: center; justify-content: space-between; gap: 1.25rem; padding: .9rem 0; }}
    .brand {{ margin: 0; font-weight: 760; letter-spacing: .01em; }}
    nav ul {{ display: flex; flex-wrap: wrap; gap: .55rem 1rem; margin: 0; padding: 0; list-style: none; }}
    nav a {{ color: #fff; }}
    main {{ padding: 3.4rem 0 4rem; }}
    section {{ scroll-margin-top: 1.5rem; margin-top: 4rem; }}
    .hero {{ display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(17rem, .65fr); gap: 2rem; align-items: start; margin-top: 0; }}
    .eyebrow, .status-label {{ text-transform: uppercase; letter-spacing: .09em; font-size: .78rem; font-weight: 800; }}
    h1 {{ max-width: 18ch; margin: .25rem 0 1rem; font-size: clamp(2.35rem, 6vw, 4.8rem); line-height: 1.02; letter-spacing: -.045em; }}
    h2 {{ margin: 0 0 .6rem; font-size: clamp(1.65rem, 3vw, 2.35rem); line-height: 1.15; }}
    h3 {{ margin: .25rem 0 .65rem; line-height: 1.25; }}
    .lede {{ max-width: 68ch; color: var(--muted); font-size: 1.12rem; }}
    .primary-link, .card-link {{ display: inline-block; font-weight: 750; }}
    .primary-link {{ margin-top: .5rem; padding: .72rem 1rem; border-radius: .35rem; color: #fff; background: var(--accent); text-decoration: none; }}
    .scope-warning, .warning {{ border-left: .32rem solid currentColor; background: #fff8df; }}
    .scope-warning {{ margin: 0; padding: 1rem 1.1rem; color: #5c4700; }}
    .legend {{ display: grid; gap: .55rem; margin: 0; padding: 0; list-style: none; }}
    .legend-item {{ display: grid; grid-template-columns: minmax(9rem, .42fr) 1fr; gap: .8rem; padding: .72rem .85rem; border: 1px solid var(--line); border-left: .35rem solid currentColor; background: var(--surface); }}
    .legend-item span {{ color: var(--ink); }}
    .status-supported {{ color: var(--supported); }}
    .status-qualified {{ color: var(--qualified); }}
    .status-contrary {{ color: var(--contrary); }}
    .status-descriptive {{ color: var(--descriptive); }}
    .status-pending {{ color: var(--pending); }}
    .result-grid {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 1rem; margin-top: 1.4rem; }}
    .result-card {{ grid-column: span 2; display: flex; flex-direction: column; padding: 1.15rem; border: 1px solid var(--line); border-top: .42rem solid currentColor; border-radius: .45rem; background: var(--surface); box-shadow: 0 .35rem 1rem rgba(20, 45, 40, .06); }}
    .result-card:nth-child(4) {{ grid-column: 2 / span 2; }}
    .result-card p:not(.status-label) {{ color: var(--ink); }}
    .result-card .warning {{ margin-top: auto; padding: .7rem .8rem; font-size: .92rem; }}
    .result-card .card-link {{ margin-top: .35rem; }}
    .feature {{ display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(16rem, .8fr); gap: 1.4rem; align-items: start; padding: 1rem; border: 1px solid var(--line); background: var(--surface); }}
    .feature img {{ display: block; width: 100%; height: auto; border: 1px solid var(--line); }}
    figcaption {{ color: var(--muted); font-size: .94rem; }}
    .resource-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); gap: .8rem; padding: 0; list-style: none; }}
    .resource-card {{ padding: 1rem; border: 1px solid var(--line); background: var(--surface); }}
    .resource-card p {{ color: var(--muted); }}
    .archive-box {{ padding: 1rem 1.2rem; border: 1px dashed #8b9690; background: #ecebe6; }}
    .archive-box ul {{ margin-bottom: 0; }}
    footer {{ padding: 1.5rem 0 3rem; color: var(--muted); border-top: 1px solid var(--line); }}
    @media (max-width: 900px) {{
      .hero, .feature {{ grid-template-columns: 1fr; }}
      .result-card, .result-card:nth-child(4) {{ grid-column: span 3; }}
    }}
    @media (max-width: 720px) {{
      .header-inner {{ display: block; }}
      nav {{ margin-top: .6rem; }}
      main {{ padding-top: 2.2rem; }}
      section {{ margin-top: 3rem; }}
      .result-grid {{ display: block; }}
      .result-card {{ margin-bottom: .8rem; }}
      .legend-item {{ grid-template-columns: 1fr; gap: .2rem; }}
      h1 {{ font-size: clamp(2.2rem, 13vw, 3.4rem); }}
    }}
    @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to the report overview</a>
  <header class="site-header">
    <div class="header-inner">
      <p class="brand">Communicative efficiency · August 2026</p>
      <nav aria-label="Landing-page sections">
        <ul>
          <li><a href="#executive-summary">Results</a></li>
          <li><a href="#current-resources">Current reports</a></li>
          <li><a href="#archives">Archives</a></li>
        </ul>
      </nav>
    </div>
  </header>
  <main id="main-content" tabindex="-1">
    <section class="hero" aria-labelledby="page-title">
      <div>
        <p class="eyebrow">Supervisor consultation landing page</p>
        <h1 id="page-title">What the current evidence supports—and what remains open</h1>
        <p class="lede">A concise entry point to the frozen August synthesis, its five evidence statuses, and the audited technical companions. Result text below is drawn from the frozen claim registry.</p>
        <a class="primary-link" href="{escape(integrated_href, quote=True)}">Open the integrated August supervisor report</a>
      </div>
      <p class="scope-warning" role="note" data-claim-ids="DIRECT_PBM_MISTRAL_CONTEXTUAL DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY HALL_RACE_CLASS_INTERACTION"><strong>Scope warning.</strong> PBM is the 21-child discovery sample; the remaining 58 children are the separate confirmation sample. Hall remains a separate historical, cross-sectional, descriptive analysis.</p>
    </section>

    <section id="status-legend" aria-labelledby="status-heading">
      <h2 id="status-heading">How to read the evidence labels</h2>
      <p>Every executive card carries a visible label and interpretation text; color is only a secondary cue.</p>
      <ul class="legend">{legend_items}</ul>
    </section>

    <section id="executive-summary" aria-labelledby="executive-heading">
      <h2 id="executive-heading">Five-result executive summary</h2>
      <p>These cards intentionally keep supported, qualified, contrary, descriptive, and pending evidence distinct.</p>
      <div class="result-grid">{card_html}</div>
    </section>

    <section id="featured-figure" aria-labelledby="figure-heading">
      <h2 id="figure-heading">Discovery and confirmation at a glance</h2>
      <figure class="feature" data-claim-ids="{escape(figure_claims, quote=True)}">
        <img src="{escape(figure_href, quote=True)}" alt="{escape(figure.alt_text, quote=True)}" loading="lazy" decoding="async">
        <figcaption><strong>Audited figure.</strong> {escape(figure.caption)} The PBM discovery and non-PBM confirmation estimates remain explicitly separated.</figcaption>
      </figure>
    </section>

    <section id="current-resources" aria-labelledby="resources-heading">
      <h2 id="resources-heading">Current August package and evidence resources</h2>
      <p>All current destinations below resolve through the frozen page registry.</p>
      <ul class="resource-grid">{resource_html}</ul>
    </section>

    <section id="archives" aria-labelledby="archives-heading">
      <div class="archive-box">
        <h2 id="archives-heading">Archived June and July packages</h2>
        <p>These earlier landing pages are preserved for historical consultation only. They are not redirects and are not the current August synthesis.</p>
        <ul>{archives}</ul>
      </div>
    </section>
  </main>
  <footer>
    <p>Frozen August 2026 reporting package · navigation and prose rendered without refitting models or generating new results.</p>
  </footer>
</body>
</html>
"""


def build_supervisor_index(
    *,
    root: Path | str,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
    plot_dir: Path | str = DEFAULT_PLOT_DIR,
    html_path: Path | str = DEFAULT_HTML_PATH,
    report_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build, hash, and locally audit the deterministic supervisor index."""

    base = Path(root).resolve()
    output = _rooted(html_path, base)
    evidence = load_index_evidence(
        root=base,
        input_dir=input_dir,
        plot_dir=plot_dir,
        report_manifest_path=report_manifest_path,
    )
    before = _snapshot(evidence)
    rendered = render_index_html(evidence, html_path=output)
    _atomic_write_text(output, rendered)
    after = _snapshot(evidence)
    if before != after:
        raise ContractError("frozen landing-page inputs changed during rendering")

    figure = evidence.report.figures[FEATURED_FIGURE_ID]
    link_audit = audit_local_references(
        output,
        root=base,
        expected_image_hashes={figure.image_path: figure.image_sha256},
    )
    return {
        "status": "PASS",
        "stage": "index",
        "output_path": _relative_to_root(output, base),
        "page_sha256": sha256_file(output),
        "executive_card_count": len(EXECUTIVE_CARD_SPECS),
        "resolved_claim_ids": sorted(spec.claim_id for spec in EXECUTIVE_CARD_SPECS),
        "current_destination_count": len(REQUIRED_DESTINATIONS),
        "archive_destination_count": len(ARCHIVE_DESTINATIONS),
        "link_audit": link_audit,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--plot-dir", type=Path, default=DEFAULT_PLOT_DIR)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_PATH)
    parser.add_argument("--report-manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = build_supervisor_index(
        root=args.root,
        input_dir=args.input_dir,
        plot_dir=args.plot_dir,
        html_path=args.html,
        report_manifest_path=args.report_manifest,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
