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
    all_coefficients = pd.concat(coefficients, ignore_index=True)
    primary = all_coefficients[all_coefficients["model_id"].isin(PRIMARY_MODELS) & ~all_coefficients["term"].eq("Intercept")].copy()
    primary["direction_support"] = [sign_label(row.estimate, row.ci_low, row.ci_high) for row in primary.itertuples(index=False)]
    sign_wide = primary.pivot_table(index=["model_id", "term"], columns="scorer", values="estimate", aggfunc="first").reset_index()
    scorer_labels = [label for label, _ in scorers]
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
    }
    atomic_frame(primary, tables["primary_coefficients"])
    atomic_frame(sign_wide, tables["primary_sign_concordance"])
    atomic_frame(concordance, tables["child_slope_sign_concordance"])
    atomic_frame(pd.DataFrame(coverage), tables["occurrence_coverage"])

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

    agreement = int(sign_wide["all_same_sign"].sum()); total = len(sign_wide)
    markdown = f"""# PBM Word-Information Cross-Scorer Comparison

Mistral, Qwen3-14B, and TinyDialogues were fit separately on the same registered word-occurrence estimands. **Raw coefficient magnitudes are not treated as calibrated across tokenizers.** This report compares direction, uncertainty labels, occurrence coverage, and child-level sign agreement.

- Primary coefficient-term directions shared by all scorers: `{agreement}/{total}`.
- PBM is one discovery sample; scorer repetition is robustness, not independent-sample confirmation.

## Direction matrix

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
    atomic_text(report_html, f"<!doctype html><html><head><meta charset='utf-8'><title>PBM Word Cross-Scorer Comparison</title><style>body{{font:15px/1.5 system-ui;max-width:1100px;margin:35px auto}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd5d3;padding:.4em}}th{{background:#e5efed}}img{{max-width:100%}}</style></head><body><h1>PBM Word-Information Cross-Scorer Comparison</h1><p>Scorers were fit separately. Raw score and coefficient magnitudes are not pooled or treated as calibrated across tokenizers.</p><p>Shared primary directions: {agreement}/{total}.</p><img src='{html.escape(os.path.relpath(fig_dir / 'primary_effect_direction_matrix.png', report_html.parent))}'><img src='{html.escape(os.path.relpath(fig_dir / 'child_slope_sign_agreement.png', report_html.parent))}'><h2>Registered estimates</h2>{table}</body></html>")
    artifacts = [
        *tables.values(),
        fig_dir / "primary_effect_direction_matrix.png",
        fig_dir / "child_slope_sign_agreement.png",
        report_md,
        report_html,
    ]
    report = {"status": "PASS", "scorers": scorer_labels, "registry_sha256": next(iter(registry_hashes)), "primary_occurrence_identity_sha256": next(iter(identity_hashes)), "primary_terms": total, "all_same_sign": agreement, "output_dir": str(output_dir), "report_md": str(report_md), "report_html": str(report_html), "artifacts": [{"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in artifacts]}
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
