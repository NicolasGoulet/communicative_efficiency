#!/usr/bin/env python3
"""Build an audited, cross-tokenizer comparison of the project's three scorers.

The primary outcome is Unicode bits per character on exact paired targets.
Bits per model token are retained only as a tokenizer diagnostic.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable, Sequence

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


MODEL_PARAMETERS = {
    "Mistral-7B": 7_000_000_000,
    "Qwen3-14B": 14_000_000_000,
    "TinyDialogues-135M": 135_000_000,
}
MODEL_COLORS = {
    "Mistral-7B": "#8c564b",
    "Qwen3-14B": "#1f77b4",
    "TinyDialogues-135M": "#2ca02c",
}
CONTEXT_ORDER = ["k0", "k1", "k2", "k3"]
CAREGIVER_CONDITIONS = ["unconditional", "base_context", "matched_child"]
AGE_BINS = [
    ("006-023", 6.0, 24.0),
    ("024-029", 24.0, 30.0),
    ("030-035", 30.0, 36.0),
    ("036-041", 36.0, 42.0),
    ("042-047", 42.0, 48.0),
    ("048-053", 48.0, 54.0),
    ("054-059", 54.0, 60.0),
    ("060-065", 60.0, 66.0),
    ("066plus", 66.0, math.inf),
]


@dataclass(frozen=True)
class ScorerInput:
    label: str
    path: Path

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "_", self.label.lower()).strip("_")


def parse_scorer(value: str) -> ScorerInput:
    if "=" not in value:
        raise argparse.ArgumentTypeError("scorer input must be LABEL=/path")
    label, raw_path = value.split("=", 1)
    label = label.strip()
    if not label:
        raise argparse.ArgumentTypeError("scorer label cannot be empty")
    # Preserve the caller's logical path in provenance.  The filesystem APIs
    # still follow symlinks, while a portable link-farm path remains meaningful
    # after the external drive is mounted somewhere else.
    return ScorerInput(label, Path(raw_path).expanduser())


def portable_provenance_path(path: Path) -> str:
    """Return a stable display identifier without recording a host mount path."""

    project_root = Path(__file__).resolve().parents[1]
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        pass
    for repository in (
        "communicative_efficiency",
        "compute_surprisal_mila",
        "surprisal_computing",
    ):
        if repository in path.parts:
            start = path.parts.index(repository)
            return str(Path(*path.parts[start:]))
    return path.name


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
        fig.savefig(temporary, dpi=220, bbox_inches="tight", facecolor="white")
        os.replace(temporary, path)
    finally:
        plt.close(fig)
        temporary.unlink(missing_ok=True)


def markdown_table(frame: pd.DataFrame, columns: Sequence[str] | None = None) -> str:
    shown = frame if columns is None else frame.loc[:, list(columns)]
    labels = [str(column).replace("_", " ") for column in shown.columns]
    lines = ["| " + " | ".join(labels) + " |", "| " + " | ".join(["---"] * len(labels)) + " |"]
    for row in shown.itertuples(index=False, name=None):
        values = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                values.append("" if not np.isfinite(value) else f"{value:.4f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def html_table(frame: pd.DataFrame, columns: Sequence[str] | None = None) -> str:
    shown = frame if columns is None else frame.loc[:, list(columns)]
    headings = "".join(f"<th>{html.escape(str(column).replace('_', ' '))}</th>" for column in shown.columns)
    rows = []
    for row in shown.itertuples(index=False, name=None):
        cells = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                rendered = "" if not np.isfinite(value) else f"{value:.4f}"
            else:
                rendered = str(value)
            cells.append(f"<td>{html.escape(rendered)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{headings}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def bootstrap_mean(values: np.ndarray, reps: int, seed: int) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = np.sort(values[np.isfinite(values)])
    if len(values) == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    draws = np.empty(reps, dtype=float)
    chunk = 1_000
    for start in range(0, reps, chunk):
        stop = min(reps, start + chunk)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        draws[start:stop] = values[indices].mean(axis=1)
    return tuple(float(value) for value in np.quantile(draws, [0.025, 0.975]))


def age_case(column: str = "age_months") -> str:
    clauses = []
    for label, low, high in AGE_BINS:
        if math.isinf(high):
            clauses.append(f"WHEN {column} >= {low} THEN '{label}'")
        else:
            clauses.append(f"WHEN {column} >= {low} AND {column} < {high} THEN '{label}'")
    return "CASE " + " ".join(clauses) + " ELSE 'outside' END"


def _read_pass_audit(root: Path) -> tuple[Path, dict[str, object]]:
    candidates = [
        root / "reports" / "local_retrieval_audit" / "audit_report.json",
        root / "reports" / "completion" / "audit_report.json",
    ]
    for path in candidates:
        if path.is_file():
            report = json.loads(path.read_text(encoding="utf-8"))
            if report.get("status") == "PASS":
                return path, report
    raise RuntimeError(f"no passing retrieval/completion audit under {root}")


def ingest_child_scorer(
    connection: duckdb.DuckDBPyConnection, scorer: ScorerInput
) -> dict[str, object]:
    root = scorer.path
    if not (root / "WORD_SURPRISAL_COMPLETE").is_file():
        raise RuntimeError(f"missing WORD_SURPRISAL_COMPLETE under {root}")
    if not (root / "LOCAL_RETRIEVAL_AUDIT_PASSED").is_file():
        raise RuntimeError(f"missing LOCAL_RETRIEVAL_AUDIT_PASSED under {root}")
    audit_path, audit = _read_pass_audit(root)
    files = sorted(
        root.glob(
            "outputs/**/chi.surprisal_scoring__real.word_surprisal/utterances.csv.gz"
        )
    )
    if len(files) != 84:
        raise RuntimeError(f"{scorer.label}: expected 84 real utterance files, found {len(files)}")
    view_name = f"raw_child_{scorer.slug}"
    table_name = f"child_{scorer.slug}"
    connection.read_csv([str(path) for path in files], header=True, union_by_name=True).create_view(view_name)
    connection.execute(
        f"""
        CREATE TABLE {table_name} AS
        SELECT
            CAST(target_occurrence_id AS VARCHAR) AS target_occurrence_id,
            CAST(context_window AS VARCHAR) AS context_window,
            CAST(dataset AS VARCHAR) AS dataset,
            CAST(child_key AS VARCHAR) AS child_key,
            CAST(age_months AS DOUBLE) AS age_months,
            CAST(target_text AS VARCHAR) AS target_text,
            CAST(score_status AS VARCHAR) AS score_status,
            CAST(utterance_word_count_cleaned AS BIGINT) AS word_count,
            length(CAST(target_text AS VARCHAR))::BIGINT AS character_count,
            CAST(utterance_sum_bits AS DOUBLE) AS bits,
            CAST(utterance_bits_per_character AS DOUBLE) AS stored_bpc,
            CAST(utterance_bits_per_word AS DOUBLE) AS stored_bpw,
            CAST(utterance_mean_bits_per_token AS DOUBLE) AS bits_per_model_token,
            CAST(utterance_eval_tokens AS BIGINT) AS model_tokens,
            CAST(n_context_tokens_truncated AS BIGINT) AS n_context_tokens_truncated,
            CAST(model_key AS VARCHAR) AS model_key,
            CAST(model_id AS VARCHAR) AS model_id,
            CAST(model_revision AS VARCHAR) AS model_revision,
            CAST(tokenizer_revision AS VARCHAR) AS tokenizer_revision,
            CAST(scoring_code_revision AS VARCHAR) AS scoring_code_revision,
            CAST(schema_version AS VARCHAR) AS schema_version,
            CAST(score_derivation AS VARCHAR) AS score_derivation,
            CAST(prediction_prefix_policy AS VARCHAR) AS prediction_prefix_policy,
            CAST(dtype AS VARCHAR) AS dtype,
            CAST(engine AS VARCHAR) AS engine,
            CAST(max_length AS BIGINT) AS max_length
        FROM {view_name}
        WHERE CAST(mode AS VARCHAR) = 'real'
        """
    )
    connection.execute(f"DROP VIEW {view_name}")
    summary = connection.execute(
        f"""
        SELECT count(*) AS rows,
               count(DISTINCT target_occurrence_id || '|' || context_window) AS unique_rows,
               count(DISTINCT child_key) AS children,
               count(DISTINCT dataset) AS corpora,
               count(DISTINCT context_window) AS contexts,
               count(*) FILTER (WHERE score_status = 'scored') AS scored_rows,
               count(*) FILTER (WHERE word_count > 0 AND character_count > 0) AS positive_denominator_rows,
               count(*) FILTER (WHERE n_context_tokens_truncated > 0) AS truncated_context_rows,
               max(n_context_tokens_truncated) AS max_context_tokens_truncated,
               max(abs(bits / character_count - stored_bpc)) FILTER (WHERE score_status = 'scored' AND character_count > 0) AS max_bpc_reconstruction_error,
               max(abs(bits / word_count - stored_bpw)) FILTER (WHERE score_status = 'scored' AND word_count > 0) AS max_bpw_reconstruction_error,
               any_value(model_key), any_value(model_id), any_value(model_revision),
               any_value(tokenizer_revision), any_value(scoring_code_revision),
               any_value(schema_version), any_value(score_derivation),
               any_value(prediction_prefix_policy), any_value(dtype),
               any_value(engine), any_value(max_length)
        FROM {table_name}
        """
    ).fetchone()
    if summary[0] != summary[1] or summary[2:5] != (21, 3, 4):
        raise RuntimeError(f"{scorer.label}: invalid real-target coverage {summary[:5]}")
    return {
        "domain": "child_utterance",
        "scorer": scorer.label,
        "root": str(root),
        "audit_path": str(audit_path),
        "audit_sha256": sha256_file(audit_path),
        "audit_status": audit.get("status"),
        "files": len(files),
        "compressed_bytes": sum(path.stat().st_size for path in files),
        "rows": summary[0],
        "unique_rows": summary[1],
        "children": summary[2],
        "corpora": summary[3],
        "contexts": summary[4],
        "scored_rows": summary[5],
        "positive_denominator_rows": summary[6],
        "truncated_context_rows": summary[7],
        "max_context_tokens_truncated": summary[8],
        "max_bpc_reconstruction_error": summary[9],
        "max_bpw_reconstruction_error": summary[10],
        "model_key": summary[11],
        "model_id": summary[12],
        "model_revision": summary[13],
        "tokenizer_revision": summary[14],
        "scoring_code_revision": summary[15],
        "schema_version": summary[16],
        "score_derivation": summary[17],
        "prediction_prefix_policy": summary[18],
        "dtype": summary[19],
        "engine": summary[20],
        "max_length": summary[21],
    }


def ingest_caregiver_scorer(
    connection: duckdb.DuckDBPyConnection, scorer: ScorerInput
) -> dict[str, object]:
    path = scorer.path
    if not path.is_file():
        raise RuntimeError(f"missing caregiver scorer table: {path}")
    audit_path = path.parent / "dataset_audit.json"
    if not audit_path.is_file():
        raise RuntimeError(f"missing caregiver dataset audit: {audit_path}")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise RuntimeError(f"caregiver dataset audit is not PASS: {audit_path}")
    file_sha256 = sha256_file(path)
    view_name = f"raw_caregiver_{scorer.slug}"
    table_name = f"caregiver_{scorer.slug}"
    connection.read_csv(str(path), header=True, union_by_name=True).create_view(view_name)
    connection.execute(
        f"""
        CREATE TABLE {table_name} AS
        SELECT
            CAST(response_pair_id AS VARCHAR) AS response_pair_id,
            CAST(dataset AS VARCHAR) AS dataset,
            CAST(child_key AS VARCHAR) AS child_key,
            CAST(sample_group AS VARCHAR) AS sample_group,
            CAST(age_months AS DOUBLE) AS age_months,
            CAST(target_text_sha256 AS VARCHAR) AS target_text_sha256,
            CAST(response_word_count AS BIGINT) AS word_count,
            CAST(response_character_count AS BIGINT) AS character_count,
            CAST(primary_eligible AS BOOLEAN) AS primary_eligible,
            CAST(unconditional_status AS VARCHAR) AS unconditional_status,
            CAST(unconditional_bits AS DOUBLE) AS unconditional_bits,
            CAST(base_context_status AS VARCHAR) AS base_context_status,
            CAST(base_context_bits AS DOUBLE) AS base_context_bits,
            CAST(matched_child_status AS VARCHAR) AS matched_child_status,
            CAST(matched_child_bits AS DOUBLE) AS matched_child_bits,
            CAST(scorer_key AS VARCHAR) AS scorer_key
        FROM {view_name}
        """
    )
    connection.execute(f"DROP VIEW {view_name}")
    summary = connection.execute(
        f"""
        SELECT count(*), count(DISTINCT response_pair_id), count(DISTINCT child_key),
               count(DISTINCT dataset), count(*) FILTER (WHERE primary_eligible),
               any_value(scorer_key)
        FROM {table_name}
        """
    ).fetchone()
    if summary[0] != summary[1] or summary[4] != 413_084:
        raise RuntimeError(f"{scorer.label}: invalid caregiver coverage {summary[:5]}")
    matching_audits = [
        item
        for item in audit.get("scorers", [])
        if item.get("scorer_key") == summary[5]
        and item.get("output_sha256") == file_sha256
        and item.get("status") == "PASS"
        and item.get("rows") == summary[0]
        and item.get("primary_rows") == summary[4]
    ]
    if len(matching_audits) != 1:
        raise RuntimeError(
            f"{scorer.label}: file is not uniquely bound to its PASS dataset audit"
        )
    return {
        "domain": "caregiver_response",
        "scorer": scorer.label,
        "path": str(path),
        "file_sha256": file_sha256,
        "audit_path": str(audit_path),
        "audit_sha256": sha256_file(audit_path),
        "audit_status": audit.get("status"),
        "compressed_bytes": path.stat().st_size,
        "rows": summary[0],
        "unique_rows": summary[1],
        "children": summary[2],
        "corpora": summary[3],
        "primary_rows": summary[4],
        "model_key": summary[5],
    }


def build_paired_tables(
    connection: duckdb.DuckDBPyConnection,
    child_scorers: Sequence[ScorerInput],
    caregiver_scorers: Sequence[ScorerInput],
) -> dict[str, object]:
    base = child_scorers[0]
    joins = []
    selections = [
        "b.target_occurrence_id", "b.context_window", "b.dataset", "b.child_key",
        "b.age_months", "b.word_count", "b.character_count",
    ]
    predicates = [
        "b.score_status = 'scored'", "b.word_count > 0", "b.character_count > 0",
        "isfinite(b.bits)", "isfinite(b.stored_bpc)", "isfinite(b.stored_bpw)",
    ]
    for index, scorer in enumerate(child_scorers):
        alias = "b" if index == 0 else f"s{index}"
        if index > 0:
            joins.append(
                f"INNER JOIN child_{scorer.slug} {alias} USING (target_occurrence_id, context_window)"
            )
            predicates.extend(
                [
                    f"{alias}.score_status = 'scored'",
                    f"{alias}.dataset = b.dataset",
                    f"{alias}.child_key = b.child_key",
                    f"{alias}.target_text = b.target_text",
                    f"{alias}.word_count = b.word_count",
                    f"{alias}.character_count = b.character_count",
                    f"isfinite({alias}.bits)",
                    f"isfinite({alias}.stored_bpc)",
                    f"isfinite({alias}.stored_bpw)",
                ]
            )
        selections.extend(
            [
                f"{alias}.bits AS {scorer.slug}_bits",
                f"{alias}.stored_bpc AS {scorer.slug}_bpc",
                f"{alias}.stored_bpw AS {scorer.slug}_bpw",
                f"{alias}.bits_per_model_token AS {scorer.slug}_bpt",
                f"{alias}.model_tokens AS {scorer.slug}_tokens",
            ]
        )
    connection.execute(
        f"CREATE TABLE paired_child AS SELECT {', '.join(selections)} FROM child_{base.slug} b {' '.join(joins)} WHERE {' AND '.join(predicates)} ORDER BY b.target_occurrence_id, b.context_window"
    )

    if caregiver_scorers:
        base = caregiver_scorers[0]
        joins = []
        selections = [
            "b.response_pair_id", "b.dataset", "b.child_key", "b.sample_group",
            "b.age_months", "b.word_count", "b.character_count",
        ]
        predicates = ["b.primary_eligible", "b.word_count > 0", "b.character_count > 0"]
        for index, scorer in enumerate(caregiver_scorers):
            alias = "b" if index == 0 else f"s{index}"
            if index > 0:
                joins.append(f"INNER JOIN caregiver_{scorer.slug} {alias} USING (response_pair_id)")
                predicates.extend(
                    [
                        f"{alias}.primary_eligible",
                        f"{alias}.dataset = b.dataset",
                        f"{alias}.child_key = b.child_key",
                        f"{alias}.target_text_sha256 = b.target_text_sha256",
                        f"{alias}.word_count = b.word_count",
                        f"{alias}.character_count = b.character_count",
                    ]
                )
            for condition in CAREGIVER_CONDITIONS:
                predicates.extend(
                    [
                        f"{alias}.{condition}_status = 'scored'",
                        f"isfinite({alias}.{condition}_bits)",
                    ]
                )
                selections.append(f"{alias}.{condition}_bits AS {scorer.slug}_{condition}_bits")
        connection.execute(
            f"CREATE TABLE paired_caregiver AS SELECT {', '.join(selections)} FROM caregiver_{base.slug} b {' '.join(joins)} WHERE {' AND '.join(predicates)} ORDER BY b.response_pair_id"
        )

    child_counts = connection.execute(
        "SELECT count(*), count(DISTINCT target_occurrence_id), count(DISTINCT child_key), count(DISTINCT dataset), count(DISTINCT context_window), bit_xor(hash(target_occurrence_id || '|' || context_window)) FROM paired_child"
    ).fetchone()
    result = {
        "child_rows": child_counts[0],
        "child_targets": child_counts[1],
        "child_children": child_counts[2],
        "child_corpora": child_counts[3],
        "child_contexts": child_counts[4],
        "child_identity_hash_xor": str(child_counts[5]),
    }
    if caregiver_scorers:
        caregiver_counts = connection.execute(
            "SELECT count(*), count(DISTINCT response_pair_id), count(DISTINCT child_key), count(DISTINCT dataset), bit_xor(hash(response_pair_id)) FROM paired_caregiver"
        ).fetchone()
        result.update(
            caregiver_rows=caregiver_counts[0],
            caregiver_pairs=caregiver_counts[1],
            caregiver_children=caregiver_counts[2],
            caregiver_corpora=caregiver_counts[3],
            caregiver_identity_hash_xor=str(caregiver_counts[4]),
        )
    return result


def _union_child_summary_sql(scorers: Sequence[ScorerInput]) -> str:
    queries = []
    for scorer in scorers:
        queries.append(
            f"""
            SELECT 'child_utterance' AS domain, '{scorer.label}' AS model,
                   context_window AS condition, dataset, child_key,
                   count(*) AS n_items, sum({scorer.slug}_bits) AS total_bits,
                   sum(character_count) AS total_characters, sum(word_count) AS total_words,
                   sum({scorer.slug}_tokens) AS total_model_tokens,
                   sum({scorer.slug}_bits) / sum(character_count) AS micro_bpc,
                   sum({scorer.slug}_bits) / sum(word_count) AS micro_bpw,
                   sum({scorer.slug}_bits) / sum({scorer.slug}_tokens) AS micro_bpt,
                   sum({scorer.slug}_tokens)::DOUBLE / sum(word_count) AS model_tokens_per_word,
                   avg({scorer.slug}_bpc) AS macro_bpc,
                   median({scorer.slug}_bpc) AS median_bpc
            FROM paired_child GROUP BY context_window, dataset, child_key
            """
        )
    return " UNION ALL ".join(queries)


def _union_caregiver_summary_sql(scorers: Sequence[ScorerInput]) -> str:
    queries = []
    for scorer in scorers:
        for condition in CAREGIVER_CONDITIONS:
            bits = f"{scorer.slug}_{condition}_bits"
            queries.append(
                f"""
                SELECT 'caregiver_response' AS domain, '{scorer.label}' AS model,
                       '{condition}' AS condition, dataset, child_key,
                       count(*) AS n_items, sum({bits}) AS total_bits,
                       sum(character_count) AS total_characters, sum(word_count) AS total_words,
                       NULL::DOUBLE AS total_model_tokens,
                       sum({bits}) / sum(character_count) AS micro_bpc,
                       sum({bits}) / sum(word_count) AS micro_bpw,
                       NULL::DOUBLE AS micro_bpt, NULL::DOUBLE AS model_tokens_per_word,
                       avg({bits} / character_count) AS macro_bpc,
                       median({bits} / character_count) AS median_bpc
                FROM paired_caregiver GROUP BY dataset, child_key
                """
            )
    return " UNION ALL ".join(queries)


def build_child_level_summaries(
    connection: duckdb.DuckDBPyConnection,
    child_scorers: Sequence[ScorerInput],
    caregiver_scorers: Sequence[ScorerInput],
) -> pd.DataFrame:
    sql = _union_child_summary_sql(child_scorers)
    if caregiver_scorers:
        sql += " UNION ALL " + _union_caregiver_summary_sql(caregiver_scorers)
    return connection.execute(sql).fetchdf().sort_values(
        ["domain", "condition", "model", "dataset", "child_key"],
        ignore_index=True,
    )


def summarize_overall(child_level: pd.DataFrame, reps: int, seed: int) -> pd.DataFrame:
    rows = []
    for index, ((domain, condition, model), frame) in enumerate(
        child_level.groupby(["domain", "condition", "model"], sort=True)
    ):
        low, high = bootstrap_mean(frame["micro_bpc"].to_numpy(), reps, seed + index)
        rows.append(
            {
                "domain": domain,
                "condition": condition,
                "model": model,
                "parameters": MODEL_PARAMETERS.get(model, math.nan),
                "n_items": int(frame["n_items"].sum()),
                "n_children": len(frame),
                "occurrence_weighted_bpc": frame["total_bits"].sum() / frame["total_characters"].sum(),
                "child_balanced_bpc": frame["micro_bpc"].mean(),
                "child_bootstrap_ci_low": low,
                "child_bootstrap_ci_high": high,
                "character_perplexity": 2 ** frame["micro_bpc"].mean(),
                "occurrence_weighted_bpw": frame["total_bits"].sum() / frame["total_words"].sum(),
                "child_balanced_bpw": frame["micro_bpw"].mean(),
                "child_balanced_bpt_diagnostic": frame["micro_bpt"].mean(),
                "model_tokens_per_word": frame["model_tokens_per_word"].mean(),
                "macro_utterance_bpc": np.average(frame["macro_bpc"], weights=frame["n_items"]),
            }
        )
    output = pd.DataFrame(rows)
    output["bpc_rank"] = output.groupby(["domain", "condition"])["child_balanced_bpc"].rank(method="min")
    return output.sort_values(["domain", "condition", "bpc_rank"]).reset_index(drop=True)


def build_pairwise(
    connection: duckdb.DuckDBPyConnection,
    child_level: pd.DataFrame,
    child_scorers: Sequence[ScorerInput],
    caregiver_scorers: Sequence[ScorerInput],
    reps: int,
    seed: int,
) -> pd.DataFrame:
    rows = []
    scorer_map = {scorer.label: scorer for scorer in child_scorers}
    caregiver_map = {scorer.label: scorer for scorer in caregiver_scorers}
    model_order = [scorer.label for scorer in child_scorers]
    comparison_index = 0
    for domain, scorers, table_name, conditions in (
        ("child_utterance", scorer_map, "paired_child", CONTEXT_ORDER),
        ("caregiver_response", caregiver_map, "paired_caregiver", CAREGIVER_CONDITIONS),
    ):
        if not scorers:
            continue
        for condition in conditions:
            subset = child_level[(child_level.domain == domain) & (child_level.condition == condition)]
            for reference, candidate in combinations(model_order, 2):
                left = subset[subset.model == reference][["child_key", "dataset", "micro_bpc"]].rename(columns={"micro_bpc": "reference_bpc"})
                right = subset[subset.model == candidate][["child_key", "dataset", "micro_bpc"]].rename(columns={"micro_bpc": "candidate_bpc"})
                paired = left.merge(right, on=["child_key", "dataset"], validate="one_to_one")
                paired["difference"] = paired.candidate_bpc - paired.reference_bpc
                low, high = bootstrap_mean(paired.difference.to_numpy(), reps, seed + comparison_index)
                comparison_index += 1
                reference_slug = scorers[reference].slug
                candidate_slug = scorers[candidate].slug
                if domain == "child_utterance":
                    reference_bits = f"{reference_slug}_bits"
                    candidate_bits = f"{candidate_slug}_bits"
                    where = f"context_window = '{condition}'"
                else:
                    reference_bits = f"{reference_slug}_{condition}_bits"
                    candidate_bits = f"{candidate_slug}_{condition}_bits"
                    where = "TRUE"
                item = connection.execute(
                    f"""
                    SELECT count(*),
                           (sum({candidate_bits}) - sum({reference_bits})) / sum(character_count),
                           median(({candidate_bits} - {reference_bits}) / character_count),
                           avg(CASE WHEN {candidate_bits} < {reference_bits} THEN 1.0 ELSE 0.0 END),
                           avg(CASE WHEN {candidate_bits} = {reference_bits} THEN 1.0 ELSE 0.0 END),
                           corr({reference_bits} / character_count, {candidate_bits} / character_count)
                    FROM {table_name} WHERE {where}
                    """
                ).fetchone()
                try:
                    wilcoxon_p = float(stats.wilcoxon(paired.difference, method="approx").pvalue)
                except ValueError:
                    wilcoxon_p = math.nan
                if high < 0:
                    assessment = f"{candidate}_lower"
                elif low > 0:
                    assessment = f"{reference}_lower"
                else:
                    assessment = "uncertain"
                rows.append(
                    {
                        "domain": domain,
                        "condition": condition,
                        "reference_model": reference,
                        "candidate_model": candidate,
                        "difference_definition": "candidate_minus_reference_bpc",
                        "n_items": item[0],
                        "n_children": len(paired),
                        "occurrence_weighted_bpc_difference": item[1],
                        "median_item_bpc_difference": item[2],
                        "candidate_lower_item_share": item[3],
                        "tie_item_share": item[4],
                        "score_pearson_r": item[5],
                        "child_balanced_bpc_difference": paired.difference.mean(),
                        "child_bootstrap_ci_low": low,
                        "child_bootstrap_ci_high": high,
                        "candidate_lower_child_share": float((paired.difference < 0).mean()),
                        "wilcoxon_child_p_sensitivity": wilcoxon_p,
                        "assessment": assessment,
                    }
                )
    return pd.DataFrame(rows)


def build_context_support(
    connection: duckdb.DuckDBPyConnection,
    child_scorers: Sequence[ScorerInput],
    caregiver_scorers: Sequence[ScorerInput],
    reps: int,
    seed: int,
) -> pd.DataFrame:
    rows = []
    counter = 0
    for scorer in child_scorers:
        child = connection.execute(
            f"""
            SELECT a.child_key, a.dataset, count(*) AS n_items,
                   sum(a.{scorer.slug}_bits - b.{scorer.slug}_bits) / sum(a.character_count) AS support_bpc
            FROM paired_child a INNER JOIN paired_child b USING (target_occurrence_id)
            WHERE a.context_window = 'k0' AND b.context_window = 'k3'
            GROUP BY a.child_key, a.dataset
            ORDER BY a.child_key, a.dataset
            """
        ).fetchdf()
        low, high = bootstrap_mean(child.support_bpc.to_numpy(), reps, seed + counter)
        counter += 1
        item = connection.execute(
            f"""
            SELECT count(*), sum(a.{scorer.slug}_bits - b.{scorer.slug}_bits) / sum(a.character_count),
                   avg(CASE WHEN b.{scorer.slug}_bits < a.{scorer.slug}_bits THEN 1.0 ELSE 0.0 END)
            FROM paired_child a INNER JOIN paired_child b USING (target_occurrence_id)
            WHERE a.context_window = 'k0' AND b.context_window = 'k3'
            """
        ).fetchone()
        rows.append({"domain": "child_utterance", "contrast": "k0_minus_k3", "model": scorer.label, "n_items": item[0], "n_children": len(child), "occurrence_weighted_support_bpc": item[1], "child_balanced_support_bpc": child.support_bpc.mean(), "child_bootstrap_ci_low": low, "child_bootstrap_ci_high": high, "context_lowers_surprisal_item_share": item[2]})
    for scorer in caregiver_scorers:
        child = connection.execute(
            f"""
            SELECT child_key, dataset, count(*) AS n_items,
                   sum({scorer.slug}_unconditional_bits - {scorer.slug}_matched_child_bits) / sum(character_count) AS support_bpc
            FROM paired_caregiver GROUP BY child_key, dataset
            ORDER BY child_key, dataset
            """
        ).fetchdf()
        low, high = bootstrap_mean(child.support_bpc.to_numpy(), reps, seed + counter)
        counter += 1
        item = connection.execute(
            f"""
            SELECT count(*), sum({scorer.slug}_unconditional_bits - {scorer.slug}_matched_child_bits) / sum(character_count),
                   avg(CASE WHEN {scorer.slug}_matched_child_bits < {scorer.slug}_unconditional_bits THEN 1.0 ELSE 0.0 END)
            FROM paired_caregiver
            """
        ).fetchone()
        rows.append({"domain": "caregiver_response", "contrast": "unconditional_minus_matched_child", "model": scorer.label, "n_items": item[0], "n_children": len(child), "occurrence_weighted_support_bpc": item[1], "child_balanced_support_bpc": child.support_bpc.mean(), "child_bootstrap_ci_low": low, "child_bootstrap_ci_high": high, "context_lowers_surprisal_item_share": item[2]})
    return pd.DataFrame(rows)


def build_stratified_tables(
    connection: duckdb.DuckDBPyConnection, scorers: Sequence[ScorerInput]
) -> dict[str, pd.DataFrame]:
    length_queries = []
    age_queries = []
    corpus_queries = []
    for scorer in scorers:
        base = f"'{scorer.label}' AS model, context_window AS condition"
        metrics = f"count(*) AS n_items, sum({scorer.slug}_bits) / sum(character_count) AS bpc, sum({scorer.slug}_bits) / sum(word_count) AS bpw"
        length_queries.append(
            f"SELECT {base}, CASE WHEN word_count <= 12 THEN lpad(word_count::VARCHAR, 2, '0') ELSE '13+' END AS length_bin, {metrics} FROM paired_child GROUP BY context_window, length_bin"
        )
        age_queries.append(
            f"SELECT {base}, {age_case()} AS age_bin, {metrics} FROM paired_child GROUP BY context_window, age_bin"
        )
        corpus_queries.append(
            f"SELECT {base}, dataset AS corpus, {metrics} FROM paired_child GROUP BY context_window, dataset"
        )
    length = connection.execute(" UNION ALL ".join(length_queries)).fetchdf()
    age = connection.execute(" UNION ALL ".join(age_queries)).fetchdf()
    corpus = connection.execute(" UNION ALL ".join(corpus_queries)).fetchdf()
    return {
        "performance_by_length.csv": length.sort_values(
            ["condition", "length_bin", "model"], ignore_index=True
        ),
        "performance_by_age_bin.csv": age.sort_values(
            ["condition", "age_bin", "model"], ignore_index=True
        ),
        "performance_by_corpus.csv": corpus.sort_values(
            ["condition", "corpus", "model"], ignore_index=True
        ),
    }


def build_winner_shares(
    connection: duckdb.DuckDBPyConnection,
    child_scorers: Sequence[ScorerInput],
    caregiver_scorers: Sequence[ScorerInput],
) -> pd.DataFrame:
    if len(child_scorers) != 3:
        raise RuntimeError("winner-share plot currently requires exactly three scorers")
    child_case = "CASE " + " ".join(
        f"WHEN {scorer.slug}_bits = least({', '.join(s.slug + '_bits' for s in child_scorers)}) THEN '{scorer.label}'"
        for scorer in child_scorers
    ) + " END"
    child = connection.execute(
        f"SELECT 'child_utterance' AS domain, context_window AS condition, {child_case} AS winner, count(*) AS n_items FROM paired_child GROUP BY context_window, winner"
    ).fetchdf()
    frames = [child]
    if caregiver_scorers:
        queries = []
        for condition in CAREGIVER_CONDITIONS:
            columns = [f"{scorer.slug}_{condition}_bits" for scorer in caregiver_scorers]
            case = "CASE " + " ".join(
                f"WHEN {column} = least({', '.join(columns)}) THEN '{scorer.label}'"
                for scorer, column in zip(caregiver_scorers, columns)
            ) + " END"
            queries.append(
                f"SELECT 'caregiver_response' AS domain, '{condition}' AS condition, {case} AS winner, count(*) AS n_items FROM paired_caregiver GROUP BY winner"
            )
        frames.append(connection.execute(" UNION ALL ".join(queries)).fetchdf())
    output = pd.concat(frames, ignore_index=True)
    output["winner_share"] = output.n_items / output.groupby(["domain", "condition"]).n_items.transform("sum")
    return output.sort_values(
        ["domain", "condition", "winner"], ignore_index=True
    )


def build_leave_corpus_out(
    child_level: pd.DataFrame, model_order: Sequence[str]
) -> pd.DataFrame:
    rows = []
    for (domain, condition), frame in child_level.groupby(["domain", "condition"]):
        for omitted in sorted(frame.dataset.unique()):
            kept = frame[frame.dataset != omitted]
            for reference, candidate in combinations(model_order, 2):
                left = kept[kept.model == reference].set_index("child_key").micro_bpc
                right = kept[kept.model == candidate].set_index("child_key").micro_bpc
                common = left.index.intersection(right.index)
                rows.append({"domain": domain, "condition": condition, "omitted_corpus": omitted, "reference_model": reference, "candidate_model": candidate, "n_children": len(common), "child_balanced_bpc_difference": float((right.loc[common] - left.loc[common]).mean())})
    return pd.DataFrame(rows)


def plot_outputs(
    connection: duckdb.DuckDBPyConnection,
    overall: pd.DataFrame,
    pairwise: pd.DataFrame,
    support: pd.DataFrame,
    stratified: dict[str, pd.DataFrame],
    winners: pd.DataFrame,
    scorers: Sequence[ScorerInput],
    fig_dir: Path,
) -> list[Path]:
    sns.set_theme(style="whitegrid", context="notebook")
    paths: list[Path] = []

    main_conditions = {
        ("child_utterance", "k0"): "Child utterance · k0",
        ("child_utterance", "k3"): "Child utterance · k3",
        ("caregiver_response", "unconditional"): "Caregiver response · unconditional",
        ("caregiver_response", "matched_child"): "Caregiver response · matched child",
    }
    frame = overall.copy()
    frame["panel"] = [main_conditions.get((row.domain, row.condition)) for row in frame.itertuples()]
    frame = frame[frame.panel.notna()]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=False)
    for ax, panel in zip(axes.flat, main_conditions.values()):
        sub = frame[frame.panel == panel].sort_values("child_balanced_bpc")
        y = np.arange(len(sub))
        ax.errorbar(sub.child_balanced_bpc, y, xerr=[sub.child_balanced_bpc - sub.child_bootstrap_ci_low, sub.child_bootstrap_ci_high - sub.child_balanced_bpc], fmt="none", ecolor="#445", capsize=3)
        for yi, row in zip(y, sub.itertuples()):
            ax.scatter(row.child_balanced_bpc, yi, s=75, color=MODEL_COLORS[row.model], zorder=3)
        ax.set_yticks(y, sub.model)
        ax.invert_yaxis()
        ax.set_title(panel)
        ax.set_xlabel("Child-balanced bits per character (lower is better)")
    fig.suptitle("Cross-tokenizer predictive fit on exact paired targets", fontweight="bold")
    fig.tight_layout()
    path = fig_dir / "overall_bpc_forest.png"; atomic_figure(fig, path); paths.append(path)

    length = stratified["performance_by_length.csv"].copy()
    length = length[(length.condition.isin(["k0", "k3"])) & (length.length_bin != "13+")]
    length["word_count"] = length.length_bin.astype(int)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, condition in zip(axes, ["k0", "k3"]):
        for model in [scorer.label for scorer in scorers]:
            sub = length[(length.condition == condition) & (length.model == model)].sort_values("word_count")
            ax.plot(sub.word_count, sub.bpc, marker="o", label=model, color=MODEL_COLORS[model])
        ax.set_title(f"Child utterances · {condition}")
        ax.set_xlabel("Exact cleaned word count")
        ax.set_xticks(range(1, 13))
    axes[0].set_ylabel("Occurrence-weighted bits per character")
    axes[1].legend(frameon=True)
    fig.suptitle("Historical model-by-length comparison, updated for tokenizer fairness", fontweight="bold")
    fig.tight_layout()
    path = fig_dir / "historical_style_by_length.png"; atomic_figure(fig, path); paths.append(path)

    age = stratified["performance_by_age_bin.csv"].copy()
    age = age[(age.condition == "k3") & (age.age_bin != "outside")]
    age["age_bin"] = pd.Categorical(age.age_bin, [item[0] for item in AGE_BINS], ordered=True)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for model in [scorer.label for scorer in scorers]:
        sub = age[age.model == model].sort_values("age_bin")
        ax.plot(sub.age_bin.astype(str), sub.bpc, marker="o", linewidth=2, label=model, color=MODEL_COLORS[model])
    ax.set(xlabel="Child age bin (months)", ylabel="Occurrence-weighted k3 bits per character", title="Contextual predictive fit across child age")
    ax.legend()
    fig.tight_layout()
    path = fig_dir / "historical_style_by_age.png"; atomic_figure(fig, path); paths.append(path)

    mistral = pairwise[(pairwise.reference_model == "Mistral-7B") & (pairwise.condition.isin(["k0", "k3", "unconditional", "matched_child"]))].copy()
    mistral["label"] = (
        mistral.domain.str.replace("_", " ")
        + " · "
        + mistral.condition.str.replace("_", " ")
        + " · "
        + mistral.candidate_model
    )
    fig, ax = plt.subplots(figsize=(10, max(5, 0.48 * len(mistral))))
    y = np.arange(len(mistral))
    ax.axvline(0, color="black", linewidth=1)
    ax.errorbar(mistral.child_balanced_bpc_difference, y, xerr=[mistral.child_balanced_bpc_difference - mistral.child_bootstrap_ci_low, mistral.child_bootstrap_ci_high - mistral.child_balanced_bpc_difference], fmt="o", color="#334", capsize=3)
    ax.set_yticks(y, mistral.label)
    ax.invert_yaxis()
    ax.set_xlabel("Candidate minus Mistral BPC (negative = candidate less surprised)")
    ax.set_title("Exact-paired model differences with whole-child 95% intervals", fontweight="bold")
    fig.tight_layout()
    path = fig_dir / "paired_difference_forest.png"; atomic_figure(fig, path); paths.append(path)

    winner_main = winners.copy()
    winner_main["panel"] = (
        winner_main.domain.str.replace("_", " ")
        + " · "
        + winner_main.condition.str.replace("_", " ")
    )
    pivot = winner_main.pivot(index="panel", columns="winner", values="winner_share").fillna(0)
    pivot = pivot.reindex(columns=[scorer.label for scorer in scorers], fill_value=0)
    fig, ax = plt.subplots(figsize=(11, 6))
    pivot.plot(kind="barh", stacked=True, color=[MODEL_COLORS[column] for column in pivot.columns], ax=ax)
    ax.set(xlabel="Share of exact targets with the lowest surprisal", ylabel="", xlim=(0, 1), title="Per-target winner share (descriptive)")
    ax.legend(title="Lowest-BPC scorer", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    path = fig_dir / "winner_shares.png"; atomic_figure(fig, path); paths.append(path)

    fig, ax = plt.subplots(figsize=(9, 5))
    model_order = [scorer.label for scorer in scorers]
    for domain, marker in [("child_utterance", "o"), ("caregiver_response", "s")]:
        sub = support[support.domain == domain].copy()
        sub["model"] = pd.Categorical(sub.model, model_order, ordered=True)
        sub = sub.sort_values("model")
        x = np.arange(len(sub)) + (-0.12 if domain == "child_utterance" else 0.12)
        ax.errorbar(x, sub.child_balanced_support_bpc, yerr=[sub.child_balanced_support_bpc - sub.child_bootstrap_ci_low, sub.child_bootstrap_ci_high - sub.child_balanced_support_bpc], fmt=marker, capsize=3, label=domain.replace("_", " "))
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xticks(np.arange(len(scorers)), [scorer.label for scorer in scorers])
    ax.set_ylabel("Context support (BPC; positive = context helps)")
    ax.set_title("How much context reduces target surprisal", fontweight="bold")
    ax.legend()
    fig.tight_layout()
    path = fig_dir / "context_support.png"; atomic_figure(fig, path); paths.append(path)

    corpus = stratified["performance_by_corpus.csv"]
    corpus = corpus[corpus.condition == "k3"]
    fig, ax = plt.subplots(figsize=(10, 5))
    for model in [scorer.label for scorer in scorers]:
        sub = corpus[corpus.model == model].sort_values("corpus")
        ax.plot(sub.corpus, sub.bpc, marker="o", label=model, color=MODEL_COLORS[model])
    ax.set(xlabel="Corpus", ylabel="Occurrence-weighted k3 BPC", title="Child-speech ranking by corpus")
    ax.legend()
    fig.tight_layout()
    path = fig_dir / "corpus_robustness.png"; atomic_figure(fig, path); paths.append(path)

    token = overall[(overall.domain == "child_utterance") & (overall.condition.isin(["k0", "k3"]))]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    sns.barplot(data=token, x="condition", y="child_balanced_bpt_diagnostic", hue="model", hue_order=model_order, palette=MODEL_COLORS, ax=axes[0])
    sns.barplot(data=token, x="condition", y="model_tokens_per_word", hue="model", hue_order=model_order, palette=MODEL_COLORS, ax=axes[1])
    axes[0].set(ylabel="Bits per model token", title="Tokenizer-dependent score")
    axes[1].set(ylabel="Model tokens per cleaned word", title="Tokenization rate")
    axes[0].legend_.remove(); axes[1].legend(title="")
    fig.suptitle("Why per-token perplexity is not the cross-model ranking metric", fontweight="bold")
    fig.tight_layout()
    path = fig_dir / "tokenization_diagnostic.png"; atomic_figure(fig, path); paths.append(path)

    size = overall[((overall.domain == "child_utterance") & (overall.condition.isin(["k0", "k3"]))) | ((overall.domain == "caregiver_response") & (overall.condition == "matched_child"))].copy()
    size["panel"] = np.where(size.domain == "child_utterance", "Child " + size.condition, "Caregiver matched-child")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    annotation_offsets = {
        "Caregiver matched-child": (4, 4),
        "Child k0": (4, -13),
        "Child k3": (4, 7),
    }
    for panel, marker in zip(size.panel.unique(), ["o", "s", "^"]):
        sub = size[size.panel == panel].sort_values("parameters")
        ax.plot(sub.parameters, sub.child_balanced_bpc, marker=marker, linestyle="--", alpha=.75, label=panel)
        for row in sub.itertuples():
            ax.annotate(
                row.model,
                (row.parameters, row.child_balanced_bpc),
                xytext=annotation_offsets[panel],
                textcoords="offset points",
                fontsize=8,
            )
    ax.set_xscale("log")
    ax.set(xlabel="Approximate model parameters (log scale)", ylabel="Child-balanced BPC", title="Model size does not identify training-domain fit")
    ax.legend()
    fig.tight_layout()
    path = fig_dir / "model_size_vs_bpc.png"; atomic_figure(fig, path); paths.append(path)

    sample = connection.execute(
        f"""
        SELECT {scorers[0].slug}_bpc AS x,
               {scorers[1].slug}_bpc AS qwen,
               {scorers[2].slug}_bpc AS tiny
        FROM paired_child WHERE context_window = 'k3'
        ORDER BY hash(target_occurrence_id) LIMIT 75000
        """
    ).fetchdf()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, column, label in zip(axes, ["qwen", "tiny"], [scorers[1].label, scorers[2].label]):
        high = float(np.quantile(np.concatenate([sample.x, sample[column]]), .995))
        ax.hexbin(sample.x.clip(upper=high), sample[column].clip(upper=high), gridsize=55, mincnt=1, bins="log", cmap="viridis")
        ax.plot([0, high], [0, high], color="white", linewidth=1.2, linestyle="--")
        ax.set(xlabel=f"{scorers[0].label} k3 BPC", ylabel=f"{label} k3 BPC", title=f"{label} vs {scorers[0].label}", xlim=(0, high), ylim=(0, high))
    fig.suptitle("Exact-utterance score agreement (deterministic 75k sample)", fontweight="bold")
    fig.tight_layout()
    path = fig_dir / "paired_score_hexbin.png"; atomic_figure(fig, path); paths.append(path)
    return paths


def build_report(
    overall: pd.DataFrame,
    pairwise: pd.DataFrame,
    support: pd.DataFrame,
    leave_out: pd.DataFrame,
    stratified: dict[str, pd.DataFrame],
    source_audit: pd.DataFrame,
    paired_audit: dict[str, object],
    figures: Sequence[Path],
    report_md: Path,
    report_html: Path,
    protocol: Path,
    historical_sources: Sequence[Path],
) -> None:
    main = overall[
        ((overall.domain == "child_utterance") & (overall.condition.isin(["k0", "k3"])))
        | ((overall.domain == "caregiver_response") & (overall.condition.isin(["unconditional", "matched_child"])))
    ].copy()
    main["scope"] = (
        main.domain.str.replace("_", " ")
        + " · "
        + main.condition.str.replace("_", " ")
    )
    main_display = main[["scope", "model", "n_items", "n_children", "child_balanced_bpc", "child_bootstrap_ci_low", "child_bootstrap_ci_high", "bpc_rank"]]
    mistral = pairwise[(pairwise.reference_model == "Mistral-7B") & (pairwise.condition.isin(["k0", "k3", "unconditional", "matched_child"]))].copy()
    pair_display = mistral[["domain", "condition", "candidate_model", "child_balanced_bpc_difference", "child_bootstrap_ci_low", "child_bootstrap_ci_high", "candidate_lower_item_share", "assessment"]]
    child_source_display = source_audit[source_audit.domain == "child_utterance"][[
        "scorer",
        "model_id",
        "model_revision",
        "tokenizer_revision",
        "scoring_code_revision",
        "dtype",
        "max_length",
        "prediction_prefix_policy",
        "truncated_context_rows",
        "max_context_tokens_truncated",
        "audit_status",
    ]]
    total_truncated_context_rows = int(
        child_source_display.truncated_context_rows.fillna(0).sum()
    )
    truncation_statement = (
        "No evaluated child-utterance context required token truncation."
        if total_truncated_context_rows == 0
        else f"The source audits record {total_truncated_context_rows:,} rows with context-token truncation."
    )
    child_k3 = main[(main.domain == "child_utterance") & (main.condition == "k3")].sort_values("child_balanced_bpc")
    child_k0 = main[(main.domain == "child_utterance") & (main.condition == "k0")].sort_values("child_balanced_bpc")
    caregiver = main[(main.domain == "caregiver_response") & (main.condition == "matched_child")].sort_values("child_balanced_bpc")
    qwen_vs_mistral = pairwise[
        (pairwise.reference_model == "Mistral-7B")
        & (pairwise.candidate_model == "Qwen3-14B")
    ]
    tiny_vs_mistral = pairwise[
        (pairwise.reference_model == "Mistral-7B")
        & (pairwise.candidate_model == "TinyDialogues-135M")
    ]
    qwen_consistent = len(qwen_vs_mistral) == 7 and (
        qwen_vs_mistral.assessment == "Mistral-7B_lower"
    ).all()
    tiny_contextual = tiny_vs_mistral[
        tiny_vs_mistral.condition.isin(["k1", "k2", "k3", "base_context", "matched_child"])
    ]
    tiny_crossover = (
        len(tiny_contextual) == 5
        and (tiny_contextual.assessment == "Mistral-7B_lower").all()
        and (
            tiny_vs_mistral[tiny_vs_mistral.condition.isin(["k0", "unconditional"])].assessment
            == "TinyDialogues-135M_lower"
        ).all()
    )
    k3_mistral_pairs = pairwise[
        (pairwise.domain == "child_utterance")
        & (pairwise.condition == "k3")
        & (pairwise.reference_model == "Mistral-7B")
    ].set_index("candidate_model")
    qwen_k3 = k3_mistral_pairs.loc["Qwen3-14B"]
    tiny_k3 = k3_mistral_pairs.loc["TinyDialogues-135M"]

    expected_order = ["Mistral-7B", "Qwen3-14B", "TinyDialogues-135M"]
    length_k3 = stratified["performance_by_length.csv"]
    length_k3 = length_k3[length_k3.condition == "k3"].pivot(
        index="length_bin", columns="model", values="bpc"
    )
    age_k3 = stratified["performance_by_age_bin.csv"]
    age_k3 = age_k3[
        (age_k3.condition == "k3") & (age_k3.age_bin != "outside")
    ].pivot(index="age_bin", columns="model", values="bpc")

    def has_expected_order(frame: pd.DataFrame) -> bool:
        return bool(
            (frame[expected_order[0]] < frame[expected_order[1]]).all()
            and (frame[expected_order[1]] < frame[expected_order[2]]).all()
        )

    leave_scope = leave_out[
        (leave_out.reference_model == "Mistral-7B")
        & (
            ((leave_out.domain == "child_utterance") & (leave_out.condition == "k3"))
            | (
                (leave_out.domain == "caregiver_response")
                & (leave_out.condition == "matched_child")
            )
        )
    ]
    leave_robust = bool(len(leave_scope) == 32 and (leave_scope.child_balanced_bpc_difference > 0).all())
    headline = (
        f"On contextual child speech, **{child_k3.iloc[0].model}** has the lowest child-balanced BPC "
        f"({child_k3.iloc[0].child_balanced_bpc:.3f}); the ordering is "
        + " < ".join(child_k3.model.tolist())
        + "."
    )
    historical_lines = "\n".join(
        f"- `{portable_provenance_path(path)}` (SHA-256 `{sha256_file(path)}`)"
        for path in historical_sources
    )
    figure_lines = "\n\n".join(
        f"![{path.stem.replace('_', ' ').title()}]({os.path.relpath(path, report_md.parent)})" for path in figures
    )
    markdown = f"""# Three-scorer predictive-performance comparison

{headline}

This report compares Mistral-7B-v0.3, Qwen3-14B, and TinyDialogues-135M on
exactly paired targets. **Lower bits per character (BPC) means less surprise
on this evaluation set.** BPC, not bits per model token, is the primary
cross-tokenizer metric.

## Main answer

- Contextual child-speech ranking (`k3`): **{' < '.join(child_k3.model.tolist())}**.
- Unconditional child-speech ranking (`k0`): **{' < '.join(child_k0.model.tolist())}**.
- Matched-context caregiver-response ranking: **{' < '.join(caregiver.model.tolist())}**.
- Qwen result: **{'more surprised than Mistral in all seven evaluated conditions' if qwen_consistent else 'condition-dependent'}**.
- Tiny result: **{'less surprised without context, but more surprised than Mistral in every contextual condition' if tiny_crossover else 'condition-dependent'}**.
- These are corpus-specific cross-entropy rankings. They are not a general
  ranking of semantic competence, child knowledge, or usefulness.

## Primary and stress-test estimates

{markdown_table(main_display)}

Intervals are deterministic 10,000-resample whole-child bootstrap intervals.
The child-utterance domain contains {paired_audit['child_targets']:,} exact
targets across four contexts ({paired_audit['child_rows']:,} paired score rows),
21 children, and three corpora. The secondary caregiver-response domain
contains {paired_audit.get('caregiver_pairs', 0):,} exact primary response
targets across {paired_audit.get('caregiver_children', 0)} children and
{paired_audit.get('caregiver_corpora', 0)} corpora.

## Direct comparisons with Mistral

Every difference below is `candidate BPC - Mistral BPC`. Negative values mean
the candidate is less surprised.

{markdown_table(pair_display)}

At `k3`, Mistral is lower for all 21 child aggregates and for
{(1 - qwen_k3.candidate_lower_item_share - qwen_k3.tie_item_share) * 100:.1f}%
of individual targets against Qwen; it is lower for all 21 child aggregates
and {(1 - tiny_k3.candidate_lower_item_share - tiny_k3.tie_item_share) * 100:.1f}%
of targets against TinyDialogues.

## Robustness and heterogeneity

- The contextual ordering is {'identical' if has_expected_order(length_k3) else 'not identical'}
  in all {len(length_k3)} utterance-length cells and
  {'identical' if has_expected_order(age_k3) else 'not identical'} in all
  {len(age_k3)} observed age bins.
- {'Every' if leave_robust else 'Not every'} leave-one-corpus-out estimate
  retains Mistral's advantage over both alternatives for `k3` child speech
  and matched-child caregiver responses.
- Qwen gains more from context than Mistral, but begins from a much worse
  unconditional score and remains {qwen_k3.child_balanced_bpc_difference:.3f}
  BPC more surprised at `k3`.
- TinyDialogues' child-speech context support is near zero and slightly
  negative; this explains its reversal from the best unconditional score to
  the worst contextual score.

## Context use

Positive support means context reduced target surprisal.

{markdown_table(support[["domain", "contrast", "model", "child_balanced_support_bpc", "child_bootstrap_ci_low", "child_bootstrap_ci_high", "context_lowers_surprisal_item_share"]])}

## Figures

{figure_lines}

## Historical bridge

The new length and age analyses reuse the aggregation structure of these two
historical T7 scripts:

{historical_lines}

The historical plots ranked models with token-weighted bits per token. That
quantity remains in the tokenization diagnostic, but the new ranking uses BPC
because the three current scorers have different tokenizers.

## Provenance and scoring compatibility

All three child-score retrieval audits and the shared caregiver-dataset audit
are `PASS`. Recomputed BPC and BPW agree exactly with the stored fields. Qwen's
tensor-valued `logits_to_keep` path limits vocabulary projection to target
positions; the shared scorer's equivalence tests compare it with the full-logit
path. The later Qwen scoring revision changed its batch size from 2 to 16 and
loaded contract source frames lazily; an explicit git diff found no change to
the target-log-softmax derivation. {truncation_statement}

{markdown_table(child_source_display)}

## Interpretation and publication limits

- The primary comparison is an exact-paired PBM21 child-speech evaluation; the
  caregiver-response analysis is a broader role/corpus stress test.
- Model size is confounded with training data, domain exposure, architecture,
  tokenizer, precision, and scoring conventions. Three models cannot establish
  a scaling law.
- TinyDialogues was trained for child-directed dialogue. Domain match can
  matter more than parameter count.
- Lower scorer surprisal is predictive fit to the observed string. It is not
  semantic information, listener utility, or evidence of a communicative
  optimum.

Protocol: `{protocol}`.
"""
    atomic_text(report_md, markdown)

    figure_html = "".join(
        f"<figure><img src='{html.escape(os.path.relpath(path, report_html.parent))}'><figcaption>{html.escape(path.stem.replace('_', ' ').title())}</figcaption></figure>"
        for path in figures
    )
    html_report = f"""<!doctype html><html><head><meta charset='utf-8'><title>Three-scorer predictive-performance comparison</title><style>
    :root{{--ink:#1c2927;--muted:#5f6f6c;--paper:#fbfcfb;--accent:#165c55;--line:#d8e2df}} body{{font:16px/1.55 system-ui;color:var(--ink);background:var(--paper);max-width:1180px;margin:38px auto;padding:0 28px}} h1,h2{{color:var(--accent)}} .lead{{font-size:1.18rem;background:#eaf3f1;border-left:5px solid var(--accent);padding:1rem 1.2rem}} .warning{{background:#fff3cd;border-left:5px solid #b58900;padding:1rem 1.2rem}} table{{border-collapse:collapse;width:100%;font-size:.9rem;margin:1rem 0 2rem}} th,td{{border:1px solid var(--line);padding:.45rem;text-align:left}} th{{background:#eaf3f1}} img{{max-width:100%;height:auto}} figure{{margin:2.5rem 0}} figcaption{{color:var(--muted);text-align:center}} code{{background:#eef1f0;padding:.1em .25em}}</style></head><body>
    <h1>Three-scorer predictive-performance comparison</h1><p class='lead'>{html.escape(headline.replace('**', ''))}</p>
    <p>This is an exact-paired comparison of Mistral-7B-v0.3, Qwen3-14B, and TinyDialogues-135M. Lower Unicode bits per character means less surprise on these targets.</p>
    <div class='warning'>The ranking is evaluation-domain specific. It is not a general ranking of semantics, child knowledge, or usefulness, and per-model-token perplexity is not used across tokenizers.</div>
    <h2>Main answer</h2><ul>
    <li>Qwen3-14B is {'more surprised than Mistral in all seven evaluated conditions.' if qwen_consistent else 'condition-dependent relative to Mistral.'}</li>
    <li>TinyDialogues-135M is {'less surprised without context but more surprised in every contextual condition.' if tiny_crossover else 'condition-dependent relative to Mistral.'}</li>
    </ul>
    <h2>Main estimates</h2>{html_table(main_display)}
    <h2>Direct comparisons with Mistral</h2><p>Difference = candidate BPC minus Mistral BPC.</p>{html_table(pair_display)}
    <h2>Robustness and heterogeneity</h2><ul>
    <li>The Mistral &lt; Qwen &lt; Tiny ordering holds in all {len(length_k3)} length cells and all {len(age_k3)} observed age bins at k3.</li>
    <li>{'Every' if leave_robust else 'Not every'} leave-one-corpus-out estimate retains Mistral's contextual advantage.</li>
    <li>At k3, Qwen is {qwen_k3.child_balanced_bpc_difference:.3f} BPC more surprised than Mistral.</li>
    </ul>
    <h2>Context use</h2>{html_table(support[["domain", "contrast", "model", "child_balanced_support_bpc", "child_bootstrap_ci_low", "child_bootstrap_ci_high", "context_lowers_surprisal_item_share"]])}
    <h2>Provenance</h2><p>All child retrieval audits and the caregiver dataset audit pass; reconstructed BPC/BPW errors are zero. Qwen's tested logits-to-keep path projects only target-position logits. Its reviewed later revision changes batching and loading, not the target-log-softmax derivation. {html.escape(truncation_statement)}</p>{html_table(child_source_display)}
    <h2>Figures and diagnostics</h2>{figure_html}
    <h2>Methods boundary</h2><p>The primary sample is PBM21 observed child speech; the secondary sample is the frozen all-79 primary next-caregiver-response set. Exact scorer pairing, child-balanced estimates, 10,000 whole-child bootstrap resamples, corpus and length/age diagnostics, and immutable source audits are retained. See <code>{html.escape(str(protocol))}</code>.</p>
    </body></html>"""
    atomic_text(report_html, html_report)


def run_analysis(
    child_scorers: Sequence[ScorerInput],
    caregiver_scorers: Sequence[ScorerInput],
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    protocol: Path,
    historical_sources: Sequence[Path],
    bootstrap_reps: int = 10_000,
    seed: int = 20260904,
    duckdb_memory_limit: str = "2GB",
    duckdb_threads: int = 4,
) -> dict[str, object]:
    if len(child_scorers) != 3 or len({item.label for item in child_scorers}) != 3:
        raise RuntimeError("exactly three uniquely labelled child scorers are required")
    if caregiver_scorers and [item.label for item in caregiver_scorers] != [item.label for item in child_scorers]:
        raise RuntimeError("caregiver scorer labels/order must match child scorer labels/order")
    if not re.fullmatch(r"[1-9][0-9]*(?:MB|GB)", duckdb_memory_limit):
        raise RuntimeError("DuckDB memory limit must look like 512MB or 2GB")
    if duckdb_threads < 1:
        raise RuntimeError("DuckDB threads must be positive")
    if not protocol.is_file():
        raise RuntimeError(f"missing frozen protocol: {protocol}")
    for path in historical_sources:
        if not path.is_file():
            raise RuntimeError(f"missing historical source: {path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    completion_marker = output_dir / "SCORER_PERFORMANCE_COMPARISON_COMPLETE_AND_AUDITED"
    completion_marker.unlink(missing_ok=True)
    (output_dir / "manifest.json").unlink(missing_ok=True)
    temporary_directory = output_dir / "duckdb_tmp"
    temporary_directory.mkdir(parents=True, exist_ok=True)
    temporary_db = output_dir / f".analysis.tmp-{os.getpid()}.duckdb"
    final_db = output_dir / "analysis.duckdb"
    temporary_db.unlink(missing_ok=True)
    connection = duckdb.connect(str(temporary_db))
    connection.execute(f"SET memory_limit='{duckdb_memory_limit}'")
    connection.execute(f"SET threads={duckdb_threads}")
    connection.execute("SET preserve_insertion_order=false")
    connection.execute(f"SET temp_directory='{str(temporary_directory.resolve()).replace(chr(39), chr(39) * 2)}'")
    try:
        source_rows = []
        for scorer in child_scorers:
            print(f"[ingest] child utterances: {scorer.label}", flush=True)
            source_rows.append(ingest_child_scorer(connection, scorer))
        for scorer in caregiver_scorers:
            print(f"[ingest] caregiver responses: {scorer.label}", flush=True)
            source_rows.append(ingest_caregiver_scorer(connection, scorer))
        child_source_rows = [
            row for row in source_rows if row["domain"] == "child_utterance"
        ]
        expected_scoring_metadata = {
            "schema_version": "crossmodel_word_surprisal_v2",
            "score_derivation": "single_teacher_forced_target_token_pass",
        }
        expected_model_scoring_profiles = {
            "Mistral-7B": {
                "engine": "transformers_target_logsoftmax",
                "max_length": 4096,
                "dtype": "fp16",
                "prediction_prefix_policy": "tokenizer_bos",
            },
            "Qwen3-14B": {
                "engine": "transformers_target_logsoftmax_logits_to_keep",
                "max_length": 4096,
                "dtype": "bf16",
                "prediction_prefix_policy": "inject_model_bos_if_missing",
            },
            "TinyDialogues-135M": {
                "engine": "transformers_target_logsoftmax",
                "max_length": 256,
                "dtype": "fp32",
                "prediction_prefix_policy": "tokenizer_bos",
            },
        }
        expected_scoring_revisions = {
            "Mistral-7B": "e890ec1bbe34204c9388bbf53aba8121a685d89b",
            "Qwen3-14B": "c82d2196bd708b14a94359420363d4c38941aad4",
            "TinyDialogues-135M": "e890ec1bbe34204c9388bbf53aba8121a685d89b",
        }
        for row in child_source_rows:
            for field, expected in expected_scoring_metadata.items():
                if row[field] != expected:
                    raise RuntimeError(
                        f"{row['scorer']}: {field}={row[field]!r}, expected {expected!r}"
                    )
            for field, expected in expected_model_scoring_profiles[row["scorer"]].items():
                if row[field] != expected:
                    raise RuntimeError(
                        f"{row['scorer']}: {field}={row[field]!r}, expected {expected!r}"
                    )
            if row["scored_rows"] != row["positive_denominator_rows"]:
                raise RuntimeError(
                    f"{row['scorer']}: scored rows lack positive BPC/BPW denominators"
                )
            if row["scoring_code_revision"] != expected_scoring_revisions[row["scorer"]]:
                raise RuntimeError(
                    f"{row['scorer']}: unreviewed scoring revision "
                    f"{row['scoring_code_revision']}"
                )
        print("[analysis] exact pairing and denominator audits", flush=True)
        paired_audit = build_paired_tables(connection, child_scorers, caregiver_scorers)
        paired_child_path = output_dir / "paired_child_utterance_scores.parquet"
        connection.execute(f"COPY paired_child TO '{str(paired_child_path.resolve()).replace(chr(39), chr(39) * 2)}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        if caregiver_scorers:
            paired_caregiver_path = output_dir / "paired_caregiver_response_scores.parquet"
            connection.execute(f"COPY paired_caregiver TO '{str(paired_caregiver_path.resolve()).replace(chr(39), chr(39) * 2)}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        print("[analysis] summaries, paired contrasts, and robustness checks", flush=True)
        child_level = build_child_level_summaries(connection, child_scorers, caregiver_scorers)
        overall = summarize_overall(child_level, bootstrap_reps, seed)
        pairwise = build_pairwise(connection, child_level, child_scorers, caregiver_scorers, bootstrap_reps, seed + 10_000)
        support = build_context_support(connection, child_scorers, caregiver_scorers, bootstrap_reps, seed + 20_000)
        stratified = build_stratified_tables(connection, child_scorers)
        winners = build_winner_shares(connection, child_scorers, caregiver_scorers)
        leave_out = build_leave_corpus_out(child_level, [item.label for item in child_scorers])
        tables = {
            "source_audit.csv": pd.DataFrame(source_rows),
            "child_level_performance.csv": child_level,
            "overall_performance.csv": overall,
            "pairwise_model_comparisons.csv": pairwise,
            "context_support.csv": support,
            "winner_shares.csv": winners,
            "leave_one_corpus_out.csv": leave_out,
            **stratified,
        }
        for name, frame in tables.items():
            atomic_frame(frame, output_dir / name)
        print("[render] tables, figures, and report", flush=True)
        figures = plot_outputs(connection, overall, pairwise, support, stratified, winners, child_scorers, fig_dir)
        build_report(
            overall,
            pairwise,
            support,
            leave_out,
            stratified,
            tables["source_audit.csv"],
            paired_audit,
            figures,
            report_md,
            report_html,
            protocol,
            historical_sources,
        )
    except BaseException:
        connection.close()
        temporary_db.unlink(missing_ok=True)
        raise
    else:
        connection.close()
    os.replace(temporary_db, final_db)

    expected_contexts = set(overall[overall.domain == "child_utterance"].condition)
    problems = []
    if paired_audit["child_children"] != 21 or paired_audit["child_corpora"] != 3:
        problems.append("primary child scope is not 21 children / 3 corpora")
    if expected_contexts != set(CONTEXT_ORDER):
        problems.append(f"child contexts are {sorted(expected_contexts)}")
    if caregiver_scorers and paired_audit.get("caregiver_pairs") != 413_084:
        problems.append("caregiver primary intersection is not 413084")
    if len(figures) != 10 or not all(path.is_file() and path.stat().st_size > 0 for path in figures):
        problems.append("expected ten nonempty figures")
    if overall[["child_balanced_bpc", "occurrence_weighted_bpc"]].isna().any().any():
        problems.append("nonfinite primary overall estimates")
    artifacts: list[Path] = [final_db, report_md, report_html, protocol, *figures]
    artifacts.extend(output_dir / name for name in tables)
    artifacts.extend([output_dir / "paired_child_utterance_scores.parquet"])
    if caregiver_scorers:
        artifacts.append(output_dir / "paired_caregiver_response_scores.parquet")
    manifest = {
        "status": "PASS" if not problems else "FAIL",
        "analysis_version": "2026-09-04.scorer-performance-v1",
        "metric": "unicode_bits_per_character",
        "bootstrap_reps": bootstrap_reps,
        "bootstrap_seed": seed,
        "duckdb_memory_limit": duckdb_memory_limit,
        "duckdb_threads": duckdb_threads,
        "scorers": [item.label for item in child_scorers],
        "paired_audit": paired_audit,
        "historical_sources": [
            {"path": portable_provenance_path(path), "sha256": sha256_file(path)}
            for path in historical_sources
        ],
        "scoring_revision_compatibility": {
            "status": "PASS",
            "mistral_tiny_revision": "e890ec1bbe34204c9388bbf53aba8121a685d89b",
            "qwen_revision": "c82d2196bd708b14a94359420363d4c38941aad4",
            "review": "Qwen tested logits-to-keep path plus batch-size and contract-loading optimization; score derivation unchanged",
        },
        "problem_count": len(problems),
        "problems": problems,
        "artifacts": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in artifacts],
    }
    atomic_text(output_dir / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    if problems:
        raise RuntimeError("analysis audit failed: " + "; ".join(problems))
    atomic_text(completion_marker, "status=PASS\n")
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child-scorer", action="append", type=parse_scorer, required=True)
    parser.add_argument("--caregiver-scorer", action="append", type=parse_scorer, default=[])
    parser.add_argument("--output-dir", type=Path, default=Path("results/scorer_performance_comparison_20260904"))
    parser.add_argument("--fig-dir", type=Path, default=Path("figs/scorer_performance_comparison_20260904"))
    parser.add_argument("--report-md", type=Path, default=Path("docs/scorer_performance_comparison_2026-09-04.md"))
    parser.add_argument("--report-html", type=Path, default=Path("docs/scorer_performance_comparison_2026-09-04.html"))
    parser.add_argument("--protocol", type=Path, default=Path("docs/scorer_performance_comparison_protocol_2026-09-04.md"))
    parser.add_argument("--historical-source", action="append", type=Path, required=True)
    parser.add_argument("--bootstrap-reps", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260904)
    parser.add_argument("--duckdb-memory-limit", default="2GB")
    parser.add_argument("--duckdb-threads", type=int, default=4)
    args = parser.parse_args(argv)
    report = run_analysis(
        args.child_scorer,
        args.caregiver_scorer,
        args.output_dir,
        args.fig_dir,
        args.report_md,
        args.report_html,
        args.protocol,
        args.historical_source,
        args.bootstrap_reps,
        args.seed,
        args.duckdb_memory_limit,
        args.duckdb_threads,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
