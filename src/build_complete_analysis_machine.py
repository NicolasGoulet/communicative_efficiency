#!/usr/bin/env python3
"""Run the project's scientifically registered analysis families in stages.

This is a controller, not a replacement statistical implementation.  It
reuses the audited Route 1, Route 2, direct-score, paired-score, and word-level
pipelines and preserves their model-specific manifests.  Commands are run
without a shell, sequentially, and are resumable only when the command,
configuration hash, and expected artifacts all still agree.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


VERSION = "2026-08-05.complete-analysis-machine-v1"
PHASES = ("prepare", "fit", "plots", "reports")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(value, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    components = payload.get("components", [])
    ids = [item.get("component_id") for item in components]
    if not components or len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError("configuration must contain uniquely named components")
    for component in components:
        unknown = set(component.get("commands", {})) - set(PHASES)
        if unknown:
            raise ValueError(f"{component['component_id']} has unknown command phases: {sorted(unknown)}")
        for phase, commands in component.get("commands", {}).items():
            if not isinstance(commands, list) or any(not isinstance(command, list) for command in commands):
                raise ValueError(f"{component['component_id']}/{phase} commands must be lists of argv lists")
    payload["_path"] = str(path.resolve())
    payload["_sha256"] = sha256_file(path)
    return payload


def _resolve(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (repo_root / path).resolve()


def _command_hash(command: Sequence[str]) -> str:
    return hashlib.sha256(json.dumps(list(command), separators=(",", ":")).encode()).hexdigest()


def _component_hash(component: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(component, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def preflight(config: Mapping[str, Any], repo_root: Path, selected: set[str] | None = None) -> dict[str, Any]:
    rows = []
    for component in config["components"]:
        component_id = component["component_id"]
        if selected and component_id not in selected:
            continue
        required = [_resolve(repo_root, value) for value in component.get("required_paths", [])]
        missing = [str(path) for path in required if not path.exists()]
        declared_blocker = str(component.get("blocked_reason", ""))
        status = "BLOCKED" if missing or declared_blocker else "READY"
        rows.append(
            {
                "component_id": component_id,
                "family": component.get("family", ""),
                "sample": component.get("sample", ""),
                "scorer": component.get("scorer", ""),
                "status": status,
                "missing_paths": missing,
                "blocked_reason": declared_blocker,
            }
        )
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": VERSION,
        "config_sha256": config["_sha256"],
        "status": "PASS" if all(row["status"] == "READY" for row in rows) else "REVIEW",
        "components": rows,
    }


def _stage_manifest_path(run_root: Path, component_id: str, phase: str) -> Path:
    return run_root / "commands" / component_id / f"{phase}.manifest.json"


def _artifacts_exist(repo_root: Path, component: Mapping[str, Any], phase: str) -> bool:
    expected = component.get("expected_artifacts", {}).get(phase, [])
    return bool(expected) and all(_resolve(repo_root, value).exists() for value in expected)


def _artifact_records(
    repo_root: Path,
    component: Mapping[str, Any],
    phase: str,
) -> list[dict[str, Any]]:
    """Fingerprint declared outputs so resume cannot accept stale replacements."""

    records: list[dict[str, Any]] = []
    for declared in component.get("expected_artifacts", {}).get(phase, []):
        path = _resolve(repo_root, declared)
        record: dict[str, Any] = {
            "declared_path": str(declared),
            "resolved_path": str(path),
            "exists": path.exists(),
        }
        if path.is_file():
            stat = path.stat()
            record.update(
                {
                    "type": "file",
                    "size_bytes": stat.st_size,
                    "sha256": sha256_file(path),
                }
            )
        elif path.is_dir():
            entries = sorted(
                str(item.relative_to(path))
                for item in path.rglob("*")
                if item.is_file()
            )
            record.update(
                {
                    "type": "directory",
                    "file_count": len(entries),
                    "listing_sha256": hashlib.sha256(
                        "\n".join(entries).encode("utf-8")
                    ).hexdigest(),
                }
            )
        else:
            record["type"] = "missing"
        records.append(record)
    return records


def _can_resume(
    manifest_path: Path,
    *,
    config_sha256: str,
    component_sha256: str,
    commands: Sequence[Sequence[str]],
    repo_root: Path,
    component: Mapping[str, Any],
    phase: str,
) -> bool:
    if not manifest_path.is_file() or not _artifacts_exist(repo_root, component, phase):
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        manifest.get("status") == "PASS"
        and manifest.get("config_sha256") == config_sha256
        and manifest.get("component_sha256") == component_sha256
        and manifest.get("command_hashes") == [_command_hash(command) for command in commands]
        and manifest.get("artifacts") == _artifact_records(repo_root, component, phase)
    )


def _prior_phase_problem(
    component: Mapping[str, Any], phase: str, run_root: Path
) -> str:
    """Require successful controller manifests for applicable upstream phases."""

    phase_index = PHASES.index(phase)
    for prior in PHASES[:phase_index]:
        if not component.get("commands", {}).get(prior, []):
            continue
        path = _stage_manifest_path(run_root, str(component["component_id"]), prior)
        if not path.is_file():
            return f"missing upstream {prior} manifest"
        try:
            status = json.loads(path.read_text(encoding="utf-8")).get("status", "")
        except (OSError, json.JSONDecodeError):
            return f"unreadable upstream {prior} manifest"
        if status != "PASS":
            return f"upstream {prior} status is {status}"
    return ""


def run_component_phase(
    component: Mapping[str, Any],
    phase: str,
    *,
    config: Mapping[str, Any],
    repo_root: Path,
    run_root: Path,
    force: bool = False,
) -> dict[str, Any]:
    component_id = str(component["component_id"])
    commands = component.get("commands", {}).get(phase, [])
    manifest_path = _stage_manifest_path(run_root, component_id, phase)
    if not commands:
        report = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "component_id": component_id,
            "phase": phase,
            "status": "NOT_APPLICABLE",
            "commands": [],
        }
        atomic_json(manifest_path, report)
        return report
    if not force and _can_resume(
        manifest_path,
        config_sha256=config["_sha256"],
        component_sha256=_component_hash(component),
        commands=commands,
        repo_root=repo_root,
        component=component,
        phase=phase,
    ):
        report = json.loads(manifest_path.read_text(encoding="utf-8"))
        report["resumed_without_rerun"] = True
        return report
    log_dir = run_root / "logs" / component_id
    log_dir.mkdir(parents=True, exist_ok=True)
    command_reports = []
    phase_status = "PASS"
    for index, raw_command in enumerate(commands):
        command = [str(value) for value in raw_command]
        log_path = log_dir / f"{phase}.{index:02d}.log"
        started = time.monotonic()
        working_dir = _resolve(repo_root, str(component.get("working_dir", ".")))
        command_env = {
            **os.environ,
            **{str(key): str(value) for key, value in component.get("environment", {}).items()},
        }
        command_env["MPLCONFIGDIR"] = command_env.get(
            "MPLCONFIGDIR", "/tmp/mpl-complete-analysis"
        )
        with log_path.open("w", encoding="utf-8") as log:
            log.write(f"command={json.dumps(command)}\n")
            log.write(f"working_dir={working_dir}\n")
            log.flush()
            result = subprocess.run(
                command,
                cwd=working_dir,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                env=command_env,
            )
        command_status = "PASS" if result.returncode == 0 else "FAILED"
        command_reports.append(
            {
                "index": index,
                "argv": command,
                "command_sha256": _command_hash(command),
                "returncode": result.returncode,
                "status": command_status,
                "elapsed_seconds": time.monotonic() - started,
                "log": str(log_path),
            }
        )
        if result.returncode:
            phase_status = "FAILED"
            break
    if phase_status == "PASS" and not _artifacts_exist(repo_root, component, phase):
        phase_status = "FAILED_ARTIFACT_AUDIT"
    artifacts = _artifact_records(repo_root, component, phase)
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": VERSION,
        "component_id": component_id,
        "family": component.get("family", ""),
        "phase": phase,
        "status": phase_status,
        "config_sha256": config["_sha256"],
        "component_sha256": _component_hash(component),
        "command_hashes": [_command_hash(command) for command in commands],
        "commands": command_reports,
        "expected_artifacts": component.get("expected_artifacts", {}).get(phase, []),
        "artifacts": artifacts,
    }
    atomic_json(manifest_path, report)
    return report


def run_phases(
    config: Mapping[str, Any],
    repo_root: Path,
    run_root: Path,
    phases: Iterable[str],
    *,
    selected: set[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    reports = []
    for phase in phases:
        for component in config["components"]:
            component_id = component["component_id"]
            if selected and component_id not in selected:
                continue
            readiness = preflight(config, repo_root, {component_id})["components"][0]
            component_ready = readiness["status"] == "READY"
            if not component_ready and (
                component.get("blocked_reason")
                or component.get("commands", {}).get(phase, [])
            ):
                reports.append(
                    {
                        "component_id": component_id,
                        "phase": phase,
                        "status": "BLOCKED_PREFLIGHT",
                    }
                )
                continue
            if not component.get("commands", {}).get(phase, []):
                reports.append(
                    run_component_phase(
                        component,
                        phase,
                        config=config,
                        repo_root=repo_root,
                        run_root=run_root,
                        force=force,
                    )
                )
                continue
            prior_problem = _prior_phase_problem(component, phase, run_root)
            if prior_problem:
                reports.append(
                    {
                        "component_id": component_id,
                        "phase": phase,
                        "status": "BLOCKED_UPSTREAM",
                        "reason": prior_problem,
                    }
                )
                continue
            reports.append(
                run_component_phase(
                    component,
                    phase,
                    config=config,
                    repo_root=repo_root,
                    run_root=run_root,
                    force=force,
                )
            )
    failures = [report for report in reports if report["status"].startswith("FAILED")]
    blocked = [report for report in reports if report["status"].startswith("BLOCKED")]
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": VERSION,
        "status": "PASS" if not failures and not blocked else "REVIEW",
        "phases": list(phases),
        "components": reports,
        "failure_count": len(failures),
        "blocked_count": len(blocked),
    }
    atomic_json(run_root / "run_manifest.json", report)
    return report


def build_synthesis(config: Mapping[str, Any], repo_root: Path, run_root: Path) -> dict[str, Any]:
    readiness = {
        row["component_id"]: row
        for row in preflight(config, repo_root)["components"]
    }
    rows = []
    for component in config["components"]:
        reports = [_resolve(repo_root, path) for path in component.get("report_paths", [])]
        existing = [path for path in reports if path.exists()]
        stage_statuses = {}
        for phase in PHASES:
            path = _stage_manifest_path(run_root, component["component_id"], phase)
            if path.is_file():
                stage_statuses[phase] = json.loads(path.read_text()).get("status", "")
        rows.append(
            {
                "component_id": component["component_id"],
                "family": component.get("family", ""),
                "sample": component.get("sample", ""),
                "scorer": component.get("scorer", ""),
                "scientific_role": component.get("scientific_role", ""),
                "readiness": readiness[component["component_id"]]["status"],
                "blocked_reason": readiness[component["component_id"]]["blocked_reason"],
                "stage_statuses": stage_statuses,
                "reports": [str(path) for path in existing],
                "guardrail": component.get("guardrail", ""),
            }
        )
    atomic_json(run_root / "artifact_index.json", {"version": VERSION, "components": rows})
    csv_path = run_root / "artifact_index.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_temporary = csv_path.with_name(f".{csv_path.name}.tmp-{os.getpid()}")
    try:
        with csv_temporary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["component_id", "family", "sample", "scorer", "scientific_role", "readiness", "blocked_reason", "stage_statuses", "reports", "guardrail"])
            writer.writeheader()
            for row in rows:
                writer.writerow({**row, "stage_statuses": json.dumps(row["stage_statuses"], sort_keys=True), "reports": " | ".join(row["reports"])})
        os.replace(csv_temporary, csv_path)
    finally:
        csv_temporary.unlink(missing_ok=True)
    lines = [
        "# Complete Analysis Machine",
        "",
        "This index separates PBM discovery, non-PBM confirmation, scorer robustness, response-space analyses, and word-level analyses. It does not pool raw surprisal across tokenizers or turn exploratory model families into confirmatory tests.",
        "",
        "| Component | Family | Sample | Scorer | Status | Scientific role | Reports | Guardrail |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        links = ", ".join(f"[{path.name}]({path})" for path in map(Path, row["reports"])) or "pending"
        lines.append(f"| {row['component_id']} | {row['family']} | {row['sample']} | {row['scorer']} | {row['readiness']} | {row['scientific_role']} | {links} | {row['guardrail']} |")
    markdown_path = repo_root / config.get("synthesis_markdown", "docs/complete_analysis_machine_index.md")
    atomic_text(markdown_path, "\n".join(lines) + "\n")
    table_rows = "".join(
        f"<tr><td>{html.escape(str(row['component_id']))}</td><td>{html.escape(str(row['family']))}</td><td>{html.escape(str(row['sample']))}</td><td>{html.escape(str(row['scorer']))}</td><td>{html.escape(str(row['readiness']))}</td><td>{html.escape(str(row['scientific_role']))}</td><td>{'<br>'.join(html.escape(path) for path in row['reports']) or 'pending'}</td><td>{html.escape(str(row['guardrail']))}</td></tr>"
        for row in rows
    )
    html_path = repo_root / config.get("synthesis_html", "docs/complete_analysis_machine_index.html")
    atomic_text(html_path, f"<!doctype html><html><head><meta charset='utf-8'><title>Complete Analysis Machine</title><style>body{{font:15px/1.5 system-ui;max-width:1250px;margin:35px auto;padding:0 25px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd5d3;padding:.5em;vertical-align:top}}th{{background:#e5efed}}h1{{color:#276c72}}</style></head><body><h1>Complete Analysis Machine</h1><p>PBM discovery, non-PBM confirmation, scorer robustness, response-space, and word-level analyses remain scientifically separated. Raw surprisal is never pooled across tokenizers.</p><table><tr><th>Component</th><th>Family</th><th>Sample</th><th>Scorer</th><th>Status</th><th>Role</th><th>Reports</th><th>Guardrail</th></tr>{table_rows}</table></body></html>")
    synthesis_problems = [
        row["component_id"]
        for row in rows
        if row["readiness"] != "READY"
        or any(
            str(status).startswith(("FAILED", "BLOCKED"))
            for status in row["stage_statuses"].values()
        )
    ]
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "version": VERSION, "status": "PASS" if not synthesis_problems else "REVIEW", "components": len(rows), "problem_components": synthesis_problems, "markdown": str(markdown_path), "html": str(html_path), "artifact_index": str(run_root / "artifact_index.json")}
    atomic_json(run_root / "synthesis_manifest.json", report)
    return report


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/complete_analysis_machine_v1.json"))
    parser.add_argument("--run-root", type=Path, default=Path("results/complete_analysis_machine_v1"))
    parser.add_argument("--stage", choices=("preflight", *PHASES, "synthesis", "audit", "all"), default="preflight")
    parser.add_argument("--components", help="Comma-separated component IDs; default is all.")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    config_path = args.config if args.config.is_absolute() else repo_root / args.config
    run_root = args.run_root if args.run_root.is_absolute() else repo_root / args.run_root
    config = load_config(config_path)
    selected = {item.strip() for item in args.components.split(",") if item.strip()} if args.components else None
    if selected:
        known = {item["component_id"] for item in config["components"]}
        unknown = selected - known
        if unknown:
            raise SystemExit(f"unknown component IDs: {sorted(unknown)}")
    if args.stage == "preflight":
        report = preflight(config, repo_root, selected)
        atomic_json(run_root / "preflight.json", report)
    elif args.stage in PHASES:
        report = run_phases(config, repo_root, run_root, [args.stage], selected=selected, force=args.force)
    elif args.stage == "synthesis":
        report = build_synthesis(config, repo_root, run_root)
    elif args.stage == "audit":
        report = preflight(config, repo_root, selected)
        report["command_manifests"] = [str(path) for path in sorted((run_root / "commands").glob("*/*.manifest.json"))]
        atomic_json(run_root / "audit.json", report)
    else:
        report = run_phases(config, repo_root, run_root, PHASES, selected=selected, force=args.force)
        report["synthesis"] = build_synthesis(config, repo_root, run_root)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report.get("status") == "PASS" else 1)


if __name__ == "__main__":
    main()
