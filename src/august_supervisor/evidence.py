"""Audited dataset extraction for the frozen August supervisor report.

This module reads only the hash-locked artifacts declared by the frozen
configuration.  It contains no statistical fitting, plotting, or report
rendering code.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .contracts import (
    CONTRACT_VERSION,
    ContractError,
    atomic_write_csv,
    read_json_strict,
    read_registry_csv,
    sha256_file,
    validate_records,
    verify_evidence_sources,
    verify_stage_manifest,
    write_stage_manifest,
)


DEFAULT_CONFIGURATION = Path("configs/august_supervisor_report_v1.json")
DEFAULT_OUTPUT_DIR = Path("results/august_supervisor_report")

_CLAIM_KEYS = {
    "claim_id",
    "claim_role",
    "scientific_question",
    "sample",
    "scorer",
    "estimand",
    "numerical_result",
    "evidence_status",
    "source",
    "required_interpretation",
    "required_limitation",
    "destination_section",
    "figure_eligibility",
}
_SAMPLE_KEYS = {"role", "scope", "rows", "children", "sessions", "corpora"}
_SCORER_KEYS = {"model", "tokenizer", "comparability_rule"}
_ESTIMAND_KEYS = {
    "name",
    "outcome",
    "formula_or_contrast",
    "controls",
    "direction_convention",
}
_SOURCE_KEYS = {"canonical_artifact", "source_sha256", "required_marker"}
_MARKER_KEYS = {"path", "expectation", "observed", "satisfied"}
_NUMERICAL_KEYS = {"estimate", "unit", "interval", "uncertainty_method"}
_INTERVAL_KEYS = {"level", "low", "high", "type"}

_CSV_SCHEMAS: dict[str, tuple[str, ...]] = {
    "results/current_scientific_synthesis/direct_primary_estimates.csv": (
        "family",
        "question",
        "sample",
        "scorer",
        "model_id",
        "term",
        "estimate",
        "ci_low",
        "ci_high",
        "evidence_status",
    ),
    "results/current_scientific_synthesis/route2_final_estimates.csv": (
        "family",
        "model_id",
        "model_label",
        "estimator_id",
        "level",
        "outcome",
        "outcome_type",
        "term",
        "estimate",
        "std_error",
        "p_value",
        "conf_low",
        "conf_high",
        "evidence_status",
    ),
    "results/corrected_pbm_bayes_report/real_overall.csv": (
        "n",
        "real_probability",
        "real_median_probability",
        "prior_rank1_rate",
        "evidence_rank1_rate",
        "combined_rank1_rate",
        "combined_top2_rate",
        "prior_mean_rank",
        "combined_mean_rank",
    ),
    "results/corrected_pbm_bayes_report/context_validation.csv": (
        "dataset",
        "validation_n",
        "matched_accuracy",
        "mean_evidence_gap_bits",
        "pass",
        "training_rows",
        "excluded_rows",
    ),
    "results/direct_surprisal_replication/mistral_full79/modular/models/child_bootstrap_summary.csv": (
        "scope",
        "model_id",
        "outcome",
        "requested_reps",
        "successful_reps",
        "bootstrap_mean",
        "bootstrap_se",
        "bootstrap_ci_low",
        "bootstrap_ci_high",
    ),
    "results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/paired_all_outcome_slopes.csv": (
        "outcome",
        "label",
        "paired_rows",
        "children",
        "slope_tiny",
        "slope_mistral",
        "slope_difference_left_minus_right",
        "difference_ci_low",
        "difference_ci_high",
        "bootstrap_reps",
    ),
    "results/hall_snapshot_analysis/models/registered_contrasts.csv": (
        "model_id",
        "outcome",
        "contrast_id",
        "label",
        "estimate",
        "std_error",
        "ci_low",
        "ci_high",
        "p_value",
        "tier",
        "label_model",
    ),
    "results/word_cross_scorer_comparison/scientific_question_summary.csv": (
        "question_id",
        "question",
        "scientific_role",
        "common_direction",
        "scorers",
        "cluster_supported_scorers",
        "bootstrap_available_scorers",
        "bootstrap_supported_scorers",
        "replication_status",
    ),
}

_DIRECT_SELECTORS = {
    "DIRECT_PBM_MISTRAL_CONTEXTUAL": ("PBM21 discovery", "Mistral", "P1_k3_contextual"),
    "DIRECT_PBM_TINY_CONTEXTUAL": ("PBM21 scorer robustness", "TinyDialogues", "P1_k3_contextual"),
    "DIRECT_PBM_MISTRAL_UNCONDITIONAL": ("PBM21 discovery", "Mistral", "P2_k0_unconditional"),
    "DIRECT_PBM_TINY_UNCONDITIONAL": ("PBM21 scorer robustness", "TinyDialogues", "P2_k0_unconditional"),
    "DIRECT_NONPBM_MISTRAL_UNCONDITIONAL": ("non-PBM58 confirmation", "Mistral", "P2_k0_unconditional"),
    "DIRECT_PBM_MISTRAL_CONTEXT_GAIN": ("PBM21 discovery", "Mistral", "P3_k3_context_gain"),
    "DIRECT_PBM_TINY_CONTEXT_GAIN": ("PBM21 scorer robustness", "TinyDialogues", "P3_k3_context_gain"),
    "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN": ("non-PBM58 confirmation", "Mistral", "P3_k3_context_gain"),
    "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY": ("non-PBM58 confirmation", "Mistral", "P1_k3_contextual"),
}

_WORD_QUESTIONS = {
    "WORD_CROSS_SCORER_PREDICTABILITY": (
        "same_word_k0_age",
        "same_word_k3_age",
    ),
    "WORD_LONGER_TYPES_CONTEXT_SUPPORT": ("longer_words_context_support",),
    "WORD_CONTEXT_GAIN_SCORER_DEPENDENT": ("context_gain_age",),
}


def _require_exact_keys(value: Any, expected: set[str], location: str) -> None:
    if type(value) is not dict:
        raise ContractError(f"{location} must be an object")
    actual = set(value)
    if actual != expected:
        raise ContractError(
            f"{location} schema mismatch; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _require_nonempty_string(value: Any, location: str) -> None:
    if type(value) is not str or not value.strip():
        raise ContractError(f"{location} must be a nonempty string")


def _require_relative_path(value: Any, location: str) -> str:
    _require_nonempty_string(value, location)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"{location} must be a safe repository-relative path")
    return path.as_posix()


def _rooted(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def load_frozen_configuration(path: Path | str) -> dict[str, Any]:
    """Read and strictly validate the frozen stage-01 configuration."""

    config = read_json_strict(path)
    expected_top = {
        "schema_version",
        "frozen_at",
        "source_commit",
        "purpose",
        "allowed_evidence_statuses",
        "allowed_claim_roles",
        "allowed_figure_eligibility",
        "tokenizer_comparability_policy",
        "page_contract",
        "locked_readings",
        "claims",
        "blockers",
    }
    _require_exact_keys(config, expected_top, "configuration")
    if config["schema_version"] != CONTRACT_VERSION:
        raise ContractError("configuration schema_version does not match contracts")
    if type(config["claims"]) is not list or not config["claims"]:
        raise ContractError("configuration claims must be a nonempty list")
    if type(config["blockers"]) is not list:
        raise ContractError("configuration blockers must be a list")

    claim_ids: list[str] = []
    for index, claim in enumerate(config["claims"]):
        location = f"claims[{index}]"
        _require_exact_keys(claim, _CLAIM_KEYS, location)
        claim_id = claim["claim_id"]
        _require_nonempty_string(claim_id, f"{location}.claim_id")
        claim_ids.append(claim_id)
        _require_exact_keys(claim["sample"], _SAMPLE_KEYS, f"{claim_id}.sample")
        _require_exact_keys(claim["scorer"], _SCORER_KEYS, f"{claim_id}.scorer")
        _require_exact_keys(claim["estimand"], _ESTIMAND_KEYS, f"{claim_id}.estimand")
        _require_exact_keys(claim["source"], _SOURCE_KEYS, f"{claim_id}.source")
        marker = claim["source"]["required_marker"]
        allowed_marker_keys = _MARKER_KEYS | {"completion_marker_path"}
        if type(marker) is not dict or not _MARKER_KEYS.issubset(marker):
            raise ContractError(f"{claim_id}.required_marker schema mismatch")
        if set(marker) - allowed_marker_keys:
            raise ContractError(f"{claim_id}.required_marker has unexpected fields")
        _require_relative_path(
            claim["source"]["canonical_artifact"],
            f"{claim_id}.source.canonical_artifact",
        )
        expected_hash = claim["source"]["source_sha256"]
        if type(expected_hash) is not str or len(expected_hash) != 64:
            raise ContractError(f"{claim_id}.source_sha256 is not a SHA-256")
        if marker["path"] is not None:
            _require_relative_path(marker["path"], f"{claim_id}.required_marker.path")
        if marker.get("completion_marker_path") is not None:
            _require_relative_path(
                marker["completion_marker_path"],
                f"{claim_id}.required_marker.completion_marker_path",
            )
        for key in ("expectation", "observed"):
            _require_nonempty_string(marker[key], f"{claim_id}.required_marker.{key}")
        if type(marker["satisfied"]) is not bool:
            raise ContractError(f"{claim_id}.required_marker.satisfied must be boolean")
        if claim["claim_role"] not in config["allowed_claim_roles"]:
            raise ContractError(f"{claim_id} has unsupported claim role")
        if claim["evidence_status"] not in config["allowed_evidence_statuses"]:
            raise ContractError(f"{claim_id} has unsupported evidence status")
        if claim["figure_eligibility"] not in config["allowed_figure_eligibility"]:
            raise ContractError(f"{claim_id} has unsupported figure eligibility")
        pending = claim["claim_role"] == "PENDING"
        if pending != (claim["evidence_status"] == "PENDING"):
            raise ContractError(f"{claim_id} pending role/status mismatch")
        if pending == marker["satisfied"]:
            raise ContractError(f"{claim_id} marker satisfaction conflicts with evidence status")
        if type(claim["estimand"]["controls"]) is not list:
            raise ContractError(f"{claim_id}.estimand.controls must be a list")
        result = claim["numerical_result"]
        if result is not None:
            _require_exact_keys(result, _NUMERICAL_KEYS, f"{claim_id}.numerical_result")
            interval = result["interval"]
            if interval is not None:
                _require_exact_keys(interval, _INTERVAL_KEYS, f"{claim_id}.interval")
        elif not pending and claim_id not in _WORD_QUESTIONS and claim["claim_role"] != "EXCLUDED":
            raise ContractError(f"{claim_id} has an unsupported missing numerical result")
    if len(claim_ids) != len(set(claim_ids)):
        duplicates = sorted({item for item in claim_ids if claim_ids.count(item) > 1})
        raise ContractError(f"duplicate claim IDs: {duplicates}")

    blocker_ids = [item.get("claim_id") for item in config["blockers"]]
    pending_ids = [
        claim["claim_id"]
        for claim in config["claims"]
        if claim["evidence_status"] == "PENDING"
    ]
    if len(blocker_ids) != len(set(blocker_ids)):
        raise ContractError("duplicate blocker claim IDs")
    if set(blocker_ids) != set(pending_ids):
        raise ContractError("blocker coverage does not match pending claims")
    for index, blocker in enumerate(config["blockers"]):
        _require_exact_keys(
            blocker,
            {"claim_id", "status", "reason", "required_resolution"},
            f"blockers[{index}]",
        )
        if blocker["status"] != "BLOCKED":
            raise ContractError(f"blocker {blocker['claim_id']} must remain BLOCKED")
    return config


def _read_marker(path: Path) -> Any:
    if path.suffix == ".json":
        return read_json_strict(path)
    return path.read_text(encoding="utf-8")


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _validate_marker(claim: Mapping[str, Any], root: Path, cache: dict[str, Any]) -> None:
    marker_spec = claim["source"]["required_marker"]
    marker_path = marker_spec["path"]
    if marker_path is None:
        _expect(not marker_spec["satisfied"], f"{claim['claim_id']} has no required marker")
        return
    data = cache.setdefault(marker_path, _read_marker(root / marker_path))
    claim_id = claim["claim_id"]

    if marker_path.endswith("/models/model_manifest.json"):
        _expect(type(data) is dict, f"{claim_id} model marker schema mismatch")
        _expect(
            data.get("status") == "COMPLETE_WITH_RECORDED_FIT_STATUS",
            f"{claim_id} model marker is not COMPLETE_WITH_RECORDED_FIT_STATUS",
        )
        _expect(data.get("failed") == 0, f"{claim_id} model marker has failed fits")
        if "bootstrap_reps=1000" in marker_spec["expectation"]:
            _expect(data.get("bootstrap_reps") == 1000, f"{claim_id} bootstrap marker mismatch")
    elif marker_path.endswith("paired_tiny_mistral_pbm/modular/model_manifest.json"):
        _expect(type(data) is dict and data.get("status") == "COMPLETE", f"{claim_id} paired marker is not COMPLETE")
        _expect(data.get("outcomes") == 11, f"{claim_id} paired outcome count mismatch")
        _expect(data.get("bootstrap_reps") == 1000, f"{claim_id} paired bootstrap count mismatch")
    elif marker_path == "results/word_cross_scorer_comparison/manifest.json":
        _expect(type(data) is dict and data.get("status") == "PASS", f"{claim_id} word marker is not PASS")
        _expect(
            data.get("scorers") == ["Mistral", "Qwen3-14B", "TinyDialogues"],
            f"{claim_id} has ambiguous word scorer identities",
        )
        artifacts = {item.get("path"): item.get("sha256") for item in data.get("artifacts", []) if type(item) is dict}
        source_path = claim["source"]["canonical_artifact"]
        if source_path != marker_path:
            _expect(
                artifacts.get(source_path) == claim["source"]["source_sha256"],
                f"{claim_id} word marker does not lock its canonical source",
            )
    elif marker_path == "results/current_scientific_synthesis/manifest.json":
        _expect(type(data) is dict and data.get("status") == "PASS", f"{claim_id} synthesis marker is not PASS")
        artifacts = {item.get("path"): item.get("sha256") for item in data.get("artifacts", []) if type(item) is dict}
        _expect(
            artifacts.get(claim["source"]["canonical_artifact"])
            == claim["source"]["source_sha256"],
            f"{claim_id} synthesis marker does not lock its canonical source",
        )
    elif marker_path.endswith("pbm_crossfit_bayes_scores.audit.json"):
        _expect(type(data) is dict, f"{claim_id} Bayes marker schema mismatch")
        _expect(data.get("all_context_validation_pass") is True, f"{claim_id} Bayes validation did not pass")
        _expect(data.get("normalization_scope") == "candidate_set_within_row", f"{claim_id} Bayes normalization mismatch")
        folds = data.get("folds")
        _expect(type(folds) is list and len(folds) == 3, f"{claim_id} Bayes folds mismatch")
        _expect(all(item.get("context_validation_pass") is True for item in folds), f"{claim_id} Bayes fold validation failed")
    elif marker_path == "results/direct_surprisal_onset_confirmation/audit.json":
        _expect(type(data) is dict and data.get("status") == "PASS", f"{claim_id} onset marker is not PASS")
        _expect(data.get("bootstrap_reps") == 1000, f"{claim_id} onset bootstrap count mismatch")
        scopes = data.get("scopes")
        _expect(type(scopes) is list and len(scopes) == 2, f"{claim_id} onset scope schema mismatch")
        _expect(all(item.get("sustained_onset") == "not_established" for item in scopes), f"{claim_id} onset status changed")
    elif marker_path == "results/hall_snapshot_analysis/final/final_audit.json":
        _expect(type(data) is dict and data.get("status") == "PASS", f"{claim_id} Hall marker is not PASS")
        _expect(data.get("problem_count") == 0, f"{claim_id} Hall audit has problems")
        _expect(data.get("passed_models") == data.get("registered_models") == 20, f"{claim_id} Hall model count mismatch")
        completion_path = marker_spec.get("completion_marker_path")
        _expect(completion_path is not None, f"{claim_id} Hall completion marker is missing")
        completion = cache.setdefault(completion_path, _read_marker(root / completion_path))
        lines = completion.splitlines()
        _expect(lines and lines[0] == "ANALYSIS_COMPLETE_AND_AUDITED", f"{claim_id} Hall completion marker changed")
        _expect(len(lines) >= 2 and lines[1] == sha256_file(root / marker_path), f"{claim_id} Hall completion hash mismatch")
    elif marker_path == "results/complete_analysis_machine_v1/preflight.json":
        _expect(type(data) is dict, f"{claim_id} preflight marker schema mismatch")
        matches = [item for item in data.get("components", []) if item.get("component_id") == "word_mistral_nonpbm58"]
        _expect(len(matches) == 1, f"{claim_id} preflight component is missing or ambiguous")
        _expect(matches[0].get("status") == "BLOCKED", f"{claim_id} is no longer declared BLOCKED")
    elif marker_path == "results/conversational_eligibility/full79_child_conversational_flags.audit.json":
        _expect(type(data) is dict and data.get("status") == "REVIEW", f"{claim_id} conversational marker is not REVIEW")
        _expect(data.get("manual_sample_rows") == 325, f"{claim_id} manual sample count mismatch")
        counts = data.get("counts")
        _expect(type(counts) is dict and counts.get("eligible_context_k1_mismatches") == 18172, f"{claim_id} mismatch count changed")
    else:
        _expect(type(data) is dict, f"{claim_id} marker schema mismatch")
        expected_status = None
        if marker_spec["expectation"].startswith("status="):
            expected_status = marker_spec["expectation"].split("=", 1)[1].split()[0]
        if expected_status is not None:
            _expect(data.get("status") == expected_status, f"{claim_id} marker status mismatch")


def verify_declared_inputs(
    claims: Iterable[Mapping[str, Any]], root: Path | str
) -> dict[str, str]:
    """Hash every source and marker before parsing any declared source table."""

    base = Path(root).resolve()
    materialized = [dict(claim) for claim in claims]
    claim_ids = [claim.get("claim_id") for claim in materialized]
    if len(claim_ids) != len(set(claim_ids)):
        raise ContractError("duplicate claim IDs in extraction input")

    expected_sources: dict[str, str] = {}
    all_paths: set[str] = set()
    for claim in materialized:
        claim_id = claim.get("claim_id", "claim")
        source = claim.get("source")
        if type(source) is not dict:
            raise ContractError(f"{claim_id}.source schema mismatch")
        source_path = _require_relative_path(source.get("canonical_artifact"), f"{claim_id}.source")
        expected_hash = source.get("source_sha256")
        if type(expected_hash) is not str or len(expected_hash) != 64:
            raise ContractError(f"{claim_id}.source hash is invalid")
        previous = expected_sources.setdefault(source_path, expected_hash)
        if previous != expected_hash:
            raise ContractError(f"conflicting frozen hashes for source {source_path}")
        all_paths.add(source_path)
        marker = source.get("required_marker")
        if type(marker) is not dict:
            raise ContractError(f"{claim_id}.required_marker schema mismatch")
        marker_path = marker.get("path")
        if marker_path is not None:
            all_paths.add(_require_relative_path(marker_path, f"{claim_id}.marker"))
        elif marker.get("satisfied") is True:
            raise ContractError(f"{claim_id} admitted evidence is missing its marker")
        completion = marker.get("completion_marker_path")
        if completion is not None:
            all_paths.add(_require_relative_path(completion, f"{claim_id}.completion_marker"))

    snapshot: dict[str, str] = {}
    for relative in sorted(all_paths):
        path = base / relative
        if not path.is_file():
            label = "source" if relative in expected_sources else "audit marker"
            raise ContractError(f"missing {label}: {relative}")
        snapshot[relative] = sha256_file(path)
    for relative, expected in sorted(expected_sources.items()):
        observed = snapshot[relative]
        if observed != expected:
            raise ContractError(
                f"changed source {relative}: expected {expected}, observed {observed}"
            )

    marker_cache: dict[str, Any] = {}
    for claim in materialized:
        _validate_marker(claim, base, marker_cache)
    return snapshot


def _read_csv_strict(path: Path, relative: str) -> list[dict[str, str]]:
    expected = _CSV_SCHEMAS.get(relative)
    if expected is None:
        raise ContractError(f"unsupported canonical CSV source: {relative}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as error:
            raise ContractError(f"{relative} is an empty CSV") from error
        if len(header) != len(set(header)):
            raise ContractError(f"{relative} has duplicate headers")
        if tuple(header) != expected:
            raise ContractError(
                f"{relative} schema mismatch; expected={expected}, observed={tuple(header)}"
            )
        rows: list[dict[str, str]] = []
        for row_number, values in enumerate(reader, start=2):
            if len(values) != len(header):
                raise ContractError(f"{relative}:{row_number} field-count schema mismatch")
            row = dict(zip(header, values))
            missing = [key for key, value in row.items() if value == ""]
            if missing:
                raise ContractError(
                    f"{relative}:{row_number} has unsupported missing values: {missing}"
                )
            rows.append(row)
    if not rows:
        raise ContractError(f"{relative} has no data rows")
    return rows


def _read_canonical_sources(
    claims: Sequence[Mapping[str, Any]], root: Path
) -> dict[str, Any]:
    sources: dict[str, Any] = {}
    for claim in claims:
        relative = claim["source"]["canonical_artifact"]
        if relative in sources:
            continue
        path = root / relative
        if path.suffix == ".csv":
            sources[relative] = _read_csv_strict(path, relative)
        elif path.suffix == ".json":
            value = read_json_strict(path)
            if type(value) is not dict:
                raise ContractError(f"{relative} JSON schema mismatch")
            sources[relative] = value
        elif path.suffix == ".md":
            # Prose is hash-gated for pending/exclusion provenance only.  No
            # estimate or count is ever scraped from it.
            sources[relative] = None
        else:
            raise ContractError(f"unsupported canonical source type: {relative}")
    return sources


def _select_one(
    rows: Sequence[Mapping[str, str]], claim_id: str, **criteria: str
) -> Mapping[str, str]:
    matches = [
        row for row in rows if all(row.get(column) == value for column, value in criteria.items())
    ]
    if not matches:
        raise ContractError(f"{claim_id} is missing from its canonical source")
    if len(matches) != 1:
        raise ContractError(f"{claim_id} has an ambiguous scorer/sample identity")
    return matches[0]


def _number(raw: Any, location: str) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError) as error:
        raise ContractError(f"{location} is not numeric") from error
    if not math.isfinite(value):
        raise ContractError(f"{location} is not finite")
    return value


def _same_frozen_number(expected: Any, observed: Any, location: str) -> None:
    if expected is None:
        raise ContractError(f"{location} unexpectedly has no frozen value")
    if not math.isclose(float(expected), _number(observed, location), rel_tol=0.0, abs_tol=5e-7):
        raise ContractError(f"{location} changed: expected {expected}, observed {observed}")


def _validate_numeric_result(
    claim: Mapping[str, Any], row: Mapping[str, str], *, low: str, high: str, estimate: str
) -> None:
    result = claim["numerical_result"]
    _expect(type(result) is dict, f"{claim['claim_id']} has no frozen numerical result")
    _same_frozen_number(result["estimate"], row[estimate], f"{claim['claim_id']}.estimate")
    interval = result["interval"]
    _expect(type(interval) is dict, f"{claim['claim_id']} has no frozen interval")
    _same_frozen_number(interval["low"], row[low], f"{claim['claim_id']}.ci_low")
    _same_frozen_number(interval["high"], row[high], f"{claim['claim_id']}.ci_high")


def _validate_one_claim(claim: Mapping[str, Any], sources: Mapping[str, Any]) -> None:
    claim_id = claim["claim_id"]
    relative = claim["source"]["canonical_artifact"]
    source = sources[relative]

    if claim_id in _DIRECT_SELECTORS:
        sample, scorer, model_id = _DIRECT_SELECTORS[claim_id]
        row = _select_one(source, claim_id, sample=sample, scorer=scorer, model_id=model_id, term="age_c")
        _validate_numeric_result(claim, row, estimate="estimate", low="ci_low", high="ci_high")
    elif claim_id == "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP":
        row = _select_one(source, claim_id, scope="non_pbm_confirmation", model_id="P1_k3_contextual", outcome="real_k3_sum_bits")
        _validate_numeric_result(
            claim,
            row,
            estimate="bootstrap_mean",
            low="bootstrap_ci_low",
            high="bootstrap_ci_high",
        )
        _expect(row["requested_reps"] == row["successful_reps"] == "1000", f"{claim_id} bootstrap is incomplete")
    elif claim_id == "DIRECT_PAIRED_CONTEXTUAL_SCORER_DIFFERENCE":
        row = _select_one(source, claim_id, outcome="real_k3_sum_bits")
        _validate_numeric_result(
            claim,
            row,
            estimate="slope_difference_left_minus_right",
            low="difference_ci_low",
            high="difference_ci_high",
        )
        _expect(int(row["paired_rows"]) == claim["sample"]["rows"], f"{claim_id} row count changed")
        _expect(int(row["children"]) == claim["sample"]["children"], f"{claim_id} child count changed")
        _expect(row["bootstrap_reps"] == "1000", f"{claim_id} bootstrap count changed")
    elif claim_id in {"ROUTE2_RELATIVE_EFFORT_AGE", "ROUTE2_AGE_ENTROPY_INTERACTION"}:
        term = "age_months_c" if claim_id.endswith("EFFORT_AGE") else "age_months_c:response_entropy_bits_c"
        row = _select_one(
            source,
            claim_id,
            model_id="minus_gen_mean_r2m5_age_by_entropy",
            estimator_id="session_gee_exchangeable",
            outcome="child_words_minus_generated_mean",
            term=term,
        )
        _validate_numeric_result(claim, row, estimate="estimate", low="conf_low", high="conf_high")
    elif claim_id == "BAYES_REAL_CANDIDATE_SET_PROBABILITY":
        _expect(len(source) == 1, f"{claim_id} canonical row is ambiguous")
        row = source[0]
        _same_frozen_number(claim["numerical_result"]["estimate"], row["combined_rank1_rate"], f"{claim_id}.estimate")
        _expect(int(row["n"]) == claim["sample"]["rows"], f"{claim_id} row count changed")
        _expect(round(_number(row["real_probability"], f"{claim_id}.real_probability"), 3) == 0.400, f"{claim_id} mean probability changed")
    elif claim_id == "BAYES_HELDOUT_CONTEXT_VALIDATION":
        _expect({row["dataset"] for row in source} == {"Brown", "Manchester", "Providence"}, f"{claim_id} corpus identities changed")
        _expect(all(row["pass"] == "True" for row in source), f"{claim_id} has a failed corpus")
        _expect(sum(int(row["validation_n"]) for row in source) == claim["sample"]["rows"], f"{claim_id} validation count changed")
        _same_frozen_number(claim["numerical_result"]["estimate"], sum(row["pass"] == "True" for row in source), f"{claim_id}.estimate")
    elif claim_id in {"ONSET_PBM_SUSTAINED", "ONSET_NONPBM_SUSTAINED"}:
        _expect(source.get("status") == "PASS" and source.get("bootstrap_reps") == 1000, f"{claim_id} onset audit changed")
        scope_name = "pbm_discovery" if claim_id == "ONSET_PBM_SUSTAINED" else "non_pbm_confirmation"
        scopes = [item for item in source.get("scopes", []) if item.get("scope") == scope_name]
        _expect(len(scopes) == 1, f"{claim_id} onset scope is missing or ambiguous")
        scope = scopes[0]
        _expect(scope.get("sustained_onset") == "not_established", f"{claim_id} onset status changed")
        _expect(scope.get("source_rows") == claim["sample"]["rows"], f"{claim_id} row count changed")
        _expect(scope.get("children") == claim["sample"]["children"], f"{claim_id} child count changed")
        _expect(scope.get("bootstrap_reps_successful") == 1000, f"{claim_id} bootstrap incomplete")
    elif claim_id.startswith("HALL_"):
        selector = {
            "HALL_RACE_CLASS_INTERACTION": ("H1_k0_primary", "race_by_class_interaction"),
            "HALL_ADULT_CONTEXT_INTERACTION": ("H9_gain_k3_adult_adjacent", "race_by_class_interaction"),
            "HALL_LOCKED_DOMAIN_SHIFT": ("E1_k0_locked_snapshot", "hall_minus_current"),
        }[claim_id]
        row = _select_one(source, claim_id, model_id=selector[0], contrast_id=selector[1])
        _validate_numeric_result(claim, row, estimate="estimate", low="ci_low", high="ci_high")
    elif claim_id in _WORD_QUESTIONS:
        rows = [_select_one(source, claim_id, question_id=question_id) for question_id in _WORD_QUESTIONS[claim_id]]
        _expect(all(row["scorers"] == "3" for row in rows), f"{claim_id} scorer count changed")
        if claim_id in {"WORD_CROSS_SCORER_PREDICTABILITY", "WORD_LONGER_TYPES_CONTEXT_SUPPORT"}:
            _expect(all(row["replication_status"] == "direction_and_interval_robust" for row in rows), f"{claim_id} robustness status changed")
            _expect(all(row["cluster_supported_scorers"] == row["bootstrap_supported_scorers"] == "3" for row in rows), f"{claim_id} interval support changed")
        else:
            _expect(rows[0]["replication_status"] == "scorer_dependent" and rows[0]["common_direction"] == "mixed", f"{claim_id} scorer-dependence status changed")
    elif claim_id == "CROSS_TOKENIZER_MAGNITUDE_POOLING":
        _expect(type(source) is dict and source.get("status") == "PASS", f"{claim_id} word manifest changed")
        _expect(source.get("scorers") == ["Mistral", "Qwen3-14B", "TinyDialogues"], f"{claim_id} scorer identities changed")
    elif claim_id in {
        "RESPONSE_ENTROPY_SEMANTIC_CLAIM",
        "GENERATED_CANDIDATE_MEANING_PRESERVATION",
        "LISTENER_UTILITY_OUTCOME",
        "DECOUPLED_RESPONSE_CALIBRATION",
        "ALTERNATIVE_EFFORT_ONSET",
    }:
        _expect(source is None, f"{claim_id} must not scrape report prose")
    elif claim_id == "WORD_NONPBM58_CONFIRMATION":
        components = [item for item in source.get("components", []) if item.get("component_id") == "word_mistral_nonpbm58"]
        _expect(len(components) == 1 and components[0].get("status") == "BLOCKED", f"{claim_id} blocker source changed")
    elif claim_id == "CONVERSATIONAL_MANUAL_VALIDATION":
        _expect(source.get("status") == "REVIEW", f"{claim_id} source is not REVIEW")
        _expect(source.get("counts", {}).get("rows") == claim["sample"]["rows"], f"{claim_id} row count changed")
        _expect(source.get("manual_sample_rows") == 325, f"{claim_id} manual sample count changed")
    else:
        raise ContractError(f"unregistered extraction rule for claim {claim_id}")


def validate_canonical_claims(
    claims: Sequence[Mapping[str, Any]], root: Path | str
) -> dict[str, Any]:
    """Validate every frozen claim against its canonical CSV/JSON source."""

    base = Path(root).resolve()
    sources = _read_canonical_sources(claims, base)
    for claim in claims:
        _validate_one_claim(claim, sources)
    return sources


def _scope_for_claim(claim: Mapping[str, Any]) -> str:
    claim_id = claim["claim_id"]
    role = claim["sample"]["role"].lower()
    if claim["evidence_status"] == "PENDING":
        return "PENDING_EVIDENCE"
    if "hall" in role:
        return "HALL_SNAPSHOT"
    if "bayes" in role or "held-out validation" in role:
        return "PBM_BAYES_ROBUSTNESS"
    if "response-space" in role or claim_id in {
        "RESPONSE_ENTROPY_SEMANTIC_CLAIM",
        "GENERATED_CANDIDATE_MEANING_PRESERVATION",
    }:
        return "PBM_RESPONSE_SPACE"
    if "non-pbm" in role:
        return "NON_PBM_CONFIRMATION"
    if "robustness" in role or "word-level" in role or claim_id == "CROSS_TOKENIZER_MAGNITUDE_POOLING":
        return "PBM_SCORER_ROBUSTNESS"
    if "pbm discovery" in role:
        return "PBM_DISCOVERY"
    raise ContractError(f"{claim_id} has an ambiguous sample scope")


def _audit_status(claim: Mapping[str, Any]) -> str:
    if claim["evidence_status"] != "PENDING":
        return "PASS"
    marker_path = claim["source"]["required_marker"]["path"]
    if marker_path == "results/conversational_eligibility/full79_child_conversational_flags.audit.json":
        return "REVIEW"
    if marker_path is not None:
        return "BLOCKED"
    return "MISSING"


def build_sample_records(
    config: Mapping[str, Any], input_hashes: Mapping[str, str]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for claim in config["claims"]:
        source = claim["source"]
        marker_path = source["required_marker"]["path"]
        records.append(
            {
                "schema_version": CONTRACT_VERSION,
                "sample_id": f"SAMPLE_{claim['claim_id']}",
                "scope": _scope_for_claim(claim),
                "sample_role": claim["sample"]["role"],
                "description": (
                    f"{claim['sample']['scope']} | scorer={claim['scorer']['model']} "
                    f"| tokenizer={claim['scorer']['tokenizer']}"
                ),
                "rows": claim["sample"]["rows"],
                "children": claim["sample"]["children"],
                "sessions": claim["sample"]["sessions"],
                "corpora": claim["sample"]["corpora"],
                "audit_status": _audit_status(claim),
                "source_artifact": source["canonical_artifact"],
                "source_sha256": source["source_sha256"],
                "audit_marker": marker_path,
                "audit_marker_sha256": None if marker_path is None else input_hashes[marker_path],
            }
        )
    return validate_records("sample", records)


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ContractError(f"stage path is outside repository root: {path}") from error


def _with_configuration_hash(
    snapshot: Mapping[str, str], configuration_path: Path, root: Path
) -> dict[str, str]:
    combined = dict(snapshot)
    combined[_relative_to_root(configuration_path, root)] = sha256_file(configuration_path)
    return dict(sorted(combined.items()))


def extract_datasets(
    *,
    root: Path | str,
    configuration_path: Path | str = DEFAULT_CONFIGURATION,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Build the deterministic sample registry and PASS dataset manifest."""

    base = Path(root).resolve()
    config_path = _rooted(configuration_path, base).resolve()
    destination = _rooted(output_dir, base).resolve()
    _relative_to_root(config_path, base)
    _relative_to_root(destination, base)
    config = load_frozen_configuration(config_path)

    before = _with_configuration_hash(
        verify_declared_inputs(config["claims"], base), config_path, base
    )
    validate_canonical_claims(config["claims"], base)
    samples = build_sample_records(config, before)
    verify_evidence_sources({"sample": samples}, base)

    registry_path = destination / "sample_registry.csv"
    manifest_path = destination / "dataset_manifest.json"
    atomic_write_csv(registry_path, "sample", samples)
    read_registry_csv(registry_path, "sample")
    manifest = write_stage_manifest(
        manifest_path,
        stage_id="datasets",
        artifact_paths=[registry_path],
        upstream_manifest_paths=[],
        root=base,
        configuration_path=config_path,
    )
    verify_stage_manifest(manifest_path, root=base, expected_stage="datasets")

    after = _with_configuration_hash(
        verify_declared_inputs(config["claims"], base), config_path, base
    )
    if before != after:
        raise ContractError("upstream inputs changed during datasets extraction")
    return {
        "status": "PASS",
        "stage": "datasets",
        "row_counts": {"sample_registry": len(samples)},
        "artifacts": {
            "sample_registry": _relative_to_root(registry_path, base),
            "dataset_manifest": _relative_to_root(manifest_path, base),
        },
        "artifact_sha256": {
            "sample_registry": sha256_file(registry_path),
            "dataset_manifest": sha256_file(manifest_path),
        },
        "input_hashes_before": before,
        "input_hashes_after": after,
        "manifest": manifest,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--configuration", type=Path, default=DEFAULT_CONFIGURATION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = extract_datasets(
        root=args.root,
        configuration_path=args.configuration,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
