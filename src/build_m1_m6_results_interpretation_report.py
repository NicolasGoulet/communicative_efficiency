#!/usr/bin/env python3
"""Render interpretation notes for the compact M1-M6 results.

This is a report-only stage. It reads the saved dual-effort M1-M6 summary and
writes a narrative document about what the fitted patterns mean for the
communicative-efficiency questions.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

try:
    from fit_m1_m6_dual_effort_quick_models import DEFAULT_OUTPUT_DIR
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.fit_m1_m6_dual_effort_quick_models import DEFAULT_OUTPUT_DIR
    from src.render_markdown_report import render_markdown_file


DEFAULT_DOC_MD = Path("docs/utterance_information_m1_m6_results_interpretation.md")
DEFAULT_DOC_HTML = Path("docs/utterance_information_m1_m6_results_interpretation.html")


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


def write_markdown_table(frame: pd.DataFrame, *, max_rows: int = 20, digits: int = 4) -> str:
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


def coefficient_direction_summary(
    summary: pd.DataFrame,
    *,
    coefficient: str,
    p_col: str,
    model_ids: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Summarize sign and p<.05 counts by model and effort strategy."""

    frame = summary.copy()
    if model_ids is not None:
        frame = frame[frame["model_id"].isin(list(model_ids))].copy()
    rows: list[dict[str, object]] = []
    for (model_id, effort_strategy), group in frame.groupby(["model_id", "effort_strategy"], sort=True):
        values = pd.to_numeric(group[coefficient], errors="coerce")
        p_values = pd.to_numeric(group[p_col], errors="coerce") if p_col in group.columns else pd.Series(index=group.index, dtype=float)
        valid = values.dropna()
        valid_p = p_values.loc[valid.index]
        rows.append(
            {
                "model": model_id,
                "effort_strategy": effort_strategy,
                "coefficient": coefficient,
                "negative": int((valid < 0).sum()),
                "positive": int((valid > 0).sum()),
                "p<.05": int((valid_p < 0.05).sum()),
                "tested_effort_versions": int(valid.shape[0]),
                "coef_min": float(valid.min()) if not valid.empty else math.nan,
                "coef_max": float(valid.max()) if not valid.empty else math.nan,
            }
        )
    return pd.DataFrame(rows)


def compact_rows(summary: pd.DataFrame, *, model_id: str, strategy: str) -> pd.DataFrame:
    """Return compact coefficient rows for one model/strategy."""

    cols = [
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
    ]
    out = summary[summary["model_id"].eq(model_id) & summary["effort_strategy"].eq(strategy)][cols].copy()
    for col in [column for column in out.columns if column.endswith("_p")]:
        out[col] = out[col].map(format_p)
    return out


def list_significant_efforts(summary: pd.DataFrame, *, model_id: str, strategy: str, coef: str, p_col: str) -> str:
    """Return a readable list of significant effort labels for a coefficient."""

    sub = summary[summary["model_id"].eq(model_id) & summary["effort_strategy"].eq(strategy)].copy()
    sub[coef] = pd.to_numeric(sub[coef], errors="coerce")
    sub[p_col] = pd.to_numeric(sub[p_col], errors="coerce")
    sig = sub[sub[p_col] < 0.05].copy()
    if sig.empty:
        return "none"
    return ", ".join(f"{row.effort_label} ({row[coef]:.3g})" for _, row in sig.iterrows())


def build_results_interpretation_markdown(output_dir: Path) -> str:
    """Build the interpretation Markdown from saved M1-M6 results."""

    summary_path = output_dir / "dual_model_summary.csv"
    audit_path = output_dir / "dual_model_audit.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing required M1-M6 summary: {summary_path}")
    summary = pd.read_csv(summary_path)
    audit = pd.read_csv(audit_path) if audit_path.exists() else pd.DataFrame()

    age_summary = coefficient_direction_summary(summary, coefficient="age_coef", p_col="age_p")
    entropy_summary = coefficient_direction_summary(
        summary,
        coefficient="entropy_coef",
        p_col="entropy_p",
        model_ids=["M4", "M5", "M6"],
    )
    age_effort_summary = coefficient_direction_summary(
        summary,
        coefficient="age_effort_coef",
        p_col="age_effort_p",
        model_ids=["M3", "M6"],
    )
    age_entropy_summary = coefficient_direction_summary(
        summary,
        coefficient="age_entropy_coef",
        p_col="age_entropy_p",
        model_ids=["M5", "M6"],
    )

    audit_sentence = ""
    if not audit.empty:
        row = audit.iloc[0]
        context_k = row.get("context_k", "unknown")
        audit_sentence = (
            f"The current run used {int(row['rows']):,} real child utterance rows, "
            f"{int(row['children'])} children, context window `{context_k}`, "
            f"and produced {int(row['fitted_model_rows'])} fitted model rows."
        )

    m2_continuous = compact_rows(summary, model_id="M2", strategy="continuous")
    m4_continuous = compact_rows(summary, model_id="M4", strategy="continuous")
    m5_continuous = compact_rows(summary, model_id="M5", strategy="continuous")
    m6_continuous = compact_rows(summary, model_id="M6", strategy="continuous")

    md = f"""# Interpretation Notes: M1-M6 Utterance Information Results

This document interprets the compact M1-M6 results in
`docs/utterance_information_m1_m6_quick_share.html`. It is separate from the
supervisor-facing report and is meant as a thinking document: what the current
models suggest, what they do not yet establish, and how they connect to the
communicative-efficiency questions motivating the project.

{audit_sentence}

## Scientific Question

The project is about communicative efficiency in child language: how children
package information while managing the amount of linguistic material they
produce. The current M1-M6 analyses focus on the **informativeness side** of
that question:

```text
Given a child utterance and its preceding caretaker context, does total
utterance surprisal change with age after controlling production effort?
```

Here, total information is `sum_bits`; effort is operationalized separately as
words, surface morphemes, two syllable estimates, and phonemes.

This is close to the first question Professor Xu articulated: whether children
optimize informativeness in their speech when utterance length or effort is
constrained. It is **not yet** the full second question: whether context
predictability causes children to shorten or lengthen their utterances. That
second question needs models where effort itself is the outcome, preferably
using response-level context entropy sampled from possible model responses.

## Main Takeaways

1. **Child identity is essential.** M1 pools children and gives weak or positive
   age patterns. M2 adds child identity and the continuous-effort versions show
   negative age effects across all five effort controls.

2. **The safest current result is the continuous-effort child-adjusted pattern.**
   In M2, M4, M5, and M6, the continuous-effort versions generally show that
   older children have lower predicted total bits for utterances with the same
   modeled effort.

3. **Low/mid/high effort groups are useful diagnostics, but not a replacement
   for exact effort control.** The effort-level models often reverse the M2-M5
   age direction. This likely happens because a low/mid/high group is coarse:
   utterances inside the same category can still differ substantially in exact
   words, morphemes, syllables, or phonemes.

4. **Current next-token context entropy behaves unexpectedly.** In M4-M6, the
   context-entropy coefficient is negative across all effort versions. This
   means that higher next-token entropy is associated with lower total child
   utterance bits after controls. This should not be overinterpreted as the
   final contextual-information result because this feature only measures
   uncertainty about the next token, not uncertainty over complete possible
   responses.

5. **The age-by-context interaction is weak in the continuous models.** M5 and
   M6 do not show a stable continuous-effort age-by-context-entropy interaction.
   This suggests that the current next-token entropy feature is not yet giving
   the developmental interaction that the larger efficiency hypothesis needs.

6. **M6 supports the broad robustness of the downward child-adjusted
   continuous-effort trend.** Even after adding multiple interactions, the
   continuous M6 age coefficients remain negative across all effort units,
   though not every one is significant.

## Results At A Glance

Age-effect signs by model and effort strategy:

{write_markdown_table(age_summary)}

Context-entropy signs in the context models:

{write_markdown_table(entropy_summary)}

Interaction summaries:

{write_markdown_table(age_effort_summary)}

{write_markdown_table(age_entropy_summary)}

## Model-by-Model Interpretation

### M1: pooled age plus effort

M1 asks the simplest question: if all child utterances are pooled together, does
age predict total bits after effort is controlled? The answer is not the one we
should treat as developmental evidence. The pooled continuous models are weak
or positive, and the effort-level versions are positive. This is exactly why M1
is useful: it shows the danger of ignoring which children contribute data at
which ages.

Interpretation: M1 is a baseline sanity check, not the primary model.

### M2: age plus effort plus child identity

M2 is the first serious developmental model in this set. It asks whether age
predicts total bits after controlling effort and giving each child their own
baseline.

The continuous-effort M2 versions are the clearest result: age coefficients are
negative for words, morphemes, both syllable estimates, and phonemes. This means
that, for the same modeled amount of linguistic material, older children
produce utterances that Mistral finds more predictable in context.

Compact M2 continuous-effort results:

{write_markdown_table(m2_continuous)}

Interpretation: this is consistent with a developmental shift toward more
contextually predictable, conventional, or efficiently recoverable utterances.
It should not be phrased as "children communicate less information" without the
effort and context caveats.

### M3: age by effort

M3 asks whether the relation between effort and total bits changes with age.
The continuous interaction term is not robust across effort units. The only
continuous age-by-effort interaction below p<.05 is:

```text
{list_significant_efforts(summary, model_id="M3", strategy="continuous", coef="age_effort_coef", p_col="age_effort_p")}
```

Interpretation: there is not strong evidence yet that the information gained
per additional unit of effort changes systematically with age. The larger
developmental effect seems to be the age effect after effort control, not a
stable age-by-effort interaction.

### M4: adding context entropy

M4 adds current context entropy to the M2 structure. The intended question is
whether context predictability helps explain total utterance information after
age, effort, and child identity are controlled.

The continuous M4 models keep the M2 age pattern: age remains negative across
all effort units. Context entropy is also negative across all effort units.

Compact M4 continuous-effort results:

{write_markdown_table(m4_continuous)}

Interpretation: the downward child-adjusted age pattern is not explained away
by the current next-token entropy feature. However, the entropy coefficient
itself is not straightforward. If this were a perfect measure of response-level
context uncertainty, one might expect higher entropy to predict higher
utterance information or more effort. Instead, the negative coefficient tells
us that this next-token entropy feature is probably capturing something more
local and should be treated as provisional.

### M5: age by context entropy

M5 tests whether the context-entropy association changes over development. In
the continuous-effort versions, the age-by-context interaction is not
significant for any effort unit:

```text
{list_significant_efforts(summary, model_id="M5", strategy="continuous", coef="age_entropy_coef", p_col="age_entropy_p")}
```

Compact M5 continuous-effort results:

{write_markdown_table(m5_continuous)}

Interpretation: with the current next-token entropy feature, we do not yet have
strong evidence that the context-information relation changes with age. This is
a key reason to build the response-level entropy feature discussed after the
meeting.

### M6: interaction-rich stress test

M6 asks whether the main conclusions survive a more flexible model with
age-by-effort, age-by-context, and effort-by-context interactions. This is not
the cleanest primary model, but it is useful as a stress test.

Compact M6 continuous-effort results:

{write_markdown_table(m6_continuous)}

Interpretation: the continuous-effort M6 models still show negative age
coefficients across all five effort measures. This supports the robustness of
the child-adjusted continuous-effort result. At the same time, the interaction
terms are not stable enough to carry the central scientific claim.

## How This Relates To Communicative Efficiency

The current results speak to one side of communicative efficiency: the
information associated with the produced utterance once production effort is
controlled. The strongest current pattern is:

```text
older age + same modeled effort + same child baseline
    -> lower predicted total surprisal
```

Scientifically, this can be interpreted in several compatible ways:

- older children may produce utterances that are more conventional or expected
  in local conversational context;
- older children may rely more on context, producing utterances that carry less
  model-surprisal per controlled unit of surface material;
- the Mistral scorer may find older children's forms easier to predict because
  they are more adult-like or less noisy;
- the result is not, by itself, proof that children are "more efficient,"
  because efficiency depends on both information and effort in relation to
  communicative need.

The experimental work on communicative efficiency in children motivates asking
whether children become more adult-like in adapting message length to the
communicative situation. The learner-directed speech literature also reminds us
that more redundancy can be efficient when the listener or context requires it.
Therefore, lower or higher surprisal is not automatically good or bad; it has
to be interpreted relative to effort, context, and communicative recoverability.

The current M1-M6 results should therefore be framed as:

```text
evidence for developmental change in utterance-level information after effort
control, with child identity controlled
```

not yet as:

```text
complete evidence that children optimize production effort based on contextual
predictability
```

## What This Suggests For The Next Analyses

1. Keep the continuous-effort child-adjusted models as the primary
   utterance-information evidence.

2. Treat low/mid/high effort-group models as robustness checks and visual
   diagnostics, not as the main effort control.

3. Use the next-token context entropy results only provisionally. They are
   useful because they show that adding a context-predictability feature does
   not remove the age effect, but they are not the final answer to the
   contextual-efficiency question.

4. Build response-level context entropy from sampled possible responses. This
   better matches the supervisor discussion: given a caretaker context, how
   many plausible complete responses does the model see?

5. Add models where effort is the outcome:

```text
effort ~ age + response_entropy + context_length + question_type + child identity
```

This directly tests the production-effort prediction: children should produce
longer or more effortful utterances when the context leaves more uncertainty
about the appropriate response.

6. Compare children against baselines and caretakers after effort control. The
   current M1-M6 report is about real child utterances only; the broader
   efficiency interpretation needs child-vs-baseline and child-vs-caretaker
   comparisons.

## Literature Anchors

- Tal, Smith, Arnon, and Culbertson (2023) motivate the developmental question:
  communicative-efficiency behavior is present in young children and becomes
  more adult-like with age.
- Tal, Grossman, Rohde, and Arnon (2023) motivate the effort/redundancy side:
  speakers can efficiently produce more linguistic material when listeners are
  learners or comprehension difficulty is higher.
- Wang, Yu, and Shao (2026) motivate interaction-style models: efficient form
  choice can be shaped jointly by multiple surprisal sources, so context,
  effort, and age interactions are theoretically meaningful.
- The current response-level entropy note in this repo formalizes the next
  project step: sample possible full responses from a model and estimate the
  entropy of the response distribution.

## References

- Tal, S., Smith, K., Arnon, I., & Culbertson, J. (2023). Communicative
  efficiency is present in young children and becomes more adult-like with age.
  Proceedings of the Annual Meeting of the Cognitive Science Society, 45.
  https://escholarship.org/uc/item/7mm0z6fk
- Tal, S., Grossman, E., Rohde, H., & Arnon, I. (2023). Speakers use more
  redundant references with language learners: Evidence for
  communicatively-efficient referential choice. Journal of Memory and Language,
  128, 104378. https://doi.org/10.1016/j.jml.2022.104378
- Wang, G., Yu, M., & Shao, B. (2026). Efficient Communication in Word
  Formation: How Syntactic and Lexical Surprisal Jointly Shape English
  Conversion Over the Past Century. Cognitive Science.
  https://doi.org/10.1111/cogs.70202
"""
    return md


def build_results_interpretation_report(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    md_path: Path = DEFAULT_DOC_MD,
    html_path: Path = DEFAULT_DOC_HTML,
) -> dict[str, Path]:
    """Write Markdown and HTML interpretation notes."""

    md = build_results_interpretation_markdown(output_dir)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    render_markdown_file(md_path, html_path)
    return {"md": md_path, "html": html_path}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--html", type=Path, default=DEFAULT_DOC_HTML)
    args = parser.parse_args(argv)
    outputs = build_results_interpretation_report(
        output_dir=args.output_dir,
        md_path=args.md,
        html_path=args.html,
    )
    print(f"[OK] wrote M1-M6 interpretation Markdown: {outputs['md']}")
    print(f"[OK] wrote M1-M6 interpretation HTML: {outputs['html']}")


if __name__ == "__main__":
    main()
