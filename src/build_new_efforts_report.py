#!/usr/bin/env python3
"""Build a multi-page working report for the newest analysis efforts."""

from __future__ import annotations

import argparse
import html
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


DOC_DIR = Path("docs")
INDEX_HTML = DOC_DIR / "new_efforts_report_index.html"

ONSET_DIR = Path("results/developmental_onset_report")
BAYES_DIR = Path("results/bayes_information_report")
ONSET_FIG_DIR = Path("figs/developmental_onset_report")
BAYES_FIG_DIR = Path("figs/bayes_information_report")

SOURCE_LABELS = {
    "real": "Real child",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
}


@dataclass(frozen=True)
class ReportPage:
    title: str
    stem: str
    description: str

    @property
    def md_path(self) -> Path:
        return DOC_DIR / f"{self.stem}.md"

    @property
    def html_path(self) -> Path:
        return DOC_DIR / f"{self.stem}.html"


PAGES = [
    ReportPage(
        "Overview",
        "new_efforts_overview",
        "Navigation and the current scientific read across the new analyses.",
    ),
    ReportPage(
        "When CE Kicks In",
        "new_efforts_ce_kickoff",
        "Developmental onset, fixed-effort age-bin timing, and context-modulation timing.",
    ),
    ReportPage(
        "Bayes-Decomposed Surprisal",
        "new_efforts_bayes_surprisal",
        "The new p(u) plus p(c|u) information family and its relation to direct Mistral surprisal.",
    ),
    ReportPage(
        "Complexity Metrics",
        "new_efforts_complexity_metrics",
        "MLU-style, syllable/phoneme proxy, and lexical complexity predictors.",
    ),
    ReportPage(
        "Promotion Plan",
        "new_efforts_promotion_plan",
        "What should move into the supervisor-facing July pages, and what needs robustness first.",
    ),
]


INDEX_CSS = """
body { margin: 0; background: #eef2f1; color: #1e2528; font: 17px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
main { max-width: 980px; margin: 48px auto; padding: 42px 48px; background: white; box-shadow: 0 18px 50px rgba(31, 45, 48, .12); }
h1 { margin-top: 0; border-bottom: 3px solid #2f6f73; padding-bottom: .35em; }
.lede { color: #4f5b5f; max-width: 760px; }
.links { display: grid; gap: 16px; margin-top: 28px; }
a.card { display: block; padding: 18px 20px; border: 1px solid #d9e0df; border-radius: 8px; color: inherit; text-decoration: none; background: #fafbfb; }
a.card:hover { border-color: #2f6f73; background: #f3f8f7; }
.title { font-weight: 700; font-size: 1.12rem; color: #2f6f73; }
.desc { color: #5e686d; margin-top: .25rem; }
.note { margin-top: 28px; padding-top: 18px; border-top: 1px solid #d9e0df; color: #5e686d; font-size: .95rem; }
"""


def fmt(value: object, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "" if value is None else str(value)
    if not math.isfinite(number):
        return ""
    if abs(number) < 0.001 and number != 0:
        return f"{number:.2e}"
    return f"{number:.{digits}f}"


def md_table(frame: pd.DataFrame, *, digits: int = 3) -> str:
    if frame.empty:
        return "_No rows._"
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].map(lambda value: fmt(value, digits))
    out = out.fillna("").astype(str)
    lines = [
        "| " + " | ".join(out.columns) + " |",
        "| " + " | ".join(["---"] * len(out.columns)) + " |",
    ]
    for _, row in out.iterrows():
        lines.append("| " + " | ".join(row[col].replace("|", "\\|") for col in out.columns) + " |")
    return "\n".join(lines)


def rel(path: Path, md_path: Path) -> str:
    return os.path.relpath(path, start=md_path.parent).replace(os.sep, "/")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required report input: {path}")
    return pd.read_csv(path)


def pct_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in columns:
        out[col] = 100 * pd.to_numeric(out[col], errors="coerce")
    return out


def html_document(*, title: str, body: str) -> str:
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escaped_title}</title>
<style>{INDEX_CSS}</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def write_index() -> Path:
    cards = "\n".join(
        (
            f'<a class="card" href="{html.escape(page.html_path.relative_to(DOC_DIR).as_posix(), quote=True)}">'
            f'<div class="title">{html.escape(page.title)}</div>'
            f'<div class="desc">{html.escape(page.description)}</div>'
            "</a>"
        )
        for page in PAGES
    )
    body = "\n".join(
        [
            "<h1>New Efforts Working Report</h1>",
            '<p class="lede">A compact multi-page report for the new communicative-efficiency work: developmental onset, Bayes-decomposed information, and complexity predictors. This is a working layer, separate from the clean July supervisor pages.</p>',
            '<div class="links">',
            cards,
            "</div>",
            '<p class="note">Generated from audited local outputs under <code>results/developmental_onset_report/</code> and <code>results/bayes_information_report/</code>.</p>',
        ]
    )
    INDEX_HTML.write_text(html_document(title="New Efforts Working Report", body=body), encoding="utf-8")
    return INDEX_HTML


def write_page(page: ReportPage, markdown: str) -> Path:
    page.md_path.write_text(markdown, encoding="utf-8")
    render_markdown_file(page.md_path, page.html_path)
    return page.html_path


def overview_page(page: ReportPage) -> str:
    onset = read_csv(ONSET_DIR / "high_level_onset_summary.csv")
    paired = read_csv(BAYES_DIR / "paired_gap_summary.csv")
    complexity = read_csv(ONSET_DIR / "complexity_age_summary.csv")
    first_mlu = complexity.loc[complexity["age_bin"] == "024-029"].iloc[0]
    trigram = paired.loc[paired["source_model"] == "trigram"].iloc[0]

    nav = pd.DataFrame(
        {
            "page": [p.title for p in PAGES if p.title != page.title],
            "what_it_answers": [p.description for p in PAGES if p.title != page.title],
            "link": [f"[open]({p.html_path.relative_to(DOC_DIR).as_posix()})" for p in PAGES if p.title != page.title],
        }
    )
    headline = pd.DataFrame(
        [
            {
                "topic": "CE onset",
                "current_read": "Fixed-word-count decrease starts in 024-029; context entropy is visible in 006-023.",
            },
            {
                "topic": "Bayes surprisal",
                "current_read": f"Trigram baseline is {trigram['delta_bayes_bits_per_token_vs_real_mean']:.2f} Bayes bits/token and {trigram['delta_mistral_bits_per_token_vs_real_mean']:.2f} Mistral bits/token above real child utterances.",
            },
            {
                "topic": "Complexity metrics",
                "current_read": f"MLU rises by 024-029: mean words/utterance is {first_mlu['mean_words_per_utterance_mean']:.2f}, with CI [{first_mlu['mean_words_per_utterance_ci_low']:.2f}, {first_mlu['mean_words_per_utterance_ci_high']:.2f}].",
            },
        ]
    )
    return f"""# New Efforts Working Report

This report collects the newest work in one browsable place. It is separate from the formal July supervisor-facing pages, so we can inspect the evidence before deciding what to promote.

## Pages

{md_table(nav)}

## Current Read Across The New Work

{md_table(headline)}

## Highest-Level Onset Table

{md_table(onset, digits=3)}

## Existing Full Working Reports

- [Developmental onset working report](developmental_onset_working_report.html)
- [Bayes-decomposed informativeness working report](bayes_information_working_report.html)
"""


def ce_page(page: ReportPage) -> str:
    onset = read_csv(ONSET_DIR / "high_level_onset_summary.csv")
    age_effects = read_csv(ONSET_DIR / "utterance_level_exact_word_age_effects.csv")
    changepoints = read_csv(ONSET_DIR / "changepoint_model_summary.csv")
    paired_onsets = read_csv(ONSET_DIR / "paired_gap_onset_summary.csv")
    context_onsets = read_csv(ONSET_DIR / "context_modulation_onset_summary.csv")

    best_break = changepoints.sort_values("delta_aic_vs_best").head(1)
    return f"""# When CE Kicks In

This page answers the supervisor question about timing: not just whether there is a downward trend, but **when the signal becomes detectable**.

## Key Read

- The fixed-word-count age-bin decrease is detectable by `024-029`.
- Context entropy modulation is detectable already in `006-023`.
- Parent-context-word modulation becomes detectable in `024-029`.
- Same-context real-vs-baseline advantages are already positive in `006-023`.

## Onset Summary

{md_table(onset, digits=3)}

![Onset signal map]({rel(ONSET_FIG_DIR / "onset_signal_map.png", page.md_path)})

## Fixed-Effort Age-Bin Model

{md_table(age_effects[["age_bin", "estimate_vs_006_023", "ci_low", "ci_high", "p_value"]], digits=4)}

![Controlled real child age effects]({rel(ONSET_FIG_DIR / "controlled_real_child_age_effects.png", page.md_path)})

## Change-Point Scan

{md_table(best_break[["breakpoint_month", "delta_aic_vs_best", "r2", "age_slope", "post_break_slope_change", "post_break_p"]], digits=4)}

![Piecewise change-point scan]({rel(ONSET_FIG_DIR / "piecewise_changepoint_scan.png", page.md_path)})

## Paired Baseline Onset

{md_table(paired_onsets, digits=3)}

![Paired real advantage onset]({rel(ONSET_FIG_DIR / "paired_real_advantage_onset.png", page.md_path)})

## Context Modulation

{md_table(context_onsets, digits=3)}

![Context modulation onset]({rel(ONSET_FIG_DIR / "context_modulation_onset.png", page.md_path)})
"""


def bayes_page(page: ReportPage) -> str:
    source = read_csv(BAYES_DIR / "source_summary.csv")
    paired = read_csv(BAYES_DIR / "paired_gap_summary.csv")
    corr = read_csv(BAYES_DIR / "bayes_mistral_correlations.csv")
    percentile = read_csv(BAYES_DIR / "real_candidate_percentile_summary.csv")
    model_summary = read_csv(BAYES_DIR / "model_summary.csv")

    source["source"] = source["source_model"].map(SOURCE_LABELS).fillna(source["source_model"])
    source_show = source[
        [
            "source",
            "n",
            "bayes_bits_per_token_mean",
            "bayes_prior_bits_per_token_mean",
            "bayes_context_bits_mean",
            "mistral_bits_per_token_mean",
        ]
    ]
    paired["source"] = paired["source_model"].map(SOURCE_LABELS).fillna(paired["source_model"])
    paired_show = paired[
        [
            "source",
            "n",
            "delta_bayes_bits_per_token_vs_real_mean",
            "delta_mistral_bits_per_token_vs_real_mean",
            "delta_words_vs_real_mean",
        ]
    ]
    pct = pct_frame(
        percentile,
        ["real_bayes_worse_fraction_mean", "real_mistral_worse_fraction_mean"],
    )
    pct = pct.rename(
        columns={
            "real_bayes_worse_fraction_mean": "real_bayes_advantage_pct",
            "real_mistral_worse_fraction_mean": "real_mistral_advantage_pct",
        }
    )
    return f"""# Bayes-Decomposed Surprisal

The Bayes-style score uses the working decomposition:

```text
bits(u, c) = -log2 p(u) - log2 p(c | u)
```

The normalizer `p(c)` is not estimated yet, so this is an **unnormalized decomposition score**. It is most defensible right now for same-context candidate comparisons.

## Source-Level Patterns

{md_table(source_show, digits=3)}

![Bayes bits per token by age and source]({rel(BAYES_FIG_DIR / "bayes_bits_per_token_by_age_source.png", page.md_path)})

![Direct Mistral bits per token by age and source]({rel(BAYES_FIG_DIR / "mistral_bits_per_token_by_age_source.png", page.md_path)})

![Bayes components by age and source]({rel(BAYES_FIG_DIR / "bayes_component_bits_by_age_source.png", page.md_path)})

## Paired Real-Versus-Baseline Checks

Positive gaps mean the generated baseline is higher-bit than the real child utterance in the same context.

{md_table(paired_show, digits=3)}

![Paired Bayes gaps]({rel(BAYES_FIG_DIR / "paired_bayes_gap_by_age.png", page.md_path)})

![Paired Mistral gaps]({rel(BAYES_FIG_DIR / "paired_mistral_gap_by_age.png", page.md_path)})

## Real Child Advantage Percentiles

{md_table(pct[["age_bin", "n", "real_bayes_advantage_pct", "real_mistral_advantage_pct"]], digits=2)}

![Real child advantage percentiles]({rel(BAYES_FIG_DIR / "real_advantage_percentiles_by_age.png", page.md_path)})

## Relationship To Direct Mistral

{md_table(corr, digits=3)}

![Bayes versus direct Mistral]({rel(BAYES_FIG_DIR / "bayes_vs_mistral_scatter.png", page.md_path)})

## First Model Checks

{md_table(model_summary, digits=3)}
"""


def complexity_page(page: ReportPage) -> str:
    complexity = read_csv(ONSET_DIR / "complexity_age_summary.csv")
    effects = read_csv(ONSET_DIR / "complexity_adjusted_age_effects.csv")
    source = read_csv(BAYES_DIR / "source_summary.csv")
    source["source"] = source["source_model"].map(SOURCE_LABELS).fillna(source["source_model"])
    source_show = source[
        [
            "source",
            "orthographic_word_count_mean",
            "estimated_syllable_count_mean",
            "mistral_bits_per_token_mean",
            "bayes_bits_per_token_mean",
        ]
    ]
    complexity_show = complexity[
        [
            "age_bin",
            "n_cells",
            "mean_words_per_utterance_mean",
            "mean_words_per_utterance_ci_low",
            "mean_words_per_utterance_ci_high",
            "mean_syllables_per_utterance_mean",
            "age_bin_vocab_size_mean",
            "age_bin_ttr_mean",
        ]
    ]
    effect_show = effects[
        effects["outcome"].isin(["mean_words_per_utterance", "mean_syllables_per_utterance", "age_bin_vocab_size"])
    ][["outcome", "age_bin", "estimate_vs_006_023", "ci_low", "ci_high", "p_value"]]
    return f"""# Complexity Metrics

The new complexity layer gives us more than raw word count. It adds MLU-style predictors, syllable and phoneme proxies, and lexical trajectory summaries that can be used as controls or developmental descriptors.

## What These Metrics Are For

- Use MLU and syllable/phoneme proxies to check whether information effects are just production-complexity effects.
- Use vocabulary and TTR measures to approximate lexical complexity over time.
- Keep these separate from the information measure itself: complexity is a predictor/control, not the same object as surprisal.

## Real Child Complexity By Age Bin

{md_table(complexity_show, digits=3)}

![Complexity timing checks]({rel(ONSET_FIG_DIR / "complexity_timing_checks.png", page.md_path)})

## Adjusted Complexity Effects

{md_table(effect_show, digits=4)}

## Complexity In The Candidate Cloud

{md_table(source_show, digits=3)}

![Real child lexical complexity trajectories]({rel(BAYES_FIG_DIR / "real_child_complexity_trajectories.png", page.md_path)})
"""


def promotion_page(page: ReportPage) -> str:
    rows = pd.DataFrame(
        [
            {
                "candidate": "CE onset map",
                "promote_now": "Yes",
                "why": "Directly answers when the signal appears.",
                "caveat": "Add child bootstrap before treating it as final.",
            },
            {
                "candidate": "Fixed-word-count age-bin model",
                "promote_now": "Yes",
                "why": "Matches the earlier Route 1 downward-trend model family.",
                "caveat": "State that the child-age aggregate sensitivity changes the weighting.",
            },
            {
                "candidate": "Paired real-vs-trigram gap",
                "promote_now": "Yes",
                "why": "Same context and same generated-baseline family; easy to explain.",
                "caveat": "Use as comparison evidence, not as a full causal claim.",
            },
            {
                "candidate": "Bayes decomposition",
                "promote_now": "Maybe",
                "why": "Scientifically useful alternative to direct Mistral surprisal.",
                "caveat": "Label as unnormalized until p(c) is estimated or explicitly conditioned away.",
            },
            {
                "candidate": "Complexity metrics",
                "promote_now": "Yes",
                "why": "They answer the supervisor concern that we returned to the initial project formulation.",
                "caveat": "Use as controls/descriptors, not as replacement CE outcomes.",
            },
        ]
    )
    next_steps = pd.DataFrame(
        [
            {
                "step": "Bootstrap onset table by child",
                "reason": "Protects against pseudo-replication and reviewer criticism.",
            },
            {
                "step": "Repeat onset with morpheme, syllable, and phoneme controls",
                "reason": "Checks whether timing survives alternative effort definitions.",
            },
            {
                "step": "Move one curated onset figure into the July developmental page",
                "reason": "Keeps the supervisor-facing report readable.",
            },
            {
                "step": "Keep Bayes as a working/additional analysis until wording is locked",
                "reason": "The decomposition is useful, but still needs careful normalizer language.",
            },
        ]
    )
    return f"""# Promotion Plan

This page is the decision layer: what should move into the clean July supervisor-facing pages, and what should stay as working evidence for now.

## What To Promote

{md_table(rows)}

## Immediate Next Steps

{md_table(next_steps)}

## Suggested Supervisor-Facing Structure

1. Put the onset map and fixed-word-count age-bin model in `Developmental Trajectory of Communicative Efficiency`.
2. Put the Bayes decomposition as a short "alternative information formulation" subsection in `Predicting Utterance Informativeness`.
3. Put MLU, syllable/phoneme proxies, vocabulary size, and TTR in `Predicting Utterance Production Effort`.
4. Keep implementation details, repo paths, and Mila logistics out of the supervisor-facing pages.
"""


def build_all() -> list[Path]:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    builders = {
        "new_efforts_overview": overview_page,
        "new_efforts_ce_kickoff": ce_page,
        "new_efforts_bayes_surprisal": bayes_page,
        "new_efforts_complexity_metrics": complexity_page,
        "new_efforts_promotion_plan": promotion_page,
    }
    outputs = [write_index()]
    for page in PAGES:
        outputs.append(write_page(page, builders[page.stem](page)))
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> None:
    parse_args()
    for path in build_all():
        print(f"[OK] {path}")


if __name__ == "__main__":
    main()
