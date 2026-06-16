#!/usr/bin/env python3
"""Build and summarize a small response-generation stopping probe."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

try:
    from render_markdown_report import render_markdown_file
    from sample_context_responses import DEFAULT_STOP_STRINGS
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file
    from src.sample_context_responses import DEFAULT_STOP_STRINGS


DEFAULT_INPUT_MANIFEST = Path("results/response_entropy_pilot_grid/pilot_generation_manifest.csv")
DEFAULT_OUTPUT_DIR = Path("results/response_entropy_stopping_probe")
DEFAULT_FIG_DIR = Path("figs/response_entropy_stopping_probe")
DEFAULT_REPORT_MD = Path("docs/response_entropy_stopping_probe.md")
DEFAULT_REPORT_HTML = Path("docs/response_entropy_stopping_probe.html")
DEFAULT_MAX_NEW_TOKENS = (12, 24, 48, 96)
DEFAULT_TEMPERATURES = (0.5, 0.7, 1.0)
DEFAULT_SAMPLES_PER_CONTEXT = 10
DEFAULT_CONTEXTS_PER_BUCKET = 10
DEFAULT_SEED = 20260616


def parse_int_csv(value: str | Sequence[int]) -> list[int]:
    """Parse comma-separated integers."""

    if isinstance(value, str):
        return [int(part.strip()) for part in value.split(",") if part.strip()]
    return [int(part) for part in value]


def parse_float_csv(value: str | Sequence[float]) -> list[float]:
    """Parse comma-separated floats."""

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


def context_length_bucket(word_count: int | float) -> str:
    """Return a compact context-length bucket label."""

    if pd.isna(word_count):
        return "unknown"
    count = int(word_count)
    if count <= 1:
        return "01_one_word"
    if count <= 4:
        return "02_two_to_four"
    if count <= 9:
        return "03_five_to_nine"
    return "04_ten_plus"


def simple_word_count(text: object) -> int:
    """Count whitespace-separated words in generated text."""

    value = str(text or "").strip()
    if not value:
        return 0
    return len(value.split())


def first_boundary_position(text: object) -> int:
    """Return first speaker-boundary character position, or -1 if absent."""

    raw = str(text or "")
    positions = [raw.find(marker) for marker in DEFAULT_STOP_STRINGS if raw.find(marker) >= 0]
    return min(positions) if positions else -1


def stop_category(row: pd.Series) -> str:
    """Classify how the generated sample ended or was trimmed."""

    empty = int(row.get("empty_response_int", 0)) == 1
    hit_max = int(row.get("hit_max_new_tokens_int", 0)) == 1
    boundary = int(row.get("stopped_by_speaker_boundary_int", 0)) == 1
    if empty:
        return "empty"
    if boundary and hit_max:
        return "boundary_seen_and_generation_hit_cap"
    if boundary:
        return "boundary_seen_before_cap"
    if hit_max:
        return "hit_cap_no_boundary"
    return "natural_eos_no_boundary"


def build_probe_manifest(
    *,
    input_manifest: Path,
    output_dir: Path,
    contexts_per_bucket: int,
    seed: int,
    max_new_tokens: Sequence[int],
    temperatures: Sequence[float],
    samples_per_context: int,
) -> dict[str, Path]:
    """Select a small balanced manifest from the full pilot manifest."""

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(input_manifest, dtype=str, keep_default_na=False)
    if "context_word_count" not in manifest.columns:
        raise KeyError(f"{input_manifest} missing context_word_count")
    manifest["context_word_count_numeric"] = pd.to_numeric(manifest["context_word_count"], errors="coerce")
    manifest["stopping_probe_bucket"] = manifest["context_word_count_numeric"].map(context_length_bucket)

    selected_parts: list[pd.DataFrame] = []
    audit_rows: list[dict[str, object]] = []
    for bucket_index, (bucket, group) in enumerate(sorted(manifest.groupby("stopping_probe_bucket"), key=lambda item: item[0])):
        group = group.sort_values(["context_word_count_numeric", "context_id"]).copy()
        take = min(contexts_per_bucket, len(group))
        selected = group.sample(n=take, random_state=seed + bucket_index).sort_values(
            ["context_word_count_numeric", "context_id"]
        )
        selected_parts.append(selected)
        audit_rows.append(
            {
                "bucket": bucket,
                "available_contexts": len(group),
                "selected_contexts": take,
                "min_context_words_selected": int(selected["context_word_count_numeric"].min()) if take else "",
                "max_context_words_selected": int(selected["context_word_count_numeric"].max()) if take else "",
            }
        )

    selected_manifest = pd.concat(selected_parts, ignore_index=True)
    selected_manifest.insert(0, "stopping_probe_row", range(len(selected_manifest)))
    selected_manifest["stopping_probe_seed"] = seed

    manifest_path = output_dir / "stopping_probe_manifest.csv"
    audit_path = output_dir / "stopping_probe_manifest_audit.csv"
    spec_path = output_dir / "stopping_probe_method_spec.json"
    selected_manifest.to_csv(manifest_path, index=False)
    pd.DataFrame(audit_rows).to_csv(audit_path, index=False)

    planned_samples = len(selected_manifest) * len(max_new_tokens) * len(temperatures) * samples_per_context
    spec = {
        "source_manifest": str(input_manifest),
        "contexts": int(len(selected_manifest)),
        "contexts_per_bucket": int(contexts_per_bucket),
        "seed": int(seed),
        "max_new_tokens": [int(value) for value in max_new_tokens],
        "temperatures": [float(value) for value in temperatures],
        "samples_per_context": int(samples_per_context),
        "planned_samples": int(planned_samples),
    }
    spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return {"manifest": manifest_path, "audit": audit_path, "spec": spec_path}


def load_probe_samples(output_dir: Path) -> pd.DataFrame:
    """Load all per-cap stopping probe sample files."""

    paths = sorted(output_dir.glob("stopping_probe_samples_max*.csv.gz"))
    if not paths:
        raise FileNotFoundError(f"no stopping_probe_samples_max*.csv.gz files in {output_dir}")
    frames = []
    for path in paths:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False, on_bad_lines="skip")
        frame["sample_source_file"] = path.name
        frames.append(frame)
    samples = pd.concat(frames, ignore_index=True)
    for column in ["temperature", "max_new_tokens", "sample_index", "generated_token_count"]:
        samples[f"{column}_numeric"] = pd.to_numeric(samples[column], errors="coerce")
    for column in ["hit_max_new_tokens", "stopped_by_speaker_boundary", "empty_response"]:
        samples[f"{column}_int"] = pd.to_numeric(samples[column], errors="coerce").fillna(0).astype(int)
    samples["sampled_response_word_count"] = samples["sampled_response_text"].map(simple_word_count)
    samples["raw_generated_word_count"] = samples["raw_generated_text"].map(simple_word_count)
    samples["sampled_response_char_count"] = samples["sampled_response_text"].map(lambda value: len(str(value or "")))
    samples["raw_generated_char_count"] = samples["raw_generated_text"].map(lambda value: len(str(value or "")))
    samples["first_boundary_char_position"] = samples["raw_generated_text"].map(first_boundary_position)
    samples["stop_category"] = samples.apply(stop_category, axis=1)
    return samples


def summarize_by_setting(samples: pd.DataFrame) -> pd.DataFrame:
    """Summarize stop behavior by max-token cap and temperature."""

    rows = []
    group_cols = ["max_new_tokens_numeric", "temperature_numeric"]
    for (max_new_tokens, temperature), group in samples.groupby(group_cols, dropna=False):
        contexts = group["context_id"].nunique()
        boundary_positions = group.loc[group["first_boundary_char_position"] >= 0, "first_boundary_char_position"]
        rows.append(
            {
                "max_new_tokens": int(max_new_tokens),
                "temperature": float(temperature),
                "rows": len(group),
                "contexts": contexts,
                "mean_samples_per_context": len(group) / contexts if contexts else math.nan,
                "empty_response_rate": group["empty_response_int"].mean(),
                "hit_max_rate": group["hit_max_new_tokens_int"].mean(),
                "boundary_seen_rate": group["stopped_by_speaker_boundary_int"].mean(),
                "hit_cap_no_boundary_rate": (group["stop_category"] == "hit_cap_no_boundary").mean(),
                "natural_eos_no_boundary_rate": (group["stop_category"] == "natural_eos_no_boundary").mean(),
                "boundary_and_hit_cap_rate": (group["stop_category"] == "boundary_seen_and_generation_hit_cap").mean(),
                "mean_generated_tokens": group["generated_token_count_numeric"].mean(),
                "mean_sampled_words_after_trim": group["sampled_response_word_count"].mean(),
                "p50_sampled_words_after_trim": group["sampled_response_word_count"].quantile(0.50),
                "p90_sampled_words_after_trim": group["sampled_response_word_count"].quantile(0.90),
                "p95_sampled_words_after_trim": group["sampled_response_word_count"].quantile(0.95),
                "mean_raw_generated_words": group["raw_generated_word_count"].mean(),
                "median_boundary_char_position": boundary_positions.median() if len(boundary_positions) else math.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["temperature", "max_new_tokens"]).reset_index(drop=True)


def summarize_stop_categories(samples: pd.DataFrame) -> pd.DataFrame:
    """Write a long stop-category count table."""

    counts = (
        samples.groupby(["max_new_tokens_numeric", "temperature_numeric", "stop_category"], dropna=False)
        .size()
        .reset_index(name="rows")
    )
    totals = counts.groupby(["max_new_tokens_numeric", "temperature_numeric"])["rows"].transform("sum")
    counts["rate"] = counts["rows"] / totals
    return counts.rename(columns={"max_new_tokens_numeric": "max_new_tokens", "temperature_numeric": "temperature"})


def manual_examples(samples: pd.DataFrame, *, per_setting: int = 4) -> pd.DataFrame:
    """Select compact manual-inspection examples for each setting."""

    rows = []
    columns = [
        "context_id",
        "context_text",
        "temperature",
        "max_new_tokens",
        "sample_index",
        "stop_category",
        "generated_token_count",
        "sampled_response_word_count",
        "raw_generated_word_count",
        "speaker_boundary_marker",
        "sampled_response_text",
        "raw_generated_text",
    ]
    for _, group in samples.groupby(["max_new_tokens_numeric", "temperature_numeric"], dropna=False):
        picked = (
            group.sort_values(["stop_category", "sampled_response_word_count", "context_id"], ascending=[True, False, True])
            .head(per_setting)
            .copy()
        )
        picked["temperature"] = picked["temperature_numeric"]
        picked["max_new_tokens"] = picked["max_new_tokens_numeric"].astype(int)
        rows.append(picked[columns])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=columns)


def plot_probe(summary: pd.DataFrame, categories: pd.DataFrame, fig_dir: Path) -> pd.DataFrame:
    """Write diagnostic figures."""

    fig_dir.mkdir(parents=True, exist_ok=True)
    figures = []

    plt.figure(figsize=(8, 5))
    sns.lineplot(data=summary, x="max_new_tokens", y="hit_max_rate", hue="temperature", marker="o")
    plt.ylim(0, 1.05)
    plt.title("Max-Token Hit Rate")
    plt.tight_layout()
    path = fig_dir / "stopping_probe_hit_max_rate.png"
    plt.savefig(path, dpi=180)
    plt.close()
    figures.append({"figure_id": path.stem, "path": str(path), "description": "Rate of samples that reached the max_new_tokens cap."})

    plt.figure(figsize=(8, 5))
    sns.lineplot(data=summary, x="max_new_tokens", y="boundary_seen_rate", hue="temperature", marker="o")
    plt.ylim(0, 1.05)
    plt.title("Speaker-Boundary Seen Rate")
    plt.tight_layout()
    path = fig_dir / "stopping_probe_boundary_rate.png"
    plt.savefig(path, dpi=180)
    plt.close()
    figures.append({"figure_id": path.stem, "path": str(path), "description": "Rate of samples containing a later speaker boundary marker."})

    plt.figure(figsize=(8, 5))
    sns.lineplot(data=summary, x="max_new_tokens", y="p90_sampled_words_after_trim", hue="temperature", marker="o")
    plt.title("P90 Trimmed Response Length")
    plt.tight_layout()
    path = fig_dir / "stopping_probe_p90_trimmed_words.png"
    plt.savefig(path, dpi=180)
    plt.close()
    figures.append({"figure_id": path.stem, "path": str(path), "description": "90th percentile words after speaker-boundary trimming."})

    category_pivot = categories.pivot_table(
        index=["temperature", "max_new_tokens"], columns="stop_category", values="rate", fill_value=0
    ).reset_index()
    long = category_pivot.melt(["temperature", "max_new_tokens"], var_name="stop_category", value_name="rate")
    long["setting"] = long.apply(
        lambda row: f"T={float(row['temperature']):g}\nmax={int(row['max_new_tokens'])}",
        axis=1,
    )
    setting_order = (
        long[["temperature", "max_new_tokens", "setting"]]
        .drop_duplicates()
        .sort_values(["temperature", "max_new_tokens"])["setting"]
        .tolist()
    )
    plt.figure(figsize=(max(8, 1.2 * len(setting_order)), 5))
    sns.barplot(data=long, x="setting", y="rate", hue="stop_category", order=setting_order)
    plt.ylim(0, 1.05)
    plt.xlabel("setting")
    plt.ylabel("rate")
    plt.title("Stop Categories")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    path = fig_dir / "stopping_probe_stop_categories.png"
    plt.savefig(path, dpi=180)
    plt.close()
    figures.append({"figure_id": path.stem, "path": str(path), "description": "Stop-category rates by temperature and max-token cap."})

    return pd.DataFrame(figures)


def build_report(
    *,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    summary: pd.DataFrame,
    categories: pd.DataFrame,
    manifest_audit: pd.DataFrame,
    figures: pd.DataFrame,
) -> None:
    """Render a small stopping-probe report."""

    fig_paths = {row["figure_id"]: row["path"] for row in figures.to_dict("records")}

    def img(figure_id: str, alt: str) -> str:
        path = Path(fig_paths.get(figure_id, ""))
        if not path.exists():
            return f"_Missing plot: `{path}`_"
        return f"![{alt}](../{path.as_posix()})"

    markdown = f"""# Response Entropy Stopping Probe

This is a bounded diagnostic rerun for response-space entropy generation. It
tests whether generated child responses stop naturally, reach a later speaker
boundary, or keep running until the configured max-token cap.

## Manifest

{markdown_table(manifest_audit, max_rows=20)}

## Setting Summary

{markdown_table(summary, max_rows=80, digits=4)}

## Stop Categories

{markdown_table(categories, max_rows=120, digits=4)}

## Figures

{img("stopping_probe_hit_max_rate", "max-token hit rate")}

{img("stopping_probe_boundary_rate", "speaker-boundary rate")}

{img("stopping_probe_p90_trimmed_words", "p90 trimmed response words")}

{img("stopping_probe_stop_categories", "stop categories")}

## Files

- Combined samples: `{output_dir / "stopping_probe_samples_combined.csv.gz"}`
- Setting summary: `{output_dir / "stopping_probe_setting_summary.csv"}`
- Stop categories: `{output_dir / "stopping_probe_stop_category_summary.csv"}`
- Manual examples: `{output_dir / "stopping_probe_manual_examples.csv"}`
- Figure manifest: `{output_dir / "stopping_probe_figure_manifest.csv"}`
"""
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(markdown, encoding="utf-8")
    render_markdown_file(report_md, report_html)


def summarize_probe(*, output_dir: Path, fig_dir: Path, report_md: Path, report_html: Path) -> dict[str, Path]:
    """Summarize generated stopping-probe samples."""

    output_dir.mkdir(parents=True, exist_ok=True)
    samples = load_probe_samples(output_dir)
    summary = summarize_by_setting(samples)
    categories = summarize_stop_categories(samples)
    examples = manual_examples(samples)
    figures = plot_probe(summary, categories, fig_dir)
    audit_path = output_dir / "stopping_probe_manifest_audit.csv"
    manifest_audit = pd.read_csv(audit_path) if audit_path.exists() else pd.DataFrame()

    paths = {
        "combined_samples": output_dir / "stopping_probe_samples_combined.csv.gz",
        "setting_summary": output_dir / "stopping_probe_setting_summary.csv",
        "stop_categories": output_dir / "stopping_probe_stop_category_summary.csv",
        "manual_examples": output_dir / "stopping_probe_manual_examples.csv",
        "figures": output_dir / "stopping_probe_figure_manifest.csv",
        "report_md": report_md,
        "report_html": report_html,
    }
    samples.to_csv(paths["combined_samples"], index=False)
    summary.to_csv(paths["setting_summary"], index=False)
    categories.to_csv(paths["stop_categories"], index=False)
    examples.to_csv(paths["manual_examples"], index=False)
    figures.to_csv(paths["figures"], index=False)
    build_report(
        output_dir=output_dir,
        fig_dir=fig_dir,
        report_md=report_md,
        report_html=report_html,
        summary=summary,
        categories=categories,
        manifest_audit=manifest_audit,
        figures=figures,
    )
    return paths


def build_cli() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["manifest", "summarize"], default="manifest")
    parser.add_argument("--input-manifest", type=Path, default=DEFAULT_INPUT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--contexts-per-bucket", type=int, default=DEFAULT_CONTEXTS_PER_BUCKET)
    parser.add_argument("--max-new-tokens", default=",".join(str(value) for value in DEFAULT_MAX_NEW_TOKENS))
    parser.add_argument("--temperatures", default=",".join(str(value) for value in DEFAULT_TEMPERATURES))
    parser.add_argument("--samples-per-context", type=int, default=DEFAULT_SAMPLES_PER_CONTEXT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Run CLI."""

    parser = build_cli()
    args = parser.parse_args(argv)
    max_new_tokens = parse_int_csv(args.max_new_tokens)
    temperatures = parse_float_csv(args.temperatures)
    if args.stage == "manifest":
        paths = build_probe_manifest(
            input_manifest=args.input_manifest,
            output_dir=args.output_dir,
            contexts_per_bucket=args.contexts_per_bucket,
            seed=args.seed,
            max_new_tokens=max_new_tokens,
            temperatures=temperatures,
            samples_per_context=args.samples_per_context,
        )
    else:
        paths = summarize_probe(
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            report_md=args.report_md,
            report_html=args.report_html,
        )
    for key, path in paths.items():
        print(f"[OK] {key}: {path}")


if __name__ == "__main__":
    main()
