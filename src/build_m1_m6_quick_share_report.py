#!/usr/bin/env python3
"""Render the compact M1-M6 dual-effort quick-share report.

This report stage does not fit models. It reads the artifacts produced by
``fit_m1_m6_dual_effort_quick_models.py`` and writes Markdown/HTML.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Sequence

import pandas as pd

try:
    from fit_m1_m6_dual_effort_quick_models import DEFAULT_FIG_DIR, DEFAULT_OUTPUT_DIR, DUAL_MODEL_SPECS
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.fit_m1_m6_dual_effort_quick_models import DEFAULT_FIG_DIR, DEFAULT_OUTPUT_DIR, DUAL_MODEL_SPECS
    from src.render_markdown_report import render_markdown_file


DEFAULT_DOC_MD = Path("docs/utterance_information_m1_m6_quick_share.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_m1_m6_quick_share.html")


def read_csv_required(path: Path) -> pd.DataFrame:
    """Read a required CSV with a clear error."""

    if not path.exists():
        raise FileNotFoundError(f"Missing required quick-share analysis output: {path}")
    return pd.read_csv(path)


def format_p(value: object) -> str:
    """Format p-values compactly."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(parsed):
        return ""
    if parsed < 0.001:
        return "<.001"
    return f"{parsed:.3f}"


def write_markdown_table(frame: pd.DataFrame, *, max_rows: int = 12, digits: int = 4) -> str:
    """Render a small dataframe as a Markdown table."""

    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    rendered = shown.astype(object).copy()
    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]):
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else f"{value:.{digits}g}")
        else:
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else str(value))
    header = "| " + " | ".join(str(col) for col in rendered.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(rendered.columns)) + " |"
    body = [
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *body])


def make_image(fig_dir: Path, filename: str, alt: str) -> str:
    """Return Markdown image syntax, with an inline warning if missing."""

    path = fig_dir / filename
    if not path.exists():
        return f"_Missing plot: `{path}`_"
    return f"![{alt}](../{path.as_posix()})"


def compact_model_table(summary: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return a compact table for one model."""

    cols = [
        "effort_strategy",
        "effort_label",
        "r2_observed_fitted",
        "age_coef",
        "age_p",
        "effort_coef",
        "effort_p",
        "entropy_coef",
        "entropy_p",
        "age_effort_coef",
        "age_effort_p",
        "age_entropy_coef",
        "age_entropy_p",
        "status",
    ]
    out = summary[summary["model_id"].eq(model_id)][[col for col in cols if col in summary.columns]].copy()
    strategy_order = {"continuous": 0, "effort_level": 1}
    out["_strategy_order"] = out["effort_strategy"].map(strategy_order).fillna(9)
    out = out.sort_values(["_strategy_order", "effort_label"]).drop(columns=["_strategy_order"])
    for col in [column for column in out.columns if column.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out


def formula_table(summary: pd.DataFrame, model_id: str) -> pd.DataFrame:
    """Return one formula row per effort strategy."""

    cols = ["effort_strategy", "readable_formula", "formula"]
    out = summary[summary["model_id"].eq(model_id)][cols].drop_duplicates().copy()
    strategy_order = {"continuous": 0, "effort_level": 1}
    out["_strategy_order"] = out["effort_strategy"].map(strategy_order).fillna(9)
    return out.sort_values("_strategy_order").drop(columns="_strategy_order")


def sign_takeaway(summary: pd.DataFrame, model_id: str) -> str:
    """Return a short sign summary for age effects by effort strategy."""

    pieces: list[str] = []
    for strategy in ["continuous", "effort_level"]:
        sub = summary[summary["model_id"].eq(model_id) & summary["effort_strategy"].eq(strategy)].copy()
        values = pd.to_numeric(sub["age_coef"], errors="coerce").dropna()
        if values.empty:
            pieces.append(f"{strategy}: age unavailable")
        else:
            pieces.append(f"{strategy}: {(values < 0).sum()} negative, {(values > 0).sum()} positive age coefficients")
    return "; ".join(pieces) + "."


def model_reading_note(model_id: str) -> str:
    """Return a compact model-specific reading note."""

    if model_id in {"M1", "M2", "M4", "M5"}:
        return (
            "The top row uses the exact effort count as a numeric control. "
            "The bottom row uses the same effort unit to make low/mid/high effort groups. "
            "If both rows tell the same age story, the result is less dependent on the effort encoding."
        )
    if model_id == "M3":
        return (
            "For M3, the bottom row is especially important: non-parallel low/mid/high lines mean the age trend differs by effort level. "
            "The continuous row asks the same interaction question with the raw effort count."
        )
    return (
        "For M6, the two rows are two ways of asking the interaction-rich question. "
        "Use it as an exploratory stress test, not as the cleanest primary model."
    )


def build_m1_m6_quick_share_markdown(output_dir: Path, fig_dir: Path) -> str:
    """Return the compact M1-M6 Markdown report."""

    summary = read_csv_required(output_dir / "dual_model_summary.csv")
    audit_path = output_dir / "dual_model_audit.csv"
    audit = pd.read_csv(audit_path) if audit_path.exists() else pd.DataFrame()
    overview_rows = [
        {
            "model": spec.model_id,
            "question": spec.question,
            "continuous effort formula": summary[
                summary["model_id"].eq(spec.model_id) & summary["effort_strategy"].eq("continuous")
            ]["readable_formula"].drop_duplicates().iloc[0],
            "effort-level formula": summary[
                summary["model_id"].eq(spec.model_id) & summary["effort_strategy"].eq("effort_level")
            ]["readable_formula"].drop_duplicates().iloc[0],
        }
        for spec in DUAL_MODEL_SPECS
    ]
    model_map = pd.DataFrame(overview_rows)
    sections: list[str] = []
    for spec in DUAL_MODEL_SPECS:
        table = compact_model_table(summary, spec.model_id)
        sections.append(
            f"""## {spec.model_id}: {spec.model_title}

**Question.** {spec.question}

**Formulas.**

{write_markdown_table(formula_table(summary, spec.model_id), max_rows=2)}

**Quick takeaway.** {sign_takeaway(summary, spec.model_id)}

**How to read the plot.** {model_reading_note(spec.model_id)} Shaded ribbons are model-based 95% confidence intervals when available.

{make_image(fig_dir, f"{spec.model_id.lower()}_dual_effort_predictions.png", f"{spec.model_id} dual effort predictions")}

**Compact results.**

{write_markdown_table(table, max_rows=10)}
"""
        )

    audit_text = write_markdown_table(audit, max_rows=2) if not audit.empty else "_No audit table found._"
    md = f"""# Quick Share: M1-M6 Utterance Information Models

This is the minimal shareable version. The fitting stage has already been run;
this file only renders saved model tables and plots.

Outcome:

```text
sum_bits
```

## What Changed In This Version

Every M1-M6 model is shown with **two effort strategies**:

- `continuous`: all utterance lengths stay in one numeric scale, and the model controls their differences directly.
- `effort_level`: utterances are grouped into low/mid/high effort within one effort unit, and those groups enter the model as categorical predictors.

The two strategies are fit separately. They are not the same model and they
should be compared as a robustness check.

## Model Map

{write_markdown_table(model_map, max_rows=6)}

## Shared Reading Rules

- Downward age lines mean lower predicted total bits as children get older, after the controls in that model.
- The top row of each plot is the continuous effort-control version.
- The bottom row of each plot is the low/mid/high effort-group version.
- Each column is a different effort unit: words, morphemes, two syllable strategies, or phonemes.
- When a top-row panel says `median = X`, that is only the value used to draw
  the prediction line. The model was still fit on all utterances with their
  actual observed effort values.
- `C(child_id)` means child fixed intercepts: each child gets their own baseline.
- Context entropy is Mistral next-token entropy in bits, not sampled full-response entropy.

{''.join(sections)}

## Analysis Audit

{audit_text}

## Files

- Analysis tables: `{output_dir / "dual_model_summary.csv"}`
- Prediction rows: `{output_dir / "dual_model_predictions.csv"}`
- Figures: `{fig_dir}`
- This report: `docs/utterance_information_m1_m6_quick_share.html`
"""
    return md


def build_quick_share_report(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
    md_path: Path = DEFAULT_DOC_MD,
    html_path: Path = DEFAULT_DOC_HTML,
) -> dict[str, Path]:
    """Write the compact M1-M6 Markdown and HTML report."""

    md = build_m1_m6_quick_share_markdown(output_dir, fig_dir)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)
    return {"md": md_path, "html": html_path}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    args = parser.parse_args(argv)
    outputs = build_quick_share_report(
        output_dir=args.output_dir,
        fig_dir=args.fig_dir,
        md_path=args.md,
        html_path=args.html,
    )
    print(f"[OK] wrote quick M1-M6 Markdown: {outputs['md']}")
    print(f"[OK] wrote quick M1-M6 HTML: {outputs['html']}")


if __name__ == "__main__":
    main()
