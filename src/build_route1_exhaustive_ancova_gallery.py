#!/usr/bin/env python3
"""Build a figure-first Route 1 ANCOVA comparison gallery.

This report is deliberately an evidence-selection gallery, not the supervisor
report. It fits broad adjusted group-comparison models across multiple effort
measures, renders the figures first, and pushes noisy statistical tables to the
audit section and CSV outputs.
"""

from __future__ import annotations

import argparse
import gc
import math
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_OUTPUT_DIR = Path("results/route1_exhaustive_ancova_gallery")
DEFAULT_FIG_DIR = Path("figs/route1_exhaustive_ancova_gallery")
DEFAULT_DOC_MD = Path("docs/route1_exhaustive_ancova_gallery.md")
DEFAULT_DOC_HTML = Path("docs/route1_exhaustive_ancova_gallery.html")
DEFAULT_INDEX = Path("docs/route1_current_reports_browser_index.html")

AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
EFFORT_MEASURES = [
    ("nb_words", "Words"),
    ("nb_morphemes", "Morphemes"),
    ("nb_syllables_cmu_or_pkg", "Syllables: CMU/pkg"),
    ("nb_syllables_pkg", "Syllables: pkg"),
    ("nb_phonemes", "Phonemes"),
]
EFFORT_LABELS = {col: label for col, label in EFFORT_MEASURES}

SOURCES = [
    "real",
    "random",
    "unigram",
    "bigram",
    "trigram",
    "lstm_additive_k3_same_length",
    "lstm_additive_k4_same_length",
    "lstm_additive_k5_same_length",
    "caretaker",
]
CHILD_SOURCES = [source for source in SOURCES if source != "caretaker"]
CONTROL_SOURCES = [source for source in CHILD_SOURCES if source != "real"]
PAIRWISE_SOURCES = [*CONTROL_SOURCES, "caretaker"]
SOURCE_LABELS = {
    "real": "Real child",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
    "lstm_additive_k3_same_length": "LSTM k3",
    "lstm_additive_k4_same_length": "LSTM k4",
    "lstm_additive_k5_same_length": "LSTM k5",
    "caretaker": "Caretaker",
}
SOURCE_ORDER = [SOURCE_LABELS[source] for source in SOURCES]
PAIRWISE_LABEL_ORDER = [SOURCE_LABELS[source] for source in PAIRWISE_SOURCES]
OUTCOME_SPECS = [("sum_bits_k3", "With-context information"), ("context_gain", "Context gain")]

SOURCE_PALETTE = {
    "Real child": "#1f2d30",
    "Random": "#c44536",
    "Unigram": "#7b4f9f",
    "Bigram": "#3b7dd8",
    "Trigram": "#1f9a8a",
    "LSTM k3": "#c78c1f",
    "LSTM k4": "#e07a1f",
    "LSTM k5": "#7a9f2f",
    "Caretaker": "#7f7f7f",
}


@dataclass(frozen=True)
class FigureRecord:
    figure_id: str
    title: str
    path: Path
    section: str
    notes: str = ""


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


def md_table(frame: pd.DataFrame, columns: Sequence[str] | None = None) -> str:
    if frame.empty:
        return "_No rows._"
    view = frame.loc[:, list(columns)].copy() if columns else frame.copy()
    view = view.fillna("").astype(str)
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        values = [str(row[col]).replace("|", "\\|") for col in view.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def age_bin_mid(age_bin: object) -> float:
    text = str(age_bin)
    try:
        low, high = text.split("-", 1)
        return (float(low) + float(high)) / 2
    except ValueError:
        return math.nan


def safe_slug(value: object) -> str:
    text = str(value).strip().lower()
    chars = [char if char.isalnum() else "_" for char in text]
    return "_".join("".join(chars).split("_")).strip("_")


def fdr_bh(values: Iterable[object]) -> list[float]:
    raw = pd.to_numeric(pd.Series(list(values)), errors="coerce")
    adjusted = pd.Series(np.nan, index=raw.index, dtype=float)
    valid = raw.dropna()
    if valid.empty:
        return adjusted.tolist()
    ranked = valid.sort_values()
    n = len(ranked)
    previous = 1.0
    out = {}
    for rank_from_end, (idx, p_value) in enumerate(reversed(list(ranked.items())), start=1):
        rank = n - rank_from_end + 1
        value = min(previous, float(p_value) * n / rank)
        previous = value
        out[idx] = min(value, 1.0)
    adjusted.loc[list(out.keys())] = pd.Series(out)
    return adjusted.tolist()


def canonical_source(frame: pd.DataFrame) -> pd.Series:
    source = frame["target_variant"].astype(str)
    return source.where(source.isin(SOURCES), "")


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna() & weights.gt(0)
    if not mask.any():
        return math.nan
    return float((values[mask] * weights[mask]).sum() / weights[mask].sum())


def aggregate_effort_cells(input_csv: Path, output_dir: Path, *, chunksize: int) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    usecols = [
        "target_variant",
        "role",
        "context_k",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "sum_bits",
        *[col for col, _ in EFFORT_MEASURES],
    ]
    parts: dict[str, list[pd.DataFrame]] = {col: [] for col, _ in EFFORT_MEASURES}
    for chunk_index, chunk in enumerate(pd.read_csv(input_csv, usecols=usecols, chunksize=chunksize), start=1):
        chunk = chunk[chunk["context_k"].isin(["k0", "k3"])].copy()
        chunk["source"] = canonical_source(chunk)
        chunk = chunk[chunk["source"].isin(SOURCES)].copy()
        if chunk.empty:
            continue
        chunk["source_label"] = chunk["source"].map(SOURCE_LABELS)
        for col in ["sum_bits", "age_months", *[effort_col for effort_col, _ in EFFORT_MEASURES]]:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        chunk = chunk.dropna(subset=["sum_bits", "age_months", "age_bin", "child_id", "session_id"])
        for effort_col, effort_label in EFFORT_MEASURES:
            sub = chunk[
                [
                    "source",
                    "source_label",
                    "role",
                    "child_id",
                    "age_bin",
                    "session_id",
                    "context_k",
                    "sum_bits",
                    "age_months",
                    effort_col,
                ]
            ].copy()
            sub = sub.dropna(subset=[effort_col])
            sub = sub[sub[effort_col].gt(0)]
            if sub.empty:
                continue
            sub["effort_col"] = effort_col
            sub["effort_label"] = effort_label
            sub = sub.rename(columns={effort_col: "effort_value"})
            sub["sum_bits_total"] = sub["sum_bits"]
            sub["age_months_total"] = sub["age_months"]
            keys = [
                "effort_col",
                "effort_label",
                "source",
                "source_label",
                "role",
                "child_id",
                "age_bin",
                "session_id",
                "effort_value",
                "context_k",
            ]
            grouped = (
                sub.groupby(keys, observed=True, dropna=False)
                .agg(
                    n=("sum_bits_total", "size"),
                    sum_bits_total=("sum_bits_total", "sum"),
                    age_months_total=("age_months_total", "sum"),
                )
                .reset_index()
            )
            parts[effort_col].append(grouped)
        print(f"[aggregate] processed chunk {chunk_index}", flush=True)

    wide_frames = []
    for effort_col, effort_label in EFFORT_MEASURES:
        if not parts[effort_col]:
            continue
        partial = pd.concat(parts[effort_col], ignore_index=True)
        keys = [
            "effort_col",
            "effort_label",
            "source",
            "source_label",
            "role",
            "child_id",
            "age_bin",
            "session_id",
            "effort_value",
            "context_k",
        ]
        final = (
            partial.groupby(keys, observed=True, dropna=False)
            .agg(
                n=("n", "sum"),
                sum_bits_total=("sum_bits_total", "sum"),
                age_months_total=("age_months_total", "sum"),
            )
            .reset_index()
        )
        final["mean_sum_bits"] = final["sum_bits_total"] / final["n"]
        final["mean_age_months"] = final["age_months_total"] / final["n"]
        index_cols = [col for col in keys if col != "context_k"]
        bits = final.pivot_table(index=index_cols, columns="context_k", values="mean_sum_bits", aggfunc="first").reset_index()
        counts = final.pivot_table(index=index_cols, columns="context_k", values="n", aggfunc="first").reset_index()
        age = final.groupby(index_cols, observed=True, dropna=False)["mean_age_months"].mean().reset_index()
        bits = bits.rename(columns={"k0": "sum_bits_k0", "k3": "sum_bits_k3"})
        counts = counts.rename(columns={"k0": "n_k0", "k3": "n_k3"})
        wide = bits.merge(counts, on=index_cols, how="left").merge(age, on=index_cols, how="left")
        wide["n"] = wide[["n_k0", "n_k3"]].min(axis=1)
        wide["context_gain"] = wide["sum_bits_k0"] - wide["sum_bits_k3"]
        wide["age_mid"] = wide["age_bin"].map(age_bin_mid)
        wide = wide.dropna(subset=["sum_bits_k3", "context_gain", "n"])
        wide = wide[wide["n"].gt(0)].copy()
        wide_frames.append(wide)
        effort_path = output_dir / f"effort_cell_summary_{effort_col}.csv.gz"
        wide.to_csv(effort_path, index=False)
        print(f"[aggregate] wrote {effort_path} ({len(wide):,} rows)", flush=True)
        del partial, final, bits, counts, wide
        gc.collect()

    if not wide_frames:
        raise RuntimeError("No aggregate effort cells were created.")
    combined = pd.concat(wide_frames, ignore_index=True)
    combined.to_csv(output_dir / "effort_cell_summary.csv.gz", index=False)
    return combined


def load_effort_cells(output_dir: Path) -> pd.DataFrame:
    path = output_dir / "effort_cell_summary.csv.gz"
    if not path.exists():
        raise FileNotFoundError(f"Missing aggregate cells: {path}")
    frame = pd.read_csv(path)
    for col in ["effort_value", "sum_bits_k0", "sum_bits_k3", "context_gain", "n", "age_mid"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["effort_value", "sum_bits_k3", "context_gain", "n"])
    frame["source_label"] = pd.Categorical(frame["source_label"], SOURCE_ORDER, ordered=True)
    frame["age_bin"] = pd.Categorical(frame["age_bin"], AGE_BIN_ORDER, ordered=True)
    return frame


def prepare_model_frame(frame: pd.DataFrame, *, effort_col: str, sources: Sequence[str], outcome: str) -> pd.DataFrame:
    sub = frame[frame["effort_col"].eq(effort_col) & frame["source"].isin(sources)].copy()
    sub = sub.dropna(subset=[outcome, "effort_value", "child_id", "age_bin", "source_label", "n"])
    sub["source_label"] = pd.Categorical(sub["source_label"], SOURCE_ORDER, ordered=True)
    sub["age_bin"] = pd.Categorical(sub["age_bin"], AGE_BIN_ORDER, ordered=True)
    effort_mean = weighted_mean(sub["effort_value"], sub["n"])
    effort_sd = math.sqrt(weighted_mean((sub["effort_value"] - effort_mean) ** 2, sub["n"]))
    if not np.isfinite(effort_sd) or effort_sd == 0:
        effort_sd = 1.0
    sub["effort_z"] = (sub["effort_value"] - effort_mean) / effort_sd
    sub.attrs["effort_mean"] = effort_mean
    sub.attrs["effort_sd"] = effort_sd
    return sub


def fit_wls(formula: str, frame: pd.DataFrame):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = smf.wls(formula, data=frame, weights=frame["n"]).fit()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return result.get_robustcov_results(cov_type="cluster", groups=frame["child_id"])
    except Exception:
        return result


def extract_terms(result, metadata: dict[str, object]) -> pd.DataFrame:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            table = result.wald_test_terms(skip_single=False).table
    except Exception as exc:
        return pd.DataFrame([{**metadata, "term": "wald_test_terms_error", "statistic": math.nan, "p_value": math.nan, "error": str(exc)}])
    rows = []
    for term, row in table.iterrows():
        statistic = row.get("statistic", np.nan)
        if isinstance(statistic, (np.ndarray, list, tuple)):
            statistic = np.asarray(statistic).ravel()[0] if np.asarray(statistic).size else np.nan
        rows.append(
            {
                **metadata,
                "term": term,
                "statistic": float(statistic) if pd.notna(statistic) else math.nan,
                "p_value": float(row.get("pvalue", np.nan)) if pd.notna(row.get("pvalue", np.nan)) else math.nan,
                "df_constraint": float(row.get("df_constraint", np.nan)) if pd.notna(row.get("df_constraint", np.nan)) else math.nan,
                "error": "",
            }
        )
    return pd.DataFrame(rows)


def average_predictions(result, frame: pd.DataFrame, *, sources: Sequence[str], age_bins: Sequence[str]) -> pd.DataFrame:
    children = sorted(frame["child_id"].dropna().astype(str).unique())
    source_labels = [SOURCE_LABELS[source] for source in sources]
    rows = []
    for source_label in source_labels:
        for age_bin in age_bins:
            grid = pd.DataFrame(
                {
                    "source_label": source_label,
                    "age_bin": age_bin,
                    "child_id": children,
                    "effort_z": 0.0,
                    "n": 1.0,
                }
            )
            try:
                predicted = result.predict(grid)
            except Exception:
                continue
            rows.append(
                {
                    "source_label": source_label,
                    "age_bin": age_bin,
                    "age_mid": age_bin_mid(age_bin),
                    "adjusted_mean": float(np.mean(predicted)),
                    "children_averaged": len(children),
                }
            )
    return pd.DataFrame(rows)


def fit_ancova_models(cell_frame: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    term_rows = []
    adjusted_rows = []
    contrast_rows = []
    for effort_col, effort_label in EFFORT_MEASURES:
        for outcome, outcome_label in OUTCOME_SPECS:
            real_frame = prepare_model_frame(cell_frame, effort_col=effort_col, sources=["real"], outcome=outcome)
            if len(real_frame) > 20:
                formula = f"{outcome} ~ C(age_bin) + effort_z + C(child_id)"
                result = fit_wls(formula, real_frame)
                meta = {
                    "model_id": "real_age_ancova",
                    "comparison": "Real child age bins",
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "outcome": outcome,
                    "outcome_label": outcome_label,
                    "n_cells": len(real_frame),
                    "n_weighted_rows": int(real_frame["n"].sum()),
                    "formula": formula,
                }
                term_rows.append(extract_terms(result, meta))
                adjusted = average_predictions(result, real_frame, sources=["real"], age_bins=AGE_BIN_ORDER)
                adjusted["model_id"] = "real_age_ancova"
                adjusted["comparison"] = "Real child age bins"
                adjusted["effort_col"] = effort_col
                adjusted["effort_label"] = effort_label
                adjusted["outcome"] = outcome
                adjusted["outcome_label"] = outcome_label
                adjusted_rows.append(adjusted)

            child_frame = prepare_model_frame(cell_frame, effort_col=effort_col, sources=CHILD_SOURCES, outcome=outcome)
            if len(child_frame) > 20:
                formula = f"{outcome} ~ C(source_label) * C(age_bin) + effort_z + C(child_id)"
                result = fit_wls(formula, child_frame)
                meta = {
                    "model_id": "child_source_omnibus",
                    "comparison": "Real vs generated child sources",
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "outcome": outcome,
                    "outcome_label": outcome_label,
                    "n_cells": len(child_frame),
                    "n_weighted_rows": int(child_frame["n"].sum()),
                    "formula": formula,
                }
                term_rows.append(extract_terms(result, meta))
                adjusted = average_predictions(result, child_frame, sources=CHILD_SOURCES, age_bins=AGE_BIN_ORDER)
                adjusted["model_id"] = "child_source_omnibus"
                adjusted["comparison"] = "Real vs generated child sources"
                adjusted["effort_col"] = effort_col
                adjusted["effort_label"] = effort_label
                adjusted["outcome"] = outcome
                adjusted["outcome_label"] = outcome_label
                adjusted_rows.append(adjusted)

            for source in PAIRWISE_SOURCES:
                pair_frame = prepare_model_frame(cell_frame, effort_col=effort_col, sources=["real", source], outcome=outcome)
                if len(pair_frame) <= 20 or pair_frame["source"].nunique() < 2:
                    continue
                formula = f"{outcome} ~ C(source_label) * C(age_bin) + effort_z + C(child_id)"
                result = fit_wls(formula, pair_frame)
                label = f"Real vs {SOURCE_LABELS[source]}"
                meta = {
                    "model_id": "pairwise_source_ancova",
                    "comparison": label,
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "outcome": outcome,
                    "outcome_label": outcome_label,
                    "n_cells": len(pair_frame),
                    "n_weighted_rows": int(pair_frame["n"].sum()),
                    "formula": formula,
                }
                term_rows.append(extract_terms(result, meta))
                adjusted = average_predictions(result, pair_frame, sources=["real", source], age_bins=AGE_BIN_ORDER)
                adjusted["model_id"] = "pairwise_source_ancova"
                adjusted["comparison"] = label
                adjusted["effort_col"] = effort_col
                adjusted["effort_label"] = effort_label
                adjusted["outcome"] = outcome
                adjusted["outcome_label"] = outcome_label
                adjusted_rows.append(adjusted)
                wide = adjusted.pivot(index="age_bin", columns="source_label", values="adjusted_mean").reset_index()
                if "Real child" in wide.columns and SOURCE_LABELS[source] in wide.columns:
                    wide["source"] = source
                    wide["source_label"] = SOURCE_LABELS[source]
                    wide["comparison"] = label
                    wide["effort_col"] = effort_col
                    wide["effort_label"] = effort_label
                    wide["outcome"] = outcome
                    wide["outcome_label"] = outcome_label
                    wide["age_mid"] = wide["age_bin"].map(age_bin_mid)
                    wide["source_minus_real"] = wide[SOURCE_LABELS[source]] - wide["Real child"]
                    contrast_rows.append(
                        wide[
                            [
                                "comparison",
                                "source",
                                "source_label",
                                "effort_col",
                                "effort_label",
                                "outcome",
                                "outcome_label",
                                "age_bin",
                                "age_mid",
                                "source_minus_real",
                                "Real child",
                                SOURCE_LABELS[source],
                            ]
                        ].rename(columns={SOURCE_LABELS[source]: "source_adjusted_mean", "Real child": "real_adjusted_mean"})
                    )
        print(f"[fit] completed {effort_col}", flush=True)

    terms = pd.concat(term_rows, ignore_index=True) if term_rows else pd.DataFrame()
    adjusted = pd.concat(adjusted_rows, ignore_index=True) if adjusted_rows else pd.DataFrame()
    contrasts = pd.concat(contrast_rows, ignore_index=True) if contrast_rows else pd.DataFrame()
    if not terms.empty:
        terms["p_fdr"] = fdr_bh(terms["p_value"])
    terms.to_csv(output_dir / "ancova_term_tests.csv", index=False)
    adjusted.to_csv(output_dir / "adjusted_marginal_means.csv", index=False)
    contrasts.to_csv(output_dir / "source_real_adjusted_contrasts.csv", index=False)
    return terms, adjusted, contrasts


def choose_top_exact_efforts(cell_frame: pd.DataFrame, output_dir: Path, *, n_values: int = 12) -> pd.DataFrame:
    rows = []
    for effort_col, effort_label in EFFORT_MEASURES:
        sub = cell_frame[cell_frame["effort_col"].eq(effort_col) & cell_frame["source"].eq("real")].copy()
        counts = sub.groupby("effort_value", as_index=False)["n"].sum().sort_values("n", ascending=False)
        counts = counts[counts["effort_value"].gt(0)].head(n_values).sort_values("effort_value")
        for _, row in counts.iterrows():
            rows.append(
                {
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "effort_value": int(row["effort_value"]) if float(row["effort_value"]).is_integer() else row["effort_value"],
                    "real_weighted_rows": int(row["n"]),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(output_dir / "top_exact_effort_values.csv", index=False)
    return out


def fit_exact_effort_models(cell_frame: pd.DataFrame, top_values: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    exact_adjusted_rows = []
    exact_gap_rows = []
    for effort_col, effort_label in EFFORT_MEASURES:
        values = top_values[top_values["effort_col"].eq(effort_col)]["effort_value"].tolist()
        if not values:
            continue
        for outcome, outcome_label in OUTCOME_SPECS:
            real = cell_frame[
                cell_frame["effort_col"].eq(effort_col)
                & cell_frame["source"].eq("real")
                & cell_frame["effort_value"].isin(values)
            ].copy()
            if len(real) > 20:
                real["effort_exact"] = real["effort_value"].astype(int).astype(str)
                formula = f"{outcome} ~ C(age_bin) * C(effort_exact) + C(child_id)"
                result = fit_wls(formula, real)
                children = sorted(real["child_id"].dropna().astype(str).unique())
                rows = []
                for age_bin in AGE_BIN_ORDER:
                    for effort_value in values:
                        grid = pd.DataFrame(
                            {
                                "age_bin": age_bin,
                                "effort_exact": str(int(effort_value)),
                                "child_id": children,
                                "n": 1.0,
                            }
                        )
                        try:
                            pred = result.predict(grid)
                        except Exception:
                            continue
                        rows.append(
                            {
                                "model_id": "real_exact_effort_ancova",
                                "effort_col": effort_col,
                                "effort_label": effort_label,
                                "outcome": outcome,
                                "outcome_label": outcome_label,
                                "age_bin": age_bin,
                                "age_mid": age_bin_mid(age_bin),
                                "effort_value": effort_value,
                                "adjusted_mean": float(np.mean(pred)),
                            }
                        )
                exact_adjusted_rows.append(pd.DataFrame(rows))

            for source in PAIRWISE_SOURCES:
                pair = cell_frame[
                    cell_frame["effort_col"].eq(effort_col)
                    & cell_frame["source"].isin(["real", source])
                    & cell_frame["effort_value"].isin(values)
                ].copy()
                if len(pair) <= 20 or pair["source"].nunique() < 2:
                    continue
                pair["effort_exact"] = pair["effort_value"].astype(int).astype(str)
                formula = f"{outcome} ~ C(source_label) * C(age_bin) * C(effort_exact) + C(child_id)"
                result = fit_wls(formula, pair)
                children = sorted(pair["child_id"].dropna().astype(str).unique())
                pred_rows = []
                for age_bin in AGE_BIN_ORDER:
                    for effort_value in values:
                        for source_label in ["Real child", SOURCE_LABELS[source]]:
                            grid = pd.DataFrame(
                                {
                                    "source_label": source_label,
                                    "age_bin": age_bin,
                                    "effort_exact": str(int(effort_value)),
                                    "child_id": children,
                                    "n": 1.0,
                                }
                            )
                            try:
                                pred = result.predict(grid)
                            except Exception:
                                continue
                            pred_rows.append(
                                {
                                    "source_label": source_label,
                                    "age_bin": age_bin,
                                    "age_mid": age_bin_mid(age_bin),
                                    "effort_value": effort_value,
                                    "adjusted_mean": float(np.mean(pred)),
                                }
                            )
                pred = pd.DataFrame(pred_rows)
                if pred.empty:
                    continue
                wide = pred.pivot_table(
                    index=["age_bin", "age_mid", "effort_value"],
                    columns="source_label",
                    values="adjusted_mean",
                    aggfunc="first",
                ).reset_index()
                if "Real child" not in wide.columns or SOURCE_LABELS[source] not in wide.columns:
                    continue
                wide["source"] = source
                wide["source_label"] = SOURCE_LABELS[source]
                wide["effort_col"] = effort_col
                wide["effort_label"] = effort_label
                wide["outcome"] = outcome
                wide["outcome_label"] = outcome_label
                wide["source_minus_real"] = wide[SOURCE_LABELS[source]] - wide["Real child"]
                exact_gap_rows.append(
                    wide[
                        [
                            "source",
                            "source_label",
                            "effort_col",
                            "effort_label",
                            "outcome",
                            "outcome_label",
                            "age_bin",
                            "age_mid",
                            "effort_value",
                            "source_minus_real",
                        ]
                    ]
                )
        print(f"[fit-exact] completed {effort_col}", flush=True)
    exact_adjusted = pd.concat(exact_adjusted_rows, ignore_index=True) if exact_adjusted_rows else pd.DataFrame()
    exact_gaps = pd.concat(exact_gap_rows, ignore_index=True) if exact_gap_rows else pd.DataFrame()
    exact_adjusted.to_csv(output_dir / "exact_effort_adjusted_means.csv", index=False)
    exact_gaps.to_csv(output_dir / "exact_effort_source_real_gaps.csv", index=False)
    return exact_adjusted, exact_gaps


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def facet_effort_axes(ncols: int = 3):
    n = len(EFFORT_MEASURES)
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.2 * ncols, 4.0 * nrows), sharex=True)
    axes = np.asarray(axes).ravel()
    for ax in axes[n:]:
        ax.axis("off")
    return fig, axes[:n]


def plot_real_adjusted(adjusted: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for outcome, outcome_label in OUTCOME_SPECS:
        sub = adjusted[adjusted["model_id"].eq("real_age_ancova") & adjusted["outcome"].eq(outcome)].copy()
        fig, axes = facet_effort_axes()
        for ax, (effort_col, effort_label) in zip(axes, EFFORT_MEASURES):
            line = sub[sub["effort_col"].eq(effort_col)].sort_values("age_mid")
            ax.plot(line["age_bin"], line["adjusted_mean"], marker="o", color="#1f2d30", linewidth=2)
            ax.set_title(effort_label)
            ax.tick_params(axis="x", rotation=35)
            ax.set_ylabel(outcome_label)
            ax.grid(alpha=0.25)
        path = fig_dir / f"real_age_adjusted_{outcome}_by_effort.png"
        fig.suptitle(f"Real children: adjusted age-bin means for {outcome_label}", y=1.02, fontsize=14)
        savefig(path)
        figures.append(FigureRecord(f"real_adjusted_{outcome}", f"Real children adjusted {outcome_label}", path, "Real Child Age"))
    return figures


def plot_source_adjusted(adjusted: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for outcome, outcome_label in OUTCOME_SPECS:
        sub = adjusted[adjusted["model_id"].eq("child_source_omnibus") & adjusted["outcome"].eq(outcome)].copy()
        fig, axes = facet_effort_axes()
        for ax, (effort_col, effort_label) in zip(axes, EFFORT_MEASURES):
            panel = sub[sub["effort_col"].eq(effort_col)].sort_values(["source_label", "age_mid"])
            for source_label in SOURCE_ORDER:
                if source_label == "Caretaker":
                    continue
                line = panel[panel["source_label"].eq(source_label)]
                if line.empty:
                    continue
                ax.plot(
                    line["age_bin"],
                    line["adjusted_mean"],
                    marker="o",
                    linewidth=1.7 if source_label == "Real child" else 1.15,
                    color=SOURCE_PALETTE.get(source_label, "gray"),
                    label=source_label,
                    alpha=1.0 if source_label == "Real child" else 0.82,
                )
            ax.set_title(effort_label)
            ax.tick_params(axis="x", rotation=35)
            ax.set_ylabel(outcome_label)
            ax.grid(alpha=0.25)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.03))
        path = fig_dir / f"child_sources_adjusted_{outcome}_by_effort.png"
        fig.suptitle(f"Real vs generated sources: adjusted {outcome_label}", y=1.02, fontsize=14)
        savefig(path)
        figures.append(FigureRecord(f"child_sources_{outcome}", f"Real vs generated adjusted {outcome_label}", path, "Source Comparisons"))
    return figures


def plot_caretaker_adjusted(adjusted: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for outcome, outcome_label in OUTCOME_SPECS:
        sub = adjusted[
            adjusted["model_id"].eq("pairwise_source_ancova")
            & adjusted["comparison"].eq("Real vs Caretaker")
            & adjusted["outcome"].eq(outcome)
        ].copy()
        if sub.empty:
            continue
        fig, axes = facet_effort_axes()
        for ax, (effort_col, effort_label) in zip(axes, EFFORT_MEASURES):
            panel = sub[sub["effort_col"].eq(effort_col)].sort_values(["source_label", "age_mid"])
            for source_label in ["Real child", "Caretaker"]:
                line = panel[panel["source_label"].eq(source_label)]
                if line.empty:
                    continue
                ax.plot(
                    line["age_bin"],
                    line["adjusted_mean"],
                    marker="o",
                    linewidth=2.0,
                    color=SOURCE_PALETTE.get(source_label, "gray"),
                    label=source_label,
                )
            ax.set_title(effort_label)
            ax.tick_params(axis="x", rotation=35)
            ax.set_ylabel(outcome_label)
            ax.grid(alpha=0.25)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.03))
        path = fig_dir / f"real_caretaker_adjusted_{outcome}_by_effort.png"
        fig.suptitle(f"Real child vs caretaker: adjusted {outcome_label}", y=1.02, fontsize=14)
        savefig(path)
        figures.append(
            FigureRecord(
                f"real_caretaker_{outcome}",
                f"Real child vs caretaker adjusted {outcome_label}",
                path,
                "Caretaker/CDS Comparison",
            )
        )
    return figures


def plot_gap_heatmaps(contrasts: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for outcome, outcome_label in OUTCOME_SPECS:
        sub = contrasts[contrasts["outcome"].eq(outcome)].copy()
        vmax = np.nanquantile(np.abs(sub["source_minus_real"]), 0.95) if not sub.empty else 1
        vmax = max(float(vmax), 1.0)
        fig, axes = facet_effort_axes()
        for ax, (effort_col, effort_label) in zip(axes, EFFORT_MEASURES):
            panel = sub[sub["effort_col"].eq(effort_col)].copy()
            pivot = panel.pivot_table(
                index="source_label",
                columns="age_bin",
                values="source_minus_real",
                aggfunc="mean",
            ).reindex(index=PAIRWISE_LABEL_ORDER, columns=AGE_BIN_ORDER)
            sns.heatmap(pivot, ax=ax, cmap="vlag", center=0, vmin=-vmax, vmax=vmax, cbar=ax is axes[-1], linewidths=0.3)
            ax.set_title(effort_label)
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.tick_params(axis="x", rotation=35)
        path = fig_dir / f"source_minus_real_{outcome}_heatmaps_by_effort.png"
        fig.suptitle(f"Adjusted source-minus-real gaps: {outcome_label}", y=1.02, fontsize=14)
        savefig(path)
        figures.append(FigureRecord(f"gap_heatmap_{outcome}", f"Source-minus-real {outcome_label} heatmaps", path, "Source Comparisons"))
    return figures


def plot_gap_lines(contrasts: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for outcome, outcome_label in OUTCOME_SPECS:
        for effort_col, effort_label in EFFORT_MEASURES:
            sub = contrasts[contrasts["outcome"].eq(outcome) & contrasts["effort_col"].eq(effort_col)].copy()
            if sub.empty:
                continue
            plt.figure(figsize=(10.5, 5.8))
            for source_label in PAIRWISE_LABEL_ORDER:
                line = sub[sub["source_label"].eq(source_label)].sort_values("age_mid")
                if line.empty:
                    continue
                plt.plot(
                    line["age_bin"],
                    line["source_minus_real"],
                    marker="o",
                    linewidth=1.8,
                    label=source_label,
                    color=SOURCE_PALETTE.get(source_label, "gray"),
                )
            plt.axhline(0, color="black", linewidth=1)
            plt.text(
                0.01,
                0.03,
                "0 = real child utterances",
                transform=plt.gca().transAxes,
                fontsize=9,
                color="#333333",
                va="bottom",
            )
            plt.title(f"How far each source is from real child utterances ({outcome_label}; {effort_label} controlled)")
            plt.ylabel("Bits above/below real child mean")
            plt.xlabel("Age bin")
            plt.xticks(rotation=35)
            plt.grid(alpha=0.25)
            plt.legend(ncol=3)
            path = fig_dir / f"{effort_col}_{outcome}_source_minus_real_gap_lines.png"
            savefig(path)
            figures.append(FigureRecord(f"{effort_col}_{outcome}_gap_lines", f"{effort_label} source-minus-real {outcome_label} lines", path, "Source Comparisons"))
    return figures


def plot_term_heatmaps(terms: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    if terms.empty:
        return figures
    wanted = terms[
        terms["term"].astype(str).str.contains("source_label|age_bin", regex=True)
        & ~terms["term"].astype(str).str.contains("child_id", regex=False)
    ].copy()
    wanted["minus_log10_fdr"] = -np.log10(pd.to_numeric(wanted["p_fdr"], errors="coerce").clip(lower=1e-12))
    wanted["test_label"] = wanted["model_id"] + " / " + wanted["outcome_label"] + " / " + wanted["term"].astype(str)
    for model_id in ["real_age_ancova", "child_source_omnibus", "pairwise_source_ancova"]:
        sub = wanted[wanted["model_id"].eq(model_id)].copy()
        if sub.empty:
            continue
        if model_id == "pairwise_source_ancova":
            sub["row_label"] = sub["comparison"] + " / " + sub["outcome_label"] + " / " + sub["term"].astype(str)
        else:
            sub["row_label"] = sub["outcome_label"] + " / " + sub["term"].astype(str)
        pivot = sub.pivot_table(index="row_label", columns="effort_label", values="minus_log10_fdr", aggfunc="max")
        pivot = pivot.reindex(columns=[label for _, label in EFFORT_MEASURES])
        height = max(4.5, 0.35 * len(pivot))
        plt.figure(figsize=(11.5, height))
        sns.heatmap(pivot, cmap="mako", linewidths=0.25, cbar_kws={"label": "-log10(FDR p)"})
        plt.title(f"Term-test strength across effort measures: {model_id}")
        plt.xlabel("")
        plt.ylabel("")
        path = fig_dir / f"{model_id}_term_test_fdr_heatmap.png"
        savefig(path)
        figures.append(FigureRecord(f"{model_id}_term_tests", f"{model_id} term-test heatmap", path, "Model Tests"))
    return figures


def slope_by_group(frame: pd.DataFrame, value_col: str, group_cols: Sequence[str]) -> pd.DataFrame:
    rows = []
    for keys, group in frame.dropna(subset=[value_col, "age_mid"]).groupby(list(group_cols), observed=True, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        if group["age_mid"].nunique() < 2:
            slope = math.nan
        else:
            slope = float(np.polyfit(group["age_mid"], group[value_col], 1)[0] * 6.0)
        rows.append({**dict(zip(group_cols, keys)), "slope_per_6_months": slope})
    return pd.DataFrame(rows)


def plot_exact_figures(exact_adjusted: pd.DataFrame, exact_gaps: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for outcome, outcome_label in OUTCOME_SPECS:
        real = exact_adjusted[exact_adjusted["outcome"].eq(outcome)].copy()
        if not real.empty:
            slopes = slope_by_group(real, "adjusted_mean", ["effort_col", "effort_label", "effort_value"])
            pivot = slopes.pivot_table(index="effort_label", columns="effort_value", values="slope_per_6_months", aggfunc="mean")
            pivot = pivot.reindex(index=[label for _, label in EFFORT_MEASURES])
            vmax = max(float(np.nanquantile(np.abs(pivot.to_numpy()), 0.95)), 0.5)
            plt.figure(figsize=(13.5, 4.8))
            sns.heatmap(pivot, cmap="vlag", center=0, vmin=-vmax, vmax=vmax, linewidths=0.25, cbar_kws={"label": "Adjusted slope per 6 months"})
            plt.title(f"Real children exact-effort age slopes: {outcome_label}")
            plt.xlabel("Exact effort value")
            plt.ylabel("")
            path = fig_dir / f"real_exact_effort_age_slopes_{outcome}.png"
            savefig(path)
            figures.append(FigureRecord(f"real_exact_slopes_{outcome}", f"Real exact-effort {outcome_label} age slopes", path, "Exact Effort"))

        gaps = exact_gaps[exact_gaps["outcome"].eq(outcome)].copy()
        if not gaps.empty:
            slopes = slope_by_group(gaps, "source_minus_real", ["source_label", "effort_col", "effort_label", "effort_value"])
            for effort_col, effort_label in EFFORT_MEASURES:
                panel = slopes[slopes["effort_col"].eq(effort_col)].copy()
                if panel.empty:
                    continue
                pivot = panel.pivot_table(index="source_label", columns="effort_value", values="slope_per_6_months", aggfunc="mean")
                pivot = pivot.reindex(index=PAIRWISE_LABEL_ORDER)
                vmax = max(float(np.nanquantile(np.abs(pivot.to_numpy()), 0.95)), 0.5)
                plt.figure(figsize=(12.5, 5.8))
                sns.heatmap(pivot, cmap="vlag", center=0, vmin=-vmax, vmax=vmax, linewidths=0.25, cbar_kws={"label": "Gap slope per 6 months"})
                plt.title(f"Exact-{effort_label.lower()} source-minus-real developmental gap slopes: {outcome_label}")
                plt.xlabel(f"Exact {effort_label.lower()} value")
                plt.ylabel("")
                path = fig_dir / f"{effort_col}_exact_source_real_gap_slopes_{outcome}.png"
                savefig(path)
                figures.append(FigureRecord(f"{effort_col}_exact_gap_slopes_{outcome}", f"{effort_label} exact-effort source gap slopes for {outcome_label}", path, "Exact Effort"))
    return figures


def plot_all(output_dir: Path, fig_dir: Path) -> list[FigureRecord]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    adjusted = pd.read_csv(output_dir / "adjusted_marginal_means.csv")
    contrasts = pd.read_csv(output_dir / "source_real_adjusted_contrasts.csv")
    terms = pd.read_csv(output_dir / "ancova_term_tests.csv")
    exact_adjusted = pd.read_csv(output_dir / "exact_effort_adjusted_means.csv")
    exact_gaps = pd.read_csv(output_dir / "exact_effort_source_real_gaps.csv")
    figures: list[FigureRecord] = []
    figures.extend(plot_real_adjusted(adjusted, fig_dir))
    figures.extend(plot_source_adjusted(adjusted, fig_dir))
    figures.extend(plot_caretaker_adjusted(adjusted, fig_dir))
    figures.extend(plot_gap_heatmaps(contrasts, fig_dir))
    figures.extend(plot_gap_lines(contrasts, fig_dir))
    figures.extend(plot_term_heatmaps(terms, fig_dir))
    figures.extend(plot_exact_figures(exact_adjusted, exact_gaps, fig_dir))
    manifest = pd.DataFrame([record.__dict__ for record in figures])
    if not manifest.empty:
        manifest["path"] = manifest["path"].map(str)
    manifest.to_csv(output_dir / "figure_manifest.csv", index=False)
    return figures


def relative_to_doc(path: Path, doc_path: Path) -> str:
    return str(Path("..") / path)


def figure_markdown(record: FigureRecord, doc_path: Path) -> str:
    return f"![{record.title}]({relative_to_doc(record.path, doc_path)})"


def line_slope_per_6mo(frame: pd.DataFrame, value_col: str) -> float:
    frame = frame.dropna(subset=["age_mid", value_col]).copy()
    if frame["age_mid"].nunique() < 2:
        return math.nan
    return float(np.polyfit(frame["age_mid"], frame[value_col], 1)[0] * 6.0)


def adjusted_change_summary(adjusted: pd.DataFrame, *, model_id: str, outcome: str, comparison: str | None = None) -> pd.DataFrame:
    sub = adjusted[adjusted["model_id"].eq(model_id) & adjusted["outcome"].eq(outcome)].copy()
    if comparison is not None:
        sub = sub[sub["comparison"].eq(comparison)].copy()
    rows = []
    for (effort_label, source_label), group in sub.groupby(["effort_label", "source_label"], observed=True):
        group = group.sort_values("age_mid")
        if group.empty:
            continue
        rows.append(
            {
                "effort": effort_label,
                "source": source_label,
                "start": float(group.iloc[0]["adjusted_mean"]),
                "end": float(group.iloc[-1]["adjusted_mean"]),
                "delta": float(group.iloc[-1]["adjusted_mean"] - group.iloc[0]["adjusted_mean"]),
                "slope_per_6mo": line_slope_per_6mo(group, "adjusted_mean"),
            }
        )
    return pd.DataFrame(rows)


def exact_slope_summary(exact_adjusted: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (outcome_label, effort_label), group in exact_adjusted.groupby(["outcome_label", "effort_label"], observed=True):
        slopes = []
        for _, exact_group in group.groupby("effort_value", observed=True):
            slopes.append(line_slope_per_6mo(exact_group, "adjusted_mean"))
        values = pd.Series(slopes).dropna()
        if values.empty:
            continue
        rows.append(
            {
                "outcome": outcome_label,
                "effort": effort_label,
                "down": int((values < 0).sum()),
                "up": int((values > 0).sum()),
                "total": int(len(values)),
                "median_slope": float(values.median()),
                "min_slope": float(values.min()),
                "max_slope": float(values.max()),
            }
        )
    return pd.DataFrame(rows)


def key_summaries(output_dir: Path, adjusted: pd.DataFrame, contrasts: pd.DataFrame) -> dict[str, object]:
    exact_adjusted = pd.read_csv(output_dir / "exact_effort_adjusted_means.csv")
    real_bits = adjusted_change_summary(adjusted, model_id="real_age_ancova", outcome="sum_bits_k3")
    real_gain = adjusted_change_summary(adjusted, model_id="real_age_ancova", outcome="context_gain")
    caretaker_bits = adjusted_change_summary(
        adjusted,
        model_id="pairwise_source_ancova",
        outcome="sum_bits_k3",
        comparison="Real vs Caretaker",
    )
    caretaker_gain = adjusted_change_summary(
        adjusted,
        model_id="pairwise_source_ancova",
        outcome="context_gain",
        comparison="Real vs Caretaker",
    )
    exact = exact_slope_summary(exact_adjusted)
    return {
        "real_bits": real_bits,
        "real_gain": real_gain,
        "caretaker_bits": caretaker_bits,
        "caretaker_gain": caretaker_gain,
        "source_gaps": contrasts.copy(),
        "exact": exact,
    }


def range_sentence(frame: pd.DataFrame, source: str | None = "Real child") -> str:
    view = frame.copy()
    if source is not None and "source" in view.columns:
        view = view[view["source"].eq(source)].copy()
    if view.empty:
        return "No summary rows were available."
    return (
        f"Across effort scales, the adjusted start-to-end change ranges from "
        f"{fmt_number(view['delta'].min(), 2)} to {fmt_number(view['delta'].max(), 2)} bits; "
        f"the fitted linear age slope ranges from {fmt_number(view['slope_per_6mo'].min(), 2)} "
        f"to {fmt_number(view['slope_per_6mo'].max(), 2)} bits per 6 months."
    )


def exact_sentence(exact: pd.DataFrame, outcome: str) -> str:
    view = exact[exact["outcome"].eq(outcome)].copy()
    if view.empty:
        return "No exact-effort slope summary was available."
    down = int(view["down"].sum())
    total = int(view["total"].sum())
    return (
        f"Across the top exact effort values and all five effort scales, "
        f"{down}/{total} exact-effort age slopes are downward; median slopes by effort scale range "
        f"from {fmt_number(view['median_slope'].min(), 2)} to {fmt_number(view['median_slope'].max(), 2)} bits per 6 months."
    )


def caregiver_sentence(frame: pd.DataFrame, source: str) -> str:
    view = frame[frame["source"].eq(source)].copy()
    if view.empty:
        return "No caregiver summary rows were available."
    return range_sentence(view, source=None)


def effort_label_from_figure(record: FigureRecord) -> str:
    for effort_col, effort_label in EFFORT_MEASURES:
        if record.figure_id.startswith(f"{effort_col}_"):
            return effort_label
    return "the named effort scale"


def source_gap_change_sentence(contrasts: pd.DataFrame, effort_label: str, outcome: str) -> str:
    view = contrasts[contrasts["effort_label"].eq(effort_label) & contrasts["outcome"].eq(outcome)].copy()
    if view.empty:
        return "No source-gap summary was available for this effort scale."

    def describe_source(source_label: str) -> str | None:
        group = view[view["source_label"].eq(source_label)].sort_values("age_mid")
        if group.empty:
            return None
        start = float(group.iloc[0]["source_minus_real"])
        end = float(group.iloc[-1]["source_minus_real"])
        delta = end - start
        return f"{source_label} changes from {fmt_number(start, 2)} to {fmt_number(end, 2)} bits (delta {fmt_number(delta, 2)})"

    if outcome == "sum_bits_k3":
        parts = [part for part in [describe_source("Random"), describe_source("Trigram")] if part]
        lstm_final = (
            view[view["source_label"].astype(str).str.startswith("LSTM")]
            .sort_values(["age_mid", "source_label"])
            .groupby("source_label", observed=True)
            .tail(1)
        )
        if not lstm_final.empty:
            closest = lstm_final.iloc[(lstm_final["source_minus_real"].abs()).argmin()]
            parts.append(
                f"the closest LSTM at the last age bin is {closest['source_label']} "
                f"with a {fmt_number(closest['source_minus_real'], 2)} bit gap"
            )
        if parts:
            return f"For {effort_label.lower()}, " + "; ".join(parts) + "."

    final = view.sort_values("age_mid").groupby("source_label", observed=True).tail(1)
    if final.empty:
        return f"For {effort_label.lower()}, source-gap rows were present but not enough to summarize."
    strongest = final.iloc[(final["source_minus_real"].abs()).argmax()]
    return (
        f"For {effort_label.lower()}, the largest final absolute context-gain gap is "
        f"{strongest['source_label']} at {fmt_number(strongest['source_minus_real'], 2)} bits."
    )


def plot_explanation(record: FigureRecord, summaries: dict[str, object]) -> list[str]:
    real_bits = summaries["real_bits"]
    real_gain = summaries["real_gain"]
    caretaker_bits = summaries["caretaker_bits"]
    caretaker_gain = summaries["caretaker_gain"]
    source_gaps = summaries["source_gaps"]
    exact = summaries["exact"]

    if record.figure_id == "real_adjusted_sum_bits_k3":
        return [
            "**What is controlled:** Each panel is a separate ANCOVA, `sum_bits_k3 ~ C(age_bin) + effort_z + C(child_id)`. The effort variable is the panel title, centered/scaled within that model; plotted means are at average effort and averaged over child identities.",
            "**How to read it:** Downward lines mean that, at the same effort scale and child-adjusted baseline, older children are less unpredictable in the preceding caretaker context.",
            f"**What it says here:** {range_sentence(real_bits)} This is the ANCOVA version of the Route 1 fixed-effort claim.",
        ]
    if record.figure_id == "real_adjusted_context_gain":
        return [
            "**What is controlled:** Same real-child ANCOVA structure, but the outcome is `context_gain = sum_bits_k0 - sum_bits_k3`.",
            "**How to read it:** Higher values mean the preceding context reduces surprisal more. A downward line means the k0-to-k3 reduction is smaller for older children at matched effort.",
            f"**What it says here:** {range_sentence(real_gain)} This suggests the developmental decrease in k3 bits is not simply because older children receive more helpful local context.",
        ]
    if record.figure_id == "child_sources_sum_bits_k3":
        return [
            "**What is controlled:** Omnibus child-source ANCOVA, `sum_bits_k3 ~ C(source) * C(age_bin) + effort_z + C(child_id)`, fit separately for each effort scale.",
            "**How to read it:** The real-child line is compared with matched generated sources at the same adjusted effort. If controls sit above real children, they are more unpredictable than real utterances under the same context.",
            "**What it says here:** Random is far above real children; n-grams are closer but still generally more surprising; LSTMs are closest but do not remove the real-child developmental pattern. This supports source specificity.",
        ]
    if record.figure_id == "child_sources_context_gain":
        return [
            "**What is controlled:** Same source-by-age ANCOVA, but the outcome is context gain rather than k3 information.",
            "**How to read it:** This separates “the utterance is predictable with context” from “the source benefits from context.”",
            "**What it says here:** The generated controls do not all exploit context like real children. This is useful for arguing that the result is not only a scoring artifact.",
        ]
    if record.figure_id == "real_caretaker_sum_bits_k3":
        return [
            "**What is controlled:** Pairwise ANCOVA for real child vs caretaker speech, `sum_bits_k3 ~ C(source) * C(age_bin) + effort_z + C(child_id)`, fit separately for each effort scale.",
            "**How to read it:** This is not the same as the phonological CDS paper. That paper asks whether caregiver speech becomes more phonologically informative with child age; this plot asks whether caretaker utterances become more Mistral-surprising at the same utterance effort in our Route 1 setup.",
            f"**What it says here:** Caretaker k3 bits show this pattern: {caregiver_sentence(caretaker_bits, 'Caretaker')} This does not reproduce the paper's phone-level CDS-informativity claim; it is a different outcome and a fixed-effort utterance-level contrast.",
        ]
    if record.figure_id == "real_caretaker_context_gain":
        return [
            "**What is controlled:** Same real-vs-caretaker pairwise ANCOVA, with context gain as the outcome.",
            "**How to read it:** This asks whether caretaker speech benefits more or less from local context across the child-age timeline.",
            f"**What it says here:** Caretaker context gain shows this pattern: {caregiver_sentence(caretaker_gain, 'Caretaker')} Treat this as a caregiver contrast, not as a direct replication of the phonological CDS paper.",
        ]
    if record.figure_id.startswith("gap_heatmap_sum_bits_k3"):
        return [
            "**What is controlled:** Pairwise source-vs-real ANCOVAs control effort and child identity before taking source-minus-real adjusted means.",
            "**How to read it:** Red/positive cells mean the source is more unpredictable than real child utterances; blue/negative cells mean less unpredictable.",
            "**What it says here:** The generated baselines are mostly positive, especially random and unigram. This is the broad visual screen for which controls are most different from real children.",
        ]
    if record.figure_id.startswith("gap_heatmap_context_gain"):
        return [
            "**What is controlled:** Pairwise source-vs-real ANCOVAs for context gain.",
            "**How to read it:** Positive cells mean the source gains more from context than real children; negative cells mean less.",
            "**What it says here:** This helps separate high surprisal from poor context use. Some sources are more surprising and also benefit differently from context.",
        ]
    if record.figure_id.endswith("_sum_bits_k3_gap_lines"):
        effort_label = effort_label_from_figure(record)
        return [
            "**What is controlled:** The model first estimates adjusted with-context information for real child utterances and for one comparison source at the same age bin, child-adjusted baseline, and effort scale. It then subtracts the real-child adjusted mean.",
            "**How to read it:** The black zero line is real child utterances. A positive value means the comparison source is that many bits more surprising than real child utterances at the same controlled effort. A negative value means it is less surprising than real child utterances. Upward lines mean the source is moving farther away from real children over development.",
            f"**What it says here:** {source_gap_change_sentence(source_gaps, effort_label, 'sum_bits_k3')} Use these line plots to pick the clearest source-comparison figure.",
        ]
    if record.figure_id.endswith("_context_gain_gap_lines"):
        effort_label = effort_label_from_figure(record)
        return [
            "**What is controlled:** The same source-minus-real subtraction, but for context gain instead of total with-context information.",
            "**How to read it:** Zero is real child utterances. Positive values mean the comparison source gains more from context than real children; negative values mean it gains less from context.",
            f"**What it says here:** {source_gap_change_sentence(source_gaps, effort_label, 'context_gain')} These are secondary to the k3 information gap lines.",
        ]
    if record.figure_id == "real_age_ancova_term_tests":
        return [
            "**What is tested:** The age-bin term in `outcome ~ C(age_bin) + effort_z + C(child_id)`.",
            "**How to read it:** Darker cells mean stronger FDR-adjusted evidence that age bins differ after effort and child identity are controlled.",
            "**What it says here:** This is the table-like statistical confirmation of the real-child adjusted age plots.",
        ]
    if record.figure_id == "child_source_omnibus_term_tests":
        return [
            "**What is tested:** Source, age bin, and source-by-age interaction in the generated-source omnibus ANCOVA.",
            "**How to read it:** Strong source-by-age cells mean the developmental trajectory differs by source, not just by overall source level.",
            "**What it says here:** This is the omnibus support for comparing real children against generated baselines.",
        ]
    if record.figure_id == "pairwise_source_ancova_term_tests":
        return [
            "**What is tested:** Pairwise real-vs-source ANCOVA terms for each source and effort scale.",
            "**How to read it:** Use this as an audit map for which comparisons have strong age/source/source-by-age terms.",
            "**What it says here:** The strongest rows are candidates for supervisor-report figures; the heatmap itself is appendix material.",
        ]
    if record.figure_id == "real_exact_slopes_sum_bits_k3":
        return [
            "**What is controlled:** Exact-effort ANCOVA, `sum_bits_k3 ~ C(age_bin) * C(exact_effort) + C(child_id)`, for the 12 most frequent exact effort values in each effort scale.",
            "**How to read it:** Each cell is an age slope within one exact effort value. Downward cells mean older children are less unpredictable at the exact same effort value.",
            f"**What it says here:** {exact_sentence(exact, 'With-context information')} This is the strongest guard against the result being only MLU.",
        ]
    if record.figure_id == "real_exact_slopes_context_gain":
        return [
            "**What is controlled:** Same exact-effort model, but the outcome is context gain.",
            "**How to read it:** Each cell shows whether context gain changes with age within the exact same effort value.",
            f"**What it says here:** {exact_sentence(exact, 'Context gain')} This is a secondary context-use check.",
        ]
    if "exact_gap_slopes_sum_bits_k3" in record.figure_id:
        return [
            "**What is controlled:** Exact-effort source-vs-real models, so source gaps are compared inside exact effort values rather than at only average effort.",
            "**How to read it:** Positive cells mean the source-real unpredictability gap grows with age at that exact effort value.",
            "**What it says here:** These are candidate appendix figures for showing that source-specific effects are not just effort-distribution artifacts.",
        ]
    if "exact_gap_slopes_context_gain" in record.figure_id:
        return [
            "**What is controlled:** Exact-effort source-vs-real models for context gain.",
            "**How to read it:** These show whether source differences in context benefit grow or shrink within exact effort values.",
            "**What it says here:** Use these only if the supervisor wants the context-gain story; they are not the primary fixed-effort information claim.",
        ]
    return [
        "**What is controlled:** This figure is generated from the saved ANCOVA/adjusted-mean outputs.",
        "**How to read it:** Treat it as a candidate plot for selection, with the full audit tables in Part II.",
    ]


def compact_term_summary(terms: pd.DataFrame) -> pd.DataFrame:
    if terms.empty:
        return terms
    wanted = terms[
        terms["term"].astype(str).str.contains("source_label|age_bin", regex=True)
        & ~terms["term"].astype(str).str.contains("child_id", regex=False)
    ].copy()
    wanted = wanted.sort_values("p_fdr").head(30)
    out = pd.DataFrame(
        {
            "model": wanted["model_id"],
            "comparison": wanted["comparison"],
            "outcome": wanted["outcome_label"],
            "effort": wanted["effort_label"],
            "term": wanted["term"],
            "p": wanted["p_value"].map(fmt_p),
            "FDR p": wanted["p_fdr"].map(fmt_p),
        }
    )
    return out


def strongest_gap_summary(contrasts: pd.DataFrame) -> pd.DataFrame:
    if contrasts.empty:
        return contrasts
    rows = []
    for (source_label, effort_label, outcome_label), group in contrasts.groupby(["source_label", "effort_label", "outcome_label"], observed=True):
        idx = group["source_minus_real"].abs().idxmax()
        row = group.loc[idx]
        rows.append(
            {
                "source": source_label,
                "effort": effort_label,
                "outcome": outcome_label,
                "age bin": row["age_bin"],
                "source-real": fmt_number(row["source_minus_real"], 2),
                "real adj": fmt_number(row["real_adjusted_mean"], 2),
                "source adj": fmt_number(row["source_adjusted_mean"], 2),
            }
        )
    return pd.DataFrame(rows).sort_values(["outcome", "source", "effort"])


def build_report(output_dir: Path, fig_dir: Path, doc_md: Path, doc_html: Path) -> None:
    figures = []
    manifest_path = output_dir / "figure_manifest.csv"
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)
        for _, row in manifest.iterrows():
            figures.append(FigureRecord(row["figure_id"], row["title"], Path(row["path"]), row["section"], row.get("notes", "")))
    terms = pd.read_csv(output_dir / "ancova_term_tests.csv")
    contrasts = pd.read_csv(output_dir / "source_real_adjusted_contrasts.csv")
    adjusted = pd.read_csv(output_dir / "adjusted_marginal_means.csv")
    top_values = pd.read_csv(output_dir / "top_exact_effort_values.csv")
    summaries = key_summaries(output_dir, adjusted, contrasts)
    cell_summary = pd.read_csv(output_dir / "effort_cell_summary.csv.gz", usecols=["effort_col", "source", "n"])
    row_summary = (
        cell_summary.groupby(["effort_col", "source"], as_index=False)["n"].sum()
        .assign(effort_label=lambda frame: frame["effort_col"].map(EFFORT_LABELS), source_label=lambda frame: frame["source"].map(SOURCE_LABELS))
    )
    row_summary = row_summary.pivot_table(index="source_label", columns="effort_label", values="n", aggfunc="sum").reindex(index=SOURCE_ORDER)
    row_summary = row_summary.reset_index()
    for col in row_summary.columns:
        if col != "source_label":
            row_summary[col] = row_summary[col].map(lambda value: f"{int(value):,}" if pd.notna(value) else "")

    lines = [
        "# Route 1 Exhaustive Group-Comparison ANCOVA Gallery",
        "",
        "This is a pre-supervisor selection gallery. It is intentionally built for choosing figures and language for the later supervisor report. The current supervisor-facing report is not modified.",
        "",
        "The central question is the Route 1 question: at the same production effort, do older children produce utterances that are less unpredictable in context? The answer in this gallery is yes for the main real-child adjusted means and mostly yes in exact-effort checks.",
        "",
        "## What The ANCOVA Is Doing",
        "",
        "This report uses ANCOVA-style models because raw ANOVA would mostly ask whether age bins differ in total information, without separating that from the fact that older children produce longer utterances. Here, effort is controlled directly.",
        "",
        "The real-child age-bin model is fit separately for each effort scale:",
        "",
        "```text",
        "sum_bits_k3 ~ C(age_bin) + effort_z + C(child_id)",
        "context_gain ~ C(age_bin) + effort_z + C(child_id)",
        "```",
        "",
        "`effort_z` is one effort measure at a time: words, morphemes, CMU/pkg syllables, package syllables, or phonemes. The plotted adjusted means are predictions at average effort for that scale, averaged over child identities. So these plots are not raw age means.",
        "",
        "The source-comparison models use:",
        "",
        "```text",
        "outcome ~ C(source_label) * C(age_bin) + effort_z + C(child_id)",
        "```",
        "",
        "The exact-effort models use exact effort values instead of only average effort:",
        "",
        "```text",
        "outcome ~ C(age_bin) * C(exact_effort) + C(child_id)",
        "```",
        "",
        "These exact-effort panels are the strongest check against the objection that the result is just MLU or utterance-length growth.",
        "",
        "## Main Reading",
        "",
        f"- **Real child same-effort information:** {range_sentence(summaries['real_bits'])}",
        f"- **Exact-effort support:** {exact_sentence(summaries['exact'], 'With-context information')}",
        f"- **Real child context gain:** {range_sentence(summaries['real_gain'])}",
        "- **Generated controls:** random, n-gram, and LSTM controls are source-specific comparisons. Random is most different; LSTMs are closest; n-grams sit in between.",
        "- **Caretakers:** the caregiver/CDS comparison is not a direct replication of the phonological CDS paper. That paper asks whether caregiver speech becomes more phonologically informative with child age. This report asks whether caretaker utterances are more Mistral-surprising at fixed utterance effort in local conversational context.",
        "",
        "## Relation To The Frequency/Informativity Paper",
        "",
        "The paper excerpt argues that caregiver-directed speech becomes phonologically more informative/less redundant as children age, while phone frequencies are comparatively stable. That is a parent-input result at the phonological-structure level.",
        "",
        "Our current Route 1 result is a child-output result at the utterance-information level: children's own utterances become less unpredictable in context at the same production effort. These can coexist. A plausible developmental story is that input to children may become less redundant as children can process more, while children’s own productions become more conventional and contextually recoverable as they learn the language.",
        "",
        "This report therefore separates the two claims: real-child fixed-effort output trajectories are the main Route 1 evidence; caretaker trajectories are a comparison; and frequency/informativity predictors are being saved for later frequency-control models.",
        "",
        "## Part I: Figure Gallery",
        "",
        "The figures are the main product, but each figure now has a short card explaining the model, how to read it, and why it matters.",
        "",
    ]
    for section in ["Real Child Age", "Source Comparisons", "Caretaker/CDS Comparison", "Model Tests", "Exact Effort"]:
        section_figs = [record for record in figures if record.section == section]
        if not section_figs:
            continue
        lines.extend([f"### {section}", ""])
        if section == "Source Comparisons":
            lines.extend(
                [
                    "**Important reading note:** in every source-minus-real plot, real child utterances are the reference line at `0`. The real utterance value has been subtracted away, so the colored lines are not raw surprisal. They answer: at the same controlled effort, how many bits above or below real child utterances is this control source?",
                    "",
                    "For example, a random line at `+20` means the random utterances are estimated to be 20 bits more surprising than real child utterances in that age bin and effort-controlled model. An LSTM line near `+3` means the LSTM is much closer to real children. A caretaker line below `0` means caretaker utterances are estimated to be less surprising than real child utterances under this same fixed-effort contrast.",
                    "",
                ]
            )
        for record in section_figs:
            lines.extend([f"#### {record.title}", ""])
            for paragraph in plot_explanation(record, summaries):
                lines.extend([paragraph, ""])
            lines.extend([figure_markdown(record, doc_md), ""])

    lines.extend(
        [
            "## Part II: Audit Tables",
            "",
            "The tables are here only to make the figures auditable. The full tables are CSV artifacts; the Markdown shows compact previews.",
            "",
            "### CSV Artifacts",
            "",
            "- `results/route1_exhaustive_ancova_gallery/effort_cell_summary.csv.gz`: aggregate k0/k3/context-gain cells by source, child, session, age bin, and exact effort value.",
            "- `results/route1_exhaustive_ancova_gallery/ancova_term_tests.csv`: Wald term tests for age, source, and source-by-age ANCOVA terms.",
            "- `results/route1_exhaustive_ancova_gallery/adjusted_marginal_means.csv`: adjusted marginal means used in the line figures.",
            "- `results/route1_exhaustive_ancova_gallery/source_real_adjusted_contrasts.csv`: source-minus-real adjusted contrasts by age bin.",
            "- `results/route1_exhaustive_ancova_gallery/top_exact_effort_values.csv`: top 12 exact real-child effort values per effort scale.",
            "- `results/route1_exhaustive_ancova_gallery/exact_effort_adjusted_means.csv`: exact-effort adjusted real-child means.",
            "- `results/route1_exhaustive_ancova_gallery/exact_effort_source_real_gaps.csv`: exact-effort source-minus-real gaps.",
            "- `results/route1_exhaustive_ancova_gallery/figure_manifest.csv`: figure inventory.",
            "- `results/route1_frequency_informativity_predictors/hash_frequency_predictors.csv.gz`: joinable exact-target frequency predictors keyed by `target_text_hash`, created as the safe first frequency-control layer inspired by the phonological CDS paper.",
            "",
            "### Weighted Cell Counts",
            "",
            md_table(row_summary),
            "",
            "### Exact Effort Values Used",
            "",
            md_table(top_values.assign(effort_value=top_values["effort_value"].astype(str), real_weighted_rows=top_values["real_weighted_rows"].map(lambda value: f"{int(value):,}"))),
            "",
            "### Strongest Adjusted Source-Real Gaps",
            "",
            md_table(strongest_gap_summary(contrasts).head(60)),
            "",
            "### Strongest Term Tests",
            "",
            md_table(compact_term_summary(terms)),
            "",
            "## Reading Notes",
            "",
            "- Positive source-minus-real values mean the comparison source is more surprising than real child utterances after the model adjustment.",
            "- The exact-effort heatmaps are the most direct guard against a pure MLU explanation because they avoid mixing different utterance sizes.",
            "- These are candidate-selection figures. The final supervisor report should pick a much smaller subset.",
            "- A separate predictor layer should be used for paper-style frequency controls. The safe first layer now exists as exact-target hash frequency; lexical frequency, phone unigram frequency, and phone-sequence informativity need a safer text-streaming pass because pandas' C parser segfaulted on the large text column in this environment.",
            "",
        ]
    )
    doc_md.parent.mkdir(parents=True, exist_ok=True)
    doc_md.write_text("\n".join(lines), encoding="utf-8")
    render_markdown_file(doc_md, doc_html)
    render_markdown_file(doc_md, doc_md.with_suffix(".embedded.html"), embed_images=True)


def update_index(index_path: Path, report_html: Path, embedded_html: Path) -> None:
    if not index_path.exists():
        return
    text = index_path.read_text(encoding="utf-8")
    additions = [
        (report_html.name, "Exhaustive ANCOVA group-comparison gallery"),
        (embedded_html.name, "Exhaustive ANCOVA group-comparison gallery, embedded images"),
    ]
    insert = ""
    for href, label in additions:
        if href not in text:
            insert += f'\n<li><a href="{href}">{label}</a></li>'
    if not insert:
        return
    text = text.replace("</ul>", insert + "\n</ul>", 1) if "</ul>" in text else text + insert
    index_path.write_text(text, encoding="utf-8")


def run_fit(output_dir: Path) -> None:
    cells = load_effort_cells(output_dir)
    fit_ancova_models(cells, output_dir)
    top_values = choose_top_exact_efforts(cells, output_dir)
    fit_exact_effort_models(cells, top_values, output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--index-html", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--stage", choices=["aggregate", "fit", "plot", "report", "all"], default="all")
    parser.add_argument("--chunksize", type=int, default=500_000)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.stage in {"aggregate", "all"}:
        aggregate_effort_cells(args.input, args.output_dir, chunksize=args.chunksize)
    if args.stage in {"fit", "all"}:
        run_fit(args.output_dir)
    if args.stage in {"plot", "all"}:
        plot_all(args.output_dir, args.fig_dir)
    if args.stage in {"report", "all"}:
        build_report(args.output_dir, args.fig_dir, args.doc_md, args.doc_html)
        update_index(args.index_html, args.doc_html, args.doc_md.with_suffix(".embedded.html"))
        print(args.doc_md)
        print(args.doc_html)
        print(args.doc_md.with_suffix(".embedded.html"))


if __name__ == "__main__":
    main()
