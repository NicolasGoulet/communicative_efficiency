#!/usr/bin/env python3
"""Build a Route 1 candidate evidence gallery.

This is deliberately not the final supervisor-facing report. It is a menu of
promising Route 1 evidence cards pulled from the Atlas v2 reports and the
robustness checks, so the scientist can decide which plots and claims are good
enough to promote into the supervisor narrative.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from build_supervisor_candidate_report import (
    BAND_ORDER,
    MODEL_ONE_LINERS,
    MODEL_ORDER,
    SOURCE_ATLAS_DIR,
    SOURCE_LABELS,
    SOURCE_ORDER,
    build_effect_sentence_table,
    build_importance_table,
    compute_predictor_correlations,
    f_text,
    markdown_table,
    model_cards,
    p_text,
    plot_heldout_calibration,
    plot_heldout_regression_check,
    plot_model_ladder_r2,
    plot_source_slope_comparison,
    read_real_summary,
    relative_to_report,
    render_pdf,
)
from render_markdown_report import render_markdown_file


DEFAULT_OUTPUT_DIR = Path("results/route1_candidate_evidence_gallery")
DEFAULT_FIG_DIR = Path("figs/route1_candidate_evidence_gallery")
DEFAULT_DOC_DIR = Path("docs")
DOC_BASENAME = "route1_candidate_evidence_gallery_v0"
ROUTE1_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")

CARETAKER_SUMMARY = Path("results/route1_caretaker_atlas/full_fit/caretaker_model_summary.csv")
AGE_ROBUSTNESS_SUMMARY = Path("results/age_scrambling_robustness/age_scrambling_robustness_summary.csv")
AGE_ROBUSTNESS_OBSERVED = Path("results/age_scrambling_robustness/age_scrambling_observed_model_summary.csv")
M1_M2_IMPORTANCE = Path("results/m1_m2_utterance_information_deep_dive/variable_importance_delta_r2.csv")
CONTEXT_M1_M6_SUMMARY = Path("results/context_m1_m6_fixed_effort_atlas/context_m1_m6_model_summary.csv")

SOURCE_FIG_ROOT = Path("figs/route1_source_specific_corrected_fixed_effort_atlas")
CARETAKER_FIG_ROOT = Path("figs/route1_caretaker_corrected_fixed_effort_atlas")
AGE_ROBUSTNESS_FIG_ROOT = Path("figs/age_scrambling_robustness")
DEEP_DIVE_FIG_ROOT = Path("figs/m1_m2_utterance_information_deep_dive")
CONTEXT_FIG_ROOT = Path("figs/context_m1_m6_fixed_effort_atlas")
HELDOUT_FIG_ROOT = Path("figs/route1_heldout_real_child_prediction")
MEETING_FIG_ROOT = Path("figs/meeting_size_controlled_plots")


@dataclass
class EvidenceCard:
    card_id: str
    title: str
    artifact_family: str
    what_to_inspect: str
    effect_one_liner: str
    variable_importance: str
    why_promising: str
    caution: str
    figures: list[Path]
    tables: list[pd.DataFrame]


def md_image(report_path: Path, figure: Path, alt: str) -> str:
    if not figure.exists():
        return f"_Missing figure: `{figure}`_"
    return f"![{alt}]({relative_to_report(report_path, figure)})"


def md_link(report_path: Path, path: Path, label: str | None = None) -> str:
    return f"[{label or path.name}]({relative_to_report(report_path, path)})"


def source_report_path(source: str) -> Path:
    return Path(f"docs/utterance_information_route1_{source}_corrected_fixed_effort_atlas_v2.html")


def source_m4c_plot(source: str) -> Path:
    return SOURCE_FIG_ROOT / source / f"{source}_k3_m4c_nb_words_fixed_effort_atlas.png"


def build_source_atlas_table(output_dir: Path) -> pd.DataFrame:
    rows = []
    for source in SOURCE_ORDER:
        slopes_path = SOURCE_ATLAS_DIR / source / "fixed_slice_slopes.csv"
        if not slopes_path.exists():
            continue
        slopes = pd.read_csv(slopes_path)
        sub = slopes[
            slopes["context_k"].eq("k3")
            & slopes["effort_col"].eq("nb_words")
            & slopes["model_id"].eq("M4c")
        ].copy()
        band_values = {
            band: float(sub[sub["atlas_bin"].eq(band)]["slope_bits_per_6_months"].mean())
            if not sub[sub["atlas_bin"].eq(band)].empty
            else float("nan")
            for band in BAND_ORDER
        }
        rows.append(
            {
                "source": source,
                "label": SOURCE_LABELS.get(source, source),
                "plot": str(source_m4c_plot(source)),
                "atlas_html": str(source_report_path(source)),
                "slope_1_4_bits_per_6mo": band_values["1-4"],
                "slope_5_8_bits_per_6mo": band_values["5-8"],
                "slope_9_12_bits_per_6mo": band_values["9-12"],
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "selected_source_atlas_cards.csv", index=False)
    return frame


def readable_source_table(frame: pd.DataFrame, report_path: Path) -> pd.DataFrame:
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "source atlas": row["label"],
                "1-4 words": f"{row['slope_1_4_bits_per_6mo']:+.2f}",
                "5-8 words": f"{row['slope_5_8_bits_per_6mo']:+.2f}",
                "9-12 words": f"{row['slope_9_12_bits_per_6mo']:+.2f}",
                "plot": md_link(report_path, Path(row["plot"]), "plot"),
                "atlas": md_link(report_path, Path(row["atlas_html"]), "html"),
            }
        )
    return pd.DataFrame(rows)


def build_caretaker_table(output_dir: Path) -> pd.DataFrame:
    if not CARETAKER_SUMMARY.exists():
        return pd.DataFrame()
    frame = pd.read_csv(CARETAKER_SUMMARY)
    sub = frame[
        frame["context_k"].eq("k3")
        & frame["effort_col"].eq("nb_words")
        & frame["model_id"].isin(["CM2", "CM3", "CM4c", "CM6"])
        & frame["status"].eq("fit")
    ].copy()
    sub = sub[
        [
            "model_id",
            "model_label",
            "readable_formula",
            "r2",
            "age_coef",
            "age_p",
            "effort_coef",
            "effort_p",
            "preceding_context_effort_coef",
            "preceding_context_effort_p",
            "age_effort_coef",
            "age_effort_p",
        ]
    ]
    sub.to_csv(output_dir / "selected_caretaker_k3_words_models.csv", index=False)
    return sub


def readable_caretaker_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "model": row["model_id"],
                "formula": row["readable_formula"],
                "R2": f_text(row["r2"], 4),
                "age effect": f"{f_text(row['age_coef'], 3)} bits/month (p={p_text(row['age_p'])})",
                "effort effect": f"{f_text(row['effort_coef'], 2)} bits/word (p={p_text(row['effort_p'])})",
                "context effort": f"{f_text(row['preceding_context_effort_coef'], 3)} (p={p_text(row['preceding_context_effort_p'])})",
                "age x effort": f"{f_text(row['age_effort_coef'], 4)} (p={p_text(row['age_effort_p'])})",
            }
        )
    return pd.DataFrame(rows)


def build_age_robustness_table(output_dir: Path) -> pd.DataFrame:
    if not AGE_ROBUSTNESS_SUMMARY.exists():
        return pd.DataFrame()
    frame = pd.read_csv(AGE_ROBUSTNESS_SUMMARY)
    sub = frame[
        frame["context_k"].eq("k3")
        & frame["effort_col"].eq("nb_words")
        & frame["model_id"].isin(["M2", "M3", "M4", "M5", "M6"])
    ].copy()
    sub = sub[
        [
            "model_id",
            "robustness_label",
            "observed_age_coef",
            "null_q025_age_coef",
            "null_q975_age_coef",
            "observed_outside_null_95",
            "two_sided_permutation_p",
        ]
    ].sort_values(["model_id", "robustness_label"])
    sub.to_csv(output_dir / "selected_age_scrambling_robustness_k3_words.csv", index=False)
    return sub


def readable_age_robustness_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "model": row["model_id"],
                "check": row["robustness_label"],
                "observed age": f_text(row["observed_age_coef"], 3),
                "null 95% interval": f"[{f_text(row['null_q025_age_coef'], 3)}, {f_text(row['null_q975_age_coef'], 3)}]",
                "outside null?": str(bool(row["observed_outside_null_95"])),
                "p": p_text(row["two_sided_permutation_p"]),
            }
        )
    return pd.DataFrame(rows)


def build_deep_dive_importance_table(output_dir: Path) -> pd.DataFrame:
    if not M1_M2_IMPORTANCE.exists():
        return pd.DataFrame()
    frame = pd.read_csv(M1_M2_IMPORTANCE)
    sub = frame[
        frame["effort_col"].eq("nb_words")
        & frame["model_id"].isin(["M1", "M2"])
    ].copy()
    sub["delta_r2_when_dropped"] = pd.to_numeric(sub["delta_r2_when_dropped"], errors="coerce")
    sub = sub.sort_values(["model_id", "delta_r2_when_dropped"], ascending=[True, False])
    sub.to_csv(output_dir / "selected_old_deep_dive_variable_importance_words.csv", index=False)
    return sub


def build_context_summary_table(output_dir: Path) -> pd.DataFrame:
    if not CONTEXT_M1_M6_SUMMARY.exists():
        return pd.DataFrame()
    frame = pd.read_csv(CONTEXT_M1_M6_SUMMARY)
    sub = frame[
        frame["context_k"].eq("k3")
        & frame["effort_col"].eq("nb_words")
        & frame["model_id"].isin(["M4E", "M4ES", "M6E", "M6ES"])
        & frame["status"].eq("fit")
    ].copy()
    keep = [
        "model_id",
        "model_label",
        "formula",
        "r2_observed_fitted",
        "age_coef",
        "age_p",
        "target_effort_coef",
        "target_effort_p",
        "context_entropy_coef",
        "context_entropy_p",
        "context_size_coef",
        "context_size_p",
    ]
    keep = [col for col in keep if col in sub.columns]
    sub = sub[keep]
    sub.to_csv(output_dir / "selected_context_m1_m6_k3_words_models.csv", index=False)
    return sub


def readable_context_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "model": row["model_id"],
                "formula": row["formula"],
                "R2": f_text(row["r2_observed_fitted"], 4),
                "age": f"{f_text(row['age_coef'], 3)} (p={p_text(row['age_p'])})",
                "target effort": f"{f_text(row['target_effort_coef'], 2)} (p={p_text(row['target_effort_p'])})",
                "context entropy": f"{f_text(row['context_entropy_coef'], 3)} (p={p_text(row['context_entropy_p'])})",
                "context size": f"{f_text(row['context_size_coef'], 3)} (p={p_text(row['context_size_p'])})",
            }
        )
    return pd.DataFrame(rows)


def card_frame(cards: list[EvidenceCard]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "card_id": card.card_id,
                "title": card.title,
                "artifact_family": card.artifact_family,
                "what_to_inspect": card.what_to_inspect,
                "effect_one_liner": card.effect_one_liner,
                "variable_importance": card.variable_importance,
                "why_promising": card.why_promising,
                "caution": card.caution,
                "figures": "; ".join(str(path) for path in card.figures),
            }
            for card in cards
        ]
    )


def write_report(
    *,
    doc_path: Path,
    output_dir: Path,
    generated_figures: dict[str, Path],
    source_table: pd.DataFrame,
    source_table_readable: pd.DataFrame,
    model_cards_frame: pd.DataFrame,
    importance_table: pd.DataFrame,
    effect_table: pd.DataFrame,
    caretaker_table: pd.DataFrame,
    age_robustness_table: pd.DataFrame,
    deep_dive_importance: pd.DataFrame,
    context_table: pd.DataFrame,
) -> None:
    cards = [
        EvidenceCard(
            card_id="C01",
            title="Real child fixed-effort developmental line",
            artifact_family="Route 1 real-child Atlas v2",
            what_to_inspect="Start with the k3/M4c/words fixed-effort Atlas plot, because it controls child identity, effort, and broad question type.",
            effect_one_liner="age -> lower sum_bits at the same word count: M4c estimates -0.127 bits/month for real child speech.",
            variable_importance="Effort dominates the outcome, child identity matters, and M4c is the clean confound-control candidate among the simple Atlas v2 models.",
            why_promising="This is the cleanest Route 1 story candidate: developmental trend after effort and child identity are controlled.",
            caution="Do not present it alone; pair it with source comparison and robustness cards so it is not just one fitted line.",
            figures=[source_m4c_plot("real"), generated_figures["r2_importance"]],
            tables=[importance_table, effect_table],
        ),
        EvidenceCard(
            card_id="C02",
            title="Every source atlas on the same slope scale",
            artifact_family="Route 1 source-specific Atlas v2",
            what_to_inspect="Compare the fixed-effort M4c k3/word slopes across real, random, n-gram, and LSTM source atlases.",
            effect_one_liner="real child slopes go down; random slopes go up; n-gram/LSTM baselines mostly go down but differ by effort band.",
            variable_importance="This card is not a predictor-importance card; it is a baseline specificity check for the age slope.",
            why_promising="It shows the real-child line is not an artifact of using any generated target or of the plotting code.",
            caution="Generated baselines are not psychological controls; use them as sanity checks, not as direct alternative children.",
            figures=[generated_figures["source_slopes"]],
            tables=[source_table_readable],
        ),
        EvidenceCard(
            card_id="C03",
            title="One selected plot from each source-specific Atlas",
            artifact_family="Real, random, unigram, bigram, trigram, LSTM k3/k4/k5 Atlas v2 reports",
            what_to_inspect="Use this as the visual menu: one M4c/k3/words fixed-effort plot per source-specific Atlas.",
            effect_one_liner="the same formula produces different age-line shapes depending on whether the target is real child speech or a baseline.",
            variable_importance="Formula is held constant here, so differences are about target source behavior, not model specification.",
            why_promising="This directly satisfies the 'pull from every atlas' requirement without burying you in hundreds of plots.",
            caution="If one source looks interesting, open the full source Atlas before promoting it.",
            figures=[source_m4c_plot(source) for source in SOURCE_ORDER],
            tables=[source_table_readable],
        ),
        EvidenceCard(
            card_id="C04",
            title="Context controls and confounds from the email",
            artifact_family="Context M1-M6 Atlas plus real Atlas v2",
            what_to_inspect="Check whether context entropy and context size change the age/effort story.",
            effect_one_liner="context entropy is a meaningful control in Route 1, but it is not yet the Route 2 claim about choosing utterance length.",
            variable_importance="In the real k3/word ladder, adding context controls changes R2 modestly compared with the effort and child-identity base.",
            why_promising="This is the bridge from the current Route 1 report to the email's stronger context-predictability story.",
            caution="Do not overclaim optimization from this card; it controls context predictability but does not yet model effort choice.",
            figures=[
                CONTEXT_FIG_ROOT / "k3_m6e_nb_words_fixed_effort_atlas.png",
                CONTEXT_FIG_ROOT / "k3_m6es_nb_words_fixed_effort_atlas.png",
                generated_figures["correlations"],
            ],
            tables=[readable_context_table(context_table)],
        ),
        EvidenceCard(
            card_id="C05",
            title="Age-scrambling and age-bin robustness",
            artifact_family="Age scrambling robustness report",
            what_to_inspect="Check whether observed age slopes sit outside shuffled or balanced-bootstrap age-label nulls.",
            effect_one_liner="the useful claim is not just 'a line exists'; it must be stronger than age-label artifacts.",
            variable_importance="Robustness varies by model; use the table to decide which model is sturdy enough for the supervisor report.",
            why_promising="This is the best defense against 'is this just age-bin composition?'",
            caution="Some checks may be mixed; only promote models whose observed slope behaves well under the relevant null.",
            figures=[
                AGE_ROBUSTNESS_FIG_ROOT / "m2_clear_robustness_regression_lines.png",
                AGE_ROBUSTNESS_FIG_ROOT / "m6_clear_robustness_regression_lines.png",
                AGE_ROBUSTNESS_FIG_ROOT / "robustness_outside_null_heatmap.png",
            ],
            tables=[age_robustness_table],
        ),
        EvidenceCard(
            card_id="C06",
            title="Estimator-family checks: OLS, GEE, GLM, MixedLM",
            artifact_family="M1/M2/M3 deep dive",
            what_to_inspect="Compare adjusted age lines across OLS with fixed effects, clustered SE, GEE, GLM, and mixed-effects variants.",
            effect_one_liner="the candidate age story is stronger if the line direction does not depend on one estimator.",
            variable_importance="Old deep-dive delta-R2 shows effort explains far more raw variance than age, which is exactly why fixed-effort plotting is necessary.",
            why_promising="This gives the methods backup: the story is not just a single OLS table.",
            caution="Use these as checks/appendix material unless a model-family contrast becomes central.",
            figures=[
                DEEP_DIVE_FIG_ROOT / "m2_ols_child_fe_adjusted_age_lines.png",
                DEEP_DIVE_FIG_ROOT / "m2_mixed_random_age_slope_adjusted_age_lines.png",
                DEEP_DIVE_FIG_ROOT / "m3_gee_gaussian_interaction_adjusted_age_lines.png",
                DEEP_DIVE_FIG_ROOT / "m1_m2_delta_r2_variable_importance.png",
            ],
            tables=[deep_dive_importance.head(12)],
        ),
        EvidenceCard(
            card_id="C07",
            title="Heldout children: actual regression line vs predicted regression line",
            artifact_family="Heldout real child prediction report",
            what_to_inspect="Black dots/line are actual heldout child monthly data; teal dashed line is PBM-trained prediction at the same child and effort band.",
            effect_one_liner="this asks whether a PBM-trained Route 1 model predicts the shape of unseen children's information trajectories.",
            variable_importance="Prediction uses population PBM models because heldout children cannot use child fixed effects learned from themselves.",
            why_promising="This is the generalization check you wanted: actual line and predicted line are literally in the same panel.",
            caution="Current heldout fixed-effort slopes are mixed by child and band, so this is a diagnostic candidate, not yet the cleanest proof.",
            figures=[generated_figures["heldout_regression"], generated_figures["heldout_calibration"]],
            tables=[pd.read_csv(output_dir / "heldout_pop_m4c_actual_vs_predicted_regression_slopes.csv")],
        ),
        EvidenceCard(
            card_id="C08",
            title="Heldout child selection coverage",
            artifact_family="Heldout child selection/corpus coverage",
            what_to_inspect="Use this only to explain why Ella, Naomi, and Helen were selected.",
            effect_one_liner="the selected three children cover a broad month range while staying outside the PBM training set.",
            variable_importance="No predictor importance; this is a sampling/support argument.",
            why_promising="It prevents the heldout section from looking arbitrary.",
            caution="This belongs before prediction results, not as evidence of communicative efficiency.",
            figures=[
                HELDOUT_FIG_ROOT / "heldout_selection_pbm_corpus_coverage.png",
                Path("figs/big_cleaned_dataset/default_naturalistic_merged_006_023/pbm_reference_and_heldout_candidate_options.png"),
            ],
            tables=[],
        ),
        EvidenceCard(
            card_id="C09",
            title="Caretaker contrast",
            artifact_family="Caretaker Route 1 Atlas v2",
            what_to_inspect="Compare parent/caretaker fixed-effort age lines to the child lines.",
            effect_one_liner="caretaker information does not show the same clean child-age downward story after dyad and effort controls.",
            variable_importance="Caretaker effort dominates caretaker sum_bits; child age is weak or model-dependent in the selected k3/word controls.",
            why_promising="This makes the child result more interpretable: the developmental pattern is not automatically present for adult speech in the same sessions.",
            caution="The caretaker report answers a different question: adult speech as a function of child age, not adult language development.",
            figures=[
                CARETAKER_FIG_ROOT / "caretaker_k3_cm2_nb_words_fixed_effort_atlas.png",
                CARETAKER_FIG_ROOT / "caretaker_k3_cm6_nb_words_fixed_effort_atlas.png",
            ],
            tables=[readable_caretaker_table(caretaker_table)],
        ),
        EvidenceCard(
            card_id="C10",
            title="Child vs caretaker size-controlled descriptive contrast",
            artifact_family="Meeting size-controlled plots",
            what_to_inspect="Use these as descriptive support before or after the model-based child/caretaker contrast.",
            effect_one_liner="child and caretaker information differ even when utterance size is held constant descriptively.",
            variable_importance="No model predictor importance; this is a descriptive exact-size comparison.",
            why_promising="It is easy to understand visually and may help introduce why fixed effort matters.",
            caution="It is not a substitute for the regression-controlled Atlas result.",
            figures=[
                MEETING_FIG_ROOT / "exact_words_child_vs_caretaker.png",
                MEETING_FIG_ROOT / "child_vs_caretaker_bits_per_word_by_size.png",
            ],
            tables=[],
        ),
    ]
    card_frame(cards).to_csv(output_dir / "candidate_evidence_cards.csv", index=False)

    real_atlas = Path("docs/utterance_information_route1_real_corrected_fixed_effort_atlas_v2.html")
    source_index = Path("docs/utterance_information_route1_source_specific_corrected_fixed_effort_atlas_v2_index.html")
    robustness_report = Path("docs/utterance_information_age_scrambling_robustness.html")
    heldout_report = Path("docs/utterance_information_route1_heldout_real_child_prediction_report.html")
    caretaker_report = Path("docs/utterance_information_route1_caretaker_corrected_fixed_effort_atlas_v2.html")
    tech_companion = Path("docs/utterance_information_m1_m6_technical_implementation_companion.html")

    lines: list[str] = [
        "# Route 1 Candidate Evidence Gallery v0",
        "",
        "This is **not** the supervisor report. It is a selectable gallery of promising Route 1 plots, checks, and exact effect sentences to inspect before deciding what goes into the supervisor-facing narrative.",
        "",
        "## What This File Is For",
        "",
        "- Pull the best candidates from every Route 1 Atlas/report family.",
        "- Put actual plots next to literal one-line effect interpretations.",
        "- Separate promising evidence from cautions and robustness checks.",
        "- Make it easy to choose what to promote into the final supervisor report.",
        "",
        "## Source Reports",
        "",
        f"- Real child Atlas v2: {md_link(doc_path, real_atlas)}",
        f"- Source-specific Atlas v2 index: {md_link(doc_path, source_index)}",
        f"- Heldout child prediction report: {md_link(doc_path, heldout_report)}",
        f"- Caretaker Atlas v2: {md_link(doc_path, caretaker_report)}",
        f"- Age-scrambling robustness: {md_link(doc_path, robustness_report)}",
        f"- Technical model companion: {md_link(doc_path, tech_companion)}",
        "",
        "## How To Read An Atlas Line",
        "",
        "A fixed-effort Atlas line is a fitted regression prediction, not a raw average.",
        "",
        "- **Downward age line:** at the same effort level, older children are predicted to carry less `sum_bits`.",
        "- **Upward age line:** at the same effort level, older children are predicted to carry more `sum_bits`.",
        "- **Separated effort bands:** longer utterances carry more total information, so effort must be controlled.",
        "- **Actual-vs-predicted heldout line:** black is the real heldout trajectory; teal dashed is the PBM-trained model's predicted trajectory.",
        "",
        "## Fast Pick List",
        "",
        "| Use status | Candidate | Why |",
        "| --- | --- | --- |",
        "| Strong candidate | C01 Real child fixed-effort line | Cleanest Route 1 developmental story. |",
        "| Strong candidate | C02 Source comparison | Shows real/random/generated baselines on same slope scale. |",
        "| Strong candidate | C05 Age-scrambling robustness | Defends against age-bin composition artifacts. |",
        "| Diagnostic candidate | C07 Heldout actual vs predicted | Direct generalization check, currently mixed. |",
        "| Context bridge | C04 Context controls | Links to email confounds without overclaiming Route 2. |",
        "| Contrast candidate | C09 Caretaker contrast | Helps show child result is not automatic in adult speech. |",
        "",
    ]

    for card in cards:
        lines.extend(
            [
                f"## {card.card_id}. {card.title}",
                "",
                f"**Artifact family:** {card.artifact_family}",
                "",
                f"**What to inspect:** {card.what_to_inspect}",
                "",
                f"**Effect one-liner:** {card.effect_one_liner}",
                "",
                f"**Variable importance / predictor relation:** {card.variable_importance}",
                "",
                f"**Why promising:** {card.why_promising}",
                "",
                f"**Caution before supervisor report:** {card.caution}",
                "",
            ]
        )
        for fig in card.figures:
            lines.extend([md_image(doc_path, fig, f"{card.card_id} {fig.name}"), ""])
        for table in card.tables:
            if table is not None and not table.empty:
                lines.extend([markdown_table(table, max_rows=24), ""])

    lines.extend(
        [
            "## Model Card Menu: M1-M15",
            "",
            "These are implementation-level cards from the current Route 1 Atlas v2 ladder. I do **not** find a real implemented M16 artifact in the current ladder, so this gallery does not invent one.",
            "",
            markdown_table(model_cards_frame, max_rows=30),
            "",
            "## Effect Sentence Menu",
            "",
            markdown_table(effect_table, max_rows=20),
            "",
            "## Saved Artifacts",
            "",
            "```text",
            str(output_dir / "candidate_evidence_cards.csv"),
            str(output_dir / "selected_source_atlas_cards.csv"),
            str(output_dir / "selected_caretaker_k3_words_models.csv"),
            str(output_dir / "selected_age_scrambling_robustness_k3_words.csv"),
            str(output_dir / "selected_old_deep_dive_variable_importance_words.csv"),
            str(output_dir / "selected_context_m1_m6_k3_words_models.csv"),
            str(output_dir / "heldout_pop_m4c_actual_vs_predicted_regression_slopes.csv"),
            str(output_dir / "pbm_real_k3_predictor_correlations.csv"),
            str(output_dir / "source_comparison_m4c_k3_words_slopes.csv"),
            str(generated_figures["source_slopes"].parent),
            "```",
            "",
        ]
    )
    doc_path.write_text("\n".join(lines), encoding="utf-8")


def run(*, output_dir: Path, fig_dir: Path, doc_dir: Path, chunksize: int) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    doc_dir.mkdir(parents=True, exist_ok=True)

    real_summary = read_real_summary()
    cards = model_cards(real_summary)
    importance = build_importance_table(real_summary)
    effects = build_effect_sentence_table(real_summary)
    cards.to_csv(output_dir / "model_cards_m1_m15.csv", index=False)
    importance.to_csv(output_dir / "real_k3_words_variable_importance.csv", index=False)
    effects.to_csv(output_dir / "effect_sentence_menu.csv", index=False)

    generated_figures = {
        "r2_importance": plot_model_ladder_r2(real_summary, fig_dir, output_dir),
        "source_slopes": plot_source_slope_comparison(fig_dir, output_dir, model_id="M4c"),
        "heldout_regression": plot_heldout_regression_check(fig_dir, output_dir, model_id="POP_M4C"),
        "heldout_calibration": plot_heldout_calibration(fig_dir, output_dir, model_id="POP_M4C"),
    }
    _, corr_path = compute_predictor_correlations(ROUTE1_INPUT, output_dir, fig_dir, chunksize)
    generated_figures["correlations"] = corr_path

    source_table = build_source_atlas_table(output_dir)
    doc_path = doc_dir / f"{DOC_BASENAME}.md"
    source_table_readable = readable_source_table(source_table, doc_path)
    caretaker_table = build_caretaker_table(output_dir)
    age_robustness_table = readable_age_robustness_table(build_age_robustness_table(output_dir))
    deep_dive_importance = build_deep_dive_importance_table(output_dir)
    context_table = build_context_summary_table(output_dir)

    write_report(
        doc_path=doc_path,
        output_dir=output_dir,
        generated_figures=generated_figures,
        source_table=source_table,
        source_table_readable=source_table_readable,
        model_cards_frame=cards,
        importance_table=importance,
        effect_table=effects,
        caretaker_table=caretaker_table,
        age_robustness_table=age_robustness_table,
        deep_dive_importance=deep_dive_importance,
        context_table=context_table,
    )

    html_path = doc_path.with_suffix(".html")
    embedded_path = doc_path.with_suffix(".embedded.html")
    pdf_path = doc_path.with_suffix(".pdf")
    render_markdown_file(doc_path, html_path)
    render_markdown_file(doc_path, embedded_path, embed_images=True)
    outputs = {"md": doc_path, "html": html_path, "embedded_html": embedded_path}
    if render_pdf(html_path, pdf_path) and pdf_path.exists():
        outputs["pdf"] = pdf_path
    return outputs


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-dir", type=Path, default=DEFAULT_DOC_DIR)
    parser.add_argument("--chunksize", type=int, default=250_000)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    outputs = run(output_dir=args.output_dir, fig_dir=args.fig_dir, doc_dir=args.doc_dir, chunksize=args.chunksize)
    for label, path in outputs.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
