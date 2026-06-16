#!/usr/bin/env python3
"""Corrected Route 1 baseline-atlas scaffolding and smoke fitting.

This module is intentionally separate from the older M1-M6 report builders.
It encodes the corrected Route 1 plan:

* one target source at a time;
* one effort unit at a time;
* hierarchical interactions;
* child-identity structures as labeled alternatives, not redundant controls.

The default CLI stage writes manifests only. Use bounded smoke inputs before
launching full-data fits.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Gaussian

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from build_m1_m2_utterance_information_deep_dive import DEFAULT_INPUT, EFFORT_MEASURES
    from build_route1_analysis_dataset import count_effort
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_m1_m2_utterance_information_deep_dive import DEFAULT_INPUT, EFFORT_MEASURES
    from src.build_route1_analysis_dataset import count_effort


DEFAULT_OUTPUT_DIR = Path("results/route1_corrected_baseline_atlas")
DEFAULT_CONTEXT_KS = ("k1", "k2", "k3")
DEFAULT_BASE_TARGET_SOURCES = ("real", "random", "unigram", "bigram", "trigram")
DEFAULT_LSTM_TARGET_SOURCES = (
    "lstm_additive_k3_same_length",
    "lstm_additive_k4_same_length",
    "lstm_additive_k5_same_length",
)
DEFAULT_TARGET_SOURCES = (*DEFAULT_BASE_TARGET_SOURCES, *DEFAULT_LSTM_TARGET_SOURCES)
TARGET_SOURCE_ORDER = {
    "real": 0,
    "random": 1,
    "unigram": 2,
    "bigram": 3,
    "trigram": 4,
    "lstm_additive_k3_same_length": 10,
    "lstm_additive_k4_same_length": 11,
    "lstm_additive_k5_same_length": 12,
}
QUESTION_TYPE_ORDER = ("empty/no context", "not question", "wh-question", "yes/no question", "other question")
CORE_MODEL_IDS = ("M1", "M2", "M3", "M4a", "M4b", "M4c", "M5", "M6")
EXTENDED_MODEL_IDS = ("M7", "M8", "M9", "M10", "M11", "M12", "M13", "M14", "M15")
DEFAULT_MODEL_IDS = (*CORE_MODEL_IDS, *EXTENDED_MODEL_IDS)


@dataclass(frozen=True)
class EffortSpec:
    """One target-effort unit and its matched parent-context effort column."""

    effort_col: str
    effort_label: str
    parent_context_col: str


@dataclass(frozen=True)
class ModelFamily:
    """One corrected Route 1 scientific model family."""

    model_id: str
    label: str
    question: str
    tier: str = "core"
    needs_parent_context_effort: bool = False
    needs_context_entropy: bool = False
    needs_question_type: bool = False
    includes_age_effort_interaction: bool = False
    includes_context_entropy_interactions: bool = False
    includes_age_quadratic: bool = False
    includes_quadratic_age_effort_interaction: bool = False
    uses_age_bin: bool = False
    includes_age_bin_effort_interaction: bool = False
    includes_age_parent_context_effort_interaction: bool = False
    includes_effort_parent_context_effort_interaction: bool = False
    includes_age_question_type_interaction: bool = False
    includes_context_entropy_question_type_interaction: bool = False
    includes_parent_context_entropy_interaction: bool = False
    include_in_child_structure_sensitivity: bool = True


@dataclass(frozen=True)
class ChildStructure:
    """One child-identity/correlation structure."""

    structure_id: str
    label: str
    estimator: str
    covariance: str
    formula_note: str
    random_effects: str = ""
    primary_for_ladder: bool = False


@dataclass(frozen=True)
class CorrectedModelSpec:
    """One concrete corrected Route 1 model to fit."""

    model_id: str
    model_label: str
    question: str
    model_tier: str
    target_source: str
    context_k: str
    effort_col: str
    effort_label: str
    parent_context_col: str
    child_structure: str
    estimator: str
    covariance: str
    random_effects: str
    readable_formula: str
    statsmodels_formula: str
    needs_parent_context_effort: bool
    needs_context_entropy: bool
    needs_question_type: bool
    uses_age_bin: bool
    stage: str


EFFORT_SPECS = tuple(
    EffortSpec(
        effort_col=effort_col,
        effort_label=effort_label,
        parent_context_col=f"parent_context_{effort_col}",
    )
    for effort_col, effort_label in EFFORT_MEASURES
)

MODEL_FAMILIES = (
    ModelFamily(
        model_id="M1",
        label="Pooled age and effort",
        question="Does age predict target information after controlling target effort, pooling children?",
    ),
    ModelFamily(
        model_id="M2",
        label="Age and effort with child identity",
        question="Does the age effect remain after child identity is controlled?",
    ),
    ModelFamily(
        model_id="M3",
        label="Age by effort",
        question="Does the effort-information relation change with age?",
        includes_age_effort_interaction=True,
    ),
    ModelFamily(
        model_id="M4a",
        label="Parent-context effort added",
        question="Does preceding caretaker effort explain additional target information?",
        needs_parent_context_effort=True,
        includes_age_effort_interaction=True,
    ),
    ModelFamily(
        model_id="M4b",
        label="Context entropy added",
        question="Does context entropy explain additional target information?",
        needs_context_entropy=True,
        includes_age_effort_interaction=True,
    ),
    ModelFamily(
        model_id="M4c",
        label="Question type added",
        question="Does preceding caretaker question type explain additional target information?",
        needs_question_type=True,
        includes_age_effort_interaction=True,
    ),
    ModelFamily(
        model_id="M5",
        label="All context controls",
        question="Do parent effort, context entropy, and question type each matter after age, target effort, and child identity?",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
    ),
    ModelFamily(
        model_id="M6",
        label="Context entropy interactions",
        question="Does context-entropy sensitivity change with age or target effort?",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
        includes_context_entropy_interactions=True,
    ),
    ModelFamily(
        model_id="M7",
        label="Nonlinear age",
        question="Does a curved age trajectory explain target information beyond linear age and effort?",
        tier="extended",
        includes_age_quadratic=True,
        include_in_child_structure_sensitivity=False,
    ),
    ModelFamily(
        model_id="M8",
        label="Nonlinear age by effort",
        question="Does the effort-information relation change along a curved age trajectory?",
        tier="extended",
        includes_age_effort_interaction=True,
        includes_age_quadratic=True,
        includes_quadratic_age_effort_interaction=True,
        include_in_child_structure_sensitivity=False,
    ),
    ModelFamily(
        model_id="M9",
        label="Categorical age-bin trajectory",
        question="Do age-bin differences remain after target effort and child identity are controlled?",
        tier="extended",
        uses_age_bin=True,
        include_in_child_structure_sensitivity=False,
    ),
    ModelFamily(
        model_id="M10",
        label="Age-bin by effort",
        question="Does the effort-information relation differ across developmental age bins?",
        tier="extended",
        uses_age_bin=True,
        includes_age_bin_effort_interaction=True,
        include_in_child_structure_sensitivity=False,
    ),
    ModelFamily(
        model_id="M11",
        label="Age by parent-context effort",
        question="Does preceding caretaker effort matter differently across development?",
        tier="extended",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
        includes_age_parent_context_effort_interaction=True,
        include_in_child_structure_sensitivity=False,
    ),
    ModelFamily(
        model_id="M12",
        label="Age by question type",
        question="Does the developmental trajectory differ by broad preceding caretaker question type?",
        tier="extended",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
        includes_age_question_type_interaction=True,
        include_in_child_structure_sensitivity=False,
    ),
    ModelFamily(
        model_id="M13",
        label="Context entropy by question type",
        question="Does context entropy matter differently after different broad caretaker question types?",
        tier="extended",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
        includes_context_entropy_question_type_interaction=True,
        include_in_child_structure_sensitivity=False,
    ),
    ModelFamily(
        model_id="M14",
        label="Parent effort by context entropy",
        question="Do context entropy and preceding caretaker effort jointly predict target information?",
        tier="extended",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
        includes_parent_context_entropy_interaction=True,
        include_in_child_structure_sensitivity=False,
    ),
    ModelFamily(
        model_id="M15",
        label="Expanded context interaction stress test",
        question="Do the main context controls alter the age-effort trajectory under a larger interaction stress test?",
        tier="extended",
        needs_parent_context_effort=True,
        needs_context_entropy=True,
        needs_question_type=True,
        includes_age_effort_interaction=True,
        includes_context_entropy_interactions=True,
        includes_age_parent_context_effort_interaction=True,
        includes_effort_parent_context_effort_interaction=True,
        includes_context_entropy_question_type_interaction=True,
        include_in_child_structure_sensitivity=False,
    ),
)

CHILD_STRUCTURES = (
    ChildStructure(
        structure_id="CS0",
        label="Pooled OLS",
        estimator="ols",
        covariance="nonrobust",
        formula_note="no child identity control",
    ),
    ChildStructure(
        structure_id="CS0c",
        label="Pooled OLS, child-clustered SE",
        estimator="ols",
        covariance="cluster_child",
        formula_note="same fitted mean as CS0, uncertainty clustered by child",
        primary_for_ladder=True,
    ),
    ChildStructure(
        structure_id="CS1",
        label="Child fixed intercepts",
        estimator="ols",
        covariance="cluster_child",
        formula_note="add C(child_id)",
        primary_for_ladder=True,
    ),
    ChildStructure(
        structure_id="CS2",
        label="Child fixed intercepts and age slopes",
        estimator="ols",
        covariance="cluster_child",
        formula_note="add C(child_id) + age_c:C(child_id)",
    ),
    ChildStructure(
        structure_id="CS3",
        label="GEE grouped by child",
        estimator="gee_gaussian",
        covariance="robust",
        formula_note="population-average model grouped by child, no child fixed intercept",
    ),
    ChildStructure(
        structure_id="CS4",
        label="Random child intercept",
        estimator="mixedlm",
        covariance="model_based",
        formula_note="no child fixed intercept",
        random_effects="1",
    ),
    ChildStructure(
        structure_id="CS5",
        label="Random child intercept and age slope",
        estimator="mixedlm",
        covariance="model_based",
        formula_note="no child fixed intercept",
        random_effects="~age_c",
    ),
    ChildStructure(
        structure_id="CS6",
        label="Fixed-effect within-child age",
        estimator="ols",
        covariance="cluster_child",
        formula_note="use age_within_child_c with C(child_id)",
    ),
    ChildStructure(
        structure_id="CS7",
        label="Mundlak within/between age",
        estimator="ols",
        covariance="cluster_child",
        formula_note="use age_within_child_c + child_mean_age_c, no C(child_id)",
    ),
)


def model_family(model_id: str) -> ModelFamily:
    """Return a model-family definition by id."""

    for family in MODEL_FAMILIES:
        if family.model_id == model_id:
            return family
    raise KeyError(f"unknown model family: {model_id}")


def child_structure(structure_id: str) -> ChildStructure:
    """Return a child-structure definition by id."""

    for structure in CHILD_STRUCTURES:
        if structure.structure_id == structure_id:
            return structure
    raise KeyError(f"unknown child structure: {structure_id}")


def ordered_target_sources(values: Iterable[object]) -> list[str]:
    """Return target sources in the canonical real/random/ngram/LSTM order."""

    seen = {str(value) for value in values if str(value)}
    return sorted(seen, key=lambda value: (TARGET_SOURCE_ORDER.get(value, 50), value))


def primary_child_structure_for_model(model_id: str) -> str:
    """Return the primary corrected-ladder child structure for a model id."""

    return "CS0c" if model_id == "M1" else "CS1"


def question_type(text: object) -> str:
    """Classify a preceding caretaker context into broad question categories."""

    clean = ("" if text is None else str(text)).strip().lower()
    if not clean:
        return "empty/no context"
    tokens = clean.split()
    starts = tokens[0].strip("¿¡.,!?;:\"'()[]{}") if tokens else ""
    wh_words = {"what", "where", "who", "why", "how", "when", "which", "whose", "whom"}
    yesno_starts = {
        "are",
        "am",
        "is",
        "was",
        "were",
        "do",
        "does",
        "did",
        "can",
        "could",
        "will",
        "would",
        "should",
        "shall",
        "have",
        "has",
        "had",
    }
    if "?" not in clean:
        return "not question"
    if starts in wh_words:
        return "wh-question"
    if starts in yesno_starts:
        return "yes/no question"
    return "other question"


def context_effort_row(text: object) -> dict[str, int]:
    """Return matched effort counts for one caretaker-context text."""

    counts = count_effort(text)
    return {
        "parent_context_nb_words": counts.nb_words,
        "parent_context_nb_morphemes": counts.nb_morphemes,
        "parent_context_nb_syllables_cmu_or_pkg": counts.nb_syllables_cmu_or_pkg,
        "parent_context_nb_syllables_pkg": counts.nb_syllables_pkg,
        "parent_context_nb_phonemes": counts.nb_phonemes,
    }


def add_corrected_predictors(frame: pd.DataFrame) -> pd.DataFrame:
    """Add target-source aliases, parent-context efforts, and question type."""

    out = frame.copy()
    if "target_source" not in out.columns:
        out["target_source"] = out.get("target_variant", "").astype(str)
    if "question_type" not in out.columns:
        out["question_type"] = out.get("context_text", "").map(question_type)
    out["question_type"] = pd.Categorical(
        out["question_type"].astype(str),
        categories=QUESTION_TYPE_ORDER,
        ordered=False,
    )
    context_series = out.get("context_text", pd.Series("", index=out.index)).fillna("").astype(str)
    unique_counts = {text: context_effort_row(text) for text in sorted(context_series.unique())}
    for col in [spec.parent_context_col for spec in EFFORT_SPECS]:
        out[col] = context_series.map(lambda text, column=col: unique_counts[text][column])
    if "context_size" not in out.columns:
        out["context_size"] = out["parent_context_nb_words"]
    return out


def base_rhs_terms(family: ModelFamily, *, age_term: str) -> list[str]:
    """Return hierarchical RHS terms before child-structure additions."""

    if family.uses_age_bin:
        terms: list[str] = (
            ["C(age_bin) * effort_c"]
            if family.includes_age_bin_effort_interaction
            else ["C(age_bin)", "effort_c"]
        )
    elif family.includes_age_effort_interaction:
        terms = [f"{age_term} * effort_c"]
    else:
        terms = [age_term, "effort_c"]
    if family.includes_age_quadratic:
        terms.append(f"I({age_term} ** 2)")
    if family.includes_quadratic_age_effort_interaction:
        terms.append(f"I({age_term} ** 2):effort_c")
    if family.needs_parent_context_effort:
        terms.append("parent_context_effort_c")
    if family.needs_context_entropy:
        terms.append("context_entropy_c")
    if family.needs_question_type:
        terms.append("C(question_type)")
    if family.includes_context_entropy_interactions:
        terms.extend([f"{age_term}:context_entropy_c", "effort_c:context_entropy_c"])
    if family.includes_age_parent_context_effort_interaction:
        terms.append(f"{age_term}:parent_context_effort_c")
    if family.includes_effort_parent_context_effort_interaction:
        terms.append("effort_c:parent_context_effort_c")
    if family.includes_age_question_type_interaction:
        terms.append(f"{age_term}:C(question_type)")
    if family.includes_context_entropy_question_type_interaction:
        terms.append("context_entropy_c:C(question_type)")
    if family.includes_parent_context_entropy_interaction:
        terms.append("parent_context_effort_c:context_entropy_c")
    return terms


def formula_for(family: ModelFamily, structure: ChildStructure) -> str:
    """Build a hierarchical statsmodels formula for one family/structure."""

    age_term = "age_within_child_c" if structure.structure_id in {"CS6", "CS7"} else "age_c"
    rhs_terms = base_rhs_terms(family, age_term=age_term)
    if structure.structure_id in {"CS1", "CS2"}:
        rhs_terms.append("C(child_id)")
    if structure.structure_id == "CS2":
        rhs_terms.append("age_c:C(child_id)")
    if structure.structure_id == "CS6":
        rhs_terms.append("C(child_id)")
    if structure.structure_id == "CS7":
        rhs_terms.append("child_mean_age_c")
    return "sum_bits ~ " + " + ".join(rhs_terms)


def readable_formula_for(family: ModelFamily, structure: ChildStructure) -> str:
    """Return a compact human-readable formula."""

    formula = formula_for(family, structure)
    return (
        formula.replace("age_within_child_c", "age_within_child")
        .replace("child_mean_age_c", "child_mean_age")
        .replace("age_c", "age")
        .replace("effort_c", "effort")
        .replace("context_entropy_c", "context_entropy")
        .replace("parent_context_effort_c", "parent_context_effort")
    )


def build_model_spec(
    *,
    family: ModelFamily,
    effort: EffortSpec,
    target_source: str,
    context_k: str,
    structure: ChildStructure,
    stage: str,
) -> CorrectedModelSpec:
    """Build one concrete model spec."""

    return CorrectedModelSpec(
        model_id=family.model_id,
        model_label=family.label,
        question=family.question,
        model_tier=family.tier,
        target_source=target_source,
        context_k=context_k,
        effort_col=effort.effort_col,
        effort_label=effort.effort_label,
        parent_context_col=effort.parent_context_col,
        child_structure=structure.structure_id,
        estimator=structure.estimator,
        covariance=structure.covariance,
        random_effects=structure.random_effects,
        readable_formula=readable_formula_for(family, structure),
        statsmodels_formula=formula_for(family, structure),
        needs_parent_context_effort=family.needs_parent_context_effort,
        needs_context_entropy=family.needs_context_entropy,
        needs_question_type=family.needs_question_type,
        uses_age_bin=family.uses_age_bin,
        stage=stage,
    )


def build_primary_manifest(
    *,
    target_sources: Sequence[str] = DEFAULT_TARGET_SOURCES,
    context_ks: Sequence[str] = DEFAULT_CONTEXT_KS,
    effort_specs: Sequence[EffortSpec] = EFFORT_SPECS,
) -> pd.DataFrame:
    """Build the source-specific primary corrected-atlas manifest."""

    rows: list[dict[str, object]] = []
    for target_source in target_sources:
        for context_k in context_ks:
            for effort in effort_specs:
                for family in MODEL_FAMILIES:
                    structure = child_structure(primary_child_structure_for_model(family.model_id))
                    rows.append(
                        asdict(
                            build_model_spec(
                                family=family,
                                effort=effort,
                                target_source=target_source,
                                context_k=context_k,
                                structure=structure,
                                stage="source_specific_primary",
                            )
                        )
                    )
    return pd.DataFrame(rows)


def build_child_structure_manifest(
    *,
    target_sources: Sequence[str] = ("real",),
    context_ks: Sequence[str] = ("k3",),
    effort_specs: Sequence[EffortSpec] = (EFFORT_SPECS[0],),
) -> pd.DataFrame:
    """Build the child-structure sensitivity manifest."""

    rows: list[dict[str, object]] = []
    for target_source in target_sources:
        for context_k in context_ks:
            for effort in effort_specs:
                for family in MODEL_FAMILIES:
                    if not family.include_in_child_structure_sensitivity:
                        continue
                    for structure in CHILD_STRUCTURES:
                        rows.append(
                            asdict(
                                build_model_spec(
                                    family=family,
                                    effort=effort,
                                    target_source=target_source,
                                    context_k=context_k,
                                    structure=structure,
                                    stage="child_structure_sensitivity",
                                )
                            )
                        )
    return pd.DataFrame(rows)


def selected_model_families(model_ids: Sequence[str]) -> list[ModelFamily]:
    """Return model families selected by ids or tier aliases."""

    requested = set(model_ids)
    if not requested or requested == {"all"}:
        return list(MODEL_FAMILIES)
    if requested == {"core"}:
        requested = set(CORE_MODEL_IDS)
    elif requested == {"extended"}:
        requested = set(EXTENDED_MODEL_IDS)
    families = [family for family in MODEL_FAMILIES if family.model_id in requested]
    missing = requested - {family.model_id for family in families}
    if missing:
        raise ValueError(f"unknown model ids: {sorted(missing)}")
    return families


def selected_effort_specs(effort_cols: Sequence[str]) -> list[EffortSpec]:
    """Return effort specs selected by column names or 'all'."""

    if not effort_cols or set(effort_cols) == {"all"}:
        return list(EFFORT_SPECS)
    lookup = {spec.effort_col: spec for spec in EFFORT_SPECS}
    missing = set(effort_cols) - set(lookup)
    if missing:
        raise ValueError(f"unknown effort columns: {sorted(missing)}")
    return [lookup[col] for col in effort_cols]


def concrete_specs(
    *,
    target_sources: Sequence[str],
    context_ks: Sequence[str],
    effort_specs: Sequence[EffortSpec],
    model_ids: Sequence[str],
    child_structures: Sequence[str],
    stage: str,
) -> list[CorrectedModelSpec]:
    """Build concrete model specs from CLI-style selections."""

    families = selected_model_families(model_ids)
    use_primary = not child_structures or set(child_structures) == {"primary"}
    specs: list[CorrectedModelSpec] = []
    for target_source in target_sources:
        for context_k in context_ks:
            for effort in effort_specs:
                for family in families:
                    structure_ids = [primary_child_structure_for_model(family.model_id)] if use_primary else list(child_structures)
                    for structure_id in structure_ids:
                        specs.append(
                            build_model_spec(
                                family=family,
                                effort=effort,
                                target_source=target_source,
                                context_k=context_k,
                                structure=child_structure(structure_id),
                                stage=stage,
                            )
                        )
    return specs


def slugify(value: str) -> str:
    """Return a safe filename slug."""

    return "".join(char if char.isalnum() else "_" for char in value.lower()).strip("_")


def build_report_plan(
    *,
    output_dir: Path,
    target_sources: Sequence[str] = DEFAULT_TARGET_SOURCES,
    context_ks: Sequence[str] = DEFAULT_CONTEXT_KS,
    effort_specs: Sequence[EffortSpec] = EFFORT_SPECS,
    model_ids: Sequence[str] = DEFAULT_MODEL_IDS,
) -> pd.DataFrame:
    """Build the expected independent report products."""

    families = selected_model_families(model_ids)
    model_count = len(context_ks) * len(effort_specs) * len(families)
    rows: list[dict[str, object]] = []
    for target_source in target_sources:
        slug = slugify(target_source)
        rows.append(
            {
                "report_type": "source_specific_atlas",
                "target_source": target_source,
                "depends_on": "source-specific fits only",
                "models_per_primary_structure": model_count,
                "model_ids": ",".join(family.model_id for family in families),
                "context_ks": ",".join(context_ks),
                "effort_cols": ",".join(spec.effort_col for spec in effort_specs),
                "markdown_path": str(output_dir / "reports" / f"{slug}_route1_corrected_atlas.md"),
                "html_path": str(output_dir / "reports" / f"{slug}_route1_corrected_atlas.html"),
            }
        )
    rows.append(
        {
            "report_type": "child_structure_sensitivity",
            "target_source": "real",
            "depends_on": "core child-structure fits",
            "models_per_primary_structure": len(CORE_MODEL_IDS) * len(EFFORT_SPECS),
            "model_ids": ",".join(CORE_MODEL_IDS),
            "context_ks": "k3",
            "effort_cols": ",".join(spec.effort_col for spec in EFFORT_SPECS),
            "markdown_path": str(output_dir / "reports" / "child_structure_sensitivity.md"),
            "html_path": str(output_dir / "reports" / "child_structure_sensitivity.html"),
        }
    )
    rows.append(
        {
            "report_type": "pooled_source_comparison",
            "target_source": ",".join(target_sources),
            "depends_on": "all source_specific_atlas reports",
            "models_per_primary_structure": len(EFFORT_SPECS),
            "model_ids": "pooled_source_age_effort_context",
            "context_ks": ",".join(context_ks),
            "effort_cols": ",".join(spec.effort_col for spec in EFFORT_SPECS),
            "markdown_path": str(output_dir / "reports" / "pooled_source_comparison.md"),
            "html_path": str(output_dir / "reports" / "pooled_source_comparison.html"),
        }
    )
    return pd.DataFrame(rows)


def needed_columns() -> set[str]:
    """Return columns used by the corrected-atlas preparer/auditor."""

    return {
        "score_id",
        "utterance_id",
        "dataset",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "role",
        "target_variant",
        "target_source",
        "context_k",
        "context_text",
        "context_entropy_bits",
        "sum_bits",
        *[spec.effort_col for spec in EFFORT_SPECS],
    }


def coerce_numeric(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Coerce selected columns to numeric when present."""

    out = frame.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def read_route1_rows(
    input_csv: Path,
    *,
    chunksize: int,
    max_rows: int | None = None,
    target_sources: Sequence[str] | None = None,
    context_ks: Sequence[str] | None = None,
    roles: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Read a bounded Route 1 long table subset."""

    parts: list[pd.DataFrame] = []
    rows_seen = 0
    usecols = needed_columns()
    wanted_sources = set(target_sources or [])
    wanted_context_ks = set(context_ks or [])
    wanted_roles = set(roles or [])
    for chunk in pd.read_csv(
        input_csv,
        usecols=lambda col: col in usecols,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    ):
        if max_rows is not None:
            remaining = max_rows - rows_seen
            if remaining <= 0:
                break
            chunk = chunk.head(remaining).copy()
        rows_seen += len(chunk)
        if "target_source" not in chunk.columns:
            chunk["target_source"] = chunk.get("target_variant", "").astype(str)
        if wanted_sources:
            chunk = chunk[chunk["target_source"].isin(wanted_sources)].copy()
        if wanted_context_ks:
            chunk = chunk[chunk["context_k"].isin(wanted_context_ks)].copy()
        if wanted_roles:
            chunk = chunk[chunk["role"].isin(wanted_roles)].copy()
        if chunk.empty:
            continue
        parts.append(chunk)
    if not parts:
        return pd.DataFrame(columns=sorted(usecols))
    return pd.concat(parts, ignore_index=True)


def audit_source_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize source/context coverage and missingness."""

    audit_columns = [
        "target_source",
        "context_k",
        "rows",
        "children",
        "utterances",
        "sessions",
        "missing_age_rows",
        "missing_sum_bits_rows",
        "missing_context_entropy_rows",
        "blank_context_rows",
        *[f"missing_{effort.effort_col}_rows" for effort in EFFORT_SPECS],
    ]
    if frame.empty:
        return pd.DataFrame(columns=audit_columns)
    out = frame.copy()
    if "target_source" not in out.columns:
        out["target_source"] = out.get("target_variant", "").astype(str)
    out = coerce_numeric(out, ["age_months", "sum_bits", "context_entropy_bits", *[spec.effort_col for spec in EFFORT_SPECS]])
    child = out[out["role"].eq("child")].copy()
    rows: list[dict[str, object]] = []
    for (target_source, context_k), group in child.groupby(["target_source", "context_k"], dropna=False, sort=True):
        row: dict[str, object] = {
            "target_source": target_source,
            "context_k": context_k,
            "rows": int(len(group)),
            "children": int(group["child_id"].nunique()) if "child_id" in group else 0,
            "utterances": int(group["utterance_id"].nunique()) if "utterance_id" in group else 0,
            "sessions": int(group["session_id"].nunique()) if "session_id" in group else 0,
            "missing_age_rows": int(group["age_months"].isna().sum()),
            "missing_sum_bits_rows": int(group["sum_bits"].isna().sum()),
            "missing_context_entropy_rows": int(group["context_entropy_bits"].isna().sum())
            if context_k != "k0" and "context_entropy_bits" in group
            else 0,
            "blank_context_rows": int(group.get("context_text", pd.Series("", index=group.index)).astype(str).eq("").sum()),
        }
        for effort in EFFORT_SPECS:
            row[f"missing_{effort.effort_col}_rows"] = int(group[effort.effort_col].isna().sum())
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=audit_columns)
    return pd.DataFrame(rows, columns=audit_columns).sort_values(["target_source", "context_k"]).reset_index(drop=True)


def prepare_model_frame(frame: pd.DataFrame, spec: CorrectedModelSpec) -> tuple[pd.DataFrame, str]:
    """Filter and center rows for one corrected model spec."""

    data = add_corrected_predictors(frame)
    for col in ["role", "target_source", "context_k", "child_id"]:
        if col not in data.columns:
            data[col] = ""
    data = data[data["role"].eq("child") & data["target_source"].astype(str).eq(spec.target_source)]
    data = data[data["context_k"].astype(str).eq(spec.context_k)].copy()
    if data.empty:
        return data, "no rows for target source/context"

    for col in ["sum_bits", "age_months", spec.effort_col, spec.parent_context_col, "context_entropy_bits"]:
        if col not in data.columns:
            data[col] = math.nan
    numeric = ["sum_bits", "age_months", spec.effort_col, spec.parent_context_col, "context_entropy_bits"]
    data = coerce_numeric(data, numeric)
    data["effort_value"] = data[spec.effort_col]
    data["parent_context_effort_value"] = data[spec.parent_context_col]
    required = ["sum_bits", "age_months", "effort_value", "child_id"]
    if spec.uses_age_bin:
        required.append("age_bin")
    if spec.needs_parent_context_effort:
        required.append("parent_context_effort_value")
    if spec.needs_context_entropy:
        required.append("context_entropy_bits")
    if spec.needs_question_type:
        required.append("question_type")
    data = data.dropna(subset=required).copy()
    data = data[(data["sum_bits"] > 0) & (data["age_months"] > 0) & (data["effort_value"] > 0)].copy()
    if spec.needs_context_entropy:
        data = data[data["context_entropy_bits"] > 0].copy()
    if data.empty:
        return data, "no complete rows"
    if data["child_id"].nunique() < 2:
        return data, "fewer than two children"

    data["age_c"] = data["age_months"] - data["age_months"].mean()
    data["effort_c"] = data["effort_value"] - data["effort_value"].mean()
    data["parent_context_effort_c"] = (
        data["parent_context_effort_value"] - data["parent_context_effort_value"].mean()
        if spec.needs_parent_context_effort
        else 0.0
    )
    data["context_entropy_c"] = (
        data["context_entropy_bits"] - data["context_entropy_bits"].mean()
        if spec.needs_context_entropy
        else 0.0
    )
    child_mean_age = data.groupby("child_id")["age_months"].transform("mean")
    data["child_mean_age_c"] = child_mean_age - data["age_months"].mean()
    data["age_within_child_c"] = data["age_months"] - child_mean_age
    data["child_id"] = data["child_id"].astype(str)
    if "age_bin" not in data.columns:
        data["age_bin"] = ""
    data["age_bin"] = data["age_bin"].astype(str)
    data["question_type"] = pd.Categorical(data["question_type"].astype(str), categories=QUESTION_TYPE_ORDER)

    variation_problem = variation_check(data, spec)
    if variation_problem:
        return data, variation_problem
    return data.reset_index(drop=True), ""


def variation_check(frame: pd.DataFrame, spec: CorrectedModelSpec) -> str:
    """Return a reason a model should not be fit, or an empty string."""

    checks = [
        ("age_c", "age has no variation"),
        ("effort_c", "target effort has no variation"),
    ]
    if spec.needs_parent_context_effort:
        checks.append(("parent_context_effort_c", "parent context effort has no variation"))
    if spec.needs_context_entropy:
        checks.append(("context_entropy_c", "context entropy has no variation"))
    if spec.child_structure in {"CS6", "CS7"}:
        checks.append(("age_within_child_c", "within-child age has no variation"))
    for col, message in checks:
        if col in frame and pd.to_numeric(frame[col], errors="coerce").std(ddof=0) <= 0:
            return message
    if spec.uses_age_bin and frame["age_bin"].nunique(dropna=True) < 2:
        return "age bin has fewer than two levels"
    return ""


def fit_prepared_model(model_frame: pd.DataFrame, spec: CorrectedModelSpec) -> tuple[object | None, str]:
    """Fit one prepared model frame according to its child structure."""

    try:
        if spec.estimator == "ols":
            result = smf.ols(spec.statsmodels_formula, data=model_frame).fit()
            if spec.covariance == "cluster_child":
                result = result.get_robustcov_results(cov_type="cluster", groups=model_frame["child_id"])
            return result, ""
        if spec.estimator == "gee_gaussian":
            return (
                smf.gee(
                    spec.statsmodels_formula,
                    groups="child_id",
                    data=model_frame,
                    cov_struct=Exchangeable(),
                    family=Gaussian(),
                ).fit(),
                "",
            )
        if spec.estimator == "mixedlm":
            return (
                smf.mixedlm(
                    spec.statsmodels_formula,
                    data=model_frame,
                    groups=model_frame["child_id"],
                    re_formula=spec.random_effects or "1",
                ).fit(reml=False, method="lbfgs", disp=False),
                "",
            )
    except Exception as exc:  # pragma: no cover - real-data guard
        return None, f"{type(exc).__name__}: {exc}"
    return None, f"unknown estimator: {spec.estimator}"


def result_metric(result: object | None, attr: str) -> float:
    """Read a scalar metric from a fitted result."""

    if result is None or not hasattr(result, attr):
        return math.nan
    try:
        return float(getattr(result, attr))
    except Exception:
        return math.nan


def fit_spec_row(frame: pd.DataFrame, spec: CorrectedModelSpec) -> dict[str, object]:
    """Fit one spec and return a compact summary row."""

    model_frame, prepare_error = prepare_model_frame(frame, spec)
    summary = asdict(spec)
    summary.update(
        {
            "n_obs": int(len(model_frame)),
            "n_children": int(model_frame["child_id"].nunique()) if "child_id" in model_frame else 0,
            "status": "skipped" if prepare_error else "fit",
            "error": prepare_error,
            "r2": math.nan,
            "aic": math.nan,
            "bic": math.nan,
        }
    )
    if prepare_error:
        return summary
    result, fit_error = fit_prepared_model(model_frame, spec)
    if fit_error:
        summary["status"] = "failed"
        summary["error"] = fit_error
        return summary
    summary["r2"] = result_metric(result, "rsquared")
    summary["aic"] = result_metric(result, "aic")
    summary["bic"] = result_metric(result, "bic")
    return summary


def run_smoke_fits(
    *,
    input_csv: Path,
    output_dir: Path,
    max_rows: int,
    target_sources: Sequence[str],
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    child_structures: Sequence[str],
    model_ids: Sequence[str],
    chunksize: int,
) -> pd.DataFrame:
    """Run bounded smoke fits and write a compact summary."""

    frame = read_route1_rows(
        input_csv,
        chunksize=chunksize,
        max_rows=max_rows,
        target_sources=target_sources,
        context_ks=context_ks,
        roles=("child",),
    )
    source_values = ordered_target_sources(frame.get("target_variant", pd.Series(dtype=str)).unique())
    target_sources = [source for source in target_sources if source in source_values]
    specs = concrete_specs(
        target_sources=target_sources,
        context_ks=context_ks,
        effort_specs=selected_effort_specs(effort_cols),
        model_ids=model_ids,
        child_structures=child_structures,
        stage="bounded_smoke_fit",
    )
    rows = [fit_spec_row(frame, spec) for spec in specs]
    summary = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_dir / "smoke_fit_summary.csv", index=False)
    return summary


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 40) -> str:
    """Render a compact Markdown table."""

    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    header = "| " + " | ".join(str(col) for col in shown.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(shown.columns)) + " |"
    rows = [
        "| " + " | ".join("" if pd.isna(value) else str(value).replace("\n", " ") for value in row) + " |"
        for row in shown.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def write_source_report(summary: pd.DataFrame, path: Path, *, target_source: str) -> None:
    """Write a technical Markdown summary for one source-specific atlas."""

    path.parent.mkdir(parents=True, exist_ok=True)
    status = (
        summary.groupby(["model_tier", "status"], dropna=False)
        .size()
        .reset_index(name="rows")
        .sort_values(["model_tier", "status"])
        if not summary.empty
        else pd.DataFrame(columns=["model_tier", "status", "rows"])
    )
    formula_cols = [
        "model_id",
        "model_label",
        "model_tier",
        "context_k",
        "effort_label",
        "child_structure",
        "readable_formula",
        "status",
        "n_obs",
        "n_children",
        "error",
    ]
    shown = summary[[col for col in formula_cols if col in summary.columns]].copy() if not summary.empty else pd.DataFrame()
    lines = [
        f"# Corrected Route 1 Atlas: {target_source}",
        "",
        "This is a source-specific technical atlas. It should be interpreted before any pooled source-comparison model.",
        "",
        "## Status Counts",
        "",
        markdown_table(status),
        "",
        "## Model Rows",
        "",
        markdown_table(shown, max_rows=120),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_fit_atlas(
    *,
    input_csv: Path,
    output_dir: Path,
    target_sources: Sequence[str],
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    child_structures: Sequence[str],
    model_ids: Sequence[str],
    chunksize: int,
    max_rows: int | None,
) -> pd.DataFrame:
    """Fit selected source-specific atlas models, one target source at a time."""

    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = output_dir / "reports"
    all_parts: list[pd.DataFrame] = []
    effort_specs = selected_effort_specs(effort_cols)
    for target_source in target_sources:
        frame = read_route1_rows(
            input_csv,
            chunksize=chunksize,
            max_rows=max_rows,
            target_sources=(target_source,),
            context_ks=context_ks,
            roles=("child",),
        )
        specs = concrete_specs(
            target_sources=(target_source,),
            context_ks=context_ks,
            effort_specs=effort_specs,
            model_ids=model_ids,
            child_structures=child_structures,
            stage="source_specific_fit",
        )
        rows = [fit_spec_row(frame, spec) for spec in specs]
        source_summary = pd.DataFrame(rows)
        source_summary.to_csv(output_dir / f"{slugify(target_source)}_model_summary.csv", index=False)
        write_source_report(
            source_summary,
            reports_dir / f"{slugify(target_source)}_route1_corrected_atlas.md",
            target_source=target_source,
        )
        all_parts.append(source_summary)
    summary = pd.concat(all_parts, ignore_index=True) if all_parts else pd.DataFrame()
    summary.to_csv(output_dir / "source_specific_model_summary.csv", index=False)
    return summary


def write_manifests(output_dir: Path) -> Mapping[str, Path]:
    """Write primary and sensitivity manifests."""

    output_dir.mkdir(parents=True, exist_ok=True)
    primary = build_primary_manifest()
    sensitivity = build_child_structure_manifest()
    report_plan = build_report_plan(output_dir=output_dir)
    child_structures = pd.DataFrame([asdict(structure) for structure in CHILD_STRUCTURES])
    families = pd.DataFrame([asdict(family) for family in MODEL_FAMILIES])
    paths = {
        "primary_manifest": output_dir / "corrected_primary_source_specific_manifest.csv",
        "child_structure_manifest": output_dir / "corrected_child_structure_sensitivity_manifest.csv",
        "report_plan": output_dir / "corrected_report_plan.csv",
        "child_structures": output_dir / "child_structure_definitions.csv",
        "model_families": output_dir / "corrected_model_family_definitions.csv",
        "launch_commands": output_dir / "FULL_RUN_COMMANDS.md",
    }
    primary.to_csv(paths["primary_manifest"], index=False)
    sensitivity.to_csv(paths["child_structure_manifest"], index=False)
    report_plan.to_csv(paths["report_plan"], index=False)
    child_structures.to_csv(paths["child_structures"], index=False)
    families.to_csv(paths["model_families"], index=False)
    write_launch_commands(paths["launch_commands"])
    return paths


def write_launch_commands(path: Path) -> None:
    """Write the recommended full-run command sequence."""

    path.parent.mkdir(parents=True, exist_ok=True)
    text = """# Corrected Route 1 Full-Run Commands

Do not run these casually. They rebuild the long Route 1 modeling frame, fit
the corrected source-specific atlas, and then fit child-structure sensitivity
models separately. Run the preflight first and inspect audits before the full
fit.

## 1. Rebuild The Unified Long Table

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_analysis_dataset.py \\
  --score-root pbm_mistral_patched_006_023=results/external/compute_surprisal_mila/raw_surprisal_cleaned_mistral_patched_006_023 \\
  --score-root lstm_additive_same_length=results/external/compute_surprisal_mila/raw_surprisal_lstm_additive_same_length \\
  --output-csv results/route1_analysis_dataset/route1_scored_utterance_effort_with_lstm_long.csv.gz \\
  --file-audit-csv results/route1_analysis_dataset/with_lstm_source_file_audit.csv \\
  --variant-audit-csv results/route1_analysis_dataset/with_lstm_variant_context_audit.csv \\
  --schema-json results/route1_analysis_dataset/with_lstm_schema.json
```

## 2. Attach Context Entropy

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/attach_context_entropy_to_route1_dataset.py \\
  --input-csv results/route1_analysis_dataset/route1_scored_utterance_effort_with_lstm_long.csv.gz \\
  --output-csv results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz \\
  --audit-csv results/route1_analysis_dataset/with_lstm_context_entropy_join_audit.csv \\
  --allow-missing-child-contexts
```

## 3. Preflight The Corrected Atlas

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_corrected_baseline_atlas.py \\
  --stage preflight \\
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz \\
  --output-dir results/route1_corrected_baseline_atlas/full_preflight \\
  --target-sources real,random,unigram,bigram,trigram,lstm_additive_k3_same_length,lstm_additive_k4_same_length,lstm_additive_k5_same_length \\
  --context-ks k1,k2,k3 \\
  --effort-cols all \\
  --model-ids all \\
  --max-rows 0 \\
  --chunksize 250000
```

## 4. Full Source-Specific Atlas Fit

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_corrected_baseline_atlas.py \\
  --stage fit-atlas \\
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz \\
  --output-dir results/route1_corrected_baseline_atlas/full_source_specific \\
  --target-sources real,random,unigram,bigram,trigram,lstm_additive_k3_same_length,lstm_additive_k4_same_length,lstm_additive_k5_same_length \\
  --context-ks k1,k2,k3 \\
  --effort-cols all \\
  --child-structures primary \\
  --model-ids all \\
  --max-rows 0 \\
  --chunksize 250000
```

This command fits independent source-specific atlases. It does not replace
those atlases with a pooled comparison model.

## 5. Core Child-Structure Sensitivity Fit

```bash
MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python src/build_route1_corrected_baseline_atlas.py \\
  --stage fit-atlas \\
  --input results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz \\
  --output-dir results/route1_corrected_baseline_atlas/full_child_structure_sensitivity \\
  --target-sources real \\
  --context-ks k3 \\
  --effort-cols all \\
  --child-structures CS0,CS0c,CS1,CS2,CS3,CS4,CS5,CS6,CS7 \\
  --model-ids core \\
  --max-rows 0 \\
  --chunksize 250000
```

This command is intentionally separate from the source-specific baseline
atlases. It compares child-identity structures for real child utterances only.
"""
    path.write_text(text, encoding="utf-8")


def run_audit(
    *,
    input_csv: Path,
    output_dir: Path,
    chunksize: int,
    max_rows: int | None,
) -> pd.DataFrame:
    """Run a bounded source coverage audit."""

    frame = read_route1_rows(input_csv, chunksize=chunksize, max_rows=max_rows)
    audit = audit_source_coverage(frame)
    output_dir.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output_dir / "source_coverage_audit.csv", index=False)
    return audit


def parse_max_rows(value: int | None) -> int | None:
    """Interpret max-row values; 0 or negative means no cap."""

    if value is None or value <= 0:
        return None
    return value


def run_preflight(
    *,
    input_csv: Path,
    output_dir: Path,
    target_sources: Sequence[str],
    context_ks: Sequence[str],
    effort_cols: Sequence[str],
    model_ids: Sequence[str],
    chunksize: int,
    max_rows: int | None,
) -> Mapping[str, Path]:
    """Write manifests, report plan, commands, and a bounded source audit."""

    output_dir.mkdir(parents=True, exist_ok=True)
    effort_specs = selected_effort_specs(effort_cols)
    primary = build_primary_manifest(
        target_sources=target_sources,
        context_ks=context_ks,
        effort_specs=effort_specs,
    )
    primary = primary[primary["model_id"].isin([family.model_id for family in selected_model_families(model_ids)])].copy()
    sensitivity = build_child_structure_manifest(effort_specs=effort_specs)
    report_plan = build_report_plan(
        output_dir=output_dir,
        target_sources=target_sources,
        context_ks=context_ks,
        effort_specs=effort_specs,
        model_ids=model_ids,
    )
    frame = read_route1_rows(
        input_csv,
        chunksize=chunksize,
        max_rows=max_rows,
        target_sources=target_sources,
        context_ks=context_ks,
        roles=("child",),
    )
    audit = audit_source_coverage(frame)
    paths = {
        "primary_manifest": output_dir / "corrected_primary_source_specific_manifest.csv",
        "child_structure_manifest": output_dir / "corrected_child_structure_sensitivity_manifest.csv",
        "report_plan": output_dir / "corrected_report_plan.csv",
        "source_audit": output_dir / "source_coverage_audit.csv",
        "launch_commands": output_dir / "FULL_RUN_COMMANDS.md",
    }
    primary.to_csv(paths["primary_manifest"], index=False)
    sensitivity.to_csv(paths["child_structure_manifest"], index=False)
    report_plan.to_csv(paths["report_plan"], index=False)
    audit.to_csv(paths["source_audit"], index=False)
    write_launch_commands(paths["launch_commands"])
    return paths


def split_csv(value: str) -> list[str]:
    """Split a comma-separated CLI argument."""

    return [part.strip() for part in value.split(",") if part.strip()]


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["manifest", "audit", "preflight", "smoke-fit", "fit-atlas"], default="manifest")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--max-rows", type=int, default=50_000)
    parser.add_argument("--target-sources", default=",".join(DEFAULT_TARGET_SOURCES))
    parser.add_argument("--context-ks", default="k3")
    parser.add_argument("--effort-cols", default="nb_words")
    parser.add_argument("--child-structures", default="CS0c,CS1")
    parser.add_argument("--model-ids", default=",".join(CORE_MODEL_IDS))
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    target_sources = split_csv(args.target_sources)
    context_ks = split_csv(args.context_ks)
    effort_cols = split_csv(args.effort_cols)
    child_structures = split_csv(args.child_structures)
    model_ids = split_csv(args.model_ids)
    max_rows = parse_max_rows(args.max_rows)
    if args.stage == "manifest":
        paths = write_manifests(args.output_dir)
        for label, path in paths.items():
            print(f"[OK] {label}: {path}")
        return
    if args.stage == "audit":
        audit = run_audit(
            input_csv=args.input,
            output_dir=args.output_dir,
            chunksize=args.chunksize,
            max_rows=max_rows,
        )
        print(f"[OK] wrote source audit rows: {len(audit)}")
        print(f"[OK] source audit: {args.output_dir / 'source_coverage_audit.csv'}")
        return
    if args.stage == "preflight":
        paths = run_preflight(
            input_csv=args.input,
            output_dir=args.output_dir,
            target_sources=target_sources,
            context_ks=context_ks,
            effort_cols=effort_cols,
            model_ids=model_ids,
            chunksize=args.chunksize,
            max_rows=max_rows,
        )
        for label, path in paths.items():
            print(f"[OK] {label}: {path}")
        return
    if args.stage == "fit-atlas":
        summary = run_fit_atlas(
            input_csv=args.input,
            output_dir=args.output_dir,
            max_rows=max_rows,
            target_sources=target_sources,
            context_ks=context_ks,
            effort_cols=effort_cols,
            child_structures=child_structures,
            model_ids=model_ids,
            chunksize=args.chunksize,
        )
        print(f"[OK] wrote fit rows: {len(summary)}")
        print(f"[OK] fit summary: {args.output_dir / 'source_specific_model_summary.csv'}")
        print(f"[OK] reports: {args.output_dir / 'reports'}")
        return
    summary = run_smoke_fits(
        input_csv=args.input,
        output_dir=args.output_dir,
        max_rows=max_rows or 50_000,
        target_sources=target_sources,
        context_ks=context_ks,
        effort_cols=effort_cols,
        child_structures=child_structures,
        model_ids=model_ids,
        chunksize=args.chunksize,
    )
    print(f"[OK] wrote smoke fit rows: {len(summary)}")
    print(f"[OK] smoke summary: {args.output_dir / 'smoke_fit_summary.csv'}")


if __name__ == "__main__":
    main()
