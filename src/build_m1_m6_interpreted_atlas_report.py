#!/usr/bin/env python3
"""Build interpreted M1-M6 atlas v2 and technical companion reports.

This is a synthesis/reporting stage. It does not fit new statistical models.
It reads the saved M1-M6 model tables and figure inventories, then writes:

- docs/utterance_information_m1_m6_super_atlas_v2_interpreted.md/html
- docs/utterance_information_m1_m6_technical_implementation_companion.md/html
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

try:
    import build_m1_m6_super_atlas_report as atlas
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src import build_m1_m6_super_atlas_report as atlas
    from src.render_markdown_report import render_markdown_file


DEFAULT_OUTPUT_DIR = Path("results/m1_m6_interpreted_atlas")
DEFAULT_INTERPRETED_MD = Path("docs/utterance_information_m1_m6_super_atlas_v2_interpreted.md")
DEFAULT_INTERPRETED_HTML = Path("docs/utterance_information_m1_m6_super_atlas_v2_interpreted.html")
DEFAULT_COMPANION_MD = Path("docs/utterance_information_m1_m6_technical_implementation_companion.md")
DEFAULT_COMPANION_HTML = Path("docs/utterance_information_m1_m6_technical_implementation_companion.html")
PROJECT_EMAIL_CONTEXT = Path("docs/project_motivation_recent_email_context_2026-06-16.md")


MODEL_STATUSES = {
    "M1": {
        "evidence_role": "Baseline and confounding warning.",
        "supervisor_pick": "Use only to explain why child identity control matters.",
        "do_not_overclaim": "Do not treat the pooled age slope as the developmental result.",
    },
    "M2": {
        "evidence_role": "Primary current evidence.",
        "supervisor_pick": "Cherry-pick the continuous exact-effort M2 table, fixed-effort plots, and k3 robustness plot.",
        "do_not_overclaim": "Do not say children communicate less; say lower predicted Mistral surprisal at fixed effort within the child-adjusted comparison.",
    },
    "M3": {
        "evidence_role": "Robustness and mechanism check.",
        "supervisor_pick": "Use only if explaining whether short and long utterances have different age slopes.",
        "do_not_overclaim": "Do not make the age-by-effort interaction central unless it is stable across effort units.",
    },
    "M4": {
        "evidence_role": "Context-control robustness.",
        "supervisor_pick": "Use to say that adding the current next-token entropy predictor does not remove the M2-like age result.",
        "do_not_overclaim": "Do not treat next-token entropy as full response uncertainty.",
    },
    "M5": {
        "evidence_role": "Exploratory context-age interaction.",
        "supervisor_pick": "Usually omit from supervisor draft unless discussing why response-level entropy is needed next.",
        "do_not_overclaim": "Do not claim developmental context sensitivity from weak or unstable age-by-entropy terms.",
    },
    "M6": {
        "evidence_role": "Interaction-rich stress test.",
        "supervisor_pick": "Use as an appendix stress test if the simpler result is challenged.",
        "do_not_overclaim": "Do not interpret one coefficient from the saturated model as a clean standalone effect.",
    },
}


IMPLEMENTATION_FORMULAS = {
    "M1": {
        "readable": "sum_bits ~ age + effort",
        "centered": "sum_bits ~ age_c + target_effort_c",
        "child_role": "omitted in the fitted mean; child can be used only for clustered SE in sensitivity rows",
    },
    "M2": {
        "readable": "sum_bits ~ age + effort + child identity",
        "centered": "sum_bits ~ age_c + target_effort_c + C(child_id)",
        "child_role": "fixed intercept through C(child_id); clustered SE in primary report rows",
    },
    "M3": {
        "readable": "sum_bits ~ age * effort + child identity",
        "centered": "sum_bits ~ age_c * target_effort_c + C(child_id)",
        "child_role": "fixed intercept through C(child_id); mixed random-intercept/slope rows are sensitivity checks",
    },
    "M4": {
        "readable": "sum_bits ~ age + effort + context predictor + child identity",
        "centered": "sum_bits ~ age_c + target_effort_c + context_entropy_c + C(child_id)",
        "child_role": "fixed intercept through C(child_id); GEE rows cluster by child",
    },
    "M5": {
        "readable": "sum_bits ~ age * context predictor + effort + child identity",
        "centered": "sum_bits ~ age_c * context_entropy_c + target_effort_c + C(child_id)",
        "child_role": "fixed intercept through C(child_id)",
    },
    "M6": {
        "readable": "sum_bits ~ age * effort + age * context + effort * context + child identity",
        "centered": "sum_bits ~ age_c * target_effort_c + age_c * context_entropy_c + target_effort_c * context_entropy_c + C(child_id)",
        "child_role": "fixed intercept through C(child_id)",
    },
}


def read_tables() -> dict[str, pd.DataFrame]:
    """Read all saved tables used by the interpreted reports."""

    tables = {
        "expanded": atlas.read_optional_csv(atlas.DEEP_DIVE_DIR / "expanded_model_family_summary.csv"),
        "m4_context": atlas.read_optional_csv(atlas.DEEP_DIVE_DIR / "m4_context_entropy_model_summary.csv"),
        "saturated": atlas.read_optional_csv(atlas.DEEP_DIVE_DIR / "m5_m6_saturated_model_summary.csv"),
        "dual": atlas.read_optional_csv(atlas.DUAL_DIR / "dual_model_summary.csv"),
        "atlas_fit": atlas.read_optional_csv(atlas.FIXED_ATLAS_DIR / "atlas_model_fit_summary.csv"),
        "atlas_slopes": atlas.read_optional_csv(atlas.FIXED_ATLAS_DIR / "atlas_fixed_slice_slopes.csv"),
        "context_summary": atlas.read_optional_csv(atlas.CONTEXT_M1_M6_DIR / "context_m1_m6_model_summary.csv"),
        "context_slopes": atlas.read_optional_csv(atlas.CONTEXT_M1_M6_DIR / "context_m1_m6_slice_slopes.csv"),
        "context_fixed": atlas.read_optional_csv(atlas.CONTEXT_FIXED_DIR / "context_fixed_effort_model_summary.csv"),
        "robustness": atlas.read_optional_csv(atlas.ROBUSTNESS_DIR / "age_scrambling_robustness_summary.csv"),
        "figure_inventory": atlas.collect_figure_inventory(),
        "source_artifacts": atlas.artifact_inventory(),
    }
    return tables


def first_existing_plot(source_id: str, filename_contains: str, figure_inventory: pd.DataFrame) -> str:
    """Return Markdown for a representative plot if one exists."""

    if figure_inventory.empty:
        return ""
    sub = figure_inventory[
        figure_inventory["exists"].astype(bool)
        & figure_inventory["source_id"].eq(source_id)
        & figure_inventory["filename"].str.contains(filename_contains, case=False, na=False)
    ].copy()
    if sub.empty:
        return ""
    path = Path(str(sub.iloc[0]["path"]))
    return atlas.image_md(path, sub.iloc[0]["filename"], md_path=DEFAULT_INTERPRETED_MD)


def compact_primary_table(dual: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return continuous exact-effort rows for one model."""

    table = atlas.compact_dual_table(dual, model_id)
    if table.empty or "effort_strategy" not in table.columns:
        return table
    return table[table["effort_strategy"].eq("continuous")].copy()


def sign_summary_from_table(table: pd.DataFrame, coef_col: str = "age_coef") -> str:
    """Summarize coefficient signs in plain language."""

    if table.empty or coef_col not in table.columns:
        return "No saved coefficient rows were available for this summary."
    values = pd.to_numeric(table[coef_col], errors="coerce").dropna()
    if values.empty:
        return "The saved rows did not contain numeric coefficients for this term."
    negative = int((values < 0).sum())
    positive = int((values > 0).sum())
    zero = int((values == 0).sum())
    return f"{negative} negative, {positive} positive, and {zero} exactly zero coefficients across {len(values)} saved rows."


def short_model_interpretation(model_id: str, tables: dict[str, pd.DataFrame]) -> str:
    """Return model-specific interpretation text."""

    dual = tables["dual"]
    context_summary = tables["context_summary"]
    atlas_slopes = tables["atlas_slopes"]
    robustness = tables["robustness"]
    computed = atlas.model_takeaway(
        model_id,
        dual=dual,
        atlas_slopes=atlas_slopes,
        context_summary=context_summary,
        robustness=robustness,
    )
    base = {
        "M1": (
            "M1 deliberately pools children. Its main value is diagnostic: it shows how the apparent "
            "developmental direction can change when children and corpora occupy different age ranges. "
            "A pooled age coefficient mixes within-child change with between-child and between-corpus composition."
        ),
        "M2": (
            "M2 is the current cleanest result. It asks whether a same-child developmental trajectory remains "
            "after exact production effort is held constant. Negative age coefficients mean that, for comparable "
            "utterance size and child baseline, older children's target utterances receive lower total Mistral "
            "surprisal."
        ),
        "M3": (
            "M3 tests whether the age trend differs across effort values. The interaction term is best read "
            "through fixed-effort plots: non-parallel lines mean the age slope changes for shorter versus longer "
            "utterances."
        ),
        "M4": (
            "M4 adds the current context predictor. This is a robustness check for the utterance-information "
            "claim, not the final context-efficiency model. The current entropy feature is next-token entropy, "
            "so it only partly represents the uncertainty of a full possible response."
        ),
        "M5": (
            "M5 asks whether the relation between context entropy and target information changes with age. "
            "This is a developmental context-sensitivity question, but the current next-token entropy results "
            "should be treated as exploratory."
        ),
        "M6": (
            "M6 is a stress test with multiple interactions. It is useful if the M2 pattern survives it, but it is "
            "not the simplest explanation because the terms are highly conditional and collinearity can make "
            "single coefficients fragile."
        ),
    }[model_id]
    return f"{base}\n\nComputed atlas summary: {computed}"


def plot_family_guide() -> pd.DataFrame:
    """Return the major plot-family reading guide."""

    return pd.DataFrame(
        [
            {
                "plot family": "cross-atlas heatmaps",
                "where": "figs/m1_m6_super_atlas",
                "x/y/facets": "Rows are model variants; columns are effort units or robustness methods.",
                "lines/colors/ribbons": "Cells are colored by coefficient, R2, sign share, or outside-null share.",
                "interpretation": "Use as a map of which results are stable before opening detailed galleries.",
                "caveat": "Heatmaps compress many models; they are not a substitute for fixed-effort plots.",
            },
            {
                "plot family": "dual continuous vs effort-level plots",
                "where": "figs/m1_m6_dual_effort_quick_share",
                "x/y/facets": "x is child age; y is predicted total bits; columns are effort units; rows are effort strategy.",
                "lines/colors/ribbons": "Lines are model-predicted age trends; colors separate effort references or levels; ribbons are model confidence bands when available.",
                "interpretation": "Compare exact continuous effort control against low/mid/high effort categories.",
                "caveat": "Low/mid/high categories are coarse and can reverse signs because exact effort still varies inside a category.",
            },
            {
                "plot family": "estimator deep-dive plots",
                "where": "figs/m1_m2_utterance_information_deep_dive",
                "x/y/facets": "x is age; y is predicted total bits; panels/figures separate estimators and effort units.",
                "lines/colors/ribbons": "Lines are fitted mean predictions. OLS and child-clustered OLS can share the same line; their uncertainty differs.",
                "interpretation": "Check whether the conclusion depends on OLS, GLM, GEE, or MixedLM choices.",
                "caveat": "Gamma/log coefficients are on a log scale; use prediction plots rather than raw coefficients for intuition.",
            },
            {
                "plot family": "fixed-effort slice atlas",
                "where": "figs/m1_m6_fixed_effort_atlas",
                "x/y/facets": "x is age; y is predicted total bits; facets group exact effort values.",
                "lines/colors/ribbons": "Each colored line is one fixed effort value; shaded bands are model confidence bands for the fitted mean.",
                "interpretation": "This is the cleanest visual answer to 'what happens at the same utterance size?'",
                "caveat": "A line at a sparse effort value is less supported; inspect row-support plots.",
            },
            {
                "plot family": "context-window fixed-effort atlas",
                "where": "figs/context_m1_m6_fixed_effort_atlas",
                "x/y/facets": "x is age; y is predicted total bits; context windows k0-k3 and context variants are split across files.",
                "lines/colors/ribbons": "Colored lines are fixed effort values. Ribbons are fitted mean uncertainty.",
                "interpretation": "Check whether the age pattern survives no context, k1, k2, k3, entropy, and context-size variants.",
                "caveat": "Context entropy is next-token entropy; context size is a surface control, not semantic/pragmatic context richness.",
            },
            {
                "plot family": "age-scrambling robustness plots",
                "where": "figs/age_scrambling_robustness",
                "x/y/facets": "x is age; y is anchored predicted mean total bits or age slope.",
                "lines/colors/ribbons": "The observed line is compared with balanced-bootstrap and scrambled-age null ribbons.",
                "interpretation": "If the observed slope is outside scrambled/null ranges, true age ordering is doing real work.",
                "caveat": "These are aggregated child-session-context-unit checks; coefficients need not equal utterance-level coefficients.",
            },
            {
                "plot family": "supervisor-facing M2 simple plots",
                "where": "figs/m2_simple_plots",
                "x/y/facets": "x is age; y is predicted total bits; each plot uses one effort unit.",
                "lines/colors/ribbons": "Colored lines are exact fixed effort values; the black line is the global adjusted trend.",
                "interpretation": "Best compact plots for explaining the current primary result.",
                "caveat": "M2 has parallel fixed-effort lines because it does not include age-by-effort interaction.",
            },
        ]
    )


def proposed_models_table() -> pd.DataFrame:
    """Return proposed/not-yet-run model additions."""

    return pd.DataFrame(
        [
            {
                "proposal": "within-child centered age",
                "formula": "sum_bits ~ age_within_child + effort + C(child_id)",
                "why": "Directly estimates within-child change while preserving each child's baseline.",
                "status": "proposed/not yet run in this v2 synthesis",
            },
            {
                "proposal": "within/between age decomposition",
                "formula": "sum_bits ~ age_within_child + child_mean_age + effort + corpus",
                "why": "Separates within-child development from between-child/corpus age composition.",
                "status": "proposed/not yet run in this v2 synthesis",
            },
            {
                "proposal": "age-overlap restricted subset",
                "formula": "same as M2/M3 after restricting to age months shared by multiple children/corpora",
                "why": "Checks whether the M2 slope is driven by children who occupy unique age ranges.",
                "status": "proposed/not yet run in this v2 synthesis",
            },
            {
                "proposal": "age-bin balanced model",
                "formula": "M2/M3 on equalized age-bin samples or child-session-context units",
                "why": "Reduces leverage of dense toddler bins and follows Pawar-style stability logic.",
                "status": "partially addressed by existing age-scrambling robustness; further utterance-level version not yet run",
            },
            {
                "proposal": "corpus fixed effects",
                "formula": "sum_bits ~ age + effort + C(child_id) + C(dataset)",
                "why": "Tests whether corpus/transcription context explains part of the child-adjusted trend.",
                "status": "proposed/not yet run in this v2 synthesis",
            },
            {
                "proposal": "child random intercept plus random age slope",
                "formula": "MixedLM: sum_bits ~ age + effort, groups=child_id, re_formula='~age'",
                "why": "Allows children to have different developmental slopes and shrinks noisy child-specific estimates.",
                "status": "M2/M3 sensitivity exists; fuller overlap/balancing interpretation still proposed",
            },
            {
                "proposal": "Route 2 effort outcome bridge",
                "formula": "effort ~ age + response_entropy + expected_model_response_length + context_size + C(child_id)",
                "why": "Tests whether contextual uncertainty predicts how much children choose to say.",
                "status": "proposed; response-space entropy pilot exists but production features are not yet the primary analysis",
            },
        ]
    )


def child_identity_section() -> str:
    """Return the shared child-identity-control interpretation."""

    return """## Is Child Identity Control Too Strong?

Short answer: child identity control is appropriate and scientifically useful here, but it changes the question. It is not automatically "better" in every sense.

M1 asks a pooled question: across all rows, does age predict total information after effort control? Because children and corpora occupy different age ranges, M1 can confound development with which child, corpus, transcription style, and recording context happens to contribute data at a given age. This is why M1 is useful as a warning light rather than as the primary result.

M2 adds child fixed intercepts. That means each child receives a separate baseline level of predicted information, while the model estimates one shared age slope. In plain terms, M2 asks whether the age effect remains after removing stable child-to-child baseline differences. This is a conservative move if the target is within-child developmental change.

The worry is real: if children occupy different age ranges, child fixed effects discard between-child age composition. Some of that between-child variation may reflect meaningful developmental structure, but it is inseparable from corpus and child composition unless modeled carefully. M2 therefore answers a narrower question than "do older children in the dataset differ from younger children?" It answers "within the child-adjusted comparison, is later age associated with different target information at fixed effort?"

Child fixed effects can be too restrictive if the scientific estimand is a population developmental trajectory that legitimately includes between-child differences. They can also leave weak support where a child's age range is short or where older ages are represented by only a few children. They do not solve time-varying confounding, caregiver style changes, topic/task changes, or sparse age-bin support.

The right interpretation is therefore balanced:

- M1 is vulnerable to child/corpus composition.
- M2 is more conservative for within-child development.
- M2 can be too narrow if we also care about between-child developmental differences.
- Random slopes, within/between decomposition, age-overlap restrictions, corpus controls, age-bin balancing, and leave-one-child/corpus-out checks should be added before making a final dissertation-level causal/developmental claim.

Recommended next formulas are listed in the technical companion. None of those additions are claimed as results in this v2 report unless they already exist in saved artifacts.
"""


def read_project_email_context(path: Path | None = None) -> str:
    """Return the saved verbatim email block if available."""

    source = PROJECT_EMAIL_CONTEXT if path is None else path
    if not source.exists():
        return ""
    text = source.read_text(encoding="utf-8")
    match = re.search(r"```text\n(?P<body>.*?)\n```", text, flags=re.S)
    if match:
        return match.group("body")
    return text.strip()


def project_history_section() -> str:
    """Return project-history context including the saved email block."""

    email_block = read_project_email_context()
    if email_block:
        email_section = f"""The exact recent email context has also been saved as `{PROJECT_EMAIL_CONTEXT}` and is quoted verbatim here:

```text
{email_block}
```"""
    else:
        email_section = (
            f"The requested verbatim email context file was not found at `{PROJECT_EMAIL_CONTEXT}`. "
            "This report therefore records the project-history synthesis only and does not invent the missing email text."
        )

    return f"""## Project Motivation / Recent Email Context

The current project began from the idea that child communicative efficiency can be studied by jointly measuring informativeness and effort in naturalistic CHILDES conversations. The original November 2024 project draft framed informativeness as surprisal or likelihood, effort as utterance length/MLU-like complexity, and efficiency as a relation between the two. It also explicitly raised comparisons to caretakers, generated baselines, social variables, and clinical language data.

The current Overleaf-style draft reframes the work around developmental communicative efficiency: children may become more adult-like in balancing information content against production effort, with large language models used as one way to quantify contextual surprisal.

{email_section}
"""


def source_context_section() -> str:
    """Return a compact source-context audit for the interpreted report."""

    return """## Source Context Inspected

This synthesis was built from the current repository reports and local course/project notes, especially:

- `AGENTS.md`, `TODO.md`, and `docs/notes.md`.
- the current supervisor-facing utterance-information report;
- the original M1-M6 super atlas, M1-M2/M1-M6 deep dive, fixed-effort atlas, context fixed-effort atlas, age-scrambling robustness report, and model zoo;
- response-level context entropy and Mila generation-plan notes;
- the Pawar and Cychosz paper summary and local PDF;
- the original November 2024 project-start draft and the Overleaf-style current-paper draft from the attachment cache;
- local `school_agent` Advanced Data Analytics notes on prediction versus explanation, model selection, clustered/longitudinal data, mixed models, and correlated observations;
- local `school_agent` project notes on hypotheses, variable map, confounds/controls, and modeling strategy;
- local paper notes for the CogSci child communicative-efficiency paper and the redundant-references-with-language-learners paper.

The named `school_agent` paper notes for the CogSci and redundant-reference papers are stubs, so this document uses them for framing only. It does not invent detailed methods/results that were not present in those notes.
"""


def build_model_section(model_id: str, tables: dict[str, pd.DataFrame], md_path: Path) -> str:
    """Build one interpreted atlas model section."""

    guide = atlas.MODEL_GUIDE[model_id]
    formula = IMPLEMENTATION_FORMULAS[model_id]
    status = MODEL_STATUSES[model_id]
    dual = tables["dual"]
    expanded = tables["expanded"]
    m4_context = tables["m4_context"]
    saturated = tables["saturated"]
    context_summary = tables["context_summary"]
    robustness = tables["robustness"]
    figure_inventory = tables["figure_inventory"]

    formula_table = pd.DataFrame(
        [
            {
                "item": "scientific question",
                "value": guide["question"],
            },
            {
                "item": "readable formula",
                "value": formula["readable"],
            },
            {
                "item": "actual centered implementation",
                "value": formula["centered"],
            },
            {
                "item": "primary estimator/library",
                "value": "ordinary linear regression / OLS via statsmodels.formula.api.ols",
            },
            {
                "item": "child identity role",
                "value": formula["child_role"],
            },
            {
                "item": "evidence role",
                "value": status["evidence_role"],
            },
        ]
    )

    coeff_meanings = pd.DataFrame(
        [
            {
                "term": "age",
                "plain-language meaning": "Expected change in total target bits for one additional month, after this model's controls.",
            },
            {
                "term": "effort",
                "plain-language meaning": "Expected change in total bits for one more word/morpheme/syllable/phoneme in that model row.",
            },
            {
                "term": "age x effort",
                "plain-language meaning": "Whether the developmental age slope is different for shorter versus longer utterances.",
            },
            {
                "term": "context entropy",
                "plain-language meaning": "Association between current next-token context uncertainty and total bits in the produced target.",
            },
            {
                "term": "age x context entropy",
                "plain-language meaning": "Whether the context-entropy association changes as children get older.",
            },
            {
                "term": "effort x context entropy",
                "plain-language meaning": "Whether the effort slope differs in more uncertain versus less uncertain contexts.",
            },
            {
                "term": "effort level",
                "plain-language meaning": "Low/mid/high bins of one effort unit. These are diagnostics, not a replacement for exact fixed-effort control.",
            },
        ]
    )

    primary = compact_primary_table(dual, model_id)
    primary_summary = sign_summary_from_table(primary)
    context_table = atlas.compact_context_table(context_summary, model_id)
    robust_table = atlas.compact_robustness_table(robustness, model_id)
    figures = atlas.figures_for_model(figure_inventory, model_id)

    sections = [
        f"""## {model_id}: {guide['title']}

{short_model_interpretation(model_id, tables)}

### Formula, Estimator, And Child Structure

{atlas.markdown_table(formula_table, max_rows=10)}

### Coefficient Dictionary

{atlas.markdown_table(coeff_meanings, max_rows=10)}

Age effects in this family should be read in bits per month. Effort effects should be read in bits per one additional effort unit. Interaction terms should be read as slope changes, not as standalone main effects.

### Scientific Interpretation

Primary continuous-effort sign summary: {primary_summary}

Supervisor-facing cherry-pick: {status['supervisor_pick']}

What not to overclaim: {status['do_not_overclaim']}
"""
    ]

    if not primary.empty:
        sections.append(
            "### Primary Continuous-Effort Rows\n\n"
            "These rows are the clearest exact-effort versions for this model family. They keep words, morphemes, syllables, and phonemes in separate models to avoid collinearity.\n\n"
            + atlas.markdown_table(primary, max_rows=20)
        )

    dual_table = atlas.compact_dual_table(dual, model_id)
    if not dual_table.empty:
        sections.append(
            "### Continuous Versus Low/Mid/High Effort Rows\n\n"
            "Use these as a strategy comparison. The continuous rows control exact effort; the effort-level rows ask a coarser question about low, middle, and high effort categories.\n\n"
            + atlas.markdown_table(dual_table, max_rows=20)
        )

    expanded_table = atlas.compact_expanded_table(expanded, model_id)
    if not expanded_table.empty:
        sections.append(
            "### Estimator Sensitivity Rows\n\n"
            "These rows show whether a similar model story survives OLS, child-clustered OLS, GLM, GEE, or MixedLM variants. They are robustness evidence, not separate primary claims.\n\n"
            + atlas.markdown_table(expanded_table, max_rows=80)
        )

    if model_id == "M4" and not m4_context.empty:
        cols = [
            "model_id",
            "model_label",
            "fit_type",
            "effort_label",
            "formula",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "entropy_coef",
            "entropy_p",
            "status",
        ]
        m4 = m4_context[[col for col in cols if col in m4_context.columns]].copy()
        sections.append(
            "### M4 Context Deep-Dive Rows\n\n"
            "These rows are useful for separating estimator sensitivity from the context-predictor question.\n\n"
            + atlas.markdown_table(m4, max_rows=40)
        )

    if model_id in {"M5", "M6"} and not saturated.empty and "model_id" in saturated.columns:
        sat = saturated[saturated["model_id"].eq(model_id)].copy()
        if not sat.empty:
            cols = [
                "model_id",
                "model_label",
                "fit_type",
                "effort_label",
                "formula",
                "n_obs",
                "n_children",
                "r2_observed_fitted",
                "age_coef",
                "age_p",
                "context_entropy_coef",
                "context_entropy_p",
                "status",
            ]
            sections.append(
                "### Earlier Effort-Level Context Rows\n\n"
                "These are exploratory rows from the effort-level context model pass. They are useful for stress testing but less clean than exact fixed-effort slices.\n\n"
                + atlas.markdown_table(sat[[col for col in cols if col in sat.columns]], max_rows=25)
            )

    if not context_table.empty:
        sections.append(
            "### Context-Window Atlas Rows\n\n"
            "These rows repeat the model logic over k0-k3 and, for M4-M6, over entropy, context-size, and entropy-plus-size variants. The purpose is context robustness.\n\n"
            + atlas.markdown_table(context_table, max_rows=85)
        )

    if not robust_table.empty:
        sections.append(
            "### Balanced Bootstrap And Scrambling Robustness\n\n"
            "These rows aggregate to child-session-context units. They ask whether the age slope survives equalized age-bin sampling and weakens when true age ordering is broken.\n\n"
            + atlas.markdown_table(robust_table, max_rows=35)
        )

    sections.append(
        f"""### Plot Gallery For {model_id}

The repeated plot families were explained once above. In this gallery, read each plot family the same way: x-axis is usually child age, y-axis is predicted or observed total bits, colors usually separate effort values/levels or model variants, facets split effort units/context windows, and ribbons are model-confidence or bootstrap/null intervals depending on the family.

{atlas.figure_gallery(figures, md_path=md_path)}
"""
    )
    return "\n\n".join(sections)


def build_interpreted_markdown(tables: dict[str, pd.DataFrame], md_path: Path) -> str:
    """Build the interpreted v2 atlas Markdown."""

    figure_inventory = tables["figure_inventory"]
    artifacts = tables["source_artifacts"]
    coverage_rows = []
    for model_id in atlas.MODEL_ORDER:
        coverage_rows.append(
            {
                "model": model_id,
                "primary continuous rows": len(compact_primary_table(tables["dual"], model_id)),
                "context rows": int((tables["context_summary"].get("model_family", pd.Series(dtype=str)).eq(model_id)).sum())
                if not tables["context_summary"].empty
                else 0,
                "robustness rows": int((tables["robustness"].get("model_id", pd.Series(dtype=str)).eq(model_id)).sum())
                if not tables["robustness"].empty
                else 0,
                "plot references": len(atlas.figures_for_model(figure_inventory, model_id)),
            }
        )
    coverage = pd.DataFrame(coverage_rows)

    overview = """# Interpreted M1-M6 Super Atlas v2

This report is the interpreted companion to the original exhaustive M1-M6 super atlas. It leaves the original atlas unchanged and adds the missing plain-language layer: what each model asks, how it was implemented, how to read the plots, what coefficients mean, what is primary evidence, and what should not be overclaimed.

No new statistical models are fit in this synthesis. New model ideas are listed as proposed/not yet run unless a saved artifact already exists.

## Main Takeaway

The strongest current result is Model 2 with exact continuous effort controls and child fixed intercepts:

```text
sum_bits ~ age_c + target_effort_c + C(child_id)
```

Across words, morphemes, two syllable measures, and phonemes, the saved M2 rows show negative age coefficients. In plain language: for comparable production effort, and after each child gets their own baseline, older child utterances are predicted to have lower total Mistral surprisal. This is best interpreted as a developmental change in utterance-level predictability/information under effort control, not as proof that children communicate less.

This is Route 1 evidence: informativeness under controlled effort. The future Route 2 question is different: whether context uncertainty predicts how much effort or length the child chooses to produce.
"""

    sections = [
        overview,
        source_context_section(),
        project_history_section(),
        "## Coverage\n\n" + atlas.markdown_table(coverage, max_rows=10),
        "## Source Artifact Inventory\n\n" + atlas.markdown_table(artifacts, max_rows=30),
        "## Model Ladder\n\n" + atlas.markdown_table(atlas.model_formula_table(), max_rows=10),
        "## Estimator And Library Guide\n\n" + atlas.markdown_table(atlas.estimator_guide_table(), max_rows=20),
        child_identity_section(),
        "## Evidence Hierarchy\n\n"
        + atlas.markdown_table(
            pd.DataFrame(
                [
                    {
                        "level": "primary",
                        "evidence": "M2 continuous exact-effort models, fixed-effort M2 plots, M2 age-scrambling robustness.",
                        "use": "Supervisor-facing central result.",
                    },
                    {
                        "level": "robustness",
                        "evidence": "M3/M4/M6 stability, estimator sensitivity, GEE/GLM/MixedLM checks, context-window variants, fixed-slice support.",
                        "use": "Appendix or defense of the main M2 story.",
                    },
                    {
                        "level": "exploratory",
                        "evidence": "M5, saturated M6 interactions, low/mid/high effort-level rows, current next-token entropy interpretation.",
                        "use": "Generate next analyses; do not headline without stronger stability.",
                    },
                ]
            ),
            max_rows=5,
        ),
        "## Major Plot Family Guide\n\n" + atlas.markdown_table(plot_family_guide(), max_rows=20),
        "## What Fixed Effort Means\n\n"
        "Fixed effort means the plotted prediction compares children at the same exact utterance size: for example, 3 words versus 3 words, or 6 morphemes versus 6 morphemes. The model is still fit on all eligible utterances. The fixed value is only the slice through the fitted surface used for the plot. This matters because raw age-bin means confound development with the fact that older children often produce longer utterances.",
        "## Raw Means Versus Model-Adjusted Predictions\n\n"
        "Raw age-bin means are descriptive summaries of what the data look like in each age bin. They are not controlled for effort, child identity, context, or corpus composition. Model-adjusted predictions are fitted expectations after the variables in the formula are controlled or fixed. When raw means and model predictions differ, the model is answering the controlled scientific question, not simply redrawing the average data.",
        "## What To Cherry-Pick For The Supervisor Report\n\n"
        "- Use the M2 continuous-effort result table for words/morphemes/syllables/phonemes.\n"
        "- Use the M2 fixed-effort plots from `figs/m2_simple_plots` or the fixed-effort atlas.\n"
        "- Use the M2 age-scrambling robustness plot as the compact robustness check.\n"
        "- Mention M1 only as the reason child identity control matters.\n"
        "- Mention M4 only as a provisional context-control check.\n"
        "- Keep M5/M6 in the appendix unless the supervisor asks about interactions.",
        "## What Not To Overclaim\n\n"
        "- Do not claim the current result proves full communicative efficiency. It is an informativeness-under-effort-control result.\n"
        "- Do not say older children communicate less. Lower surprisal at fixed effort may mean more contextual predictability, conventionality, adult-likeness, or scorer familiarity.\n"
        "- Do not treat next-token context entropy as response-level uncertainty.\n"
        "- Do not treat child fixed effects as the only correct answer. They answer a within-child-adjusted question and should be supplemented by within/between and overlap checks.\n"
        "- Do not present p-values as model selection. The model ladder is theory-driven and robustness-driven.",
    ]

    sections.extend(build_model_section(model_id, tables, md_path) for model_id in atlas.MODEL_ORDER)

    context_fixed = tables["context_fixed"]
    if not context_fixed.empty:
        cols = [
            "context_k",
            "model_id",
            "model_label",
            "effort_label",
            "formula",
            "n_obs",
            "n_children",
            "r2_observed_fitted",
            "age_coef",
            "age_p",
            "context_entropy_coef",
            "context_entropy_p",
            "context_size_coef",
            "context_size_p",
            "status",
        ]
        adjunct_figs = figure_inventory[
            figure_inventory["exists"].astype(bool) & figure_inventory["source_id"].eq("context_adjunct")
        ].copy()
        sections.append(
            "## Appendix A: Context-Predictor Adjunct Atlas\n\n"
            "The CF0-CF3 adjunct models are not part of M1-M6, but they are useful for separating target effort, context entropy, and matched context size. They should be treated as adjacent robustness/exploratory material.\n\n"
            + atlas.markdown_table(context_fixed[[col for col in cols if col in context_fixed.columns]], max_rows=90)
            + "\n\n### Context Adjunct Gallery\n\n"
            + atlas.figure_gallery(adjunct_figs, md_path=md_path)
        )

    sections.append(
        "## Appendix B: Proposed Additions Not Claimed As Results\n\n"
        + atlas.markdown_table(proposed_models_table(), max_rows=20)
    )

    sections.append(
        "## Appendix C: Complete Figure Inventory\n\n"
        "This inventory is included so image coverage is auditable. The report embeds PNGs; PDF duplicates are intentionally not embedded.\n\n"
        + atlas.markdown_table(
            figure_inventory[figure_inventory["exists"].astype(bool)][
                ["source_id", "filename", "models", "context_k", "effort_label", "path"]
            ],
            max_rows=700,
        )
    )
    return "\n\n".join(sections)


def build_companion_markdown(tables: dict[str, pd.DataFrame]) -> str:
    """Build the technical implementation companion Markdown."""

    m2_table = compact_primary_table(tables["dual"], "M2")
    return f"""# M1-M6 Technical Implementation Companion

This companion explains the modeling mechanics behind the interpreted M1-M6 atlas. It is written for moments when the formulas, estimators, fixed effects, clustered standard errors, interactions, or Route 1 versus Route 2 distinction feel muddy.

No new models are fit here. Proposed additions are explicitly marked as proposed/not yet run.

## Route 1 And Route 2

Route 1 is the current utterance-information analysis:

```text
informativeness ~ age + effort + controls
```

The outcome is `sum_bits`, the total Mistral surprisal of the target utterance. Route 1 asks whether the information in what the child actually said changes with age after production effort is controlled.

Route 2 is the future effort-choice analysis:

```text
effort_or_length ~ age + context_uncertainty + controls
```

Route 2 asks whether the context leads children to choose shorter or longer responses. It needs a context-level predictor such as response-space entropy, not only target-utterance surprisal.

## Core Variables

- `sum_bits`: total target-utterance information in Mistral bits.
- `age_c`: child age in months, centered by subtracting a reference mean.
- `target_effort_c`: one effort measure, centered. Effort is words, morphemes, syllables, or phonemes.
- `context_entropy_c`: current next-token context entropy, centered.
- `context_size_c`: matched surface size of the context window, centered.
- `C(child_id)`: child fixed intercepts in a statsmodels formula.

## What Is OLS?

Ordinary least squares is ordinary linear regression. It fits a line or plane by choosing coefficients that minimize squared residuals:

```text
observed sum_bits - predicted sum_bits
```

In these reports, OLS coefficients are on the additive bits scale. If the M2 word-count age coefficient is about `-0.122`, the model predicts about 0.122 fewer total bits per additional month for same-word-count utterances after child identity is controlled.

Library used:

```text
statsmodels.formula.api.ols
```

## What Is A GLM?

A generalized linear model keeps the idea of a linear predictor but allows a different outcome distribution and link function. A Gaussian GLM with identity link is very close to ordinary linear regression. A Gamma/log GLM is different: it is for positive continuous outcomes and models the log expected outcome.

In a Gamma/log model, a coefficient is not "bits per month" directly. It is a change in log expected bits. Use prediction plots for intuition.

Library used:

```text
statsmodels.formula.api.glm
```

## What Is GEE?

Generalized estimating equations fit population-average regression models while accounting for clustered/repeated observations. In this project, the cluster is child. GEE is useful because utterance rows from the same child are correlated.

Library used:

```text
statsmodels.formula.api.gee(..., groups='child_id')
```

GEE is a sensitivity family here, not the primary supervisor-facing model.

## What Is MixedLM?

MixedLM is a linear mixed model. It can include random effects such as a random child intercept or a random child age slope. A random intercept lets children vary around a population baseline. A random age slope lets children vary in developmental trajectory.

Library used:

```text
statsmodels mixed linear model
```

Mixed models are useful for correlated longitudinal data, but they can be singular or unstable when the data do not support all random-effect terms. In this project they are diagnostics rather than the current headline model.

## Fixed Effects

A fixed effect estimates a separate coefficient for each level of a categorical variable. `C(child_id)` gives every child their own intercept. This controls stable child-level differences such as baseline verbosity, transcription style, corpus membership, or general predictability.

In M2-M6, child fixed intercepts mean the age slope is estimated after each child has a personal baseline.

## Random Effects

A random effect treats child-specific deviations as drawn from a population distribution. Random effects are useful when we want child-specific intercepts or slopes but also want shrinkage toward the population mean.

Random effects answer a different question from fixed effects. They are not simply "better fixed effects"; they encode a different statistical assumption.

## Clustered Standard Errors

Child-clustered standard errors adjust uncertainty for repeated utterances from the same child. They do not change the fitted line. They change standard errors, confidence intervals, and p-values.

This is why OLS and child-clustered OLS can have identical plotted mean lines but different shaded confidence bands and p-values.

## What Is An Interaction?

An interaction means the effect of one predictor depends on another predictor.

Age x effort:

```text
sum_bits ~ age_c * effort_c
```

asks whether the age slope differs for short versus long utterances.

Age x effort level:

```text
sum_bits ~ age_c * C(effort_level)
```

asks whether low, mid, and high effort groups have different age slopes.

Age x context entropy:

```text
sum_bits ~ age_c * context_entropy_c
```

asks whether the context-entropy association changes with age.

Effort x context entropy:

```text
sum_bits ~ effort_c * context_entropy_c
```

asks whether the relation between effort and total information differs in high-entropy contexts.

## Why Center Variables?

Centering subtracts a reference mean from a numeric predictor. It does not change model fit or slopes for simple main effects. It makes the intercept and interaction main effects easier to read.

With centered variables, an age coefficient in an interaction model is the age slope at average effort/context entropy, not at effort zero.

## Why Separate Effort Units?

Words, morphemes, syllables, and phonemes are highly correlated. Putting all of them in one regression makes the coefficients unstable and hard to interpret. The current strategy fits parallel models, one effort unit at a time.

That means a "Words" row and a "Morphemes" row are separate models asking the same question under different effort definitions.

## What R2 Means Here

`r2_observed_fitted` is an in-sample correspondence between observed and fitted `sum_bits`. It is useful for descriptive fit. It is not held-out predictive accuracy and should not be treated as proof that the model will generalize to new corpora.

## What P-Values Mean Here

A p-value describes how surprising a coefficient estimate would be under a null model, given the model assumptions and uncertainty calculation. It is not an effect size, not a probability the hypothesis is true, and not a model-selection device by itself.

For clustered child data, p-values are more credible when uncertainty respects child clustering or when robustness checks agree.

## Model-Based Predictions

Model-based prediction plots show fitted expected `sum_bits` under specified values of age, effort, context, and child structure. They are not raw averages. Fixed-effort slice plots hold effort at exact values so the age trend is not merely driven by older children producing longer utterances.

## Robustness And Scrambling Tests

Balanced bootstrap checks whether an age effect survives when age bins contribute equalized samples. Age scrambling checks whether the observed developmental slope depends on true age ordering. If the real slope is outside the scrambled null range, the age structure is doing real work.

The current robustness report aggregates to child-session-context units to reduce the illusion that hundreds of thousands of utterance rows are independent.

## Aggregating To Child-Session-Context Units

Aggregation changes the observational unit from utterance rows to:

```text
child x session x context window
```

This reduces row-level dependence and makes robustness tests more conservative. It also means coefficients will not exactly match utterance-level models.

{child_identity_section()}

## Current M2 Result In Mechanical Terms

{atlas.markdown_table(m2_table, max_rows=10)}

M2 is an OLS model with child fixed intercepts. Its uncertainty in the supervisor-facing report uses child-clustered robust standard errors. It answers a within-child-adjusted Route 1 question: for the same effort and child baseline, how does target utterance information change with age?

## Route 2 Length Prediction Bridge

Route 2 should use effort as the outcome. The conceptual formula is:

```text
production_effort ~ age + response_entropy + expected_model_response_length + context_size + question_type + child controls
```

Why Route 2 differs from Route 1:

- Route 1 asks how much information is in the utterance after effort is controlled.
- Route 2 asks how much effort the child chooses after context uncertainty is measured.
- Route 1 can use `sum_bits` as the outcome.
- Route 2 needs a context-level uncertainty measure available before the child speaks.

The current next-token entropy feature is only a provisional bridge. Response-space entropy from sampled full responses is a better match for the Route 2 hypothesis.

## Proposed Additions

{atlas.markdown_table(proposed_models_table(), max_rows=20)}

## Implementation Cheat Sheet

{atlas.markdown_table(atlas.estimator_guide_table(), max_rows=20)}

## Practical Reading Order

1. Read M2 first.
2. Check the M2 fixed-effort plots.
3. Check M2 balanced/scrambled robustness.
4. Use M3 only for age-by-effort nuance.
5. Use M4 to explain context-control robustness.
6. Treat M5/M6 as exploratory unless their interactions become stable in future runs.
"""


def validate_markdown_image_links(md_path: Path) -> pd.DataFrame:
    """Return a dataframe of image references and whether each file exists."""

    text = md_path.read_text(encoding="utf-8")
    rows = []
    for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        raw = match.group(1)
        path = (md_path.parent / raw).resolve()
        rows.append({"image": raw, "exists": path.exists(), "resolved_path": path.as_posix()})
    return pd.DataFrame(rows)


def build_interpreted_outputs(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    interpreted_md: Path = DEFAULT_INTERPRETED_MD,
    interpreted_html: Path = DEFAULT_INTERPRETED_HTML,
    companion_md: Path = DEFAULT_COMPANION_MD,
    companion_html: Path = DEFAULT_COMPANION_HTML,
) -> dict[str, Path]:
    """Write both interpreted reports and image-link audit tables."""

    output_dir.mkdir(parents=True, exist_ok=True)
    tables = read_tables()

    interpreted_text = build_interpreted_markdown(tables, interpreted_md)
    interpreted_md.parent.mkdir(parents=True, exist_ok=True)
    interpreted_md.write_text(interpreted_text, encoding="utf-8")
    render_markdown_file(interpreted_md, interpreted_html)

    companion_text = build_companion_markdown(tables)
    companion_md.parent.mkdir(parents=True, exist_ok=True)
    companion_md.write_text(companion_text, encoding="utf-8")
    render_markdown_file(companion_md, companion_html)

    image_audit = validate_markdown_image_links(interpreted_md)
    audit_path = output_dir / "interpreted_atlas_image_link_audit.csv"
    image_audit.to_csv(audit_path, index=False)
    tables["source_artifacts"].to_csv(output_dir / "source_artifact_inventory.csv", index=False)
    tables["figure_inventory"].to_csv(output_dir / "figure_inventory.csv", index=False)

    missing = int((~image_audit["exists"]).sum()) if not image_audit.empty else 0
    if missing:
        missing_path = output_dir / "missing_interpreted_atlas_images.csv"
        image_audit[~image_audit["exists"]].to_csv(missing_path, index=False)
        raise FileNotFoundError(f"{missing} image links are missing; see {missing_path}")

    return {
        "interpreted_md": interpreted_md,
        "interpreted_html": interpreted_html,
        "companion_md": companion_md,
        "companion_html": companion_html,
        "image_audit": audit_path,
        "figure_inventory": output_dir / "figure_inventory.csv",
        "source_artifacts": output_dir / "source_artifact_inventory.csv",
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--interpreted-md", type=Path, default=DEFAULT_INTERPRETED_MD)
    parser.add_argument("--interpreted-html", type=Path, default=DEFAULT_INTERPRETED_HTML)
    parser.add_argument("--companion-md", type=Path, default=DEFAULT_COMPANION_MD)
    parser.add_argument("--companion-html", type=Path, default=DEFAULT_COMPANION_HTML)
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""

    args = parse_args()
    outputs = build_interpreted_outputs(
        output_dir=args.output_dir,
        interpreted_md=args.interpreted_md,
        interpreted_html=args.interpreted_html,
        companion_md=args.companion_md,
        companion_html=args.companion_html,
    )
    for label, path in outputs.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
