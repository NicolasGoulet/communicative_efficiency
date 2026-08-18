"""Claim-resolved sections for the integrated August supervisor report.

The report stage reads only the compact scientific-synthesis tables, page
registry, and frozen figure manifests.  It never reads scored rows, model
tables, or plotting data, and it performs no statistical calculation.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .contracts import (
    CONTRACT_VERSION,
    ContractError,
    read_registry_csv,
    sha256_file,
    verify_stage_manifest,
)


DEFAULT_INPUT_DIR = Path("results/august_supervisor_report")
DEFAULT_PLOT_DIR = DEFAULT_INPUT_DIR / "plots"

REQUIRED_SECTION_TITLES = (
    "Executive reading",
    "Sample logic",
    "Utterance predictability at fixed effort",
    "Word-level findings across three scorers",
    "Unconditional and contextual decomposition",
    "Generated baselines and corrected candidate-set Bayes evidence",
    "Response uncertainty and effort adaptation",
    "Developmental onset",
    "Hall: a separate historical snapshot",
    "Conclusions and next decisive tests",
)

EXPECTED_CLASSIFICATIONS = {
    "BAYES_HELDOUT_CONTEXT_VALIDATION": "SUPPORTED",
    "BAYES_REAL_CANDIDATE_SET_PROBABILITY": "SUPPORTED",
    "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP": "QUALIFIED",
    "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY": "QUALIFIED",
    "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN": "CONTRARY",
    "DIRECT_NONPBM_MISTRAL_UNCONDITIONAL": "SUPPORTED",
    "DIRECT_PAIRED_CONTEXTUAL_SCORER_DIFFERENCE": "QUALIFIED",
    "DIRECT_PBM_MISTRAL_CONTEXTUAL": "SUPPORTED",
    "DIRECT_PBM_MISTRAL_CONTEXT_GAIN": "CONTRARY",
    "DIRECT_PBM_MISTRAL_UNCONDITIONAL": "SUPPORTED",
    "DIRECT_PBM_TINY_CONTEXTUAL": "SUPPORTED",
    "DIRECT_PBM_TINY_CONTEXT_GAIN": "CONTRARY",
    "DIRECT_PBM_TINY_UNCONDITIONAL": "SUPPORTED",
    "ONSET_NONPBM_SUSTAINED": "QUALIFIED",
    "ONSET_PBM_SUSTAINED": "QUALIFIED",
    "ROUTE2_AGE_ENTROPY_INTERACTION": "CONTRARY",
    "ROUTE2_RELATIVE_EFFORT_AGE": "QUALIFIED",
    "WORD_CONTEXT_GAIN_SCORER_DEPENDENT": "QUALIFIED",
    "WORD_CROSS_SCORER_PREDICTABILITY": "SUPPORTED",
    "WORD_LONGER_TYPES_CONTEXT_SUPPORT": "SUPPORTED",
    "HALL_ADULT_CONTEXT_INTERACTION": "DESCRIPTIVE",
    "HALL_LOCKED_DOMAIN_SHIFT": "DESCRIPTIVE",
    "HALL_RACE_CLASS_INTERACTION": "DESCRIPTIVE",
    "ALTERNATIVE_EFFORT_ONSET": "PENDING",
    "CONVERSATIONAL_MANUAL_VALIDATION": "PENDING",
    "CROSS_TOKENIZER_MAGNITUDE_POOLING": "QUALIFIED",
    "DECOUPLED_RESPONSE_CALIBRATION": "PENDING",
    "GENERATED_CANDIDATE_MEANING_PRESERVATION": "QUALIFIED",
    "LISTENER_UTILITY_OUTCOME": "PENDING",
    "RESPONSE_ENTROPY_SEMANTIC_CLAIM": "QUALIFIED",
    "WORD_NONPBM58_CONFIRMATION": "PENDING",
}

EXPECTED_FIGURE_CLAIMS = {
    "FIGURE_01_FIXED_EFFORT_PREDICTABILITY": (
        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP",
        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
        "DIRECT_PBM_MISTRAL_CONTEXTUAL",
    ),
    "FIGURE_02_UNCONDITIONAL_CONTEXTUAL_COMPONENTS": (
        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
        "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN",
        "DIRECT_NONPBM_MISTRAL_UNCONDITIONAL",
        "DIRECT_PBM_MISTRAL_CONTEXTUAL",
        "DIRECT_PBM_MISTRAL_CONTEXT_GAIN",
        "DIRECT_PBM_MISTRAL_UNCONDITIONAL",
        "DIRECT_PBM_TINY_CONTEXTUAL",
        "DIRECT_PBM_TINY_CONTEXT_GAIN",
        "DIRECT_PBM_TINY_UNCONDITIONAL",
    ),
    "FIGURE_03_WORD_CROSS_SCORER_SIGNS": (
        "WORD_CONTEXT_GAIN_SCORER_DEPENDENT",
        "WORD_CROSS_SCORER_PREDICTABILITY",
        "WORD_LONGER_TYPES_CONTEXT_SUPPORT",
    ),
    "FIGURE_04_ROUTE2_QUALIFICATION": (
        "ROUTE2_AGE_ENTROPY_INTERACTION",
        "ROUTE2_RELATIVE_EFFORT_AGE",
    ),
    "FIGURE_05_SUSTAINED_ONSET_STATUS": (
        "ONSET_NONPBM_SUSTAINED",
        "ONSET_PBM_SUSTAINED",
    ),
    "FIGURE_06_HALL_SNAPSHOT": (
        "HALL_ADULT_CONTEXT_INTERACTION",
        "HALL_LOCKED_DOMAIN_SHIFT",
        "HALL_RACE_CLASS_INTERACTION",
    ),
}

REQUIRED_READY_PAGE_IDS = (
    "PAGE_RESOURCE_DIRECT_RESULTS_EXPLORER",
    "PAGE_RESOURCE_WORD_CROSS_SCORER_COMPARISON",
    "PAGE_RESOURCE_HALL_SNAPSHOT",
    "PAGE_RESOURCE_CORRECTED_BAYES",
    "PAGE_RESOURCE_SUSTAINED_ONSET",
    "PAGE_RESOURCE_CHILD_TRAJECTORIES",
    "PAGE_RESOURCE_FORMAL_DEFINITIONS",
    "PAGE_RESOURCE_TECHNICAL_ANALYSIS_INVENTORY",
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


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    classification: str
    destination_section: str
    finding: str
    limitation: str
    evidence_id: str


@dataclass(frozen=True)
class FigureRecord:
    figure_id: str
    claim_ids: tuple[str, ...]
    image_path: str
    image_sha256: str
    caption: str
    alt_text: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PageRecord:
    page_id: str
    title: str
    output_path: str
    page_status: str
    display_order: int


@dataclass(frozen=True)
class ReportEvidence:
    root: Path
    input_dir: Path
    plot_dir: Path
    plot_manifest_path: Path
    claims: dict[str, ClaimRecord]
    figures: dict[str, FigureRecord]
    pages: dict[str, PageRecord]


@dataclass(frozen=True)
class ReportStatement:
    status: str
    text: str
    claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReportSection:
    section_id: str
    title: str
    lead: str
    statements: tuple[ReportStatement, ...]
    figure_ids: tuple[str, ...] = ()
    source_page_ids: tuple[str, ...] = ()


def _rooted(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ContractError(f"report-stage path is outside repository root: {path}") from error
    return resolved


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as error:
        raise ContractError(f"report-stage path is outside repository root: {path}") from error


def _input_snapshot(paths: Iterable[Path], root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in paths:
        if not path.is_file():
            raise ContractError(f"missing report input: {_relative(path, root)}")
        snapshot[_relative(path, root)] = sha256_file(path)
    return dict(sorted(snapshot.items()))


def _parse_json_list(
    value: str, *, label: str, require_sorted: bool = True
) -> tuple[str, ...]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ContractError(f"{label} is not valid JSON") from error
    if (
        type(parsed) is not list
        or not parsed
        or any(type(item) is not str or not item for item in parsed)
        or len(parsed) != len(set(parsed))
        or (require_sorted and parsed != sorted(parsed))
    ):
        raise ContractError(f"{label} must be a nonempty sorted unique string list")
    return tuple(parsed)


def _read_figure_manifest(path: Path, *, root: Path) -> dict[str, FigureRecord]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FIGURE_MANIFEST_COLUMNS:
            raise ContractError("figure manifest columns changed")
        rows = list(reader)
    figures: dict[str, FigureRecord] = {}
    for index, row in enumerate(rows):
        figure_id = row["figure_id"]
        if figure_id in figures:
            raise ContractError(f"duplicate report figure: {figure_id}")
        if row["schema_version"] != CONTRACT_VERSION:
            raise ContractError(f"{figure_id} schema version changed")
        claim_ids = _parse_json_list(
            row["claim_ids"], label=f"figure[{index}].claim_ids"
        )
        warnings = _parse_json_list(
            row["warnings"],
            label=f"figure[{index}].warnings",
            require_sorted=False,
        )
        expected_claims = EXPECTED_FIGURE_CLAIMS.get(figure_id)
        if expected_claims is None or claim_ids != expected_claims:
            raise ContractError(f"{figure_id} source claim IDs changed")
        if not row["caption"].strip() or not row["alt_text"].strip():
            raise ContractError(f"{figure_id} caption or alt text is empty")
        image_path = _rooted(row["image_path"], root)
        if not image_path.is_file() or sha256_file(image_path) != row["image_sha256"]:
            raise ContractError(f"{figure_id} image hash verification failed")
        plot_data_path = _rooted(row["plot_data_path"], root)
        if (
            not plot_data_path.is_file()
            or sha256_file(plot_data_path) != row["plot_data_sha256"]
        ):
            raise ContractError(f"{figure_id} plot-data hash verification failed")
        figures[figure_id] = FigureRecord(
            figure_id=figure_id,
            claim_ids=claim_ids,
            image_path=_relative(image_path, root),
            image_sha256=row["image_sha256"],
            caption=row["caption"].strip(),
            alt_text=row["alt_text"].strip(),
            warnings=warnings,
        )
    if set(figures) != set(EXPECTED_FIGURE_CLAIMS):
        raise ContractError(
            "figure coverage mismatch; "
            f"missing={sorted(set(EXPECTED_FIGURE_CLAIMS) - set(figures))}, "
            f"extra={sorted(set(figures) - set(EXPECTED_FIGURE_CLAIMS))}"
        )
    return dict(sorted(figures.items()))


def load_report_evidence(
    *,
    root: Path | str,
    input_dir: Path | str = DEFAULT_INPUT_DIR,
    plot_dir: Path | str = DEFAULT_PLOT_DIR,
    plot_manifest_path: Path | str | None = None,
) -> ReportEvidence:
    """Load and validate the complete frozen report-stage input boundary."""

    base = Path(root).resolve()
    inputs = _rooted(input_dir, base)
    figures_dir = _rooted(plot_dir, base)
    plot_manifest_file = _rooted(
        figures_dir / "plot_manifest.json"
        if plot_manifest_path is None
        else plot_manifest_path,
        base,
    )
    synthesis_manifest_file = inputs / "synthesis_manifest.json"

    plot_manifest = verify_stage_manifest(
        plot_manifest_file, root=base, expected_stage="plots"
    )
    synthesis_manifest = verify_stage_manifest(
        synthesis_manifest_file, root=base, expected_stage="synthesis"
    )
    expected_upstream = [
        {
            "stage_id": "synthesis",
            "path": _relative(synthesis_manifest_file, base),
            "sha256": sha256_file(synthesis_manifest_file),
        }
    ]
    if plot_manifest["upstream_manifests"] != expected_upstream:
        raise ContractError("plot/synthesis manifest link drift")

    named_inputs = {
        "headline": inputs / "headline_findings.csv",
        "supporting": inputs / "supporting_findings.csv",
        "limitations": inputs / "coverage_and_limitations.csv",
        "pages": inputs / "page_registry.csv",
        "synthesis_manifest": synthesis_manifest_file,
        "figure_manifest": figures_dir / "figure_manifest.csv",
        "plot_manifest": plot_manifest_file,
    }
    _input_snapshot(named_inputs.values(), base)

    synthesis_rows = [
        row
        for name in ("headline", "supporting", "limitations")
        for row in read_registry_csv(named_inputs[name], "synthesis")
    ]
    claims: dict[str, ClaimRecord] = {}
    for row in synthesis_rows:
        claim_id = row["claim_id"]
        if claim_id in claims:
            raise ContractError(f"duplicate synthesis claim: {claim_id}")
        claims[claim_id] = ClaimRecord(
            claim_id=claim_id,
            classification=row["classification"],
            destination_section=row["destination_section"],
            finding=row["finding"],
            limitation=row["limitation"],
            evidence_id=row["evidence_id"],
        )
    if set(claims) != set(EXPECTED_CLASSIFICATIONS):
        raise ContractError(
            "report claim coverage mismatch; "
            f"missing={sorted(set(EXPECTED_CLASSIFICATIONS) - set(claims))}, "
            f"extra={sorted(set(claims) - set(EXPECTED_CLASSIFICATIONS))}"
        )
    for claim_id, expected in EXPECTED_CLASSIFICATIONS.items():
        if claims[claim_id].classification != expected:
            raise ContractError(
                f"{claim_id} classification changed: expected {expected}, "
                f"observed {claims[claim_id].classification}"
            )

    page_rows = read_registry_csv(named_inputs["pages"], "page")
    pages = {
        row["page_id"]: PageRecord(
            page_id=row["page_id"],
            title=row["title"],
            output_path=row["output_path"],
            page_status=row["page_status"],
            display_order=row["display_order"],
        )
        for row in page_rows
    }
    ready_page_ids = {
        page_id for page_id, page in pages.items() if page.page_status == "READY"
    }
    if ready_page_ids != set(REQUIRED_READY_PAGE_IDS):
        raise ContractError(
            "ready source-link coverage mismatch; "
            f"missing={sorted(set(REQUIRED_READY_PAGE_IDS) - ready_page_ids)}, "
            f"extra={sorted(ready_page_ids - set(REQUIRED_READY_PAGE_IDS))}"
        )
    for page_id in REQUIRED_READY_PAGE_IDS:
        resource = _rooted(pages[page_id].output_path, base)
        if not resource.is_file():
            raise ContractError(f"required report source is missing: {pages[page_id].output_path}")

    figures = _read_figure_manifest(named_inputs["figure_manifest"], root=base)
    for figure in figures.values():
        unknown = set(figure.claim_ids) - set(claims)
        if unknown:
            raise ContractError(
                f"{figure.figure_id} has unresolved source claims: {sorted(unknown)}"
            )

    return ReportEvidence(
        root=base,
        input_dir=inputs,
        plot_dir=figures_dir,
        plot_manifest_path=plot_manifest_file,
        claims=dict(sorted(claims.items())),
        figures=figures,
        pages=dict(sorted(pages.items())),
    )


def _statement(
    evidence: ReportEvidence,
    status: str,
    claim_ids: tuple[str, ...],
    text: str,
) -> ReportStatement:
    if not text.strip():
        raise ContractError("report statement may not be empty")
    if not claim_ids or len(claim_ids) != len(set(claim_ids)):
        raise ContractError("report statement claim IDs must be nonempty and unique")
    unresolved = set(claim_ids) - set(evidence.claims)
    if unresolved:
        raise ContractError(f"report statement has unresolved claims: {sorted(unresolved)}")
    observed = {evidence.claims[claim_id].classification for claim_id in claim_ids}
    if observed != {status}:
        raise ContractError(
            f"report statement status mismatch: expected {status}, observed {sorted(observed)}"
        )
    frozen_text = " ".join(
        f"{evidence.claims[claim_id].finding} {evidence.claims[claim_id].limitation}"
        for claim_id in claim_ids
    )
    for number in re.findall(r"(?<![A-Za-z])\d[\d,.]*(?![A-Za-z])", text):
        if number not in frozen_text:
            raise ContractError(
                f"numeric report text {number!r} does not resolve to {claim_ids}"
            )
    return ReportStatement(status=status, text=text.strip(), claim_ids=claim_ids)


def build_report_sections(evidence: ReportEvidence) -> tuple[ReportSection, ...]:
    """Build the fixed, fully claim-resolved supervisor narrative."""

    def statement(status: str, claim_ids: tuple[str, ...], text: str) -> ReportStatement:
        return _statement(evidence, status, claim_ids, text)

    sections = (
        ReportSection(
            section_id="executive-reading",
            title="Executive reading",
            lead=(
                "The central result is narrow but coherent: development is associated "
                "with greater model-based predictability of form at fixed measured "
                "effort. The report separates evidence labels so directional "
                "robustness is not mistaken for sample confirmation."
            ),
            statements=(
                statement(
                    "SUPPORTED",
                    (
                        "DIRECT_PBM_MISTRAL_CONTEXTUAL",
                        "WORD_CROSS_SCORER_PREDICTABILITY",
                    ),
                    (
                        "In PBM discovery, older children's forms are more predictable "
                        "at the same measured effort; the same-word direction is also "
                        "robust across the three separately fit scorers."
                    ),
                ),
                statement(
                    "QUALIFIED",
                    (
                        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
                        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP",
                    ),
                    (
                        "The separate non-PBM contextual association points in the same "
                        "direction but is not confirmed because the frozen primary "
                        "child-clustered interval crosses zero; child-resampling remains "
                        "a sensitivity, not a replacement decision rule."
                    ),
                ),
                statement(
                    "CONTRARY",
                    (
                        "DIRECT_PBM_MISTRAL_CONTEXT_GAIN",
                        "ROUTE2_AGE_ENTROPY_INTERACTION",
                    ),
                    (
                        "Context gain declines rather than rises, and the principal "
                        "response-uncertainty interaction also runs opposite to its "
                        "registered positive prediction."
                    ),
                ),
                statement(
                    "PENDING",
                    ("LISTENER_UTILITY_OUTCOME",),
                    (
                        "A broad communicative-success claim remains pending: target "
                        "surprisal is not listener utility, and no validated downstream "
                        "listener-relevant outcome is registered."
                    ),
                ),
            ),
        ),
        ReportSection(
            section_id="sample-logic",
            title="Sample logic",
            lead=(
                "The report uses discovery, confirmation, scorer-robustness, and "
                "cross-sectional samples for different inferential jobs. They are "
                "never pooled into one evidential label."
            ),
            statements=(
                statement(
                    "SUPPORTED",
                    (
                        "DIRECT_PBM_MISTRAL_CONTEXTUAL",
                        "DIRECT_PBM_TINY_CONTEXTUAL",
                    ),
                    (
                        "PBM is the 21-child discovery sample. TinyDialogues reuses those "
                        "children, so agreement is scorer robustness rather than an "
                        "independent replication."
                    ),
                ),
                statement(
                    "QUALIFIED",
                    (
                        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
                        "ONSET_NONPBM_SUSTAINED",
                    ),
                    (
                        "The remaining 58 children form the distinct non-PBM "
                        "confirmation sample; its frozen primary contextual result keeps "
                        "the qualified label."
                    ),
                ),
                statement(
                    "PENDING",
                    ("CONVERSATIONAL_MANUAL_VALIDATION",),
                    (
                        "The proposed conversationally responsive sample remains at "
                        "review stage: the 325-row manual validation and resolution of "
                        "18,172 context-k1 mismatches are still required."
                    ),
                ),
            ),
        ),
        ReportSection(
            section_id="utterance-predictability-fixed-effort",
            title="Utterance predictability at fixed effort",
            lead=(
                "The estimand is scorer self-information conditional on measured word "
                "effort and child baseline. Lower surprisal means greater scorer-based "
                "predictability or conventionality of form."
            ),
            statements=(
                statement(
                    "SUPPORTED",
                    (
                        "DIRECT_PBM_MISTRAL_CONTEXTUAL",
                        "DIRECT_PBM_TINY_CONTEXTUAL",
                    ),
                    (
                        "The negative fixed-effort age direction is supported for PBM "
                        "with Mistral and repeats with TinyDialogues on the same children. "
                        "It is not listener utility, greater Shannon information "
                        "communicated, or proof of optimization."
                    ),
                ),
                statement(
                    "QUALIFIED",
                    ("DIRECT_PAIRED_CONTEXTUAL_SCORER_DIFFERENCE",),
                    (
                        "The paired scorer comparison supports directional robustness, "
                        "but tokenizer and calibration differences prevent a universal "
                        "cross-model magnitude interpretation."
                    ),
                ),
                statement(
                    "QUALIFIED",
                    (
                        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_PRIMARY",
                        "DIRECT_NONPBM_MISTRAL_CONTEXTUAL_BOOTSTRAP",
                    ),
                    (
                        "The non-PBM estimate is direction-consistent but not confirmed "
                        "under the primary clustered interval. The child-resampling "
                        "interval is reported beside it only as sensitivity evidence."
                    ),
                ),
            ),
            figure_ids=("FIGURE_01_FIXED_EFFORT_PREDICTABILITY",),
            source_page_ids=("PAGE_RESOURCE_DIRECT_RESULTS_EXPLORER",),
        ),
        ReportSection(
            section_id="word-level-three-scorer",
            title="Word-level findings across three scorers",
            lead=(
                "The word analysis compares separate scorer-specific fits on the exact "
                "shared PBM word-occurrence set. Raw bits and coefficients are not "
                "pooled across tokenizers."
            ),
            statements=(
                statement(
                    "SUPPORTED",
                    ("WORD_CROSS_SCORER_PREDICTABILITY",),
                    (
                        "Same-word unconditional and contextual age directions are "
                        "interval-supported in all three scorer-specific fits. This is "
                        "same-sample robustness, not confirmation in the remaining 58 "
                        "children."
                    ),
                ),
                statement(
                    "SUPPORTED",
                    ("WORD_LONGER_TYPES_CONTEXT_SUPPORT",),
                    (
                        "Longer word types receive more contextual support in all three "
                        "separate fits, while remaining a lexical and scorer-indexed "
                        "association rather than a listener-utility result."
                    ),
                ),
                statement(
                    "QUALIFIED",
                    (
                        "WORD_CONTEXT_GAIN_SCORER_DEPENDENT",
                        "CROSS_TOKENIZER_MAGNITUDE_POOLING",
                    ),
                    (
                        "Word-level context-gain development is scorer-dependent, with "
                        "mixed signs. Direction and uncertainty may be compared, but raw "
                        "magnitudes have no registered pooled interpretation."
                    ),
                ),
                statement(
                    "PENDING",
                    ("WORD_NONPBM58_CONFIRMATION",),
                    (
                        "No remaining-58 word estimate is available for promotion; the "
                        "registered production, audit, and frozen analysis must finish "
                        "before this result can be tested out of sample."
                    ),
                ),
            ),
            figure_ids=("FIGURE_03_WORD_CROSS_SCORER_SIGNS",),
            source_page_ids=("PAGE_RESOURCE_WORD_CROSS_SCORER_COMPARISON",),
        ),
        ReportSection(
            section_id="unconditional-contextual-decomposition",
            title="Unconditional and contextual decomposition",
            lead=(
                "Contextual surprisal, unconditional surprisal, and context gain answer "
                "different questions. The decomposition keeps conventionality of form "
                "separate from the support supplied by preceding context."
            ),
            statements=(
                statement(
                    "SUPPORTED",
                    (
                        "DIRECT_PBM_MISTRAL_UNCONDITIONAL",
                        "DIRECT_PBM_TINY_UNCONDITIONAL",
                        "DIRECT_NONPBM_MISTRAL_UNCONDITIONAL",
                    ),
                    (
                        "Unconditional surprisal declines with age in PBM under both "
                        "scorers and is also supported in the non-PBM Mistral sample. "
                        "That association is distinct from contextual support."
                    ),
                ),
                statement(
                    "CONTRARY",
                    (
                        "DIRECT_PBM_MISTRAL_CONTEXT_GAIN",
                        "DIRECT_PBM_TINY_CONTEXT_GAIN",
                        "DIRECT_NONPBM_MISTRAL_CONTEXT_GAIN",
                    ),
                    (
                        "Utterance context gain declines in PBM under both scorers and in "
                        "the non-PBM sample. This repeated negative direction is contrary "
                        "to the frozen positive prediction, not confirmation of it."
                    ),
                ),
            ),
            figure_ids=("FIGURE_02_UNCONDITIONAL_CONTEXTUAL_COMPONENTS",),
            source_page_ids=("PAGE_RESOURCE_FORMAL_DEFINITIONS",),
        ),
        ReportSection(
            section_id="baseline-bayes-evidence",
            title="Generated baselines and corrected candidate-set Bayes evidence",
            lead=(
                "Generated alternatives are useful reference distributions and "
                "diagnostics. They do not define a meaning-preserving choice set for the "
                "child."
            ),
            statements=(
                statement(
                    "QUALIFIED",
                    ("GENERATED_CANDIDATE_MEANING_PRESERVATION",),
                    (
                        "Generated alternatives are model-based references or "
                        "diagnostics and are not meaning-preserving. They cannot support "
                        "Pareto-optimality or intended-meaning choice claims."
                    ),
                ),
                statement(
                    "SUPPORTED",
                    ("BAYES_REAL_CANDIDATE_SET_PROBABILITY",),
                    (
                        "Within the supplied matched candidate set, the observed "
                        "utterance ranks first on 43.7% of real rows and has mean "
                        "candidate-set probability 0.400. This is not a posterior over "
                        "every possible utterance."
                    ),
                ),
                statement(
                    "SUPPORTED",
                    ("BAYES_HELDOUT_CONTEXT_VALIDATION",),
                    (
                        "The corrected context-evidence calculation passes the registered "
                        "matched-versus-shuffled validation in all three held-out corpora. "
                        "That validates the decomposition mechanics, not meaning "
                        "preservation or a universal posterior."
                    ),
                ),
            ),
            source_page_ids=("PAGE_RESOURCE_CORRECTED_BAYES",),
        ),
        ReportSection(
            section_id="response-uncertainty-effort",
            title="Response uncertainty and effort adaptation",
            lead=(
                "This analysis compares observed child effort with a generated response "
                "reference. The generated expectation can mediate contextual demand, so "
                "the result is kept distinct from raw effort."
            ),
            statements=(
                statement(
                    "QUALIFIED",
                    ("ROUTE2_RELATIVE_EFFORT_AGE",),
                    (
                        "Observed effort relative to the model-generated reference "
                        "increases with age, but the association is measurement-limited "
                        "by the coupled generator and scorer."
                    ),
                ),
                statement(
                    "CONTRARY",
                    ("ROUTE2_AGE_ENTROPY_INTERACTION",),
                    (
                        "The principal age-by-response-entropy interaction is negative, "
                        "opposite to the simple prediction that older children would "
                        "increasingly lengthen responses as uncertainty rises."
                    ),
                ),
                statement(
                    "QUALIFIED",
                    ("RESPONSE_ENTROPY_SEMANTIC_CLAIM",),
                    (
                        "The present measure is exact-string response entropy. It is not "
                        "semantic uncertainty and is model-, prompt-, temperature-, and "
                        "seed-dependent."
                    ),
                ),
                statement(
                    "PENDING",
                    ("DECOUPLED_RESPONSE_CALIBRATION",),
                    (
                        "Semantic clustering, rarefaction, settings sensitivity, and a "
                        "decoupled generator comparison remain pending before the "
                        "response-space hypothesis can receive a stronger reading."
                    ),
                ),
            ),
            figure_ids=("FIGURE_04_ROUTE2_QUALIFICATION",),
        ),
        ReportSection(
            section_id="developmental-onset",
            title="Developmental onset",
            lead=(
                "The registered onset question requires a decrease that is sustained "
                "under simultaneous uncertainty, rather than selecting a favorable "
                "pointwise age contrast."
            ),
            statements=(
                statement(
                    "QUALIFIED",
                    ("ONSET_PBM_SUSTAINED", "ONSET_NONPBM_SUSTAINED"),
                    (
                        "Sustained onset is not established in either PBM discovery or "
                        "the 58-child non-PBM confirmation sample. The earlier nominal "
                        "24-29-month PBM contrast is not promoted as onset."
                    ),
                ),
                statement(
                    "PENDING",
                    ("ALTERNATIVE_EFFORT_ONSET",),
                    (
                        "Equivalent sustained-onset tests with validated morpheme, "
                        "syllable, and phoneme effort controls remain pending."
                    ),
                ),
            ),
            figure_ids=("FIGURE_05_SUSTAINED_ONSET_STATUS",),
            source_page_ids=("PAGE_RESOURCE_SUSTAINED_ONSET",),
        ),
        ReportSection(
            section_id="hall-historical-snapshot",
            title="Hall: a separate historical snapshot",
            lead=(
                "Hall is treated as a historical cross-sectional and domain-sensitivity "
                "analysis, separate from longitudinal development. Its scorer-indexed "
                "stratum contrasts are descriptive."
            ),
            statements=(
                statement(
                    "DESCRIPTIVE",
                    ("HALL_RACE_CLASS_INTERACTION",),
                    (
                        "The within-Hall race-by-class interaction is a historical, "
                        "scorer-indexed comparison at fixed cleaned word count and "
                        "setting. It is not a causal SES effect, linguistic deficit, or "
                        "inherent group difference."
                    ),
                ),
                statement(
                    "DESCRIPTIVE",
                    ("HALL_ADULT_CONTEXT_INTERACTION",),
                    (
                        "The adult-adjacent context-support interaction has an interval "
                        "crossing zero, so there is no clear interaction under the frozen "
                        "scorer and specification."
                    ),
                ),
                statement(
                    "DESCRIPTIVE",
                    ("HALL_LOCKED_DOMAIN_SHIFT",),
                    (
                        "The Hall-minus-current contrast is evidence of sensitivity to "
                        "domain, era, dialect, geography, transcription, setting, and "
                        "model representation—not a causal cohort comparison."
                    ),
                ),
            ),
            figure_ids=("FIGURE_06_HALL_SNAPSHOT",),
            source_page_ids=("PAGE_RESOURCE_HALL_SNAPSHOT",),
        ),
        ReportSection(
            section_id="conclusions-next-tests",
            title="Conclusions and next decisive tests",
            lead=(
                "The evidence supports a constrained developmental claim about scorer "
                "predictability at fixed lexical effort. It does not yet support a "
                "single normative efficiency optimum or a general claim about "
                "communicative success."
            ),
            statements=(
                statement(
                    "PENDING",
                    ("WORD_NONPBM58_CONFIRMATION",),
                    (
                        "First, complete and audit the remaining-child same-pass word "
                        "scores, then apply the already frozen word protocol."
                    ),
                ),
                statement(
                    "PENDING",
                    ("CONVERSATIONAL_MANUAL_VALIDATION",),
                    (
                        "Second, finish blinded manual validation before promoting a "
                        "caregiver-responsive conversational sample."
                    ),
                ),
                statement(
                    "PENDING",
                    ("LISTENER_UTILITY_OUTCOME",),
                    (
                        "Third, define and validate a downstream caregiver-response, "
                        "repair, clarification, acknowledgement, or contingency outcome."
                    ),
                ),
                statement(
                    "PENDING",
                    ("DECOUPLED_RESPONSE_CALIBRATION",),
                    (
                        "Fourth, calibrate response uncertainty semantically and across "
                        "generation settings, including a decoupled generator."
                    ),
                ),
                statement(
                    "PENDING",
                    ("ALTERNATIVE_EFFORT_ONSET",),
                    (
                        "Finally, repeat the frozen sustained-onset rule only after the "
                        "alternative effort measures pass validation."
                    ),
                ),
            ),
            source_page_ids=(
                "PAGE_RESOURCE_CHILD_TRAJECTORIES",
                "PAGE_RESOURCE_TECHNICAL_ANALYSIS_INVENTORY",
            ),
        ),
    )

    if tuple(section.title for section in sections) != REQUIRED_SECTION_TITLES:
        raise ContractError("required report section order changed")
    resolved_claims = {
        claim_id
        for section in sections
        for item in section.statements
        for claim_id in item.claim_ids
    }
    if resolved_claims != set(evidence.claims):
        raise ContractError(
            "section claim resolution mismatch; "
            f"missing={sorted(set(evidence.claims) - resolved_claims)}, "
            f"extra={sorted(resolved_claims - set(evidence.claims))}"
        )
    referenced_figures = {
        figure_id for section in sections for figure_id in section.figure_ids
    }
    if referenced_figures != set(evidence.figures):
        raise ContractError("report figure reference coverage changed")
    referenced_pages = {
        page_id for section in sections for page_id in section.source_page_ids
    }
    if referenced_pages != set(REQUIRED_READY_PAGE_IDS):
        raise ContractError("report source-link coverage changed")
    return sections
