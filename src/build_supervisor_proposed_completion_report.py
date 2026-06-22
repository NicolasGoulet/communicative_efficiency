#!/usr/bin/env python3
"""Build a side-draft proposed completion of the supervisor-facing report.

This script intentionally leaves the current supervisor-facing report unchanged.
It reads that report as a base, inserts a proposed completion section using the
current Route 1 real-vs-controls artifacts, and writes a separate Markdown/HTML
draft for manual reworking.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


BASE_MD = Path("docs/predicting_utterance_level_information_report.md")
OUT_MD = Path("docs/predicting_utterance_level_information_report_proposed_completion.md")
OUT_HTML = Path("docs/predicting_utterance_level_information_report_proposed_completion.html")
INDEX_HTML = Path("docs/route1_current_reports_browser_index.html")

REAL_VS_CONTROLS_DIR = Path("results/route1_real_vs_controls_context_report")
CHILD_SUITE_DIR = Path("results/route1_child_length_controlled_model_suite")
CANDIDATE_DIR = Path("results/route1_candidate_evidence_gallery")
BEST_MODEL_DIR = Path("results/route1_best_model_robustness_package")
AGE_SCRAMBLE_DIR = Path("results/age_scrambling_robustness")

SOURCE_ORDER = [
    "Real child",
    "Random",
    "Unigram",
    "Bigram",
    "Trigram",
    "LSTM k3",
    "LSTM k4",
    "LSTM k5",
    "Caretaker",
]


def fmt_number(value: object, digits: int = 3) -> str:
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


def md_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows._"
    view = frame.loc[:, columns].fillna("").astype(str)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in view.iterrows():
        values = [str(row[col]).replace("|", "\\|") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def weighted_mean(frame: pd.DataFrame, value_col: str, weight_col: str = "n") -> float:
    weights = pd.to_numeric(frame[weight_col], errors="coerce")
    values = pd.to_numeric(frame[value_col], errors="coerce")
    mask = weights.notna() & values.notna()
    if not mask.any():
        return math.nan
    return float((values[mask] * weights[mask]).sum() / weights[mask].sum())


def source_overview_table(source_age: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for source_label, group in source_age.groupby("source_label", sort=False):
        rows.append(
            {
                "source": source_label,
                "rows": int(group["n"].sum()),
                "mean_k0": weighted_mean(group, "mean_sum_bits_k0"),
                "mean_k3": weighted_mean(group, "mean_sum_bits_k3"),
                "context_gain": weighted_mean(group, "mean_context_gain"),
                "mean_words": weighted_mean(group, "mean_nb_words"),
            }
        )
    out = pd.DataFrame(rows)
    out["order"] = out["source"].map(lambda source: SOURCE_ORDER.index(source) if source in SOURCE_ORDER else 99)
    out = out.sort_values("order").drop(columns=["order"])
    for col in ["mean_k0", "mean_k3", "context_gain", "mean_words"]:
        out[col] = out[col].map(lambda value: fmt_number(value, 2))
    out["rows"] = out["rows"].map(lambda value: f"{int(value):,}")
    return out


def primary_slope_table(slope_diff: pd.DataFrame) -> pd.DataFrame:
    table = slope_diff[slope_diff["common_model_id"].eq("M2")].copy()
    table["order"] = table["source_label"].map(lambda source: SOURCE_ORDER.index(source) if source in SOURCE_ORDER else 99)
    table = table.sort_values("order")
    out = pd.DataFrame(
        {
            "comparison source": table["source_label"],
            "real slope": table["real_slope_bits_per_6_months"].map(lambda value: fmt_number(value, 3)),
            "source slope": table["source_slope_bits_per_6_months"].map(lambda value: fmt_number(value, 3)),
            "source - real": table["source_minus_real_slope"].map(lambda value: fmt_number(value, 3)),
            "source downward lines": table["downward_lines"].astype(int).astype(str)
            + "/"
            + table["total_lines"].astype(int).astype(str),
        }
    )
    return out


def paired_gap_table(diff_models: pd.DataFrame) -> pd.DataFrame:
    wanted = diff_models[
        diff_models["model_kind"].isin(["paired_gap_k3", "paired_context_gain_gap"])
        & diff_models["source_label"].isin(SOURCE_ORDER)
    ].copy()
    wanted["test"] = wanted["model_kind"].map(
        {
            "paired_gap_k3": "k3 source-real gap",
            "paired_context_gain_gap": "context-gain source-real gap",
        }
    )
    wanted["mean"] = wanted["mean_outcome"].map(lambda value: fmt_number(value, 3))
    wanted["age slope"] = wanted["age_coef"].map(lambda value: fmt_number(value, 3))
    wanted["p"] = wanted["age_p"].map(fmt_p)
    wanted["n"] = wanted["n"].astype(int).map(lambda value: f"{value:,}")
    wanted["order"] = wanted["source_label"].map(lambda source: SOURCE_ORDER.index(source) if source in SOURCE_ORDER else 99)
    wanted["test_order"] = wanted["model_kind"].map({"paired_gap_k3": 0, "paired_context_gain_gap": 1})
    wanted = wanted.sort_values(["order", "test_order"])
    return wanted[["source_label", "test", "mean", "age slope", "p", "n"]].rename(columns={"source_label": "source"})


def caretaker_gap_table(diff_models: pd.DataFrame) -> pd.DataFrame:
    wanted = diff_models[diff_models["source"].eq("caretaker")].copy()
    if wanted.empty:
        return wanted
    out = pd.DataFrame(
        {
            "outcome": wanted["outcome"],
            "real mean": wanted["mean_real"].map(lambda value: fmt_number(value, 3)),
            "caretaker mean": wanted["mean_control"].map(lambda value: fmt_number(value, 3)),
            "source x age": wanted["source_age_coef"].map(lambda value: fmt_number(value, 3)),
            "p": wanted["source_age_p"].map(fmt_p),
            "n": wanted["n"].astype(int).map(lambda value: f"{value:,}"),
        }
    )
    return out


def img(path: str, alt: str) -> str:
    return f"![{alt}]({path})"


def source_visual_block(slug: str, label: str, include_regression: bool = True) -> list[str]:
    lines = [
        f"#### {label}",
        "",
        img(f"../figs/route1_real_vs_controls_context_report/{slug}_k0_vs_k3_age_means.png", f"{label} k0 versus k3 age means"),
        "",
        img(f"../figs/route1_real_vs_controls_context_report/{slug}_context_gain_by_age.png", f"{label} context gain through age"),
        "",
        img(f"../figs/route1_real_vs_controls_context_report/{slug}_k3_with_context_focus.png", f"{label} with-context k3 focus"),
        "",
    ]
    if include_regression:
        lines.extend(
            [
                img(
                    f"../figs/route1_real_vs_controls_context_report/{slug}_m2_k3_fixed_word_regression_lines.png",
                    f"{label} fixed-word regression lines",
                ),
                "",
                img(
                    f"../figs/route1_real_vs_controls_context_report/{slug}_m2_k3_fixed_word_regression_gaps.png",
                    f"{label} fixed-word source-minus-real regression gaps",
                ),
                "",
                img(
                    f"../figs/route1_real_vs_controls_context_report/{slug}_k3_word_model_slope_differences.png",
                    f"{label} model slope differences",
                ),
                "",
            ]
        )
    return lines


def candidate_model_ladder_table() -> pd.DataFrame:
    data = pd.read_csv(CANDIDATE_DIR / "real_k3_words_model_ladder_importance.csv")
    out = data[
        [
            "model_id",
            "model_label",
            "r2_observed_fitted",
            "delta_r2_vs_m2",
            "age_coef",
            "age_p",
            "effort_coef",
            "effort_p",
            "parent_context_effort_coef",
            "context_entropy_coef",
            "age_effort_coef",
        ]
    ].copy()
    out = out.rename(
        columns={
            "model_id": "model",
            "model_label": "role",
            "r2_observed_fitted": "R2",
            "delta_r2_vs_m2": "delta R2 vs M2",
            "age_coef": "age bits/month",
            "age_p": "age p",
            "effort_coef": "effort bits/word",
            "effort_p": "effort p",
            "parent_context_effort_coef": "parent effort",
            "context_entropy_coef": "context entropy",
            "age_effort_coef": "age x effort",
        }
    )
    for col in ["R2", "delta R2 vs M2", "age bits/month", "effort bits/word", "parent effort", "context entropy", "age x effort"]:
        out[col] = out[col].map(lambda value: fmt_number(value, 3))
    for col in ["age p", "effort p"]:
        out[col] = out[col].map(fmt_p)
    return out


def child_formula_summary_table() -> pd.DataFrame:
    summaries = pd.read_csv(CHILD_SUITE_DIR / "model_summary.csv")
    slopes = pd.read_csv(CHILD_SUITE_DIR / "fixed_slice_slopes.csv")
    formulas = pd.read_csv(CHILD_SUITE_DIR / "formula_definitions.csv")
    row = summaries[summaries["estimator_id"].eq("row_ols_fe_cluster")].copy()
    agg = summaries[summaries["estimator_id"].eq("agg_gee_gaussian")].copy()
    mix = summaries[summaries["estimator_id"].eq("agg_mixed_random_age_slope")].copy()

    direction = (
        slopes[slopes["estimator_id"].eq("row_ols_fe_cluster")]
        .groupby("formula_id")["direction"]
        .agg(
            downward=lambda values: int((values == "downward").sum()),
            upward=lambda values: int((values == "upward").sum()),
            total="size",
        )
        .reset_index()
    )
    out = formulas[["formula_id", "label", "tier", "uses_exact_effort_category"]].merge(
        row[["formula_id", "r2_observed_fitted", "n_obs"]], on="formula_id", how="left"
    )
    out = out.merge(
        agg[["formula_id", "r2_observed_fitted"]].rename(columns={"r2_observed_fitted": "agg_gee_R2"}),
        on="formula_id",
        how="left",
    )
    out = out.merge(
        mix[["formula_id", "r2_observed_fitted"]].rename(columns={"r2_observed_fitted": "mixed_age_R2"}),
        on="formula_id",
        how="left",
    )
    out = out.merge(direction, on="formula_id", how="left")
    table = pd.DataFrame(
        {
            "formula": out["formula_id"] + ": " + out["label"],
            "tier": out["tier"],
            "row R2": out["r2_observed_fitted"].map(lambda value: fmt_number(value, 3)),
            "agg GEE R2": out["agg_gee_R2"].map(lambda value: fmt_number(value, 3)),
            "mixed age R2": out["mixed_age_R2"].map(lambda value: fmt_number(value, 3)),
            "row slope directions": out["downward"].fillna(0).astype(int).astype(str)
            + " down / "
            + out["total"].fillna(0).astype(int).astype(str),
        }
    )
    return table


def exact_length_table() -> pd.DataFrame:
    slopes = pd.read_csv(CHILD_SUITE_DIR / "fixed_slice_slopes.csv")
    sub = slopes[
        slopes["estimator_id"].eq("row_ols_fe_cluster")
        & slopes["formula_id"].isin(["F18", "F19", "F20", "F21"])
    ].copy()
    rows = []
    for (formula_id, formula_label), group in sub.groupby(["formula_id", "formula_label"], sort=True):
        rows.append(
            {
                "formula": f"{formula_id}: {formula_label}",
                "min slope/6mo": fmt_number(group["slope_bits_per_6_months"].min(), 3),
                "max slope/6mo": fmt_number(group["slope_bits_per_6_months"].max(), 3),
                "downward lines": f"{int((group['direction'] == 'downward').sum())}/{len(group)}",
                "upward lengths": ", ".join(
                    str(int(value))
                    for value in group.loc[group["direction"].eq("upward"), "fixed_effort_value"].tolist()
                )
                or "none",
            }
        )
    return pd.DataFrame(rows)


def estimator_family_table() -> pd.DataFrame:
    data = pd.read_csv(CHILD_SUITE_DIR / "model_summary.csv")
    grouped = (
        data[data["status"].eq("fit")]
        .groupby(["estimator_id", "estimator_label", "frame_kind"], as_index=False)
        .agg(
            fit_formulas=("formula_id", "nunique"),
            median_R2=("r2_observed_fitted", "median"),
            max_R2=("r2_observed_fitted", "max"),
            n_rows=("n_obs", "median"),
        )
    )
    order = [
        "row_ols_fe_cluster",
        "agg_ols_fe_cluster",
        "agg_gee_gaussian",
        "agg_gee_gamma_log",
        "agg_glm_gaussian",
        "agg_glm_gamma_log",
        "agg_mixed_random_intercept",
        "agg_mixed_random_age_slope",
        "agg_mixed_session_intercept",
    ]
    grouped["order"] = grouped["estimator_id"].map(lambda value: order.index(value) if value in order else 99)
    grouped = grouped.sort_values("order")
    out = pd.DataFrame(
        {
            "estimator": grouped["estimator_label"],
            "frame": grouped["frame_kind"],
            "fit formulas": grouped["fit_formulas"].astype(int).astype(str),
            "median R2": grouped["median_R2"].map(lambda value: fmt_number(value, 3)),
            "max R2": grouped["max_R2"].map(lambda value: fmt_number(value, 3)),
            "median n": grouped["n_rows"].map(lambda value: f"{int(value):,}"),
        }
    )
    return out


def age_scramble_table() -> pd.DataFrame:
    data = pd.read_csv(AGE_SCRAMBLE_DIR / "age_scrambling_robustness_summary.csv")
    sub = data[
        data["context_k"].eq("k3")
        & data["effort_col"].eq("nb_words")
        & data["model_id"].isin(["M2", "M3", "M4", "M5", "M6"])
        & data["robustness_method"].isin(["balanced_bootstrap", "age_bin_group_scramble", "unit_age_scramble", "within_child_age_scramble"])
    ].copy()
    sub["order"] = sub["model_id"].map({"M2": 0, "M3": 1, "M4": 2, "M5": 3, "M6": 4})
    sub["method_order"] = sub["robustness_method"].map(
        {
            "balanced_bootstrap": 0,
            "age_bin_group_scramble": 1,
            "unit_age_scramble": 2,
            "within_child_age_scramble": 3,
        }
    )
    sub = sub.sort_values(["order", "method_order"])
    out = pd.DataFrame(
        {
            "model": sub["model_id"],
            "check": sub["robustness_label"],
            "observed age": sub["observed_age_coef"].map(lambda value: fmt_number(value, 3)),
            "null 95%": sub["null_q025_age_coef"].map(lambda value: fmt_number(value, 3))
            + " to "
            + sub["null_q975_age_coef"].map(lambda value: fmt_number(value, 3)),
            "outside null": sub["observed_outside_null_95"].map(lambda value: "yes" if bool(value) else "no"),
            "p": sub["two_sided_permutation_p"].map(fmt_p),
        }
    )
    return out


def heldout_slope_table() -> pd.DataFrame:
    data = pd.read_csv(CANDIDATE_DIR / "heldout_pop_m4c_actual_vs_predicted_regression_slopes.csv")
    out = pd.DataFrame(
        {
            "child": data["child_key"],
            "effort band": data["effort_band"],
            "actual slope/month": data["actual_slope_bits_per_month"].map(lambda value: fmt_number(value, 3)),
            "predicted slope/month": data["predicted_slope_bits_per_month"].map(lambda value: fmt_number(value, 3)),
            "month points": data["actual_month_points"].astype(int).astype(str),
        }
    )
    return out


def proposed_completion_section() -> str:
    source_age = pd.read_csv(REAL_VS_CONTROLS_DIR / "source_age_summary.csv")
    diff_models = pd.read_csv(REAL_VS_CONTROLS_DIR / "difference_model_summary.csv")
    slope_diff = pd.read_csv(REAL_VS_CONTROLS_DIR / "regression_line_slope_difference_summary.csv")

    overview = source_overview_table(source_age)
    primary_slopes = primary_slope_table(slope_diff)
    paired_gaps = paired_gap_table(diff_models)
    caretaker_gaps = caretaker_gap_table(diff_models)
    model_ladder = candidate_model_ladder_table()
    formula_suite = child_formula_summary_table()
    exact_lengths = exact_length_table()
    estimator_families = estimator_family_table()
    age_robustness = age_scramble_table()
    heldout_slopes = heldout_slope_table()

    return "\n".join(
        [
            "## Proposed Completion v2: Model-Rich Route 1 Synthesis",
            "",
            "This section is a proposed replacement for the weaker completion draft. It is intentionally model-rich: it promotes the strongest current analyses, shows what each model family contributes, and keeps the original supervisor-facing report untouched.",
            "",
            "The fixed scientific target remains: estimate conditional utterance information at fixed production effort, using repeated child utterances sampled across sessions and ages. The key distinction is that raw total bits can rise with utterance length, while the main developmental claim is about fitted information at the same effort level.",
            "",
            "### What Should Be Promoted",
            "",
            "I would promote the evidence in this order:",
            "",
            "1. **Primary row-level fixed-effort model:** age + child effort + child identity, with child-clustered uncertainty.",
            "2. **Exact-length proof:** exact word-count categories and exact-length age slopes, showing the result is not just MLU.",
            "3. **Context/confound controls:** parent-context effort, context entropy, question type, and richer interactions.",
            "4. **Estimator-family checks:** OLS, GEE, GLM, Gamma/log, and MixedLM variants on session/effort cells.",
            "5. **Age-label robustness:** balanced bootstrap and scrambled-age nulls.",
            "6. **Source specificity:** real children versus random, n-gram, LSTM, and caretaker targets.",
            "7. **Heldout prediction:** actual heldout child regression lines versus PBM-trained predicted lines.",
            "",
            "### Main Row-Level Model Ladder",
            "",
            "The table below is the current real-child k3/word model ladder. It is more important than a single Model 2 paragraph because it shows the age effect surviving the main confound controls. M1 is the pooled sanity check. M2 adds child identity and becomes the primary simple model. M4a/M4b/M4c add parent effort, context entropy, and question type. M5/M6 combine context controls. M15 is the richest current interaction stress test.",
            "",
            md_table(
                model_ladder,
                [
                    "model",
                    "role",
                    "R2",
                    "delta R2 vs M2",
                    "age bits/month",
                    "age p",
                    "effort bits/word",
                    "parent effort",
                    "context entropy",
                    "age x effort",
                ],
            ),
            "",
            img("../figs/route1_candidate_evidence_gallery/real_k3_words_model_ladder_r2_importance.png", "Real-child model ladder R2 and delta R2"),
            "",
            "The clean read is that the age coefficient stays negative once child identity and effort are controlled. Question type improves fit among the simple confound controls; context entropy and parent-context effort matter, but they do not erase the developmental fixed-effort result. The richest stress model still estimates a negative age coefficient.",
            "",
            "### Fixed-Effort Lines To Show First",
            "",
            "These are the plots I should have put into the proposed completion. They are not raw age means. They are fitted lines asking what happens to predicted k3 `sum_bits` when word count is held fixed.",
            "",
            img("../figs/route1_child_length_controlled_model_suite/f01_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png", "F01 row-level fixed-effort lines"),
            "",
            img("../figs/route1_child_length_controlled_model_suite/f07_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png", "F07 question-type controlled fixed-effort lines"),
            "",
            img("../figs/route1_child_length_controlled_model_suite/f12_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png", "F12 full context-interaction stress-test fixed-effort lines"),
            "",
            "F01 is the minimal defensible fixed-effort model. F07 adds question type. F12 is a richer context-interaction stress test. The reason to show all three is that the downward fixed-effort story is not limited to the simplest model.",
            "",
            "### Exact-Length Proof That This Is Not Just MLU",
            "",
            "This is the missing proof layer. The exact-length models replace continuous word count with exact word-count categories. F18 and F20 absorb exact length baselines. F19 and F21 allow separate age slopes inside exact word counts. The well-supported short and middle lengths remain mostly downward.",
            "",
            md_table(exact_lengths, ["formula", "min slope/6mo", "max slope/6mo", "downward lines", "upward lengths"]),
            "",
            img("../figs/route1_child_length_controlled_model_suite/mlu_proof_exact_length_age_slopes.png", "Exact-length age-slope proof plot"),
            "",
            img("../figs/route1_child_length_controlled_model_suite/f19_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png", "F19 exact-length age slopes"),
            "",
            img("../figs/route1_child_length_controlled_model_suite/f21_k3_nb_words_row_ols_fe_cluster_fixed_effort_lines.png", "F21 exact-length age slopes with context controls"),
            "",
            "This is where the report can answer the MLU objection directly: even after exact word-count categories are absorbed, the developmental trend is mostly downward. The upward lines are concentrated at sparse longer lengths, so they should be discussed as support-limited rather than promoted as the main signal.",
            "",
            "### Full Length-Controlled Model Suite",
            "",
            "The side draft should show that this is not one cherry-picked model. The length-controlled suite fits 21 formulas with row-level and aggregate/repeated-measures estimators. The row-level fixed-effect models all fit 446,985 utterances; aggregate models use session/effort cells.",
            "",
            md_table(formula_suite, ["formula", "tier", "row R2", "agg GEE R2", "mixed age R2", "row slope directions"]),
            "",
            img("../figs/route1_child_length_controlled_model_suite/slope_heatmap_formula_by_estimator.png", "Formula by estimator slope heatmap"),
            "",
            img("../figs/route1_child_length_controlled_model_suite/variance_explained_by_formula_estimator.png", "Variance explained by formula and estimator"),
            "",
            "### Estimator-Family Checks",
            "",
            "The estimator-family layer is appendix material, but it is powerful. It shows which conclusions are stable across OLS with child fixed effects, GEE, GLM, Gamma/log, and mixed-effects models. This should be used to defend the analysis if a supervisor asks whether ordinary OLS is too fragile for repeated utterance data.",
            "",
            md_table(estimator_families, ["estimator", "frame", "fit formulas", "median R2", "max R2", "median n"]),
            "",
            img("../figs/route1_best_model_robustness_package/aggregate_estimator_age_effect_forest.png", "Aggregate estimator age-effect forest"),
            "",
            img("../figs/route1_best_model_robustness_package/m15_aggregate_estimator_fixed_effort_age_lines.png", "M15 aggregate estimator fixed-effort lines"),
            "",
            "Important caveat: the aggregate estimator screen is not the same estimand as the row-level fixed-effort Atlas. It is a repeated-measures sensitivity screen over session/effort cells. It belongs as robustness, not as the lead result.",
            "",
            "### Age Scrambling And Balanced Bootstrap",
            "",
            "This is the best defense against the claim that the result is just age-bin composition or child/session imbalance. For the k3/word checks, observed slopes are compared with balanced and scrambled-age nulls.",
            "",
            md_table(age_robustness, ["model", "check", "observed age", "null 95%", "outside null", "p"]),
            "",
            img("../figs/age_scrambling_robustness/m2_clear_robustness_regression_lines.png", "M2 balanced and age-scrambled robustness"),
            "",
            img("../figs/age_scrambling_robustness/m6_clear_robustness_regression_lines.png", "M6 balanced and age-scrambled robustness"),
            "",
            img("../figs/age_scrambling_robustness/robustness_outside_null_heatmap.png", "Age-scrambling robustness heatmap"),
            "",
            "### Source Specificity: Real Children Versus Baselines And Caretakers",
            "",
            "The source-specific layer answers whether the real-child line is a property of real child speech or a mechanical artifact of the scoring pipeline. Random goes in the opposite direction. N-grams and LSTMs are closer but flatter. Caretakers also differ from the child trajectory.",
            "",
            md_table(primary_slopes, ["comparison source", "real slope", "source slope", "source - real", "source downward lines"]),
            "",
            img("../figs/route1_candidate_evidence_gallery/source_comparison_m4c_k3_words_slopes.png", "M4c source comparison slopes"),
            "",
            "The visual evidence should be shown source by source. For each comparison, the first panel contrasts no context (`k0`) with caretaker context (`k3`), the second panel plots the context gain through age, the third focuses only on the with-context condition, and the regression panels show the fixed-word-count model comparison.",
            "",
            *source_visual_block("random", "Real vs Random"),
            *source_visual_block("unigram", "Real vs Unigram"),
            *source_visual_block("bigram", "Real vs Bigram"),
            *source_visual_block("trigram", "Real vs Trigram"),
            *source_visual_block("lstm", "Real vs LSTM family"),
            *source_visual_block("caretaker", "Real vs Caretakers"),
            "The source-specific M4c Atlas panels are useful appendix figures because they put each source into the same corrected fixed-effort plotting grammar.",
            "",
            img("../figs/route1_source_specific_corrected_fixed_effort_atlas/real/real_k3_m4c_nb_words_fixed_effort_atlas.png", "Real child source-specific M4c Atlas"),
            "",
            img("../figs/route1_source_specific_corrected_fixed_effort_atlas/random/random_k3_m4c_nb_words_fixed_effort_atlas.png", "Random source-specific M4c Atlas"),
            "",
            img("../figs/route1_source_specific_corrected_fixed_effort_atlas/unigram/unigram_k3_m4c_nb_words_fixed_effort_atlas.png", "Unigram source-specific M4c Atlas"),
            "",
            img("../figs/route1_source_specific_corrected_fixed_effort_atlas/bigram/bigram_k3_m4c_nb_words_fixed_effort_atlas.png", "Bigram source-specific M4c Atlas"),
            "",
            img("../figs/route1_source_specific_corrected_fixed_effort_atlas/trigram/trigram_k3_m4c_nb_words_fixed_effort_atlas.png", "Trigram source-specific M4c Atlas"),
            "",
            img("../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k3_same_length/lstm_additive_k3_same_length_k3_m4c_nb_words_fixed_effort_atlas.png", "LSTM k3 source-specific M4c Atlas"),
            "",
            img("../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k4_same_length/lstm_additive_k4_same_length_k3_m4c_nb_words_fixed_effort_atlas.png", "LSTM k4 source-specific M4c Atlas"),
            "",
            img("../figs/route1_source_specific_corrected_fixed_effort_atlas/lstm_additive_k5_same_length/lstm_additive_k5_same_length_k3_m4c_nb_words_fixed_effort_atlas.png", "LSTM k5 source-specific M4c Atlas"),
            "",
            "Descriptive context means are still useful for orientation, but they are not the main inference because they are not fixed-effort regression estimates.",
            "",
            md_table(overview, ["source", "rows", "mean_k0", "mean_k3", "context_gain", "mean_words"]),
            "",
            "The paired generated-control models use the same original child utterance as the comparison unit. Positive k3 gaps mean that the generated control is more surprising than the real child utterance in the same context.",
            "",
            md_table(paired_gaps, ["source", "test", "mean", "age slope", "p", "n"]),
            "",
            "Caretakers are a different comparison because they are not generated alternatives for the same child row. They ask whether adult speech in the same families has the same child-age trajectory.",
            "",
            md_table(caretaker_gaps, ["outcome", "real mean", "caretaker mean", "source x age", "p", "n"]),
            "",
            "### Heldout Children",
            "",
            "The heldout panel is not the cleanest proof, but it is important because it makes generalization inspectable. Black lines are actual heldout child trends; dashed teal lines are PBM-trained predictions.",
            "",
            md_table(heldout_slopes, ["child", "effort band", "actual slope/month", "predicted slope/month", "month points"]),
            "",
            img("../figs/route1_candidate_evidence_gallery/heldout_pop_m4c_actual_vs_predicted_regression_lines.png", "Heldout actual versus predicted regression lines"),
            "",
            img("../figs/route1_candidate_evidence_gallery/heldout_pop_m4c_calibration_residuals.png", "Heldout calibration and residual diagnostics"),
            "",
            "### Candidate Supervisor Claim",
            "",
            "> At the same production-effort level, older children produce utterances that are more predictable in context than younger children. This fixed-effort developmental decrease appears in the primary row-level child-identity model, survives major context/form controls, remains visible in exact-length checks for well-supported word counts, is defended by age-scrambling robustness, and differs from random, n-gram, LSTM, and caretaker comparison patterns.",
            "",
            "The claim must stay conditional. It is not saying older children communicate less overall. Older children often produce longer utterances, and longer utterances carry more total bits. The claim is that among utterances of comparable effort, the model finds older children's utterances more contextually predictable.",
            "",
            "### What To Cut Or Keep For The Final Supervisor Version",
            "",
            "Keep in the main text: one primary fixed-effort figure, the exact-length proof figure, one compact model-ladder table, one age-scrambling figure, and one source-comparison figure.",
            "",
            "Move to appendix: the full F01-F21 table, the estimator-family table, heldout calibration, all paired source-gap model tables, and individual source-specific Atlas figures.",
            "",
            "Do not overclaim yet: Route 2 effort choice. The current report controls effort; it does not yet prove that children choose effort as a function of response-space context uncertainty.",
            "",
        ]
    )


def build_proposed_markdown(base_text: str) -> str:
    text = base_text.replace(
        "# Predicting Informational Content at the Utterance Level",
        "# Predicting Informational Content at the Utterance Level: Proposed Completion Draft",
        1,
    )
    text = text.replace(
        "Working draft, June 2026",
        "Proposed completion draft, June 2026\n\nThis side draft starts from the current supervisor-facing report and adds candidate completion text. The current supervisor-facing report files were not modified.",
        1,
    )
    text = text.replace("where the size of their vocabulary is expended", "where the size of their vocabulary is expanded")
    text = text.replace(
        "The planned LSTM comparison follows the same additive developmental logic as the\nn-gram baselines.",
        "The current LSTM comparison follows the same additive developmental logic as the\nn-gram baselines.",
    )
    text = text.replace(
        "The first LSTM comparison will use same-length generated utterances, so effort\nis held constant relative to the real child utterance.",
        "The current LSTM comparison uses same-length generated utterances, so effort\nis held constant relative to the real child utterance.",
    )
    marker = "\n## Possible Next Steps\n"
    completion = "\n" + proposed_completion_section()
    if marker not in text:
        return text.rstrip() + completion + "\n"
    before, after = text.split(marker, 1)
    return before.rstrip() + "\n" + completion + marker + after


def update_index(index_path: Path, report_html: Path, embedded_html: Path) -> None:
    if not index_path.exists():
        return
    text = index_path.read_text(encoding="utf-8")
    additions = [
        (report_html.name, "Supervisor proposed completion draft"),
        (embedded_html.name, "Supervisor proposed completion draft, embedded images"),
    ]
    insert = ""
    for href, label in additions:
        if href not in text:
            insert += f'\n<li><a href="{href}">{label}</a></li>'
    if not insert:
        return
    marker = "</ul>"
    if marker in text:
        text = text.replace(marker, insert + "\n" + marker, 1)
    else:
        text += insert
    index_path.write_text(text, encoding="utf-8")


def main() -> None:
    base_text = BASE_MD.read_text(encoding="utf-8")
    markdown = build_proposed_markdown(base_text)
    OUT_MD.write_text(markdown, encoding="utf-8")
    render_markdown_file(OUT_MD, OUT_HTML)
    embedded = OUT_MD.with_suffix(".embedded.html")
    render_markdown_file(OUT_MD, embedded, embed_images=True)
    update_index(INDEX_HTML, OUT_HTML, embedded)
    print(OUT_MD)
    print(OUT_HTML)
    print(embedded)


if __name__ == "__main__":
    main()
