#!/usr/bin/env python3
"""Build visual HTML exports for the completed Route 1 atlas outputs."""

from __future__ import annotations

import argparse
import html
import textwrap
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


SOURCE_ROOT = Path("results/route1_corrected_baseline_atlas/full_source_specific")
STRUCTURE_ROOT = Path("results/route1_corrected_baseline_atlas/full_child_structure_sensitivity")
CARETAKER_ROOT = Path("results/route1_caretaker_atlas/full_fit")

BASE_CSS = """
:root {
  color-scheme: light;
  --ink: #1f2933;
  --muted: #52606d;
  --line: #d9e2ec;
  --panel: #f7f9fb;
  --accent: #0f766e;
}
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: white;
  line-height: 1.45;
}
main {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 28px 56px;
}
h1, h2, h3 { line-height: 1.15; }
h1 { font-size: 34px; margin: 0 0 8px; }
h2 { margin-top: 34px; border-bottom: 1px solid var(--line); padding-bottom: 8px; }
p, li { color: var(--muted); }
.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 12px;
  margin: 22px 0;
}
.metric {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px 14px;
  background: var(--panel);
}
.metric strong {
  display: block;
  color: var(--ink);
  font-size: 22px;
}
.figure-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
  gap: 18px;
  align-items: start;
}
figure {
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  background: white;
}
figure img { width: 100%; height: auto; display: block; }
figcaption { margin-top: 8px; color: var(--muted); font-size: 13px; }
.table-wrap {
  max-height: 540px;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
}
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { border-bottom: 1px solid var(--line); padding: 6px 8px; vertical-align: top; }
th { position: sticky; top: 0; background: #eef3f8; text-align: left; z-index: 1; }
.note {
  background: #ecfdf5;
  border-left: 4px solid var(--accent);
  padding: 12px 14px;
  border-radius: 6px;
}
details {
  margin-top: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px 14px;
}
summary { cursor: pointer; font-weight: 700; }
pre {
  white-space: pre-wrap;
  overflow-x: auto;
  background: #111827;
  color: #f9fafb;
  padding: 12px;
  border-radius: 6px;
}
@media print {
  main { max-width: none; padding: 18px; }
  .figure-grid { display: block; }
  figure { page-break-inside: avoid; margin-bottom: 14px; }
  .table-wrap { max-height: none; overflow: visible; }
  th { position: static; }
}
"""


def slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_heatmap(data: pd.DataFrame, path: Path, *, title: str, fmt: str = ".3f") -> Path:
    ensure_dir(path.parent)
    plt.figure(figsize=(max(7, 0.6 * len(data.columns)), max(3.8, 0.45 * len(data.index))))
    sns.heatmap(data, annot=True, fmt=fmt, cmap="viridis", linewidths=0.3, cbar_kws={"label": "mean R2"})
    plt.title(title)
    plt.xlabel("")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def save_count_heatmap(data: pd.DataFrame, path: Path, *, title: str) -> Path:
    ensure_dir(path.parent)
    plt.figure(figsize=(max(7, 0.6 * len(data.columns)), max(3.4, 0.45 * len(data.index))))
    sns.heatmap(data, annot=True, fmt=".0f", cmap="Blues", linewidths=0.3, cbar=False)
    plt.title(title)
    plt.xlabel("")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()
    return path


def table_html(frame: pd.DataFrame, *, max_rows: int | None = None) -> str:
    shown = frame if max_rows is None else frame.head(max_rows)
    return '<div class="table-wrap">' + shown.to_html(index=False, escape=False, border=0) + "</div>"


def metric(label: str, value: object) -> str:
    return f'<div class="metric"><span>{html.escape(label)}</span><strong>{html.escape(str(value))}</strong></div>'


def figure_block(path: Path, report_dir: Path, caption: str) -> str:
    rel = path.relative_to(report_dir)
    return (
        "<figure>"
        f'<img src="{html.escape(rel.as_posix())}" alt="{html.escape(caption)}">'
        f"<figcaption>{html.escape(caption)}</figcaption>"
        "</figure>"
    )


def write_html(
    *,
    path: Path,
    title: str,
    subtitle: str,
    metrics: Sequence[tuple[str, object]],
    figures: Sequence[tuple[Path, str]],
    tables: Sequence[tuple[str, pd.DataFrame, int | None]],
    note: str,
    markdown_path: Path | None = None,
) -> Path:
    ensure_dir(path.parent)
    report_dir = path.parent
    metrics_html = "\n".join(metric(label, value) for label, value in metrics)
    figure_html = "\n".join(figure_block(fig_path, report_dir, caption) for fig_path, caption in figures)
    table_sections = []
    for heading, frame, max_rows in tables:
        table_sections.append(f"<h2>{html.escape(heading)}</h2>\n{table_html(frame, max_rows=max_rows)}")
    original = ""
    if markdown_path and markdown_path.exists():
        original_text = markdown_path.read_text(encoding="utf-8")
        original = (
            "<details><summary>Original Markdown technical report</summary>"
            f"<pre>{html.escape(original_text)}</pre>"
            "</details>"
        )
    body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{BASE_CSS}</style>
</head>
<body>
<main>
<h1>{html.escape(title)}</h1>
<p>{html.escape(subtitle)}</p>
<div class="note">{html.escape(note)}</div>
<section class="meta">{metrics_html}</section>
<h2>Visual Checks</h2>
<section class="figure-grid">{figure_html}</section>
{''.join(table_sections)}
{original}
</main>
</body>
</html>
"""
    path.write_text(body, encoding="utf-8")
    return path


def source_figures(summary: pd.DataFrame, source: str, report_dir: Path) -> list[tuple[Path, str]]:
    fig_dir = report_dir / "figures"
    data = summary[summary["target_source"].eq(source)].copy()
    data["r2"] = pd.to_numeric(data["r2"], errors="coerce")
    figures: list[tuple[Path, str]] = []
    pivot = data.pivot_table(index="context_k", columns="model_id", values="r2", aggfunc="mean")
    path = save_heatmap(pivot, fig_dir / f"{slugify(source)}_r2_by_context_model.png", title=f"{source}: mean R2 by context and model")
    figures.append((path, "Mean R2 by context window and model family, averaged over effort units."))
    pivot = data.pivot_table(index="effort_label", columns="context_k", values="r2", aggfunc="mean")
    path = save_heatmap(pivot, fig_dir / f"{slugify(source)}_r2_by_effort_context.png", title=f"{source}: mean R2 by effort and context")
    figures.append((path, "Mean R2 by effort unit and context window, averaged over model families."))
    counts = data.pivot_table(index="context_k", columns="status", values="model_id", aggfunc="count", fill_value=0)
    path = save_count_heatmap(counts, fig_dir / f"{slugify(source)}_status_counts.png", title=f"{source}: model status counts")
    figures.append((path, "Model fit status counts by context window."))
    return figures


def build_source_reports() -> list[Path]:
    summary_path = SOURCE_ROOT / "source_specific_model_summary.csv"
    if not summary_path.exists():
        return []
    summary = pd.read_csv(summary_path)
    report_dir = SOURCE_ROOT / "reports"
    outputs: list[Path] = []
    for source in sorted(summary["target_source"].dropna().unique()):
        data = summary[summary["target_source"].eq(source)].copy()
        status_counts = data["status"].value_counts().rename_axis("status").reset_index(name="rows")
        figures = source_figures(summary, source, report_dir)
        compact = data[
            [
                "model_id",
                "model_label",
                "model_tier",
                "context_k",
                "effort_label",
                "child_structure",
                "n_obs",
                "n_children",
                "status",
                "r2",
                "aic",
                "bic",
                "error",
            ]
        ].copy()
        compact["r2"] = pd.to_numeric(compact["r2"], errors="coerce").round(4)
        md_path = report_dir / f"{slugify(source)}_route1_corrected_atlas.md"
        html_path = report_dir / f"{slugify(source)}_route1_corrected_atlas.html"
        outputs.append(
            write_html(
                path=html_path,
                title=f"Corrected Route 1 Atlas: {source}",
                subtitle="Source-specific child/baseline atlas with visual fit diagnostics.",
                metrics=[
                    ("model rows", len(data)),
                    ("fit rows", int(data["status"].eq("fit").sum())),
                    ("contexts", ", ".join(sorted(data["context_k"].astype(str).unique()))),
                    ("effort units", data["effort_col"].nunique()),
                ],
                figures=figures,
                tables=[("Status Counts", status_counts, None), ("Model Summary", compact, None)],
                note="This HTML/PDF export is generated from the completed CSV fit outputs. It adds plots to the original technical Markdown.",
                markdown_path=md_path,
            )
        )
    overview = summary.copy()
    overview["r2"] = pd.to_numeric(overview["r2"], errors="coerce")
    fig_dir = report_dir / "figures"
    pivot = overview.pivot_table(index="target_source", columns="context_k", values="r2", aggfunc="mean")
    overview_fig = save_heatmap(pivot, fig_dir / "source_specific_overview_r2_by_source_context.png", title="Source-specific atlas: mean R2 by source/context")
    status = overview.groupby(["target_source", "status"], dropna=False).size().reset_index(name="rows")
    source_rows = overview.groupby("target_source", dropna=False).agg(
        rows=("model_id", "size"),
        fit_rows=("status", lambda s: int((s == "fit").sum())),
        mean_r2=("r2", "mean"),
        min_n_obs=("n_obs", "min"),
    ).reset_index()
    source_rows["mean_r2"] = source_rows["mean_r2"].round(4)
    outputs.append(
        write_html(
            path=report_dir / "source_specific_visual_overview.html",
            title="Corrected Route 1 Source-Specific Atlas: Visual Overview",
            subtitle="All child and generated-baseline source-specific fits.",
            metrics=[
                ("sources", overview["target_source"].nunique()),
                ("model rows", len(overview)),
                ("fit rows", int(overview["status"].eq("fit").sum())),
                ("contexts", ", ".join(sorted(overview["context_k"].astype(str).unique()))),
            ],
            figures=[(overview_fig, "Mean R2 by target source and context window.")],
            tables=[("Source Summary", source_rows, None), ("Status Counts", status, None)],
            note="Use this overview first, then open the per-source HTML/PDF reports for detailed tables.",
        )
    )
    return outputs


def build_child_structure_report() -> list[Path]:
    summary_path = STRUCTURE_ROOT / "source_specific_model_summary.csv"
    if not summary_path.exists():
        return []
    summary = pd.read_csv(summary_path)
    report_dir = STRUCTURE_ROOT / "reports"
    fig_dir = report_dir / "figures"
    summary["r2"] = pd.to_numeric(summary["r2"], errors="coerce")
    figures: list[tuple[Path, str]] = []
    pivot = summary.pivot_table(index="child_structure", columns="model_id", values="r2", aggfunc="mean")
    figures.append(
        (
            save_heatmap(pivot, fig_dir / "child_structure_r2_by_structure_model.png", title="Child-structure sensitivity: mean R2"),
            "Mean R2 by child-identity/correlation structure and core model.",
        )
    )
    pivot = summary.pivot_table(index="effort_label", columns="child_structure", values="r2", aggfunc="mean")
    figures.append(
        (
            save_heatmap(pivot, fig_dir / "child_structure_r2_by_effort_structure.png", title="Child-structure sensitivity: effort summaries"),
            "Mean R2 by effort unit and child-structure variant.",
        )
    )
    status = summary.groupby(["child_structure", "status"], dropna=False).size().reset_index(name="rows")
    compact = summary[
        [
            "model_id",
            "model_label",
            "child_structure",
            "estimator",
            "covariance",
            "effort_label",
            "n_obs",
            "n_children",
            "status",
            "r2",
            "error",
        ]
    ].copy()
    compact["r2"] = compact["r2"].round(4)
    html_path = report_dir / "real_route1_corrected_atlas.html"
    return [
        write_html(
            path=html_path,
            title="Corrected Route 1 Atlas: Child-Structure Sensitivity",
            subtitle="Real-child k3 sensitivity across child identity and correlation structures.",
            metrics=[
                ("model rows", len(summary)),
                ("fit rows", int(summary["status"].eq("fit").sum())),
                ("structures", summary["child_structure"].nunique()),
                ("effort units", summary["effort_col"].nunique()),
            ],
            figures=figures,
            tables=[("Status Counts", status, None), ("Model Summary", compact, None)],
            note="This is the sensitivity stage for the real child source, separate from the source-specific baseline atlas.",
            markdown_path=report_dir / "real_route1_corrected_atlas.md",
        )
    ]


def build_caretaker_report() -> list[Path]:
    summary_path = CARETAKER_ROOT / "caretaker_model_summary.csv"
    if not summary_path.exists():
        return []
    summary = pd.read_csv(summary_path)
    report_dir = CARETAKER_ROOT / "reports"
    fig_dir = report_dir / "figures"
    summary["r2"] = pd.to_numeric(summary["r2"], errors="coerce")
    figures: list[tuple[Path, str]] = []
    fit_only = summary[summary["status"].eq("fit")].copy()
    pivot = fit_only.pivot_table(index="context_k", columns="model_id", values="r2", aggfunc="mean")
    figures.append(
        (
            save_heatmap(pivot, fig_dir / "caretaker_r2_by_context_model.png", title="Caretaker atlas: mean R2 by context/model"),
            "Mean R2 by context window and caretaker model family, fit rows only.",
        )
    )
    pivot = fit_only.pivot_table(index="effort_label", columns="context_k", values="r2", aggfunc="mean")
    figures.append(
        (
            save_heatmap(pivot, fig_dir / "caretaker_r2_by_effort_context.png", title="Caretaker atlas: mean R2 by effort/context"),
            "Mean R2 by effort unit and context window, averaged over model families.",
        )
    )
    counts = summary.pivot_table(index="context_k", columns="status", values="model_id", aggfunc="count", fill_value=0)
    figures.append(
        (
            save_count_heatmap(counts, fig_dir / "caretaker_status_counts.png", title="Caretaker atlas: status counts"),
            "Fit/skipped counts by context window. k0 skips are expected for context-dependent models.",
        )
    )
    prediction_path = CARETAKER_ROOT / "caretaker_fixed_effort_predictions.csv"
    if prediction_path.exists():
        pred = pd.read_csv(prediction_path)
        pred = pred[
            pred["model_id"].isin(["CM1", "CM3", "CM5"])
            & pred["effort_col"].eq("nb_words")
            & pred["context_k"].isin(["k1", "k2", "k3"])
        ].copy()
        if not pred.empty:
            plt.figure(figsize=(10, 6))
            sns.lineplot(
                data=pred,
                x="age_months",
                y="predicted_sum_bits",
                hue="model_id",
                style="context_k",
                units="effort_value",
                estimator=None,
                alpha=0.65,
            )
            plt.title("Caretaker fixed-word trajectories, selected models")
            plt.xlabel("Child age in months")
            plt.ylabel("Predicted caretaker sum bits")
            plt.tight_layout()
            path = fig_dir / "caretaker_fixed_word_trajectories_selected_models.png"
            ensure_dir(path.parent)
            plt.savefig(path, dpi=180)
            plt.close()
            figures.append((path, "Fixed-word predicted caretaker trajectories for selected model families."))
    status = summary.groupby(["context_k", "status"], dropna=False).size().reset_index(name="rows")
    compact = summary[
        [
            "model_id",
            "model_label",
            "context_k",
            "effort_label",
            "n_obs",
            "n_dyads",
            "n_speakers",
            "status",
            "r2",
            "error",
        ]
    ].copy()
    compact["r2"] = pd.to_numeric(compact["r2"], errors="coerce").round(4)
    return [
        write_html(
            path=report_dir / "caretaker_route1_atlas.html",
            title="Caretaker Route 1 Atlas",
            subtitle="Entropy-free caretaker-target atlas using focal child age as the timeline.",
            metrics=[
                ("model rows", len(summary)),
                ("fit rows", int(summary["status"].eq("fit").sum())),
                ("skipped rows", int(summary["status"].eq("skipped").sum())),
                ("contexts", ", ".join(sorted(summary["context_k"].astype(str).unique()))),
            ],
            figures=figures,
            tables=[("Status Counts", status, None), ("Model Summary", compact, None)],
            note="The skipped rows are expected k0 context-control models, where preceding-context effort/question type cannot vary.",
            markdown_path=report_dir / "caretaker_route1_atlas.md",
        )
    ]


def build_all() -> list[Path]:
    outputs: list[Path] = []
    outputs.extend(build_source_reports())
    outputs.extend(build_child_structure_report())
    outputs.extend(build_caretaker_report())
    return outputs


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-list", type=Path, default=Path("results/route1_atlas_visual_exports_html_files.txt"))
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    outputs = build_all()
    ensure_dir(args.write_list.parent)
    args.write_list.write_text("\n".join(str(path) for path in outputs) + "\n", encoding="utf-8")
    for path in outputs:
        print(f"[OK] {path}")
    print(f"[OK] html list: {args.write_list}")


if __name__ == "__main__":
    main()
