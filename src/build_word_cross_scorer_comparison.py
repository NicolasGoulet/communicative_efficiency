#!/usr/bin/env python3
"""Compare PBM word-effect directions across separately fitted scorers."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from itertools import combinations
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PRIMARY_MODELS = {
    "same_word_k0_primary",
    "same_word_k3_primary",
    "context_gain_k3_primary",
    "integrative_between_primary__unweighted",
    "integrative_between_primary__token_weighted",
    "integrative_within_primary",
}


SCIENTIFIC_QUESTIONS = (
    {
        "question_id": "same_word_k0_age",
        "question": "Does unconditional surprisal for the same word decrease with age?",
        "model_id": "same_word_k0_primary",
        "term": "age_c",
        "role": "registered supporting",
    },
    {
        "question_id": "same_word_k3_age",
        "question": "Does contextual surprisal for the same word decrease with age?",
        "model_id": "same_word_k3_primary",
        "term": "age_c",
        "role": "registered directional supporting",
    },
    {
        "question_id": "context_gain_age",
        "question": "Does word-level context gain change with age?",
        "model_id": "context_gain_k3_primary",
        "term": "age_c",
        "role": "registered two-sided supporting",
    },
    {
        "question_id": "longer_words_context_support",
        "question": "At the centered age, do longer word types receive more contextual support?",
        "model_id": "integrative_between_primary__unweighted",
        "term": "word_char_length_c",
        "role": "registered primary",
    },
    {
        "question_id": "length_support_age_change",
        "question": "Does the longer-word context-support association change with age?",
        "model_id": "integrative_between_primary__unweighted",
        "term": "word_char_length_c:age_c",
        "role": "registered primary",
    },
    {
        "question_id": "rarity_support_age_change",
        "question": "Does the rarity-context-support association change with age?",
        "model_id": "integrative_between_primary__unweighted",
        "term": "log_frequency_lco_c:age_c",
        "role": "registered primary",
    },
    {
        "question_id": "within_word_length_age_change",
        "question": "Within word type, does the age trend in context gain vary by word length?",
        "model_id": "integrative_within_primary",
        "term": "age_c:word_char_length_c",
        "role": "registered companion",
    },
    {
        "question_id": "k3_information_placement_age_change",
        "question": "Does the within-utterance k3 information-position gradient change with age?",
        "model_id": "placement_k3_primary",
        "term": "position_c:age_c",
        "role": "registered supporting",
    },
)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(value, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        frame.to_csv(temporary, index=False)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.stem}.tmp-{os.getpid()}{path.suffix}")
    try:
        fig.savefig(temporary, dpi=180, bbox_inches="tight")
        os.replace(temporary, path)
    finally:
        plt.close(fig)
        temporary.unlink(missing_ok=True)


def parse_scorer(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--scorer must be LABEL=/path/to/analysis")
    label, path = value.split("=", 1)
    return label.strip(), Path(path).resolve()


def load_scorer(
    label: str, root: Path
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], dict[str, object]]:
    audit = json.loads((root / "audit_all.json").read_text())
    model = json.loads((root / "models" / "model_manifest.json").read_text())
    if audit.get("status") != "PASS" or model.get("status") != "PASS":
        raise RuntimeError(
            f"{label} is not analysis-ready: audit={audit.get('status')} model={model.get('status')}"
        )
    coefficients = pd.read_csv(root / "models" / "coefficients.csv")
    slopes = pd.read_csv(root / "models" / "unit_slopes.csv")
    feature = json.loads((root / "features" / "feature_manifest.json").read_text())
    if feature.get("status") != "PASS":
        raise RuntimeError(
            f"{label} is not analysis-ready: feature={feature.get('status')}"
        )
    coefficients.insert(0, "scorer", label)
    slopes.insert(0, "scorer", label)
    return coefficients, slopes, feature, model


def sign_label(value: float, low: float, high: float) -> str:
    direction = "positive" if value > 0 else "negative" if value < 0 else "zero"
    support = "excludes_zero" if low > 0 or high < 0 else "includes_zero"
    return f"{direction}_{support}"


def _interval_excludes_zero(low: object, high: object) -> bool:
    if pd.isna(low) or pd.isna(high):
        return False
    return bool(float(low) > 0 or float(high) < 0)


def build_question_summary(
    coefficients: pd.DataFrame, scorer_labels: Sequence[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reduce registered coefficients to the actual scientific questions.

    Raw magnitudes remain scorer-specific.  Only signs and within-scorer
    interval support are summarized across scorers.
    """

    summary_rows: list[dict[str, object]] = []
    effect_rows: list[pd.DataFrame] = []
    expected_scorers = set(scorer_labels)
    for specification in SCIENTIFIC_QUESTIONS:
        selected = coefficients[
            coefficients["model_id"].eq(specification["model_id"])
            & coefficients["term"].eq(specification["term"])
        ].copy()
        if selected.empty:
            continue
        actual_scorers = set(selected["scorer"])
        if actual_scorers != expected_scorers or selected["scorer"].duplicated().any():
            raise RuntimeError(
                f"{specification['question_id']} does not have exactly one row per scorer: "
                f"expected={sorted(expected_scorers)} actual={sorted(actual_scorers)}"
            )
        selected.insert(1, "question_id", specification["question_id"])
        selected.insert(2, "question", specification["question"])
        selected.insert(3, "scientific_role", specification["role"])
        selected["cluster_interval_excludes_zero"] = [
            _interval_excludes_zero(row.ci_low, row.ci_high)
            for row in selected.itertuples(index=False)
        ]
        bootstrap_available = (
            selected.get("bootstrap_ci_low", pd.Series(np.nan, index=selected.index)).notna()
            & selected.get("bootstrap_ci_high", pd.Series(np.nan, index=selected.index)).notna()
        )
        selected["bootstrap_interval_available"] = bootstrap_available
        selected["bootstrap_interval_excludes_zero"] = [
            _interval_excludes_zero(low, high)
            for low, high in zip(
                selected.get("bootstrap_ci_low", pd.Series(np.nan, index=selected.index)),
                selected.get("bootstrap_ci_high", pd.Series(np.nan, index=selected.index)),
            )
        ]
        signs = {int(np.sign(value)) for value in selected["estimate"]}
        same_sign = len(signs) == 1 and 0 not in signs
        direction = (
            "positive"
            if same_sign and next(iter(signs)) > 0
            else "negative"
            if same_sign
            else "mixed"
        )
        cluster_supported = int(selected["cluster_interval_excludes_zero"].sum())
        bootstrap_count = int(selected["bootstrap_interval_available"].sum())
        bootstrap_supported = int(
            (
                selected["bootstrap_interval_available"]
                & selected["bootstrap_interval_excludes_zero"]
            ).sum()
        )
        fully_supported = cluster_supported == len(scorer_labels) and (
            bootstrap_count == 0 or bootstrap_supported == bootstrap_count
        )
        if not same_sign:
            replication_status = "scorer_dependent"
        elif fully_supported:
            replication_status = "direction_and_interval_robust"
        else:
            replication_status = "direction_robust_partial_uncertainty"
        summary_rows.append(
            {
                "question_id": specification["question_id"],
                "question": specification["question"],
                "scientific_role": specification["role"],
                "common_direction": direction,
                "scorers": len(scorer_labels),
                "cluster_supported_scorers": cluster_supported,
                "bootstrap_available_scorers": bootstrap_count,
                "bootstrap_supported_scorers": bootstrap_supported,
                "replication_status": replication_status,
            }
        )
        effect_rows.append(selected)
    if not summary_rows:
        raise RuntimeError("no registered scientific-question coefficients are available")
    return pd.DataFrame(summary_rows), pd.concat(effect_rows, ignore_index=True)


def _question_evidence_figure(
    question_effects: pd.DataFrame,
    scorer_labels: Sequence[str],
    path: Path,
) -> None:
    question_order = [
        item["question_id"]
        for item in SCIENTIFIC_QUESTIONS
        if item["question_id"] in set(question_effects["question_id"])
    ]
    labels = {
        item["question_id"]: item["question"] for item in SCIENTIFIC_QUESTIONS
    }
    matrix = (
        question_effects.pivot(index="question_id", columns="scorer", values="estimate")
        .reindex(index=question_order, columns=scorer_labels)
        .apply(np.sign)
    )
    support = question_effects.pivot(
        index="question_id", columns="scorer", values="cluster_interval_excludes_zero"
    ).reindex(index=question_order, columns=scorer_labels)
    fig, ax = plt.subplots(figsize=(7.6, max(4.8, len(matrix) * 0.72)))
    image = ax.imshow(matrix.to_numpy(float), vmin=-1, vmax=1, cmap="PiYG", aspect="auto")
    for row_index, question_id in enumerate(matrix.index):
        for column_index, scorer in enumerate(matrix.columns):
            estimate_sign = matrix.loc[question_id, scorer]
            marker = "●" if bool(support.loc[question_id, scorer]) else "○"
            direction = "+" if estimate_sign > 0 else "−" if estimate_sign < 0 else "0"
            ax.text(column_index, row_index, f"{direction} {marker}", ha="center", va="center", fontsize=11)
    ax.set(
        xticks=np.arange(len(scorer_labels)),
        xticklabels=scorer_labels,
        yticks=np.arange(len(matrix)),
        yticklabels=[labels[item] for item in matrix.index],
        title="Registered word-information evidence by scorer",
    )
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    fig.colorbar(image, ax=ax, ticks=[-1, 0, 1], label="coefficient direction")
    fig.text(0.01, 0.01, "Filled circle: clustered 95% interval excludes zero; open circle: includes zero.", fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    atomic_figure(fig, path)


def compare(scorers: Sequence[tuple[str, Path]], output_dir: Path, fig_dir: Path, report_md: Path, report_html: Path) -> dict[str, object]:
    coefficients = []; slopes = []; coverage = []; model_manifests = []; feature_manifests = []
    for label, root in scorers:
        coefficient, unit_slope, feature, model = load_scorer(label, root)
        coefficients.append(coefficient); slopes.append(unit_slope)
        model_manifests.append(model)
        feature_manifests.append(feature)
        coverage.append({"scorer": label, "rows": feature["rows"], "lexical_eligible_rows": feature["lexical_eligible_rows"], "primary_rows": feature["primary_rows"], "children": feature["children"], "corpora": feature["corpora"]})
    registry_hashes = {str(item.get("registry_sha256", "")) for item in model_manifests}
    if len(registry_hashes) != 1 or "" in registry_hashes:
        raise RuntimeError(
            f"cross-scorer inputs do not share one recorded registry hash: {sorted(registry_hashes)}"
        )
    identity_hashes = {
        str(item.get("primary_occurrence_identity_sha256", ""))
        for item in feature_manifests
    }
    if len(identity_hashes) != 1 or "" in identity_hashes:
        raise RuntimeError(
            "cross-scorer inputs do not share one exact supported occurrence identity hash: "
            f"{sorted(identity_hashes)}"
        )
    scorer_labels = [label for label, _ in scorers]
    all_coefficients = pd.concat(coefficients, ignore_index=True)
    question_summary, question_effects = build_question_summary(
        all_coefficients, scorer_labels
    )
    primary = all_coefficients[all_coefficients["model_id"].isin(PRIMARY_MODELS) & ~all_coefficients["term"].eq("Intercept")].copy()
    primary["direction_support"] = [sign_label(row.estimate, row.ci_low, row.ci_high) for row in primary.itertuples(index=False)]
    sign_wide = primary.pivot_table(index=["model_id", "term"], columns="scorer", values="estimate", aggfunc="first").reset_index()
    sign_wide["all_same_sign"] = sign_wide[scorer_labels].apply(
        lambda row: row.notna().all()
        and len({int(np.sign(value)) for value in row}) == 1,
        axis=1,
    )

    child = pd.concat(slopes, ignore_index=True)
    child = child[child["level"].eq("child")]
    concordance_rows = []
    for left, right in combinations(scorer_labels, 2):
        left_frame = child[child["scorer"].eq(left)][["unit", "outcome", "age_slope"]].rename(columns={"age_slope": "left_slope"})
        right_frame = child[child["scorer"].eq(right)][["unit", "outcome", "age_slope"]].rename(columns={"age_slope": "right_slope"})
        paired = left_frame.merge(right_frame, on=["unit", "outcome"], validate="one_to_one")
        for outcome, group in paired.groupby("outcome", observed=True):
            concordance_rows.append({"left": left, "right": right, "outcome": outcome, "children": len(group), "sign_agreement": float((np.sign(group["left_slope"]) == np.sign(group["right_slope"])).mean())})
    concordance = pd.DataFrame(concordance_rows)
    output_dir.mkdir(parents=True, exist_ok=True); fig_dir.mkdir(parents=True, exist_ok=True)
    if primary.empty or sign_wide.empty:
        raise RuntimeError("no complete registered primary coefficient rows are available")
    tables = {
        "primary_coefficients": output_dir / "primary_coefficients_by_scorer.csv",
        "primary_sign_concordance": output_dir / "primary_sign_concordance.csv",
        "child_slope_sign_concordance": output_dir / "child_slope_sign_concordance.csv",
        "occurrence_coverage": output_dir / "occurrence_coverage_by_scorer.csv",
        "scientific_question_summary": output_dir / "scientific_question_summary.csv",
        "scientific_question_effects": output_dir / "scientific_question_effects_by_scorer.csv",
    }
    atomic_frame(primary, tables["primary_coefficients"])
    atomic_frame(sign_wide, tables["primary_sign_concordance"])
    atomic_frame(concordance, tables["child_slope_sign_concordance"])
    atomic_frame(pd.DataFrame(coverage), tables["occurrence_coverage"])
    atomic_frame(question_summary, tables["scientific_question_summary"])
    atomic_frame(question_effects, tables["scientific_question_effects"])

    matrix = sign_wide.set_index(sign_wide["model_id"] + " · " + sign_wide["term"])[scorer_labels].apply(np.sign)
    fig, ax = plt.subplots(figsize=(7.5, max(4, len(matrix) * .35)))
    image = ax.imshow(matrix.to_numpy(float), vmin=-1, vmax=1, cmap="PiYG", aspect="auto")
    ax.set(xticks=np.arange(len(scorer_labels)), xticklabels=scorer_labels, yticks=np.arange(len(matrix)), yticklabels=matrix.index, title="Direction of registered PBM word effects")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right"); fig.colorbar(image, ax=ax, ticks=[-1, 0, 1], label="negative / zero / positive")
    fig.tight_layout(); atomic_figure(fig, fig_dir / "primary_effect_direction_matrix.png")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    if not concordance.empty:
        labels = concordance["left"] + " vs " + concordance["right"] + " · " + concordance["outcome"]
        ax.barh(labels, concordance["sign_agreement"], color="#2d777d")
    ax.axvline(.5, color="black", linestyle="--", linewidth=.8); ax.set(xlim=(0, 1), xlabel="Proportion of children with matching slope sign", title="Child-level cross-scorer sign agreement")
    fig.tight_layout(); atomic_figure(fig, fig_dir / "child_slope_sign_agreement.png")

    question_figure = fig_dir / "scientific_question_evidence_matrix.png"
    _question_evidence_figure(question_effects, scorer_labels, question_figure)

    agreement = int(sign_wide["all_same_sign"].sum()); total = len(sign_wide)
    question_rows = "\n".join(
        "| {question} | {common_direction} | {cluster_supported_scorers}/{scorers} | "
        "{bootstrap_supported_scorers}/{bootstrap_available_scorers} | {replication_status} |".format(
            **row
        )
        for row in question_summary.to_dict("records")
    )
    robust_questions = question_summary[
        question_summary["replication_status"].eq("direction_and_interval_robust")
    ]["question"].tolist()
    dependent_questions = question_summary[
        question_summary["replication_status"].eq("scorer_dependent")
    ]["question"].tolist()
    robust_text = "; ".join(robust_questions) or "none"
    dependent_text = "; ".join(dependent_questions) or "none"
    markdown = f"""# PBM Word-Information Cross-Scorer Comparison

Mistral, Qwen3-14B, and TinyDialogues were fit separately on the same registered word-occurrence estimands. **Raw coefficient magnitudes are not treated as calibrated across tokenizers.** This report compares direction, uncertainty labels, occurrence coverage, and child-level sign agreement.

- All registered primary-model coefficient directions shared by all scorers: `{agreement}/{total}`. This broad diagnostic includes nuisance controls and is not the scientific headline.
- PBM is one discovery sample; scorer repetition is robustness, not independent-sample confirmation.

## Question-by-question evidence

| Scientific question | Common direction | Cluster interval support | Bootstrap interval support | Assessment |
| --- | --- | ---: | ---: | --- |
{question_rows}

- Direction and interval robust across scorers: {robust_text}.
- Scorer-dependent direction: {dependent_text}.

![Scientific question evidence]({os.path.relpath(question_figure, report_md.parent)})

Filled circles mark scorer-specific clustered 95% intervals excluding zero; open circles include zero. Child-bootstrap support is reported separately in the table.

## Full registered-coefficient diagnostic

![Primary direction matrix]({os.path.relpath(fig_dir / 'primary_effect_direction_matrix.png', report_md.parent)})

## Child-level agreement

![Child slope sign agreement]({os.path.relpath(fig_dir / 'child_slope_sign_agreement.png', report_md.parent)})

## Guardrails

- Word surprisal is scorer-based predictability, not semantic information or listener utility.
- Positive context gain means k3 context reduced surprisal for the exact word occurrence.
- A difference in raw bits or bits/month between models is not interpreted as a calibrated effect-size difference.
- Null and contrary directions remain visible.
"""
    atomic_text(report_md, markdown)
    table = primary[["scorer", "model_id", "term", "estimate", "ci_low", "ci_high", "direction_support"]].to_html(index=False)
    question_table = question_summary.rename(
        columns={
            "question": "Scientific question",
            "common_direction": "Direction",
            "cluster_supported_scorers": "Cluster-supported scorers",
            "bootstrap_supported_scorers": "Bootstrap-supported scorers",
            "replication_status": "Assessment",
        }
    )[
        [
            "Scientific question",
            "Direction",
            "Cluster-supported scorers",
            "Bootstrap-supported scorers",
            "Assessment",
        ]
    ].to_html(index=False)
    atomic_text(report_html, f"<!doctype html><html><head><meta charset='utf-8'><title>PBM Word Cross-Scorer Comparison</title><style>body{{font:15px/1.5 system-ui;max-width:1100px;margin:35px auto;padding:0 24px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd5d3;padding:.4em;vertical-align:top}}th{{background:#e5efed}}img{{max-width:100%}}.warning{{background:#fff3cd;padding:1em;border-left:5px solid #b58900}}</style></head><body><h1>PBM Word-Information Cross-Scorer Comparison</h1><p>Scorers were fit separately on the same registered occurrence set. Raw score and coefficient magnitudes are not pooled or treated as calibrated across tokenizers.</p><div class='warning'>PBM is one discovery sample. Three-scorer agreement is robustness, not independent-sample confirmation.</div><h2>Question-by-question evidence</h2>{question_table}<img src='{html.escape(os.path.relpath(question_figure, report_html.parent))}'><p>Filled circles mark clustered 95% intervals excluding zero; open circles include zero. Child-bootstrap support remains separately recorded.</p><h2>Child-level agreement</h2><img src='{html.escape(os.path.relpath(fig_dir / 'child_slope_sign_agreement.png', report_html.parent))}'><h2>Full registered-coefficient diagnostic</h2><p>{agreement}/{total} primary-model coefficient directions agree, but this includes nuisance controls and is not the scientific headline.</p><img src='{html.escape(os.path.relpath(fig_dir / 'primary_effect_direction_matrix.png', report_html.parent))}'><h2>Registered estimates</h2>{table}</body></html>")
    artifacts = [
        *tables.values(),
        fig_dir / "primary_effect_direction_matrix.png",
        fig_dir / "child_slope_sign_agreement.png",
        question_figure,
        report_md,
        report_html,
    ]
    report = {"status": "PASS", "scorers": scorer_labels, "registry_sha256": next(iter(registry_hashes)), "primary_occurrence_identity_sha256": next(iter(identity_hashes)), "primary_terms": total, "all_same_sign": agreement, "scientific_questions": len(question_summary), "direction_and_interval_robust_questions": int(question_summary["replication_status"].eq("direction_and_interval_robust").sum()), "scorer_dependent_questions": int(question_summary["replication_status"].eq("scorer_dependent").sum()), "output_dir": str(output_dir), "report_md": str(report_md), "report_html": str(report_html), "artifacts": [{"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in artifacts]}
    atomic_text(output_dir / "manifest.json", json.dumps(report, indent=2) + "\n")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scorer", action="append", type=parse_scorer, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results/word_cross_scorer_comparison"))
    parser.add_argument("--fig-dir", type=Path, default=Path("figs/word_cross_scorer_comparison"))
    parser.add_argument("--report-md", type=Path, default=Path("docs/word_cross_scorer_comparison.md"))
    parser.add_argument("--report-html", type=Path, default=Path("docs/word_cross_scorer_comparison.html"))
    args = parser.parse_args(argv)
    if len(args.scorer) < 2:
        parser.error("at least two --scorer inputs are required")
    print(json.dumps(compare(args.scorer, args.output_dir, args.fig_dir, args.report_md, args.report_html), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
