"""Build deterministic supervisor figures from frozen August registries only.

This stage does not inspect canonical analysis products, fit models, smooth
data, resample observations, or calculate scientific effects.  Numeric marks
come directly from ``effect_registry.csv``; word and onset displays use only
the categorical readings registered by the preceding PASS stages.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "august-supervisor-mpl")
)

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from PIL import Image

from .contracts import (
    CONTRACT_VERSION,
    ContractError,
    atomic_write_json,
    read_registry_csv,
    sha256_file,
    validate_records,
    validate_registry_bundle,
    verify_stage_manifest,
    write_stage_manifest,
)
from .evidence import (
    DEFAULT_CONFIGURATION,
    DEFAULT_OUTPUT_DIR,
    load_frozen_configuration,
)


DEFAULT_PLOT_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "plots"
FIGURE_WIDTH_PX = 1600
FIGURE_HEIGHT_PX = 900
FIGURE_DPI = 100

NAVY = "#17324D"
BLUE = "#356F95"
TEAL = "#2C7A78"
AMBER = "#C58B2A"
RED = "#B84A4A"
PALE_BLUE = "#E8F1F5"
PALE_TEAL = "#E7F2F0"
PALE_AMBER = "#FBF2DE"
PALE_RED = "#F8E8E7"
GREY = "#65737E"
LIGHT_GREY = "#D8E0E5"
INK = "#1F2933"


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    stem: str
    claim_ids: tuple[str, ...]
    figure_role: str
    scientific_role: str
    caption: str
    alt_text: str
    warnings: tuple[str, ...]
    width_px: int = FIGURE_WIDTH_PX
    height_px: int = FIGURE_HEIGHT_PX

    @property
    def image_name(self) -> str:
        return f"{self.stem}.png"

    @property
    def plot_data_name(self) -> str:
        return f"{self.stem}.csv"


FIGURE_SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        figure_id="FIGURE_01_FIXED_EFFORT_PREDICTABILITY",
        stem="figure_01_fixed_effort_predictability",
        claim_ids=(
            "DIRECT_PBM_MISTRAL_CONTEXTUAL",
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP",
        ),
        figure_role="MAIN",
        scientific_role=(
            "PBM discovery and non-PBM confirmation, displayed in separate panels"
        ),
        caption=(
            "Fixed-effort contextual Mistral age slopes. The 21-child PBM discovery "
            "estimate is supported; the separate 58-child primary estimate is "
            "direction-consistent but not confirmed because its clustered interval "
            "crosses zero. The child-resampling interval is shown only as sensitivity."
        ),
        alt_text=(
            "Two-panel interval plot. The PBM discovery panel shows a negative "
            "contextual-surprisal age slope whose interval remains below zero. The "
            "non-PBM panel shows the clustered primary interval crossing zero and a "
            "separately labelled child-resampling sensitivity interval below zero."
        ),
        warnings=(
            "PBM discovery and non-PBM confirmation are not pooled.",
            "The non-PBM child-resampling sensitivity does not replace the clustered primary interval.",
            "Lower scorer surprisal means greater model predictability, not greater Shannon information communicated.",
        ),
    ),
    FigureSpec(
        figure_id="FIGURE_02_UNCONDITIONAL_CONTEXTUAL_COMPONENTS",
        stem="figure_02_unconditional_contextual_components",
        claim_ids=(
            "DIRECT_PBM_MISTRAL_UNCONDITIONAL",
            "DIRECT_PBM_MISTRAL_CONTEXTUAL",
            "DIRECT_PBM_MISTRAL_CONTEXT_GAIN",
            "DIRECT_PBM_TINY_UNCONDITIONAL",
            "DIRECT_PBM_TINY_CONTEXTUAL",
            "DIRECT_PBM_TINY_CONTEXT_GAIN",
            "DIRECT_NONPBM_MISTRAL_UNCONDITIONAL",
            "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
            "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN",
        ),
        figure_role="SUPPORTING",
        scientific_role=(
            "Unconditional form, contextual form, and context-gain components in "
            "separate sample/scorer panels"
        ),
        caption=(
            "Registered fixed-effort age slopes for unconditional surprisal, contextual "
            "surprisal, and context gain. PBM Mistral discovery, same-child TinyDialogues "
            "robustness, and non-PBM Mistral confirmation are isolated on independent "
            "axes. All registered context-gain slopes are negative, contrary to the "
            "frozen positive developmental prediction."
        ),
        alt_text=(
            "Three independent interval-plot panels: PBM Mistral discovery, PBM "
            "TinyDialogues scorer robustness, and non-PBM Mistral confirmation. Each "
            "panel shows unconditional, contextual, and context-gain age slopes. The "
            "three context-gain marks are highlighted as contrary negative directions."
        ),
        warnings=(
            "Each scorer panel has its own horizontal scale; coefficient magnitudes are not compared across tokenizers.",
            "TinyDialogues reuses the same 21 PBM children and is scorer robustness, not independent confirmation.",
            "Negative context gain is contrary to the registered positive direction and is not relabelled as confirmation.",
        ),
    ),
    FigureSpec(
        figure_id="FIGURE_03_WORD_CROSS_SCORER_SIGNS",
        stem="figure_03_word_cross_scorer_signs",
        claim_ids=(
            "WORD_CROSS_SCORER_PREDICTABILITY",
            "WORD_LONGER_TYPES_CONTEXT_SUPPORT",
            "WORD_CONTEXT_GAIN_SCORER_DEPENDENT",
        ),
        figure_role="MAIN",
        scientific_role=(
            "PBM word-level same-occurrence scorer robustness, categorical only"
        ),
        caption=(
            "Categorical word-level readings on the exact shared PBM occurrence set. "
            "All three separately fit scorers support negative same-word k0 and k3 age "
            "directions and positive context support for longer word types. Development "
            "of word-level context gain has mixed signs and remains scorer-dependent."
        ),
        alt_text=(
            "A categorical matrix with separate columns for Mistral, Qwen3-14B, and "
            "TinyDialogues. Every scorer column shows negative, interval-supported "
            "same-word predictability directions and positive, interval-supported "
            "longer-word context support. A separate band states that context-gain "
            "development has mixed signs across scorers."
        ),
        warnings=(
            "No raw bits or coefficients are shown or pooled across tokenizers.",
            "These are three scorer fits on the same 21 PBM children, not confirmation in the remaining 58 children.",
            "The mixed context-gain reading is retained without selecting a preferred scorer.",
        ),
    ),
    FigureSpec(
        figure_id="FIGURE_04_ROUTE2_QUALIFICATION",
        stem="figure_04_route2_qualification",
        claim_ids=(
            "ROUTE2_RELATIVE_EFFORT_AGE",
            "ROUTE2_AGE_ENTROPY_INTERACTION",
        ),
        figure_role="MAIN",
        scientific_role="PBM response-space exploratory qualification",
        caption=(
            "Registered response-space relative-effort associations on 976 PBM "
            "child-session aggregates. Relative effort increases with age, while the "
            "age-by-exact-string-entropy interaction is negative, opposite the simple "
            "lengthening prediction. Independent axes preserve the two different units."
        ),
        alt_text=(
            "Two independent interval panels. The left panel shows a positive age "
            "association for observed word effort relative to a generated reference. "
            "The right panel shows a negative age-by-response-entropy interaction, "
            "labelled contrary to the registered positive prediction."
        ),
        warnings=(
            "Exact-string entropy is not semantic response uncertainty.",
            "The generated reference may mediate contextual demand and couples the generator/scorer namespace.",
            "The contrary interaction is a result or measurement diagnostic, not confirmation of the original prediction.",
        ),
    ),
    FigureSpec(
        figure_id="FIGURE_05_SUSTAINED_ONSET_STATUS",
        stem="figure_05_sustained_onset_status",
        claim_ids=("ONSET_PBM_SUSTAINED", "ONSET_NONPBM_SUSTAINED"),
        figure_role="MAIN",
        scientific_role=(
            "Frozen sustained-onset status, with discovery and confirmation separated"
        ),
        caption=(
            "Categorical outcomes of the frozen simultaneous sustained-onset rule. "
            "Sustained onset is not established in either the 21-child PBM discovery "
            "sample or the separate 58-child non-PBM confirmation sample. No pointwise "
            "age-bin contrast is substituted for the registered rule."
        ),
        alt_text=(
            "Two separate status cards, one for PBM discovery and one for non-PBM "
            "confirmation. Both cards read not established under the frozen "
            "simultaneous sustained-onset rule; no numeric onset age is displayed."
        ),
        warnings=(
            "No numeric onset age is registered for either sample.",
            "The earlier nominal 24-29-month PBM contrast is not promoted as onset.",
            "Alternative morpheme, syllable, and phoneme effort onset analyses remain pending.",
        ),
    ),
    FigureSpec(
        figure_id="FIGURE_06_HALL_SNAPSHOT",
        stem="figure_06_hall_snapshot",
        claim_ids=(
            "HALL_RACE_CLASS_INTERACTION",
            "HALL_ADULT_CONTEXT_INTERACTION",
            "HALL_LOCKED_DOMAIN_SHIFT",
        ),
        figure_role="SUPPORTING",
        scientific_role=(
            "Separate Hall historical cross-sectional and domain-sensitivity snapshot"
        ),
        caption=(
            "Hall-only descriptive snapshot with independent axes for the registered "
            "race-by-class k0 interaction, adult-adjacent context-support interaction, "
            "and guarded Hall-minus-current domain shift. These scorer-indexed "
            "contrasts are historical, non-causal, and separate from development."
        ),
        alt_text=(
            "Three Hall-only interval panels with different labelled horizontal scales. "
            "The historical race-by-class interaction is negative, the adult-adjacent "
            "context-support interval crosses zero, and the guarded Hall-minus-current "
            "domain-shift contrast is positive. Each panel is marked descriptive."
        ),
        warnings=(
            "Hall is not a 14th longitudinal corpus or an 80th child.",
            "Race/class contrasts are non-causal and non-deficit; dialect, era, geography, transcription, setting, and model representation remain plausible sources.",
            "The guarded Hall-minus-current contrast is domain sensitivity, not a causal cohort comparison.",
        ),
    ),
)


EXPECTED_OUTPUT_NAMES: tuple[str, ...] = tuple(
    [name for spec in FIGURE_SPECS for name in (spec.plot_data_name, spec.image_name)]
    + ["figure_manifest.csv", "plot_manifest.json"]
)

PLOT_DATA_COLUMNS = (
    "schema_version",
    "figure_id",
    "display_order",
    "panel_id",
    "panel_title",
    "mark_label",
    "claim_id",
    "effect_id",
    "sample_id",
    "sample_scope",
    "sample_role",
    "scorer",
    "value_kind",
    "estimate",
    "ci_level",
    "ci_low",
    "ci_high",
    "unit",
    "evidence_status",
    "figure_eligibility",
    "categorical_value",
    "source_artifact",
    "source_sha256",
    "audit_marker",
    "audit_marker_sha256",
)

FIGURE_MANIFEST_COLUMNS = (
    "schema_version",
    "figure_id",
    "claim_ids",
    "effect_ids",
    "eligibility",
    "scientific_role",
    "figure_role",
    "plot_data_path",
    "plot_data_sha256",
    "image_path",
    "image_sha256",
    "caption",
    "alt_text",
    "width_px",
    "height_px",
    "warnings",
    "upstream_provenance",
)


def _rooted(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()


def _relative_to_root(path: Path | str, root: Path) -> str:
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ContractError(f"plot-stage path is outside repository root: {path}") from error


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _number_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is int:
        return str(value)
    return format(value, ".17g")


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write_rows(
    path: Path, columns: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> None:
    materialized = [dict(row) for row in rows]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(columns),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in materialized:
        if set(row) != set(columns):
            raise ContractError(
                f"CSV row schema mismatch for {path.name}: "
                f"missing={sorted(set(columns) - set(row))}, "
                f"extra={sorted(set(row) - set(columns))}"
            )
        writer.writerow(row)
    _atomic_write_bytes(path, stream.getvalue().encode("utf-8"))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ContractError(f"invalid CSV header: {path}")
        return list(reader)


def _claims_by_id(config: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {claim["claim_id"]: claim for claim in config["claims"]}


def validate_plot_evidence(
    *,
    config: Mapping[str, Any],
    effects: Iterable[Mapping[str, Any]],
    models: Iterable[Mapping[str, Any]],
    samples: Iterable[Mapping[str, Any]],
    synthesis: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate complete frozen coverage and every figure source claim."""

    effect_rows = validate_records("effect", effects)
    model_rows = validate_records("model", models)
    sample_rows = validate_records("sample", samples)
    synthesis_rows = validate_records("synthesis", synthesis)
    claims = _claims_by_id(config)
    configured_claims = set(claims)

    expected_effect_claims = {
        claim_id
        for claim_id, claim in claims.items()
        if claim["evidence_status"] != "PENDING"
    }
    observed_effect_claims = {row["claim_id"] for row in effect_rows}
    if observed_effect_claims != expected_effect_claims:
        raise ContractError(
            "effect claim coverage mismatch; "
            f"missing={sorted(expected_effect_claims - observed_effect_claims)}, "
            f"extra={sorted(observed_effect_claims - expected_effect_claims)}"
        )
    observed_sample_claims = {
        row["sample_id"].removeprefix("SAMPLE_") for row in sample_rows
    }
    if observed_sample_claims != configured_claims:
        raise ContractError(
            "sample claim coverage mismatch; "
            f"missing={sorted(configured_claims - observed_sample_claims)}, "
            f"extra={sorted(observed_sample_claims - configured_claims)}"
        )
    observed_synthesis_claims = {row["claim_id"] for row in synthesis_rows}
    if observed_synthesis_claims != configured_claims:
        raise ContractError(
            "synthesis claim coverage mismatch; "
            f"missing={sorted(configured_claims - observed_synthesis_claims)}, "
            f"extra={sorted(observed_synthesis_claims - configured_claims)}"
        )

    effects_by_claim = {row["claim_id"]: row for row in effect_rows}
    samples_by_id = {row["sample_id"]: row for row in sample_rows}
    synthesis_by_claim = {row["claim_id"]: row for row in synthesis_rows}
    models_by_claim: dict[str, list[dict[str, Any]]] = {}
    for row in model_rows:
        if row["claim_id"] not in claims:
            raise ContractError(f"model has extra claim {row['claim_id']}")
        models_by_claim.setdefault(row["claim_id"], []).append(row)
    expected_model_claims = {
        claim_id
        for claim_id, claim in claims.items()
        if claim["evidence_status"] != "PENDING" and claim["claim_role"] != "EXCLUDED"
    }
    if set(models_by_claim) != expected_model_claims:
        raise ContractError(
            "model claim coverage mismatch; "
            f"missing={sorted(expected_model_claims - set(models_by_claim))}, "
            f"extra={sorted(set(models_by_claim) - expected_model_claims)}"
        )

    for claim_id, claim in claims.items():
        sample_id = f"SAMPLE_{claim_id}"
        sample = samples_by_id[sample_id]
        if sample["source_artifact"] != claim["source"]["canonical_artifact"]:
            raise ContractError(f"{claim_id} sample source drift")
        synthesized = synthesis_by_claim[claim_id]
        if synthesized["destination_section"] != claim["destination_section"]:
            raise ContractError(f"{claim_id} synthesis destination drift")
        if claim["evidence_status"] == "PENDING":
            if synthesized["classification"] != "PENDING" or synthesized["evidence_kind"] != "BLOCKER":
                raise ContractError(f"{claim_id} pending synthesis drift")
            continue

        effect = effects_by_claim[claim_id]
        comparisons = {
            "claim_role": claim["claim_role"],
            "sample_id": sample_id,
            "source_artifact": claim["source"]["canonical_artifact"],
            "source_sha256": claim["source"]["source_sha256"],
            "figure_eligibility": claim["figure_eligibility"],
        }
        for field, expected in comparisons.items():
            if effect[field] != expected:
                label = "figure eligibility drift" if field == "figure_eligibility" else "claim drift"
                raise ContractError(f"{claim_id} {label} in effect.{field}")
        if effect["evidence_status"] != claim["evidence_status"]:
            raise ContractError(f"{claim_id} classification drift")
        result = claim["numerical_result"]
        expected_numeric = {
            "estimate": None if result is None else result["estimate"],
            "ci_level": None if result is None or result["interval"] is None else result["interval"]["level"],
            "ci_low": None if result is None or result["interval"] is None else result["interval"]["low"],
            "ci_high": None if result is None or result["interval"] is None else result["interval"]["high"],
        }
        for field, expected in expected_numeric.items():
            if effect[field] != expected:
                raise ContractError(f"{claim_id} registered numeric drift in effect.{field}")
        if synthesized["classification"] != effect["evidence_status"]:
            raise ContractError(f"{claim_id} synthesis classification drift")
        if synthesized["evidence_kind"] != "EFFECT" or synthesized["evidence_id"] != effect["effect_id"]:
            raise ContractError(f"{claim_id} synthesis evidence drift")

    selected_claims = {
        claim_id for spec in FIGURE_SPECS for claim_id in spec.claim_ids
    }
    missing_selected = selected_claims - set(effects_by_claim)
    if missing_selected:
        raise ContractError(f"missing selected figure claims: {sorted(missing_selected)}")
    for spec in FIGURE_SPECS:
        if len(spec.claim_ids) != len(set(spec.claim_ids)):
            raise ContractError(f"{spec.figure_id} has duplicated source claims")
        if not spec.caption.strip() or not spec.alt_text.strip() or not spec.warnings:
            raise ContractError(f"{spec.figure_id} is missing accessibility metadata")
        for claim_id in spec.claim_ids:
            effect = effects_by_claim[claim_id]
            if effect["figure_eligibility"] == "NONE" or effect["claim_role"] in {"EXCLUDED", "PENDING"}:
                raise ContractError(f"{spec.figure_id} uses ineligible claim {claim_id}")

    word_scorers = {
        row["scorer"]
        for claim_id in (
            "WORD_CROSS_SCORER_PREDICTABILITY",
            "WORD_LONGER_TYPES_CONTEXT_SUPPORT",
            "WORD_CONTEXT_GAIN_SCORER_DEPENDENT",
        )
        for row in models_by_claim[claim_id]
    }
    expected_word_scorers = {
        "MISTRAL_7B_V03",
        "QWEN3_14B",
        "TINYDIALOGUES_SMOLLM2_135M",
    }
    if word_scorers != expected_word_scorers:
        raise ContractError(
            f"word scorer coverage drift: expected={sorted(expected_word_scorers)}, observed={sorted(word_scorers)}"
        )

    return {
        "effects": effects_by_claim,
        "models": models_by_claim,
        "samples": samples_by_id,
        "synthesis": synthesis_by_claim,
        "effect_rows": effect_rows,
        "model_rows": model_rows,
        "sample_rows": sample_rows,
    }


def _base_plot_row(
    *,
    spec: FigureSpec,
    display_order: int,
    panel_id: str,
    panel_title: str,
    mark_label: str,
    claim_id: str,
    evidence: Mapping[str, Any],
    scorer: str,
    value_kind: str,
    categorical_value: str = "",
) -> dict[str, str]:
    effect = evidence["effects"][claim_id]
    sample = evidence["samples"][effect["sample_id"]]
    return {
        "schema_version": CONTRACT_VERSION,
        "figure_id": spec.figure_id,
        "display_order": str(display_order),
        "panel_id": panel_id,
        "panel_title": panel_title,
        "mark_label": mark_label,
        "claim_id": claim_id,
        "effect_id": effect["effect_id"],
        "sample_id": effect["sample_id"],
        "sample_scope": sample["scope"],
        "sample_role": sample["sample_role"],
        "scorer": scorer,
        "value_kind": value_kind,
        "estimate": _number_text(effect["estimate"]) if value_kind == "NUMERIC" else "",
        "ci_level": _number_text(effect["ci_level"]) if value_kind == "NUMERIC" else "",
        "ci_low": _number_text(effect["ci_low"]) if value_kind == "NUMERIC" else "",
        "ci_high": _number_text(effect["ci_high"]) if value_kind == "NUMERIC" else "",
        "unit": effect["unit"],
        "evidence_status": effect["evidence_status"],
        "figure_eligibility": effect["figure_eligibility"],
        "categorical_value": categorical_value,
        "source_artifact": effect["source_artifact"],
        "source_sha256": effect["source_sha256"],
        "audit_marker": effect["audit_marker"] or "",
        "audit_marker_sha256": effect["audit_marker_sha256"] or "",
    }


def _single_scorer(claim_id: str, evidence: Mapping[str, Any]) -> str:
    models = evidence["models"][claim_id]
    if len(models) != 1:
        raise ContractError(f"{claim_id} does not resolve to exactly one scorer")
    return models[0]["scorer"]


def _build_plot_rows(spec: FigureSpec, evidence: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def numeric(
        claim_id: str,
        order: int,
        panel_id: str,
        panel_title: str,
        mark_label: str,
    ) -> None:
        rows.append(
            _base_plot_row(
                spec=spec,
                display_order=order,
                panel_id=panel_id,
                panel_title=panel_title,
                mark_label=mark_label,
                claim_id=claim_id,
                evidence=evidence,
                scorer=_single_scorer(claim_id, evidence),
                value_kind="NUMERIC",
            )
        )

    if spec.figure_id == "FIGURE_01_FIXED_EFFORT_PREDICTABILITY":
        numeric(spec.claim_ids[0], 0, "PBM_DISCOVERY", "PBM discovery (21 children)", "Clustered primary")
        numeric(spec.claim_ids[1], 1, "NON_PBM_CONFIRMATION", "Non-PBM confirmation (58 children)", "Clustered primary")
        numeric(spec.claim_ids[2], 2, "NON_PBM_CONFIRMATION", "Non-PBM confirmation (58 children)", "Child-resampling sensitivity")
    elif spec.figure_id == "FIGURE_02_UNCONDITIONAL_CONTEXTUAL_COMPONENTS":
        panels = (
            (
                "PBM_MISTRAL",
                "PBM discovery\nMistral",
                (
                    ("DIRECT_PBM_MISTRAL_UNCONDITIONAL", "Unconditional k0"),
                    ("DIRECT_PBM_MISTRAL_CONTEXTUAL", "Contextual k3"),
                    ("DIRECT_PBM_MISTRAL_CONTEXT_GAIN", "Context gain k0-k3"),
                ),
            ),
            (
                "PBM_TINY",
                "PBM scorer robustness\nTinyDialogues",
                (
                    ("DIRECT_PBM_TINY_UNCONDITIONAL", "Unconditional k0"),
                    ("DIRECT_PBM_TINY_CONTEXTUAL", "Contextual k3"),
                    ("DIRECT_PBM_TINY_CONTEXT_GAIN", "Context gain k0-k3"),
                ),
            ),
            (
                "NON_PBM_MISTRAL",
                "Non-PBM confirmation\nMistral",
                (
                    ("DIRECT_NONPBM_MISTRAL_UNCONDITIONAL", "Unconditional k0"),
                    ("DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY", "Contextual k3"),
                    ("DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN", "Context gain k0-k3"),
                ),
            ),
        )
        order = 0
        for panel_id, title, claims in panels:
            for claim_id, label in claims:
                numeric(claim_id, order, panel_id, title, label)
                order += 1
    elif spec.figure_id == "FIGURE_03_WORD_CROSS_SCORER_SIGNS":
        scorer_labels = (
            ("MISTRAL_7B_V03", "Mistral"),
            ("QWEN3_14B", "Qwen3-14B"),
            ("TINYDIALOGUES_SMOLLM2_135M", "TinyDialogues"),
        )
        order = 0
        for claim_id, panel_id, panel_title, category in (
            (
                "WORD_CROSS_SCORER_PREDICTABILITY",
                "SAME_WORD_PREDICTABILITY",
                "Same-word k0 and k3 age directions",
                "negative with interval support",
            ),
            (
                "WORD_LONGER_TYPES_CONTEXT_SUPPORT",
                "LONGER_WORD_CONTEXT_SUPPORT",
                "Longer word types and context support",
                "positive with interval support",
            ),
        ):
            available = {row["scorer"] for row in evidence["models"][claim_id]}
            for scorer, label in scorer_labels:
                if scorer not in available:
                    raise ContractError(f"{claim_id} is missing scorer {scorer}")
                rows.append(
                    _base_plot_row(
                        spec=spec,
                        display_order=order,
                        panel_id=panel_id,
                        panel_title=panel_title,
                        mark_label=label,
                        claim_id=claim_id,
                        evidence=evidence,
                        scorer=scorer,
                        value_kind="CATEGORICAL",
                        categorical_value=category,
                    )
                )
                order += 1
        rows.append(
            _base_plot_row(
                spec=spec,
                display_order=order,
                panel_id="CONTEXT_GAIN_DEVELOPMENT",
                panel_title="Word-level context-gain development",
                mark_label="Across separately fit scorers",
                claim_id="WORD_CONTEXT_GAIN_SCORER_DEPENDENT",
                evidence=evidence,
                scorer="MULTI_SCORER",
                value_kind="CATEGORICAL",
                categorical_value="mixed signs",
            )
        )
    elif spec.figure_id == "FIGURE_04_ROUTE2_QUALIFICATION":
        numeric(spec.claim_ids[0], 0, "RELATIVE_EFFORT_AGE", "Relative effort and age", "Age association")
        numeric(spec.claim_ids[1], 1, "AGE_ENTROPY_INTERACTION", "Age × exact-string entropy", "Registered interaction")
    elif spec.figure_id == "FIGURE_05_SUSTAINED_ONSET_STATUS":
        for order, (claim_id, panel_id, title) in enumerate(
            (
                ("ONSET_PBM_SUSTAINED", "PBM_DISCOVERY", "PBM discovery (21 children)"),
                ("ONSET_NONPBM_SUSTAINED", "NON_PBM_CONFIRMATION", "Non-PBM confirmation (58 children)"),
            )
        ):
            rows.append(
                _base_plot_row(
                    spec=spec,
                    display_order=order,
                    panel_id=panel_id,
                    panel_title=title,
                    mark_label="Frozen simultaneous sustained rule",
                    claim_id=claim_id,
                    evidence=evidence,
                    scorer=_single_scorer(claim_id, evidence),
                    value_kind="CATEGORICAL",
                    categorical_value="not established",
                )
            )
    elif spec.figure_id == "FIGURE_06_HALL_SNAPSHOT":
        numeric(spec.claim_ids[0], 0, "RACE_CLASS", "Within-Hall race × class", "k0 interaction")
        numeric(spec.claim_ids[1], 1, "ADULT_CONTEXT", "Adult-adjacent context support", "k0-k3 interaction")
        numeric(spec.claim_ids[2], 2, "DOMAIN_SHIFT", "Hall minus current snapshot", "Guarded k0 contrast")
    else:
        raise ContractError(f"no registered plot-data rule for {spec.figure_id}")

    if {row["claim_id"] for row in rows} != set(spec.claim_ids):
        raise ContractError(f"{spec.figure_id} plot-data claim coverage drift")
    return sorted(rows, key=lambda row: int(row["display_order"]))


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "axes.titlesize": 16,
            "axes.labelsize": 12,
            "axes.edgecolor": LIGHT_GREY,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _new_figure(spec: FigureSpec, *, columns: int = 1) -> tuple[Figure, Any]:
    _style()
    figure, axes = plt.subplots(
        1,
        columns,
        figsize=(spec.width_px / FIGURE_DPI, spec.height_px / FIGURE_DPI),
        dpi=FIGURE_DPI,
        squeeze=False,
    )
    return figure, axes[0]


def _format_axis(axis: Axes, *, xlabel: str, xlim: tuple[float, float]) -> None:
    axis.axvline(0, color=GREY, linewidth=1.2, linestyle="--", zorder=0)
    axis.grid(axis="x", color=LIGHT_GREY, linewidth=0.8, alpha=0.8)
    axis.set_xlim(*xlim)
    axis.set_xlabel(xlabel)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0)


def _interval_mark(
    axis: Axes,
    row: Mapping[str, str],
    y: float,
    *,
    color: str,
    marker: str = "o",
) -> None:
    estimate = float(row["estimate"])
    low = float(row["ci_low"])
    high = float(row["ci_high"])
    axis.errorbar(
        estimate,
        y,
        xerr=[[estimate - low], [high - estimate]],
        fmt=marker,
        markersize=9,
        color=color,
        ecolor=color,
        elinewidth=3,
        capsize=6,
        capthick=2,
        zorder=3,
    )


def _render_fixed_effort(spec: FigureSpec, rows: list[dict[str, str]]) -> Figure:
    figure, axes = _new_figure(spec, columns=2)
    figure.suptitle(
        "Fixed-effort contextual predictability: discovery and confirmation",
        fontsize=23,
        fontweight="bold",
        x=0.04,
        ha="left",
        y=0.96,
    )
    discovery = [row for row in rows if row["panel_id"] == "PBM_DISCOVERY"]
    confirmation = [row for row in rows if row["panel_id"] == "NON_PBM_CONFIRMATION"]
    panels = (
        (axes[0], discovery, (-0.21, 0.03), PALE_BLUE),
        (axes[1], confirmation, (-0.19, 0.04), PALE_AMBER),
    )
    for axis, panel_rows, xlim, face in panels:
        axis.set_facecolor(face)
        axis.set_title(panel_rows[0]["panel_title"], loc="left", fontweight="bold", pad=16)
        ys = list(reversed(range(len(panel_rows))))
        for y, row in zip(ys, panel_rows):
            color = NAVY if row["mark_label"] == "Clustered primary" else AMBER
            marker = "o" if row["mark_label"] == "Clustered primary" else "D"
            _interval_mark(axis, row, y, color=color, marker=marker)
            axis.text(
                xlim[1] - 0.006,
                y,
                f"{float(row['estimate']):+.3f}",
                ha="right",
                va="center",
                color=color,
                fontweight="bold",
            )
        axis.set_yticks(ys, [row["mark_label"] for row in panel_rows])
        axis.set_ylim(-0.8, max(ys) + 0.8)
        _format_axis(axis, xlabel="Registered age slope (Mistral bits/month)", xlim=xlim)
    axes[0].text(
        0.02,
        -0.28,
        "Supported discovery association",
        transform=axes[0].transAxes,
        color=NAVY,
        fontweight="bold",
    )
    axes[1].text(
        0.02,
        -0.28,
        "Primary interval crosses zero: confirmation not achieved",
        transform=axes[1].transAxes,
        color=RED,
        fontweight="bold",
    )
    figure.text(
        0.04,
        0.035,
        "Negative = greater scorer predictability with age at fixed observed word effort. "
        "Sensitivity evidence is not a replacement confirmation criterion.",
        fontsize=11,
        color=GREY,
    )
    figure.subplots_adjust(left=0.16, right=0.97, top=0.83, bottom=0.23, wspace=0.32)
    return figure


def _render_components(spec: FigureSpec, rows: list[dict[str, str]]) -> Figure:
    figure, axes = _new_figure(spec, columns=3)
    figure.suptitle(
        "Unconditional form, contextual form, and context gain",
        fontsize=23,
        fontweight="bold",
        x=0.04,
        ha="left",
        y=0.96,
    )
    panel_contract = (
        ("PBM_MISTRAL", axes[0], (-0.24, 0.025), PALE_BLUE),
        ("PBM_TINY", axes[1], (-0.38, 0.035), PALE_TEAL),
        ("NON_PBM_MISTRAL", axes[2], (-0.17, 0.025), PALE_AMBER),
    )
    for panel_id, axis, xlim, face in panel_contract:
        panel_rows = [row for row in rows if row["panel_id"] == panel_id]
        axis.set_facecolor(face)
        axis.set_title(panel_rows[0]["panel_title"], loc="left", fontweight="bold", pad=14)
        ys = [2, 1, 0]
        for y, row in zip(ys, panel_rows):
            is_gain = "Context gain" in row["mark_label"]
            _interval_mark(axis, row, y, color=RED if is_gain else NAVY)
            axis.text(
                xlim[1] - (xlim[1] - xlim[0]) * 0.025,
                y,
                f"{float(row['estimate']):+.3f}",
                ha="right",
                va="center",
                color=RED if is_gain else NAVY,
                fontweight="bold",
            )
        axis.set_yticks(ys, [row["mark_label"] for row in panel_rows])
        axis.set_ylim(-0.75, 2.75)
        _format_axis(axis, xlabel="Registered slope (scorer-native bits/month)", xlim=xlim)
        axis.text(
            0.5,
            -0.25,
            "Independent scale; no magnitude pooling",
            transform=axis.transAxes,
            fontsize=9.5,
            color=GREY,
            ha="center",
        )
    figure.text(
        0.04,
        0.035,
        "Red marks: context-gain direction is negative and contrary to the frozen positive prediction.",
        fontsize=11,
        color=RED,
        fontweight="bold",
    )
    figure.subplots_adjust(left=0.12, right=0.98, top=0.82, bottom=0.22, wspace=0.5)
    return figure


def _render_word_signs(spec: FigureSpec, rows: list[dict[str, str]]) -> Figure:
    _style()
    figure = plt.figure(
        figsize=(spec.width_px / FIGURE_DPI, spec.height_px / FIGURE_DPI),
        dpi=FIGURE_DPI,
        facecolor="white",
    )
    axis = figure.add_axes([0.04, 0.08, 0.92, 0.82])
    axis.set_axis_off()
    axis.text(
        0,
        1.04,
        "Word-level cross-scorer evidence — signs, not magnitudes",
        fontsize=23,
        fontweight="bold",
        va="bottom",
    )
    scorer_order = (
        ("MISTRAL_7B_V03", "Mistral"),
        ("QWEN3_14B", "Qwen3-14B"),
        ("TINYDIALOGUES_SMOLLM2_135M", "TinyDialogues"),
    )
    x_positions = (0.43, 0.66, 0.89)
    for x, (_, label) in zip(x_positions, scorer_order):
        axis.text(x, 0.91, label, ha="center", va="center", fontsize=15, fontweight="bold")
    row_contract = (
        (
            "SAME_WORD_PREDICTABILITY",
            0.68,
            "Same-word k0 and k3\nage directions",
            "NEGATIVE\ninterval-supported",
            PALE_BLUE,
            NAVY,
        ),
        (
            "LONGER_WORD_CONTEXT_SUPPORT",
            0.43,
            "Longer word types and\ncontext support",
            "POSITIVE\ninterval-supported",
            PALE_TEAL,
            TEAL,
        ),
    )
    for panel_id, y, row_label, cell_text, face, color in row_contract:
        axis.text(0.02, y, row_label, va="center", fontsize=15, fontweight="bold")
        panel_rows = {row["scorer"]: row for row in rows if row["panel_id"] == panel_id}
        for x, (scorer, _) in zip(x_positions, scorer_order):
            if scorer not in panel_rows:
                raise ContractError(f"{spec.figure_id} missing categorical scorer {scorer}")
            axis.text(
                x,
                y,
                cell_text,
                ha="center",
                va="center",
                fontsize=13,
                fontweight="bold",
                color=color,
                bbox={"boxstyle": "round,pad=0.75", "facecolor": face, "edgecolor": color, "linewidth": 1.5},
            )
    axis.text(
        0.02,
        0.16,
        "Word-level context-gain development",
        va="center",
        fontsize=15,
        fontweight="bold",
    )
    axis.text(
        0.66,
        0.16,
        "MIXED SIGNS ACROSS SCORERS\nOnly one scorer has clustered + child-resampling interval support",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=RED,
        bbox={"boxstyle": "round,pad=0.9", "facecolor": PALE_RED, "edgecolor": RED, "linewidth": 1.5},
    )
    axis.text(
        0,
        -0.02,
        "Exact shared PBM occurrence set; three separate scorer fits. Raw bits and coefficient magnitudes are not pooled.",
        fontsize=11,
        color=GREY,
    )
    return figure


def _render_route2(spec: FigureSpec, rows: list[dict[str, str]]) -> Figure:
    figure, axes = _new_figure(spec, columns=2)
    figure.suptitle(
        "Response-space effort adaptation: registered result and qualification",
        fontsize=23,
        fontweight="bold",
        x=0.04,
        ha="left",
        y=0.96,
    )
    contracts = (
        (axes[0], rows[0], (0.06, 0.115), TEAL, PALE_TEAL, "Positive age association"),
        (axes[1], rows[1], (-0.044, 0.006), RED, PALE_RED, "Opposite the registered positive prediction"),
    )
    for axis, row, xlim, color, face, reading in contracts:
        axis.set_facecolor(face)
        axis.set_title(row["panel_title"], loc="left", fontweight="bold", pad=16)
        _interval_mark(axis, row, 0, color=color)
        axis.set_yticks([0], [row["mark_label"]])
        axis.set_ylim(-0.85, 0.85)
        _format_axis(axis, xlabel=row["unit"], xlim=xlim)
        axis.text(
            0.02,
            -0.28,
            reading,
            transform=axis.transAxes,
            color=color,
            fontweight="bold",
        )
        axis.text(
            0.98,
            0.86,
            f"{float(row['estimate']):+.3f}  [95%: {float(row['ci_low']):+.3f}, {float(row['ci_high']):+.3f}]",
            transform=axis.transAxes,
            ha="right",
            color=color,
            fontweight="bold",
        )
    figure.text(
        0.04,
        0.035,
        "PBM response-space exploratory evidence. Exact-string entropy is measurement-limited and is not semantic uncertainty.",
        fontsize=11,
        color=GREY,
    )
    figure.subplots_adjust(left=0.15, right=0.97, top=0.82, bottom=0.23, wspace=0.35)
    return figure


def _render_onset(spec: FigureSpec, rows: list[dict[str, str]]) -> Figure:
    figure, axes = _new_figure(spec, columns=2)
    figure.suptitle(
        "Developmental onset under the frozen sustained rule",
        fontsize=23,
        fontweight="bold",
        x=0.04,
        ha="left",
        y=0.96,
    )
    for axis, row in zip(axes, rows):
        axis.set_axis_off()
        axis.add_patch(
            plt.Rectangle(
                (0.03, 0.08),
                0.94,
                0.78,
                transform=axis.transAxes,
                facecolor=PALE_AMBER,
                edgecolor=AMBER,
                linewidth=2,
            )
        )
        axis.text(0.08, 0.76, row["panel_title"], transform=axis.transAxes, fontsize=17, fontweight="bold")
        axis.text(
            0.5,
            0.49,
            "NOT ESTABLISHED",
            transform=axis.transAxes,
            ha="center",
            va="center",
            fontsize=25,
            color=RED,
            fontweight="bold",
        )
        axis.text(
            0.5,
            0.31,
            "Frozen simultaneous\nsustained-onset rule",
            transform=axis.transAxes,
            ha="center",
            va="center",
            fontsize=14,
            color=INK,
        )
        axis.text(
            0.08,
            0.13,
            "No numeric onset age registered",
            transform=axis.transAxes,
            fontsize=11,
            color=GREY,
        )
    figure.text(
        0.04,
        0.035,
        "Discovery and confirmation remain separate. Nominal pointwise age-bin contrasts do not replace the simultaneous rule.",
        fontsize=11,
        color=GREY,
    )
    figure.subplots_adjust(left=0.04, right=0.96, top=0.84, bottom=0.12, wspace=0.08)
    return figure


def _render_hall(spec: FigureSpec, rows: list[dict[str, str]]) -> Figure:
    figure, axes = _new_figure(spec, columns=3)
    figure.suptitle(
        "Hall historical snapshot — descriptive and separate",
        fontsize=23,
        fontweight="bold",
        x=0.04,
        ha="left",
        y=0.96,
    )
    contracts = (
        (axes[0], rows[0], (-6.4, 0.6)),
        (axes[1], rows[1], (-1.4, 1.0)),
        (axes[2], rows[2], (-0.4, 4.6)),
    )
    for axis, row, xlim in contracts:
        axis.set_facecolor(PALE_AMBER)
        axis.set_title(row["panel_title"], loc="left", fontweight="bold", pad=14)
        _interval_mark(axis, row, 0, color=AMBER)
        axis.set_yticks([0], [row["mark_label"]])
        axis.set_ylim(-0.85, 0.85)
        _format_axis(axis, xlabel=row["unit"], xlim=xlim)
        axis.text(
            0.98,
            0.86,
            f"{float(row['estimate']):+.3f}\n[{float(row['ci_low']):+.3f}, {float(row['ci_high']):+.3f}]",
            transform=axis.transAxes,
            ha="right",
            va="top",
            color=NAVY,
            fontweight="bold",
        )
        axis.text(
            0.02,
            -0.25,
            "Independent descriptive scale",
            transform=axis.transAxes,
            fontsize=10,
            color=GREY,
        )
    figure.text(
        0.04,
        0.035,
        "Historical, non-causal, non-deficit, and scorer-indexed. Not part of the longitudinal discovery/confirmation analysis.",
        fontsize=11,
        color=RED,
        fontweight="bold",
    )
    figure.subplots_adjust(left=0.11, right=0.98, top=0.82, bottom=0.22, wspace=0.48)
    return figure


def _render_figure(spec: FigureSpec, rows: list[dict[str, str]]) -> Figure:
    renderers = {
        "FIGURE_01_FIXED_EFFORT_PREDICTABILITY": _render_fixed_effort,
        "FIGURE_02_UNCONDITIONAL_CONTEXTUAL_COMPONENTS": _render_components,
        "FIGURE_03_WORD_CROSS_SCORER_SIGNS": _render_word_signs,
        "FIGURE_04_ROUTE2_QUALIFICATION": _render_route2,
        "FIGURE_05_SUSTAINED_ONSET_STATUS": _render_onset,
        "FIGURE_06_HALL_SNAPSHOT": _render_hall,
    }
    try:
        renderer = renderers[spec.figure_id]
    except KeyError as error:
        raise ContractError(f"missing renderer for {spec.figure_id}") from error
    return renderer(spec, rows)


def _save_figure(path: Path, figure: Figure, spec: FigureSpec) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.", suffix=".png", dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        figure.savefig(
            temporary,
            format="png",
            dpi=FIGURE_DPI,
            facecolor="white",
            edgecolor="white",
            metadata={"Software": "August supervisor report frozen plot stage v1"},
        )
        with Image.open(temporary) as image:
            if image.size != (spec.width_px, spec.height_px):
                raise ContractError(
                    f"{spec.figure_id} dimensions changed: {image.size}"
                )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
        plt.close(figure)


def _input_snapshot(paths: Iterable[Path], root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in paths:
        if not path.is_file():
            raise ContractError(f"missing plot input: {_relative_to_root(path, root)}")
        snapshot[_relative_to_root(path, root)] = sha256_file(path)
    return dict(sorted(snapshot.items()))


def _validate_page_registry(
    config: Mapping[str, Any], pages: Iterable[Mapping[str, Any]]
) -> None:
    rows = validate_records("page", pages)
    expected_paths = set(config["page_contract"]["outputs"]) | set(
        config["page_contract"]["required_links"].values()
    )
    observed_paths = {row["output_path"] for row in rows}
    if observed_paths != expected_paths:
        raise ContractError(
            "page registry coverage mismatch; "
            f"missing={sorted(expected_paths - observed_paths)}, "
            f"extra={sorted(observed_paths - expected_paths)}"
        )


def _upstream_provenance(
    *,
    spec: FigureSpec,
    evidence: Mapping[str, Any],
    configuration_path: Path,
    synthesis_manifest_path: Path,
    synthesis_manifest: Mapping[str, Any],
    model_manifest_path: Path,
    model_manifest: Mapping[str, Any],
    root: Path,
) -> dict[str, Any]:
    sources: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for claim_id in spec.claim_ids:
        effect = evidence["effects"][claim_id]
        key = (
            effect["source_artifact"],
            effect["source_sha256"],
            effect["audit_marker"] or "",
            effect["audit_marker_sha256"] or "",
        )
        sources[key] = {
            "source_artifact": key[0],
            "source_sha256": key[1],
            "audit_marker": key[2],
            "audit_marker_sha256": key[3],
        }
    return {
        "configuration": {
            "path": _relative_to_root(configuration_path, root),
            "sha256": sha256_file(configuration_path),
        },
        "model_results_manifest": {
            "path": _relative_to_root(model_manifest_path, root),
            "sha256": sha256_file(model_manifest_path),
            "manifest_sha256": model_manifest["manifest_sha256"],
            "stage_id": model_manifest["stage_id"],
        },
        "synthesis_manifest": {
            "path": _relative_to_root(synthesis_manifest_path, root),
            "sha256": sha256_file(synthesis_manifest_path),
            "manifest_sha256": synthesis_manifest["manifest_sha256"],
            "stage_id": synthesis_manifest["stage_id"],
        },
        "registered_sources": [sources[key] for key in sorted(sources)],
    }


def _reject_extra_outputs(output_dir: Path) -> None:
    if not output_dir.exists():
        return
    extras = sorted(
        entry.name for entry in output_dir.iterdir() if entry.name not in EXPECTED_OUTPUT_NAMES
    )
    if extras:
        raise ContractError(f"plots output directory contains extra products: {extras}")


def build_supervisor_plots(
    *,
    root: Path | str,
    configuration_path: Path | str = DEFAULT_CONFIGURATION,
    input_dir: Path | str = DEFAULT_OUTPUT_DIR,
    output_dir: Path | str = DEFAULT_PLOT_OUTPUT_DIR,
    synthesis_manifest_path: Path | str | None = None,
    model_results_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Write the fixed six-figure set and a chained PASS manifest."""

    base = Path(root).resolve()
    config_path = _rooted(configuration_path, base)
    inputs = _rooted(input_dir, base)
    destination = _rooted(output_dir, base)
    synthesis_manifest_file = (
        inputs / "synthesis_manifest.json"
        if synthesis_manifest_path is None
        else _rooted(synthesis_manifest_path, base)
    )
    model_manifest_file = (
        inputs / "model_results_manifest.json"
        if model_results_manifest_path is None
        else _rooted(model_results_manifest_path, base)
    )
    for path in (config_path, inputs, destination, synthesis_manifest_file, model_manifest_file):
        _relative_to_root(path, base)

    _reject_extra_outputs(destination)
    synthesis_manifest = verify_stage_manifest(
        synthesis_manifest_file, root=base, expected_stage="synthesis"
    )
    model_manifest = verify_stage_manifest(
        model_manifest_file, root=base, expected_stage="model-results"
    )
    if synthesis_manifest["upstream_manifests"] != [
        {
            "stage_id": "model-results",
            "path": _relative_to_root(model_manifest_file, base),
            "sha256": sha256_file(model_manifest_file),
        }
    ]:
        raise ContractError("synthesis/model-results manifest link drift")

    named_inputs = {
        "configuration": config_path,
        "headline": inputs / "headline_findings.csv",
        "supporting": inputs / "supporting_findings.csv",
        "limitations": inputs / "coverage_and_limitations.csv",
        "pages": inputs / "page_registry.csv",
        "synthesis_manifest": synthesis_manifest_file,
        "effects": inputs / "effect_registry.csv",
        "models": inputs / "model_inventory.csv",
        "samples": inputs / "sample_registry.csv",
        "model_results_manifest": model_manifest_file,
    }
    before = _input_snapshot(named_inputs.values(), base)
    config = load_frozen_configuration(config_path)
    synthesis_rows = [
        row
        for name in ("headline", "supporting", "limitations")
        for row in read_registry_csv(named_inputs[name], "synthesis")
    ]
    effects = read_registry_csv(named_inputs["effects"], "effect")
    models = read_registry_csv(named_inputs["models"], "model")
    samples = read_registry_csv(named_inputs["samples"], "sample")
    pages = read_registry_csv(named_inputs["pages"], "page")
    _validate_page_registry(config, pages)
    evidence = validate_plot_evidence(
        config=config,
        effects=effects,
        models=models,
        samples=samples,
        synthesis=synthesis_rows,
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}-build-", dir=destination.parent
    ) as temporary_directory:
        staging = Path(temporary_directory)
        figure_records: list[dict[str, Any]] = []
        core_records: list[dict[str, Any]] = []
        for spec in FIGURE_SPECS:
            plot_rows = _build_plot_rows(spec, evidence)
            data_path = staging / spec.plot_data_name
            image_path = staging / spec.image_name
            _atomic_write_rows(data_path, PLOT_DATA_COLUMNS, plot_rows)
            exported = _read_rows(data_path)
            if exported != plot_rows:
                raise ContractError(f"{spec.figure_id} plot-data export changed values")
            figure = _render_figure(spec, plot_rows)
            _save_figure(image_path, figure, spec)

            final_data = destination / spec.plot_data_name
            final_image = destination / spec.image_name
            claim_ids = sorted(spec.claim_ids)
            effect_ids = sorted(evidence["effects"][claim_id]["effect_id"] for claim_id in claim_ids)
            eligibility = (
                "PRIMARY"
                if any(evidence["effects"][claim_id]["figure_eligibility"] == "PRIMARY" for claim_id in claim_ids)
                else "SUPPORTING"
            )
            provenance = _upstream_provenance(
                spec=spec,
                evidence=evidence,
                configuration_path=config_path,
                synthesis_manifest_path=synthesis_manifest_file,
                synthesis_manifest=synthesis_manifest,
                model_manifest_path=model_manifest_file,
                model_manifest=model_manifest,
                root=base,
            )
            core = {
                "schema_version": CONTRACT_VERSION,
                "figure_id": spec.figure_id,
                "claim_ids": claim_ids,
                "effect_ids": effect_ids,
                "eligibility": eligibility,
                "figure_role": spec.figure_role,
                "plot_data_path": _relative_to_root(final_data, base),
                "plot_data_sha256": sha256_file(data_path),
                "image_path": _relative_to_root(final_image, base),
                "image_sha256": sha256_file(image_path),
                "caption": spec.caption,
                "alt_text": spec.alt_text,
                "width_px": spec.width_px,
                "height_px": spec.height_px,
            }
            core_records.append(core)
            figure_records.append(
                {
                    **core,
                    "claim_ids": _canonical_json(claim_ids),
                    "effect_ids": _canonical_json(effect_ids),
                    "scientific_role": spec.scientific_role,
                    "warnings": _canonical_json(list(spec.warnings)),
                    "upstream_provenance": _canonical_json(provenance),
                }
            )

        validate_registry_bundle(
            {
                "sample": evidence["sample_rows"],
                "model": evidence["model_rows"],
                "effect": evidence["effect_rows"],
                "figure": core_records,
            }
        )
        figure_records.sort(key=lambda row: row["figure_id"])
        figure_manifest_staging = staging / "figure_manifest.csv"
        _atomic_write_rows(
            figure_manifest_staging, FIGURE_MANIFEST_COLUMNS, figure_records
        )

        after = _input_snapshot(named_inputs.values(), base)
        if before != after:
            raise ContractError("upstream inputs changed during plot generation")

        destination.mkdir(parents=True, exist_ok=True)
        promoted_names = [
            name for name in EXPECTED_OUTPUT_NAMES if name != "plot_manifest.json"
        ]
        for name in promoted_names:
            source = staging / name
            if not source.is_file():
                raise ContractError(f"missing staged plot product: {name}")
        for name in promoted_names:
            os.replace(staging / name, destination / name)

    manifest_path = destination / "plot_manifest.json"
    artifact_paths = [destination / name for name in EXPECTED_OUTPUT_NAMES if name != "plot_manifest.json"]
    manifest = write_stage_manifest(
        manifest_path,
        stage_id="plots",
        artifact_paths=artifact_paths,
        upstream_manifest_paths=[synthesis_manifest_file],
        root=base,
        configuration_path=config_path,
    )
    verify_stage_manifest(manifest_path, root=base, expected_stage="plots")
    _reject_extra_outputs(destination)
    observed_names = sorted(entry.name for entry in destination.iterdir())
    if observed_names != sorted(EXPECTED_OUTPUT_NAMES):
        raise ContractError(
            f"fixed plot output set mismatch: observed={observed_names}"
        )

    figure_manifest_rows = _read_rows(destination / "figure_manifest.csv")
    if [row["figure_id"] for row in figure_manifest_rows] != sorted(
        spec.figure_id for spec in FIGURE_SPECS
    ):
        raise ContractError("figure manifest ordering changed")
    for row in figure_manifest_rows:
        for path_field, hash_field in (
            ("plot_data_path", "plot_data_sha256"),
            ("image_path", "image_sha256"),
        ):
            path = _rooted(row[path_field], base)
            if sha256_file(path) != row[hash_field]:
                raise ContractError(
                    f"{row['figure_id']} {path_field} hash verification failed"
                )

    artifact_sha256 = {
        name: sha256_file(destination / name) for name in EXPECTED_OUTPUT_NAMES
    }
    return {
        "status": "PASS",
        "stage": "plots",
        "figure_count": len(FIGURE_SPECS),
        "plot_data_count": len(FIGURE_SPECS),
        "output_dir": _relative_to_root(destination, base),
        "figure_manifest": _relative_to_root(destination / "figure_manifest.csv", base),
        "plot_manifest": _relative_to_root(manifest_path, base),
        "artifact_sha256": dict(sorted(artifact_sha256.items())),
        "input_hashes_before": before,
        "input_hashes_after": after,
        "manifest": manifest,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--configuration", type=Path, default=DEFAULT_CONFIGURATION)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_PLOT_OUTPUT_DIR)
    parser.add_argument("--synthesis-manifest", type=Path)
    parser.add_argument("--model-results-manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = build_supervisor_plots(
        root=args.root,
        configuration_path=args.configuration,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        synthesis_manifest_path=args.synthesis_manifest,
        model_results_manifest_path=args.model_results_manifest,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
