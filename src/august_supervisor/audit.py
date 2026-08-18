"""Independent scientific and publication audit for the August package.

This module is deliberately read-only with respect to the report products.  It
rehashes and reconciles their frozen inputs, performs two render-only builds in
the ignored audit namespace, and emits findings instead of repairing defects.
It does not import a statistical fitting or plotting library.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import unquote, urlsplit

from src.render_markdown_report import render_markdown_file

from .contracts import ContractError, sha256_file, verify_stage_manifest
from .index import load_index_evidence, render_index_html
from .render import render_report_markdown
from .sections import build_report_sections, load_report_evidence


DEFAULT_CONFIGURATION = Path("configs/august_supervisor_report_v1.json")
DEFAULT_INPUT_DIR = Path("results/august_supervisor_report")
DEFAULT_PLOT_DIR = DEFAULT_INPUT_DIR / "plots"
DEFAULT_AUDIT_DIR = DEFAULT_INPUT_DIR / "audit"
DEFAULT_REPORT_MARKDOWN = Path("docs/august_supervisor_report.md")
DEFAULT_REPORT_HTML = Path("docs/august_supervisor_report.html")
DEFAULT_INDEX_HTML = Path("docs/august_supervisor_index.html")
DEFAULT_TRAJECTORY_HTML = Path(
    "docs/paired_tinydialogues_mistral_child_trajectories.html"
)

BLOCKING_SEVERITIES = frozenset({"CRITICAL", "MAJOR"})
SEVERITY_ORDER = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2, "INFO": 3}

_DIRECT_SELECTORS = {
    "DIRECT_PBM_MISTRAL_CONTEXTUAL": (
        "PBM21 discovery",
        "Mistral",
        "P1_k3_contextual",
    ),
    "DIRECT_PBM_TINY_CONTEXTUAL": (
        "PBM21 scorer robustness",
        "TinyDialogues",
        "P1_k3_contextual",
    ),
    "DIRECT_PBM_MISTRAL_UNCONDITIONAL": (
        "PBM21 discovery",
        "Mistral",
        "P2_k0_unconditional",
    ),
    "DIRECT_PBM_TINY_UNCONDITIONAL": (
        "PBM21 scorer robustness",
        "TinyDialogues",
        "P2_k0_unconditional",
    ),
    "DIRECT_NONPBM_MISTRAL_UNCONDITIONAL": (
        "non-PBM58 confirmation",
        "Mistral",
        "P2_k0_unconditional",
    ),
    "DIRECT_PBM_MISTRAL_CONTEXT_GAIN": (
        "PBM21 discovery",
        "Mistral",
        "P3_k3_context_gain",
    ),
    "DIRECT_PBM_TINY_CONTEXT_GAIN": (
        "PBM21 scorer robustness",
        "TinyDialogues",
        "P3_k3_context_gain",
    ),
    "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN": (
        "non-PBM58 confirmation",
        "Mistral",
        "P3_k3_context_gain",
    ),
    "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY": (
        "non-PBM58 confirmation",
        "Mistral",
        "P1_k3_contextual",
    ),
}

_HALL_SELECTORS = {
    "HALL_RACE_CLASS_INTERACTION": (
        "H1_k0_primary",
        "race_by_class_interaction",
    ),
    "HALL_ADULT_CONTEXT_INTERACTION": (
        "H9_gain_k3_adult_adjacent",
        "race_by_class_interaction",
    ),
    "HALL_LOCKED_DOMAIN_SHIFT": (
        "E1_k0_locked_snapshot",
        "hall_minus_current",
    ),
}

_TRAJECTORY_REMEDIATION_ALLOWLIST = (
    "configs/august_supervisor_report_v1.json",
    "src/august_supervisor/sections.py",
    "tests/test_august_supervisor_report_spec.py",
    "tests/test_august_supervisor_report.py",
    "tests/test_august_supervisor_index.py",
    "docs/august_supervisor_report_spec.md",
    "docs/august_supervisor_report.md",
    "docs/august_supervisor_report.html",
    "docs/august_supervisor_index.html",
    "results/august_supervisor_report/dataset_manifest.json",
    "results/august_supervisor_report/effect_registry.csv",
    "results/august_supervisor_report/model_results_manifest.json",
    "results/august_supervisor_report/headline_findings.csv",
    "results/august_supervisor_report/page_registry.csv",
    "results/august_supervisor_report/synthesis_manifest.json",
    "results/august_supervisor_report/plots/figure_manifest.csv",
    "results/august_supervisor_report/plots/plot_manifest.json",
    "results/august_supervisor_report/report_trace.json",
    "results/august_supervisor_report/report_manifest.json",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    claim_id: str | None
    file: str
    evidence: str
    required_action: str
    remediation_file_allowlist: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "code": self.code,
            "claim_id": self.claim_id,
            "file": self.file,
            "evidence": self.evidence,
            "required_action": self.required_action,
            "remediation_file_allowlist": list(self.remediation_file_allowlist),
        }


def _finding(
    severity: str,
    code: str,
    *,
    claim_id: str | None,
    file: str,
    evidence: str,
    required_action: str,
    remediation: Sequence[str],
) -> dict[str, object]:
    if severity not in SEVERITY_ORDER:
        raise ValueError(f"unknown audit severity: {severity}")
    return Finding(
        severity=severity,
        code=code,
        claim_id=claim_id,
        file=file,
        evidence=evidence,
        required_action=required_action,
        remediation_file_allowlist=tuple(sorted(set(remediation))),
    ).as_dict()


def _rooted(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ContractError(f"audit path is outside repository root: {path}") from error
    return resolved


def _relative(path: Path | str, root: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _json_list(value: str, location: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ContractError(f"{location} is not valid JSON") from error
    if type(parsed) is not list or any(type(item) is not str for item in parsed):
        raise ContractError(f"{location} must be a JSON list of strings")
    return parsed


def _same_number(left: Any, right: Any, *, tolerance: float = 5e-7) -> bool:
    if left in (None, "") or right in (None, ""):
        return left in (None, "") and right in (None, "")
    try:
        return math.isclose(
            float(left), float(right), rel_tol=0.0, abs_tol=tolerance
        )
    except (TypeError, ValueError):
        return False


def _select_one(
    rows: Sequence[Mapping[str, str]], **criteria: str
) -> Mapping[str, str] | None:
    selected = [
        row
        for row in rows
        if all(row.get(column) == expected for column, expected in criteria.items())
    ]
    return selected[0] if len(selected) == 1 else None


def _canonical_numeric_values(
    claim: Mapping[str, Any], source: Any
) -> tuple[Any, Any, Any] | None:
    """Independently select the frozen numeric result from its canonical source."""

    claim_id = claim["claim_id"]
    if claim_id in _DIRECT_SELECTORS:
        sample, scorer, model_id = _DIRECT_SELECTORS[claim_id]
        row = _select_one(
            source,
            sample=sample,
            scorer=scorer,
            model_id=model_id,
            term="age_c",
        )
        return None if row is None else (row["estimate"], row["ci_low"], row["ci_high"])
    if claim_id == "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP":
        row = _select_one(
            source,
            scope="non_pbm_confirmation",
            model_id="P1_k3_contextual",
            outcome="real_k3_sum_bits",
        )
        return (
            None
            if row is None
            else (
                row["bootstrap_mean"],
                row["bootstrap_ci_low"],
                row["bootstrap_ci_high"],
            )
        )
    if claim_id == "DIRECT_PAIRED_CONTEXTUAL_SCORER_DIFFERENCE":
        row = _select_one(source, outcome="real_k3_sum_bits")
        return (
            None
            if row is None
            else (
                row["slope_difference_left_minus_right"],
                row["difference_ci_low"],
                row["difference_ci_high"],
            )
        )
    if claim_id in {"ROUTE2_RELATIVE_EFFORT_AGE", "ROUTE2_AGE_ENTROPY_INTERACTION"}:
        term = (
            "age_months_c"
            if claim_id == "ROUTE2_RELATIVE_EFFORT_AGE"
            else "age_months_c:response_entropy_bits_c"
        )
        row = _select_one(
            source,
            model_id="minus_gen_mean_r2m5_age_by_entropy",
            estimator_id="session_gee_exchangeable",
            outcome="child_words_minus_generated_mean",
            term=term,
        )
        return None if row is None else (row["estimate"], row["conf_low"], row["conf_high"])
    if claim_id == "BAYES_REAL_CANDIDATE_SET_PROBABILITY":
        if type(source) is list and len(source) == 1:
            return (source[0]["combined_rank1_rate"], None, None)
        return None
    if claim_id == "BAYES_HELDOUT_CONTEXT_VALIDATION":
        if type(source) is not list:
            return None
        passed = sum(row.get("pass") == "True" for row in source)
        return (passed, None, None)
    if claim_id in _HALL_SELECTORS:
        model_id, contrast_id = _HALL_SELECTORS[claim_id]
        row = _select_one(source, model_id=model_id, contrast_id=contrast_id)
        return None if row is None else (row["estimate"], row["ci_low"], row["ci_high"])
    return None


def _sorted_findings(findings: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        findings,
        key=lambda item: (
            SEVERITY_ORDER[str(item["severity"])],
            str(item["code"]),
            str(item["claim_id"] or ""),
            str(item["file"]),
        ),
    )


def audit_claim_reconciliation(
    *,
    root: Path | str,
    configuration_path: Path | str = DEFAULT_CONFIGURATION,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
    plot_dir: Path | str = DEFAULT_PLOT_DIR,
    report_trace_path: Path | str | None = None,
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    """Trace claims from hash-locked sources through plots and report trace."""

    base = Path(root).resolve()
    configuration_file = _rooted(configuration_path, base)
    inputs = _rooted(input_dir, base)
    plots = _rooted(plot_dir, base)
    trace_file = _rooted(
        inputs / "report_trace.json"
        if report_trace_path is None
        else report_trace_path,
        base,
    )
    findings: list[dict[str, object]] = []
    config = _read_json(configuration_file)
    claims = {claim["claim_id"]: claim for claim in config["claims"]}
    if len(claims) != len(config["claims"]):
        findings.append(
            _finding(
                "CRITICAL",
                "DUPLICATE_FROZEN_CLAIM",
                claim_id=None,
                file=_relative(configuration_file, base),
                evidence="The frozen configuration contains duplicate claim IDs.",
                required_action="Restore one unambiguous record per frozen claim ID.",
                remediation=(_relative(configuration_file, base),),
            )
        )

    registry_paths = {
        "samples": inputs / "sample_registry.csv",
        "models": inputs / "model_inventory.csv",
        "effects": inputs / "effect_registry.csv",
        "blockers": inputs / "declared_blockers.csv",
    }
    registries = {name: _read_csv(path) for name, path in registry_paths.items()}
    samples = {row["sample_id"]: row for row in registries["samples"]}
    models = {row["model_id"]: row for row in registries["models"]}
    effects = {row["claim_id"]: row for row in registries["effects"]}
    blockers = {row["claim_id"]: row for row in registries["blockers"]}

    synthesis_paths = (
        inputs / "headline_findings.csv",
        inputs / "supporting_findings.csv",
        inputs / "coverage_and_limitations.csv",
    )
    synthesis_rows = [row for path in synthesis_paths for row in _read_csv(path)]
    synthesis = {row["claim_id"]: row for row in synthesis_rows}
    if len(synthesis) != len(synthesis_rows):
        findings.append(
            _finding(
                "CRITICAL",
                "DUPLICATE_SYNTHESIS_CLAIM",
                claim_id=None,
                file=", ".join(_relative(path, base) for path in synthesis_paths),
                evidence="A claim ID occurs more than once across the synthesis tables.",
                required_action="Restore the one-claim/one-synthesis-row contract.",
                remediation=tuple(_relative(path, base) for path in synthesis_paths),
            )
        )

    source_cache: dict[str, Any] = {}
    source_hash_mismatch_count = 0
    canonical_number_count = 0
    for claim_id, claim in sorted(claims.items()):
        source_relative = claim["source"]["canonical_artifact"]
        source_path = _rooted(source_relative, base)
        observed_source_hash = sha256_file(source_path) if source_path.is_file() else None
        if observed_source_hash != claim["source"]["source_sha256"]:
            source_hash_mismatch_count += 1
            findings.append(
                _finding(
                    "CRITICAL",
                    "CANONICAL_SOURCE_HASH_MISMATCH",
                    claim_id=claim_id,
                    file=source_relative,
                    evidence=(
                        f"expected {claim['source']['source_sha256']}; "
                        f"observed {observed_source_hash or 'MISSING'}"
                    ),
                    required_action="Restore or re-freeze the canonical source before rebuilding downstream products.",
                    remediation=(source_relative, _relative(configuration_file, base)),
                )
            )
            continue
        if source_relative not in source_cache:
            if source_path.suffix == ".csv":
                source_cache[source_relative] = _read_csv(source_path)
            elif source_path.suffix == ".json":
                source_cache[source_relative] = _read_json(source_path)
            else:
                source_cache[source_relative] = None

        marker_relative = claim["source"]["required_marker"]["path"]
        marker_path = (
            None if marker_relative is None else _rooted(marker_relative, base)
        )
        if marker_path is not None and not marker_path.is_file():
            findings.append(
                _finding(
                    "CRITICAL",
                    "MISSING_REQUIRED_AUDIT_MARKER",
                    claim_id=claim_id,
                    file=marker_relative,
                    evidence="The frozen claim's required upstream audit marker is missing.",
                    required_action="Restore the audited marker; do not promote the claim without it.",
                    remediation=(marker_relative,),
                )
            )

        pending = claim["evidence_status"] == "PENDING"
        evidence_row = blockers.get(claim_id) if pending else effects.get(claim_id)
        expected_kind = "blocker" if pending else "effect"
        if evidence_row is None:
            findings.append(
                _finding(
                    "CRITICAL",
                    "MISSING_REGISTERED_EVIDENCE_ROW",
                    claim_id=claim_id,
                    file=_relative(
                        registry_paths["blockers" if pending else "effects"], base
                    ),
                    evidence=f"No {expected_kind} registry row resolves this frozen claim.",
                    required_action=f"Rebuild the {expected_kind} registry from the unchanged frozen claim.",
                    remediation=(
                        _relative(registry_paths["blockers" if pending else "effects"], base),
                    ),
                )
            )
            continue

        expected_source_fields = {
            "source_artifact": source_relative,
            "source_sha256": claim["source"]["source_sha256"],
            "audit_marker": marker_relative or "",
        }
        for field, expected in expected_source_fields.items():
            if evidence_row.get(field) != expected:
                findings.append(
                    _finding(
                        "CRITICAL",
                        "CLAIM_PROVENANCE_DRIFT",
                        claim_id=claim_id,
                        file=_relative(
                            registry_paths["blockers" if pending else "effects"], base
                        ),
                        evidence=(
                            f"{field}: expected {expected!r}; "
                            f"observed {evidence_row.get(field)!r}"
                        ),
                        required_action="Re-extract the registry from the hash-locked frozen claim.",
                        remediation=(
                            _relative(registry_paths["blockers" if pending else "effects"], base),
                        ),
                    )
                )
        if (
            marker_path is not None
            and marker_path.is_file()
            and evidence_row.get("audit_marker_sha256") != sha256_file(marker_path)
        ):
            findings.append(
                _finding(
                    "CRITICAL",
                    "AUDIT_MARKER_HASH_MISMATCH",
                    claim_id=claim_id,
                    file=marker_relative,
                    evidence=(
                        f"registry records {evidence_row.get('audit_marker_sha256')}; "
                        f"actual marker is {sha256_file(marker_path)}"
                    ),
                    required_action="Restore the audited marker or rebuild the registry from the current frozen marker.",
                    remediation=(
                        marker_relative,
                        _relative(registry_paths["blockers" if pending else "effects"], base),
                    ),
                )
            )

        sample_id = evidence_row.get("sample_id", f"SAMPLE_{claim_id}")
        sample_row = samples.get(sample_id)
        if sample_row is None:
            findings.append(
                _finding(
                    "CRITICAL",
                    "MISSING_SAMPLE_TRACE",
                    claim_id=claim_id,
                    file=_relative(registry_paths["samples"], base),
                    evidence=f"Evidence row points to absent sample {sample_id!r}.",
                    required_action="Restore the claim's sample-registry row.",
                    remediation=(_relative(registry_paths["samples"], base),),
                )
            )
        else:
            for field in ("rows", "children", "sessions", "corpora"):
                expected = claim["sample"][field]
                observed = sample_row.get(field) or None
                expected_text = None if expected is None else str(expected)
                if expected_text != observed:
                    findings.append(
                        _finding(
                            "CRITICAL",
                            "CLAIM_SAMPLE_COUNT_MISMATCH",
                            claim_id=claim_id,
                            file=_relative(registry_paths["samples"], base),
                            evidence=(
                                f"{field}: expected {expected_text!r}; observed {observed!r}"
                            ),
                            required_action="Re-extract sample counts from the frozen claim without recomputing models.",
                            remediation=(_relative(registry_paths["samples"], base),),
                        )
                    )

        if not pending:
            result = claim["numerical_result"]
            expected_numbers = {
                "estimate": None if result is None else result["estimate"],
                "ci_level": (
                    None
                    if result is None or result["interval"] is None
                    else result["interval"]["level"]
                ),
                "ci_low": (
                    None
                    if result is None or result["interval"] is None
                    else result["interval"]["low"]
                ),
                "ci_high": (
                    None
                    if result is None or result["interval"] is None
                    else result["interval"]["high"]
                ),
            }
            for field, expected in expected_numbers.items():
                if not _same_number(expected, evidence_row.get(field), tolerance=1e-12):
                    findings.append(
                        _finding(
                            "CRITICAL",
                            "CLAIM_EFFECT_NUMBER_MISMATCH",
                            claim_id=claim_id,
                            file=_relative(registry_paths["effects"], base),
                            evidence=(
                                f"{field}: frozen={expected!r}; "
                                f"effect={evidence_row.get(field)!r}"
                            ),
                            required_action="Re-extract the effect row from the frozen configuration and canonical source.",
                            remediation=(_relative(registry_paths["effects"], base),),
                        )
                    )
            canonical = _canonical_numeric_values(
                claim, source_cache[source_relative]
            )
            if result is not None and result["estimate"] is not None:
                canonical_number_count += 1
                expected_tuple = (
                    result["estimate"],
                    None if result["interval"] is None else result["interval"]["low"],
                    None if result["interval"] is None else result["interval"]["high"],
                )
                if canonical is None or any(
                    not _same_number(expected, observed)
                    for expected, observed in zip(expected_tuple, canonical)
                ):
                    findings.append(
                        _finding(
                            "CRITICAL",
                            "CANONICAL_SOURCE_NUMBER_MISMATCH",
                            claim_id=claim_id,
                            file=source_relative,
                            evidence=f"frozen={expected_tuple!r}; canonical={canonical!r}",
                            required_action="Correct the frozen claim from its registered canonical row, then rebuild every dependent stage.",
                            remediation=(
                                _relative(configuration_file, base),
                                source_relative,
                            ),
                        )
                    )
            model_id = evidence_row.get("model_id")
            if model_id and (
                model_id not in models or models[model_id].get("claim_id") != claim_id
            ):
                findings.append(
                    _finding(
                        "CRITICAL",
                        "MODEL_EFFECT_TRACE_MISMATCH",
                        claim_id=claim_id,
                        file=_relative(registry_paths["models"], base),
                        evidence=f"Effect points to unresolved or cross-claim model {model_id!r}.",
                        required_action="Restore the model/effect foreign-key trace.",
                        remediation=(
                            _relative(registry_paths["models"], base),
                            _relative(registry_paths["effects"], base),
                        ),
                    )
                )

        synthesis_row = synthesis.get(claim_id)
        if synthesis_row is None:
            findings.append(
                _finding(
                    "CRITICAL",
                    "MISSING_SYNTHESIS_TRACE",
                    claim_id=claim_id,
                    file=", ".join(_relative(path, base) for path in synthesis_paths),
                    evidence="The frozen claim has no synthesis row.",
                    required_action="Rebuild synthesis from the unchanged compact registries.",
                    remediation=tuple(_relative(path, base) for path in synthesis_paths),
                )
            )
        else:
            expected_evidence_id = (
                f"BLOCKER_{claim_id}" if pending else f"EFFECT_{claim_id}"
            )
            synthesis_expectations = {
                "classification": claim["evidence_status"],
                "evidence_id": expected_evidence_id,
                "finding": claim["required_interpretation"],
            }
            for field, expected in synthesis_expectations.items():
                if synthesis_row.get(field) != expected:
                    findings.append(
                        _finding(
                            "CRITICAL",
                            "SYNTHESIS_CLAIM_DRIFT",
                            claim_id=claim_id,
                            file=next(
                                _relative(path, base)
                                for path in synthesis_paths
                                if synthesis_row in _read_csv(path)
                            ),
                            evidence=(
                                f"{field}: expected {expected!r}; "
                                f"observed {synthesis_row.get(field)!r}"
                            ),
                            required_action="Regenerate the deterministic synthesis row from the registered evidence.",
                            remediation=tuple(_relative(path, base) for path in synthesis_paths),
                        )
                    )
            if not synthesis_row.get("limitation", "").startswith(
                claim["required_limitation"]
            ):
                findings.append(
                    _finding(
                        "MAJOR",
                        "SYNTHESIS_LIMITATION_DRIFT",
                        claim_id=claim_id,
                        file=", ".join(_relative(path, base) for path in synthesis_paths),
                        evidence="The synthesis limitation no longer begins with the frozen required limitation.",
                        required_action="Restore the frozen limitation and any registered blocker detail.",
                        remediation=tuple(_relative(path, base) for path in synthesis_paths),
                    )
                )

    expected_claims = set(claims)
    observed_effect_or_blocker = set(effects) | set(blockers)
    for label, observed, paths in (
        (
            "registered evidence",
            observed_effect_or_blocker,
            (registry_paths["effects"], registry_paths["blockers"]),
        ),
        ("synthesis", set(synthesis), synthesis_paths),
    ):
        if observed != expected_claims:
            findings.append(
                _finding(
                    "CRITICAL",
                    "CLAIM_COVERAGE_MISMATCH",
                    claim_id=None,
                    file=", ".join(_relative(path, base) for path in paths),
                    evidence=(
                        f"{label}: missing={sorted(expected_claims - observed)}; "
                        f"extra={sorted(observed - expected_claims)}"
                    ),
                    required_action="Restore exact one-to-one frozen claim coverage.",
                    remediation=tuple(_relative(path, base) for path in paths),
                )
            )

    figure_rows = _read_csv(plots / "figure_manifest.csv")
    numeric_plot_rows = 0
    for figure in figure_rows:
        claim_ids = _json_list(figure["claim_ids"], f"{figure['figure_id']}.claim_ids")
        effect_ids = set(
            _json_list(figure["effect_ids"], f"{figure['figure_id']}.effect_ids")
        )
        plot_data_path = plots / Path(figure["plot_data_path"]).name
        if sha256_file(plot_data_path) != figure["plot_data_sha256"]:
            findings.append(
                _finding(
                    "CRITICAL",
                    "FIGURE_DATA_HASH_MISMATCH",
                    claim_id=None,
                    file=_relative(plot_data_path, base),
                    evidence="Plot-data bytes differ from the figure-manifest hash.",
                    required_action="Restore the frozen plot data and rerun the plot/report chain.",
                    remediation=(
                        _relative(plot_data_path, base),
                        _relative(plots / "figure_manifest.csv", base),
                    ),
                )
            )
        for row in _read_csv(plot_data_path):
            claim_id = row["claim_id"]
            effect = effects.get(claim_id)
            if claim_id not in claim_ids or row["effect_id"] not in effect_ids or effect is None:
                findings.append(
                    _finding(
                        "CRITICAL",
                        "PLOT_CLAIM_TRACE_MISMATCH",
                        claim_id=claim_id,
                        file=_relative(plot_data_path, base),
                        evidence="Plot row is not resolved by its figure and effect registries.",
                        required_action="Regenerate plot data from the compact registered evidence.",
                        remediation=(
                            _relative(plot_data_path, base),
                            _relative(plots / "figure_manifest.csv", base),
                        ),
                    )
                )
                continue
            if row["value_kind"] == "NUMERIC":
                numeric_plot_rows += 1
                for field in ("estimate", "ci_level", "ci_low", "ci_high"):
                    if not _same_number(
                        effect.get(field), row.get(field), tolerance=1e-12
                    ):
                        findings.append(
                            _finding(
                                "CRITICAL",
                                "PLOT_EFFECT_NUMBER_MISMATCH",
                                claim_id=claim_id,
                                file=_relative(plot_data_path, base),
                                evidence=(
                                    f"{field}: effect={effect.get(field)!r}; "
                                    f"plot={row.get(field)!r}"
                                ),
                                required_action="Rebuild plot data from the frozen effect registry.",
                                remediation=(_relative(plot_data_path, base),),
                            )
                        )
            for field in (
                "source_artifact",
                "source_sha256",
                "audit_marker",
                "audit_marker_sha256",
            ):
                if row.get(field) != effect.get(field):
                    findings.append(
                        _finding(
                            "CRITICAL",
                            "PLOT_PROVENANCE_MISMATCH",
                            claim_id=claim_id,
                            file=_relative(plot_data_path, base),
                            evidence=(
                                f"{field}: effect={effect.get(field)!r}; "
                                f"plot={row.get(field)!r}"
                            ),
                            required_action="Restore the source provenance copied from the registered effect.",
                            remediation=(_relative(plot_data_path, base),),
                        )
                    )

    trace = _read_json(trace_file)
    trace_claims = set(trace.get("resolved_claim_ids", []))
    section_claims = {
        claim_id
        for section in trace.get("sections", [])
        for claim_id in section.get("claim_ids", [])
    }
    if trace_claims != expected_claims or section_claims != expected_claims:
        findings.append(
            _finding(
                "CRITICAL",
                "REPORT_CLAIM_TRACE_MISMATCH",
                claim_id=None,
                file=_relative(trace_file, base),
                evidence=(
                    f"resolved missing={sorted(expected_claims - trace_claims)}, "
                    f"section missing={sorted(expected_claims - section_claims)}, "
                    f"extra={sorted((trace_claims | section_claims) - expected_claims)}"
                ),
                required_action="Regenerate the report trace from the complete synthesis registry.",
                remediation=(_relative(trace_file, base),),
            )
        )

    index_source = (_rooted(DEFAULT_INDEX_HTML, base)).read_text(encoding="utf-8")
    landing_claims = set(
        re.findall(r'data-claim-id="([A-Z][A-Z0-9_]+)"', index_source)
    )
    for group in re.findall(r'data-claim-ids="([A-Z0-9_ ]+)"', index_source):
        landing_claims.update(group.split())
    unknown_landing = landing_claims - expected_claims
    if unknown_landing:
        findings.append(
            _finding(
                "CRITICAL",
                "LANDING_CLAIM_TRACE_MISMATCH",
                claim_id=None,
                file=_relative(_rooted(DEFAULT_INDEX_HTML, base), base),
                evidence=f"Unregistered landing-page claim IDs: {sorted(unknown_landing)}",
                required_action="Resolve every landing claim to the frozen registry.",
                remediation=("src/august_supervisor/index.py", "docs/august_supervisor_index.html"),
            )
        )

    summary = {
        "claim_count": len(claims),
        "effect_count": len(effects),
        "blocker_count": len(blockers),
        "model_count": len(models),
        "sample_count": len(samples),
        "synthesis_claim_count": len(synthesis),
        "report_trace_claim_count": len(trace_claims),
        "landing_claim_count": len(landing_claims),
        "figure_count": len(figure_rows),
        "numeric_plot_row_count": numeric_plot_rows,
        "canonical_number_count": canonical_number_count,
        "source_hash_mismatch_count": source_hash_mismatch_count,
    }
    return _sorted_findings(findings), summary


_DISPLAY_REQUIREMENTS = (
    (
        "DIRECT_PBM_MISTRAL_CONTEXTUAL",
        "21-child",
        "PBM discovery sample size",
        ("markdown", "html", "index"),
    ),
    (
        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
        "58-child",
        "non-PBM confirmation sample size",
        ("markdown", "html", "index"),
    ),
    (
        "CONVERSATIONAL_MANUAL_VALIDATION",
        "325-row",
        "manual-validation sample size",
        ("markdown", "html"),
    ),
    (
        "CONVERSATIONAL_MANUAL_VALIDATION",
        "18,172",
        "context-k1 mismatch count",
        ("markdown", "html"),
    ),
    (
        "BAYES_REAL_CANDIDATE_SET_PROBABILITY",
        "43.7%",
        "rounded rank-first percentage",
        ("markdown", "html"),
    ),
    (
        "BAYES_REAL_CANDIDATE_SET_PROBABILITY",
        "0.400",
        "three-decimal candidate-set mean probability",
        ("markdown", "html"),
    ),
    (
        "ROUTE2_RELATIVE_EFFORT_AGE",
        "976",
        "PBM child-session aggregate count",
        ("markdown", "html"),
    ),
    (
        "ONSET_PBM_SUSTAINED",
        "24-29-month",
        "nominal age-bin label retained only as a non-promoted contrast",
        ("markdown", "html"),
    ),
)


def audit_number_formatting(
    *,
    root: Path | str,
    configuration_path: Path | str = DEFAULT_CONFIGURATION,
    markdown_path: Path | str = DEFAULT_REPORT_MARKDOWN,
    html_path: Path | str = DEFAULT_REPORT_HTML,
    index_path: Path | str = DEFAULT_INDEX_HTML,
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    """Require the exact claim-registered display precision and grouping."""

    base = Path(root).resolve()
    configuration_file = _rooted(configuration_path, base)
    config = _read_json(configuration_file)
    claims = {claim["claim_id"]: claim for claim in config["claims"]}
    paths = {
        "markdown": _rooted(markdown_path, base),
        "html": _rooted(html_path, base),
        "index": _rooted(index_path, base),
    }
    sources = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}
    findings: list[dict[str, object]] = []
    checked = 0
    for claim_id, token, label, documents in _DISPLAY_REQUIREMENTS:
        checked += 1
        if claim_id not in claims:
            findings.append(
                _finding(
                    "CRITICAL",
                    "UNREGISTERED_DISPLAY_NUMBER",
                    claim_id=claim_id,
                    file=_relative(configuration_file, base),
                    evidence=f"No frozen claim supports {label}: {token!r}.",
                    required_action="Register the number or remove it from the product.",
                    remediation=(_relative(configuration_file, base),),
                )
            )
            continue
        for document in documents:
            if token not in sources[document]:
                findings.append(
                    _finding(
                        "MAJOR",
                        "NUMBER_FORMAT_DRIFT",
                        claim_id=claim_id,
                        file=_relative(paths[document], base),
                        evidence=f"Missing exact locked presentation {token!r} for {label}.",
                        required_action="Restore the registered rounding/grouping without changing the frozen estimate.",
                        remediation=(
                            "src/august_supervisor/sections.py",
                            "src/august_supervisor/index.py",
                            _relative(paths[document], base),
                        ),
                    )
                )
    forbidden_variants = {
        "43.70%": "43.7%",
        "43.6671%": "43.7%",
        "0.40 ": "0.400",
        "18,172.0": "18,172",
        "18172": "18,172",
        "24–29-month": "24-29-month",
    }
    for name, source in sources.items():
        for bad, expected in forbidden_variants.items():
            if bad in source:
                findings.append(
                    _finding(
                        "MAJOR",
                        "NUMBER_FORMAT_DRIFT",
                        claim_id=None,
                        file=_relative(paths[name], base),
                        evidence=f"Observed {bad!r}; frozen display is {expected!r}.",
                        required_action="Restore the exact claim-locked formatting.",
                        remediation=(
                            "src/august_supervisor/sections.py",
                            "src/august_supervisor/index.py",
                            _relative(paths[name], base),
                        ),
                    )
                )
    return _sorted_findings(findings), {
        "locked_display_count": checked,
        "document_count": len(paths),
    }


def _walk_manifest_chain(path: Path, root: Path) -> list[str]:
    record = _read_json(path)
    stages: list[str] = []
    for upstream in record.get("upstream_manifests", []):
        stages.extend(_walk_manifest_chain(_rooted(upstream["path"], root), root))
    stages.append(record["stage_id"])
    return stages


def audit_manifest_hashes(
    *, root: Path | str, report_manifest_path: Path | str
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    """Rehash the complete datasets-to-report manifest chain."""

    base = Path(root).resolve()
    manifest = _rooted(report_manifest_path, base)
    findings: list[dict[str, object]] = []
    stages: list[str] = []
    try:
        verify_stage_manifest(manifest, root=base, expected_stage="report")
        stages = _walk_manifest_chain(manifest, base)
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as error:
        findings.append(
            _finding(
                "CRITICAL",
                "MANIFEST_HASH_MISMATCH",
                claim_id=None,
                file=_relative(manifest, base),
                evidence=str(error),
                required_action="Restore the last valid hash-chained stage products and rebuild only the affected downstream stages.",
                remediation=(_relative(manifest, base),),
            )
        )
    return _sorted_findings(findings), {
        "verified_stage_chain": stages,
        "manifest_path": _relative(manifest, base),
        "manifest_sha256": sha256_file(manifest) if manifest.is_file() else None,
    }


class _HTMLAuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.images: list[tuple[str, str]] = []
        self.lang: str | None = None
        self.title_parts: list[str] = []
        self.in_title = False
        self.main_count = 0
        self.h1_count = 0
        self.viewport = False
        self.skip_links = 0
        self.base_tags = 0
        self.link_text_stack: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if tag == "html":
            self.lang = values.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta" and values.get("name", "").lower() == "viewport":
            self.viewport = bool(values.get("content", "").strip())
        elif tag == "main":
            self.main_count += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "base":
            self.base_tags += 1
        elif tag == "a":
            href = values.get("href") or ""
            self.link_text_stack.append((href, []))
            if "skip-link" in (values.get("class") or "").split():
                self.skip_links += 1
        elif tag == "img":
            self.images.append((values.get("src") or "", values.get("alt") or ""))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "a" and self.link_text_stack:
            href, parts = self.link_text_stack.pop()
            self.links.append((href, " ".join(parts).strip()))

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.link_text_stack:
            self.link_text_stack[-1][1].append(data)


def _parse_html(path: Path) -> tuple[_HTMLAuditParser, str]:
    source = path.read_text(encoding="utf-8")
    parser = _HTMLAuditParser()
    parser.feed(source)
    parser.close()
    return parser, source


def _visible_word_count(source: str) -> int:
    without_code = re.sub(
        r"<(?:style|script)\b.*?</(?:style|script)>", " ", source, flags=re.I | re.S
    )
    return len(re.findall(r"\b[\w’'-]+\b", html.unescape(re.sub(r"<[^>]+>", " ", without_code))))


def _local_reference_target(reference: str, source_path: Path, root: Path) -> tuple[Path, str]:
    split = urlsplit(reference)
    raw_path = unquote(split.path)
    target = source_path if not raw_path else (source_path.parent / raw_path).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ContractError(f"local reference escapes repository root: {reference}") from error
    return target, unquote(split.fragment)


def audit_html_package(
    *,
    root: Path | str,
    html_paths: Sequence[Path | str],
    figure_manifest_path: Path | str | None,
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    """Audit source, accessibility, links, images, fragments, and shareability."""

    base = Path(root).resolve()
    documents = tuple(_rooted(path, base) for path in html_paths)
    expected_images: dict[Path, str] = {}
    if figure_manifest_path is not None:
        figure_manifest = _rooted(figure_manifest_path, base)
        for row in _read_csv(figure_manifest):
            expected_images[_rooted(row["image_path"], base)] = row["image_sha256"]
    findings: list[dict[str, object]] = []
    fragment_cache: dict[Path, set[str]] = {}
    local_reference_count = 0
    external_reference_count = 0
    missing_target_count = 0
    empty_alt_count = 0
    checked_images: set[Path] = set()

    for document in documents:
        parser, source = _parse_html(document)
        fragment_cache[document] = set(parser.ids)
        relative_document = _relative(document, base)
        accessibility_problems = []
        if parser.lang != "en":
            accessibility_problems.append("missing html lang=en")
        if not "".join(parser.title_parts).strip():
            accessibility_problems.append("empty title")
        if not parser.viewport:
            accessibility_problems.append("missing viewport metadata")
        if parser.main_count != 1:
            accessibility_problems.append(f"main count={parser.main_count}")
        if parser.h1_count != 1:
            accessibility_problems.append(f"h1 count={parser.h1_count}")
        duplicate_ids = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
        if duplicate_ids:
            accessibility_problems.append(f"duplicate ids={duplicate_ids}")
        if parser.base_tags:
            accessibility_problems.append("base tag makes relative sharing context-dependent")
        if accessibility_problems:
            findings.append(
                _finding(
                    "MAJOR",
                    "HTML_ACCESSIBILITY_BASICS",
                    claim_id=None,
                    file=relative_document,
                    evidence="; ".join(accessibility_problems),
                    required_action="Restore semantic landmarks, unique IDs, language/title/viewport metadata, and context-independent relative paths.",
                    remediation=(relative_document,),
                )
            )
        if "@media" not in source or "max-width" not in source:
            findings.append(
                _finding(
                    "MAJOR",
                    "HTML_RESPONSIVE_LAYOUT_MISSING",
                    claim_id=None,
                    file=relative_document,
                    evidence="No max-width responsive media rule was found.",
                    required_action="Add a tested narrow-viewport layout without changing scientific content.",
                    remediation=(relative_document,),
                )
            )
        if document.name == DEFAULT_INDEX_HTML.name and (
            parser.skip_links < 1 or ":focus-visible" not in source
        ):
            findings.append(
                _finding(
                    "MAJOR",
                    "LANDING_KEYBOARD_ACCESS_MISSING",
                    claim_id=None,
                    file=relative_document,
                    evidence=(
                        f"skip links={parser.skip_links}; focus-visible style="
                        f"{':focus-visible' in source}"
                    ),
                    required_action="Restore the skip link and visible keyboard focus treatment.",
                    remediation=("src/august_supervisor/index.py", relative_document),
                )
            )

        references = [(href, "link", text) for href, text in parser.links] + [
            (src, "image", alt) for src, alt in parser.images
        ]
        for reference, kind, label in references:
            if not reference:
                findings.append(
                    _finding(
                        "MAJOR",
                        "HTML_EMPTY_REFERENCE",
                        claim_id=None,
                        file=relative_document,
                        evidence=f"An empty {kind} reference is present.",
                        required_action="Remove the empty element or provide a resolving target.",
                        remediation=(relative_document,),
                    )
                )
                continue
            split = urlsplit(reference)
            if split.scheme in {"http", "https", "mailto"} or split.netloc:
                external_reference_count += 1
                continue
            if split.scheme or reference.startswith(("/", "\\")):
                findings.append(
                    _finding(
                        "MAJOR",
                        "HTML_NONPORTABLE_REFERENCE",
                        claim_id=None,
                        file=relative_document,
                        evidence=f"Nonportable reference: {reference!r}",
                        required_action="Use a repository-relative link suitable for the external sharing bundle.",
                        remediation=(relative_document,),
                    )
                )
                continue
            local_reference_count += 1
            try:
                target, fragment = _local_reference_target(reference, document, base)
            except ContractError as error:
                findings.append(
                    _finding(
                        "CRITICAL",
                        "HTML_REFERENCE_ESCAPE",
                        claim_id=None,
                        file=relative_document,
                        evidence=str(error),
                        required_action="Replace the escaping reference with an in-package relative target.",
                        remediation=(relative_document,),
                    )
                )
                continue
            if not target.is_file():
                missing_target_count += 1
                findings.append(
                    _finding(
                        "CRITICAL",
                        "HTML_MISSING_TARGET",
                        claim_id=None,
                        file=relative_document,
                        evidence=f"Missing {kind} target {reference!r}.",
                        required_action="Restore the nonempty target or remove the reference through the owning renderer.",
                        remediation=(relative_document,),
                    )
                )
                continue
            if fragment:
                if target.suffix.lower() not in {".html", ".htm"}:
                    fragment_ids: set[str] = set()
                else:
                    if target not in fragment_cache:
                        fragment_cache[target] = set(_parse_html(target)[0].ids)
                    fragment_ids = fragment_cache[target]
                if fragment not in fragment_ids:
                    findings.append(
                        _finding(
                            "MAJOR",
                            "HTML_MISSING_FRAGMENT",
                            claim_id=None,
                            file=relative_document,
                            evidence=f"Fragment {fragment!r} does not exist in {reference!r}.",
                            required_action="Correct the anchor or restore the intended target ID.",
                            remediation=(relative_document,),
                        )
                    )
            if kind == "image":
                checked_images.add(target)
                if not label.strip():
                    empty_alt_count += 1
                    findings.append(
                        _finding(
                            "MAJOR",
                            "HTML_EMPTY_IMAGE_ALT",
                            claim_id=None,
                            file=relative_document,
                            evidence=f"Image {reference!r} has empty alternative text.",
                            required_action="Supply claim-consistent descriptive alt text in the owning figure/report renderer.",
                            remediation=(relative_document,),
                        )
                    )
                if target in expected_images and sha256_file(target) != expected_images[target]:
                    findings.append(
                        _finding(
                            "CRITICAL",
                            "HTML_IMAGE_HASH_MISMATCH",
                            claim_id=None,
                            file=_relative(target, base),
                            evidence=(
                                f"expected {expected_images[target]}; observed {sha256_file(target)}"
                            ),
                            required_action="Restore the hash-locked figure or rerun the affected plot/report stages after authorized remediation.",
                            remediation=(_relative(target, base),),
                        )
                    )
            elif target.suffix.lower() in {".html", ".htm"}:
                target_source = target.read_text(encoding="utf-8", errors="replace")
                if _visible_word_count(target_source) < 40:
                    findings.append(
                        _finding(
                            "MAJOR",
                            "HTML_EMPTY_SHELL_TARGET",
                            claim_id=None,
                            file=_relative(target, base),
                            evidence=f"Linked HTML target has only {_visible_word_count(target_source)} visible words.",
                            required_action="Link a substantive audited resource or remove the empty shell.",
                            remediation=(relative_document, _relative(target, base)),
                        )
                    )
            if kind == "link" and label.strip().lower() in {
                "here",
                "click here",
                "read more",
            }:
                findings.append(
                    _finding(
                        "MINOR",
                        "HTML_UNINFORMATIVE_LINK_TEXT",
                        claim_id=None,
                        file=relative_document,
                        evidence=f"Link {reference!r} uses label {label!r}.",
                        required_action="Use destination-specific link text.",
                        remediation=(relative_document,),
                    )
                )

    referenced_expected = checked_images & set(expected_images)
    if expected_images and referenced_expected != set(expected_images):
        missing = sorted(_relative(path, base) for path in set(expected_images) - referenced_expected)
        findings.append(
            _finding(
                "CRITICAL",
                "HTML_FIGURE_COVERAGE_MISMATCH",
                claim_id=None,
                file=_relative(_rooted(figure_manifest_path, base), base),
                evidence=f"Hash-locked report figures not referenced by audited HTML: {missing}",
                required_action="Restore exact figure coverage in the integrated HTML report.",
                remediation=(
                    "src/august_supervisor/render.py",
                    _relative(_rooted(DEFAULT_REPORT_HTML, base), base),
                ),
            )
        )
    return _sorted_findings(findings), {
        "html_document_count": len(documents),
        "local_reference_count": local_reference_count,
        "external_reference_count": external_reference_count,
        "expected_image_count": len(expected_images),
        "checked_expected_image_count": len(referenced_expected),
        "missing_target_count": missing_target_count,
        "empty_alt_count": empty_alt_count,
    }


def _contains_all(source: str, fragments: Sequence[str]) -> bool:
    lowered = source.lower()
    return all(fragment.lower() in lowered for fragment in fragments)


def audit_scientific_language(
    *,
    root: Path | str,
    configuration_path: Path | str = DEFAULT_CONFIGURATION,
    report_path: Path | str = DEFAULT_REPORT_MARKDOWN,
    index_path: Path | str = DEFAULT_INDEX_HTML,
    trajectory_path: Path | str = DEFAULT_TRAJECTORY_HTML,
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    """Audit eight required guardrail families and prohibited assertions."""

    base = Path(root).resolve()
    config_file = _rooted(configuration_path, base)
    report_file = _rooted(report_path, base)
    index_file = _rooted(index_path, base)
    trajectory_file = _rooted(trajectory_path, base)
    config = _read_json(config_file)
    registered_claims = {claim["claim_id"] for claim in config["claims"]}
    report = report_file.read_text(encoding="utf-8")
    index = index_file.read_text(encoding="utf-8")
    trajectory = trajectory_file.read_text(encoding="utf-8")
    package = "\n".join((report, index))
    findings: list[dict[str, object]] = []

    guardrails = (
        (
            "NONPBM_PRIMARY_CI_GUARDRAIL_MISSING",
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
            report_file,
            report,
            ("non-pbm", "not confirmed", "interval crosses zero", "sensitivity"),
            "State that the frozen primary interval crosses zero and bootstrap evidence is sensitivity only.",
        ),
        (
            "CONTEXT_GAIN_DIRECTION_GUARDRAIL_MISSING",
            "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN",
            report_file,
            report,
            ("context gain declines", "contrary", "positive prediction"),
            "Restore the negative, contrary-to-registered-direction reading.",
        ),
        (
            "CROSS_TOKENIZER_NONPOOLING_MISSING",
            "CROSS_TOKENIZER_MAGNITUDE_POOLING",
            report_file,
            report,
            ("raw bits", "not pooled across tokenizers"),
            "State that raw bits and coefficient magnitudes are not pooled across tokenizer namespaces.",
        ),
        (
            "RESPONSE_ENTROPY_LIMIT_MISSING",
            "RESPONSE_ENTROPY_SEMANTIC_CLAIM",
            report_file,
            report,
            (
                "exact-string response entropy",
                "not semantic uncertainty",
                "model-",
                "prompt-",
                "temperature-",
                "seed-dependent",
            ),
            "Restore every generator-setting and semantic-uncertainty limitation.",
        ),
        (
            "ONSET_NOT_ESTABLISHED_MISSING",
            "ONSET_PBM_SUSTAINED",
            report_file,
            report,
            ("sustained onset is not established", "pbm", "non-pbm"),
            "State the frozen no-sustained-onset result for both samples.",
        ),
        (
            "BAYES_SCOPE_GUARDRAIL_MISSING",
            "BAYES_REAL_CANDIDATE_SET_PROBABILITY",
            report_file,
            report,
            (
                "within the supplied matched candidate set",
                "not a posterior over every possible utterance",
                "not meaning-preserving",
            ),
            "Restore the finite-candidate-set and non-meaning-preserving scope.",
        ),
        (
            "HALL_DESCRIPTIVE_GUARDRAIL_MISSING",
            "HALL_RACE_CLASS_INTERACTION",
            report_file,
            report,
            (
                "historical cross-sectional",
                "descriptive",
                "not a causal ses effect",
                "linguistic deficit",
            ),
            "Restore Hall's separate historical, cross-sectional, descriptive, non-causal reading.",
        ),
    )
    for code, claim_id, path, source, fragments, required_action in guardrails:
        if claim_id not in registered_claims or not _contains_all(source, fragments):
            findings.append(
                _finding(
                    "MAJOR",
                    code,
                    claim_id=claim_id,
                    file=_relative(path, base),
                    evidence=f"Required co-occurring guardrail fragments are absent: {list(fragments)}",
                    required_action=required_action,
                    remediation=(
                        "src/august_supervisor/sections.py",
                        "docs/august_supervisor_report.md",
                        "docs/august_supervisor_report.html",
                    ),
                )
            )

    trajectory_text = f"{report}\n{index}\n{trajectory}".lower()
    trajectory_guardrail = re.search(
        r"heterogen|var(?:y|ies|iation)\s+(?:across|among)\s+(?:children|individual)|"
        r"(?:not|no)\s+(?:one\s+)?universal\s+developmental",
        trajectory_text,
    )
    if trajectory_guardrail is None:
        findings.append(
            _finding(
                "MAJOR",
                "TRAJECTORY_HETEROGENEITY_MISSING",
                claim_id="DIRECT_PBM_MISTRAL_CONTEXTUAL",
                file=(
                    f"{_relative(report_file, base)}; "
                    f"{_relative(trajectory_file, base)}"
                ),
                evidence=(
                    "The package links 21 individual trajectory profiles but nowhere "
                    "states that trajectories are heterogeneous or that the aggregate "
                    "association is not one universal developmental law; the central "
                    "frozen claim's limitation does not carry this profile-level caveat."
                ),
                required_action=(
                    "Extend the frozen central claim and supervisor prose with the "
                    "non-extrapolation limit that individual profiles do not establish "
                    "one universal developmental law; do not add a numerical trajectory "
                    "claim without separately registering its source. Then rebuild the "
                    "hash-chained stages without refitting."
                ),
                remediation=_TRAJECTORY_REMEDIATION_ALLOWLIST,
            )
        )

    prohibited = (
        (
            "PROHIBITED_INTERNAL_LABEL",
            re.compile(r"\broute\s+[12]\b", re.I),
            "Remove internal Route labels from supervisor-facing visible prose.",
        ),
        (
            "PROHIBITED_CAUSAL_HALL_LANGUAGE",
            re.compile(
                r"(?:hall.{0,80}\b(?:proves?|causes?|causal)\b.{0,60}\b(?:ses|race|class|deficit)\b)|"
                r"(?:\bcausal\s+ses\s+deficit\b)",
                re.I | re.S,
            ),
            "Restore Hall's descriptive, non-causal, non-deficit interpretation.",
        ),
        (
            "PROHIBITED_OPTIMALITY_LANGUAGE",
            re.compile(r"\b(?:proves?|establishes?)\b.{0,60}\b(?:optim(?:al|izes?)|pareto)\b", re.I | re.S),
            "Remove unsupported optimization or Pareto claims.",
        ),
    )
    for code, pattern, required_action in prohibited:
        match = pattern.search(package)
        if match:
            findings.append(
                _finding(
                    "CRITICAL",
                    code,
                    claim_id=(
                        "HALL_RACE_CLASS_INTERACTION"
                        if code == "PROHIBITED_CAUSAL_HALL_LANGUAGE"
                        else None
                    ),
                    file=f"{_relative(report_file, base)}; {_relative(index_file, base)}",
                    evidence=f"Matched prohibited visible language: {match.group(0)!r}",
                    required_action=required_action,
                    remediation=(
                        "src/august_supervisor/sections.py",
                        "src/august_supervisor/index.py",
                        "docs/august_supervisor_report.md",
                        "docs/august_supervisor_report.html",
                        "docs/august_supervisor_index.html",
                    ),
                )
            )
    return _sorted_findings(findings), {
        "guardrail_count": 8,
        "registered_claim_count": len(registered_claims),
        "prohibited_pattern_count": len(prohibited),
    }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def audit_deterministic_renders(
    *,
    root: Path | str,
    output_dir: Path | str,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
    plot_dir: Path | str = DEFAULT_PLOT_DIR,
    markdown_path: Path | str = DEFAULT_REPORT_MARKDOWN,
    html_path: Path | str = DEFAULT_REPORT_HTML,
    index_path: Path | str = DEFAULT_INDEX_HTML,
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    """Perform two render-only builds and compare them with frozen products."""

    base = Path(root).resolve()
    output = _rooted(output_dir, base)
    output.mkdir(parents=True, exist_ok=True)
    inputs = _rooted(input_dir, base)
    plots = _rooted(plot_dir, base)
    markdown_file = _rooted(markdown_path, base)
    html_file = _rooted(html_path, base)
    index_file = _rooted(index_path, base)
    findings: list[dict[str, object]] = []
    evidence = load_report_evidence(root=base, input_dir=inputs, plot_dir=plots)
    sections = build_report_sections(evidence)
    index_evidence = load_index_evidence(root=base, input_dir=inputs, plot_dir=plots)

    frozen_hashes = {
        "markdown": sha256_file(markdown_file),
        "html": sha256_file(html_file),
        "index": sha256_file(index_file),
    }
    render_runs = []
    for run_number in (1, 2):
        run_dir = output / f"run_{run_number}"
        run_dir.mkdir(parents=True, exist_ok=True)
        markdown = render_report_markdown(
            evidence, sections, markdown_path=markdown_file
        )
        rendered_markdown = run_dir / "august_supervisor_report.md"
        rendered_html = run_dir / "august_supervisor_report.html"
        rendered_index = run_dir / "august_supervisor_index.html"
        rendered_markdown.write_text(markdown, encoding="utf-8", newline="\n")
        render_markdown_file(
            rendered_markdown,
            rendered_html,
            title="August 2026 Supervisor Report",
            embed_images=False,
        )
        rendered_index.write_text(
            render_index_html(index_evidence, html_path=index_file),
            encoding="utf-8",
            newline="\n",
        )
        hashes = {
            "markdown": sha256_file(rendered_markdown),
            "html": sha256_file(rendered_html),
            "index": sha256_file(rendered_index),
        }
        render_runs.append(
            {
                "run": run_number,
                "artifact_sha256": hashes,
                "bundle_sha256": _sha256_bytes(_canonical_json_bytes(hashes)),
            }
        )

    if render_runs[0]["bundle_sha256"] != render_runs[1]["bundle_sha256"]:
        findings.append(
            _finding(
                "CRITICAL",
                "NONDETERMINISTIC_RENDER",
                claim_id=None,
                file="src/august_supervisor/render.py; src/august_supervisor/index.py",
                evidence=f"run hashes differ: {render_runs}",
                required_action="Remove nondeterministic render inputs and prove two byte-identical rebuilds.",
                remediation=(
                    "src/august_supervisor/render.py",
                    "src/august_supervisor/index.py",
                ),
            )
        )
    matches_frozen = render_runs[0]["artifact_sha256"] == frozen_hashes
    if not matches_frozen:
        findings.append(
            _finding(
                "CRITICAL",
                "FROZEN_PRODUCT_RENDER_DRIFT",
                claim_id=None,
                file=(
                    "docs/august_supervisor_report.md; "
                    "docs/august_supervisor_report.html; "
                    "docs/august_supervisor_index.html"
                ),
                evidence=(
                    f"frozen={frozen_hashes}; "
                    f"fresh={render_runs[0]['artifact_sha256']}"
                ),
                required_action="Rebuild the affected products from the unchanged frozen inputs and re-audit.",
                remediation=(
                    "docs/august_supervisor_report.md",
                    "docs/august_supervisor_report.html",
                    "docs/august_supervisor_index.html",
                ),
            )
        )
    return _sorted_findings(findings), {
        "render_runs": render_runs,
        "frozen_product_sha256": frozen_hashes,
        "matches_frozen_products": matches_frozen,
    }


def audit_git_hygiene(
    *,
    root: Path | str,
    allowed_dirty_paths: Sequence[str] = (),
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    """Audit branch state, dirty paths, package sizes, and ignored products."""

    base = Path(root).resolve()
    findings: list[dict[str, object]] = []

    def git(*arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ("git", "-C", str(base), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    branch = git("branch", "--show-current").stdout.decode().strip()
    commit = git("rev-parse", "HEAD").stdout.decode().strip()
    status_lines = git("status", "--short").stdout.decode().splitlines()
    dirty_paths: list[str] = []
    for line in status_lines:
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        dirty_paths.append(value)
    unexpected_dirty = sorted(set(dirty_paths) - set(allowed_dirty_paths))
    if branch != "agent/august-supervisor-report-v1":
        findings.append(
            _finding(
                "CRITICAL",
                "WRONG_GIT_BRANCH",
                claim_id=None,
                file=".git",
                evidence=f"observed branch {branch!r}",
                required_action="Return to the authorized workflow branch in a clean handoff task.",
                remediation=(".git",),
            )
        )
    if unexpected_dirty:
        findings.append(
            _finding(
                "CRITICAL",
                "UNEXPECTED_DIRTY_WORKTREE",
                claim_id=None,
                file="; ".join(unexpected_dirty),
                evidence=f"Dirty paths outside the Stage 08 allowlist: {unexpected_dirty}",
                required_action="Stop and resolve ownership of unexpected changes before continuing.",
                remediation=tuple(unexpected_dirty),
            )
        )

    tracked_raw = git("ls-files", "-z").stdout.split(b"\0")
    tracked = [item.decode() for item in tracked_raw if item]
    sizes = {
        path: (base / path).stat().st_size
        for path in tracked
        if (base / path).is_file()
    }
    package_paths = [
        path
        for path in tracked
        if path.startswith("docs/august_supervisor_")
        or path.startswith("src/august_supervisor/")
        or path.startswith("configs/august_supervisor_")
        or path.startswith("tests/test_august_supervisor_")
    ]
    oversize_package = sorted(path for path in package_paths if sizes[path] > 1_000_000)
    if oversize_package:
        findings.append(
            _finding(
                "MAJOR",
                "TRACKED_PACKAGE_FILE_TOO_LARGE",
                claim_id=None,
                file="; ".join(oversize_package),
                evidence="A tracked August package file exceeds the 1 MB lightweight-product limit.",
                required_action="Move binary or embedded output under ignored results and retain a lightweight tracked product.",
                remediation=tuple(oversize_package),
            )
        )
    forbidden_tracked = sorted(
        path
        for path in tracked
        if path.startswith(("results/august_supervisor_report/", "data/", "figs/"))
    )
    if forbidden_tracked:
        findings.append(
            _finding(
                "CRITICAL",
                "GENERATED_PRODUCT_TRACKED",
                claim_id=None,
                file="; ".join(forbidden_tracked),
                evidence="Generated/data paths prohibited by the workflow are tracked by Git.",
                required_action="Remove the generated products from Git tracking while preserving local ignored copies.",
                remediation=tuple(forbidden_tracked),
            )
        )
    ignored_checks = {}
    for relative in (
        "results/august_supervisor_report/report_manifest.json",
        "results/august_supervisor_report/plots/figure_01_fixed_effort_predictability.png",
    ):
        result = subprocess.run(
            ("git", "-C", str(base), "check-ignore", "-q", relative),
            check=False,
        )
        ignored_checks[relative] = result.returncode == 0
        if result.returncode != 0:
            findings.append(
                _finding(
                    "CRITICAL",
                    "GENERATED_PRODUCT_NOT_IGNORED",
                    claim_id=None,
                    file=relative,
                    evidence="Expected generated product is not covered by Git ignore rules.",
                    required_action="Restore the narrow ignore rule before publication integration.",
                    remediation=(".gitignore",),
                )
            )
    legacy_large = sum(size > 5_000_000 for size in sizes.values())
    return _sorted_findings(findings), {
        "branch": branch,
        "commit": commit,
        "status_lines": status_lines,
        "allowed_dirty_paths": sorted(allowed_dirty_paths),
        "unexpected_dirty_paths": unexpected_dirty,
        "tracked_file_count": len(tracked),
        "tracked_package_file_count": len(package_paths),
        "largest_tracked_package_bytes": max(
            (sizes[path] for path in package_paths), default=0
        ),
        "legacy_tracked_files_over_5mb": legacy_large,
        "forbidden_tracked_product_count": len(forbidden_tracked),
        "ignored_product_checks": ignored_checks,
    }


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    payload = path.read_bytes()[:24]
    if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", payload[16:24])


def audit_browser_renders(
    *,
    root: Path | str,
    output_dir: Path | str,
    html_paths: Sequence[Path | str],
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    """Render desktop/mobile screenshots for independent visual inspection."""

    base = Path(root).resolve()
    output = _rooted(output_dir, base)
    screenshots = output / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    # Prefer the direct Chrome binary.  Some Brave wrapper builds wait on a
    # crash-handler child even after headless capture, which makes a successful
    # screenshot look like an audit timeout.
    browser = shutil.which("google-chrome") or shutil.which("brave-browser")
    findings: list[dict[str, object]] = []
    records = []
    if browser is None:
        findings.append(
            _finding(
                "MAJOR",
                "BROWSER_RENDER_UNAVAILABLE",
                claim_id=None,
                file="environment",
                evidence="Neither brave-browser nor google-chrome is available.",
                required_action="Run the audit in an environment with a headless browser and inspect desktop/mobile renders.",
                remediation=("src/august_supervisor/audit.py",),
            )
        )
        return findings, {"browser": None, "screenshots": records}
    viewports = (("desktop", 1440, 1200), ("mobile", 390, 844))
    for html_path in html_paths:
        document = _rooted(html_path, base)
        for label, width, height in viewports:
            with tempfile.TemporaryDirectory(
                prefix=".august-browser-", dir=output
            ) as profile:
                screenshot = screenshots / f"{document.stem}_{label}.png"
                command = (
                    browser,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-background-networking",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-sync",
                    "--metrics-recording-only",
                    "--mute-audio",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-breakpad",
                    "--disable-crash-reporter",
                    "--hide-scrollbars",
                    f"--user-data-dir={profile}",
                    f"--window-size={width},{height}",
                    f"--screenshot={screenshot}",
                    document.as_uri(),
                )
                result = subprocess.run(
                    command,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60,
                )
                dimensions = _png_dimensions(screenshot) if screenshot.is_file() else None
                if result.returncode != 0 or dimensions != (width, height) or screenshot.stat().st_size < 1_000:
                    findings.append(
                        _finding(
                            "MAJOR",
                            "BROWSER_RENDER_FAILED",
                            claim_id=None,
                            file=_relative(document, base),
                            evidence=(
                                f"viewport={width}x{height}; returncode={result.returncode}; "
                                f"png_dimensions={dimensions}; stderr="
                                f"{result.stderr.decode(errors='replace')[-500:]}"
                            ),
                            required_action="Repair the HTML/CSS or rerun in a working browser environment, then inspect the viewport render.",
                            remediation=(_relative(document, base),),
                        )
                    )
                else:
                    records.append(
                        {
                            "document": _relative(document, base),
                            "viewport": label,
                            "width_px": width,
                            "height_px": height,
                            "path": _relative(screenshot, base),
                            "sha256": sha256_file(screenshot),
                            "bytes": screenshot.stat().st_size,
                        }
                    )
    return _sorted_findings(findings), {
        "browser": browser,
        "screenshots": records,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def run_independent_audit(
    *,
    root: Path | str,
    output_dir: Path | str = DEFAULT_AUDIT_DIR,
    include_browser_renders: bool = True,
    allowed_dirty_paths: Sequence[str] = (),
) -> dict[str, Any]:
    """Run every Stage 08 check and emit deterministic machine-readable products."""

    base = Path(root).resolve()
    output = _rooted(output_dir, base)
    output.mkdir(parents=True, exist_ok=True)
    checks: dict[str, Any] = {}
    findings: list[dict[str, object]] = []

    check_calls = (
        (
            "claim_reconciliation",
            lambda: audit_claim_reconciliation(root=base),
        ),
        (
            "number_formatting",
            lambda: audit_number_formatting(root=base),
        ),
        (
            "manifest_hashes",
            lambda: audit_manifest_hashes(
                root=base,
                report_manifest_path=DEFAULT_INPUT_DIR / "report_manifest.json",
            ),
        ),
        (
            "html_package",
            lambda: audit_html_package(
                root=base,
                html_paths=(DEFAULT_REPORT_HTML, DEFAULT_INDEX_HTML),
                figure_manifest_path=DEFAULT_PLOT_DIR / "figure_manifest.csv",
            ),
        ),
        (
            "scientific_language",
            lambda: audit_scientific_language(root=base),
        ),
        (
            "deterministic_renders",
            lambda: audit_deterministic_renders(
                root=base, output_dir=output / "deterministic_renders"
            ),
        ),
        (
            "git_hygiene",
            lambda: audit_git_hygiene(
                root=base, allowed_dirty_paths=allowed_dirty_paths
            ),
        ),
    )
    for name, call in check_calls:
        try:
            check_findings, summary = call()
        except Exception as error:  # pragma: no cover - last-resort audit containment
            check_findings = [
                _finding(
                    "CRITICAL",
                    "AUDIT_CHECK_CRASH",
                    claim_id=None,
                    file="src/august_supervisor/audit.py",
                    evidence=f"{name}: {type(error).__name__}: {error}",
                    required_action="Repair the independent audit check and rerun Stage 08 before interpreting package status.",
                    remediation=(
                        "src/august_supervisor/audit.py",
                        "tests/test_august_supervisor_audit.py",
                    ),
                )
            ]
            summary = {"status": "CHECK_CRASH"}
        findings.extend(check_findings)
        checks[name] = {
            "finding_count": len(check_findings),
            "blocking_finding_count": sum(
                str(item["severity"]) in BLOCKING_SEVERITIES
                for item in check_findings
            ),
            "summary": summary,
        }

    if include_browser_renders:
        try:
            browser_findings, browser_summary = audit_browser_renders(
                root=base,
                output_dir=output,
                html_paths=(DEFAULT_REPORT_HTML, DEFAULT_INDEX_HTML),
            )
        except Exception as error:  # pragma: no cover - environmental containment
            browser_findings = [
                _finding(
                    "MAJOR",
                    "BROWSER_RENDER_FAILED",
                    claim_id=None,
                    file="environment",
                    evidence=f"{type(error).__name__}: {error}",
                    required_action="Rerun desktop/mobile browser rendering in a working environment and inspect the screenshots.",
                    remediation=("src/august_supervisor/audit.py",),
                )
            ]
            browser_summary = {"status": "CHECK_CRASH", "screenshots": []}
        findings.extend(browser_findings)
        checks["browser_renders"] = {
            "finding_count": len(browser_findings),
            "blocking_finding_count": sum(
                str(item["severity"]) in BLOCKING_SEVERITIES
                for item in browser_findings
            ),
            "summary": browser_summary,
        }
    else:
        checks["browser_renders"] = {
            "finding_count": 0,
            "blocking_finding_count": 0,
            "summary": {"status": "SKIPPED_BY_CALLER", "screenshots": []},
        }

    findings = _sorted_findings(findings)
    findings_path = output / "findings.json"
    _write_json(findings_path, findings)
    findings_hash = sha256_file(findings_path)
    blocking = [
        item for item in findings if str(item["severity"]) in BLOCKING_SEVERITIES
    ]
    verdict = "AUDIT_FAIL" if blocking else "AUDIT_PASS"
    git_summary = checks["git_hygiene"]["summary"]
    remediation_allowlist = sorted(
        {
            path
            for finding in blocking
            for path in finding["remediation_file_allowlist"]
        }
    )
    report = {
        "schema_version": "1.0.0",
        "stage_id": "audit",
        "verdict": verdict,
        "audited_commit": git_summary.get("commit"),
        "branch": git_summary.get("branch"),
        "finding_count": len(findings),
        "blocking_finding_count": len(blocking),
        "severity_counts": {
            severity: sum(item["severity"] == severity for item in findings)
            for severity in SEVERITY_ORDER
        },
        "findings_path": _relative(findings_path, base),
        "findings_sha256": findings_hash,
        "remediation_file_allowlist": remediation_allowlist,
        "checks": checks,
        "independence_boundary": {
            "models_recomputed": False,
            "report_products_edited": False,
            "final_completion_marker_created": False,
        },
    }
    report_path = output / "audit_report.json"
    _write_json(report_path, report)
    report_hash = sha256_file(report_path)
    marker_path = output / verdict
    opposite = output / ("AUDIT_PASS" if verdict == "AUDIT_FAIL" else "AUDIT_FAIL")
    opposite.unlink(missing_ok=True)
    marker_path.write_text(
        f"{verdict}\naudit_report_sha256={report_hash}\nfindings_sha256={findings_hash}\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "verdict": verdict,
        "audit_report_path": _relative(report_path, base),
        "audit_report_sha256": report_hash,
        "findings_path": _relative(findings_path, base),
        "findings_sha256": findings_hash,
        "blocking_finding_count": len(blocking),
        "remediation_file_allowlist": remediation_allowlist,
        "marker_path": _relative(marker_path, base),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--skip-browser-renders", action="store_true")
    parser.add_argument("--allow-dirty", action="append", default=[])
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_independent_audit(
        root=args.root,
        output_dir=args.output_dir,
        include_browser_renders=not args.skip_browser_renders,
        allowed_dirty_paths=args.allow_dirty,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["verdict"] == "AUDIT_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
