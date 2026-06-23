#!/usr/bin/env python3
"""Build Portelance/Xu-motivated Route 1/2 extension analyses.

This is a sidecar analysis package, not the supervisor-facing report.  It
turns the literature-derived desiderata into reusable predictors, model tables,
and figure-first diagnostics:

* Route 2 effort-as-outcome models.
* Frequency-controlled Route 1 model comparisons.
* Child/caretaker adult-likeness distances.
* Effort-information tradeoff plots.
* Equalized age-bin bootstrap summaries.
* Scrambled-age null checks.

The implementation deliberately writes compact intermediate tables so later
paper/report figures can be regenerated without re-reading the 2.6GB long CSV.
"""

from __future__ import annotations

import argparse
import csv
import gzip
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
    from utterance_count_strategies import normalize_text, word_tokens_regex
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file
    from src.utterance_count_strategies import normalize_text, word_tokens_regex


DEFAULT_INPUT = Path("results/route1_analysis_dataset/route1_scored_utterance_effort_context_entropy_with_lstm_long.csv.gz")
DEFAULT_FREQ = Path("results/route1_frequency_informativity_predictors/hash_frequency_predictors.csv.gz")
DEFAULT_ANCOVA_DIR = Path("results/route1_exhaustive_ancova_gallery")
DEFAULT_OUTPUT_DIR = Path("results/route1_portelance_xu_extension_suite")
DEFAULT_FIG_DIR = Path("figs/route1_portelance_xu_extension_suite")
DEFAULT_DOC_MD = Path("docs/route1_portelance_xu_extension_suite.md")
DEFAULT_DOC_HTML = Path("docs/route1_portelance_xu_extension_suite.html")
DEFAULT_INDEX = Path("docs/route1_current_reports_browser_index.html")

AGE_BIN_ORDER = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
AGE_MIDS = {age: (float(age.split("-")[0]) + float(age.split("-")[1])) / 2 for age in AGE_BIN_ORDER}
EFFORT_MEASURES = [
    ("nb_words", "Words"),
    ("nb_morphemes", "Morphemes"),
    ("nb_syllables_cmu_or_pkg", "Syllables: CMU/pkg"),
    ("nb_syllables_pkg", "Syllables: pkg"),
    ("nb_phonemes", "Phonemes"),
]
EFFORT_LABELS = dict(EFFORT_MEASURES)
SOURCE_LABELS = {"real": "Real child", "caretaker": "Caretaker"}
TRADEOFF_SOURCES = ["Real child", "Random", "Trigram", "LSTM k4", "Caretaker"]
TRADEOFF_SOURCE_MAP = {
    "real": "Real child",
    "random": "Random",
    "trigram": "Trigram",
    "lstm_additive_k4_same_length": "LSTM k4",
    "caretaker": "Caretaker",
}

QUESTION_AUXILIARIES = {
    "am",
    "are",
    "can",
    "could",
    "did",
    "do",
    "does",
    "had",
    "has",
    "have",
    "is",
    "may",
    "might",
    "shall",
    "should",
    "was",
    "were",
    "will",
    "would",
}
QUESTION_WH = {"what", "where", "when", "which", "who", "whom", "whose", "why", "how"}


@dataclass(frozen=True)
class FigureRecord:
    figure_id: str
    title: str
    path: Path
    section: str
    rationale: str


def fmt(value: object, digits: int = 3) -> str:
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


def md_table(frame: pd.DataFrame, columns: Sequence[str] | None = None, max_rows: int | None = None) -> str:
    if frame.empty:
        return "_No rows._"
    view = frame.loc[:, list(columns)].copy() if columns else frame.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    view = view.fillna("").astype(str)
    lines = [
        "| " + " | ".join(view.columns) + " |",
        "| " + " | ".join(["---"] * len(view.columns)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("|", "\\|") for col in view.columns) + " |")
    return "\n".join(lines)


def relative_to_doc(path: Path) -> str:
    return str(Path("..") / path)


def age_mid(age_bin: object) -> float:
    return AGE_MIDS.get(str(age_bin), math.nan)


def word_count(text: object) -> int:
    return len(word_tokens_regex(normalize_text(str(text or ""))))


def last_context_line(text: object) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    return lines[-1] if lines else str(text or "").strip()


def question_type(context_text: object) -> str:
    """Coarse question type for preceding context.

    This is intentionally transparent and conservative.  It is not a syntactic
    parser; it is a control for obvious discourse-form differences.
    """

    line = normalize_text(last_context_line(context_text)).lower().strip()
    tokens = word_tokens_regex(line)
    if not tokens:
        return "empty_context"
    first = tokens[0].lower()
    has_question_mark = "?" in str(context_text)
    if first in QUESTION_WH:
        return f"wh_{first}" if first != "how" else "wh_how"
    if first in QUESTION_AUXILIARIES:
        return "yes_no_question"
    if has_question_mark:
        return "other_question"
    return "statement_or_fragment"


def center_columns(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in columns:
        values = pd.to_numeric(out[col], errors="coerce")
        mean = float(values.mean())
        std = float(values.std(ddof=0))
        if not math.isfinite(std) or std == 0:
            std = 1.0
        out[f"{col}_c"] = (values - mean) / std
    return out


def load_hash_frequency_predictors(freq_csv: Path) -> pd.DataFrame:
    keep = ["target_text_hash", "exact_target_frequency", "exact_target_frequency_bits"]
    freq = pd.read_csv(freq_csv, usecols=["target_text_hash", "reference_scope", *keep[1:]])
    freq = freq[freq["reference_scope"].eq("real_plus_caretaker")].copy()
    return freq.loc[:, keep].drop_duplicates("target_text_hash")


def write_chunked_csv(chunks: Iterable[pd.DataFrame], output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    first = True
    opener = gzip.open if str(output_path).endswith(".gz") else open
    with opener(output_path, "wt", encoding="utf-8", newline="") as handle:
        for chunk in chunks:
            if chunk.empty:
                continue
            chunk.to_csv(handle, index=False, header=first)
            first = False
            rows += len(chunk)
    return rows


def prepare_analysis_rows(input_csv: Path, freq_csv: Path, output_dir: Path, *, chunksize: int) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "portelance_xu_k3_real_caretaker_analysis_rows.csv.gz"
    freq = load_hash_frequency_predictors(freq_csv)
    freq_lookup = {
        str(row.target_text_hash): (row.exact_target_frequency, row.exact_target_frequency_bits)
        for row in freq.itertuples(index=False)
    }
    context_cache: dict[str, tuple[int, str]] = {}
    keep_cols = [
        "target_variant",
        "source_label",
        "role",
        "child_id",
        "session_id",
        "age_months",
        "age_bin",
        "age_mid",
        "target_text_hash",
        "sum_bits",
        "bits_per_word",
        "bits_per_phoneme",
        "nb_words",
        "nb_morphemes",
        "nb_syllables_cmu_or_pkg",
        "nb_syllables_pkg",
        "nb_phonemes",
        "log_nb_words",
        "log_nb_morphemes",
        "log_nb_syllables_cmu_or_pkg",
        "log_nb_syllables_pkg",
        "log_nb_phonemes",
        "context_entropy_join_status",
        "context_entropy_bits",
        "context_next_top1_prob",
        "context_next_argmax_bits",
        "context_effort_words",
        "question_type",
        "exact_target_frequency",
        "exact_target_frequency_bits",
    ]

    def as_float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return math.nan

    def iter_chunks() -> Iterable[pd.DataFrame]:
        opener = gzip.open if str(input_csv).endswith(".gz") else open
        scanned = 0
        kept = 0
        batch: list[dict[str, object]] = []
        with opener(input_csv, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                scanned += 1
                if row.get("context_k") != "k3":
                    if scanned % chunksize == 0:
                        print(f"[prepare] scanned={scanned:,}; kept={kept:,}; contexts={len(context_cache):,}", flush=True)
                    continue
                source = row.get("target_variant", "")
                if source not in SOURCE_LABELS:
                    continue
                age_value = as_float(row.get("age_months"))
                sum_bits = as_float(row.get("sum_bits"))
                context_entropy = as_float(row.get("context_entropy_bits"))
                if not (math.isfinite(age_value) and math.isfinite(sum_bits) and math.isfinite(context_entropy)):
                    continue
                efforts = {effort_col: as_float(row.get(effort_col)) for effort_col, _ in EFFORT_MEASURES}
                if any((not math.isfinite(value)) or value <= 0 for value in efforts.values()):
                    continue
                text_hash = str(row.get("target_text_hash", "")).strip()
                freq_count, freq_bits = freq_lookup.get(text_hash, (math.nan, math.nan))
                context_hash = str(row.get("context_text_hash", "")).strip()
                if context_hash not in context_cache:
                    context_cache[context_hash] = (word_count(row.get("context_text", "")), question_type(row.get("context_text", "")))
                context_effort, q_type = context_cache[context_hash]
                out_row: dict[str, object] = {
                    "target_variant": source,
                    "source_label": SOURCE_LABELS[source],
                    "role": row.get("role", ""),
                    "child_id": row.get("child_id", ""),
                    "session_id": row.get("session_id", ""),
                    "age_months": age_value,
                    "age_bin": row.get("age_bin", ""),
                    "age_mid": age_mid(row.get("age_bin", "")),
                    "target_text_hash": text_hash,
                    "sum_bits": sum_bits,
                    "bits_per_word": as_float(row.get("bits_per_word")),
                    "bits_per_phoneme": as_float(row.get("bits_per_phoneme")),
                    "context_entropy_join_status": row.get("context_entropy_join_status", ""),
                    "context_entropy_bits": context_entropy,
                    "context_next_top1_prob": as_float(row.get("context_next_top1_prob")),
                    "context_next_argmax_bits": as_float(row.get("context_next_argmax_bits")),
                    "context_effort_words": context_effort,
                    "question_type": q_type,
                    "exact_target_frequency": freq_count,
                    "exact_target_frequency_bits": freq_bits,
                }
                for effort_col, _ in EFFORT_MEASURES:
                    out_row[effort_col] = efforts[effort_col]
                    out_row[f"log_{effort_col}"] = math.log1p(efforts[effort_col])
                batch.append(out_row)
                kept += 1
                if len(batch) >= chunksize:
                    print(f"[prepare] scanned={scanned:,}; kept={kept:,}; contexts={len(context_cache):,}", flush=True)
                    yield pd.DataFrame(batch, columns=keep_cols)
                    batch = []
            if batch:
                print(f"[prepare] scanned={scanned:,}; kept={kept:,}; contexts={len(context_cache):,}", flush=True)
                yield pd.DataFrame(batch, columns=keep_cols)

    rows = write_chunked_csv(iter_chunks(), out_path)
    manifest = pd.DataFrame(
        [
            {
                "artifact": str(out_path),
                "rows": rows,
                "description": "K3 real-child and caretaker rows with context, question-type, effort, and exact-frequency predictors.",
            }
        ]
    )
    manifest.to_csv(output_dir / "artifact_manifest.csv", index=False)
    return out_path


def balanced_sample(frame: pd.DataFrame, *, group_cols: Sequence[str], max_per_group: int, seed: int) -> pd.DataFrame:
    parts = []
    for _, group in frame.groupby(list(group_cols), observed=True, dropna=False):
        if len(group) <= max_per_group:
            parts.append(group)
        else:
            parts.append(group.sample(n=max_per_group, random_state=seed))
    return pd.concat(parts, ignore_index=True) if parts else frame.iloc[0:0].copy()


def fit_ols_cluster(frame: pd.DataFrame, formula: str):
    model = smf.ols(formula, data=frame, missing="drop")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return model.fit(cov_type="cluster", cov_kwds={"groups": frame.loc[model.data.row_labels, "child_id"]})


def coefficient_row(result, *, model_id: str, source_label: str, effort_col: str, effort_label: str, outcome: str) -> list[dict[str, object]]:
    rows = []
    for term, coef in result.params.items():
        rows.append(
            {
                "model_id": model_id,
                "source_label": source_label,
                "effort_col": effort_col,
                "effort_label": effort_label,
                "outcome": outcome,
                "term": term,
                "coef": float(coef),
                "se": float(result.bse.get(term, math.nan)),
                "p": float(result.pvalues.get(term, math.nan)),
                "nobs": int(result.nobs),
                "r2": float(getattr(result, "rsquared", math.nan)),
                "aic": float(getattr(result, "aic", math.nan)),
            }
        )
    return rows


def prediction_average(result, grid: pd.DataFrame, child_ids: Sequence[str]) -> np.ndarray:
    parts = []
    for child_id in child_ids:
        g = grid.copy()
        g["child_id"] = child_id
        parts.append(np.asarray(result.predict(g), dtype=float))
    return np.vstack(parts).mean(axis=0)


def fit_route2_effort_models(rows_path: Path, output_dir: Path, *, max_per_group: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(rows_path)
    frame = frame.dropna(subset=["context_entropy_bits", "context_effort_words"]).copy()
    frame = center_columns(frame, ["age_months", "context_entropy_bits", "context_effort_words"])
    model_frame = balanced_sample(frame, group_cols=["source_label", "age_bin"], max_per_group=max_per_group, seed=seed)
    model_frame.to_csv(output_dir / "route2_balanced_model_rows.csv.gz", index=False)

    coef_rows: list[dict[str, object]] = []
    pred_rows: list[dict[str, object]] = []
    for source_label in ["Real child", "Caretaker"]:
        source = model_frame[model_frame["source_label"].eq(source_label)].copy()
        if source.empty:
            continue
        entropy_levels = {
            "low_context_uncertainty": float(source["context_entropy_bits"].quantile(0.10)),
            "median_context_uncertainty": float(source["context_entropy_bits"].quantile(0.50)),
            "high_context_uncertainty": float(source["context_entropy_bits"].quantile(0.90)),
        }
        source = center_columns(source, ["age_months", "context_entropy_bits", "context_effort_words"])
        age_mean = float(source["age_months"].mean())
        age_std = float(source["age_months"].std(ddof=0) or 1)
        ent_mean = float(source["context_entropy_bits"].mean())
        ent_std = float(source["context_entropy_bits"].std(ddof=0) or 1)
        ctx_mean = float(source["context_effort_words"].mean())
        ctx_std = float(source["context_effort_words"].std(ddof=0) or 1)
        modal_question = str(source["question_type"].mode().iloc[0])
        child_ids = sorted(source["child_id"].astype(str).unique())
        for effort_col, effort_label in EFFORT_MEASURES:
            outcome = f"log_{effort_col}"
            formula = (
                f"{outcome} ~ age_months_c + context_entropy_bits_c + "
                "context_effort_words_c + C(question_type) + "
                "age_months_c:context_entropy_bits_c + C(child_id)"
            )
            result = fit_ols_cluster(source, formula)
            coef_rows.extend(
                coefficient_row(
                    result,
                    model_id="route2_effort_outcome",
                    source_label=source_label,
                    effort_col=effort_col,
                    effort_label=effort_label,
                    outcome=outcome,
                )
            )
            base_grid = []
            for age_bin in AGE_BIN_ORDER:
                for level, entropy in entropy_levels.items():
                    age = AGE_MIDS[age_bin]
                    base_grid.append(
                        {
                            "age_bin": age_bin,
                            "age_months": age,
                            "age_months_c": (age - age_mean) / age_std,
                            "context_entropy_bits": entropy,
                            "context_entropy_bits_c": (entropy - ent_mean) / ent_std,
                            "context_effort_words": ctx_mean,
                            "context_effort_words_c": (ctx_mean - ctx_mean) / ctx_std,
                            "question_type": modal_question,
                            "entropy_level": level,
                        }
                    )
            grid = pd.DataFrame(base_grid)
            predicted_log = prediction_average(result, grid, child_ids)
            for row, pred in zip(grid.to_dict("records"), predicted_log):
                pred_rows.append(
                    {
                        "source_label": source_label,
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "age_bin": row["age_bin"],
                        "age_mid": AGE_MIDS[row["age_bin"]],
                        "entropy_level": row["entropy_level"],
                        "predicted_log_effort": float(pred),
                        "predicted_effort": float(np.expm1(pred)),
                    }
                )
    coef = pd.DataFrame(coef_rows)
    pred = pd.DataFrame(pred_rows)
    coef.to_csv(output_dir / "route2_effort_outcome_coefficients.csv", index=False)
    pred.to_csv(output_dir / "route2_effort_outcome_predictions.csv", index=False)
    return coef, pred


def fit_joint_route1_models(rows_path: Path, output_dir: Path, *, max_per_group: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = pd.read_csv(rows_path)
    real = frame[frame["source_label"].eq("Real child")].dropna(
        subset=["sum_bits", "context_entropy_bits", "context_effort_words", "exact_target_frequency_bits"]
    ).copy()
    real = balanced_sample(real, group_cols=["age_bin"], max_per_group=max_per_group, seed=seed)
    real.to_csv(output_dir / "route1_joint_model_balanced_real_rows.csv.gz", index=False)
    real = center_columns(real, ["age_months", "context_entropy_bits", "context_effort_words", "exact_target_frequency_bits"])

    model_specs = [
        ("base_effort_child", "age_months_c + {effort_c} + C(child_id)", "Base fixed-effort child model."),
        (
            "context_controls",
            "age_months_c + {effort_c} + context_entropy_bits_c + context_effort_words_c + C(question_type) + C(child_id)",
            "Adds context uncertainty, context effort, and question type.",
        ),
        (
            "frequency_control",
            "age_months_c + {effort_c} + exact_target_frequency_bits_c + C(child_id)",
            "Adds exact-target recurrence/frequency bits.",
        ),
        (
            "joint_context_frequency",
            "age_months_c + {effort_c} + context_entropy_bits_c + context_effort_words_c + C(question_type) + exact_target_frequency_bits_c + C(child_id)",
            "Joint model with context and frequency controls.",
        ),
        (
            "joint_interactions",
            "age_months_c + {effort_c} + context_entropy_bits_c + context_effort_words_c + C(question_type) + exact_target_frequency_bits_c + age_months_c:context_entropy_bits_c + age_months_c:exact_target_frequency_bits_c + C(child_id)",
            "Tests whether context/frequency effects change over development.",
        ),
    ]
    coef_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for effort_col, effort_label in EFFORT_MEASURES:
        effort_c = f"{effort_col}_c"
        work = center_columns(real, [effort_col])
        for model_id, rhs_template, rationale in model_specs:
            rhs = rhs_template.format(effort_c=effort_c)
            formula = f"sum_bits ~ {rhs}"
            result = fit_ols_cluster(work, formula)
            coef_rows.extend(
                coefficient_row(
                    result,
                    model_id=model_id,
                    source_label="Real child",
                    effort_col=effort_col,
                    effort_label=effort_label,
                    outcome="sum_bits",
                )
            )
            summary_rows.append(
                {
                    "model_id": model_id,
                    "effort_col": effort_col,
                    "effort_label": effort_label,
                    "formula": formula,
                    "rationale": rationale,
                    "nobs": int(result.nobs),
                    "r2": float(result.rsquared),
                    "aic": float(result.aic),
                    "age_coef": float(result.params.get("age_months_c", math.nan)),
                    "age_p": float(result.pvalues.get("age_months_c", math.nan)),
                    "context_entropy_coef": float(result.params.get("context_entropy_bits_c", math.nan)),
                    "frequency_bits_coef": float(result.params.get("exact_target_frequency_bits_c", math.nan)),
                }
            )
    coef = pd.DataFrame(coef_rows)
    summary = pd.DataFrame(summary_rows)
    base_r2 = summary[summary["model_id"].eq("base_effort_child")].loc[:, ["effort_col", "r2"]].rename(columns={"r2": "base_r2"})
    summary = summary.merge(base_r2, on="effort_col", how="left")
    summary["delta_r2_vs_base"] = summary["r2"] - summary["base_r2"]
    coef.to_csv(output_dir / "route1_joint_model_coefficients.csv", index=False)
    summary.to_csv(output_dir / "route1_joint_model_summary.csv", index=False)
    return coef, summary


def build_equalized_bootstrap(
    rows_path: Path,
    output_dir: Path,
    *,
    n_boot: int,
    cap_per_age: int,
    min_age_rows: int,
    seed: int,
) -> pd.DataFrame:
    frame = pd.read_csv(
        rows_path,
        usecols=["source_label", "age_bin", "bits_per_word", "bits_per_phoneme", "exact_target_frequency_bits", "context_entropy_bits"],
    ).dropna()
    rng = np.random.default_rng(seed)
    outcomes = ["bits_per_word", "bits_per_phoneme", "exact_target_frequency_bits", "context_entropy_bits"]
    rows = []
    for source_label, source in frame.groupby("source_label", observed=True):
        sizes = source.groupby("age_bin", observed=True).size().reindex(AGE_BIN_ORDER).dropna()
        sizes = sizes[sizes.ge(min_age_rows)]
        if sizes.empty:
            continue
        n_per_age = int(min(cap_per_age, sizes.min()))
        for b in range(n_boot):
            for age_bin in [age for age in AGE_BIN_ORDER if age in sizes.index]:
                group = source[source["age_bin"].eq(age_bin)]
                if group.empty:
                    continue
                take = group.sample(n=n_per_age, replace=True, random_state=int(rng.integers(0, 2**31 - 1)))
                row = {"source_label": source_label, "age_bin": age_bin, "age_mid": AGE_MIDS[age_bin], "bootstrap": b, "n_per_age": n_per_age}
                for outcome in outcomes:
                    row[outcome] = float(take[outcome].mean())
                rows.append(row)
    boot = pd.DataFrame(rows)
    boot.to_csv(output_dir / "equalized_age_bootstrap_samples.csv.gz", index=False)
    summary_rows = []
    for keys, group in boot.groupby(["source_label", "age_bin", "age_mid", "n_per_age"], observed=True):
        source_label, age_bin, mid, n_per_age = keys
        for outcome in outcomes:
            values = group[outcome].dropna()
            summary_rows.append(
                {
                    "source_label": source_label,
                    "age_bin": age_bin,
                    "age_mid": mid,
                    "n_per_age": n_per_age,
                    "outcome": outcome,
                    "mean": float(values.mean()),
                    "lo": float(values.quantile(0.025)),
                    "hi": float(values.quantile(0.975)),
                }
            )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(output_dir / "equalized_age_bootstrap_summary.csv", index=False)
    return summary


def weighted_partial_age_slope(frame: pd.DataFrame, outcome: str, *, age_values: np.ndarray | None = None) -> float:
    work = frame.dropna(subset=[outcome, "age_mid", "effort_value", "n", "child_id"]).copy()
    if work.empty:
        return math.nan
    age = np.asarray(age_values if age_values is not None else work["age_mid"].to_numpy(), dtype=float)
    y = work[outcome].to_numpy(dtype=float)
    effort = work["effort_value"].to_numpy(dtype=float)
    child_dummies = pd.get_dummies(work["child_id"].astype(str), drop_first=True, dtype=float)
    x = np.column_stack([np.ones(len(work)), age, effort, child_dummies.to_numpy(dtype=float)])
    weights = np.sqrt(np.maximum(work["n"].to_numpy(dtype=float), 1.0))
    coef, *_ = np.linalg.lstsq(x * weights[:, None], y * weights, rcond=None)
    return float(coef[1] * 6.0)


def build_scrambled_age_nulls(ancova_dir: Path, output_dir: Path, *, n_perm: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for effort_col, effort_label in EFFORT_MEASURES:
        path = ancova_dir / f"effort_cell_summary_{effort_col}.csv.gz"
        cells = pd.read_csv(path)
        cells = cells[cells["source_label"].isin(["Real child", "Caretaker"])].copy()
        for source_label, group in cells.groupby("source_label", observed=True):
            for outcome in ["sum_bits_k3", "context_gain"]:
                observed = weighted_partial_age_slope(group, outcome)
                null = []
                age_values = group["age_mid"].to_numpy(dtype=float)
                for _ in range(n_perm):
                    null.append(weighted_partial_age_slope(group, outcome, age_values=rng.permutation(age_values)))
                null_values = np.asarray([v for v in null if math.isfinite(v)], dtype=float)
                if null_values.size:
                    if observed < 0:
                        p_emp = (np.sum(null_values <= observed) + 1) / (null_values.size + 1)
                    else:
                        p_emp = (np.sum(null_values >= observed) + 1) / (null_values.size + 1)
                    lo, hi = np.quantile(null_values, [0.025, 0.975])
                    null_mean = float(null_values.mean())
                else:
                    p_emp, lo, hi, null_mean = math.nan, math.nan, math.nan, math.nan
                rows.append(
                    {
                        "source_label": source_label,
                        "effort_col": effort_col,
                        "effort_label": effort_label,
                        "outcome": outcome,
                        "observed_slope_per_6mo": observed,
                        "null_mean": null_mean,
                        "null_lo": lo,
                        "null_hi": hi,
                        "empirical_p": p_emp,
                        "n_permutations": int(null_values.size),
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(output_dir / "scrambled_age_null_slopes.csv", index=False)
    return out


def build_adult_likeness_tables(ancova_dir: Path, route2_coef: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    contrasts = pd.read_csv(ancova_dir / "source_real_adjusted_contrasts.csv")
    caregiver = contrasts[contrasts["comparison"].eq("Real vs Caretaker")].copy()
    caregiver["abs_caretaker_minus_real"] = caregiver["source_minus_real"].abs()
    caregiver.to_csv(output_dir / "adult_likeness_caretaker_minus_real_adjusted_gaps.csv", index=False)

    wanted = route2_coef[route2_coef["term"].eq("context_entropy_bits_c")].copy()
    wide = wanted.pivot_table(index=["effort_col", "effort_label", "outcome"], columns="source_label", values="coef", aggfunc="first").reset_index()
    if "Real child" in wide.columns and "Caretaker" in wide.columns:
        wide["caretaker_minus_real_context_entropy_coef"] = wide["Caretaker"] - wide["Real child"]
        wide["abs_coef_distance"] = wide["caretaker_minus_real_context_entropy_coef"].abs()
    wide.to_csv(output_dir / "adult_likeness_route2_context_entropy_coefficient_distance.csv", index=False)
    return caregiver, wide


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_route2_predictions(pred: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for effort_col, effort_label in EFFORT_MEASURES:
        sub = pred[pred["effort_col"].eq(effort_col)].copy()
        if sub.empty:
            continue
        plt.figure(figsize=(11.5, 6.2))
        sns.lineplot(
            data=sub,
            x="age_bin",
            y="predicted_effort",
            hue="entropy_level",
            style="source_label",
            markers=True,
            dashes=False,
        )
        plt.xticks(rotation=35)
        plt.ylabel(f"Predicted {effort_label.lower()} effort")
        plt.xlabel("Age bin")
        plt.title(f"Route 2: predicted effort by context uncertainty ({effort_label})")
        plt.grid(alpha=0.25)
        path = fig_dir / f"route2_predicted_{effort_col}_by_context_uncertainty.png"
        savefig(path)
        figures.append(
            FigureRecord(
                f"route2_{effort_col}",
                f"Route 2 predicted {effort_label.lower()} by context uncertainty",
                path,
                "Route 2 Effort Outcome",
                "Tests the Portelance/Xu question of whether children modulate production effort according to how uncertain the preceding context is.",
            )
        )
    return figures


def plot_route2_coefficients(coef: pd.DataFrame, fig_dir: Path) -> FigureRecord:
    sub = coef[coef["term"].isin(["context_entropy_bits_c", "age_months_c:context_entropy_bits_c"])].copy()
    sub["ci_lo"] = sub["coef"] - 1.96 * sub["se"]
    sub["ci_hi"] = sub["coef"] + 1.96 * sub["se"]
    sub["term_label"] = sub["term"].map(
        {
            "context_entropy_bits_c": "Context uncertainty",
            "age_months_c:context_entropy_bits_c": "Age x context uncertainty",
        }
    )
    g = sns.catplot(
        data=sub,
        x="effort_label",
        y="coef",
        hue="source_label",
        col="term_label",
        kind="bar",
        height=4.7,
        aspect=1.35,
        sharey=False,
    )
    for ax, (_, panel) in zip(g.axes.flat, sub.groupby("term_label", sort=False)):
        for container, (_, group) in zip(ax.containers, panel.groupby("source_label", sort=False)):
            pass
        ax.axhline(0, color="black", linewidth=1)
        ax.tick_params(axis="x", rotation=35)
        ax.set_xlabel("")
        ax.grid(alpha=0.2, axis="y")
    g.figure.suptitle("Route 2 model coefficients: effort response to context uncertainty", y=1.04)
    path = fig_dir / "route2_context_uncertainty_coefficients.png"
    savefig(path)
    return FigureRecord(
        "route2_context_coefficients",
        "Route 2 context-uncertainty coefficients",
        path,
        "Route 2 Effort Outcome",
        "A positive context-uncertainty coefficient means higher contextual uncertainty predicts longer/more effortful productions, directly testing effort modulation.",
    )


def plot_joint_models(summary: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    plt.figure(figsize=(11.5, 6.2))
    sns.lineplot(data=summary, x="effort_label", y="age_coef", hue="model_id", marker="o")
    plt.axhline(0, color="black", linewidth=1)
    plt.xticks(rotation=35)
    plt.ylabel("Age coefficient on k3 information")
    plt.xlabel("")
    plt.title("Route 1 age effect after adding context and frequency controls")
    plt.grid(alpha=0.25)
    path = fig_dir / "route1_age_coefficients_with_context_frequency_controls.png"
    savefig(path)
    figures.append(
        FigureRecord(
            "route1_joint_age_coefficients",
            "Route 1 age coefficients with context/frequency controls",
            path,
            "Frequency-Controlled Route 1",
            "Shows whether the fixed-effort developmental effect survives controls motivated by frequency/informativity peer-review concerns.",
        )
    )

    plt.figure(figsize=(11.5, 6.2))
    sns.barplot(data=summary[~summary["model_id"].eq("base_effort_child")], x="effort_label", y="delta_r2_vs_base", hue="model_id")
    plt.xticks(rotation=35)
    plt.ylabel("Delta R2 versus base fixed-effort model")
    plt.xlabel("")
    plt.title("Incremental explanatory value of context and frequency predictors")
    plt.grid(alpha=0.25, axis="y")
    path = fig_dir / "route1_joint_model_delta_r2.png"
    savefig(path)
    figures.append(
        FigureRecord(
            "route1_joint_delta_r2",
            "Joint model incremental fit",
            path,
            "Frequency-Controlled Route 1",
            "Addresses the joint-inference idea: context and frequency should be evaluated together rather than as isolated single predictors.",
        )
    )
    return figures


def plot_adult_likeness(caregiver: pd.DataFrame, coef_distance: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for outcome, label in [("sum_bits_k3", "with-context information"), ("context_gain", "context gain")]:
        sub = caregiver[caregiver["outcome"].eq(outcome)].copy()
        plt.figure(figsize=(11.5, 6.2))
        sns.lineplot(data=sub, x="age_bin", y="source_minus_real", hue="effort_label", marker="o")
        plt.axhline(0, color="black", linewidth=1)
        plt.xticks(rotation=35)
        plt.ylabel("Caretaker adjusted mean - real child adjusted mean")
        plt.xlabel("Age bin")
        plt.title(f"Adult-likeness contrast: caretaker minus real child {label}")
        plt.grid(alpha=0.25)
        path = fig_dir / f"adult_likeness_caretaker_minus_real_{outcome}.png"
        savefig(path)
        figures.append(
            FigureRecord(
                f"adult_likeness_{outcome}",
                f"Caretaker-minus-real {label}",
                path,
                "Adult-Likeness / Caretaker Distance",
                "Makes the adult-likeness claim explicit by tracking the signed distance between child behavior and caretaker behavior.",
            )
        )
    if not coef_distance.empty and "abs_coef_distance" in coef_distance.columns:
        plt.figure(figsize=(10.5, 5.8))
        sns.barplot(data=coef_distance, x="effort_label", y="abs_coef_distance")
        plt.xticks(rotation=35)
        plt.ylabel("|caretaker - real| context-uncertainty coefficient")
        plt.xlabel("")
        plt.title("Adult-likeness in Route 2 effort modulation")
        plt.grid(alpha=0.25, axis="y")
        path = fig_dir / "adult_likeness_route2_context_coefficient_distance.png"
        savefig(path)
        figures.append(
            FigureRecord(
                "adult_likeness_route2_coefficients",
                "Adult-likeness in context-based effort modulation",
                path,
                "Adult-Likeness / Caretaker Distance",
                "Shows whether children's effort response to context uncertainty resembles caretaker/adult response patterns.",
            )
        )
    return figures


def plot_tradeoff(ancova_dir: Path, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    selected_ages = ["006-023", "036-041", "060-065"]
    for effort_col, effort_label in [("nb_words", "Words"), ("nb_phonemes", "Phonemes")]:
        cells = pd.read_csv(ancova_dir / f"effort_cell_summary_{effort_col}.csv.gz")
        cells = cells[cells["source_label"].isin(TRADEOFF_SOURCES) & cells["age_bin"].isin(selected_ages)].copy()
        grouped = (
            cells.groupby(["source_label", "age_bin", "effort_value"], as_index=False)
            .apply(lambda g: pd.Series({"mean_sum_bits_k3": np.average(g["sum_bits_k3"], weights=g["n"]), "rows": g["n"].sum()}))
            .reset_index(drop=True)
        )
        grouped = grouped[grouped["rows"].ge(50)].copy()
        plt.figure(figsize=(12.5, 6.6))
        sns.lineplot(data=grouped, x="effort_value", y="mean_sum_bits_k3", hue="source_label", style="age_bin", marker="o")
        plt.ylabel("Mean k3 information bits")
        plt.xlabel(f"Exact {effort_label.lower()} effort")
        plt.title(f"Effort-information tradeoff space ({effort_label})")
        plt.grid(alpha=0.25)
        path = fig_dir / f"effort_information_tradeoff_{effort_col}.png"
        savefig(path)
        figures.append(
            FigureRecord(
                f"tradeoff_{effort_col}",
                f"Effort-information tradeoff space ({effort_label})",
                path,
                "Efficiency Tradeoff",
                "Connects the project to communicative-efficiency theory by showing the observed effort/information region occupied by real children, controls, LSTMs, and caretakers.",
            )
        )
    return figures


def plot_equalized_bootstrap(summary: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    labels = {
        "bits_per_word": "Bits per word",
        "bits_per_phoneme": "Bits per phoneme",
        "exact_target_frequency_bits": "Exact-target frequency bits",
        "context_entropy_bits": "Context entropy bits",
    }
    for outcome, label in labels.items():
        sub = summary[summary["outcome"].eq(outcome)].copy()
        plt.figure(figsize=(10.8, 5.8))
        for source_label, group in sub.groupby("source_label", observed=True):
            group = group.sort_values("age_mid")
            plt.plot(group["age_bin"], group["mean"], marker="o", label=source_label)
            plt.fill_between(np.arange(len(group)), group["lo"], group["hi"], alpha=0.18)
        plt.xticks(range(len(AGE_BIN_ORDER)), AGE_BIN_ORDER, rotation=35)
        plt.ylabel(label)
        plt.xlabel("Age bin")
        plt.title(f"Equalized age-bin bootstrap: {label}")
        plt.legend()
        plt.grid(alpha=0.25)
        path = fig_dir / f"equalized_bootstrap_{outcome}.png"
        savefig(path)
        figures.append(
            FigureRecord(
                f"bootstrap_{outcome}",
                f"Equalized bootstrap: {label}",
                path,
                "Equalized Sampling",
                "Follows the Pawar/Cychosz-style sampling concern: age trajectories should not be artifacts of unequal data volume across bins.",
            )
        )
    return figures


def plot_scrambled_nulls(nulls: pd.DataFrame, fig_dir: Path) -> list[FigureRecord]:
    figures = []
    for outcome, label in [("sum_bits_k3", "with-context information"), ("context_gain", "context gain")]:
        sub = nulls[nulls["outcome"].eq(outcome)].copy()
        plt.figure(figsize=(11.6, 6.2))
        sns.pointplot(data=sub, x="effort_label", y="observed_slope_per_6mo", hue="source_label", dodge=0.4, markers="o")
        for i, effort_label in enumerate([label for _, label in EFFORT_MEASURES]):
            panel = sub[sub["effort_label"].eq(effort_label)]
            for _, row in panel.iterrows():
                offset = -0.18 if row["source_label"] == "Real child" else 0.18
                plt.vlines(i + offset, row["null_lo"], row["null_hi"], colors="gray", linewidth=3, alpha=0.45)
        plt.axhline(0, color="black", linewidth=1)
        plt.xticks(rotation=35)
        plt.ylabel("Observed age slope per 6 months; gray = scrambled 95% range")
        plt.xlabel("")
        plt.title(f"Scrambled-age null check: {label}")
        plt.grid(alpha=0.25, axis="y")
        path = fig_dir / f"scrambled_age_null_{outcome}.png"
        savefig(path)
        figures.append(
            FigureRecord(
                f"scrambled_{outcome}",
                f"Scrambled-age null check: {label}",
                path,
                "Scrambled-Age Robustness",
                "Peer-review guardrail: developmental slopes should stand apart from age-label scrambling, not merely reflect binning or sampling structure.",
            )
        )
    return figures


def plot_all(output_dir: Path, fig_dir: Path, ancova_dir: Path) -> list[FigureRecord]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    route2_coef = pd.read_csv(output_dir / "route2_effort_outcome_coefficients.csv")
    route2_pred = pd.read_csv(output_dir / "route2_effort_outcome_predictions.csv")
    joint_summary = pd.read_csv(output_dir / "route1_joint_model_summary.csv")
    boot = pd.read_csv(output_dir / "equalized_age_bootstrap_summary.csv")
    nulls = pd.read_csv(output_dir / "scrambled_age_null_slopes.csv")
    caregiver, coef_distance = build_adult_likeness_tables(ancova_dir, route2_coef, output_dir)

    figures: list[FigureRecord] = []
    figures.extend(plot_route2_predictions(route2_pred, fig_dir))
    figures.append(plot_route2_coefficients(route2_coef, fig_dir))
    figures.extend(plot_joint_models(joint_summary, fig_dir))
    figures.extend(plot_adult_likeness(caregiver, coef_distance, fig_dir))
    figures.extend(plot_tradeoff(ancova_dir, fig_dir))
    figures.extend(plot_equalized_bootstrap(boot, fig_dir))
    figures.extend(plot_scrambled_nulls(nulls, fig_dir))
    manifest = pd.DataFrame([record.__dict__ for record in figures])
    if not manifest.empty:
        manifest["path"] = manifest["path"].map(str)
    manifest.to_csv(output_dir / "figure_manifest.csv", index=False)
    return figures


def feature_status_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "feature": "Context uncertainty",
                "status": "implemented",
                "artifact": "context_entropy_bits in analysis rows",
                "peer_review_reason": "Tests whether effort/information effects are actually context-sensitive.",
            },
            {
                "feature": "Context effort",
                "status": "implemented",
                "artifact": "context_effort_words",
                "peer_review_reason": "Controls for the amount of preceding caregiver material.",
            },
            {
                "feature": "Question type",
                "status": "implemented, coarse",
                "artifact": "question_type",
                "peer_review_reason": "Questions can mechanically elicit different child response lengths.",
            },
            {
                "feature": "Exact target recurrence / frequency bits",
                "status": "implemented",
                "artifact": "exact_target_frequency_bits from hash_frequency_predictors.csv.gz",
                "peer_review_reason": "Separates age effects from children/caretakers using more repeated conventional utterances.",
            },
            {
                "feature": "Word-unigram and phone-bigram informativity",
                "status": "implemented in code, not full-run completed here",
                "artifact": "src/build_route1_frequency_informativity_predictors.py --mode text",
                "peer_review_reason": "Closest analogue to Pawar/Cychosz frequency-vs-informativity controls; full run needs a safer long text pass.",
            },
            {
                "feature": "Full response-space entropy",
                "status": "pilot-only, not full scored",
                "artifact": "response_entropy pilot reports",
                "peer_review_reason": "Would directly quantify uncertainty over possible child responses, but full Mila-scale generation is still a separate run.",
            },
        ]
    )


def add_to_index(index_path: Path, doc_html: Path) -> None:
    if not index_path.exists():
        return
    text = index_path.read_text(encoding="utf-8")
    rel = doc_html.name
    embedded = doc_html.with_suffix(".embedded.html").name
    if rel in text:
        return
    insert = (
        f'<li><a href="{rel}">Portelance/Xu extension analysis suite</a></li>\n'
        f'<li><a href="{embedded}">Portelance/Xu extension analysis suite, embedded images</a></li>\n'
    )
    if "</ul>" in text:
        text = text.replace("</ul>", insert + "</ul>", 1)
    else:
        text += "\n<ul>\n" + insert + "</ul>\n"
    index_path.write_text(text, encoding="utf-8")


def build_report(output_dir: Path, fig_dir: Path, doc_md: Path, doc_html: Path, index_html: Path) -> None:
    manifest = pd.read_csv(output_dir / "figure_manifest.csv")
    figures = [
        FigureRecord(row.figure_id, row.title, Path(row.path), row.section, row.rationale)
        for row in manifest.itertuples(index=False)
    ]
    route2_coef = pd.read_csv(output_dir / "route2_effort_outcome_coefficients.csv")
    joint_summary = pd.read_csv(output_dir / "route1_joint_model_summary.csv")
    nulls = pd.read_csv(output_dir / "scrambled_age_null_slopes.csv")
    feature_status = feature_status_table()
    feature_status.to_csv(output_dir / "feature_status_for_peer_review.csv", index=False)
    rows_path = output_dir / "portelance_xu_k3_real_caretaker_analysis_rows.csv.gz"
    if rows_path.exists():
        row_coverage_raw = pd.read_csv(rows_path, usecols=["source_label", "age_bin"])
        row_coverage = (
            row_coverage_raw.groupby(["source_label", "age_bin"], as_index=False)
            .size()
            .pivot_table(index="source_label", columns="age_bin", values="size", aggfunc="sum")
            .reindex(columns=AGE_BIN_ORDER)
            .reset_index()
        )
        for col in row_coverage.columns:
            if col != "source_label":
                row_coverage[col] = row_coverage[col].map(lambda value: f"{int(value):,}" if pd.notna(value) else "")
    else:
        row_coverage = pd.DataFrame()

    route2_context = route2_coef[route2_coef["term"].eq("context_entropy_bits_c")].copy()
    route2_view = route2_context.assign(
        coef=lambda f: f["coef"].map(lambda v: fmt(v, 3)),
        p=lambda f: f["p"].map(fmt_p),
        nobs=lambda f: f["nobs"].map(lambda v: f"{int(v):,}"),
    ).loc[:, ["source_label", "effort_label", "coef", "p", "nobs"]]

    joint_view = joint_summary.assign(
        age_coef=lambda f: f["age_coef"].map(lambda v: fmt(v, 3)),
        age_p=lambda f: f["age_p"].map(fmt_p),
        r2=lambda f: f["r2"].map(lambda v: fmt(v, 3)),
        delta_r2_vs_base=lambda f: f["delta_r2_vs_base"].map(lambda v: fmt(v, 4)),
    ).loc[:, ["model_id", "effort_label", "age_coef", "age_p", "r2", "delta_r2_vs_base"]]

    null_view = nulls.assign(
        observed_slope_per_6mo=lambda f: f["observed_slope_per_6mo"].map(lambda v: fmt(v, 3)),
        null_lo=lambda f: f["null_lo"].map(lambda v: fmt(v, 3)),
        null_hi=lambda f: f["null_hi"].map(lambda v: fmt(v, 3)),
        empirical_p=lambda f: f["empirical_p"].map(fmt_p),
    ).loc[:, ["source_label", "effort_label", "outcome", "observed_slope_per_6mo", "null_lo", "null_hi", "empirical_p"]]

    lines = [
        "# Portelance/Xu Communicative-Efficiency Extension Suite",
        "",
        "This is a sidecar analysis package for choosing paper-ready analyses. It does not modify the current supervisor-facing report.",
        "",
        "The suite translates the Portelance/Xu discussion and the Pawar/Cychosz frequency-informativity template into concrete checks: effort as an outcome, frequency controls, adult-likeness/caretaker distance, equalized sampling, scrambled-age nulls, and effort-information tradeoff plots.",
        "",
        "## Why These Analyses Matter",
        "",
        "- **For Prof. Portelance:** these analyses connect the CHILDES/Mistral work to communicative efficiency as a tradeoff between informativeness, effort, and listener/learner context.",
        "- **For Prof. Xu:** they operationalize the two-route framing: Route 1 asks about information at fixed effort; Route 2 asks whether context predicts effort itself.",
        "- **For peer reviewers:** the suite adds controls for frequency, context effort, question type, unequal age-bin sampling, age-label artifacts, and adult/caretaker comparison baselines.",
        "",
        "## Feature Status",
        "",
        md_table(feature_status),
        "",
        "## Main Status",
        "",
        "- Implemented now: Route 2 effort models, exact-frequency Route 1 controls, adult-likeness plots, effort-information tradeoff plots, equalized bootstraps, scrambled-age nulls.",
        "- Implemented as proxy now: exact target recurrence/frequency bits. This is the stable first frequency-control layer.",
        "- Route 2 effort models are real-child models in this build. The finite k3 context-entropy row extract contains real child rows; caretaker/adult-likeness comparisons are still implemented through the fixed-effort ANCOVA artifacts.",
        "- Equalized bootstrap plots use only age bins with at least 1,000 prepared rows, then sample up to 4,000 rows per included age bin. This avoids letting the sparse `060-065` context-entropy coverage force all bins down to 10 rows.",
        "- Not fully scored now: full response-space entropy and full text/phone informativity predictors. The code path exists for text/phone predictors, but a full safe text pass remains a separate long run.",
        "",
        "### Analysis Row Coverage",
        "",
        md_table(row_coverage),
        "",
        "## Figure Gallery",
        "",
    ]

    for section in [
        "Route 2 Effort Outcome",
        "Frequency-Controlled Route 1",
        "Adult-Likeness / Caretaker Distance",
        "Efficiency Tradeoff",
        "Equalized Sampling",
        "Scrambled-Age Robustness",
    ]:
        section_figs = [fig for fig in figures if fig.section == section]
        if not section_figs:
            continue
        lines.extend([f"### {section}", ""])
        for fig in section_figs:
            lines.extend(
                [
                    f"#### {fig.title}",
                    "",
                    f"**Why this matters:** {fig.rationale}",
                    "",
                    f"![{fig.title}]({relative_to_doc(fig.path)})",
                    "",
                ]
            )

    lines.extend(
        [
            "## Compact Tables",
            "",
            "### Route 2 Context-Uncertainty Coefficients",
            "",
            "Positive coefficients mean that more uncertain contexts predict more production effort. These are log-effort outcomes, so the sign is the key first reading.",
            "",
            md_table(route2_view, max_rows=40),
            "",
            "### Route 1 Joint Model Summary",
            "",
            "The age coefficient is the fixed-effort developmental signal after adding context/frequency controls. `delta_r2_vs_base` shows what each added predictor family contributes over the base effort+child model.",
            "",
            md_table(joint_view, max_rows=60),
            "",
            "### Scrambled-Age Null Summary",
            "",
            "Observed slopes should sit outside or near the edge of scrambled-age null intervals if the developmental effect is not just an age-bin/sampling artifact.",
            "",
            md_table(null_view, max_rows=40),
            "",
            "## Saved Artifacts",
            "",
            "```text",
            str(output_dir / "portelance_xu_k3_real_caretaker_analysis_rows.csv.gz"),
            str(output_dir / "route2_effort_outcome_coefficients.csv"),
            str(output_dir / "route2_effort_outcome_predictions.csv"),
            str(output_dir / "route1_joint_model_coefficients.csv"),
            str(output_dir / "route1_joint_model_summary.csv"),
            str(output_dir / "equalized_age_bootstrap_samples.csv.gz"),
            str(output_dir / "equalized_age_bootstrap_summary.csv"),
            str(output_dir / "scrambled_age_null_slopes.csv"),
            str(output_dir / "adult_likeness_caretaker_minus_real_adjusted_gaps.csv"),
            str(output_dir / "adult_likeness_route2_context_entropy_coefficient_distance.csv"),
            str(output_dir / "feature_status_for_peer_review.csv"),
            str(output_dir / "figure_manifest.csv"),
            "```",
        ]
    )

    doc_md.parent.mkdir(parents=True, exist_ok=True)
    doc_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(doc_md, doc_html, title="Portelance/Xu Extension Suite")
    render_markdown_file(doc_md, doc_html.with_suffix(".embedded.html"), title="Portelance/Xu Extension Suite", embed_images=True)
    add_to_index(index_html, doc_html)


def run_models(
    rows_path: Path,
    output_dir: Path,
    ancova_dir: Path,
    *,
    max_per_group: int,
    n_boot: int,
    bootstrap_cap: int,
    min_bootstrap_age_rows: int,
    n_perm: int,
    seed: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    route2_coef, _ = fit_route2_effort_models(rows_path, output_dir, max_per_group=max_per_group, seed=seed)
    fit_joint_route1_models(rows_path, output_dir, max_per_group=max_per_group, seed=seed)
    build_equalized_bootstrap(
        rows_path,
        output_dir,
        n_boot=n_boot,
        cap_per_age=bootstrap_cap,
        min_age_rows=min_bootstrap_age_rows,
        seed=seed,
    )
    build_scrambled_age_nulls(ancova_dir, output_dir, n_perm=n_perm, seed=seed)
    # Adult-likeness tables are also generated during plotting, but write them
    # here so the model stage is complete as a data product.
    build_adult_likeness_tables(ancova_dir, route2_coef, output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--frequency-predictors", type=Path, default=DEFAULT_FREQ)
    parser.add_argument("--ancova-dir", type=Path, default=DEFAULT_ANCOVA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--doc-html", type=Path, default=DEFAULT_DOC_HTML)
    parser.add_argument("--index-html", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--stage", choices=["prepare", "models", "plot", "report", "all"], default="all")
    parser.add_argument("--chunksize", type=int, default=250_000)
    parser.add_argument("--max-per-source-age", type=int, default=12_000)
    parser.add_argument("--bootstrap-samples", type=int, default=100)
    parser.add_argument("--bootstrap-cap-per-age", type=int, default=4_000)
    parser.add_argument("--bootstrap-min-age-rows", type=int, default=1_000)
    parser.add_argument("--permutations", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260622)
    args = parser.parse_args()

    rows_path = args.output_dir / "portelance_xu_k3_real_caretaker_analysis_rows.csv.gz"
    if args.stage in {"prepare", "all"}:
        rows_path = prepare_analysis_rows(args.input, args.frequency_predictors, args.output_dir, chunksize=args.chunksize)
    if args.stage in {"models", "all"}:
        run_models(
            rows_path,
            args.output_dir,
            args.ancova_dir,
            max_per_group=args.max_per_source_age,
            n_boot=args.bootstrap_samples,
            bootstrap_cap=args.bootstrap_cap_per_age,
            min_bootstrap_age_rows=args.bootstrap_min_age_rows,
            n_perm=args.permutations,
            seed=args.seed,
        )
    if args.stage in {"plot", "all"}:
        plot_all(args.output_dir, args.fig_dir, args.ancova_dir)
    if args.stage in {"report", "all"}:
        build_report(args.output_dir, args.fig_dir, args.doc_md, args.doc_html, args.index_html)


if __name__ == "__main__":
    main()
