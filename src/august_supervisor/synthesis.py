"""Build deterministic scientific-synthesis registries for the August report.

This stage reads only the frozen configuration and the compact, PASS-gated
dataset/model-result registries.  It does not inspect scientific source trees,
fit models, calculate effects, plot, render HTML, or write report prose.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .contracts import (
    CONTRACT_VERSION,
    ContractError,
    atomic_write_csv,
    read_registry_csv,
    sha256_file,
    validate_registry_bundle,
    validate_records,
    verify_stage_manifest,
    write_stage_manifest,
)
from .evidence import (
    DEFAULT_CONFIGURATION,
    DEFAULT_OUTPUT_DIR,
    load_frozen_configuration,
)


_TABLE_FOR_ROLE = {
    "PROMOTED": "headline_findings",
    "SUPPORTING": "supporting_findings",
    "EXCLUDED": "coverage_and_limitations",
    "PENDING": "coverage_and_limitations",
}
_SYNTHESIS_FILENAMES = {
    "headline_findings": "headline_findings.csv",
    "supporting_findings": "supporting_findings.csv",
    "coverage_and_limitations": "coverage_and_limitations.csv",
}
_PAGE_CONTRACT_KEYS = {
    "outputs",
    "section_order",
    "required_links",
    "render_from_frozen_artifacts_only",
    "allow_model_fitting",
    "allow_plot_generation",
    "figure_policy",
}


def _rooted(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()


def _relative_to_root(path: Path | str, root: Path) -> str:
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ContractError(f"stage path is outside repository root: {path}") from error


def _require_nonempty_string(value: Any, location: str) -> str:
    if type(value) is not str or not value.strip():
        raise ContractError(f"{location} must be a nonempty string")
    return value


def _require_relative_path(value: Any, location: str) -> str:
    text = _require_nonempty_string(value, location)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"{location} must be a safe repository-relative path")
    return path.as_posix()


def _validate_page_contract(config: Mapping[str, Any]) -> Mapping[str, Any]:
    contract = config.get("page_contract")
    if type(contract) is not dict or set(contract) != _PAGE_CONTRACT_KEYS:
        actual = set(contract) if type(contract) is dict else set()
        raise ContractError(
            "page_contract schema mismatch; "
            f"missing={sorted(_PAGE_CONTRACT_KEYS - actual)}, "
            f"extra={sorted(actual - _PAGE_CONTRACT_KEYS)}"
        )
    outputs = contract["outputs"]
    sections = contract["section_order"]
    links = contract["required_links"]
    if type(outputs) is not list or not outputs:
        raise ContractError("page_contract.outputs must be a nonempty list")
    if type(sections) is not list or not sections:
        raise ContractError("page_contract.section_order must be a nonempty list")
    if type(links) is not dict or not links:
        raise ContractError("page_contract.required_links must be a nonempty object")
    normalized_outputs = [
        _require_relative_path(value, f"page_contract.outputs[{index}]")
        for index, value in enumerate(outputs)
    ]
    if len(normalized_outputs) != len(set(normalized_outputs)):
        raise ContractError("page_contract.outputs contains duplicate paths")
    for index, section in enumerate(sections):
        _require_nonempty_string(section, f"page_contract.section_order[{index}]")
    if len(sections) != len(set(sections)):
        raise ContractError("page_contract.section_order contains duplicates")
    normalized_links: list[str] = []
    for key, value in links.items():
        _require_nonempty_string(key, "page_contract.required_links key")
        normalized_links.append(
            _require_relative_path(value, f"page_contract.required_links.{key}")
        )
    if len(normalized_links) != len(set(normalized_links)):
        raise ContractError("page_contract.required_links contains duplicate paths")
    overlap = sorted(set(normalized_outputs) & set(normalized_links))
    if overlap:
        raise ContractError(f"page_contract output/resource path overlap: {overlap}")
    expected_flags = {
        "render_from_frozen_artifacts_only": True,
        "allow_model_fitting": False,
        "allow_plot_generation": False,
    }
    for key, expected in expected_flags.items():
        if contract[key] is not expected:
            raise ContractError(f"page_contract.{key} must remain {expected}")
    _require_nonempty_string(contract["figure_policy"], "page_contract.figure_policy")
    destinations = {claim["destination_section"] for claim in config["claims"]}
    undeclared = sorted(destinations - set(sections))
    if undeclared:
        raise ContractError(
            f"claim destination sections are absent from page contract: {undeclared}"
        )
    return contract


def _records_by_claim(
    records: Iterable[Mapping[str, Any]], *, kind: str
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        claim_id = record["claim_id"]
        if claim_id in indexed:
            raise ContractError(f"duplicate {kind} evidence for claim {claim_id}")
        indexed[claim_id] = dict(record)
    return indexed


def _validate_effect_against_claim(
    claim: Mapping[str, Any], effect: Mapping[str, Any]
) -> None:
    claim_id = claim["claim_id"]
    comparisons = {
        "claim_role": claim["claim_role"],
        "evidence_status": claim["evidence_status"],
        "sample_id": f"SAMPLE_{claim_id}",
        "interpretation": claim["required_interpretation"],
        "limitation": claim["required_limitation"],
        "figure_eligibility": claim["figure_eligibility"],
        "source_artifact": claim["source"]["canonical_artifact"],
        "source_sha256": claim["source"]["source_sha256"],
        "audit_marker": claim["source"]["required_marker"]["path"],
    }
    for field, expected in comparisons.items():
        observed = effect[field]
        if observed != expected:
            label = "classification drift" if field == "evidence_status" else "claim drift"
            raise ContractError(
                f"{claim_id} {label} in effect.{field}: "
                f"expected {expected!r}, observed {observed!r}"
            )


def _validate_blocker_against_claim(
    claim: Mapping[str, Any],
    blocker: Mapping[str, Any],
    blocker_config: Mapping[str, Any],
) -> None:
    claim_id = claim["claim_id"]
    comparisons = {
        "sample_id": f"SAMPLE_{claim_id}",
        "blocker_status": blocker_config["status"],
        "reason": blocker_config["reason"],
        "required_resolution": blocker_config["required_resolution"],
        "source_artifact": claim["source"]["canonical_artifact"],
        "source_sha256": claim["source"]["source_sha256"],
        "audit_marker": claim["source"]["required_marker"]["path"],
    }
    for field, expected in comparisons.items():
        observed = blocker[field]
        if observed != expected:
            raise ContractError(
                f"{claim_id} claim drift in blocker.{field}: "
                f"expected {expected!r}, observed {observed!r}"
            )


def build_synthesis_tables(
    config: Mapping[str, Any],
    effects: Iterable[Mapping[str, Any]],
    blockers: Iterable[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Map each frozen claim to one role-partitioned synthesis record.

    The classification rule is deliberately exhaustive and non-statistical:
    admitted effects retain ``effect.evidence_status`` and blockers are
    ``PENDING``.  No coefficient, interval, sign, or p-value is recalculated.
    """

    effect_records = validate_records("effect", effects)
    blocker_records = validate_records("blocker", blockers)
    effects_by_claim = _records_by_claim(effect_records, kind="effect")
    blockers_by_claim = _records_by_claim(blocker_records, kind="blocker")
    configured_blockers = {
        record["claim_id"]: record for record in config["blockers"]
    }
    claims = config["claims"]
    configured_claim_ids = {claim["claim_id"] for claim in claims}
    evidence_claim_ids = set(effects_by_claim) | set(blockers_by_claim)
    overlap = sorted(set(effects_by_claim) & set(blockers_by_claim))
    if overlap:
        raise ContractError(f"ambiguous effect/blocker claim evidence: {overlap}")
    if evidence_claim_ids != configured_claim_ids:
        raise ContractError(
            "synthesis evidence claim coverage mismatch; "
            f"missing={sorted(configured_claim_ids - evidence_claim_ids)}, "
            f"extra={sorted(evidence_claim_ids - configured_claim_ids)}"
        )

    section_orders: defaultdict[str, int] = defaultdict(int)
    tables: dict[str, list[dict[str, Any]]] = {
        name: [] for name in _SYNTHESIS_FILENAMES
    }
    for claim in claims:
        claim_id = claim["claim_id"]
        role = claim["claim_role"]
        if role not in _TABLE_FOR_ROLE:
            raise ContractError(f"{claim_id} has no synthesis-table role rule")
        display_order = section_orders[claim["destination_section"]]
        section_orders[claim["destination_section"]] += 1
        if role == "PENDING":
            if claim["evidence_status"] != "PENDING":
                raise ContractError(f"{claim_id} pending classification drift")
            blocker = blockers_by_claim.get(claim_id)
            if blocker is None or claim_id not in configured_blockers:
                raise ContractError(f"{claim_id} is missing its frozen blocker")
            _validate_blocker_against_claim(
                claim, blocker, configured_blockers[claim_id]
            )
            evidence_kind = "BLOCKER"
            evidence_id = blocker["blocker_id"]
            classification = "PENDING"
            finding = claim["required_interpretation"]
            limitation = (
                f"{claim['required_limitation']} "
                f"Blocker: {blocker['reason']} "
                f"Required resolution: {blocker['required_resolution']}"
            )
        else:
            effect = effects_by_claim.get(claim_id)
            if effect is None:
                raise ContractError(f"{claim_id} is missing its frozen effect")
            _validate_effect_against_claim(claim, effect)
            evidence_kind = "EFFECT"
            evidence_id = effect["effect_id"]
            classification = effect["evidence_status"]
            finding = effect["interpretation"]
            limitation = effect["limitation"]
        record = {
            "schema_version": CONTRACT_VERSION,
            "synthesis_id": f"SYNTHESIS_{claim_id}",
            "claim_id": claim_id,
            "evidence_kind": evidence_kind,
            "evidence_id": evidence_id,
            "classification": classification,
            "destination_section": claim["destination_section"],
            "display_order": display_order,
            "finding": finding,
            "limitation": limitation,
        }
        tables[_TABLE_FOR_ROLE[role]].append(record)

    combined = [record for rows in tables.values() for record in rows]
    validate_records("synthesis", combined)
    return {
        name: validate_records("synthesis", records)
        for name, records in tables.items()
    }


def _page_identifier(prefix: str, value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")
    if not normalized:
        raise ContractError(f"cannot derive page identifier from {value!r}")
    return f"PAGE_{prefix}_{normalized}"


def _page_title_from_path(path: str) -> str:
    name = Path(path).name
    stem = name[:-3] if name.endswith(".md") else Path(name).stem
    title = stem.replace("_", " ").replace("-", " ").title()
    if path.endswith(".md"):
        return f"{title} (Markdown)"
    return title


def build_page_records(
    config: Mapping[str, Any],
    *,
    root: Path | str,
    source_manifest_sha256: str,
) -> list[dict[str, Any]]:
    """Build the frozen output/resource navigation registry."""

    base = Path(root).resolve()
    contract = _validate_page_contract(config)
    records: list[dict[str, Any]] = []
    for display_order, path in enumerate(contract["outputs"]):
        page_kind = "LANDING" if path.endswith("_index.html") else "REPORT"
        records.append(
            {
                "schema_version": CONTRACT_VERSION,
                "page_id": _page_identifier("OUTPUT", path),
                "page_kind": page_kind,
                "output_path": path,
                "title": _page_title_from_path(path),
                "display_order": display_order,
                "source_stage_id": "model-results",
                "source_manifest_sha256": source_manifest_sha256,
                "page_status": "PLANNED",
            }
        )
    offset = len(records)
    for index, (key, path) in enumerate(contract["required_links"].items()):
        resource_path = base / path
        if not resource_path.is_file():
            raise ContractError(f"required technical resource is missing: {path}")
        records.append(
            {
                "schema_version": CONTRACT_VERSION,
                "page_id": _page_identifier("RESOURCE", key),
                "page_kind": "TECHNICAL_RESOURCE",
                "output_path": path,
                "title": key.replace("_", " ").title(),
                "display_order": offset + index,
                "source_stage_id": "model-results",
                "source_manifest_sha256": source_manifest_sha256,
                "page_status": "READY",
            }
        )
    return validate_records("page", records)


def _input_snapshot(paths: Iterable[Path], root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in paths:
        if not path.is_file():
            raise ContractError(f"missing synthesis input: {_relative_to_root(path, root)}")
        snapshot[_relative_to_root(path, root)] = sha256_file(path)
    return dict(sorted(snapshot.items()))


def synthesize(
    *,
    root: Path | str,
    configuration_path: Path | str = DEFAULT_CONFIGURATION,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    model_results_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Write deterministic synthesis/page registries and a chained PASS manifest."""

    base = Path(root).resolve()
    config_path = _rooted(configuration_path, base)
    destination = _rooted(output_dir, base)
    model_manifest_path = (
        destination / "model_results_manifest.json"
        if model_results_manifest_path is None
        else _rooted(model_results_manifest_path, base)
    )
    input_paths = [
        config_path,
        model_manifest_path,
        destination / "sample_registry.csv",
        destination / "effect_registry.csv",
        destination / "model_inventory.csv",
        destination / "declared_blockers.csv",
    ]
    for path in [destination, *input_paths]:
        _relative_to_root(path, base)

    upstream = verify_stage_manifest(
        model_manifest_path, root=base, expected_stage="model-results"
    )
    before = _input_snapshot(input_paths, base)
    config = load_frozen_configuration(config_path)
    samples = read_registry_csv(destination / "sample_registry.csv", "sample")
    effects = read_registry_csv(destination / "effect_registry.csv", "effect")
    models = read_registry_csv(destination / "model_inventory.csv", "model")
    blockers = read_registry_csv(destination / "declared_blockers.csv", "blocker")
    validate_registry_bundle(
        {
            "sample": samples,
            "model": models,
            "effect": effects,
            "blocker": blockers,
        }
    )
    tables = build_synthesis_tables(config, effects, blockers)
    validate_registry_bundle(
        {
            "sample": samples,
            "model": models,
            "effect": effects,
            "blocker": blockers,
            "synthesis": [
                record for records in tables.values() for record in records
            ],
        }
    )
    pages = build_page_records(
        config,
        root=base,
        source_manifest_sha256=sha256_file(model_manifest_path),
    )

    artifact_paths: list[Path] = []
    for table_name, filename in _SYNTHESIS_FILENAMES.items():
        path = destination / filename
        atomic_write_csv(path, "synthesis", tables[table_name])
        read_registry_csv(path, "synthesis")
        artifact_paths.append(path)
    page_path = destination / "page_registry.csv"
    atomic_write_csv(page_path, "page", pages)
    read_registry_csv(page_path, "page")
    artifact_paths.append(page_path)

    manifest_path = destination / "synthesis_manifest.json"
    manifest = write_stage_manifest(
        manifest_path,
        stage_id="synthesis",
        artifact_paths=artifact_paths,
        upstream_manifest_paths=[model_manifest_path],
        root=base,
        configuration_path=config_path,
    )
    verify_stage_manifest(manifest_path, root=base, expected_stage="synthesis")
    after = _input_snapshot(input_paths, base)
    if before != after:
        raise ContractError("upstream inputs changed during scientific synthesis")

    classifications = Counter(
        record["classification"]
        for records in tables.values()
        for record in records
    )
    artifact_names = {
        **{
            table_name: _relative_to_root(destination / filename, base)
            for table_name, filename in _SYNTHESIS_FILENAMES.items()
        },
        "page_registry": _relative_to_root(page_path, base),
        "synthesis_manifest": _relative_to_root(manifest_path, base),
    }
    return {
        "status": "PASS",
        "stage": "synthesis",
        "row_counts": {
            **{name: len(records) for name, records in tables.items()},
            "page_registry": len(pages),
        },
        "classification_counts": dict(sorted(classifications.items())),
        "artifacts": artifact_names,
        "artifact_sha256": {
            name: sha256_file(base / path) for name, path in artifact_names.items()
        },
        "input_hashes_before": before,
        "input_hashes_after": after,
        "upstream_manifest_sha256": sha256_file(model_manifest_path),
        "manifest": manifest,
        "upstream_stage": upstream["stage_id"],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--configuration", type=Path, default=DEFAULT_CONFIGURATION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model-results-manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = synthesize(
        root=args.root,
        configuration_path=args.configuration,
        output_dir=args.output_dir,
        model_results_manifest_path=args.model_results_manifest,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
