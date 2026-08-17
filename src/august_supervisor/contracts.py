"""Strict, deterministic contracts for the August supervisor-report stages.

This module deliberately contains no extraction, statistical, plotting, or
rendering logic.  It defines the compact records exchanged by later stages and
the provenance checks that keep those stages isolated from one another.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


CONTRACT_VERSION = "1.0.0"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

EVIDENCE_STATUSES = frozenset(
    {"SUPPORTED", "QUALIFIED", "CONTRARY", "DESCRIPTIVE", "PENDING"}
)
CLAIM_ROLES = frozenset({"PROMOTED", "SUPPORTING", "EXCLUDED", "PENDING"})
FIGURE_ELIGIBILITIES = frozenset({"PRIMARY", "SUPPORTING", "NONE"})
SAMPLE_SCOPES = frozenset(
    {
        "PBM_DISCOVERY",
        "NON_PBM_CONFIRMATION",
        "PBM_SCORER_ROBUSTNESS",
        "PBM_RESPONSE_SPACE",
        "PBM_BAYES_ROBUSTNESS",
        "HALL_SNAPSHOT",
        "PENDING_EVIDENCE",
    }
)
SCORERS = frozenset(
    {
        "MISTRAL_7B_V03",
        "TINYDIALOGUES_SMOLLM2_135M",
        "QWEN3_14B",
        "MULTI_SCORER",
        "MISTRAL_RESPONSE_SPACE",
        "CORRECTED_BAYES",
        "NOT_APPLICABLE",
    }
)
AUDIT_STATUSES = frozenset(
    {"PASS", "COMPLETE", "AUDIT_PASS", "REVIEW", "BLOCKED", "MISSING"}
)
MODEL_FIT_STATUSES = frozenset(
    {"PASS", "PASS_WITH_WARNINGS", "BLOCKED", "NOT_APPLICABLE"}
)
BLOCKER_STATUSES = frozenset({"BLOCKED", "PENDING_NEW_ANALYSIS", "REVIEW"})
PAGE_KINDS = frozenset({"LANDING", "REPORT", "TECHNICAL_RESOURCE"})
PAGE_STATUSES = frozenset({"PLANNED", "READY", "PUBLISHED"})
FIGURE_ROLES = frozenset({"MAIN", "SUPPORTING"})
STAGE_IDS = (
    "datasets",
    "model-results",
    "synthesis",
    "plots",
    "report",
    "index",
    "audit",
)
STAGE_STATUSES = frozenset({"PASS", "AUDIT_PASS"})
REQUIRED_UPSTREAM_STAGE = {
    "datasets": None,
    "model-results": "datasets",
    "synthesis": "model-results",
    "plots": "synthesis",
    "report": "plots",
    "index": "report",
    "audit": "index",
}


class ContractError(ValueError):
    """Raised when a report record or stage boundary violates its contract."""


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    kind: str
    nullable: bool = False
    enum: frozenset[str] | None = None
    pattern: re.Pattern[str] | None = None


@dataclass(frozen=True)
class ForeignKeySpec:
    local_column: str
    target_schema: str
    target_column: str
    nullable: bool = False


@dataclass(frozen=True)
class RecordSchema:
    name: str
    version: str
    columns: tuple[ColumnSpec, ...]
    primary_key: tuple[str, ...]
    unique_keys: tuple[tuple[str, ...], ...] = ()
    foreign_keys: tuple[ForeignKeySpec, ...] = ()

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)


def _column(
    name: str,
    kind: str = "str",
    *,
    nullable: bool = False,
    enum: frozenset[str] | None = None,
    pattern: re.Pattern[str] | None = None,
) -> ColumnSpec:
    return ColumnSpec(name, kind, nullable, enum, pattern)


def _base_columns() -> tuple[ColumnSpec, ...]:
    return (_column("schema_version", enum=frozenset({CONTRACT_VERSION})),)


def _source_columns() -> tuple[ColumnSpec, ...]:
    return (
        _column("source_artifact"),
        _column("source_sha256", pattern=SHA256_PATTERN),
        _column("audit_marker", nullable=True),
        _column("audit_marker_sha256", nullable=True, pattern=SHA256_PATTERN),
    )


SCHEMAS: dict[str, RecordSchema] = {
    "sample": RecordSchema(
        name="sample",
        version=CONTRACT_VERSION,
        columns=_base_columns()
        + (
            _column("sample_id", pattern=IDENTIFIER_PATTERN),
            _column("scope", enum=SAMPLE_SCOPES),
            _column("sample_role"),
            _column("description"),
            _column("rows", "int", nullable=True),
            _column("children", "int", nullable=True),
            _column("sessions", "int", nullable=True),
            _column("corpora", "int", nullable=True),
            _column("audit_status", enum=AUDIT_STATUSES),
        )
        + _source_columns(),
        primary_key=("sample_id",),
    ),
    "model": RecordSchema(
        name="model",
        version=CONTRACT_VERSION,
        columns=_base_columns()
        + (
            _column("model_id", pattern=IDENTIFIER_PATTERN),
            _column("claim_id", pattern=IDENTIFIER_PATTERN),
            _column("sample_id", pattern=IDENTIFIER_PATTERN),
            _column("scorer", enum=SCORERS),
            _column("tokenizer_namespace"),
            _column("outcome"),
            _column("formula_or_contrast"),
            _column("estimator"),
            _column("uncertainty_method"),
            _column("fit_status", enum=MODEL_FIT_STATUSES),
        )
        + _source_columns(),
        primary_key=("model_id",),
        foreign_keys=(ForeignKeySpec("sample_id", "sample", "sample_id"),),
    ),
    "effect": RecordSchema(
        name="effect",
        version=CONTRACT_VERSION,
        columns=_base_columns()
        + (
            _column("effect_id", pattern=IDENTIFIER_PATTERN),
            _column("claim_id", pattern=IDENTIFIER_PATTERN),
            _column("claim_role", enum=CLAIM_ROLES),
            _column("sample_id", pattern=IDENTIFIER_PATTERN),
            _column("model_id", nullable=True, pattern=IDENTIFIER_PATTERN),
            _column("evidence_status", enum=EVIDENCE_STATUSES),
            _column("estimate", "number", nullable=True),
            _column("unit"),
            _column("ci_level", "number", nullable=True),
            _column("ci_low", "number", nullable=True),
            _column("ci_high", "number", nullable=True),
            _column("uncertainty_method"),
            _column("direction_convention"),
            _column("interpretation"),
            _column("limitation"),
            _column("figure_eligibility", enum=FIGURE_ELIGIBILITIES),
        )
        + _source_columns(),
        primary_key=("effect_id",),
        unique_keys=(("claim_id",),),
        foreign_keys=(
            ForeignKeySpec("sample_id", "sample", "sample_id"),
            ForeignKeySpec("model_id", "model", "model_id", nullable=True),
        ),
    ),
    "blocker": RecordSchema(
        name="blocker",
        version=CONTRACT_VERSION,
        columns=_base_columns()
        + (
            _column("blocker_id", pattern=IDENTIFIER_PATTERN),
            _column("claim_id", pattern=IDENTIFIER_PATTERN),
            _column("sample_id", nullable=True, pattern=IDENTIFIER_PATTERN),
            _column("blocker_status", enum=BLOCKER_STATUSES),
            _column("reason"),
            _column("required_resolution"),
        )
        + _source_columns(),
        primary_key=("blocker_id",),
        unique_keys=(("claim_id",),),
        foreign_keys=(
            ForeignKeySpec("sample_id", "sample", "sample_id", nullable=True),
        ),
    ),
    "synthesis": RecordSchema(
        name="synthesis",
        version=CONTRACT_VERSION,
        columns=_base_columns()
        + (
            _column("synthesis_id", pattern=IDENTIFIER_PATTERN),
            _column("claim_id", pattern=IDENTIFIER_PATTERN),
            _column("evidence_kind", enum=frozenset({"EFFECT", "BLOCKER"})),
            _column("evidence_id", pattern=IDENTIFIER_PATTERN),
            _column("classification", enum=EVIDENCE_STATUSES),
            _column("destination_section"),
            _column("display_order", "int"),
            _column("finding"),
            _column("limitation"),
        ),
        primary_key=("synthesis_id",),
        unique_keys=(("claim_id",), ("destination_section", "display_order")),
    ),
    "page": RecordSchema(
        name="page",
        version=CONTRACT_VERSION,
        columns=_base_columns()
        + (
            _column("page_id", pattern=IDENTIFIER_PATTERN),
            _column("page_kind", enum=PAGE_KINDS),
            _column("output_path"),
            _column("title"),
            _column("display_order", "int"),
            _column("source_stage_id", enum=frozenset(STAGE_IDS)),
            _column("source_manifest_sha256", pattern=SHA256_PATTERN),
            _column("page_status", enum=PAGE_STATUSES),
        ),
        primary_key=("page_id",),
        unique_keys=(("output_path",), ("display_order",)),
    ),
    "figure": RecordSchema(
        name="figure",
        version=CONTRACT_VERSION,
        columns=_base_columns()
        + (
            _column("figure_id", pattern=IDENTIFIER_PATTERN),
            _column("claim_ids", "list"),
            _column("effect_ids", "list"),
            _column("eligibility", enum=frozenset({"PRIMARY", "SUPPORTING"})),
            _column("figure_role", enum=FIGURE_ROLES),
            _column("plot_data_path"),
            _column("plot_data_sha256", pattern=SHA256_PATTERN),
            _column("image_path"),
            _column("image_sha256", pattern=SHA256_PATTERN),
            _column("caption"),
            _column("alt_text"),
            _column("width_px", "int"),
            _column("height_px", "int"),
        ),
        primary_key=("figure_id",),
        unique_keys=(("image_path",),),
    ),
    "stage_manifest": RecordSchema(
        name="stage_manifest",
        version=CONTRACT_VERSION,
        columns=_base_columns()
        + (
            _column("stage_id", enum=frozenset(STAGE_IDS)),
            _column("status", enum=STAGE_STATUSES),
            _column("configuration_path", nullable=True),
            _column("configuration_sha256", nullable=True, pattern=SHA256_PATTERN),
            _column("upstream_manifests", "list"),
            _column("artifacts", "list"),
            _column("manifest_sha256", pattern=SHA256_PATTERN),
        ),
        primary_key=("stage_id",),
    ),
}


def _is_kind(value: Any, kind: str) -> bool:
    if kind == "str":
        return type(value) is str and bool(value.strip())
    if kind == "int":
        return type(value) is int
    if kind == "number":
        return type(value) in (int, float) and math.isfinite(value)
    if kind == "bool":
        return type(value) is bool
    if kind == "list":
        return type(value) is list
    if kind == "dict":
        return type(value) is dict
    raise RuntimeError(f"unknown schema kind {kind!r}")


def _validate_record(schema: RecordSchema, record: Mapping[str, Any], index: int) -> None:
    expected = set(schema.column_names)
    actual = set(record)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise ContractError(f"{schema.name}[{index}] missing required columns: {missing}")
    if extra:
        raise ContractError(f"{schema.name}[{index}] has unexpected columns: {extra}")
    for column in schema.columns:
        value = record[column.name]
        if value is None:
            if not column.nullable:
                raise ContractError(
                    f"{schema.name}[{index}].{column.name} may not be null"
                )
            continue
        if not _is_kind(value, column.kind):
            raise ContractError(
                f"{schema.name}[{index}].{column.name} must be {column.kind}; "
                f"got {type(value).__name__}"
            )
        if column.enum is not None and value not in column.enum:
            raise ContractError(
                f"{schema.name}[{index}].{column.name} has invalid value {value!r}; "
                f"allowed={sorted(column.enum)}"
            )
        if column.pattern is not None and not column.pattern.fullmatch(value):
            raise ContractError(
                f"{schema.name}[{index}].{column.name} has invalid format: {value!r}"
            )


def _record_key(record: Mapping[str, Any], columns: Sequence[str]) -> tuple[Any, ...]:
    return tuple(record[column] for column in columns)


def _validate_effect(record: Mapping[str, Any], index: int) -> None:
    interval = (record["ci_level"], record["ci_low"], record["ci_high"])
    if any(value is None for value in interval) and not all(
        value is None for value in interval
    ):
        raise ContractError(f"effect[{index}] confidence interval must be complete or null")
    if interval[0] is not None:
        level, low, high = interval
        if not 0 < level < 1:
            raise ContractError(f"effect[{index}].ci_level must be between 0 and 1")
        if low > high:
            raise ContractError(f"effect[{index}] confidence interval is reversed")
    if record["estimate"] is None and any(value is not None for value in interval):
        raise ContractError(f"effect[{index}] cannot have an interval without an estimate")
    if record["evidence_status"] == "PENDING" and record["estimate"] is not None:
        raise ContractError(f"effect[{index}] pending evidence cannot have an estimate")
    if (record["claim_role"] == "PENDING") != (
        record["evidence_status"] == "PENDING"
    ):
        raise ContractError(f"effect[{index}] pending role/status must agree")
    if record["claim_role"] in {"EXCLUDED", "PENDING"} and record[
        "figure_eligibility"
    ] != "NONE":
        raise ContractError(f"effect[{index}] excluded/pending evidence cannot have a figure")
    marker_pair = (record["audit_marker"], record["audit_marker_sha256"])
    if (marker_pair[0] is None) != (marker_pair[1] is None):
        raise ContractError(f"effect[{index}] audit marker path/hash must be paired")


def _validate_nonnegative_counts(schema_name: str, record: Mapping[str, Any], index: int) -> None:
    for column in ("rows", "children", "sessions", "corpora"):
        value = record[column]
        if value is not None and value < 0:
            raise ContractError(f"{schema_name}[{index}].{column} may not be negative")


def _validate_source_marker_pair(
    schema_name: str, record: Mapping[str, Any], index: int
) -> None:
    _require_relative_path(record["source_artifact"], f"{schema_name}[{index}].source_artifact")
    marker = record["audit_marker"]
    marker_hash = record["audit_marker_sha256"]
    if (marker is None) != (marker_hash is None):
        raise ContractError(
            f"{schema_name}[{index}] audit marker path/hash must be paired"
        )
    if marker is not None:
        _require_relative_path(marker, f"{schema_name}[{index}].audit_marker")


def _validate_stage_manifest(record: Mapping[str, Any]) -> None:
    upstream = record["upstream_manifests"]
    artifacts = record["artifacts"]
    upstream_keys = {"stage_id", "path", "sha256"}
    artifact_keys = {"path", "sha256", "kind"}
    configuration_pair = (
        record["configuration_path"],
        record["configuration_sha256"],
    )
    if (configuration_pair[0] is None) != (configuration_pair[1] is None):
        raise ContractError("stage_manifest configuration path/hash must be paired")
    if configuration_pair[0] is not None:
        _require_relative_path(configuration_pair[0], "configuration_path")
    for index, item in enumerate(upstream):
        if type(item) is not dict or set(item) != upstream_keys:
            raise ContractError(f"stage_manifest upstream[{index}] has invalid fields")
        if item["stage_id"] not in STAGE_IDS:
            raise ContractError(f"stage_manifest upstream[{index}] has invalid stage")
        _require_relative_path(item["path"], f"upstream[{index}].path")
        _require_sha256(item["sha256"], f"upstream[{index}].sha256")
    for index, item in enumerate(artifacts):
        if type(item) is not dict or set(item) != artifact_keys:
            raise ContractError(f"stage_manifest artifacts[{index}] has invalid fields")
        _require_relative_path(item["path"], f"artifacts[{index}].path")
        _require_sha256(item["sha256"], f"artifacts[{index}].sha256")
        if item["kind"] != "file":
            raise ContractError(f"stage_manifest artifacts[{index}].kind must be 'file'")
    upstream_paths = [item["path"] for item in upstream]
    artifact_paths = [item["path"] for item in artifacts]
    if len(upstream_paths) != len(set(upstream_paths)):
        raise ContractError("stage_manifest has duplicate upstream paths")
    if len(artifact_paths) != len(set(artifact_paths)):
        raise ContractError("stage_manifest has duplicate artifact paths")
    if not artifact_paths:
        raise ContractError("stage_manifest is missing all artifacts")
    if artifact_paths != sorted(artifact_paths):
        raise ContractError("stage_manifest artifacts are not deterministically ordered")
    if upstream != sorted(upstream, key=lambda item: (STAGE_IDS.index(item["stage_id"]), item["path"])):
        raise ContractError("stage_manifest upstream records are not deterministically ordered")
    required = REQUIRED_UPSTREAM_STAGE[record["stage_id"]]
    actual_stages = [item["stage_id"] for item in upstream]
    if required is None and actual_stages:
        raise ContractError("datasets stage may not declare an upstream stage")
    if required is not None and actual_stages != [required]:
        raise ContractError(
            f"{record['stage_id']} requires exactly one {required!r} upstream manifest"
        )
    expected_status = "AUDIT_PASS" if record["stage_id"] == "audit" else "PASS"
    if record["status"] != expected_status:
        raise ContractError(
            f"{record['stage_id']} manifest status must be {expected_status!r}"
        )


def validate_records(
    schema_name: str,
    records: Iterable[Mapping[str, Any]],
    *,
    allow_empty: bool = False,
) -> list[dict[str, Any]]:
    """Validate records and return a deterministic primary-key ordering."""

    if schema_name not in SCHEMAS:
        raise ContractError(f"unknown schema {schema_name!r}")
    schema = SCHEMAS[schema_name]
    materialized = [dict(record) for record in records]
    if not materialized and not allow_empty:
        raise ContractError(f"{schema_name} registry is missing all records")
    for index, record in enumerate(materialized):
        _validate_record(schema, record, index)
        if schema_name == "sample":
            _validate_nonnegative_counts(schema_name, record, index)
            _validate_source_marker_pair(schema_name, record, index)
            if record["audit_status"] in {"PASS", "COMPLETE", "AUDIT_PASS"} and record[
                "audit_marker"
            ] is None:
                raise ContractError(f"sample[{index}] passed evidence needs an audit marker")
        elif schema_name in {"model", "blocker"}:
            _validate_source_marker_pair(schema_name, record, index)
            if schema_name == "model" and record["fit_status"] in {
                "PASS",
                "PASS_WITH_WARNINGS",
            } and record["audit_marker"] is None:
                raise ContractError(f"model[{index}] passed fit needs an audit marker")
        elif schema_name == "effect":
            _validate_effect(record, index)
            _validate_source_marker_pair(schema_name, record, index)
            if record["evidence_status"] != "PENDING" and record["audit_marker"] is None:
                raise ContractError(f"effect[{index}] admitted evidence needs an audit marker")
        elif schema_name == "synthesis" and record["display_order"] < 0:
            raise ContractError(f"synthesis[{index}].display_order may not be negative")
        elif schema_name == "page":
            if record["display_order"] < 0:
                raise ContractError(f"page[{index}].display_order may not be negative")
            _require_relative_path(record["output_path"], f"page[{index}].output_path")
        elif schema_name == "figure":
            if record["width_px"] <= 0 or record["height_px"] <= 0:
                raise ContractError(f"figure[{index}] dimensions must be positive")
            _require_relative_path(record["plot_data_path"], f"figure[{index}].plot_data_path")
            _require_relative_path(record["image_path"], f"figure[{index}].image_path")
            for column in ("claim_ids", "effect_ids"):
                values = record[column]
                if not values:
                    raise ContractError(f"figure[{index}].{column} may not be empty")
                if any(
                    type(value) is not str or not IDENTIFIER_PATTERN.fullmatch(value)
                    for value in values
                ):
                    raise ContractError(f"figure[{index}].{column} has invalid identifiers")
                if len(values) != len(set(values)):
                    raise ContractError(f"figure[{index}].{column} has duplicates")
                if values != sorted(values):
                    raise ContractError(
                        f"figure[{index}].{column} is not deterministically ordered"
                    )
        elif schema_name == "stage_manifest":
            _validate_stage_manifest(record)
    for columns in (schema.primary_key,) + schema.unique_keys:
        seen: dict[tuple[Any, ...], int] = {}
        for index, record in enumerate(materialized):
            key = _record_key(record, columns)
            if key in seen:
                raise ContractError(
                    f"{schema_name} duplicate unique key {columns}={key!r} "
                    f"at rows {seen[key]} and {index}"
                )
            seen[key] = index
    return sorted(materialized, key=lambda record: _record_key(record, schema.primary_key))


def validate_registry_bundle(
    registries: Mapping[str, Iterable[Mapping[str, Any]]]
) -> dict[str, list[dict[str, Any]]]:
    """Validate registries together, including all foreign-key relationships."""

    unknown = set(registries) - (set(SCHEMAS) - {"stage_manifest"})
    if unknown:
        raise ContractError(f"registry bundle has unknown schemas: {sorted(unknown)}")
    validated = {
        name: validate_records(name, records)
        for name, records in registries.items()
    }
    for name, records in validated.items():
        for foreign_key in SCHEMAS[name].foreign_keys:
            target_records = validated.get(foreign_key.target_schema)
            if target_records is None:
                raise ContractError(
                    f"{name}.{foreign_key.local_column} requires missing "
                    f"{foreign_key.target_schema} registry"
                )
            target_values = {
                record[foreign_key.target_column] for record in target_records
            }
            for record in records:
                value = record[foreign_key.local_column]
                if value is None and foreign_key.nullable:
                    continue
                if value not in target_values:
                    raise ContractError(
                        f"{name}.{foreign_key.local_column}={value!r} has no "
                        f"{foreign_key.target_schema}.{foreign_key.target_column}"
                    )

    effects_by_claim = {
        record["claim_id"]: record for record in validated.get("effect", [])
    }
    blockers_by_claim = {
        record["claim_id"]: record for record in validated.get("blocker", [])
    }
    ambiguous = set(effects_by_claim) & set(blockers_by_claim)
    if ambiguous:
        raise ContractError(f"ambiguous claim IDs occur as effect and blocker: {sorted(ambiguous)}")

    effects_by_id = {
        record["effect_id"]: record for record in validated.get("effect", [])
    }
    models_by_id = {
        record["model_id"]: record for record in validated.get("model", [])
    }
    blockers_by_id = {
        record["blocker_id"]: record for record in validated.get("blocker", [])
    }
    for model in models_by_id.values():
        effect = effects_by_claim.get(model["claim_id"])
        if effect is None:
            raise ContractError(f"model {model['model_id']} has no claim-level effect")
        if effect["sample_id"] != model["sample_id"]:
            raise ContractError(f"model {model['model_id']} changes its claim sample")
    for effect in effects_by_id.values():
        if effect["model_id"] is None:
            continue
        model = models_by_id[effect["model_id"]]
        if model["claim_id"] != effect["claim_id"]:
            raise ContractError(f"effect {effect['effect_id']} changes its model claim")
        if model["sample_id"] != effect["sample_id"]:
            raise ContractError(f"effect {effect['effect_id']} changes its model sample")
    for record in validated.get("synthesis", []):
        source = (
            effects_by_id.get(record["evidence_id"])
            if record["evidence_kind"] == "EFFECT"
            else blockers_by_id.get(record["evidence_id"])
        )
        if source is None:
            raise ContractError(
                f"synthesis evidence {record['evidence_kind']}/{record['evidence_id']} is missing"
            )
        if source["claim_id"] != record["claim_id"]:
            raise ContractError(
                f"synthesis {record['synthesis_id']} claim does not match its evidence"
            )
        expected_classification = (
            source["evidence_status"]
            if record["evidence_kind"] == "EFFECT"
            else "PENDING"
        )
        if record["classification"] != expected_classification:
            raise ContractError(
                f"synthesis {record['synthesis_id']} changes upstream classification"
            )
    if "synthesis" in validated:
        synthesized_claims = {
            record["claim_id"] for record in validated["synthesis"]
        }
        evidence_claims = set(effects_by_claim) | set(blockers_by_claim)
        missing_claims = sorted(evidence_claims - synthesized_claims)
        extra_claims = sorted(synthesized_claims - evidence_claims)
        if missing_claims or extra_claims:
            raise ContractError(
                "synthesis claim coverage mismatch; "
                f"missing={missing_claims}, extra={extra_claims}"
            )

    for record in validated.get("figure", []):
        missing_effects = sorted(set(record["effect_ids"]) - set(effects_by_id))
        if missing_effects:
            raise ContractError(
                f"figure {record['figure_id']} has missing effects: {missing_effects}"
            )
        effects = [effects_by_id[effect_id] for effect_id in record["effect_ids"]]
        source_claims = sorted(effect["claim_id"] for effect in effects)
        if source_claims != record["claim_ids"]:
            raise ContractError(f"figure {record['figure_id']} claim/effect mismatch")
        expected_eligibility = (
            "PRIMARY"
            if any(effect["figure_eligibility"] == "PRIMARY" for effect in effects)
            else "SUPPORTING"
        )
        if any(effect["figure_eligibility"] == "NONE" for effect in effects):
            raise ContractError(f"figure {record['figure_id']} uses ineligible evidence")
        if expected_eligibility != record["eligibility"]:
            raise ContractError(f"figure {record['figure_id']} changes figure eligibility")
        if any(effect["claim_role"] in {"EXCLUDED", "PENDING"} for effect in effects):
            raise ContractError(f"figure {record['figure_id']} uses ineligible evidence")
    return validated


def resolve_claim(
    claim_id: str,
    *,
    effects: Iterable[Mapping[str, Any]],
    blockers: Iterable[Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Resolve one claim to exactly one effect or blocker record."""

    matches = [record for record in effects if record.get("claim_id") == claim_id]
    matches.extend(record for record in blockers if record.get("claim_id") == claim_id)
    if not matches:
        raise ContractError(f"missing evidence for claim {claim_id!r}")
    if len(matches) != 1:
        raise ContractError(f"ambiguous evidence for claim {claim_id!r}")
    return matches[0]


def canonical_json_bytes(value: Any) -> bytes:
    """Return UTF-8 canonical JSON with stable keys and no non-finite values."""

    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise ContractError(f"value is not canonical-JSON serializable: {error}") from error
    return text.encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_bytes(path: Path | str, payload: bytes) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_json(path: Path | str, value: Any) -> None:
    _atomic_write_bytes(path, canonical_json_bytes(value) + b"\n")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def read_json_strict(path: Path | str) -> Any:
    try:
        return json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ContractError(f"non-finite JSON number {value}")
            ),
        )
    except json.JSONDecodeError as error:
        raise ContractError(f"invalid JSON in {path}: {error}") from error


def _csv_value(value: Any, kind: str) -> str:
    if value is None:
        return ""
    if kind == "bool":
        return "true" if value else "false"
    if kind == "number" and type(value) is float:
        return format(value, ".17g")
    if kind in {"list", "dict"}:
        return canonical_json_bytes(value).decode("utf-8")
    return str(value)


def atomic_write_csv(
    path: Path | str,
    schema_name: str,
    records: Iterable[Mapping[str, Any]],
) -> None:
    """Validate and atomically write a registry in canonical row/column order."""

    validated = validate_records(schema_name, records)
    schema = SCHEMAS[schema_name]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(schema.column_names),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for record in validated:
        writer.writerow(
            {
                column.name: _csv_value(record[column.name], column.kind)
                for column in schema.columns
            }
        )
    _atomic_write_bytes(path, buffer.getvalue().encode("utf-8"))


def _parse_csv_value(raw: str, column: ColumnSpec, location: str) -> Any:
    if raw == "" and column.nullable:
        return None
    try:
        if column.kind == "str":
            return raw
        if column.kind == "int":
            if not re.fullmatch(r"-?(0|[1-9][0-9]*)", raw):
                raise ValueError("not a canonical integer")
            return int(raw)
        if column.kind == "number":
            value = float(raw)
            if not math.isfinite(value):
                raise ValueError("non-finite number")
            return value
        if column.kind == "bool":
            if raw not in {"true", "false"}:
                raise ValueError("boolean must be true or false")
            return raw == "true"
        if column.kind in {"list", "dict"}:
            return json.loads(raw, object_pairs_hook=_reject_duplicate_json_keys)
    except (ValueError, json.JSONDecodeError) as error:
        raise ContractError(f"{location} cannot parse {raw!r}: {error}") from error
    raise RuntimeError(f"unknown schema kind {column.kind!r}")


def read_registry_csv(path: Path | str, schema_name: str) -> list[dict[str, Any]]:
    schema = SCHEMAS[schema_name]
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as error:
            raise ContractError(f"{path} is an empty CSV") from error
        if len(header) != len(set(header)):
            raise ContractError(f"{path} has duplicate CSV headers")
        if tuple(header) != schema.column_names:
            raise ContractError(
                f"{path} columns do not match {schema_name} schema; "
                f"expected={schema.column_names}, observed={tuple(header)}"
            )
        records: list[dict[str, Any]] = []
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ContractError(f"{path}:{row_number} has {len(row)} fields; expected {len(header)}")
            records.append(
                {
                    column.name: _parse_csv_value(
                        raw, column, f"{path}:{row_number}:{column.name}"
                    )
                    for raw, column in zip(row, schema.columns)
                }
            )
    return validate_records(schema_name, records)


def _require_sha256(value: Any, location: str) -> None:
    if type(value) is not str or not SHA256_PATTERN.fullmatch(value):
        raise ContractError(f"{location} is not a lowercase SHA-256")


def _require_relative_path(value: Any, location: str) -> None:
    if type(value) is not str or not value:
        raise ContractError(f"{location} must be a nonempty path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"{location} must be a repository-relative safe path")


def _relative_path(path: Path | str, root: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ContractError(f"path is outside stage root: {resolved}") from error


def _rooted_path(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()


def verify_evidence_sources(
    registries: Mapping[str, Iterable[Mapping[str, Any]]], root: Path | str
) -> None:
    """Require every declared evidence file and marker to retain its frozen hash."""

    base = Path(root).resolve()
    observed_hashes: dict[Path, str] = {}
    for schema_name in ("sample", "model", "effect", "blocker"):
        records = [dict(record) for record in registries.get(schema_name, [])]
        if not records:
            continue
        for record in validate_records(schema_name, records):
            identity = record.get(
                f"{schema_name}_id", record.get("claim_id", schema_name)
            )
            for label, path_column, hash_column in (
                ("source", "source_artifact", "source_sha256"),
                ("audit marker", "audit_marker", "audit_marker_sha256"),
            ):
                declared = record[path_column]
                expected = record[hash_column]
                if declared is None and expected is None:
                    continue
                _require_relative_path(declared, f"{identity}.{path_column}")
                path = base / declared
                if not path.is_file():
                    raise ContractError(f"{identity} missing {label}: {declared}")
                resolved = path.resolve()
                if resolved not in observed_hashes:
                    observed_hashes[resolved] = sha256_file(path)
                observed = observed_hashes[resolved]
                if observed != expected:
                    raise ContractError(
                        f"{identity} changed {label}: expected {expected}, observed {observed}"
                    )


def _manifest_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key != "manifest_sha256"}


def _resolve_recorded_path(root: Path, value: str) -> Path:
    _require_relative_path(value, "recorded path")
    resolved = (root / value).resolve()
    _relative_path(resolved, root)
    return resolved


def verify_stage_manifest(
    path: Path | str,
    *,
    root: Path | str,
    expected_stage: str | None = None,
    _seen: set[Path] | None = None,
) -> dict[str, Any]:
    """Verify one stage manifest, its complete chain, and all frozen artifacts."""

    base = Path(root).resolve()
    manifest_path = _rooted_path(path, base)
    _relative_path(manifest_path, base)
    seen = set() if _seen is None else _seen
    if manifest_path in seen:
        raise ContractError(f"stage-manifest cycle detected at {manifest_path}")
    seen.add(manifest_path)
    if not manifest_path.is_file():
        raise ContractError(f"missing stage manifest: {manifest_path}")
    record = read_json_strict(manifest_path)
    if type(record) is not dict:
        raise ContractError(f"stage manifest is not an object: {manifest_path}")
    validate_records("stage_manifest", [record])
    if expected_stage is not None and record["stage_id"] != expected_stage:
        raise ContractError(
            f"expected {expected_stage!r} manifest; observed {record['stage_id']!r}"
        )
    observed_self_hash = sha256_json(_manifest_payload(record))
    if observed_self_hash != record["manifest_sha256"]:
        raise ContractError(f"stage manifest payload changed: {manifest_path}")
    for upstream in record["upstream_manifests"]:
        upstream_path = _resolve_recorded_path(base, upstream["path"])
        if not upstream_path.is_file():
            raise ContractError(f"missing upstream manifest: {upstream['path']}")
        observed = sha256_file(upstream_path)
        if observed != upstream["sha256"]:
            raise ContractError(f"changed upstream manifest: {upstream['path']}")
        verify_stage_manifest(
            upstream_path,
            root=base,
            expected_stage=upstream["stage_id"],
            _seen=seen,
        )
    for artifact in record["artifacts"]:
        artifact_path = _resolve_recorded_path(base, artifact["path"])
        if not artifact_path.is_file():
            raise ContractError(f"missing stage artifact: {artifact['path']}")
        observed = sha256_file(artifact_path)
        if observed != artifact["sha256"]:
            raise ContractError(f"changed stage artifact: {artifact['path']}")
    if record["configuration_path"] is not None:
        configuration_path = _resolve_recorded_path(base, record["configuration_path"])
        if not configuration_path.is_file():
            raise ContractError(
                f"missing stage configuration: {record['configuration_path']}"
            )
        observed = sha256_file(configuration_path)
        if observed != record["configuration_sha256"]:
            raise ContractError(
                f"changed stage configuration: {record['configuration_path']}"
            )
    seen.remove(manifest_path)
    return record


def _upstream_product_paths(
    manifests: Sequence[Path], root: Path
) -> set[Path]:
    products: set[Path] = set()
    pending = list(manifests)
    visited: set[Path] = set()
    while pending:
        manifest_path = pending.pop()
        if manifest_path in visited:
            continue
        visited.add(manifest_path)
        record = verify_stage_manifest(manifest_path, root=root)
        products.add(manifest_path.resolve())
        products.update(
            _resolve_recorded_path(root, artifact["path"])
            for artifact in record["artifacts"]
        )
        pending.extend(
            _resolve_recorded_path(root, upstream["path"])
            for upstream in record["upstream_manifests"]
        )
    return products


def write_stage_manifest(
    path: Path | str,
    *,
    stage_id: str,
    artifact_paths: Sequence[Path | str],
    upstream_manifest_paths: Sequence[Path | str],
    root: Path | str,
    configuration_path: Path | str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Hash-chain a stage without permitting it to replace upstream products."""

    base = Path(root).resolve()
    destination = _rooted_path(path, base)
    _relative_path(destination, base)
    artifacts = [_rooted_path(item, base) for item in artifact_paths]
    upstream_paths = [_rooted_path(item, base) for item in upstream_manifest_paths]
    configuration = (
        None if configuration_path is None else _rooted_path(configuration_path, base)
    )
    if len(artifacts) != len(set(artifacts)):
        raise ContractError("duplicate stage artifact paths")
    protected = _upstream_product_paths(upstream_paths, base)
    collisions = sorted(str(item) for item in set(artifacts + [destination]) & protected)
    if collisions:
        raise ContractError(f"stage output would replace upstream product: {collisions}")
    artifact_records = []
    for artifact in artifacts:
        if not artifact.is_file():
            raise ContractError(f"missing stage artifact: {artifact}")
        artifact_records.append(
            {
                "path": _relative_path(artifact, base),
                "sha256": sha256_file(artifact),
                "kind": "file",
            }
        )
    upstream_records = []
    for upstream_path in upstream_paths:
        upstream_record = verify_stage_manifest(upstream_path, root=base)
        upstream_records.append(
            {
                "stage_id": upstream_record["stage_id"],
                "path": _relative_path(upstream_path, base),
                "sha256": sha256_file(upstream_path),
            }
        )
    payload: dict[str, Any] = {
        "schema_version": CONTRACT_VERSION,
        "stage_id": stage_id,
        "status": status or ("AUDIT_PASS" if stage_id == "audit" else "PASS"),
        "configuration_path": (
            None if configuration is None else _relative_path(configuration, base)
        ),
        "configuration_sha256": (
            None if configuration is None else sha256_file(configuration)
        ),
        "upstream_manifests": sorted(
            upstream_records,
            key=lambda item: (STAGE_IDS.index(item["stage_id"]), item["path"]),
        ),
        "artifacts": sorted(artifact_records, key=lambda item: item["path"]),
    }
    record = {**payload, "manifest_sha256": sha256_json(payload)}
    validate_records("stage_manifest", [record])
    atomic_write_json(destination, record)
    verify_stage_manifest(destination, root=base, expected_stage=stage_id)
    return record
