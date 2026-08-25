#!/usr/bin/env python3
"""Build the restarted supervisor homepage and Data description page only.

The presentation deliberately follows the original July landing page: one
plain page of large links, with each substantive section living on its own
page.  This first pass exposes only Data description.  It does not fit models
or modify any earlier audited report.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from render_markdown_report import markdown_to_html


DEFAULT_INDEX_MD = Path("docs/supervisor_report.md")
DEFAULT_INDEX_HTML = Path("docs/supervisor_report.html")
DEFAULT_DATA_MD = Path("docs/supervisor_data_description.md")
DEFAULT_DATA_HTML = Path("docs/supervisor_data_description.html")
DEFAULT_OUTPUT_DIR = Path("results/supervisor_report/data_description")

PBM_CORPORA = {"Brown", "Manchester", "Providence"}
SCOPE_ORDER = ["pbm_discovery", "non_pbm_confirmation", "all79_descriptive"]
SCOPE_LABELS = {
    "pbm_discovery": "Brown, Manchester, and Providence",
    "non_pbm_confirmation": "Other 10 corpora",
    "all79_descriptive": "All 13 corpora combined",
}
AGE_ORDER = [
    "006-023",
    "024-029",
    "030-035",
    "036-041",
    "042-047",
    "048-053",
    "054-059",
    "060-065",
]

GALLERY_START = "<!-- AGE_DISTRIBUTION_GALLERY_START -->"
GALLERY_END = "<!-- AGE_DISTRIBUTION_GALLERY_END -->"

PROTECTED_PATHS = [
    Path("docs/august_supervisor_index.html"),
    Path("docs/august_supervisor_report.md"),
    Path("docs/august_supervisor_report.html"),
    Path("results/august_supervisor_report/AUGUST_REPORT_COMPLETE_AND_AUDITED"),
]

CSS = """
:root { --ink: #1e2528; --muted: #536267; --line: #d9e0df; --accent: #2f6f73; --paper: #ffffff; --soft: #fafbfb; --warm: #c76f2c; }
* { box-sizing: border-box; }
body { margin: 0; background: #eef2f1; color: var(--ink); font: 17px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 920px; margin: 48px auto; padding: 42px 48px; background: var(--paper); box-shadow: 0 18px 50px rgba(31, 45, 48, .12); }
h1 { margin-top: 0; border-bottom: 3px solid var(--accent); padding-bottom: .35em; }
h2 { margin-top: 2em; color: var(--accent); }
h3 { margin-top: 1.5em; }
.intro { color: var(--muted); max-width: 760px; }
.links { display: grid; gap: 16px; margin-top: 32px; }
a.card { display: block; padding: 20px 22px; border: 1px solid var(--line); border-radius: 8px; color: inherit; text-decoration: none; background: var(--soft); }
a.card:hover { border-color: var(--accent); background: #f3f8f7; }
.title { font-weight: 700; font-size: 1.12rem; color: var(--accent); }
.description { margin-top: 5px; color: #5b696d; font-size: .95rem; }
.back { display: inline-block; margin-bottom: 24px; color: var(--accent); font-weight: 650; text-decoration: none; }
.back:hover { text-decoration: underline; }
.summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 24px 0; }
.summary .item { padding: 16px; border: 1px solid var(--line); border-radius: 8px; background: var(--soft); }
.summary strong { display: block; color: var(--accent); font-size: 1.55rem; line-height: 1.15; }
.summary span { display: block; margin-top: 4px; color: var(--muted); font-size: .9rem; }
table { width: 100%; margin: 18px 0 26px; border-collapse: collapse; font-size: .91rem; }
th, td { padding: 9px 10px; border: 1px solid var(--line); text-align: left; vertical-align: top; }
th { background: #e7efed; }
tr:nth-child(even) td { background: var(--soft); }
figure { margin: 24px 0 32px; }
figure img { display: block; width: 100%; border: 1px solid var(--line); border-radius: 6px; background: white; }
figcaption { margin-top: 8px; color: var(--muted); font-size: .9rem; }
main > img { display: block; width: 100%; max-width: 100%; margin: 24px 0 8px; border: 1px solid var(--line); border-radius: 6px; background: white; }
.distribution-gallery { position: relative; margin: 24px 0 32px; }
.distribution-gallery figure { margin: 0; }
.distribution-arrow { position: absolute; z-index: 2; top: 50%; transform: translateY(-70%); width: 46px; height: 46px; border: 1px solid rgba(47, 111, 115, .45); border-radius: 50%; background: rgba(255, 255, 255, .92); color: var(--accent); font-size: 1.65rem; line-height: 1; cursor: pointer; box-shadow: 0 2px 10px rgba(31, 45, 48, .18); }
.distribution-arrow:hover, .distribution-arrow:focus-visible { background: white; border-color: var(--accent); outline: 3px solid rgba(47, 111, 115, .18); }
.distribution-arrow.previous { left: 12px; }
.distribution-arrow.next { right: 12px; }
.distribution-position { font-weight: 700; color: var(--accent); }
.note { margin: 22px 0; padding: 14px 18px; border-left: 4px solid var(--warm); background: #fff8f2; color: var(--muted); }
.age-bins { display: flex; flex-wrap: wrap; gap: 8px; padding: 0; list-style: none; }
.age-bins li { padding: 5px 9px; border: 1px solid var(--line); border-radius: 5px; background: var(--soft); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: .86rem; }
code { padding: .08em .3em; border: 1px solid var(--line); border-radius: 4px; background: var(--soft); }
@media screen and (max-width: 700px) {
  main { margin: 0; padding: 28px 22px 42px; box-shadow: none; }
  .summary { grid-template-columns: 1fr; }
  .table-wrap { max-width: 100%; overflow-x: auto; }
  table { min-width: 700px; font-size: .84rem; }
  .distribution-arrow { width: 40px; height: 40px; }
}
"""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(value, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.stem}.tmp-{os.getpid()}{path.suffix}")
    try:
        fig.savefig(temporary, dpi=170, bbox_inches="tight", facecolor="white")
        os.replace(temporary, path)
    finally:
        plt.close(fig)
        temporary.unlink(missing_ok=True)


def document(*, title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def _html_href(markdown_href: str) -> str:
    """Point local Markdown page links at their generated HTML counterpart."""

    if markdown_href.lower().endswith(".md"):
        return markdown_href[:-3] + ".html"
    return markdown_href


def _markdown_links_to_html(markdown_text: str) -> str:
    return re.sub(
        r"\]\(([^)]+)\)",
        lambda match: f"]({_html_href(match.group(1))})",
        markdown_text,
    )


def render_index(markdown_text: str) -> str:
    """Render the July-style homepage entirely from its editable Markdown."""

    title_match = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
    if not title_match:
        raise ValueError("homepage Markdown needs one level-one heading")
    title = title_match.group(1).strip()
    card_matches = list(
        re.finditer(
            r"^##\s+\[([^]]+)\]\(([^)]+)\)\s*$\n+(.*?)(?=\n##\s+\[|\Z)",
            markdown_text,
            flags=re.MULTILINE | re.DOTALL,
        )
    )
    if not card_matches:
        raise ValueError("homepage Markdown needs at least one linked level-two heading")
    intro_source = markdown_text[title_match.end() : card_matches[0].start()].strip()
    intro_html = markdown_to_html(intro_source)
    cards = []
    for match in card_matches:
        label, href, description = match.groups()
        description_html = markdown_to_html(description.strip())
        if description_html.startswith("<p>") and description_html.endswith("</p>"):
            description_html = description_html[3:-4]
        cards.append(
            f'<a class="card" href="{html.escape(_html_href(href), quote=True)}">'
            f'<div class="title">{html.escape(label)}</div>'
            f'<div class="description">{description_html}</div></a>'
        )
    body = "\n".join(
        [
            f"<h1>{html.escape(title)}</h1>",
            f'<div class="intro">{intro_html}</div>',
            '<div class="links">',
            *cards,
            "</div>",
        ]
    )
    return document(title=title, body=body)


def build_sample_summary(sample_flow: pd.DataFrame) -> pd.DataFrame:
    """Return one non-overlapping role-labelled row per longitudinal scope."""

    required = {"role", "scope", "step", "rows", "children", "corpora", "sessions"}
    missing = required - set(sample_flow.columns)
    if missing:
        raise ValueError(f"sample-flow columns missing: {sorted(missing)}")
    source = sample_flow[sample_flow["step"].eq("source_rows")].copy()
    rows = []
    for scope in SCOPE_ORDER:
        child = source[(source["scope"].eq(scope)) & source["role"].eq("child")]
        caregiver = source[(source["scope"].eq(scope)) & source["role"].eq("caretaker")]
        if len(child) != 1 or len(caregiver) != 1:
            raise ValueError(f"expected one child and caretaker source row for {scope}")
        child_row = child.iloc[0]
        caregiver_row = caregiver.iloc[0]
        rows.append(
            {
                "sample": SCOPE_LABELS[scope],
                "scope": scope,
                "children": int(child_row["children"]),
                "corpora": int(child_row["corpora"]),
                "child_utterances": int(child_row["rows"]),
                "caregiver_utterances": int(caregiver_row["rows"]),
                "child_sessions": int(child_row["sessions"]),
            }
        )
    return pd.DataFrame(rows)


def build_corpus_summary(coverage: pd.DataFrame) -> pd.DataFrame:
    """Summarize the 79-child corpus contributions from frozen coverage."""

    required = {
        "role",
        "scope",
        "dataset",
        "child_key",
        "rows",
        "sessions",
        "age_min",
        "age_max",
    }
    missing = required - set(coverage.columns)
    if missing:
        raise ValueError(f"coverage columns missing: {sorted(missing)}")
    child = coverage[
        coverage["role"].eq("child") & coverage["scope"].eq("all79_descriptive")
    ].copy()
    if child.empty:
        raise ValueError("all-79 child coverage is empty")
    summary = (
        child.groupby("dataset", sort=True)
        .agg(
            children=("child_key", "nunique"),
            child_utterances=("rows", "sum"),
            child_sessions=("sessions", "sum"),
            age_min=("age_min", "min"),
            age_max=("age_max", "max"),
        )
        .reset_index()
        .rename(columns={"dataset": "corpus"})
    )
    summary["sample_role"] = np.where(
        summary["corpus"].isin(PBM_CORPORA),
        "Brown, Manchester, and Providence",
        "Other 10 corpora",
    )
    summary["age_range_months"] = summary.apply(
        lambda row: f"{float(row['age_min']):.1f}–{float(row['age_max']):.1f}", axis=1
    )
    summary["role_order"] = summary["sample_role"].map(
        {"Brown, Manchester, and Providence": 0, "Other 10 corpora": 1}
    )
    summary = summary.sort_values(["role_order", "corpus"]).drop(columns="role_order")
    for column in ["children", "child_utterances", "child_sessions"]:
        summary[column] = summary[column].astype(int)
    return summary.reset_index(drop=True)


def _view_slug(corpus: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", corpus.lower()).strip("_")


def distribution_view_specs(corpora: Sequence[str]) -> list[dict[str, object]]:
    """Return the ordered all/group/corpus views shown in the gallery."""

    corpus_names = list(corpora)
    if len(corpus_names) != len(set(corpus_names)):
        raise ValueError("distribution corpus names must be unique")
    views: list[dict[str, object]] = [
        {
            "id": "all_children",
            "label": "All 79 children",
            "title": "Longitudinal utterance coverage by developmental age",
            "corpus": None,
        },
        {
            "id": "three_corpora",
            "label": "Brown, Manchester, and Providence (21 children)",
            "title": "Longitudinal utterance coverage by age — Brown + Manchester + Providence",
            "corpus": None,
        },
        {
            "id": "other_corpora",
            "label": "Other 10 corpora (58 children)",
            "title": "Longitudinal utterance coverage by age — Other 10 corpora",
            "corpus": None,
        },
    ]
    views.extend(
        {
            "id": f"corpus_{_view_slug(corpus)}",
            "label": f"{corpus} corpus",
            "title": f"Longitudinal utterance coverage by developmental age — {corpus}",
            "corpus": corpus,
        }
        for corpus in corpus_names
    )
    return views


def build_age_distribution_summary(
    child_rows: pd.DataFrame,
    caregiver_rows: pd.DataFrame,
    *,
    corpora: Sequence[str],
) -> pd.DataFrame:
    """Count scored utterances by age for all, grouped, and corpus views."""

    corpus_names = list(corpora)
    allowed = set(corpus_names)
    frames = []
    for role, source in [("child", child_rows), ("caretaker", caregiver_rows)]:
        missing = {"dataset", "age_bin"} - set(source.columns)
        if missing:
            raise ValueError(f"{role} distribution columns missing: {sorted(missing)}")
        frame = source[["dataset", "age_bin"]].copy()
        frame["role"] = role
        frames.append(frame)
    rows = pd.concat(frames, ignore_index=True)
    unexpected_corpora = sorted(set(rows["dataset"].dropna()) - allowed)
    unexpected_ages = sorted(set(rows["age_bin"].dropna()) - set(AGE_ORDER))
    if unexpected_corpora:
        raise ValueError(f"unexpected corpora in distribution rows: {unexpected_corpora}")
    if unexpected_ages:
        raise ValueError(f"unexpected age bins in distribution rows: {unexpected_ages}")

    output = []
    for view in distribution_view_specs(corpus_names):
        view_id = str(view["id"])
        if view_id == "all_children":
            selected = rows
        elif view_id == "three_corpora":
            selected = rows[rows["dataset"].isin(PBM_CORPORA)]
        elif view_id == "other_corpora":
            selected = rows[~rows["dataset"].isin(PBM_CORPORA)]
        else:
            selected = rows[rows["dataset"].eq(view["corpus"])]
        counts = selected.groupby(["role", "age_bin"]).size()
        for role in ["child", "caretaker"]:
            for age_bin in AGE_ORDER:
                output.append(
                    {
                        "view_id": view_id,
                        "role": role,
                        "age_bin": age_bin,
                        "rows": int(counts.get((role, age_bin), 0)),
                    }
                )
    return pd.DataFrame(output)


def _table_html(frame: pd.DataFrame, columns: Sequence[tuple[str, str]]) -> str:
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body_rows = []
    integer_columns = {
        "children",
        "corpora",
        "child_utterances",
        "caregiver_utterances",
        "child_sessions",
    }
    for row in frame.itertuples(index=False):
        values = row._asdict()
        cells = []
        for column, _ in columns:
            value = values[column]
            if column in integer_columns:
                rendered = f"{int(value):,}"
            else:
                rendered = str(value)
            cells.append(f"<td>{html.escape(rendered)}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></div>"
    )


def render_distribution_gallery(views: Sequence[Mapping[str, object]]) -> str:
    """Render an overlay-arrow gallery without changing the displayed plot box."""

    serialized = [
        {
            "id": str(view["id"]),
            "label": str(view["label"]),
            "title": str(view["title"]),
            "src": str(view["src"]),
        }
        for view in views
    ]
    if not serialized:
        raise ValueError("the distribution gallery needs at least one view")
    first = serialized[0]
    payload = json.dumps(serialized, ensure_ascii=False, separators=(",", ":"))
    return "\n".join(
        [
            f'<div class="distribution-gallery" data-distribution-count="{len(serialized)}">',
            '<button class="distribution-arrow previous" type="button" aria-label="Previous distribution">&#8592;</button>',
            "<figure>",
            f'<img class="distribution-image" src="{html.escape(first["src"], quote=True)}" alt="{html.escape(first["label"], quote=True)}">',
            f'<figcaption><span class="distribution-position">1 of {len(serialized)}</span> · <span class="distribution-label">{html.escape(first["label"])}</span></figcaption>',
            "</figure>",
            '<button class="distribution-arrow next" type="button" aria-label="Next distribution">&#8594;</button>',
            "</div>",
            "<script>",
            "(() => {",
            f"const views={payload};",
            'const gallery=document.querySelector(".distribution-gallery");',
            "if(!gallery){return;}",
            'const image=gallery.querySelector(".distribution-image");',
            'const position=gallery.querySelector(".distribution-position");',
            'const label=gallery.querySelector(".distribution-label");',
            "let current=0;",
            "const show=(index)=>{current=(index+views.length)%views.length;const view=views[current];image.src=view.src;image.alt=view.label;position.textContent=`${current+1} of ${views.length}`;label.textContent=view.label;};",
            'gallery.querySelector(".previous").addEventListener("click",()=>show(current-1));',
            'gallery.querySelector(".next").addEventListener("click",()=>show(current+1));',
            'gallery.addEventListener("keydown",(event)=>{if(event.key==="ArrowLeft"){show(current-1);}if(event.key==="ArrowRight"){show(current+1);}});',
            "})();",
            "</script>",
        ]
    )


def render_data_description(
    markdown_text: str,
    *,
    distribution_views: Sequence[Mapping[str, object]],
) -> str:
    """Render the data page from Markdown and inject its interactive gallery."""

    if markdown_text.count(GALLERY_START) != 1 or markdown_text.count(GALLERY_END) != 1:
        raise ValueError("data-description Markdown needs exactly one distribution gallery region")
    gallery_region = re.compile(
        re.escape(GALLERY_START) + r".*?" + re.escape(GALLERY_END),
        flags=re.DOTALL,
    )
    working = gallery_region.sub("{{AGE_DISTRIBUTION_GALLERY}}", markdown_text)
    body = markdown_to_html(_markdown_links_to_html(working))
    placeholder = "<p>{{AGE_DISTRIBUTION_GALLERY}}</p>"
    if placeholder not in body:
        raise RuntimeError("distribution gallery placeholder did not render as expected")
    body = body.replace(placeholder, render_distribution_gallery(distribution_views))
    return document(title="Data description — Supervisor Report", body=body)


def plot_age_coverage(descriptive: pd.DataFrame, path: Path) -> None:
    data = descriptive[
        descriptive["scope"].eq("all79_descriptive")
        & descriptive["outcome"].eq("lexical_words")
        & descriptive["role"].isin(["child", "caretaker"])
    ].copy()
    if data.empty:
        raise ValueError("all-79 lexical-word coverage is missing")
    x = np.arange(len(AGE_ORDER))
    width = 0.38
    colors = {"child": "#2f6f73", "caretaker": "#c76f2c"}
    labels = {"child": "Child utterances", "caretaker": "Caregiver utterances"}
    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    for index, role in enumerate(["child", "caretaker"]):
        subset = data[data["role"].eq(role)].set_index("age_bin").reindex(AGE_ORDER)
        values = pd.to_numeric(subset["rows"], errors="coerce").fillna(0).to_numpy(float)
        ax.bar(x + (index - 0.5) * width, values, width, color=colors[role], label=labels[role])
    ax.set_xticks(x, AGE_ORDER, rotation=35, ha="right")
    ax.set_ylabel("scored utterances")
    ax.set_xlabel("child age bin (months)")
    ax.set_title("Longitudinal utterance coverage by developmental age")
    ax.grid(axis="y", color="#d9e0df", linewidth=0.8)
    ax.legend(frameon=False)
    fig.tight_layout()
    atomic_figure(fig, path)


def plot_age_coverage_counts(data: pd.DataFrame, path: Path, *, title: str) -> None:
    """Draw another distribution with the exact dimensions/style of the total."""

    required = {"role", "age_bin", "rows"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"age-distribution columns missing: {sorted(missing)}")
    x = np.arange(len(AGE_ORDER))
    width = 0.38
    colors = {"child": "#2f6f73", "caretaker": "#c76f2c"}
    labels = {"child": "Child utterances", "caretaker": "Caregiver utterances"}
    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    for index, role in enumerate(["child", "caretaker"]):
        subset = data[data["role"].eq(role)].set_index("age_bin").reindex(AGE_ORDER)
        values = pd.to_numeric(subset["rows"], errors="coerce").fillna(0).to_numpy(float)
        ax.bar(x + (index - 0.5) * width, values, width, color=colors[role], label=labels[role])
    ax.set_xticks(x, AGE_ORDER, rotation=35, ha="right")
    ax.set_ylabel("scored utterances")
    ax.set_xlabel("child age bin (months)")
    ax.set_title(title)
    ax.grid(axis="y", color="#d9e0df", linewidth=0.8)
    ax.legend(frameon=False)
    fig.tight_layout()
    atomic_figure(fig, path)


def plot_child_coverage(coverage: pd.DataFrame, path: Path) -> None:
    data = coverage[
        coverage["role"].eq("child") & coverage["scope"].eq("all79_descriptive")
    ].copy()
    if data["child_key"].nunique() != 79:
        raise ValueError("expected exactly 79 children for the longitudinal coverage plot")
    data["sample_role"] = np.where(
        data["dataset"].isin(PBM_CORPORA), "PBM discovery", "Non-PBM confirmation"
    )
    data["role_order"] = data["sample_role"].map(
        {"PBM discovery": 0, "Non-PBM confirmation": 1}
    )
    data = data.sort_values(["role_order", "dataset", "age_min", "child_id"]).reset_index(drop=True)
    colors = {"PBM discovery": "#2f6f73", "Non-PBM confirmation": "#c76f2c"}
    y = np.arange(len(data))
    fig, ax = plt.subplots(figsize=(11.5, 17.5))
    for index, row in data.iterrows():
        color = colors[row["sample_role"]]
        ax.hlines(index, float(row["age_min"]), float(row["age_max"]), color=color, linewidth=2.4)
        ax.scatter([float(row["age_min"]), float(row["age_max"])], [index, index], color=color, s=11)
    ax.set_yticks(y, [f"{row.dataset} / {row.child_id}" for row in data.itertuples()])
    ax.set_xlim(6, 66)
    ax.set_xlabel("child age (months)")
    ax.set_title("Observed longitudinal age span for every child")
    ax.grid(axis="x", color="#d9e0df", linewidth=0.8)
    ax.invert_yaxis()
    ax.tick_params(axis="y", labelsize=7.5)
    ax.legend(
        handles=[
            Line2D([0], [0], color=colors[label], lw=3, label=label)
            for label in ["PBM discovery", "Non-PBM confirmation"]
        ],
        frameon=False,
        loc="lower right",
    )
    fig.tight_layout()
    atomic_figure(fig, path)


def _validate_inputs(root: Path, paths: Mapping[str, Path]) -> None:
    for label, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(f"required {label} input is missing: {path}")
    dataset_manifest = json.loads(paths["dataset_manifest"].read_text(encoding="utf-8"))
    if dataset_manifest.get("status") != "COMPLETE":
        raise RuntimeError("full-79 dataset manifest is not COMPLETE")
    completion = json.loads(paths["completion_marker"].read_text(encoding="utf-8"))
    if completion.get("audit", {}).get("verdict") != "AUDIT_PASS":
        raise RuntimeError("August evidence package is not AUDIT_PASS")


def build(
    *,
    root: Path,
    index_md: Path,
    index_html: Path,
    data_md: Path,
    data_html: Path,
    output_dir: Path,
) -> dict[str, object]:
    root = root.resolve()
    index_md = (root / index_md).resolve() if not index_md.is_absolute() else index_md.resolve()
    index_html = (root / index_html).resolve() if not index_html.is_absolute() else index_html.resolve()
    data_md = (root / data_md).resolve() if not data_md.is_absolute() else data_md.resolve()
    data_html = (root / data_html).resolve() if not data_html.is_absolute() else data_html.resolve()
    output_dir = (root / output_dir).resolve() if not output_dir.is_absolute() else output_dir.resolve()
    paths = {
        "index_markdown": index_md,
        "data_markdown": data_md,
        "coverage": root / "results/direct_surprisal_replication/mistral_full79/modular/prepared/child_coverage.csv",
        "sample_flow": root / "results/direct_surprisal_replication/mistral_full79/modular/prepared/sample_flow.csv",
        "descriptive": root / "results/direct_surprisal_replication/mistral_full79/modular/prepared/descriptive_age_bin_summary.csv",
        "dataset_manifest": root / "results/direct_surprisal_replication/mistral_full79/modular/prepared/dataset_manifest.json",
        "child_wide": root / "results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz",
        "caregiver_wide": root / "results/direct_surprisal_replication/mistral_full79/caretaker_direct_surprisal_wide.csv.gz",
        "completion_marker": root / "results/august_supervisor_report/AUGUST_REPORT_COMPLETE_AND_AUDITED",
    }
    _validate_inputs(root, paths)

    protected = {str(root / path): sha256_file(root / path) for path in PROTECTED_PATHS}
    coverage = pd.read_csv(paths["coverage"])
    sample_flow = pd.read_csv(paths["sample_flow"])
    descriptive = pd.read_csv(paths["descriptive"])
    sample_summary = build_sample_summary(sample_flow)
    corpus_summary = build_corpus_summary(coverage)
    if int(sample_summary.iloc[-1]["children"]) != 79 or len(corpus_summary) != 13:
        raise RuntimeError("current longitudinal coverage is not 79 children across 13 corpora")
    corpora = sorted(corpus_summary["corpus"].tolist())

    child_distribution_rows = pd.read_csv(
        paths["child_wide"], usecols=["dataset", "age_bin"]
    )
    caregiver_distribution_rows = pd.read_csv(
        paths["caregiver_wide"], usecols=["dataset", "age_bin"]
    )
    distribution_summary = build_age_distribution_summary(
        child_distribution_rows,
        caregiver_distribution_rows,
        corpora=corpora,
    )
    expected = (
        descriptive[
            descriptive["scope"].eq("all79_descriptive")
            & descriptive["outcome"].eq("lexical_words")
        ][["role", "age_bin", "rows"]]
        .sort_values(["role", "age_bin"])
        .reset_index(drop=True)
    )
    observed = (
        distribution_summary[distribution_summary["view_id"].eq("all_children")][
            ["role", "age_bin", "rows"]
        ]
        .sort_values(["role", "age_bin"])
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(observed, expected, check_dtype=False)

    output_dir.mkdir(parents=True, exist_ok=True)
    age_plot = output_dir / "utterance_coverage_by_age.png"
    child_plot = output_dir / "child_longitudinal_coverage.png"
    sample_csv = output_dir / "analysis_sample_summary.csv"
    corpus_csv = output_dir / "corpus_summary.csv"
    distribution_csv = output_dir / "age_distribution_summary.csv"
    previous_age_plot_hash = sha256_file(age_plot) if age_plot.exists() else None
    plot_age_coverage(descriptive, age_plot)
    if previous_age_plot_hash is not None and sha256_file(age_plot) != previous_age_plot_hash:
        raise RuntimeError("the existing all-79 distribution plot changed")
    plot_child_coverage(coverage, child_plot)
    sample_summary.to_csv(sample_csv, index=False)
    corpus_summary.to_csv(corpus_csv, index=False)
    distribution_summary.to_csv(distribution_csv, index=False)

    plot_paths: list[Path] = [age_plot]
    public_views = []
    for view in distribution_view_specs(corpora):
        view_id = str(view["id"])
        if view_id == "all_children":
            plot_path = age_plot
        else:
            plot_path = output_dir / f"utterance_coverage_by_age__{view_id}.png"
            plot_age_coverage_counts(
                distribution_summary[distribution_summary["view_id"].eq(view_id)],
                plot_path,
                title=str(view["title"]),
            )
            plot_paths.append(plot_path)
        public_view = dict(view)
        public_view["src"] = os.path.relpath(plot_path, data_html.parent)
        public_views.append(public_view)

    image_shapes = {
        tuple(plt.imread(path).shape[:2])
        for path in plot_paths
    }
    if len(image_shapes) != 1:
        raise RuntimeError(f"distribution plot dimensions differ: {sorted(image_shapes)}")

    index_page = render_index(index_md.read_text(encoding="utf-8"))
    data_page = render_data_description(
        data_md.read_text(encoding="utf-8"),
        distribution_views=public_views,
    )
    atomic_text(index_html, index_page)
    atomic_text(data_html, data_page)

    after = {path: sha256_file(Path(path)) for path in protected}
    if protected != after:
        raise RuntimeError("an existing audited August artifact changed")

    outputs = [
        index_html,
        data_html,
        child_plot,
        sample_csv,
        corpus_csv,
        distribution_csv,
        *plot_paths,
    ]
    manifest = {
        "status": "PASS",
        "purpose": "restart supervisor report: July-style homepage plus Data description only",
        "pages": {
            "index_markdown": str(index_md.relative_to(root)),
            "index_html": str(index_html.relative_to(root)),
            "data_description_markdown": str(data_md.relative_to(root)),
            "data_description_html": str(data_html.relative_to(root)),
        },
        "counts": {
            "children": 79,
            "corpora": 13,
            "three_corpora_children": 21,
            "other_corpora_children": 58,
            "distribution_views": len(public_views),
        },
        "distribution_plot_pixels": list(next(iter(image_shapes))),
        "input_hashes": {
            str(path.relative_to(root)): sha256_file(path) for path in paths.values()
        },
        "protected_hashes": protected,
        "output_hashes": {
            str(path.relative_to(root)): sha256_file(path) for path in outputs
        },
    }
    manifest_path = output_dir / "manifest.json"
    atomic_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--index-md", type=Path, default=DEFAULT_INDEX_MD)
    parser.add_argument("--index-html", type=Path, default=DEFAULT_INDEX_HTML)
    parser.add_argument("--data-md", type=Path, default=DEFAULT_DATA_MD)
    parser.add_argument("--data-html", type=Path, default=DEFAULT_DATA_HTML)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = build(
        root=args.root,
        index_md=args.index_md,
        index_html=args.index_html,
        data_md=args.data_md,
        data_html=args.data_html,
        output_dir=args.output_dir,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
