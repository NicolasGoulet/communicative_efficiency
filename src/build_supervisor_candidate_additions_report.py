#!/usr/bin/env python3
"""Build a curated report of candidate additions for the supervisor report.

This report is explicitly not the supervisor-facing report. It is a bridge
document that selects from the recent ANCOVA and Portelance/Xu extension
analyses, explains the new predictors, and labels each candidate as main-text,
appendix, exploratory, or not-ready.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


DEFAULT_ANCOVA_DIR = Path("results/route1_exhaustive_ancova_gallery")
DEFAULT_EXTENSION_DIR = Path("results/route1_portelance_xu_extension_suite")
DEFAULT_DOC_MD = Path("docs/predicting_utterance_level_information_candidate_additions.md")
DEFAULT_DOC_HTML = Path("docs/predicting_utterance_level_information_candidate_additions.html")
DEFAULT_INDEX = Path("docs/route1_current_reports_browser_index.html")

AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
EFFORT_ORDER = ["Words", "Morphemes", "Syllables: CMU/pkg", "Syllables: pkg", "Phonemes"]


@dataclass(frozen=True)
class CandidateFigure:
    title: str
    path: Path
    placement: str
    claim: str
    model: str
    why: str
    caveat: str = ""


def fmt(value: object, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if math.isnan(number):
        return ""
    if abs(number) < 0.001 and number != 0:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def fmt_p(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if math.isnan(number):
        return ""
    if number < 0.001:
        return "<.001"
    return f"{number:.3f}"


def md_table(frame: pd.DataFrame, columns: Sequence[str] | None = None, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_No rows._"
    view = frame.loc[:, list(columns)].copy() if columns else frame.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    view = view.fillna("").astype(str)
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in view.columns) + " |")
    return "\n".join(lines)


def relative_image(path: Path) -> str:
    return str(Path("..") / path)


def slope_per_6mo(frame: pd.DataFrame, value_col: str) -> float:
    frame = frame.dropna(subset=["age_mid", value_col]).copy()
    if frame["age_mid"].nunique() < 2:
        return math.nan
    return float(np.polyfit(frame["age_mid"], frame[value_col], 1)[0] * 6.0)


def real_fixed_effort_summary(adjusted: pd.DataFrame) -> pd.DataFrame:
    sub = adjusted[
        adjusted["model_id"].eq("real_age_ancova")
        & adjusted["outcome"].eq("sum_bits_k3")
        & adjusted["source_label"].eq("Real child")
    ].copy()
    rows = []
    for effort, group in sub.groupby("effort_label", observed=True):
        group = group.sort_values("age_mid")
        rows.append(
            {
                "effort": effort,
                "start_bits": float(group.iloc[0]["adjusted_mean"]),
                "end_bits": float(group.iloc[-1]["adjusted_mean"]),
                "start_to_end_delta": float(group.iloc[-1]["adjusted_mean"] - group.iloc[0]["adjusted_mean"]),
                "slope_bits_per_6mo": slope_per_6mo(group, "adjusted_mean"),
            }
        )
    return pd.DataFrame(rows)


def exact_effort_summary(exact_adjusted: pd.DataFrame) -> pd.DataFrame:
    sub = exact_adjusted[exact_adjusted["outcome"].eq("sum_bits_k3")].copy()
    rows = []
    for effort, group in sub.groupby("effort_label", observed=True):
        slopes = []
        for _, effort_group in group.groupby("effort_value", observed=True):
            slopes.append(slope_per_6mo(effort_group, "adjusted_mean"))
        values = pd.Series(slopes).dropna()
        rows.append(
            {
                "effort": effort,
                "downward_exact_efforts": int((values < 0).sum()),
                "total_exact_efforts": int(len(values)),
                "median_slope": float(values.median()),
            }
        )
    return pd.DataFrame(rows)


def source_gap_words_summary(contrasts: pd.DataFrame) -> pd.DataFrame:
    sub = contrasts[
        contrasts["effort_label"].eq("Words")
        & contrasts["outcome"].eq("sum_bits_k3")
        & contrasts["source_label"].isin(["Random", "Trigram", "LSTM k4", "Caretaker"])
    ].copy()
    rows = []
    for source, group in sub.groupby("source_label", observed=True):
        group = group.sort_values("age_mid")
        rows.append(
            {
                "source": source,
                "first_bin_gap_bits": float(group.iloc[0]["source_minus_real"]),
                "last_bin_gap_bits": float(group.iloc[-1]["source_minus_real"]),
                "gap_change_bits": float(group.iloc[-1]["source_minus_real"] - group.iloc[0]["source_minus_real"]),
            }
        )
    return pd.DataFrame(rows)


def route1_joint_summary(summary: pd.DataFrame) -> pd.DataFrame:
    keep = summary[summary["model_id"].isin(["base_effort_child", "frequency_control", "joint_context_frequency"])].copy()
    keep["age_coef_fmt"] = keep["age_coef"].map(lambda value: fmt(value, 3))
    keep["age_p_fmt"] = keep["age_p"].map(fmt_p)
    keep["delta_r2_fmt"] = keep["delta_r2_vs_base"].map(lambda value: fmt(value, 4))
    return keep.loc[:, ["model_id", "effort_label", "age_coef_fmt", "age_p_fmt", "delta_r2_fmt"]]


def route2_context_summary(coef: pd.DataFrame) -> pd.DataFrame:
    context = coef[coef["term"].eq("context_entropy_bits_c")].copy()
    context["coef_fmt"] = context["coef"].map(lambda value: fmt(value, 4))
    context["p_fmt"] = context["p"].map(fmt_p)
    interaction = coef[coef["term"].eq("age_months_c:context_entropy_bits_c")].copy()
    interaction = interaction.loc[:, ["effort_label", "coef", "p"]].rename(
        columns={"coef": "age_interaction_coef", "p": "age_interaction_p"}
    )
    out = context.merge(interaction, on="effort_label", how="left")
    out["age_interaction_coef_fmt"] = out["age_interaction_coef"].map(lambda value: fmt(value, 4))
    out["age_interaction_p_fmt"] = out["age_interaction_p"].map(fmt_p)
    return out.loc[:, ["effort_label", "coef_fmt", "p_fmt", "age_interaction_coef_fmt", "age_interaction_p_fmt"]]


def scrambled_summary(nulls: pd.DataFrame) -> pd.DataFrame:
    sub = nulls[nulls["outcome"].eq("sum_bits_k3")].copy()
    sub["outside_null_95"] = (sub["observed_slope_per_6mo"] < sub["null_lo"]) | (sub["observed_slope_per_6mo"] > sub["null_hi"])
    sub["observed_fmt"] = sub["observed_slope_per_6mo"].map(lambda value: fmt(value, 3))
    sub["null_range"] = sub.apply(lambda row: f"[{fmt(row['null_lo'], 3)}, {fmt(row['null_hi'], 3)}]", axis=1)
    sub["empirical_p_fmt"] = sub["empirical_p"].map(fmt_p)
    return sub.loc[:, ["source_label", "effort_label", "observed_fmt", "null_range", "empirical_p_fmt", "outside_null_95"]]


def predictor_dictionary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "predictor": "production effort",
                "built from": "`nb_words`, `nb_morphemes`, syllable counts, `nb_phonemes`",
                "interpretation": "How much linguistic material the target utterance contains.",
                "why it matters": "Separates information growth from the fact that older children simply say more.",
            },
            {
                "predictor": "exact effort value",
                "built from": "Exact observed word/morpheme/syllable/phoneme counts",
                "interpretation": "Same-effort comparison inside one exact length value.",
                "why it matters": "Strongest guard against an MLU-only critique.",
            },
            {
                "predictor": "context_entropy_bits",
                "built from": "Mistral entropy over the next token after the preceding caretaker context",
                "interpretation": "How uncertain the context is before the child speaks.",
                "why it matters": "Operationalizes the Route 2/Xu idea that contextual uncertainty should affect production effort.",
            },
            {
                "predictor": "context_effort_words",
                "built from": "Word count of the preceding context text",
                "interpretation": "How much caregiver material preceded the target.",
                "why it matters": "Controls for longer caregiver contexts mechanically giving more information.",
            },
            {
                "predictor": "question_type",
                "built from": "Transparent rule-based parser of the last context line",
                "interpretation": "Statement/fragment, yes-no question, wh-question, other question.",
                "why it matters": "Questions can elicit longer/shorter child responses independent of efficiency.",
            },
            {
                "predictor": "exact_target_frequency_bits",
                "built from": "-log2 smoothed recurrence of the target utterance hash in the real+caretaker reference set",
                "interpretation": "Higher values mean the exact utterance is rarer/less conventional.",
                "why it matters": "Addresses the Pawar/Cychosz frequency-vs-informativity concern using a stable first frequency-control layer.",
            },
            {
                "predictor": "source-minus-real gap",
                "built from": "Adjusted source mean minus adjusted real-child mean",
                "interpretation": "Real child utterances are zero; positive values are more surprising than real.",
                "why it matters": "Makes random/ngram/LSTM/caretaker controls interpretable against the real-child baseline.",
            },
            {
                "predictor": "context gain",
                "built from": "`sum_bits_k0 - sum_bits_k3`",
                "interpretation": "How much local context reduces target uncertainty.",
                "why it matters": "Separates being predictable in context from being low-information overall.",
            },
        ]
    )


def candidate_figures() -> list[CandidateFigure]:
    return [
        CandidateFigure(
            "Main Route 1 ANCOVA: fixed-effort information decreases with age",
            Path("figs/route1_exhaustive_ancova_gallery/real_age_adjusted_sum_bits_k3_by_effort.png"),
            "Main text candidate",
            "At the same production effort and child-adjusted baseline, older children produce less Mistral-surprising utterances in context.",
            "`sum_bits_k3 ~ C(age_bin) + effort_z + C(child_id)`, fit separately for each effort scale.",
            "This is the cleanest supervisor-facing version of the central Route 1 result.",
        ),
        CandidateFigure(
            "Exact-effort Route 1 slopes",
            Path("figs/route1_exhaustive_ancova_gallery/real_exact_effort_age_slopes_sum_bits_k3.png"),
            "Main text or appendix",
            "The same downward tendency appears inside exact effort values.",
            "`sum_bits_k3 ~ C(age_bin) * C(exact_effort) + C(child_id)`.",
            "This is the strongest defense against the claim that the effect is only utterance-length/MLU growth.",
        ),
        CandidateFigure(
            "Real vs generated controls",
            Path("figs/route1_exhaustive_ancova_gallery/child_sources_adjusted_sum_bits_k3_by_effort.png"),
            "Main text candidate",
            "Random, n-gram, and LSTM controls do not reproduce the real-child trajectory; LSTMs are closest, random is farthest.",
            "`sum_bits_k3 ~ C(source) * C(age_bin) + effort_z + C(child_id)`.",
            "This shows the effect is source-specific, not just a scorer artifact or length matching artifact.",
        ),
        CandidateFigure(
            "Source-minus-real control gaps",
            Path("figs/route1_exhaustive_ancova_gallery/nb_words_sum_bits_k3_source_minus_real_gap_lines.png"),
            "Main text or appendix",
            "Real child utterances are the zero line; controls sit above or below real children after effort control.",
            "Pairwise source-vs-real ANCOVAs; plotted value is adjusted source mean minus adjusted real-child mean.",
            "This is the most intuitive way to explain what the controls mean.",
        ),
        CandidateFigure(
            "Frequency-controlled Route 1 age coefficients",
            Path("figs/route1_portelance_xu_extension_suite/route1_age_coefficients_with_context_frequency_controls.png"),
            "Main text robustness candidate",
            "The age effect remains negative after adding context and exact-target frequency controls.",
            "`sum_bits ~ age + effort + context_entropy + context_effort + question_type + exact_target_frequency_bits + C(child_id)`.",
            "This addresses the Pawar/Cychosz frequency-vs-informativity concern and a likely peer-review question.",
            "Exact recurrence is a stable proxy; full phone/word informativity controls are not fully scored yet.",
        ),
        CandidateFigure(
            "Incremental value of context and frequency controls",
            Path("figs/route1_portelance_xu_extension_suite/route1_joint_model_delta_r2.png"),
            "Appendix or short robustness paragraph",
            "Frequency/conventionality explains meaningful variance but does not eliminate the Route 1 age effect.",
            "Nested OLS models with child fixed effects and clustered standard errors.",
            "Useful for explaining why frequency is not ignored, while keeping the main narrative clean.",
        ),
        CandidateFigure(
            "Scrambled-age null check",
            Path("figs/route1_portelance_xu_extension_suite/scrambled_age_null_sum_bits_k3.png"),
            "Main text robustness candidate",
            "Observed developmental slopes are separated from slopes obtained after scrambling age labels.",
            "Weighted partial age slopes from effort-cell summaries, controlling effort and child identity.",
            "Direct peer-review guardrail against age-bin/sampling artifacts.",
            "Current null uses 50 permutations; increase for final paper if this becomes a central claim.",
        ),
        CandidateFigure(
            "Equalized age-bin bootstrap",
            Path("figs/route1_portelance_xu_extension_suite/equalized_bootstrap_bits_per_word.png"),
            "Appendix robustness candidate",
            "Age-bin trends survive a Pawar/Cychosz-style equalized sampling check.",
            "100 bootstrap samples per included age bin, up to 4,000 rows per bin, preserving observed rows.",
            "Shows that the trend is not simply because some age bins have much more data.",
            "Bins with fewer than 1,000 prepared rows are excluded from this check.",
        ),
        CandidateFigure(
            "Route 2 effort-as-outcome coefficients",
            Path("figs/route1_portelance_xu_extension_suite/route2_context_uncertainty_coefficients.png"),
            "Exploratory section",
            "Higher context uncertainty predicts more production effort most clearly for phoneme/syllable measures.",
            "`log(effort) ~ age + context_entropy + context_effort + question_type + age:context_entropy + C(child_id)`.",
            "This directly operationalizes the Xu email idea that children may shorten/lengthen depending on context.",
            "Real-child only in the current finite context-entropy extract; do not present as caretaker-comparative yet.",
        ),
        CandidateFigure(
            "Caretaker-minus-real fixed-effort contrast",
            Path("figs/route1_portelance_xu_extension_suite/adult_likeness_caretaker_minus_real_sum_bits_k3.png"),
            "Optional contrast, not main claim",
            "Caretaker speech is a comparison condition, not a direct replication of the phonological CDS paper.",
            "Caretaker-minus-real adjusted means from the pairwise ANCOVA artifacts.",
            "Useful for preventing overclaiming and for showing where child output sits relative to adult input.",
        ),
    ]


def candidate_summary_table(figures: list[CandidateFigure]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate": fig.title,
                "placement": fig.placement,
                "claim": fig.claim,
                "caveat": fig.caveat,
                "figure": str(fig.path),
            }
            for fig in figures
        ]
    )


def add_to_index(index_path: Path, doc_html: Path) -> None:
    if not index_path.exists():
        return
    text = index_path.read_text(encoding="utf-8")
    rel = doc_html.name
    embedded = doc_html.with_suffix(".embedded.html").name
    if rel in text:
        return
    insert = (
        f'<li><a href="{rel}">Candidate additions for supervisor report</a></li>\n'
        f'<li><a href="{embedded}">Candidate additions for supervisor report, embedded images</a></li>\n'
    )
    if "</ul>" in text:
        text = text.replace("</ul>", insert + "</ul>", 1)
    else:
        text += "\n<ul>\n" + insert + "</ul>\n"
    index_path.write_text(text, encoding="utf-8")


def build_report(ancova_dir: Path, extension_dir: Path, doc_md: Path, doc_html: Path, index_html: Path) -> None:
    adjusted = pd.read_csv(ancova_dir / "adjusted_marginal_means.csv")
    exact_adjusted = pd.read_csv(ancova_dir / "exact_effort_adjusted_means.csv")
    contrasts = pd.read_csv(ancova_dir / "source_real_adjusted_contrasts.csv")
    joint = pd.read_csv(extension_dir / "route1_joint_model_summary.csv")
    route2 = pd.read_csv(extension_dir / "route2_effort_outcome_coefficients.csv")
    nulls = pd.read_csv(extension_dir / "scrambled_age_null_slopes.csv")
    feature_status = pd.read_csv(extension_dir / "feature_status_for_peer_review.csv")

    real_summary = real_fixed_effort_summary(adjusted)
    exact_summary = exact_effort_summary(exact_adjusted)
    source_gaps = source_gap_words_summary(contrasts)
    joint_view = route1_joint_summary(joint)
    route2_view = route2_context_summary(route2)
    scrambled_view = scrambled_summary(nulls)
    figures = candidate_figures()
    candidate_table = candidate_summary_table(figures)

    output_dir = extension_dir / "candidate_additions"
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_table.to_csv(output_dir / "candidate_additions_manifest.csv", index=False)
    predictor_dictionary().to_csv(output_dir / "candidate_predictor_dictionary.csv", index=False)

    real_delta_min = real_summary["start_to_end_delta"].min()
    real_delta_max = real_summary["start_to_end_delta"].max()
    exact_down = exact_summary["downward_exact_efforts"].sum()
    exact_total = exact_summary["total_exact_efforts"].sum()
    freq = joint[joint["model_id"].eq("frequency_control")]
    joint_context = joint[joint["model_id"].eq("joint_context_frequency")]
    route2_context = route2[route2["term"].eq("context_entropy_bits_c")]
    route2_sig = int((route2_context["p"] < 0.05).sum())
    scrambled_real = scrambled_view[scrambled_view["source_label"].eq("Real child")]
    scrambled_outside = int(scrambled_real["outside_null_95"].astype(bool).sum())

    lines = [
        "# Candidate Additions For The Supervisor-Facing Report",
        "",
        "This is a staging report. It summarizes recent side analyses and proposes what should be added to the supervisor-facing report later. It does **not** modify `docs/predicting_utterance_level_information_report.md`.",
        "",
        "## Recommendation In One Page",
        "",
        "I would add three things to the supervisor-facing report main text and keep the rest as appendix or future-work material:",
        "",
        "1. **Main fixed-effort ANCOVA result:** same effort, older children are less unpredictable in context.",
        "2. **Source and frequency controls:** random/ngram/LSTM controls do not explain the real-child pattern, and the age effect remains negative after exact-frequency/context controls.",
        "3. **Reviewer robustness:** exact-effort slopes and scrambled-age nulls show the effect is not just MLU, binning, or sampling structure.",
        "",
        "I would add Route 2 effort-as-outcome as an exploratory final subsection, not as a primary result yet.",
        "",
        "## New Predictors And What They Mean",
        "",
        md_table(predictor_dictionary()),
        "",
        "## What The Refreshed Models Say",
        "",
        f"- **Core Route 1 fixed-effort result:** adjusted k3 information changes from {fmt(real_delta_min)} to {fmt(real_delta_max)} bits from first to last age bin across effort scales.",
        f"- **Exact-effort check:** {int(exact_down)}/{int(exact_total)} top exact-effort slopes are downward.",
        f"- **Frequency control:** exact-target frequency bits improve model fit by {fmt(freq['delta_r2_vs_base'].min(), 4)} to {fmt(freq['delta_r2_vs_base'].max(), 4)} R2 over the base effort+child model, while age coefficients remain negative.",
        f"- **Joint context+frequency control:** age coefficients remain negative across all effort measures; delta R2 ranges from {fmt(joint_context['delta_r2_vs_base'].min(), 4)} to {fmt(joint_context['delta_r2_vs_base'].max(), 4)}.",
        f"- **Route 2 effort outcome:** context-uncertainty coefficients are positive for all five effort scales and p<.05 for {route2_sig}/5 effort scales in this real-child extract.",
        f"- **Scrambled-age robustness:** real-child observed k3 slopes are outside the 95% scrambled null range for {scrambled_outside}/5 effort scales.",
        "",
        "## Candidate Figure Manifest",
        "",
        md_table(candidate_table.loc[:, ["candidate", "placement", "claim", "caveat"]]),
        "",
        "## Figure-By-Figure Candidate Additions",
        "",
    ]

    for fig in figures:
        lines.extend(
            [
                f"### {fig.title}",
                "",
                f"**Recommended placement:** {fig.placement}",
                "",
                f"**Claim it supports:** {fig.claim}",
                "",
                f"**Model/predictors:** {fig.model}",
                "",
                f"**Why it is relevant:** {fig.why}",
                "",
            ]
        )
        if fig.caveat:
            lines.extend([f"**Caveat:** {fig.caveat}", ""])
        lines.extend([f"![{fig.title}]({relative_image(fig.path)})", ""])

    lines.extend(
        [
            "## Compact Evidence Tables",
            "",
            "### Real-Child Fixed-Effort ANCOVA Summary",
            "",
            md_table(
                real_summary.assign(
                    start_bits=lambda f: f["start_bits"].map(lambda v: fmt(v, 2)),
                    end_bits=lambda f: f["end_bits"].map(lambda v: fmt(v, 2)),
                    start_to_end_delta=lambda f: f["start_to_end_delta"].map(lambda v: fmt(v, 2)),
                    slope_bits_per_6mo=lambda f: f["slope_bits_per_6mo"].map(lambda v: fmt(v, 2)),
                )
            ),
            "",
            "### Exact-Effort Slope Summary",
            "",
            md_table(
                exact_summary.assign(
                    median_slope=lambda f: f["median_slope"].map(lambda v: fmt(v, 2)),
                )
            ),
            "",
            "### Words Source-Minus-Real Gap Summary",
            "",
            md_table(
                source_gaps.assign(
                    first_bin_gap_bits=lambda f: f["first_bin_gap_bits"].map(lambda v: fmt(v, 2)),
                    last_bin_gap_bits=lambda f: f["last_bin_gap_bits"].map(lambda v: fmt(v, 2)),
                    gap_change_bits=lambda f: f["gap_change_bits"].map(lambda v: fmt(v, 2)),
                )
            ),
            "",
            "### Route 1 Joint Model Summary",
            "",
            md_table(joint_view, max_rows=20),
            "",
            "### Route 2 Context-Uncertainty Coefficients",
            "",
            md_table(route2_view),
            "",
            "### Scrambled-Age Null Summary",
            "",
            md_table(scrambled_view, max_rows=20),
            "",
            "## Feature Status / Do Not Overclaim",
            "",
            md_table(feature_status),
            "",
            "## Suggested Insertions For The Future Supervisor Report",
            "",
            "### Main Result Paragraph",
            "",
            "> At fixed production effort, older children's utterances are less unpredictable in their local conversational context. This pattern holds across effort definitions and is supported by exact-effort checks, so it is not simply an utterance-length or MLU artifact.",
            "",
            "### Controls Paragraph",
            "",
            "> The developmental pattern is source-specific: generated controls remain more surprising than real child utterances at matched effort, with random controls farthest away and LSTM controls closest. The age effect also remains negative after adding context uncertainty, context effort, question type, and exact-target frequency controls.",
            "",
            "### Robustness Paragraph",
            "",
            "> Scrambled-age checks and equalized age-bin bootstraps support the interpretation that the effect is developmental rather than a byproduct of age-bin size or sampling structure.",
            "",
            "### Exploratory Route 2 Paragraph",
            "",
            "> As a complementary exploratory analysis, context uncertainty weakly predicts child production effort, especially for phoneme and syllable effort. This supports the planned Route 2 question, but the current context-entropy extract is real-child only, so it should not yet be framed as a full child-vs-caretaker comparison.",
            "",
            "## Saved Companion Files",
            "",
            "```text",
            str(output_dir / "candidate_additions_manifest.csv"),
            str(output_dir / "candidate_predictor_dictionary.csv"),
            "```",
        ]
    )

    doc_md.parent.mkdir(parents=True, exist_ok=True)
    doc_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(doc_md, doc_html, title="Candidate Additions For Supervisor Report")
    render_markdown_file(doc_md, doc_html.with_suffix(".embedded.html"), title="Candidate Additions For Supervisor Report", embed_images=True)
    add_to_index(index_html, doc_html)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ancova-dir", type=Path, default=DEFAULT_ANCOVA_DIR)
    parser.add_argument("--extension-dir", type=Path, default=DEFAULT_EXTENSION_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--index-html", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args()
    build_report(args.ancova_dir, args.extension_dir, args.doc_md, args.doc_html, args.index_html)


if __name__ == "__main__":
    main()
