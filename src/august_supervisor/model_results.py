"""Extract frozen model results into audited August report registries.

The stage copies only already-audited claim metadata and numeric values that
have been reconciled against canonical CSV/JSON sources.  It never imports a
model-fitting library or calls an analysis entry point.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import (
    CONTRACT_VERSION,
    ContractError,
    atomic_write_csv,
    read_json_strict,
    read_registry_csv,
    sha256_file,
    validate_registry_bundle,
    verify_evidence_sources,
    verify_stage_manifest,
    write_stage_manifest,
)
from .evidence import (
    DEFAULT_CONFIGURATION,
    DEFAULT_OUTPUT_DIR,
    _relative_to_root,
    _rooted,
    _with_configuration_hash,
    build_sample_records,
    load_frozen_configuration,
    validate_canonical_claims,
    verify_declared_inputs,
)


_WORD_CLAIMS = {
    "WORD_CROSS_SCORER_PREDICTABILITY",
    "WORD_LONGER_TYPES_CONTEXT_SUPPORT",
    "WORD_CONTEXT_GAIN_SCORER_DEPENDENT",
}
_EXCLUDED_CLAIMS = {
    "CROSS_TOKENIZER_MAGNITUDE_POOLING",
    "RESPONSE_ENTROPY_SEMANTIC_CLAIM",
    "GENERATED_CANDIDATE_MEANING_PRESERVATION",
}


def _source_fields(
    claim: Mapping[str, Any], input_hashes: Mapping[str, str]
) -> dict[str, Any]:
    source = claim["source"]
    marker_path = source["required_marker"]["path"]
    return {
        "source_artifact": source["canonical_artifact"],
        "source_sha256": source["source_sha256"],
        "audit_marker": marker_path,
        "audit_marker_sha256": (
            None if marker_path is None else input_hashes[marker_path]
        ),
    }


def _scorer_for_claim(claim: Mapping[str, Any]) -> str:
    claim_id = claim["claim_id"]
    model = claim["scorer"]["model"].lower()
    if claim_id.startswith("BAYES_"):
        return "CORRECTED_BAYES"
    if "response space" in model or "response generator" in model:
        return "MISTRAL_RESPONSE_SPACE"
    has_mistral = "mistral" in model
    has_tiny = "tinydialogues" in model or "smollm" in model
    has_qwen = "qwen" in model
    if sum((has_mistral, has_tiny, has_qwen)) > 1:
        return "MULTI_SCORER"
    if has_qwen:
        return "QWEN3_14B"
    if has_tiny:
        return "TINYDIALOGUES_SMOLLM2_135M"
    if has_mistral:
        return "MISTRAL_7B_V03"
    if model in {"not applicable", "not registered"}:
        return "NOT_APPLICABLE"
    raise ContractError(f"{claim_id} has an ambiguous scorer identity")


def _estimator_for_claim(claim_id: str) -> str:
    if claim_id == "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP":
        return "Frozen child-resampling bootstrap of P1 WLS"
    if claim_id == "DIRECT_PAIRED_CONTEXTUAL_SCORER_DIFFERENCE":
        return "Paired child-resampling bootstrap"
    if claim_id.startswith("DIRECT_"):
        return "Frozen WLS on child-age-effort design cells"
    if claim_id in _WORD_CLAIMS:
        return "Registered scorer-specific word model"
    if claim_id.startswith("ROUTE2_"):
        return "Session-level exchangeable GEE"
    if claim_id == "BAYES_REAL_CANDIDATE_SET_PROBABILITY":
        return "Descriptive leave-corpus-out candidate-set aggregation"
    if claim_id == "BAYES_HELDOUT_CONTEXT_VALIDATION":
        return "Predefined held-out per-corpus validation gate"
    if claim_id.startswith("ONSET_"):
        return "Frozen simultaneous-band sustained-onset procedure"
    if claim_id.startswith("HALL_"):
        return "Registered Hall contrast model"
    raise ContractError(f"no registered estimator for claim {claim_id}")


def _clustering_unit(claim_id: str) -> str:
    if claim_id.startswith("DIRECT_") or claim_id.startswith("ONSET_"):
        return "child"
    if claim_id in _WORD_CLAIMS:
        return "scorer-specific child/corpus structure from frozen word protocol"
    if claim_id.startswith("ROUTE2_"):
        return "child with child-session aggregate observations"
    if claim_id.startswith("HALL_"):
        return "child"
    if claim_id.startswith("BAYES_"):
        return "not applicable to promoted descriptive/gate summary"
    return "not applicable"


def _warning_summary(claim: Mapping[str, Any], root: Path) -> tuple[str, str]:
    marker_path = claim["source"]["required_marker"]["path"]
    if marker_path is None:
        return "NOT_APPLICABLE", "no completed model marker"
    if marker_path.endswith("/models/model_manifest.json"):
        marker = read_json_strict(root / marker_path)
        singular = marker["singular"]
        nonconverged = marker["nonconverged"]
        failed = marker["failed"]
        summary = (
            f"aggregate declared model family: singular_or_boundary={singular}; "
            f"nonconverged={nonconverged}; failed={failed}"
        )
        status = "PASS_WITH_WARNINGS" if singular or nonconverged else "PASS"
        return status, summary
    return "PASS", "no claim-level convergence warning in the declared marker"


def _formula_with_controls(claim: Mapping[str, Any]) -> str:
    controls = json.dumps(
        claim["estimand"]["controls"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"{claim['estimand']['formula_or_contrast']} | controls={controls}"


def _model_variants(claim: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    claim_id = claim["claim_id"]
    if claim_id in _WORD_CLAIMS:
        return [
            ("MISTRAL", "MISTRAL_7B_V03", "Mistral-7B-v0.3 tokenizer"),
            ("QWEN3", "QWEN3_14B", "Qwen3-14B tokenizer"),
            (
                "TINYDIALOGUES",
                "TINYDIALOGUES_SMOLLM2_135M",
                "SmolLM2/TinyDialogues tokenizer",
            ),
        ]
    return [
        (
            "",
            _scorer_for_claim(claim),
            claim["scorer"]["tokenizer"],
        )
    ]


def build_model_records(
    config: Mapping[str, Any], input_hashes: Mapping[str, str], root: Path
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    records: list[dict[str, Any]] = []
    models_by_claim: dict[str, list[str]] = {}
    for claim in config["claims"]:
        claim_id = claim["claim_id"]
        if claim["evidence_status"] == "PENDING" or claim_id in _EXCLUDED_CLAIMS:
            continue
        fit_status, warnings = _warning_summary(claim, root)
        for suffix, scorer, tokenizer in _model_variants(claim):
            model_id = f"MODEL_{claim_id}" + (f"_{suffix}" if suffix else "")
            models_by_claim.setdefault(claim_id, []).append(model_id)
            records.append(
                {
                    "schema_version": CONTRACT_VERSION,
                    "model_id": model_id,
                    "claim_id": claim_id,
                    "sample_id": f"SAMPLE_{claim_id}",
                    "scorer": scorer,
                    "tokenizer_namespace": tokenizer,
                    "outcome": claim["estimand"]["outcome"],
                    "formula_or_contrast": _formula_with_controls(claim),
                    "estimator": f"{_estimator_for_claim(claim_id)}; convergence_warnings={warnings}",
                    "uncertainty_method": (
                        f"{_effect_uncertainty(claim)}; "
                        f"clustering_unit={_clustering_unit(claim_id)}"
                    ),
                    "fit_status": fit_status,
                    **_source_fields(claim, input_hashes),
                }
            )
    return records, models_by_claim


def _effect_uncertainty(claim: Mapping[str, Any]) -> str:
    result = claim["numerical_result"]
    if result is not None:
        return result["uncertainty_method"]
    if claim["claim_id"] in _WORD_CLAIMS:
        return "Separate scorer-specific clustered and bootstrap interval classification"
    return "Not applicable; this is a frozen interpretation exclusion"


def _effect_unit(claim: Mapping[str, Any]) -> str:
    result = claim["numerical_result"]
    if result is not None:
        return result["unit"]
    if claim["claim_id"] in _WORD_CLAIMS:
        return "separate scorer-native effect classifications"
    return "not applicable"


def build_effect_records(
    config: Mapping[str, Any],
    input_hashes: Mapping[str, str],
    models_by_claim: Mapping[str, list[str]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for claim in config["claims"]:
        if claim["evidence_status"] == "PENDING":
            continue
        result = claim["numerical_result"]
        interval = None if result is None else result["interval"]
        model_ids = models_by_claim.get(claim["claim_id"], [])
        records.append(
            {
                "schema_version": CONTRACT_VERSION,
                "effect_id": f"EFFECT_{claim['claim_id']}",
                "claim_id": claim["claim_id"],
                "claim_role": claim["claim_role"],
                "sample_id": f"SAMPLE_{claim['claim_id']}",
                "model_id": model_ids[0] if len(model_ids) == 1 else None,
                "evidence_status": claim["evidence_status"],
                "estimate": None if result is None else result["estimate"],
                "unit": _effect_unit(claim),
                "ci_level": None if interval is None else interval["level"],
                "ci_low": None if interval is None else interval["low"],
                "ci_high": None if interval is None else interval["high"],
                "uncertainty_method": (
                    f"{_effect_uncertainty(claim)}; "
                    f"clustering_unit={_clustering_unit(claim['claim_id'])}"
                ),
                "direction_convention": claim["estimand"]["direction_convention"],
                "interpretation": claim["required_interpretation"],
                "limitation": claim["required_limitation"],
                "figure_eligibility": claim["figure_eligibility"],
                **_source_fields(claim, input_hashes),
            }
        )
    return records


def build_blocker_records(
    config: Mapping[str, Any], input_hashes: Mapping[str, str]
) -> list[dict[str, Any]]:
    claims = {claim["claim_id"]: claim for claim in config["claims"]}
    records: list[dict[str, Any]] = []
    for blocker in config["blockers"]:
        claim = claims[blocker["claim_id"]]
        records.append(
            {
                "schema_version": CONTRACT_VERSION,
                "blocker_id": f"BLOCKER_{claim['claim_id']}",
                "claim_id": claim["claim_id"],
                "sample_id": f"SAMPLE_{claim['claim_id']}",
                "blocker_status": blocker["status"],
                "reason": blocker["reason"],
                "required_resolution": blocker["required_resolution"],
                **_source_fields(claim, input_hashes),
            }
        )
    return records


def _snapshot_with_dataset_inputs(
    snapshot: Mapping[str, str],
    *,
    configuration_path: Path,
    dataset_manifest_path: Path,
    sample_registry_path: Path,
    root: Path,
) -> dict[str, str]:
    combined = _with_configuration_hash(snapshot, configuration_path, root)
    for path in (dataset_manifest_path, sample_registry_path):
        combined[_relative_to_root(path, root)] = sha256_file(path)
    return dict(sorted(combined.items()))


def extract_model_results(
    *,
    root: Path | str,
    configuration_path: Path | str = DEFAULT_CONFIGURATION,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    dataset_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build effect/model/blocker registries and their chained PASS manifest."""

    base = Path(root).resolve()
    config_path = _rooted(configuration_path, base).resolve()
    destination = _rooted(output_dir, base).resolve()
    dataset_manifest = (
        destination / "dataset_manifest.json"
        if dataset_manifest_path is None
        else _rooted(dataset_manifest_path, base).resolve()
    )
    sample_registry_path = destination / "sample_registry.csv"
    for path in (config_path, destination, dataset_manifest, sample_registry_path):
        _relative_to_root(path, base)

    verify_stage_manifest(dataset_manifest, root=base, expected_stage="datasets")
    config = load_frozen_configuration(config_path)
    before = _snapshot_with_dataset_inputs(
        verify_declared_inputs(config["claims"], base),
        configuration_path=config_path,
        dataset_manifest_path=dataset_manifest,
        sample_registry_path=sample_registry_path,
        root=base,
    )
    validate_canonical_claims(config["claims"], base)

    samples = read_registry_csv(sample_registry_path, "sample")
    expected_samples = build_sample_records(config, before)
    if samples != expected_samples:
        raise ContractError("dataset sample registry does not match the frozen claims")

    models, models_by_claim = build_model_records(config, before, base)
    effects = build_effect_records(config, before, models_by_claim)
    blockers = build_blocker_records(config, before)
    bundle = validate_registry_bundle(
        {
            "sample": samples,
            "model": models,
            "effect": effects,
            "blocker": blockers,
        }
    )
    verify_evidence_sources(bundle, base)

    effect_path = destination / "effect_registry.csv"
    model_path = destination / "model_inventory.csv"
    blocker_path = destination / "declared_blockers.csv"
    manifest_path = destination / "model_results_manifest.json"
    atomic_write_csv(effect_path, "effect", bundle["effect"])
    atomic_write_csv(model_path, "model", bundle["model"])
    atomic_write_csv(blocker_path, "blocker", bundle["blocker"])
    read_registry_csv(effect_path, "effect")
    read_registry_csv(model_path, "model")
    read_registry_csv(blocker_path, "blocker")
    manifest = write_stage_manifest(
        manifest_path,
        stage_id="model-results",
        artifact_paths=[effect_path, model_path, blocker_path],
        upstream_manifest_paths=[dataset_manifest],
        root=base,
        configuration_path=config_path,
    )
    verify_stage_manifest(manifest_path, root=base, expected_stage="model-results")

    after = _snapshot_with_dataset_inputs(
        verify_declared_inputs(config["claims"], base),
        configuration_path=config_path,
        dataset_manifest_path=dataset_manifest,
        sample_registry_path=sample_registry_path,
        root=base,
    )
    if before != after:
        raise ContractError("upstream inputs changed during model-results extraction")
    return {
        "status": "PASS",
        "stage": "model-results",
        "row_counts": {
            "effect_registry": len(bundle["effect"]),
            "model_inventory": len(bundle["model"]),
            "declared_blockers": len(bundle["blocker"]),
        },
        "artifacts": {
            "effect_registry": _relative_to_root(effect_path, base),
            "model_inventory": _relative_to_root(model_path, base),
            "declared_blockers": _relative_to_root(blocker_path, base),
            "model_results_manifest": _relative_to_root(manifest_path, base),
        },
        "artifact_sha256": {
            "effect_registry": sha256_file(effect_path),
            "model_inventory": sha256_file(model_path),
            "declared_blockers": sha256_file(blocker_path),
            "model_results_manifest": sha256_file(manifest_path),
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
    parser.add_argument("--dataset-manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = extract_model_results(
        root=args.root,
        configuration_path=args.configuration,
        output_dir=args.output_dir,
        dataset_manifest_path=args.dataset_manifest,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
