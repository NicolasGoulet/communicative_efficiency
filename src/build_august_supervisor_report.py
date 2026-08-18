#!/usr/bin/env python3
"""Orchestrate and completion-gate the frozen August supervisor package.

This is intentionally a thin controller.  The existing stage modules own all
scientific extraction, synthesis, figure construction, rendering, and audit
checks; this module only orders them and verifies their hash boundaries.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:  # Support ``python src/build_...py``.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.august_supervisor.audit import run_independent_audit
from src.august_supervisor.contracts import (
    ContractError,
    atomic_write_json,
    read_json_strict,
    sha256_file,
    verify_stage_manifest,
)
from src.august_supervisor.evidence import extract_datasets
from src.august_supervisor.index import build_supervisor_index
from src.august_supervisor.model_results import extract_model_results
from src.august_supervisor.plots import build_supervisor_plots
from src.august_supervisor.render import build_supervisor_report
from src.august_supervisor.synthesis import synthesize


STAGES = (
    "datasets",
    "model-results",
    "synthesis",
    "plots",
    "report",
    "index",
    "audit",
)
EXPECTED_BRANCH = "agent/august-supervisor-report-v1"
OUTPUT_DIR = Path("results/august_supervisor_report")
AUDIT_DIR = OUTPUT_DIR / "audit"
COMPLETION_MARKER = OUTPUT_DIR / "AUGUST_REPORT_COMPLETE_AND_AUDITED"
REPORT_MANIFEST = OUTPUT_DIR / "report_manifest.json"
PRIMARY_PRODUCTS = (
    Path("docs/august_supervisor_report.md"),
    Path("docs/august_supervisor_report.html"),
    Path("docs/august_supervisor_index.html"),
)
STAGE_MANIFESTS = {
    "datasets": OUTPUT_DIR / "dataset_manifest.json",
    "model-results": OUTPUT_DIR / "model_results_manifest.json",
    "synthesis": OUTPUT_DIR / "synthesis_manifest.json",
    "plots": OUTPUT_DIR / "plots" / "plot_manifest.json",
    "report": REPORT_MANIFEST,
}
REQUIRED_AUDIT_CHECKS = frozenset(
    {
        "claim_reconciliation",
        "number_formatting",
        "manifest_hashes",
        "html_package",
        "scientific_language",
        "deterministic_renders",
        "git_hygiene",
        "browser_renders",
    }
)


def _rooted(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ContractError(f"controller path is outside repository root: {path}") from error
    return resolved


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as error:
        raise ContractError(f"controller path is outside repository root: {path}") from error


def _git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(root), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or str(error)
        raise ContractError(f"git state check failed: {detail}") from error
    return result.stdout.strip()


def _require_stage_name(stage: str, *, allow_all: bool = False) -> None:
    allowed = STAGES + (("all",) if allow_all else ())
    if stage not in allowed:
        raise ValueError(f"invalid stage {stage!r}; expected one of {allowed}")


def validate_stage_dependencies(*, root: Path | str, stage: str) -> dict[str, Any]:
    """Verify the complete predecessor boundary before a stage can run."""

    _require_stage_name(stage)
    base = Path(root).resolve()
    predecessor = {
        "datasets": None,
        "model-results": "datasets",
        "synthesis": "model-results",
        "plots": "synthesis",
        "report": "plots",
        "index": "report",
        "audit": "report",
    }[stage]
    manifest: dict[str, Any] | None = None
    if predecessor is not None:
        manifest_path = _rooted(base, STAGE_MANIFESTS[predecessor])
        manifest = verify_stage_manifest(
            manifest_path,
            root=base,
            expected_stage=predecessor,
        )
    if stage == "audit":
        index = _rooted(base, PRIMARY_PRODUCTS[2])
        if not index.is_file():
            raise ContractError(f"missing product required by audit: {_relative(base, index)}")
    return {
        "stage": stage,
        "predecessor": predecessor,
        "predecessor_manifest": manifest,
    }


def _verify_stage_output(root: Path, stage: str, result: Mapping[str, Any]) -> None:
    if stage in STAGE_MANIFESTS:
        verify_stage_manifest(
            _rooted(root, STAGE_MANIFESTS[stage]),
            root=root,
            expected_stage=stage,
        )
    if stage == "index":
        index = _rooted(root, PRIMARY_PRODUCTS[2])
        if not index.is_file():
            raise ContractError("index stage did not create its declared product")
        if result.get("page_sha256") != sha256_file(index):
            raise ContractError("index stage returned a stale product hash")


def run_stage(
    *,
    root: Path | str,
    stage: str,
    include_browser_renders: bool = True,
) -> dict[str, Any]:
    """Run one existing stage after verifying its predecessor products."""

    _require_stage_name(stage)
    base = Path(root).resolve()
    validate_stage_dependencies(root=base, stage=stage)
    if stage == "datasets":
        result = extract_datasets(root=base)
    elif stage == "model-results":
        result = extract_model_results(root=base)
    elif stage == "synthesis":
        result = synthesize(root=base)
    elif stage == "plots":
        result = build_supervisor_plots(root=base)
    elif stage == "report":
        result = build_supervisor_report(root=base)
    elif stage == "index":
        result = build_supervisor_index(root=base)
    else:
        audit = run_independent_audit(
            root=base,
            include_browser_renders=include_browser_renders,
        )
        if audit.get("verdict") != "AUDIT_PASS":
            raise ContractError(
                "independent audit did not pass: "
                f"{audit.get('blocking_finding_count', 'unknown')} blocking findings"
            )
        validate_audit_pass(root=base, require_current_commit=True)
        result = {"stage": "audit", "status": "AUDIT_PASS", **audit}
    expected_status = "AUDIT_PASS" if stage == "audit" else "PASS"
    if result.get("status") != expected_status:
        raise ContractError(
            f"{stage} returned {result.get('status')!r}; expected {expected_status!r}"
        )
    _verify_stage_output(base, stage, result)
    return dict(result)


def run_controller(
    *,
    root: Path | str,
    stage: str,
    include_browser_renders: bool = True,
) -> dict[str, Any]:
    """Run one named stage or the complete ordered stage chain."""

    _require_stage_name(stage, allow_all=True)
    if stage != "all":
        return run_stage(
            root=root,
            stage=stage,
            include_browser_renders=include_browser_renders,
        )
    results = [
        run_stage(
            root=root,
            stage=item,
            include_browser_renders=include_browser_renders,
        )
        for item in STAGES
    ]
    return {
        "stage": "all",
        "status": "PASS",
        "stages": results,
        "audit_verdict": results[-1]["status"],
    }


def _manifest_product_paths(root: Path, manifest_path: Path) -> set[Path]:
    pending = [manifest_path]
    visited: set[Path] = set()
    products: set[Path] = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        record = verify_stage_manifest(current, root=root)
        products.add(current)
        for artifact in record["artifacts"]:
            products.add(_rooted(root, artifact["path"]))
        for upstream in record["upstream_manifests"]:
            pending.append(_rooted(root, upstream["path"]))
    return products


def collect_product_hashes(*, root: Path | str) -> dict[str, str]:
    """Hash every manifest-chain product plus index and audit evidence."""

    base = Path(root).resolve()
    report_manifest = _rooted(base, REPORT_MANIFEST)
    products = _manifest_product_paths(base, report_manifest)
    products.update(_rooted(base, path) for path in PRIMARY_PRODUCTS)
    products.update(
        {
            _rooted(base, AUDIT_DIR / "audit_report.json"),
            _rooted(base, AUDIT_DIR / "findings.json"),
            _rooted(base, AUDIT_DIR / "AUDIT_PASS"),
        }
    )
    hashes: dict[str, str] = {}
    for path in sorted(products):
        if not path.is_file():
            raise ContractError(f"missing product: {_relative(base, path)}")
        hashes[_relative(base, path)] = sha256_file(path)
    return hashes


def validate_audit_pass(
    *, root: Path | str, require_current_commit: bool
) -> dict[str, Any]:
    """Validate the independent marker, report, findings, and commit binding."""

    base = Path(root).resolve()
    marker_path = _rooted(base, AUDIT_DIR / "AUDIT_PASS")
    report_path = _rooted(base, AUDIT_DIR / "audit_report.json")
    findings_path = _rooted(base, AUDIT_DIR / "findings.json")
    if not marker_path.is_file():
        raise ContractError("missing independent AUDIT_PASS marker")
    if not report_path.is_file() or not findings_path.is_file():
        raise ContractError("AUDIT_PASS is incomplete: report or findings are absent")
    lines = marker_path.read_text(encoding="utf-8").splitlines()
    expected_lines = {
        "audit_report_sha256": sha256_file(report_path),
        "findings_sha256": sha256_file(findings_path),
    }
    observed: dict[str, str] = {}
    for line in lines[1:]:
        if "=" not in line:
            raise ContractError("AUDIT_PASS marker has an invalid field")
        key, value = line.split("=", 1)
        observed[key] = value
    if not lines or lines[0] != "AUDIT_PASS" or observed != expected_lines:
        raise ContractError("AUDIT_PASS marker is stale or hash-inconsistent")

    report = read_json_strict(report_path)
    if type(report) is not dict:
        raise ContractError("audit report is not a JSON object")
    if (
        report.get("stage_id") != "audit"
        or report.get("verdict") != "AUDIT_PASS"
        or report.get("blocking_finding_count") != 0
        or report.get("findings_sha256") != expected_lines["findings_sha256"]
    ):
        raise ContractError("audit report does not record an unblocked AUDIT_PASS")
    checks = report.get("checks")
    if type(checks) is not dict or set(checks) != REQUIRED_AUDIT_CHECKS:
        raise ContractError("audit report check coverage is incomplete")
    if any(checks[name].get("blocking_finding_count") != 0 for name in checks):
        raise ContractError("audit report contains a blocking sub-check")
    boundary = report.get("independence_boundary")
    if type(boundary) is not dict or any(
        boundary.get(key) is not False
        for key in (
            "models_recomputed",
            "report_products_edited",
            "final_completion_marker_created",
        )
    ):
        raise ContractError("audit independence boundary is incomplete")
    if require_current_commit:
        commit = _git(base, "rev-parse", "HEAD")
        branch = _git(base, "branch", "--show-current")
        if report.get("audited_commit") != commit or report.get("branch") != branch:
            raise ContractError("AUDIT_PASS was not produced for the current branch and commit")
    return report


def validate_completion_gate(*, root: Path | str) -> dict[str, Any]:
    """Refuse completion unless Git, manifests, products, and audit all agree."""

    base = Path(root).resolve()
    branch = _git(base, "branch", "--show-current")
    if branch != EXPECTED_BRANCH:
        raise ContractError(
            f"completion requires branch {EXPECTED_BRANCH!r}; observed {branch!r}"
        )
    status = _git(base, "status", "--short")
    if status:
        raise ContractError(f"completion requires a clean worktree; observed:\n{status}")
    report_manifest_path = _rooted(base, REPORT_MANIFEST)
    report_manifest = verify_stage_manifest(
        report_manifest_path,
        root=base,
        expected_stage="report",
    )
    for product in PRIMARY_PRODUCTS:
        path = _rooted(base, product)
        if not path.is_file():
            raise ContractError(f"missing product: {_relative(base, path)}")
    audit = validate_audit_pass(root=base, require_current_commit=True)
    product_hashes = collect_product_hashes(root=base)
    return {
        "branch": branch,
        "commit": _git(base, "rev-parse", "HEAD"),
        "report_manifest": report_manifest,
        "report_manifest_sha256": sha256_file(report_manifest_path),
        "audit": audit,
        "audit_report_sha256": sha256_file(_rooted(base, AUDIT_DIR / "audit_report.json")),
        "audit_marker_sha256": sha256_file(_rooted(base, AUDIT_DIR / "AUDIT_PASS")),
        "product_hashes": product_hashes,
    }


def _validate_test_summary(test_summary: Mapping[str, Any]) -> dict[str, Any]:
    if not test_summary:
        raise ContractError("completion requires a nonempty test summary")
    normalized = dict(test_summary)
    for name, record in normalized.items():
        if type(record) is not dict:
            raise ContractError(f"test summary {name!r} is not an object")
        for field in ("command", "tests", "failures"):
            if field not in record:
                raise ContractError(f"test summary {name!r} is missing {field!r}")
        if record["failures"] != 0 or record.get("errors", 0) != 0:
            raise ContractError(f"test summary {name!r} is not passing")
    return normalized


def write_completion_marker(
    *,
    root: Path | str,
    test_summary: Mapping[str, Any],
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Write the ignored completion record after every final gate passes."""

    base = Path(root).resolve()
    gate = validate_completion_gate(root=base)
    tests = _validate_test_summary(test_summary)
    report_manifest_path = _rooted(base, REPORT_MANIFEST)
    audit_report_path = _rooted(base, AUDIT_DIR / "audit_report.json")
    audit_marker_path = _rooted(base, AUDIT_DIR / "AUDIT_PASS")
    payload = {
        "status": "AUGUST_REPORT_COMPLETE_AND_AUDITED",
        "created_at_utc": timestamp or datetime.now(timezone.utc).isoformat(),
        "branch": gate["branch"],
        "commit": gate["commit"],
        "manifest": {
            "path": _relative(base, report_manifest_path),
            "sha256": gate["report_manifest_sha256"],
            "manifest_sha256": gate["report_manifest"]["manifest_sha256"],
        },
        "audit": {
            "verdict": gate["audit"]["verdict"],
            "report_path": _relative(base, audit_report_path),
            "report_sha256": gate["audit_report_sha256"],
            "marker_path": _relative(base, audit_marker_path),
            "marker_sha256": gate["audit_marker_sha256"],
        },
        "product_hashes": gate["product_hashes"],
        "test_summary": tests,
    }
    marker = _rooted(base, COMPLETION_MARKER)
    atomic_write_json(marker, payload)
    return {
        "status": payload["status"],
        "marker_path": _relative(base, marker),
        "marker_sha256": sha256_file(marker),
        "commit": payload["commit"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--stage", required=True, choices=(*STAGES, "all"))
    parser.add_argument("--skip-browser-renders", action="store_true")
    parser.add_argument("--write-completion-marker", action="store_true")
    parser.add_argument("--test-summary-file", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.write_completion_marker and args.stage not in {"audit", "all"}:
        raise SystemExit("--write-completion-marker requires --stage audit or --stage all")
    if args.write_completion_marker and args.test_summary_file is None:
        raise SystemExit("--write-completion-marker requires --test-summary-file")
    try:
        result = run_controller(
            root=args.root,
            stage=args.stage,
            include_browser_renders=not args.skip_browser_renders,
        )
        if args.write_completion_marker:
            summary = read_json_strict(args.test_summary_file)
            if type(summary) is not dict:
                raise ContractError("test summary file must contain a JSON object")
            result = {
                **result,
                "completion": write_completion_marker(
                    root=args.root,
                    test_summary=summary,
                ),
            }
    except (ContractError, OSError, ValueError) as error:
        print(f"STAGE_FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
