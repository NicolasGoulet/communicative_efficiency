#!/usr/bin/env python3
"""Build and audit a response-space entropy pilot grid.

This is the publication-facing pilot framework for sampled full-response
entropy. It does not call a language model. It prepares a stratified context
manifest from the split scored-result tree, writes a deduplicated generation
manifest for ``sample_context_responses.py``, and audits sampled responses after
generation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from build_m1_m2_utterance_information_deep_dive import AGE_BIN_ORDER
    from build_response_entropy_manifest import context_id, normalize_context
    from build_route1_analysis_dataset import DEFAULT_MAIN_SCORED_ROOT, context_text_for_row, iter_scored_files
    from build_route1_report_assets import age_to_route1_bin, resolve_age_months
    from render_markdown_report import render_markdown_file
    from summarize_response_entropy_samples import (
        canonical_response,
        empirical_entropy_bits,
        miller_madow_entropy_bits,
        response_effort_counts,
    )
except ModuleNotFoundError:  # pragma: no cover - used when imported as src.*
    from src.build_m1_m2_utterance_information_deep_dive import AGE_BIN_ORDER
    from src.build_response_entropy_manifest import context_id, normalize_context
    from src.build_route1_analysis_dataset import DEFAULT_MAIN_SCORED_ROOT, context_text_for_row, iter_scored_files
    from src.build_route1_report_assets import age_to_route1_bin, resolve_age_months
    from src.render_markdown_report import render_markdown_file
    from src.summarize_response_entropy_samples import (
        canonical_response,
        empirical_entropy_bits,
        miller_madow_entropy_bits,
        response_effort_counts,
    )


DEFAULT_OUTPUT_DIR = Path("results/response_entropy_pilot_grid")
DEFAULT_FIG_DIR = Path("figs/response_entropy_pilot_grid")
DEFAULT_DESIGN_MD = Path("docs/response_entropy_pilot_grid_design.md")
DEFAULT_DESIGN_HTML = Path("docs/response_entropy_pilot_grid_design.html")
DEFAULT_DIAGNOSTIC_MD = Path("docs/response_entropy_pilot_grid_diagnostics.md")
DEFAULT_DIAGNOSTIC_HTML = Path("docs/response_entropy_pilot_grid_diagnostics.html")
DEFAULT_CONTEXT_KS = ("k1", "k2", "k3")
DEFAULT_TEMPERATURES = (0.3, 0.5, 0.7, 1.0, 1.3, 1.6)
DEFAULT_MODEL = "mistralai/Mistral-7B-v0.3"
DEFAULT_PROMPT_TEMPLATE = "Caregiver: {context}\nChild:"
DEFAULT_SEED = 20260615

SCORED_TREE_USECOLS = [
    "dataset",
    "child_id",
    "session_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "context_k1",
    "context_k2",
    "context_k3",
    "context_col_used",
    "chi_utterance_clean",
]


def split_csv(value: str | Sequence[str]) -> list[str]:
    """Parse comma-separated command-line values."""

    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part).strip() for part in value if str(part).strip()]


def parse_float_csv(value: str | Sequence[float]) -> list[float]:
    """Parse comma-separated float command-line values."""

    if isinstance(value, str):
        return [float(part.strip()) for part in value.split(",") if part.strip()]
    return [float(part) for part in value]


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 80, digits: int = 4) -> str:
    """Render a compact Markdown table."""

    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    rendered = shown.astype(object).copy()
    for col in shown.columns:
        if pd.api.types.is_float_dtype(shown[col]) or pd.api.types.is_integer_dtype(shown[col]):
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else f"{float(value):.{digits}g}")
        else:
            rendered[col] = shown[col].map(lambda value: "" if pd.isna(value) else str(value))
    header = "| " + " | ".join(str(col) for col in rendered.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(rendered.columns)) + " |"
    rows = [
        "| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |"
        for row in rendered.itertuples(index=False, name=None)
    ]
    return "\n".join([header, sep, *rows])


def read_csv_header(path: Path) -> list[str]:
    """Read just the CSV header."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            return []


@dataclass
class ContextStratumStats:
    """Accumulated support for one context text within age-bin/context-k stratum."""

    context_id: str
    context_text: str
    context_k: str
    age_bin: str
    context_word_count: int
    n_target_rows: int = 0
    datasets: set[str] = field(default_factory=set)
    child_ids: set[str] = field(default_factory=set)
    session_ids: set[str] = field(default_factory=set)
    age_months_min: float | None = None
    age_months_max: float | None = None
    example_target_utterance_clean: str = ""
    example_file: str = ""
    example_line_no: str = ""

    def update(self, row: Mapping[str, object]) -> None:
        """Add one target row using this context."""

        self.n_target_rows += 1
        self.datasets.add(str(row.get("dataset", "")))
        self.child_ids.add(str(row.get("child_id", "")))
        self.session_ids.add(str(row.get("session_id", "")))
        age = pd.to_numeric(row.get("age_months", math.nan), errors="coerce")
        if pd.notna(age):
            value = float(age)
            self.age_months_min = value if self.age_months_min is None else min(self.age_months_min, value)
            self.age_months_max = value if self.age_months_max is None else max(self.age_months_max, value)
        if not self.example_target_utterance_clean:
            self.example_target_utterance_clean = str(row.get("chi_utterance_clean", ""))
            self.example_file = str(row.get("file", ""))
            self.example_line_no = str(row.get("line_no", ""))

    def as_dict(self) -> dict[str, object]:
        """Return a CSV row."""

        return {
            "context_stratum_id": f"{self.age_bin}::{self.context_k}::{self.context_id}",
            "context_id": self.context_id,
            "context_text": self.context_text,
            "context_word_count": self.context_word_count,
            "context_k": self.context_k,
            "age_bin": self.age_bin,
            "n_target_rows": self.n_target_rows,
            "datasets": ";".join(sorted(x for x in self.datasets if x)),
            "child_ids": ";".join(sorted(x for x in self.child_ids if x)),
            "child_count": len([x for x in self.child_ids if x]),
            "session_count": len([x for x in self.session_ids if x]),
            "age_months_min": self.age_months_min,
            "age_months_max": self.age_months_max,
            "example_target_utterance_clean": self.example_target_utterance_clean,
            "example_file": self.example_file,
            "example_line_no": self.example_line_no,
        }


def iter_real_child_context_chunks(
    *,
    scored_root: Path,
    score_source: str,
    context_ks: Sequence[str],
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Read split scored files and return context rows plus file audits."""

    wanted_ks = set(context_ks)
    parts: list[pd.DataFrame] = []
    audits: list[dict[str, object]] = []
    for spec in iter_scored_files(scored_root, score_source):
        if spec.role != "child" or spec.target_variant != "real" or spec.context_k not in wanted_ks:
            continue
        header = read_csv_header(spec.path)
        usecols = [col for col in SCORED_TREE_USECOLS if col in set(header)]
        df = pd.read_csv(spec.path, usecols=usecols, dtype=str, keep_default_na=False, low_memory=False)
        audit = {
            "scored_file": str(spec.path),
            "context_k": spec.context_k,
            "dataset": spec.dataset_dir,
            "child": spec.child_dir,
            "rows_read": int(len(df)),
        }
        for col in ["dataset", "child_id", "session_id", "age_months", "file", "line_no", "chi_utterance_clean"]:
            if col not in df.columns:
                df[col] = ""
        df["dataset"] = df["dataset"].replace("", spec.dataset_dir)
        df["child_id"] = df["child_id"].replace("", spec.child_dir)
        df["context_k"] = spec.context_k
        df["context_text"] = [
            context_text_for_row(row, spec)[0]
            for row in df.to_dict("records")
        ]
        df["context_text"] = df["context_text"].map(normalize_context)
        df["age_months"] = [
            resolve_age_months(row.get("age_months", ""), row.get("file", ""))[0]
            for row in df.to_dict("records")
        ]
        df["age_months"] = pd.to_numeric(df["age_months"], errors="coerce")
        df["age_bin"] = df["age_months"].map(age_to_route1_bin)
        parts.append(df)
        audit["rows_with_nonempty_context"] = int(df["context_text"].astype(str).str.len().gt(0).sum())
        audit["rows_with_age_bin"] = int(df["age_bin"].notna().sum())
        audits.append(audit)
    if not parts:
        return pd.DataFrame(), audits
    return pd.concat(parts, ignore_index=True), audits


def build_eligible_context_strata(
    *,
    scored_root: Path,
    score_source: str,
    context_ks: Sequence[str],
    min_context_words: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build unique context rows within age-bin/context-k strata."""

    rows, file_audits = iter_real_child_context_chunks(
        scored_root=scored_root,
        score_source=score_source,
        context_ks=context_ks,
    )
    if rows.empty:
        return pd.DataFrame(), pd.DataFrame(file_audits)
    rows = rows[rows["context_text"].astype(str).str.len() > 0].copy()
    rows["context_word_count"] = rows["context_text"].map(lambda text: len(str(text).split()))
    rows = rows[(rows["context_word_count"] >= min_context_words) & rows["age_bin"].notna()].copy()
    stats: dict[tuple[str, str, str], ContextStratumStats] = {}
    for row in rows.to_dict("records"):
        text = str(row["context_text"])
        cid = context_id(text)
        key = (str(row["age_bin"]), str(row["context_k"]), cid)
        if key not in stats:
            stats[key] = ContextStratumStats(
                context_id=cid,
                context_text=text,
                context_k=str(row["context_k"]),
                age_bin=str(row["age_bin"]),
                context_word_count=int(row["context_word_count"]),
            )
        stats[key].update(row)
    eligible = pd.DataFrame([item.as_dict() for item in stats.values()])
    if not eligible.empty:
        eligible["age_bin"] = pd.Categorical(eligible["age_bin"], categories=AGE_BIN_ORDER, ordered=True)
        eligible = eligible.sort_values(["age_bin", "context_k", "context_id"]).reset_index(drop=True)
        eligible["age_bin"] = eligible["age_bin"].astype(str)
    return eligible, pd.DataFrame(file_audits)


def select_pilot_strata(
    eligible: pd.DataFrame,
    *,
    sample_per_age_bin_context_k: int,
    seed: int,
) -> pd.DataFrame:
    """Select a balanced pilot subset by age bin and context window."""

    if eligible.empty:
        return eligible.copy()
    rng = np.random.default_rng(seed)
    parts: list[pd.DataFrame] = []
    for (age_bin, context_k), group in eligible.groupby(["age_bin", "context_k"], sort=True, dropna=False):
        group = group.copy()
        group = group.sort_values(["child_count", "n_target_rows", "context_id"], ascending=[False, False, True])
        n = min(sample_per_age_bin_context_k, len(group))
        if len(group) > n:
            indices = np.sort(rng.choice(group.index.to_numpy(), size=n, replace=False))
            sampled = group.loc[indices].copy()
        else:
            sampled = group.copy()
        sampled["selection_age_bin"] = age_bin
        sampled["selection_context_k"] = context_k
        sampled["selection_seed"] = seed
        sampled["selection_rank_within_stratum"] = range(len(sampled))
        sampled["selection_n_requested"] = sample_per_age_bin_context_k
        sampled["selection_n_available"] = len(group)
        parts.append(sampled)
    return pd.concat(parts, ignore_index=True).sort_values(["selection_age_bin", "selection_context_k", "selection_rank_within_stratum"])


def build_generation_manifest(selected: pd.DataFrame, *, design: Mapping[str, object]) -> pd.DataFrame:
    """Deduplicate selected strata into one row per generated context text."""

    if selected.empty:
        return selected.copy()
    rows: list[dict[str, object]] = []
    for context_id_value, group in selected.groupby("context_id", sort=True):
        first = group.iloc[0]
        rows.append(
            {
                "context_id": context_id_value,
                "context_text": first["context_text"],
                "context_word_count": first["context_word_count"],
                "selected_stratum_count": int(len(group)),
                "selected_age_bins": ";".join(sorted(group["selection_age_bin"].astype(str).unique().tolist())),
                "selected_context_ks": ";".join(sorted(group["selection_context_k"].astype(str).unique().tolist())),
                "selected_context_stratum_ids": ";".join(group["context_stratum_id"].astype(str).tolist()),
                "n_target_rows_in_selected_strata": int(pd.to_numeric(group["n_target_rows"], errors="coerce").fillna(0).sum()),
                "child_count_in_selected_strata": int(len(set(";".join(group["child_ids"].astype(str)).split(";")) - {""})),
                "example_target_utterance_clean": first["example_target_utterance_clean"],
                "pilot_design_json": json.dumps(design, sort_keys=True),
            }
        )
    out = pd.DataFrame(rows).sort_values(["context_word_count", "context_id"]).reset_index(drop=True)
    out.insert(0, "manifest_row", range(len(out)))
    return out


def build_pilot_audit(
    eligible: pd.DataFrame,
    selected: pd.DataFrame,
    generation_manifest: pd.DataFrame,
    *,
    file_audit: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize eligible and selected contexts by stratum."""

    if eligible.empty:
        return pd.DataFrame()
    eligible_counts = (
        eligible.groupby(["age_bin", "context_k"], observed=True)
        .agg(
            eligible_context_strata=("context_stratum_id", "nunique"),
            eligible_unique_context_texts=("context_id", "nunique"),
            eligible_target_rows=("n_target_rows", "sum"),
            eligible_children=("child_ids", lambda values: len(set(";".join(values.astype(str)).split(";")) - {""})),
        )
        .reset_index()
    )
    selected_counts = (
        selected.groupby(["selection_age_bin", "selection_context_k"], observed=True)
        .agg(
            selected_context_strata=("context_stratum_id", "nunique"),
            selected_unique_context_texts=("context_id", "nunique"),
            selected_target_rows=("n_target_rows", "sum"),
        )
        .reset_index()
        .rename(columns={"selection_age_bin": "age_bin", "selection_context_k": "context_k"})
    )
    out = eligible_counts.merge(selected_counts, on=["age_bin", "context_k"], how="left")
    for col in ["selected_context_strata", "selected_unique_context_texts", "selected_target_rows"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    out["generation_manifest_contexts_total"] = int(len(generation_manifest))
    out["source_files_read_total"] = int(len(file_audit))
    out["source_rows_read_total"] = int(pd.to_numeric(file_audit.get("rows_read", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    return out


def command_block(
    *,
    generation_manifest: Path,
    sample_output: Path,
    model_name: str,
    temperatures: Sequence[float],
    samples_per_context: int,
    max_new_tokens: int,
    top_p: float,
    top_k: int,
    batch_contexts: int,
    batch_samples: int,
    dtype: str,
) -> str:
    """Return a copy-pasteable generation command."""

    temps = ",".join(str(t) for t in temperatures)
    return f"""env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \\
  src/sample_context_responses.py \\
  --manifest {generation_manifest} \\
  --output {sample_output} \\
  --model {model_name} \\
  --temperatures {temps} \\
  --samples-per-context {samples_per_context} \\
  --batch-contexts {batch_contexts} \\
  --batch-samples {batch_samples} \\
  --max-new-tokens {max_new_tokens} \\
  --top-p {top_p} \\
  --top-k {top_k} \\
  --dtype {dtype} \\
  --device auto"""


def build_design_markdown(
    *,
    output_dir: Path,
    design: Mapping[str, object],
    audit: pd.DataFrame,
    generation_manifest: pd.DataFrame,
    command: str,
) -> str:
    """Build the pilot design report."""

    compact_audit = audit[
        [
            "age_bin",
            "context_k",
            "eligible_context_strata",
            "selected_context_strata",
            "selected_unique_context_texts",
            "eligible_children",
            "selected_target_rows",
        ]
    ].copy()
    overview = pd.DataFrame(
        [
            {"field": key, "value": json.dumps(value) if isinstance(value, (list, dict)) else value}
            for key, value in design.items()
        ]
    )
    return f"""# Response-Space Entropy Pilot Grid Design

This document defines the pilot grid for sampling possible child responses from
base Mistral. It is a measurement-design artifact: the goal is to decide which
decoding settings produce stable and interpretable response-space entropy
before running the full production job.

## Design

{markdown_table(overview, max_rows=40)}

## Stratified Context Selection

The pilot uses observed caregiver contexts from real child-response rows. The
selection is balanced by:

```text
age_bin x context window
```

The generation manifest is deduplicated by normalized context text. This keeps
the scientific stratum audit while avoiding repeated generation for identical
prompts.

{markdown_table(compact_audit, max_rows=80)}

## Scale

```text
selected stratum rows: {len(pd.read_csv(output_dir / "pilot_selected_context_strata.csv")) if (output_dir / "pilot_selected_context_strata.csv").exists() else "not written"}
deduplicated generation contexts: {len(generation_manifest)}
temperatures: {len(design["temperatures"])}
samples per context per temperature: {design["samples_per_context"]}
planned generations: {len(generation_manifest) * len(design["temperatures"]) * int(design["samples_per_context"]):,}
```

## Generation Command

Run this on the GPU machine, not on the laptop:

```bash
{command}
```

## After Generation

After the sample CSV exists, run diagnostics:

```bash
env MPLCONFIGDIR=/tmp/matplotlib .venv/bin/python \\
  src/build_response_entropy_pilot_grid.py \\
  --stage diagnostics \\
  --samples {output_dir / "pilot_response_samples.csv.gz"} \\
  --output-dir {output_dir}
```

## Output Files

- Eligible context strata: `{output_dir / "pilot_eligible_context_strata.csv.gz"}`
- Selected context strata: `{output_dir / "pilot_selected_context_strata.csv"}`
- Deduplicated generation manifest: `{output_dir / "pilot_generation_manifest.csv"}`
- Pilot audit: `{output_dir / "pilot_manifest_audit.csv"}`
- Method spec: `{output_dir / "pilot_method_spec.json"}`
"""


def build_pilot_manifest(
    *,
    scored_root: Path,
    output_dir: Path,
    fig_dir: Path,
    design_md: Path,
    design_html: Path,
    score_source: str,
    context_ks: Sequence[str],
    sample_per_age_bin_context_k: int,
    min_context_words: int,
    temperatures: Sequence[float],
    samples_per_context: int,
    max_new_tokens: int,
    top_p: float,
    top_k: int,
    model_name: str,
    prompt_template: str,
    batch_contexts: int,
    batch_samples: int,
    dtype: str,
    seed: int,
) -> dict[str, Path]:
    """Write the complete pilot design and generation manifest."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    eligible, file_audit = build_eligible_context_strata(
        scored_root=scored_root,
        score_source=score_source,
        context_ks=context_ks,
        min_context_words=min_context_words,
    )
    selected = select_pilot_strata(
        eligible,
        sample_per_age_bin_context_k=sample_per_age_bin_context_k,
        seed=seed,
    )
    design = {
        "model": model_name,
        "prompt_template": prompt_template,
        "context_ks": list(context_ks),
        "sample_per_age_bin_context_k": sample_per_age_bin_context_k,
        "min_context_words": min_context_words,
        "temperatures": list(temperatures),
        "samples_per_context": samples_per_context,
        "max_new_tokens": max_new_tokens,
        "top_p": top_p,
        "top_k": top_k,
        "batch_contexts": batch_contexts,
        "batch_samples": batch_samples,
        "do_sample": True,
        "num_beams": 1,
        "repetition_penalty": 1.0,
        "no_repeat_ngram_size": 0,
        "seed": seed,
        "source": "split scored tree",
        "scored_root": str(scored_root),
    }
    generation_manifest = build_generation_manifest(selected, design=design)
    audit = build_pilot_audit(eligible, selected, generation_manifest, file_audit=file_audit)
    paths = {
        "eligible": output_dir / "pilot_eligible_context_strata.csv.gz",
        "selected": output_dir / "pilot_selected_context_strata.csv",
        "generation_manifest": output_dir / "pilot_generation_manifest.csv",
        "audit": output_dir / "pilot_manifest_audit.csv",
        "file_audit": output_dir / "pilot_source_file_audit.csv",
        "method_spec": output_dir / "pilot_method_spec.json",
        "design_md": design_md,
        "design_html": design_html,
        "sample_output": output_dir / "pilot_response_samples.csv.gz",
    }
    eligible.to_csv(paths["eligible"], index=False)
    selected.to_csv(paths["selected"], index=False)
    generation_manifest.to_csv(paths["generation_manifest"], index=False)
    audit.to_csv(paths["audit"], index=False)
    file_audit.to_csv(paths["file_audit"], index=False)
    paths["method_spec"].write_text(json.dumps(design, indent=2), encoding="utf-8")
    command = command_block(
        generation_manifest=paths["generation_manifest"],
        sample_output=paths["sample_output"],
        model_name=model_name,
        temperatures=temperatures,
        samples_per_context=samples_per_context,
        max_new_tokens=max_new_tokens,
        top_p=top_p,
        top_k=top_k,
        batch_contexts=batch_contexts,
        batch_samples=batch_samples,
        dtype=dtype,
    )
    markdown = build_design_markdown(
        output_dir=output_dir,
        design=design,
        audit=audit,
        generation_manifest=generation_manifest,
        command=command,
    )
    design_md.parent.mkdir(parents=True, exist_ok=True)
    design_md.write_text(markdown, encoding="utf-8")
    render_markdown_file(design_md, design_html)
    return paths


def entropy_for_texts(texts: Sequence[object], *, normalization: str) -> tuple[float, float, int, int, float]:
    """Return entropy, corrected entropy, unique count, total count, top probability."""

    canonical = [canonical_response(text, mode=normalization) for text in texts]
    counts = Counter(canonical)
    total = sum(counts.values())
    entropy = empirical_entropy_bits(counts)
    corrected = miller_madow_entropy_bits(entropy, unique_count=len(counts), sample_count=total)
    top = counts.most_common(1)[0][1] / total if total else math.nan
    return entropy, corrected, len(counts), total, top


def safe_corr(left: pd.Series, right: pd.Series, *, method: str) -> float:
    """Return a correlation or NaN when one side is constant/too small."""

    frame = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(frame) < 2 or frame["left"].nunique() < 2 or frame["right"].nunique() < 2:
        return math.nan
    return float(frame["left"].corr(frame["right"], method=method))


def summarize_sample_groups(samples: pd.DataFrame, *, normalization: str) -> pd.DataFrame:
    """Summarize response samples by context and temperature."""

    samples = samples.copy()
    samples["temperature"] = pd.to_numeric(samples["temperature"], errors="coerce")
    samples["sample_index"] = pd.to_numeric(samples["sample_index"], errors="coerce")
    rows: list[dict[str, object]] = []
    for (cid, temp), group in samples.groupby(["context_id", "temperature"], sort=True, dropna=False):
        entropy, corrected, unique_count, sample_count, top_prob = entropy_for_texts(
            group["sampled_response_text"].tolist(),
            normalization=normalization,
        )
        effort = pd.DataFrame([response_effort_counts(text) for text in group["sampled_response_text"].tolist()])
        rows.append(
            {
                "context_id": cid,
                "temperature": temp,
                "sample_count": sample_count,
                "unique_response_count": unique_count,
                "response_entropy_mle_bits": entropy,
                "response_entropy_miller_madow_bits": corrected,
                "top_response_probability": top_prob,
                "mean_sample_word_count": float(effort["sample_word_count"].mean()) if not effort.empty else math.nan,
                "mean_sample_morpheme_count_surface": float(effort["sample_morpheme_count_surface"].mean()) if not effort.empty else math.nan,
                "mean_sample_syllable_count_pkg": float(effort["sample_syllable_count_pkg"].mean()) if not effort.empty else math.nan,
                "empty_response_rate": float(pd.to_numeric(group.get("empty_response", 0), errors="coerce").fillna(0).mean()),
                "hit_max_new_tokens_rate": float(pd.to_numeric(group.get("hit_max_new_tokens", 0), errors="coerce").fillna(0).mean()),
                "stopped_by_boundary_rate": float(pd.to_numeric(group.get("stopped_by_speaker_boundary", 0), errors="coerce").fillna(0).mean()),
                "mean_generated_token_count": float(pd.to_numeric(group.get("generated_token_count", pd.Series(dtype=float)), errors="coerce").mean()),
            }
        )
    return pd.DataFrame(rows)


def split_half_reliability(samples: pd.DataFrame, *, normalization: str) -> pd.DataFrame:
    """Compute split-half entropy reliability by temperature."""

    samples = samples.copy()
    samples["sample_index"] = pd.to_numeric(samples["sample_index"], errors="coerce")
    rows: list[dict[str, object]] = []
    for (cid, temp), group in samples.groupby(["context_id", "temperature"], sort=True, dropna=False):
        if group["sample_index"].notna().sum() < 4:
            continue
        median_index = group["sample_index"].median()
        first = group[group["sample_index"] <= median_index]
        second = group[group["sample_index"] > median_index]
        if first.empty or second.empty:
            continue
        _, h1, _, n1, _ = entropy_for_texts(first["sampled_response_text"].tolist(), normalization=normalization)
        _, h2, _, n2, _ = entropy_for_texts(second["sampled_response_text"].tolist(), normalization=normalization)
        rows.append(
            {
                "context_id": cid,
                "temperature": float(temp),
                "first_half_entropy_bits": h1,
                "second_half_entropy_bits": h2,
                "abs_diff_bits": abs(h1 - h2),
                "first_half_n": n1,
                "second_half_n": n2,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    out_rows: list[dict[str, object]] = []
    for temp, group in frame.groupby("temperature", sort=True):
        out_rows.append(
            {
                "temperature": temp,
                "contexts": int(len(group)),
                "pearson_r": safe_corr(group["first_half_entropy_bits"], group["second_half_entropy_bits"], method="pearson"),
                "spearman_r": safe_corr(group["first_half_entropy_bits"], group["second_half_entropy_bits"], method="spearman"),
                "mean_abs_diff_bits": float(group["abs_diff_bits"].mean()),
                "median_abs_diff_bits": float(group["abs_diff_bits"].median()),
            }
        )
    return pd.DataFrame(out_rows)


def downsample_stability(samples: pd.DataFrame, *, sample_sizes: Sequence[int], normalization: str) -> pd.DataFrame:
    """Compare entropy from smaller prefixes to full-sample entropy."""

    samples = samples.copy()
    samples["sample_index"] = pd.to_numeric(samples["sample_index"], errors="coerce")
    full = summarize_sample_groups(samples, normalization=normalization)[
        ["context_id", "temperature", "response_entropy_miller_madow_bits"]
    ].rename(columns={"response_entropy_miller_madow_bits": "full_entropy_bits"})
    rows: list[dict[str, object]] = []
    for size in sample_sizes:
        sub = samples[samples["sample_index"] < size].copy()
        partial = summarize_sample_groups(sub, normalization=normalization)[
            ["context_id", "temperature", "sample_count", "response_entropy_miller_madow_bits"]
        ].rename(columns={"response_entropy_miller_madow_bits": "partial_entropy_bits"})
        partial = partial[partial["sample_count"] >= size].copy()
        merged = partial.merge(full, on=["context_id", "temperature"], how="inner")
        for temp, group in merged.groupby("temperature", sort=True):
            rows.append(
                {
                    "sample_size": size,
                    "temperature": temp,
                    "contexts": int(len(group)),
                    "pearson_r_vs_full": safe_corr(group["partial_entropy_bits"], group["full_entropy_bits"], method="pearson"),
                    "spearman_r_vs_full": safe_corr(group["partial_entropy_bits"], group["full_entropy_bits"], method="spearman"),
                    "mean_abs_diff_bits_vs_full": float((group["partial_entropy_bits"] - group["full_entropy_bits"]).abs().mean()),
                }
            )
    return pd.DataFrame(rows)


def temperature_rank_correlations(features: pd.DataFrame) -> pd.DataFrame:
    """Return Spearman rank correlations between temperature entropy estimates."""

    pivot = features.pivot_table(
        index="context_id",
        columns="temperature",
        values="response_entropy_miller_madow_bits",
        aggfunc="first",
    )
    corr = pivot.corr(method="spearman")
    return corr.reset_index().rename(columns={"temperature": "temperature_row"})


def quality_by_temperature(features: pd.DataFrame) -> pd.DataFrame:
    """Summarize output quality and entropy by temperature."""

    return (
        features.groupby("temperature", observed=True)
        .agg(
            contexts=("context_id", "nunique"),
            mean_sample_count=("sample_count", "mean"),
            min_sample_count=("sample_count", "min"),
            mean_entropy_mm_bits=("response_entropy_miller_madow_bits", "mean"),
            sd_entropy_mm_bits=("response_entropy_miller_madow_bits", "std"),
            mean_unique_response_count=("unique_response_count", "mean"),
            mean_top_response_probability=("top_response_probability", "mean"),
            mean_empty_response_rate=("empty_response_rate", "mean"),
            mean_hit_max_new_tokens_rate=("hit_max_new_tokens_rate", "mean"),
            mean_stopped_by_boundary_rate=("stopped_by_boundary_rate", "mean"),
            mean_sample_word_count=("mean_sample_word_count", "mean"),
        )
        .reset_index()
    )


def plot_diagnostics(
    *,
    features: pd.DataFrame,
    quality: pd.DataFrame,
    split_half: pd.DataFrame,
    downsample: pd.DataFrame,
    temp_corr: pd.DataFrame,
    fig_dir: Path,
) -> pd.DataFrame:
    """Write pilot diagnostics figures."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    plt.figure(figsize=(9, 5))
    sns.boxplot(data=features, x="temperature", y="response_entropy_miller_madow_bits", color="#7aa6b8")
    plt.xlabel("Temperature")
    plt.ylabel("Response entropy (Miller-Madow bits)")
    plt.title("Entropy Distribution By Temperature")
    plt.tight_layout()
    path = fig_dir / "pilot_entropy_distribution_by_temperature.png"
    plt.savefig(path, dpi=180)
    plt.close()
    rows.append({"figure_id": path.stem, "path": str(path), "description": "Distribution of response entropy by temperature."})

    q_long = quality.melt(
        id_vars=["temperature"],
        value_vars=["mean_empty_response_rate", "mean_hit_max_new_tokens_rate", "mean_stopped_by_boundary_rate"],
        var_name="quality_metric",
        value_name="rate",
    )
    plt.figure(figsize=(9, 5))
    sns.lineplot(data=q_long, x="temperature", y="rate", hue="quality_metric", marker="o")
    plt.xlabel("Temperature")
    plt.ylabel("Mean rate across contexts")
    plt.title("Output Quality Rates By Temperature")
    plt.tight_layout()
    path = fig_dir / "pilot_quality_rates_by_temperature.png"
    plt.savefig(path, dpi=180)
    plt.close()
    rows.append({"figure_id": path.stem, "path": str(path), "description": "Empty, max-token, and boundary-stop rates by temperature."})

    if not split_half.empty:
        plt.figure(figsize=(8, 4.8))
        sns.lineplot(data=split_half, x="temperature", y="spearman_r", marker="o")
        plt.ylim(0, 1)
        plt.xlabel("Temperature")
        plt.ylabel("Split-half Spearman r")
        plt.title("Split-Half Entropy Reliability")
        plt.tight_layout()
        path = fig_dir / "pilot_split_half_reliability.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Rank reliability between first and second half samples."})

    if not downsample.empty:
        plt.figure(figsize=(9, 5))
        sns.lineplot(data=downsample, x="sample_size", y="spearman_r_vs_full", hue="temperature", marker="o")
        plt.ylim(0, 1)
        plt.xlabel("Samples per context")
        plt.ylabel("Spearman r vs full sample")
        plt.title("Downsample Stability")
        plt.tight_layout()
        path = fig_dir / "pilot_downsample_stability.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "How quickly entropy rankings stabilize as M increases."})

    if not temp_corr.empty:
        corr = temp_corr.set_index("temperature_row")
        plt.figure(figsize=(7, 6))
        sns.heatmap(corr, vmin=0, vmax=1, cmap="viridis", annot=True, fmt=".2f")
        plt.xlabel("Temperature")
        plt.ylabel("Temperature")
        plt.title("Temperature Rank-Correlation Matrix")
        plt.tight_layout()
        path = fig_dir / "pilot_temperature_rank_correlation.png"
        plt.savefig(path, dpi=180)
        plt.close()
        rows.append({"figure_id": path.stem, "path": str(path), "description": "Spearman correlations of context entropy rankings across temperatures."})

    return pd.DataFrame(rows)


def image_md(path: str | Path, alt: str) -> str:
    """Return Markdown image syntax."""

    path = Path(path)
    if not path.exists():
        return f"_Missing plot: `{path}`_"
    return f"![{alt}](../{path.as_posix()})"


def build_diagnostics_markdown(
    *,
    output_dir: Path,
    quality: pd.DataFrame,
    split_half: pd.DataFrame,
    downsample: pd.DataFrame,
    temp_corr: pd.DataFrame,
    figures: pd.DataFrame,
) -> str:
    """Build the diagnostics report after generation."""

    fig_paths = {row["figure_id"]: row["path"] for row in figures.to_dict("records")}
    return f"""# Response-Space Entropy Pilot Diagnostics

This report audits the sampled-response pilot before any production-scale
response entropy run. It focuses on output quality, entropy stability, and
temperature sensitivity.

## Output Quality By Temperature

{markdown_table(quality, max_rows=20)}

**How to read this table.** Temperatures with high empty-response rates, high
max-token-hit rates, or very unstable entropy should not be used as primary
measurement settings. Boundary-stop rate is not automatically bad: it can mean
the model naturally moved to the next speaker turn and the cleaner truncated it.

{image_md(fig_paths.get("pilot_quality_rates_by_temperature", ""), "quality rates by temperature")}

## Entropy Distributions

{image_md(fig_paths.get("pilot_entropy_distribution_by_temperature", ""), "entropy distributions by temperature")}

**How to read this plot.** Higher temperatures should usually increase entropy.
If entropy saturates near the sample cap or stops varying by context, that
temperature may be measuring decoding noise rather than contextual uncertainty.

## Split-Half Reliability

{markdown_table(split_half, max_rows=20)}

{image_md(fig_paths.get("pilot_split_half_reliability", ""), "split-half reliability")}

**How to read this plot.** High Spearman correlation means the ranking of
contexts by response entropy is similar in the first and second half of the
samples. Low reliability means more samples or a different decoding setting may
be needed.

## Downsample Stability

{markdown_table(downsample, max_rows=80)}

{image_md(fig_paths.get("pilot_downsample_stability", ""), "downsample stability")}

**How to read this plot.** If M=50 already matches M=100 closely, production
could potentially use fewer samples. If M=100 is still unstable, the pilot
argues for more samples or more robust predictors.

## Temperature Rank Correlation

{markdown_table(temp_corr, max_rows=20)}

{image_md(fig_paths.get("pilot_temperature_rank_correlation", ""), "temperature rank correlation")}

**How to read this plot.** High correlations mean temperatures mostly rank
contexts similarly. Low correlations mean temperature is not just a sensitivity
check: it changes the measurement object substantially.

## Files

- Context-temperature features: `{output_dir / "pilot_context_temperature_features.csv"}`
- Quality by temperature: `{output_dir / "pilot_quality_by_temperature.csv"}`
- Split-half reliability: `{output_dir / "pilot_split_half_reliability.csv"}`
- Downsample stability: `{output_dir / "pilot_downsample_stability.csv"}`
- Temperature correlations: `{output_dir / "pilot_temperature_rank_correlations.csv"}`
- Figure manifest: `{output_dir / "pilot_diagnostic_figure_manifest.csv"}`
"""


def build_pilot_diagnostics(
    *,
    samples_csv: Path,
    output_dir: Path,
    fig_dir: Path,
    diagnostic_md: Path,
    diagnostic_html: Path,
    normalization: str,
    downsample_sizes: Sequence[int],
) -> dict[str, Path]:
    """Build all post-generation pilot diagnostics."""

    output_dir.mkdir(parents=True, exist_ok=True)
    samples = pd.read_csv(samples_csv, dtype=str, keep_default_na=False, low_memory=False)
    features = summarize_sample_groups(samples, normalization=normalization)
    quality = quality_by_temperature(features)
    split_half = split_half_reliability(samples, normalization=normalization)
    downsample = downsample_stability(samples, sample_sizes=downsample_sizes, normalization=normalization)
    temp_corr = temperature_rank_correlations(features)
    figures = plot_diagnostics(
        features=features,
        quality=quality,
        split_half=split_half,
        downsample=downsample,
        temp_corr=temp_corr,
        fig_dir=fig_dir,
    )
    paths = {
        "features": output_dir / "pilot_context_temperature_features.csv",
        "quality": output_dir / "pilot_quality_by_temperature.csv",
        "split_half": output_dir / "pilot_split_half_reliability.csv",
        "downsample": output_dir / "pilot_downsample_stability.csv",
        "temperature_correlations": output_dir / "pilot_temperature_rank_correlations.csv",
        "figures": output_dir / "pilot_diagnostic_figure_manifest.csv",
        "diagnostic_md": diagnostic_md,
        "diagnostic_html": diagnostic_html,
    }
    features.to_csv(paths["features"], index=False)
    quality.to_csv(paths["quality"], index=False)
    split_half.to_csv(paths["split_half"], index=False)
    downsample.to_csv(paths["downsample"], index=False)
    temp_corr.to_csv(paths["temperature_correlations"], index=False)
    figures.to_csv(paths["figures"], index=False)
    markdown = build_diagnostics_markdown(
        output_dir=output_dir,
        quality=quality,
        split_half=split_half,
        downsample=downsample,
        temp_corr=temp_corr,
        figures=figures,
    )
    diagnostic_md.parent.mkdir(parents=True, exist_ok=True)
    diagnostic_md.write_text(markdown, encoding="utf-8")
    render_markdown_file(diagnostic_md, diagnostic_html)
    return paths


def build_cli() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["manifest", "diagnostics"], default="manifest")
    parser.add_argument("--scored-root", type=Path, default=DEFAULT_MAIN_SCORED_ROOT)
    parser.add_argument("--score-source", default="pbm_mistral_patched_006_023")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--design-md", type=Path, default=DEFAULT_DESIGN_MD)
    parser.add_argument("--design-html", type=Path, default=DEFAULT_DESIGN_HTML)
    parser.add_argument("--diagnostic-md", type=Path, default=DEFAULT_DIAGNOSTIC_MD)
    parser.add_argument("--diagnostic-html", type=Path, default=DEFAULT_DIAGNOSTIC_HTML)
    parser.add_argument("--context-ks", default=",".join(DEFAULT_CONTEXT_KS))
    parser.add_argument("--sample-per-age-bin-context-k", type=int, default=20)
    parser.add_argument("--min-context-words", type=int, default=1)
    parser.add_argument("--temperatures", default=",".join(str(x) for x in DEFAULT_TEMPERATURES))
    parser.add_argument("--samples-per-context", type=int, default=100)
    parser.add_argument("--max-new-tokens", type=int, default=24)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--top-k", type=int, default=0)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt-template", default=DEFAULT_PROMPT_TEMPLATE)
    parser.add_argument("--batch-contexts", type=int, default=2)
    parser.add_argument("--batch-samples", type=int, default=16)
    parser.add_argument("--dtype", default="bfloat16")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--samples", type=Path, default=DEFAULT_OUTPUT_DIR / "pilot_response_samples.csv.gz")
    parser.add_argument("--normalization", choices=["exact", "casefold"], default="casefold")
    parser.add_argument("--downsample-sizes", default="25,50,75,100")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint."""

    args = build_cli().parse_args(argv)
    context_ks = split_csv(args.context_ks)
    temperatures = parse_float_csv(args.temperatures)
    if args.stage == "manifest":
        paths = build_pilot_manifest(
            scored_root=args.scored_root,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            design_md=args.design_md,
            design_html=args.design_html,
            score_source=args.score_source,
            context_ks=context_ks,
            sample_per_age_bin_context_k=args.sample_per_age_bin_context_k,
            min_context_words=args.min_context_words,
            temperatures=temperatures,
            samples_per_context=args.samples_per_context,
            max_new_tokens=args.max_new_tokens,
            top_p=args.top_p,
            top_k=args.top_k,
            model_name=args.model,
            prompt_template=args.prompt_template,
            batch_contexts=args.batch_contexts,
            batch_samples=args.batch_samples,
            dtype=args.dtype,
            seed=args.seed,
        )
    else:
        paths = build_pilot_diagnostics(
            samples_csv=args.samples,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            diagnostic_md=args.diagnostic_md,
            diagnostic_html=args.diagnostic_html,
            normalization=args.normalization,
            downsample_sizes=[int(x) for x in split_csv(args.downsample_sizes)],
        )
    for label, path in paths.items():
        print(f"[OK] {label}: {path}")


if __name__ == "__main__":
    main()
