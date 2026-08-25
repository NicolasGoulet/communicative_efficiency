#!/usr/bin/env python3
"""Build the staged full-79 conditional joint-efficiency analysis.

Stages are deliberately independent:

``datasets -> metrics -> models -> plots -> report -> audit``

The workflow never generates or scores responses.  It consumes the audited
all-79 direct-score and Qwen100 products, models length as an adaptive response
to context demand, and treats raw Pareto status as a secondary diagnostic.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover
    from src.render_markdown_report import render_markdown_file


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "results/full79_information_effort_clouds"
DEFAULT_OUTPUT = ROOT / "results/full79_joint_efficiency_analysis"
DEFAULT_FIGURES = ROOT / "figs/full79_joint_efficiency_analysis"
DEFAULT_REPORT_MD = ROOT / "docs/full79_joint_efficiency_explorer.md"
DEFAULT_REPORT_HTML = ROOT / "docs/full79_joint_efficiency_explorer.html"
DEFAULT_QWEN_ROOT = (
    ROOT
    / "results/external/compute_surprisal_mila/"
    "qwen_response_mistral_full100_20260817_f5dd5aa"
)
DEFAULT_BAYES = ROOT / "results/corrected_pbm_bayes_v2/scores/pbm_crossfit_bayes_scores.csv.gz"
MODEL_SCRIPT = ROOT / "src/fit_full79_joint_efficiency_models.R"

AGE_BINS = (
    "006-023",
    "024-029",
    "030-035",
    "036-041",
    "042-047",
    "048-053",
    "054-059",
    "060-065",
)
AGE_ORDER_SQL = "CASE age_bin " + " ".join(
    f"WHEN '{age}' THEN {index}" for index, age in enumerate(AGE_BINS, start=1)
) + " END"
WORD_PATTERN = r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:'[A-Za-zÀ-ÖØ-öø-ÿ]+)*"
WORD_PATTERN_SQL = WORD_PATTERN.replace("'", "''")

SOURCE_LABELS = {
    "observed_child": "Observed child",
    "qwen": "Qwen free-length",
    "random": "Random",
    "unigram": "Unigram",
    "bigram": "Bigram",
    "trigram": "Trigram",
}
SOURCE_COLORS = {
    "observed_child": "#111111",
    "qwen": "#9ca3af",
    "random": "#d73027",
    "unigram": "#f59e0b",
    "bigram": "#2ca25f",
    "trigram": "#2563eb",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunksize: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunksize):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    compression = "gzip" if path.suffix == ".gz" else None
    frame.to_csv(temporary, index=False, compression=compression, lineterminator="\n")
    os.replace(temporary, path)


def atomic_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def configure_duckdb(connection: duckdb.DuckDBPyConnection, temporary: Path, memory_limit: str) -> None:
    temporary.mkdir(parents=True, exist_ok=True)
    connection.execute(f"SET memory_limit={sql_literal(memory_limit)}")
    connection.execute("SET threads=4")
    connection.execute("SET preserve_insertion_order=false")
    connection.execute("SET temp_directory=?", [str(temporary)])


def copy_parquet(connection: duckdb.DuckDBPyConnection, query: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    connection.execute(
        f"COPY ({query}) TO ? (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)",
        [str(temporary)],
    )
    os.replace(temporary, path)


def copy_csv_gz(connection: duckdb.DuckDBPyConnection, query: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    connection.execute(
        f"COPY ({query}) TO ? (FORMAT CSV, HEADER, COMPRESSION GZIP)",
        [str(temporary)],
    )
    os.replace(temporary, path)


def file_record(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return {"path": str(path.resolve()), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def schema_record(connection: duckdb.DuckDBPyConnection, parquet_path: Path, schema_path: Path) -> None:
    frame = connection.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(parquet_path)]).fetchdf()
    atomic_json(
        {
            "path": str(parquet_path.resolve()),
            "columns": [
                {"name": str(row.column_name), "type": str(row.column_type), "nullable": str(row.null) == "YES"}
                for row in frame.itertuples(index=False)
            ],
        },
        schema_path,
    )


def write_manifest(
    *,
    stage: str,
    path: Path,
    inputs: Mapping[str, Path],
    outputs: Mapping[str, Path],
    audit: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "stage": stage,
        "completed_at": utc_now(),
        "controller_sha256": sha256_file(Path(__file__)),
        "inputs": {name: file_record(value) for name, value in inputs.items()},
        "outputs": {name: file_record(value) for name, value in outputs.items()},
        "audit": dict(audit),
    }
    if extra:
        payload.update(extra)
    atomic_json(payload, path)
    return payload


def require_manifest(path: Path, stage: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing {stage} manifest: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("stage") != stage:
        raise RuntimeError(f"expected {stage} manifest, found {manifest.get('stage')}")
    for name, record in manifest.get("outputs", {}).items():
        output = Path(record["path"])
        if not output.exists() or sha256_file(output) != record["sha256"]:
            raise RuntimeError(f"stale {stage} output: {name} ({output})")
    return manifest


def manifest_output(manifest: Mapping[str, Any], name: str) -> Path:
    return Path(manifest["outputs"][name]["path"])


def run_datasets_stage(args: argparse.Namespace) -> dict[str, Any]:
    upstream_audit = args.upstream_dir / "audit/final_audit.json"
    normalized = args.upstream_dir / "metrics/candidate_context_normalized.parquet"
    contexts = args.upstream_dir / "metrics/qwen_context_metrics.parquet"
    candidates = args.upstream_dir / "datasets/non_lstm_candidates.parquet"
    for path in (upstream_audit, normalized, contexts, candidates):
        if not path.exists():
            raise FileNotFoundError(path)
    audit_payload = json.loads(upstream_audit.read_text(encoding="utf-8"))
    if audit_payload.get("status") != "PASS_CORE_LSTM_PENDING" or audit_payload.get("problems"):
        raise RuntimeError("upstream cloud analysis has not passed its core audit")

    dataset_dir = args.output_dir / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = dataset_dir / "analysis_rows.parquet"
    schema_path = dataset_dir / "analysis_rows.schema.json"
    audit_path = dataset_dir / "dataset_audit.json"

    with tempfile.TemporaryDirectory(prefix="joint_eff_dataset_", dir=args.temp_dir) as temp_name:
        connection = duckdb.connect(str(Path(temp_name) / "datasets.duckdb"))
        configure_duckdb(connection, Path(temp_name) / "spill", args.duckdb_memory_limit)
        connection.execute(f"CREATE VIEW normalized AS SELECT * FROM read_parquet({sql_literal(normalized)})")
        connection.execute(f"CREATE VIEW contexts AS SELECT * FROM read_parquet({sql_literal(contexts)})")
        query = """
            SELECT n.utterance_id, n.context_id, n.dataset, n.child_key, n.session_id,
                   n.age_months, n.age_bin,
                   CAST(n.word_count AS INTEGER) AS child_words,
                   n.k0_sum_bits AS child_k0_sum_bits,
                   n.k3_sum_bits AS child_k3_sum_bits,
                   n.k3_mean_bits_per_token AS child_k3_bits_per_token,
                   n.context_support_bits AS child_context_support_bits,
                   q.context_word_count,
                   q.unique_response_count, q.top_response_probability,
                   q.exact_string_entropy_bits AS response_entropy_bits,
                   q.qwen_mean_word_count, q.qwen_sd_word_count,
                   q.qwen_median_word_count, q.qwen_p10_word_count, q.qwen_p90_word_count,
                   q.qwen_min_word_count, q.qwen_max_word_count,
                   q.qwen_mean_k0_sum_bits, q.qwen_mean_k3_sum_bits,
                   q.qwen_sd_k3_sum_bits, q.qwen_median_k3_sum_bits,
                   q.qwen_p10_k3_sum_bits, q.qwen_p90_k3_sum_bits,
                   q.qwen_mean_k3_bits_per_token, q.qwen_mean_context_support_bits,
                   n.z_effort, n.z_k3,
                   n.effort_percentile_in_qwen,
                   n.k3_percentile_in_qwen,
                   n.word_count-q.qwen_mean_word_count AS child_words_minus_qwen_mean,
                   n.word_count-q.qwen_median_word_count AS child_words_minus_qwen_median,
                   n.word_count/NULLIF(q.qwen_mean_word_count, 0) AS child_words_ratio_qwen_mean,
                   (n.effort_percentile_in_qwen*99.0+0.5)/100.0 AS effort_percentile_open,
                   (n.k3_percentile_in_qwen*99.0+0.5)/100.0 AS k3_percentile_open
            FROM normalized n JOIN contexts q USING (context_id)
            WHERE n.source='observed_child'
            ORDER BY n.dataset, n.child_key, n.age_months, n.utterance_id
        """
        copy_parquet(connection, query, analysis_path)
        schema_record(connection, analysis_path, schema_path)
        checks = connection.execute(
            """
            SELECT count(*) AS rows,
                   count(DISTINCT utterance_id) AS unique_utterances,
                   count(DISTINCT context_id) AS contexts,
                   count(DISTINCT child_key) AS children,
                   count(DISTINCT dataset) AS corpora,
                   sum(age_months IS NULL OR NOT isfinite(age_months)) AS invalid_age,
                   sum(child_words IS NULL OR child_words <= 0) AS invalid_words,
                   sum(child_k3_sum_bits IS NULL OR NOT isfinite(child_k3_sum_bits)) AS invalid_k3,
                   sum(response_entropy_bits IS NULL OR NOT isfinite(response_entropy_bits)) AS invalid_entropy,
                   sum(effort_percentile_in_qwen < 0 OR effort_percentile_in_qwen > 1) AS invalid_effort_rank,
                   sum(k3_percentile_in_qwen < 0 OR k3_percentile_in_qwen > 1) AS invalid_k3_rank
            FROM read_parquet(?)
            """,
            [str(analysis_path)],
        ).fetchone()
        audit = {
            "rows": int(checks[0]),
            "unique_utterances": int(checks[1]),
            "contexts": int(checks[2]),
            "children": int(checks[3]),
            "corpora": int(checks[4]),
            "invalid_age": int(checks[5]),
            "invalid_words": int(checks[6]),
            "invalid_k3": int(checks[7]),
            "invalid_entropy": int(checks[8]),
            "invalid_effort_rank": int(checks[9]),
            "invalid_k3_rank": int(checks[10]),
        }
        expected = {
            "rows": args.expected_eligible_rows,
            "unique_utterances": args.expected_eligible_rows,
            "contexts": args.expected_contexts,
            "children": args.expected_children,
            "corpora": args.expected_corpora,
        }
        problems = [key for key, value in expected.items() if audit[key] != value]
        problems.extend(key for key in audit if key.startswith("invalid_") and audit[key] != 0)
        audit["status"] = "PASS" if not problems else "FAIL"
        audit["problems"] = problems
        atomic_json(audit, audit_path)
        if problems:
            raise RuntimeError(f"dataset audit failed: {problems}")
        connection.close()

    manifest_path = dataset_dir / "dataset_manifest.json"
    return write_manifest(
        stage="datasets",
        path=manifest_path,
        inputs={
            "upstream_audit": upstream_audit,
            "candidate_context_normalized": normalized,
            "qwen_context_metrics": contexts,
            "candidate_text_table": candidates,
        },
        outputs={"analysis_rows": analysis_path, "schema": schema_path, "audit": audit_path},
        audit=audit,
        extra={"scientific_unit": "one eligible observed child utterance"},
    )


def _qwen_glob(qwen_root: Path, tier: str) -> str:
    return str((qwen_root / f"processed/{tier}/scored_*.csv.gz").resolve())


def _bootstrap_child_age(
    child_cells: pd.DataFrame,
    *,
    metrics: Sequence[str],
    draws: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    children = sorted(child_cells["child_key"].astype(str).unique())
    records: list[dict[str, Any]] = []
    for age_bin in AGE_BINS:
        age_rows = child_cells.loc[child_cells["age_bin"].eq(age_bin)].copy()
        if age_rows.empty:
            continue
        point = age_rows.groupby("child_key", observed=True)[list(metrics)].mean().mean()
        draw_values = {metric: [] for metric in metrics}
        by_child = {str(key): value for key, value in age_rows.groupby("child_key", observed=True)}
        available = sorted(by_child)
        for _ in range(draws):
            sampled = rng.choice(available, size=len(available), replace=True)
            for metric in metrics:
                values = [float(by_child[str(child)][metric].mean()) for child in sampled]
                draw_values[metric].append(float(np.nanmean(values)))
        for metric in metrics:
            values = np.asarray(draw_values[metric], dtype=float)
            records.append(
                {
                    "age_bin": age_bin,
                    "metric": metric,
                    "estimate": float(point[metric]),
                    "ci_low": float(np.nanquantile(values, 0.025)),
                    "ci_high": float(np.nanquantile(values, 0.975)),
                    "bootstrap_draws": int(draws),
                    "children": int(len(available)),
                }
            )
    return pd.DataFrame.from_records(records)


def run_metrics_stage(args: argparse.Namespace) -> dict[str, Any]:
    dataset_manifest_path = args.output_dir / "datasets/dataset_manifest.json"
    dataset_manifest = require_manifest(dataset_manifest_path, "datasets")
    analysis_path = manifest_output(dataset_manifest, "analysis_rows")
    candidates_path = args.upstream_dir / "datasets/non_lstm_candidates.parquet"
    length_cells_path = args.upstream_dir / "metrics/child_age_model_length_cells.parquet"
    bayes_path = args.bayes_scores
    metrics_dir = args.output_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, Path] = {}
    with tempfile.TemporaryDirectory(prefix="joint_eff_metrics_", dir=args.temp_dir) as temp_name:
        temp_root = Path(temp_name)
        connection = duckdb.connect(str(temp_root / "metrics.duckdb"))
        configure_duckdb(connection, temp_root / "spill", args.duckdb_memory_limit)
        connection.execute(f"CREATE VIEW observed AS SELECT * FROM read_parquet({sql_literal(analysis_path)})")

        correlations_path = metrics_dir / "raw_correlations.csv"
        correlations = connection.execute(
            """
            SELECT corr(child_words, response_entropy_bits) AS child_length_entropy,
                   corr(qwen_mean_word_count, response_entropy_bits) AS qwen_length_entropy,
                   corr(child_words_minus_qwen_mean, response_entropy_bits) AS residual_entropy,
                   corr(age_months, child_words) AS age_child_length,
                   corr(age_months, effort_percentile_in_qwen) AS age_effort_percentile,
                   corr(age_months, k3_percentile_in_qwen) AS age_k3_percentile
            FROM observed
            """
        ).fetchdf()
        atomic_csv(correlations, correlations_path)
        outputs["raw_correlations"] = correlations_path

        age_summary_path = metrics_dir / "age_distribution_summary.csv"
        age_summary = connection.execute(
            f"""
            SELECT age_bin, count(*)::BIGINT AS n_rows,
                   count(DISTINCT child_key)::INTEGER AS children,
                   avg(child_words) AS mean_child_words,
                   median(child_words) AS median_child_words,
                   quantile_cont(child_words, 0.25) AS p25_child_words,
                   quantile_cont(child_words, 0.75) AS p75_child_words,
                   avg(qwen_mean_word_count) AS mean_qwen_words,
                   median(qwen_mean_word_count) AS median_qwen_words,
                   avg(child_words_minus_qwen_mean) AS mean_length_residual,
                   median(child_words_minus_qwen_mean) AS median_length_residual,
                   median(effort_percentile_in_qwen) AS median_effort_percentile,
                   median(k3_percentile_in_qwen) AS median_k3_percentile,
                   avg(response_entropy_bits) AS mean_response_entropy
            FROM observed GROUP BY age_bin ORDER BY {AGE_ORDER_SQL}
            """
        ).fetchdf()
        atomic_csv(age_summary, age_summary_path)
        outputs["age_distribution_summary"] = age_summary_path

        entropy_contract_path = metrics_dir / "entropy_band_contract.json"
        entropy_quantiles = connection.execute(
            "SELECT quantile_cont(response_entropy_bits, [0.2,0.4,0.6,0.8]) FROM observed"
        ).fetchone()[0]
        entropy_contract = {
            "definition": "global utterance-weighted quintiles of exact-string Qwen response entropy",
            "cutpoints": [float(value) for value in entropy_quantiles],
            "labels": ["lowest", "low", "middle", "high", "highest"],
        }
        atomic_json(entropy_contract, entropy_contract_path)
        outputs["entropy_band_contract"] = entropy_contract_path
        cut = entropy_contract["cutpoints"]
        entropy_case = (
            f"CASE WHEN response_entropy_bits <= {cut[0]} THEN 'lowest' "
            f"WHEN response_entropy_bits <= {cut[1]} THEN 'low' "
            f"WHEN response_entropy_bits <= {cut[2]} THEN 'middle' "
            f"WHEN response_entropy_bits <= {cut[3]} THEN 'high' ELSE 'highest' END"
        )

        demand_path = metrics_dir / "age_entropy_distribution_summary.csv"
        demand = connection.execute(
            f"""
            WITH labelled AS (SELECT *, {entropy_case} AS entropy_band FROM observed)
            SELECT age_bin, entropy_band, count(*)::BIGINT AS n_rows,
                   count(DISTINCT child_key)::INTEGER AS children,
                   avg(response_entropy_bits) AS mean_entropy,
                   avg(child_words) AS mean_child_words,
                   median(child_words) AS median_child_words,
                   quantile_cont(child_words, 0.1) AS p10_child_words,
                   quantile_cont(child_words, 0.25) AS p25_child_words,
                   quantile_cont(child_words, 0.75) AS p75_child_words,
                   quantile_cont(child_words, 0.9) AS p90_child_words,
                   avg(qwen_mean_word_count) AS mean_qwen_words,
                   avg(child_words_minus_qwen_mean) AS mean_length_residual,
                   median(child_words_minus_qwen_mean) AS median_length_residual,
                   median(effort_percentile_in_qwen) AS median_effort_percentile,
                   median(k3_percentile_in_qwen) AS median_k3_percentile
            FROM labelled GROUP BY age_bin, entropy_band
            ORDER BY {AGE_ORDER_SQL},
              CASE entropy_band WHEN 'lowest' THEN 1 WHEN 'low' THEN 2 WHEN 'middle' THEN 3
                   WHEN 'high' THEN 4 ELSE 5 END
            """
        ).fetchdf()
        atomic_csv(demand, demand_path)
        outputs["age_entropy_distribution"] = demand_path

        calibration_path = metrics_dir / "length_calibration_deciles.csv"
        calibration = connection.execute(
            f"""
            WITH ranked AS (
              SELECT *, ntile(10) OVER (PARTITION BY age_bin ORDER BY qwen_mean_word_count) AS qwen_length_decile
              FROM observed
            )
            SELECT age_bin, qwen_length_decile, count(*)::BIGINT AS n_rows,
                   avg(qwen_mean_word_count) AS qwen_expected_words,
                   avg(response_entropy_bits) AS response_entropy,
                   avg(child_words) AS mean_child_words,
                   median(child_words) AS median_child_words,
                   quantile_cont(child_words, 0.25) AS p25_child_words,
                   quantile_cont(child_words, 0.75) AS p75_child_words
            FROM ranked GROUP BY age_bin, qwen_length_decile
            ORDER BY {AGE_ORDER_SQL}, qwen_length_decile
            """
        ).fetchdf()
        atomic_csv(calibration, calibration_path)
        outputs["length_calibration"] = calibration_path

        atlas_path = metrics_dir / "paper_atlas_distribution_summary.csv"
        atlas = connection.execute(
            f"""
            SELECT source, age_bin, word_count, sum(n_rows)::BIGINT AS n_rows,
                   count(*)::INTEGER AS child_age_cells,
                   count(DISTINCT child_key)::INTEGER AS children,
                   sum(mean_k3_sum_bits*n_k3_rows)/sum(n_k3_rows) AS weighted_mean_k3,
                   median(mean_k3_sum_bits) AS median_k3,
                   quantile_cont(mean_k3_sum_bits, 0.1) AS p10_k3,
                   quantile_cont(mean_k3_sum_bits, 0.25) AS p25_k3,
                   quantile_cont(mean_k3_sum_bits, 0.75) AS p75_k3,
                   quantile_cont(mean_k3_sum_bits, 0.9) AS p90_k3,
                   median(mean_k3_bits_per_token) AS median_k3_bits_per_token,
                   median(mean_k0_sum_bits) AS median_k0,
                   median(mean_context_support_bits) AS median_context_support
            FROM read_parquet(?)
            WHERE word_count BETWEEN 1 AND 12
            GROUP BY source, age_bin, word_count
            ORDER BY {AGE_ORDER_SQL}, source, word_count
            """,
            [str(length_cells_path)],
        ).fetchdf()
        atomic_csv(atlas, atlas_path)
        outputs["paper_atlas_distribution"] = atlas_path

        print("[metrics] materializing slim Qwen response coordinates", flush=True)
        core_glob = _qwen_glob(args.qwen_root, "core75")
        extension_glob = _qwen_glob(args.qwen_root, "extension25")
        connection.execute(
            f"""
            CREATE TABLE qwen_slim AS
            SELECT response_id, context_id,
                   len(regexp_extract_all(target_text, '{WORD_PATTERN_SQL}'))::INTEGER AS word_count,
                   sum_bits_k3::DOUBLE AS k3_sum_bits
            FROM read_csv_auto({sql_literal(core_glob)}, header=true, union_by_name=true)
            UNION ALL
            SELECT response_id, context_id,
                   len(regexp_extract_all(target_text, '{WORD_PATTERN_SQL}'))::INTEGER AS word_count,
                   sum_bits_k3::DOUBLE AS k3_sum_bits
            FROM read_csv_auto({sql_literal(extension_glob)}, header=true, union_by_name=true)
            """
        )
        qwen_checks = connection.execute(
            """
            SELECT count(*), count(DISTINCT response_id), count(DISTINCT context_id),
                   sum(word_count < 0 OR word_count IS NULL),
                   sum(k3_sum_bits IS NULL OR NOT isfinite(k3_sum_bits))
            FROM qwen_slim
            """
        ).fetchone()
        if tuple(int(value) for value in qwen_checks[:3]) != (
            args.expected_qwen_responses,
            args.expected_qwen_responses,
            args.expected_contexts,
        ):
            raise RuntimeError(f"Qwen slim-table count mismatch: {qwen_checks}")
        if int(qwen_checks[3]) or int(qwen_checks[4]):
            raise RuntimeError(f"invalid Qwen slim values: {qwen_checks}")

        print("[metrics] calculating exact-length and raw dominance diagnostics", flush=True)
        cloud_path = metrics_dir / "observed_cloud_metrics.parquet"
        cloud_query = """
            SELECT o.utterance_id,
                   count(*)::INTEGER AS qwen_responses,
                   sum(CASE WHEN q.word_count=o.child_words THEN 1 ELSE 0 END)::INTEGER AS exact_length_support,
                   CASE WHEN sum(CASE WHEN q.word_count=o.child_words THEN 1 ELSE 0 END) > 0 THEN
                     (sum(CASE WHEN q.word_count=o.child_words AND q.k3_sum_bits<o.child_k3_sum_bits THEN 1 ELSE 0 END)
                      + 0.5*sum(CASE WHEN q.word_count=o.child_words AND q.k3_sum_bits=o.child_k3_sum_bits THEN 1 ELSE 0 END))
                     / sum(CASE WHEN q.word_count=o.child_words THEN 1 ELSE 0 END)
                   END AS exact_length_k3_percentile,
                   median(CASE WHEN q.word_count=o.child_words THEN q.k3_sum_bits END) AS exact_length_qwen_median_k3,
                   quantile_cont(CASE WHEN q.word_count=o.child_words THEN q.k3_sum_bits END, 0.1) AS exact_length_qwen_p10_k3,
                   quantile_cont(CASE WHEN q.word_count=o.child_words THEN q.k3_sum_bits END, 0.9) AS exact_length_qwen_p90_k3,
                   o.child_k3_sum_bits-median(CASE WHEN q.word_count=o.child_words THEN q.k3_sum_bits END)
                     AS child_minus_exact_length_qwen_median_k3,
                   sum(CASE WHEN q.word_count<=o.child_words AND q.k3_sum_bits<=o.child_k3_sum_bits
                                  AND (q.word_count<o.child_words OR q.k3_sum_bits<o.child_k3_sum_bits)
                            THEN 1 ELSE 0 END)::INTEGER AS dominating_qwen_count,
                   sum(CASE WHEN q.word_count<=o.child_words AND q.k3_sum_bits<=o.child_k3_sum_bits
                                  AND (q.word_count<o.child_words OR q.k3_sum_bits<o.child_k3_sum_bits)
                            THEN 1 ELSE 0 END)/100.0 AS dominating_qwen_proportion,
                   CASE WHEN sum(CASE WHEN q.word_count<=o.child_words AND q.k3_sum_bits<=o.child_k3_sum_bits
                                           AND (q.word_count<o.child_words OR q.k3_sum_bits<o.child_k3_sum_bits)
                                      THEN 1 ELSE 0 END)=0 THEN 1 ELSE 0 END AS raw_nondominated,
                   min(CASE WHEN q.word_count<=o.child_words AND q.k3_sum_bits<=o.child_k3_sum_bits
                                  AND (q.word_count<o.child_words OR q.k3_sum_bits<o.child_k3_sum_bits)
                            THEN sqrt(pow((o.child_words-q.word_count)/NULLIF(o.qwen_sd_word_count,0),2)
                                     +pow((o.child_k3_sum_bits-q.k3_sum_bits)/NULLIF(o.qwen_sd_k3_sum_bits,0),2)) END)
                     AS nearest_dominating_distance,
                   min(sqrt(pow((o.child_words-q.word_count)/NULLIF(o.qwen_sd_word_count,0),2)
                            +pow((o.child_k3_sum_bits-q.k3_sum_bits)/NULLIF(o.qwen_sd_k3_sum_bits,0),2)))
                     AS nearest_qwen_cloud_distance
            FROM observed o JOIN qwen_slim q USING (context_id)
            GROUP BY o.utterance_id, o.child_words, o.child_k3_sum_bits,
                     o.qwen_sd_word_count, o.qwen_sd_k3_sum_bits
        """
        copy_parquet(connection, cloud_query, cloud_path)
        outputs["observed_cloud_metrics"] = cloud_path

        cloud_checks = connection.execute(
            """
            SELECT count(*), count(DISTINCT utterance_id), sum(qwen_responses<>100),
                   sum(exact_length_support=0),
                   sum(exact_length_k3_percentile<0 OR exact_length_k3_percentile>1),
                   sum(raw_nondominated NOT IN (0,1))
            FROM read_parquet(?)
            """,
            [str(cloud_path)],
        ).fetchone()
        if int(cloud_checks[0]) != args.expected_eligible_rows or int(cloud_checks[1]) != args.expected_eligible_rows:
            raise RuntimeError(f"cloud metric row mismatch: {cloud_checks}")
        if int(cloud_checks[2]) or int(cloud_checks[4]) or int(cloud_checks[5]):
            raise RuntimeError(f"cloud metric audit failed: {cloud_checks}")

        model_rows_path = metrics_dir / "model_rows.parquet"
        model_rows_csv = metrics_dir / "model_rows.csv.gz"
        model_query = f"""
            SELECT o.*, c.exact_length_support, c.exact_length_k3_percentile,
                   (c.exact_length_k3_percentile*99.0+0.5)/100.0 AS exact_length_k3_percentile_open,
                   c.exact_length_qwen_median_k3, c.exact_length_qwen_p10_k3,
                   c.exact_length_qwen_p90_k3,
                   c.child_minus_exact_length_qwen_median_k3,
                   c.dominating_qwen_count, c.dominating_qwen_proportion,
                   c.raw_nondominated, c.nearest_dominating_distance,
                   c.nearest_qwen_cloud_distance
            FROM observed o JOIN read_parquet({sql_literal(cloud_path)}) c USING (utterance_id)
        """
        connection.execute("CREATE VIEW model_rows AS " + model_query)
        copy_parquet(connection, "SELECT * FROM model_rows ORDER BY dataset, child_key, age_months, utterance_id", model_rows_path)
        copy_csv_gz(connection, "SELECT * FROM model_rows ORDER BY dataset, child_key, age_months, utterance_id", model_rows_csv)
        outputs["model_rows"] = model_rows_path
        outputs["model_rows_csv"] = model_rows_csv
        gamm_rows_csv = metrics_dir / "gamm_rows.csv.gz"
        copy_csv_gz(
            connection,
            """
            SELECT utterance_id, dataset, child_key, session_id, age_months, age_bin,
                   child_words, child_k0_sum_bits, child_k3_sum_bits,
                   child_k3_bits_per_token, child_context_support_bits,
                   context_word_count, response_entropy_bits,
                   qwen_mean_word_count, qwen_median_word_count,
                   child_words_minus_qwen_mean, effort_percentile_open,
                   z_effort, z_k3, exact_length_support,
                   exact_length_k3_percentile_open,
                   child_minus_exact_length_qwen_median_k3,
                   raw_nondominated, dominating_qwen_proportion,
                   nearest_qwen_cloud_distance
            FROM model_rows
            ORDER BY dataset, child_key, age_months, utterance_id
            """,
            gamm_rows_csv,
        )
        outputs["gamm_rows_csv"] = gamm_rows_csv

        cloud_summary_path = metrics_dir / "cloud_distribution_summary.csv"
        cloud_summary = connection.execute(
            f"""
            WITH labelled AS (SELECT *, {entropy_case} AS entropy_band FROM model_rows)
            SELECT age_bin, entropy_band, count(*)::BIGINT AS n_rows,
                   sum(exact_length_support>=5)::BIGINT AS exact_length_supported_rows,
                   median(effort_percentile_in_qwen) AS median_effort_percentile,
                   quantile_cont(effort_percentile_in_qwen,0.25) AS p25_effort_percentile,
                   quantile_cont(effort_percentile_in_qwen,0.75) AS p75_effort_percentile,
                   median(k3_percentile_in_qwen) AS median_k3_percentile,
                   median(CASE WHEN exact_length_support>=5 THEN exact_length_k3_percentile END)
                     AS median_exact_length_k3_percentile,
                   median(CASE WHEN exact_length_support>=5 THEN child_minus_exact_length_qwen_median_k3 END)
                     AS median_exact_length_k3_gap,
                   avg(raw_nondominated) AS raw_nondominated_rate,
                   median(dominating_qwen_proportion) AS median_dominating_proportion,
                   median(nearest_qwen_cloud_distance) AS median_nearest_cloud_distance
            FROM labelled GROUP BY age_bin, entropy_band
            ORDER BY {AGE_ORDER_SQL},
              CASE entropy_band WHEN 'lowest' THEN 1 WHEN 'low' THEN 2 WHEN 'middle' THEN 3
                   WHEN 'high' THEN 4 ELSE 5 END
            """
        ).fetchdf()
        atomic_csv(cloud_summary, cloud_summary_path)
        outputs["cloud_distribution_summary"] = cloud_summary_path

        child_cells_path = metrics_dir / "child_age_metric_cells.parquet"
        child_cells_query = """
            SELECT dataset, child_key, age_bin, count(*)::INTEGER AS n_rows,
                   avg(child_words) AS child_words,
                   avg(child_words_minus_qwen_mean) AS child_words_minus_qwen_mean,
                   avg(effort_percentile_in_qwen) AS effort_percentile_in_qwen,
                   avg(k3_percentile_in_qwen) AS k3_percentile_in_qwen,
                   avg(CASE WHEN exact_length_support>=5 THEN child_minus_exact_length_qwen_median_k3 END)
                     AS exact_length_k3_gap,
                   avg(raw_nondominated) AS raw_nondominated
            FROM model_rows GROUP BY dataset, child_key, age_bin
        """
        copy_parquet(connection, child_cells_query, child_cells_path)
        outputs["child_age_metric_cells"] = child_cells_path
        child_cells = connection.execute("SELECT * FROM read_parquet(?)", [str(child_cells_path)]).fetchdf()
        bootstrap_path = metrics_dir / "child_bootstrap_age_trajectories.csv"
        bootstrap = _bootstrap_child_age(
            child_cells,
            metrics=[
                "child_words",
                "child_words_minus_qwen_mean",
                "effort_percentile_in_qwen",
                "k3_percentile_in_qwen",
                "exact_length_k3_gap",
                "raw_nondominated",
            ],
            draws=args.bootstrap_draws,
            seed=args.bootstrap_seed,
        )
        atomic_csv(bootstrap, bootstrap_path)
        outputs["child_bootstrap_age_trajectories"] = bootstrap_path

        if bayes_path.exists():
            bayes_summary_path = metrics_dir / "corrected_bayes_decomposition_summary.csv"
            bayes_summary = connection.execute(
                f"""
                SELECT age_bin, source_model, count(*)::BIGINT AS n_rows,
                       avg(log2_p_u_crossfit) AS mean_log2_prior,
                       median(log2_p_u_crossfit) AS median_log2_prior,
                       avg(context_log2_evidence_crossfit) AS mean_context_evidence,
                       median(context_log2_evidence_crossfit) AS median_context_evidence,
                       avg(candidate_set_probability) AS mean_candidate_probability,
                       median(candidate_set_probability) AS median_candidate_probability,
                       avg(CAST(candidate_set_rank=1 AS INTEGER)) AS rank1_rate
                FROM read_csv_auto(?, header=true)
                GROUP BY age_bin, source_model ORDER BY {AGE_ORDER_SQL}, source_model
                """,
                [str(bayes_path)],
            ).fetchdf()
            atomic_csv(bayes_summary, bayes_summary_path)
            outputs["corrected_bayes_summary"] = bayes_summary_path

        schema_path = metrics_dir / "model_rows.schema.json"
        schema_record(connection, model_rows_path, schema_path)
        outputs["model_rows_schema"] = schema_path
        metric_audit = {
            "status": "PASS",
            "model_rows": int(connection.execute("SELECT count(*) FROM model_rows").fetchone()[0]),
            "contexts": int(connection.execute("SELECT count(DISTINCT context_id) FROM model_rows").fetchone()[0]),
            "children": int(connection.execute("SELECT count(DISTINCT child_key) FROM model_rows").fetchone()[0]),
            "corpora": int(connection.execute("SELECT count(DISTINCT dataset) FROM model_rows").fetchone()[0]),
            "qwen_responses_scanned": int(qwen_checks[0]),
            "exact_length_zero_support_rows": int(cloud_checks[3]),
            "exact_length_support_at_least_5": int(
                connection.execute("SELECT sum(exact_length_support>=5) FROM model_rows").fetchone()[0]
            ),
            "raw_nondominance_is_secondary": True,
            "bootstrap_draws": int(args.bootstrap_draws),
        }
        audit_path = metrics_dir / "metrics_audit.json"
        atomic_json(metric_audit, audit_path)
        outputs["audit"] = audit_path
        connection.close()

    manifest_path = metrics_dir / "metrics_manifest.json"
    inputs = {
        "dataset_manifest": dataset_manifest_path,
        "analysis_rows": analysis_path,
        "length_cells": length_cells_path,
        "upstream_candidates": candidates_path,
    }
    if bayes_path.exists():
        inputs["corrected_bayes_scores"] = bayes_path
    return write_manifest(
        stage="metrics",
        path=manifest_path,
        inputs=inputs,
        outputs=outputs,
        audit=metric_audit,
        extra={
            "qwen_root": str(args.qwen_root.resolve()),
            "qwen_core_glob": _qwen_glob(args.qwen_root, "core75"),
            "qwen_extension_glob": _qwen_glob(args.qwen_root, "extension25"),
        },
    )


def run_models_stage(args: argparse.Namespace) -> dict[str, Any]:
    metrics_manifest_path = args.output_dir / "metrics/metrics_manifest.json"
    metrics_manifest = require_manifest(metrics_manifest_path, "metrics")
    model_rows_csv = manifest_output(metrics_manifest, "gamm_rows_csv")
    if not MODEL_SCRIPT.exists():
        raise FileNotFoundError(MODEL_SCRIPT)
    model_dir = args.output_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    scope_contract = {
        "all79": "all",
        "pbm_discovery": "core",
        "non_pbm_confirmation": "core",
    }
    r_manifests: dict[str, dict[str, Any]] = {}
    output_paths: dict[str, Path] = {}
    for scope, model_set in scope_contract.items():
        scope_dir = model_dir / scope
        scope_dir.mkdir(parents=True, exist_ok=True)
        command = [
            "Rscript",
            str(MODEL_SCRIPT),
            "--input",
            str(model_rows_csv),
            "--output",
            str(scope_dir),
            "--threads",
            str(args.model_threads),
            "--scope",
            scope,
            "--model-set",
            model_set,
        ]
        subprocess.run(command, cwd=ROOT, check=True)
        r_manifest_path = scope_dir / "r_model_manifest.json"
        if not r_manifest_path.exists():
            raise RuntimeError(f"R model engine did not write its {scope} manifest")
        r_manifest = json.loads(r_manifest_path.read_text(encoding="utf-8"))
        if r_manifest.get("status") != "PASS" or r_manifest.get("analysis_scope") != scope:
            raise RuntimeError(f"R model engine failed its {scope} contract")
        r_manifests[scope] = r_manifest
        output_paths[f"{scope}__r_model_manifest"] = r_manifest_path
        for key, value in r_manifest["outputs"].items():
            output_paths[f"{scope}__{key}"] = Path(value["path"])

    combined_contract = {
        "model_registry": ("model_registry", model_dir / "combined_model_registry.csv"),
        "smooth_terms": ("smooth_terms", model_dir / "combined_smooth_terms.csv"),
        "parametric_terms": ("parametric_terms", model_dir / "combined_parametric_terms.csv"),
        "smooth_k_diagnostics": ("smooth_k_diagnostics", model_dir / "combined_smooth_k_diagnostics.csv"),
        "prediction_grids": ("prediction_grids", model_dir / "combined_prediction_grids.csv.gz"),
        "residual_diagnostics": ("residual_diagnostics", model_dir / "combined_residual_diagnostics.csv.gz"),
        "child_effects": ("child_effects", model_dir / "combined_child_effects.csv"),
        "model_contrasts": ("model_contrasts", model_dir / "combined_model_contrasts.csv"),
    }
    for output_name, (r_key, path) in combined_contract.items():
        frames = [pd.read_csv(manifest["outputs"][r_key]["path"]) for manifest in r_manifests.values()]
        atomic_csv(pd.concat(frames, ignore_index=True, sort=False), path)
        output_paths[output_name] = path

    registry_path = output_paths["model_registry"]
    registry = pd.read_csv(registry_path)
    problems = registry.loc[~registry["status"].eq("PASS"), "model_id"].astype(str).tolist()
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "registered_models": int(len(registry)),
        "passed_models": int(registry["status"].eq("PASS").sum()),
        "failed_models": problems,
        "engine": "mgcv::bam",
        "child_identity_controlled": bool(registry["formula"].str.contains("child_key").all()),
        "scope_model_counts": registry.groupby("analysis_scope").size().astype(int).to_dict(),
        "sample_roles": {
            "all79": "pooled_descriptive",
            "pbm_discovery": "discovery",
            "non_pbm_confirmation": "confirmation",
        },
    }
    if problems:
        raise RuntimeError(f"registered GAMM failures: {problems}")
    manifest_path = model_dir / "models_manifest.json"
    return write_manifest(
        stage="models",
        path=manifest_path,
        inputs={
            "metrics_manifest": metrics_manifest_path,
            "model_rows_csv": model_rows_csv,
            "r_model_script": MODEL_SCRIPT,
        },
        outputs=output_paths,
        audit=audit,
        extra={"scope_contract": scope_contract, "model_engine_manifests": r_manifests},
    )


def _savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()


def _scope_label(scope: str) -> str:
    return {
        "all79": "All 79 · pooled descriptive",
        "pbm_discovery": "PBM 21 · discovery",
        "non_pbm_confirmation": "Other 58 · confirmation",
    }.get(scope, scope)


def _plot_raw_bootstrap(bootstrap: pd.DataFrame, path: Path) -> None:
    contract = [
        ("child_words", "Child words"),
        ("child_words_minus_qwen_mean", "Child − Qwen expected words"),
        ("effort_percentile_in_qwen", "Effort percentile in Qwen"),
        ("k3_percentile_in_qwen", "k3 percentile in Qwen"),
        ("exact_length_k3_gap", "Child − exact-length Qwen k3 (bits)"),
        ("raw_nondominated", "Raw nondominated rate (secondary)"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(16, 8.8), constrained_layout=True)
    x = np.arange(len(AGE_BINS))
    for ax, (metric, label) in zip(axes.ravel(), contract):
        rows = bootstrap[bootstrap["metric"].eq(metric)].set_index("age_bin").reindex(AGE_BINS)
        estimate = rows["estimate"].to_numpy(float)
        low = rows["ci_low"].to_numpy(float)
        high = rows["ci_high"].to_numpy(float)
        ax.plot(x, estimate, color="#19647e", marker="o", lw=2.2)
        ax.fill_between(x, low, high, color="#19647e", alpha=0.18)
        if "percentile" in metric or metric == "raw_nondominated":
            ax.axhline(0.5, color="#777", ls="--", lw=1)
        elif "minus" in metric or "gap" in metric:
            ax.axhline(0, color="#777", ls="--", lw=1)
        ax.set_title(label)
        ax.set_xticks(x, AGE_BINS, rotation=35, ha="right")
        ax.grid(alpha=0.2)
    fig.suptitle("Whole-child bootstrap developmental summaries\npoints are child-balanced age-bin estimates; ribbons are 95% bootstrap intervals", fontsize=15)
    _savefig(path)


def _nearest_age_rows(frame: pd.DataFrame, target: float) -> pd.DataFrame:
    ages = np.sort(frame["age_months"].unique())
    selected = float(ages[np.argmin(np.abs(ages - target))])
    return frame[np.isclose(frame["age_months"], selected)].sort_values("response_entropy_bits")


def _plot_m1_entropy_lines(predictions: pd.DataFrame, path: Path) -> None:
    scopes = ["all79", "pbm_discovery", "non_pbm_confirmation"]
    ages = [18, 30, 42, 54, 60]
    colors = matplotlib.colormaps["viridis"](np.linspace(0.08, 0.92, len(ages)))
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.3), sharey=True, constrained_layout=True)
    for ax, scope in zip(axes, scopes):
        panel = predictions[(predictions.analysis_scope == scope) & (predictions.model_id == "m1_length_primary")]
        for target, color in zip(ages, colors):
            rows = _nearest_age_rows(panel, target)
            if rows.empty:
                continue
            actual = rows["age_months"].iloc[0]
            ax.plot(rows.response_entropy_bits, rows.estimate, color=color, lw=2, label=f"{actual:.0f} mo")
            ax.fill_between(rows.response_entropy_bits, rows.ci_low, rows.ci_high, color=color, alpha=0.08)
        ax.set_title(_scope_label(scope))
        ax.set_xlabel("Exact-string response entropy (bits)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Predicted child word count")
    axes[-1].legend(title="Age", frameon=False, fontsize=8)
    fig.suptitle("M1: adjusted response-length adaptation to generated response uncertainty", fontsize=15)
    _savefig(path)


def _plot_surface(panel: pd.DataFrame, x: str, y: str, z: str, ax: Any, title: str, cbar_label: str) -> None:
    pivot = panel.pivot_table(index=y, columns=x, values=z, aggfunc="mean").sort_index().sort_index(axis=1)
    image = ax.imshow(
        pivot.to_numpy(), origin="lower", aspect="auto", cmap="magma",
        extent=[pivot.columns.min(), pivot.columns.max(), pivot.index.min(), pivot.index.max()],
    )
    ax.set_title(title)
    ax.set_xlabel(x.replace("_", " "))
    ax.set_ylabel(y.replace("_", " "))
    colorbar = plt.colorbar(image, ax=ax, shrink=0.84)
    colorbar.set_label(cbar_label)


def _plot_m1_surface(predictions: pd.DataFrame, path: Path) -> None:
    panel = predictions[(predictions.analysis_scope == "all79") & (predictions.model_id == "m1_length_primary")]
    fig, ax = plt.subplots(figsize=(9.2, 6.4), constrained_layout=True)
    _plot_surface(panel, "age_months", "response_entropy_bits", "estimate", ax, "Pooled nonlinear length policy", "Predicted words")
    _savefig(path)


def _plot_m2_reference(predictions: pd.DataFrame, path: Path) -> None:
    panel = predictions[(predictions.analysis_scope == "all79") & (predictions.model_id == "m2_length_qwen_reference")]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    for ax, level in zip(axes, ["low", "median", "high"]):
        rows = panel[panel.reference_level.eq(level)]
        _plot_surface(rows, "age_months", "response_entropy_bits", "estimate", ax, f"Qwen expected length: {level}", "Predicted words")
    fig.suptitle("M2 sensitivity: response length after conditioning on generated expected length", fontsize=15)
    _savefig(path)


def _plot_length_calibration(calibration: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(16, 8.3), sharex=True, sharey=True, constrained_layout=True)
    limits = [0, max(calibration.qwen_expected_words.max(), calibration.mean_child_words.max()) * 1.05]
    for ax, age in zip(axes.ravel(), AGE_BINS):
        rows = calibration[calibration.age_bin.eq(age)].sort_values("qwen_expected_words")
        ax.fill_between(rows.qwen_expected_words, rows.p25_child_words, rows.p75_child_words, color="#2a9d8f", alpha=0.18)
        scatter = ax.scatter(rows.qwen_expected_words, rows.mean_child_words, c=rows.response_entropy, cmap="plasma", s=42, zorder=3)
        ax.plot(rows.qwen_expected_words, rows.mean_child_words, color="#2a9d8f", lw=1.5)
        ax.plot(limits, limits, color="#666", ls="--", lw=1)
        ax.set_title(age)
        ax.grid(alpha=0.18)
    for ax in axes[-1]:
        ax.set_xlabel("Qwen expected words")
    for ax in axes[:, 0]:
        ax.set_ylabel("Observed child words")
    fig.colorbar(scatter, ax=axes, label="Mean exact-string entropy", shrink=0.72)
    fig.suptitle("Length calibration by developmental period\npoints are Qwen-length deciles; bands are child-response IQRs", fontsize=15)
    _savefig(path)


def _plot_paper_atlas(atlas: pd.DataFrame, path: Path) -> None:
    source_order = ["observed_child", "qwen", "trigram", "bigram", "unigram", "random"]
    fig, axes = plt.subplots(2, 4, figsize=(18, 9.5), sharex=True, sharey=True, constrained_layout=True)
    for ax, age in zip(axes.ravel(), AGE_BINS):
        panel = atlas[atlas.age_bin.eq(age)]
        for source in source_order:
            rows = panel[panel.source.eq(source)].sort_values("word_count")
            if rows.empty:
                continue
            color = SOURCE_COLORS[source]
            ax.plot(rows.word_count, rows.median_k3, color=color, lw=2.6 if source == "observed_child" else 1.35, label=SOURCE_LABELS[source])
            ax.fill_between(rows.word_count, rows.p25_k3, rows.p75_k3, color=color, alpha=0.13 if source == "observed_child" else 0.055)
        ax.set_title(age)
        ax.set_xlim(1, 12)
        ax.set_xticks([1, 2, 4, 6, 8, 10, 12])
        ax.grid(alpha=0.18)
    for ax in axes[-1]:
        ax.set_xlabel("Exact cleaned-word length")
    for ax in axes[:, 0]:
        ax.set_ylabel("Mistral k3 total surprisal (bits)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=6, frameon=False)
    fig.suptitle("Paper-inspired all-model information × effort atlas\nline = median child-age cell; ribbon = interquartile range", fontsize=15)
    _savefig(path)


def _plot_m3_surfaces(predictions: pd.DataFrame, path: Path) -> None:
    scopes = ["all79", "pbm_discovery", "non_pbm_confirmation"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6), constrained_layout=True)
    for ax, scope in zip(axes, scopes):
        panel = predictions[(predictions.analysis_scope == scope) & (predictions.model_id == "m3_information_k3_total")]
        _plot_surface(panel, "age_months", "child_words", "estimate", ax, _scope_label(scope), "Predicted k3 bits")
    fig.suptitle("M3: contextual surprisal over age at fixed exact effort\nmedian response entropy and context length", fontsize=15)
    _savefig(path)


def _covariance_ellipse(ax: Any, x: np.ndarray, y: np.ndarray, color: Any) -> None:
    finite = np.isfinite(x) & np.isfinite(y)
    if finite.sum() < 3:
        return
    covariance = np.cov(x[finite], y[finite])
    values, vectors = np.linalg.eigh(covariance)
    order = values.argsort()[::-1]
    values, vectors = values[order], vectors[:, order]
    angle = np.degrees(np.arctan2(vectors[1, 0], vectors[0, 0]))
    width, height = 2 * np.sqrt(np.maximum(values, 0))
    ax.add_patch(Ellipse((np.mean(x[finite]), np.mean(y[finite])), width, height, angle=angle, edgecolor=color, facecolor="none", lw=1.8, alpha=0.75))


def _plot_joint_phase(child_cells: pd.DataFrame, path: Path) -> None:
    colors = matplotlib.colormaps["viridis"](np.linspace(0.04, 0.96, len(AGE_BINS)))
    fig, ax = plt.subplots(figsize=(9, 7), constrained_layout=True)
    for age, color in zip(AGE_BINS, colors):
        rows = child_cells[child_cells.age_bin.eq(age)]
        x = rows.effort_percentile_in_qwen.to_numpy(float)
        y = rows.k3_percentile_in_qwen.to_numpy(float)
        ax.scatter(x, y, s=18, color=color, alpha=0.28)
        _covariance_ellipse(ax, x, y, color)
        ax.plot(np.nanmean(x), np.nanmean(y), marker="o", ms=8, color=color, label=age)
    ax.axvline(0.5, color="#777", ls="--", lw=1)
    ax.axhline(0.5, color="#777", ls="--", lw=1)
    ax.set(xlabel="Child effort percentile in its Qwen context", ylabel="Child k3 percentile in its Qwen context")
    ax.grid(alpha=0.18)
    ax.legend(title="Age bin", ncol=2, frameon=False, fontsize=8)
    ax.set_title("Joint context-relative phase portrait\nsmall points = child-age cells; ellipses = one-SD covariance contours")
    _savefig(path)


def _plot_m4_entropy_lines(predictions: pd.DataFrame, path: Path) -> None:
    scopes = ["all79", "pbm_discovery", "non_pbm_confirmation"]
    ages = [18, 30, 42, 54, 60]
    colors = matplotlib.colormaps["viridis"](np.linspace(0.08, 0.92, len(ages)))
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.3), sharey=True, constrained_layout=True)
    for ax, scope in zip(axes, scopes):
        panel = predictions[(predictions.analysis_scope == scope) & (predictions.model_id == "m4_effort_percentile")]
        for target, color in zip(ages, colors):
            rows = _nearest_age_rows(panel, target)
            if rows.empty:
                continue
            ax.plot(rows.response_entropy_bits, rows.estimate, color=color, lw=2, label=f"{rows.age_months.iloc[0]:.0f} mo")
            ax.fill_between(rows.response_entropy_bits, rows.ci_low, rows.ci_high, color=color, alpha=0.08)
        ax.axhline(0.5, color="#777", ls="--", lw=1)
        ax.set_title(_scope_label(scope))
        ax.set_xlabel("Exact-string response entropy (bits)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Predicted Qwen-relative effort percentile")
    axes[-1].legend(title="Age", frameon=False, fontsize=8)
    fig.suptitle("M4: relative-effort adaptation changes over development", fontsize=15)
    _savefig(path)


def _plot_gap_and_nondominance(bootstrap: pd.DataFrame, predictions: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), constrained_layout=True)
    for ax, metric, title, baseline in [
        (axes[0], "exact_length_k3_gap", "Exact-length child − Qwen k3 gap", 0),
        (axes[1], "raw_nondominated", "Raw nondominated rate (secondary)", 0.5),
    ]:
        rows = bootstrap[bootstrap.metric.eq(metric)].set_index("age_bin").reindex(AGE_BINS)
        x = np.arange(len(AGE_BINS))
        ax.errorbar(rows.estimate, x, xerr=[rows.estimate - rows.ci_low, rows.ci_high - rows.estimate], fmt="o-", color="#19647e", capsize=3)
        ax.axvline(baseline, color="#777", ls="--", lw=1)
        ax.set_yticks(x, AGE_BINS)
        ax.invert_yaxis()
        ax.set_xlabel(title)
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle("Conditional information comparison and the explicitly secondary raw Pareto diagnostic\nwhole-child bootstrap 95% intervals", fontsize=14)
    _savefig(path)


def _plot_child_heterogeneity(child_effects: pd.DataFrame, path: Path) -> None:
    panel = child_effects[child_effects.analysis_scope.eq("all79")]
    contract = [
        ("m1_length_primary", "age_change_per_month", "Length: age change / month"),
        ("m1_length_primary", "entropy_change_per_bit", "Length: entropy change / bit"),
        ("m3_information_k3_total", "age_change_per_month", "k3: age change / month"),
        ("m3_information_k3_total", "entropy_change_per_bit", "k3: entropy change / bit"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    for ax, (model, column, label) in zip(axes.ravel(), contract):
        rows = panel[panel.model_id.eq(model)].sort_values(column).reset_index(drop=True)
        ax.scatter(np.arange(len(rows)), rows[column], c=rows[column], cmap="coolwarm", s=24)
        ax.axhline(0, color="#555", ls="--", lw=1)
        ax.set_title(label)
        ax.set_xlabel("Children ordered by shrunken predicted effect")
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Child heterogeneity retained by random intercepts and random age/entropy slopes\nmodel-based conditional effects; not 79 independent significance tests", fontsize=14)
    _savefig(path)


def _plot_bayes_sidecar(bayes: pd.DataFrame, path: Path) -> None:
    sources = ["real", "trigram", "bigram", "unigram", "random"]
    colors = {"real": "#111111", "trigram": "#2563eb", "bigram": "#2ca25f", "unigram": "#f59e0b", "random": "#d73027"}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), constrained_layout=True)
    x = np.arange(len(AGE_BINS))
    for source in sources:
        rows = bayes[bayes.source_model.eq(source)].set_index("age_bin").reindex(AGE_BINS)
        axes[0].plot(x, rows.median_log2_prior, marker="o", color=colors[source], label=source)
        axes[1].plot(x, rows.median_context_evidence, marker="o", color=colors[source], label=source)
    axes[0].set_ylabel("Median cross-fitted log2 prior")
    axes[1].set_ylabel("Median cross-fitted context evidence")
    for ax in axes:
        ax.set_xticks(x, AGE_BINS, rotation=35, ha="right")
        ax.grid(alpha=0.2)
    axes[1].legend(frameon=False)
    fig.suptitle("Corrected PBM Bayes decomposition sidecar\nseparate from the all-79 direct-Mistral analysis", fontsize=14)
    _savefig(path)


def _plot_diagnostics(residuals: pd.DataFrame, path: Path) -> None:
    models = ["m1_length_primary", "m3_information_k3_total", "m4_effort_percentile", "m5_exact_length_k3_gap"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    for ax, model in zip(axes.ravel(), models):
        rows = residuals[(residuals.analysis_scope.eq("all79")) & (residuals.model_id.eq(model))]
        ax.hexbin(rows.fitted, rows.deviance_residual, gridsize=45, mincnt=1, cmap="viridis", bins="log")
        ax.axhline(0, color="#555", ls="--", lw=1)
        ax.set(title=model, xlabel="Fitted value", ylabel="Deviance residual")
    fig.suptitle("Registered model residual diagnostics (fixed reproducible samples)", fontsize=14)
    _savefig(path)


def _plot_scope_contrasts(contrasts: pd.DataFrame, path: Path) -> None:
    scopes = ["all79", "pbm_discovery", "non_pbm_confirmation"]
    labels = [_scope_label(scope) for scope in scopes]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2), constrained_layout=True)
    panels = [
        ("m1_length_primary", "entropy_p10_to_p90", "42", "ratio", "Length ratio: entropy p10 → p90 at 42 mo"),
        ("m3_information_k3_total", "age_min_to_max", "2", "difference", "k3 difference: supported age endpoints at 2 words"),
        ("m4_effort_percentile", "entropy_p10_to_p90", "42", "ratio", "Effort-percentile odds ratio at 42 mo"),
    ]
    for ax, (model, comparison, moderator, scale, title) in zip(axes, panels):
        selected = contrasts[(contrasts.model_id.eq(model)) & (contrasts.comparison.eq(comparison)) & (contrasts.moderator_value.astype(str).eq(moderator))].set_index("analysis_scope")
        for position, scope in enumerate(scopes):
            if scope not in selected.index:
                continue
            row = selected.loc[scope]
            if scale == "ratio":
                estimate, low, high, null = row.ratio_or_odds_ratio, row.ratio_or_odds_ci_low, row.ratio_or_odds_ci_high, 1
            else:
                estimate, low, high, null = row.response_difference, row.link_ci_low, row.link_ci_high, 0
            ax.errorbar(estimate, position, xerr=[[estimate - low], [high - estimate]], fmt="o", color="#19647e", capsize=4)
        ax.axvline(null, color="#666", ls="--", lw=1)
        ax.set_yticks(range(len(scopes)), labels)
        ax.invert_yaxis()
        ax.set_title(title, fontsize=10)
        ax.grid(axis="x", alpha=0.2)
    fig.suptitle("Covariance-aware adjusted contrasts across frozen sample roles", fontsize=14)
    _savefig(path)


def _plot_context_gallery(contexts: pd.DataFrame, responses: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(18, 9), constrained_layout=True)
    for ax, row in zip(axes.ravel(), contexts.sort_values("age_months").itertuples(index=False)):
        panel = responses[responses.context_id.eq(row.context_id)]
        qwen = panel[panel.source.eq("qwen")]
        ax.scatter(qwen.word_count, qwen.k3_sum_bits, s=13, color="#aab0b5", alpha=0.42, label="Qwen")
        for source in ["random", "unigram", "bigram", "trigram"]:
            points = panel[panel.source.eq(source)]
            if not points.empty:
                ax.scatter(points.word_count, points.k3_sum_bits, marker="x", s=46, color=SOURCE_COLORS[source])
        child = panel[panel.source.eq("observed_child")]
        ax.scatter(child.word_count, child.k3_sum_bits, marker="*", s=150, color="#111", edgecolor="white", linewidth=0.7, zorder=5)
        ax.set_title(f"{row.age_bin} · {row.child_key}\nage {row.age_months:.1f}", fontsize=9)
        ax.set_xlabel("Words")
        ax.set_ylabel("k3 bits")
        ax.grid(alpha=0.16)
    fig.suptitle("Eight audited context-matched response clouds\nQwen responses do not preserve the observed child's intended meaning", fontsize=14)
    _savefig(path)


def _plot_raw_length_age_lines(atlas: pd.DataFrame, path: Path) -> None:
    source_order = ["observed_child", "qwen", "trigram", "bigram", "unigram", "random"]
    lengths = list(range(1, 13))
    colors = matplotlib.colormaps["viridis"](np.linspace(0.03, 0.97, len(lengths)))
    x = np.arange(len(AGE_BINS))
    fig, axes = plt.subplots(2, 3, figsize=(17, 9.5), sharex=True, constrained_layout=True)
    for ax, source in zip(axes.ravel(), source_order):
        panel = atlas[atlas.source.eq(source)]
        for length, color in zip(lengths, colors):
            rows = panel[panel.word_count.eq(length)].set_index("age_bin").reindex(AGE_BINS)
            ax.plot(x, rows.median_k3, color=color, lw=1.35, marker="o", ms=2.8, label=str(length))
        ax.set_title(SOURCE_LABELS[source])
        ax.set_ylabel("Median k3 total surprisal")
        ax.grid(alpha=0.18)
    for ax in axes[-1]:
        ax.set_xticks(x, AGE_BINS, rotation=35, ha="right")
        ax.set_xlabel("Developmental period")
    handles = [plt.Line2D([0], [0], color=color, lw=2, label=f"{length} words") for length, color in zip(lengths, colors)]
    fig.legend(handles=handles, loc="outside lower center", ncol=6, frameon=False, fontsize=8)
    fig.suptitle("Raw model × exact length trajectories over age\neach line is one exact length; panel-specific y scales", fontsize=15)
    _savefig(path)


def _plot_adjusted_length_age_lines(predictions: pd.DataFrame, path: Path) -> None:
    scopes = ["all79", "pbm_discovery", "non_pbm_confirmation"]
    lengths = [1, 2, 4, 6, 8, 10, 12]
    colors = matplotlib.colormaps["viridis"](np.linspace(0.03, 0.97, len(lengths)))
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    for ax, scope in zip(axes, scopes):
        panel = predictions[(predictions.analysis_scope.eq(scope)) & (predictions.model_id.eq("m3_information_k3_total"))]
        for length, color in zip(lengths, colors):
            rows = panel[panel.child_words.eq(length)].sort_values("age_months")
            ax.plot(rows.age_months, rows.estimate, color=color, lw=2, label=f"{length} words")
            ax.fill_between(rows.age_months, rows.ci_low, rows.ci_high, color=color, alpha=0.05)
        ax.set_title(_scope_label(scope))
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Adjusted k3 total surprisal")
        ax.grid(alpha=0.18)
    axes[-1].legend(frameon=False, fontsize=8, ncol=2)
    fig.suptitle("M3 regression trajectories: one line per exact word length\nchild identity, corpus, response entropy, and context length controlled", fontsize=15)
    _savefig(path)


def run_plots_stage(args: argparse.Namespace) -> dict[str, Any]:
    metrics_manifest_path = args.output_dir / "metrics/metrics_manifest.json"
    models_manifest_path = args.output_dir / "models/models_manifest.json"
    metrics_manifest = require_manifest(metrics_manifest_path, "metrics")
    models_manifest = require_manifest(models_manifest_path, "models")
    args.fig_dir.mkdir(parents=True, exist_ok=True)

    def metric(name: str) -> pd.DataFrame:
        return pd.read_csv(manifest_output(metrics_manifest, name))

    predictions = pd.read_csv(manifest_output(models_manifest, "prediction_grids"))
    residuals = pd.read_csv(manifest_output(models_manifest, "residual_diagnostics"))
    child_effects = pd.read_csv(manifest_output(models_manifest, "child_effects"))
    contrasts = pd.read_csv(manifest_output(models_manifest, "model_contrasts"))
    child_cells_path = manifest_output(metrics_manifest, "child_age_metric_cells")
    with duckdb.connect() as connection:
        child_cells = connection.execute("SELECT * FROM read_parquet(?)", [str(child_cells_path)]).fetchdf()

    gallery_contexts_path = args.upstream_dir / "metrics/gallery_contexts.csv"
    gallery_responses_path = args.upstream_dir / "metrics/gallery_responses.csv.gz"
    gallery_contexts = pd.read_csv(gallery_contexts_path)
    gallery_responses = pd.read_csv(gallery_responses_path)

    catalog = [
        ("developmental_distributions", "Developmental distributions", "development", _plot_raw_bootstrap, [metric("child_bootstrap_age_trajectories")]),
        ("m1_entropy_lines", "Adjusted response-length adaptation", "adaptation", _plot_m1_entropy_lines, [predictions]),
        ("m1_policy_surface", "Pooled joint length policy", "adaptation", _plot_m1_surface, [predictions]),
        ("m2_qwen_reference", "Generated expected-length sensitivity", "adaptation", _plot_m2_reference, [predictions]),
        ("length_calibration", "Observed versus generated expected length", "adaptation", _plot_length_calibration, [metric("length_calibration")]),
        ("paper_information_effort_atlas", "Paper-inspired model × length × age atlas", "information", _plot_paper_atlas, [metric("paper_atlas_distribution")]),
        ("m3_fixed_effort_surfaces", "Fixed-effort contextual surprisal", "information", _plot_m3_surfaces, [predictions]),
        ("joint_phase_portrait", "Joint context-relative phase portrait", "cloud", _plot_joint_phase, [child_cells]),
        ("m4_relative_effort", "Relative effort by uncertainty and age", "cloud", _plot_m4_entropy_lines, [predictions]),
        ("gap_and_nondominance", "Exact-length gap and raw nondominance", "cloud", _plot_gap_and_nondominance, [metric("child_bootstrap_age_trajectories"), predictions]),
        ("child_heterogeneity", "Child-specific developmental heterogeneity", "heterogeneity", _plot_child_heterogeneity, [child_effects]),
        ("bayes_decomposition", "Corrected PBM Bayes sidecar", "robustness", _plot_bayes_sidecar, [metric("corrected_bayes_summary")]),
        ("model_diagnostics", "Model diagnostics", "diagnostics", _plot_diagnostics, [residuals]),
        ("scope_contrasts", "Discovery/confirmation contrast forest", "robustness", _plot_scope_contrasts, [contrasts]),
        ("context_gallery", "Context-matched response-cloud examples", "cloud", _plot_context_gallery, [gallery_contexts, gallery_responses]),
        ("raw_model_length_age_lines", "Raw model × length trajectories", "information", _plot_raw_length_age_lines, [metric("paper_atlas_distribution")]),
        ("adjusted_length_age_lines", "Adjusted one-line-per-length trajectories", "information", _plot_adjusted_length_age_lines, [predictions]),
    ]
    rows: list[dict[str, Any]] = []
    outputs: dict[str, Path] = {}
    for index, (plot_id, title, group, function, function_args) in enumerate(catalog, start=1):
        path = args.fig_dir / f"{index:02d}_{plot_id}.png"
        function(*function_args, path)
        outputs[plot_id] = path
        rows.append({"plot_id": plot_id, "title": title, "group": group, "path": str(path.resolve()), "bytes": path.stat().st_size, "status": "PASS"})

    plot_dir = args.output_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = plot_dir / "figure_catalog.csv"
    atomic_csv(pd.DataFrame(rows), catalog_path)
    outputs["figure_catalog"] = catalog_path
    audit = {"status": "PASS", "registered_figures": len(catalog), "passed_figures": len(rows), "groups": sorted({row["group"] for row in rows})}
    audit_path = plot_dir / "plot_audit.json"
    atomic_json(audit, audit_path)
    outputs["audit"] = audit_path
    manifest_path = plot_dir / "plots_manifest.json"
    return write_manifest(
        stage="plots", path=manifest_path,
        inputs={
            "metrics_manifest": metrics_manifest_path,
            "models_manifest": models_manifest_path,
            "gallery_contexts": gallery_contexts_path,
            "gallery_responses": gallery_responses_path,
        },
        outputs=outputs, audit=audit,
    )


def run_report_stage(args: argparse.Namespace) -> dict[str, Any]:
    metrics_manifest_path = args.output_dir / "metrics/metrics_manifest.json"
    models_manifest_path = args.output_dir / "models/models_manifest.json"
    plots_manifest_path = args.output_dir / "plots/plots_manifest.json"
    metrics_manifest = require_manifest(metrics_manifest_path, "metrics")
    models_manifest = require_manifest(models_manifest_path, "models")
    plots_manifest = require_manifest(plots_manifest_path, "plots")

    correlations = pd.read_csv(manifest_output(metrics_manifest, "raw_correlations")).iloc[0]
    age_summary = pd.read_csv(manifest_output(metrics_manifest, "age_distribution_summary"))
    bootstrap = pd.read_csv(manifest_output(metrics_manifest, "child_bootstrap_age_trajectories"))
    registry = pd.read_csv(manifest_output(models_manifest, "model_registry"))
    contrasts = pd.read_csv(manifest_output(models_manifest, "model_contrasts"))
    figures = pd.read_csv(manifest_output(plots_manifest, "figure_catalog"))
    contexts = pd.read_csv(args.upstream_dir / "metrics/gallery_contexts.csv")
    responses = pd.read_csv(args.upstream_dir / "metrics/gallery_responses.csv.gz")

    def contrast(model: str, comparison: str, moderator: str, scope: str = "all79") -> pd.Series:
        selected = contrasts[
            contrasts.model_id.eq(model)
            & contrasts.comparison.eq(comparison)
            & contrasts.analysis_scope.eq(scope)
            & contrasts.moderator_value.astype(str).eq(str(moderator))
        ]
        if selected.empty:
            raise RuntimeError(f"missing registered contrast: {scope}/{model}/{comparison}/{moderator}")
        return selected.iloc[0]

    m1_all = contrast("m1_length_primary", "entropy_p10_to_p90", "42")
    m1_pbm = contrast("m1_length_primary", "entropy_p10_to_p90", "42", "pbm_discovery")
    m1_non = contrast("m1_length_primary", "entropy_p10_to_p90", "42", "non_pbm_confirmation")
    m4_all = contrast("m4_effort_percentile", "entropy_p10_to_p90", "42")
    m4_pbm = contrast("m4_effort_percentile", "entropy_p10_to_p90", "42", "pbm_discovery")
    m4_non = contrast("m4_effort_percentile", "entropy_p10_to_p90", "42", "non_pbm_confirmation")
    m3_all = contrast("m3_information_k3_total", "age_min_to_max", "2")
    m3_pbm = contrast("m3_information_k3_total", "age_min_to_max", "2", "pbm_discovery")
    m3_non = contrast("m3_information_k3_total", "age_min_to_max", "2", "non_pbm_confirmation")
    m5_high = contrast("m5_exact_length_k3_gap", "age_min_to_max", "high")

    descriptions = {
        "developmental_distributions": "Child-balanced raw trajectories for effort, Qwen-relative position, exact-length k3 gap, and the secondary nondominance flag.",
        "m1_entropy_lines": "Negative-binomial GAMM predictions show how absolute response length changes with exact-string response entropy at several ages and in each frozen sample role.",
        "m1_policy_surface": "One pooled surface for the conditional length policy over developmental age and response-space uncertainty.",
        "m2_qwen_reference": "Sensitivity surfaces add Qwen expected response length; this is a distinct reference-adjusted estimand, not the primary total association.",
        "length_calibration": "Observed length is compared with the complete generated length distribution rather than only one generated mean.",
        "paper_information_effort_atlas": "Every age panel contains every source and exact length 1–12: x is effort and y is contextual Mistral surprisal.",
        "m3_fixed_effort_surfaces": "The nonlinear age-by-length surface directly tests predictability at fixed exact effort in pooled, discovery, and confirmation scopes.",
        "joint_phase_portrait": "Child-age cells jointly locate effort percentile and surprisal percentile inside their context-matched generated response spaces.",
        "m4_relative_effort": "The Qwen-relative effort response to entropy reverses over development instead of following one universal increasing line.",
        "gap_and_nondominance": "Exact-length comparison is kept separate from raw nondominance; neither generated reference preserves intended meaning.",
        "child_heterogeneity": "Shrunken child-specific age and entropy responses show why a pooled mean is incomplete.",
        "bayes_decomposition": "Cross-fitted PBM priors and context evidence are a decomposition sidecar, not a Bayesian hierarchical fit and not all-79 evidence.",
        "model_diagnostics": "Fixed residual samples expose outcome-specific fit structure for the registered nonlinear models.",
        "scope_contrasts": "Covariance-aware contrasts keep pooled description, PBM discovery, and other-58 confirmation visibly separate.",
        "context_gallery": "Eight complete 100-response examples make the context-matching operation concrete and expose meaning-preservation limits.",
        "raw_model_length_age_lines": "This reconstructs the earlier readable 2D logic: every exact length is its own line over age, with a separate panel for each source model.",
        "adjusted_length_age_lines": "The registered M3 predictions retain one line per exact length while controlling child identity, corpus, response entropy, and context length.",
    }
    figure_records = []
    for row in figures.itertuples(index=False):
        path = Path(row.path)
        relative = os.path.relpath(path, start=args.report_html.parent)
        figure_records.append({
            "id": row.plot_id,
            "title": row.title,
            "group": row.group,
            "src": relative,
            "description": descriptions[row.plot_id],
        })

    headline = {
        "raw_child_entropy_correlation": float(correlations.child_length_entropy),
        "raw_qwen_entropy_correlation": float(correlations.qwen_length_entropy),
        "m1_age42_length_ratio": float(m1_all.ratio_or_odds_ratio),
        "m1_age42_length_ratio_ci": [float(m1_all.ratio_or_odds_ci_low), float(m1_all.ratio_or_odds_ci_high)],
        "m4_age42_effort_odds_ratio": float(m4_all.ratio_or_odds_ratio),
        "m4_age42_effort_odds_ci": [float(m4_all.ratio_or_odds_ci_low), float(m4_all.ratio_or_odds_ci_high)],
        "m3_two_word_age_difference_bits": float(m3_all.response_difference),
        "m3_two_word_age_difference_ci": [float(m3_all.link_ci_low), float(m3_all.link_ci_high)],
        "exact_length_supported_rows": int(metrics_manifest["audit"]["exact_length_support_at_least_5"]),
    }
    payload = {
        "generated_at": utc_now(),
        "headline": headline,
        "figures": figure_records,
        "models": registry.replace({np.nan: None}).to_dict(orient="records"),
        "contexts": contexts.replace({np.nan: None}).to_dict(orient="records"),
        "responses": responses.replace({np.nan: None}).to_dict(orient="records"),
        "sample": {"rows": 1_122_396, "contexts": 645_524, "children": 79, "corpora": 13, "qwen_responses": 64_552_400},
    }

    def ratio_text(row: pd.Series) -> str:
        return f"{row.ratio_or_odds_ratio:.3f} (95% CI {row.ratio_or_odds_ci_low:.3f}–{row.ratio_or_odds_ci_high:.3f})"

    def diff_text(row: pd.Series) -> str:
        return f"{row.response_difference:+.2f} bits (95% CI {row.link_ci_low:+.2f} to {row.link_ci_high:+.2f})"

    md_figure_lines = []
    for record in figure_records:
        md_figure_lines.extend([f"### {record['title']}", "", f"![{record['title']}]({record['src']})", "", record["description"], ""])
    markdown = f"""# Conditional joint efficiency in child responses

## What this analysis asks

Longer is not automatically worse. The analysis estimates the joint policy of
response length and scorer predictability conditional on conversational demand
and child age. It combines 1,122,396 child utterances from 79 children with the
complete 100-response Qwen cloud for each of 645,524 contexts.

## Main results

1. **Absolute length adapts only modestly to exact-string response entropy.** At
   42 months, the pooled M1 predicted length ratio from entropy p10 to p90 is
   {ratio_text(m1_all)}. The PBM discovery ratio is {ratio_text(m1_pbm)}; the
   other-58 confirmation ratio is {ratio_text(m1_non)}.
2. **Relative effort reverses with development.** At 42 months, the pooled M4
   effort-percentile odds ratio is {ratio_text(m4_all)}, with the same direction
   in PBM discovery ({ratio_text(m4_pbm)}) and other-58 confirmation
   ({ratio_text(m4_non)}). Near 18 months the adjusted direction is positive;
   later it is mostly negative or weak. The simple prediction that children
   always lengthen *relative to Qwen* as entropy rises is therefore not supported.
3. **At fixed exact effort, older speech is more predictable for common short
   lengths.** For two-word utterances, the pooled supported-range age contrast
   is {diff_text(m3_all)}; PBM discovery is {diff_text(m3_pbm)} and the other-58
   confirmation result is {diff_text(m3_non)}. Longer, sparse cells are visibly
   less stable and are not generalized.
4. **Same-length generated comparison adds a different result.** Child targets
   remain more surprising than Qwen's median generated response at the same
   length in raw summaries. Under high response entropy, M5 estimates a
   developmental reduction of {abs(m5_high.response_difference):.2f} bits
   (95% CI {m5_high.link_ci_low:+.2f} to {m5_high.link_ci_high:+.2f}). This is a
   model-relative form comparison, not evidence that generated alternatives
   preserve what the child meant.

## Interpretation boundary

- Mistral surprisal is scorer self-information: lower means more predictable,
  not “more Shannon information transmitted.”
- Response entropy is exact-string entropy under one Qwen prompt and sampling
  procedure. It is not semantic uncertainty.
- Raw Qwen nondominance is secondary. It is not a Pareto-optimality claim and
  does not preserve intended meaning.
- Pooled all-79 estimates are descriptive. Brown/Manchester/Providence are
  discovery; the other 58 children are confirmation.
- The corrected PBM Bayes result decomposes a cross-fitted prior and context
  evidence over a supplied candidate set. It is separate from the GAMMs.

## Figures

{os.linesep.join(md_figure_lines)}
## Registered analysis

The model stage fitted 15/15 registered `mgcv::bam` models: nine pooled models
and unchanged M1/M3/M4 core models in discovery and confirmation. Every model
contains a child random intercept, child random age slope, child random entropy
slope, and corpus random intercept. Plotting and this report consume saved
tables and never refit models.

## Reproducibility

The independent stages are `datasets → metrics → models → plots → report →
audit`. Each stage has a hash-bound manifest. The final completion marker is
written only after the separate audit checks sample coverage, all 15 models,
all registered figures, report links, and interpretation guardrails.
"""
    atomic_text(markdown, args.report_md)

    plot_cards = "".join(
        f"<article class='plot-card' data-group='{html.escape(item['group'])}' data-title='{html.escape(item['title'])}'>"
        f"<button class='plot-open' data-src='{html.escape(item['src'])}' data-caption='{html.escape(item['description'])}'>"
        f"<img loading='lazy' src='{html.escape(item['src'])}' alt='{html.escape(item['title'])}'></button>"
        f"<div class='plot-copy'><span>{html.escape(item['group'])}</span><h3>{html.escape(item['title'])}</h3><p>{html.escape(item['description'])}</p></div></article>"
        for item in figure_records
    )
    model_rows = "".join(
        f"<tr><td>{html.escape(_scope_label(str(row.analysis_scope)))}</td><td><code>{html.escape(str(row.model_id))}</code></td>"
        f"<td>{html.escape(str(row.family))}</td><td>{int(row.n_rows):,}</td><td>{float(row.deviance_explained):.3f}</td><td>{html.escape(str(row.status))}</td></tr>"
        for row in registry.itertuples(index=False)
    )
    embedded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    document = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Conditional joint efficiency · full-79 explorer</title><style>
:root{{--ink:#172126;--muted:#5d6970;--paper:#fff;--soft:#f3f6f5;--line:#d9e1df;--teal:#176b73;--gold:#d58a28;--purple:#6f5aa8}}*{{box-sizing:border-box}}body{{margin:0;background:#eef3f1;color:var(--ink);font:15.5px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}}nav{{position:sticky;top:0;z-index:9;display:flex;gap:18px;align-items:center;padding:11px max(20px,calc((100vw - 1180px)/2));background:rgba(255,255,255,.94);border-bottom:1px solid var(--line);backdrop-filter:blur(8px)}}nav strong{{margin-right:auto}}nav a{{color:var(--teal);text-decoration:none;font-weight:650}}main{{max-width:1180px;margin:auto;background:var(--paper);box-shadow:0 18px 60px rgba(20,40,36,.09)}}header{{padding:70px 64px 46px;background:linear-gradient(135deg,#123f47,#176b73 58%,#609e8b);color:white}}.eyebrow,.plot-copy span{{text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;font-weight:800}}h1{{font-size:clamp(2.4rem,6vw,5rem);line-height:.98;max-width:900px;margin:.2em 0}}header p{{font-size:1.18rem;max-width:830px;color:#e3f1ed}}.stats,.finding-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.stat,.finding{{border:1px solid var(--line);border-radius:13px;padding:17px;background:white}}.stats{{margin-top:30px}}.stat{{background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.3)}}.stat b{{display:block;font-size:1.55rem}}section{{padding:44px 64px;border-bottom:1px solid var(--line)}}h2{{font-size:2rem;margin:.1em 0 .45em}}h3{{line-height:1.25}}.lede{{font-size:1.08rem;color:var(--muted);max-width:900px}}.finding-grid{{grid-template-columns:repeat(2,1fr);margin-top:22px}}.finding{{border-top:4px solid var(--teal)}}.finding b{{color:var(--teal)}}.guard{{background:#fff8e9;border-left:5px solid var(--gold);padding:18px 22px;margin:22px 0}}.chips{{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}}.chip{{border:1px solid var(--line);background:white;border-radius:999px;padding:8px 13px;cursor:pointer}}.chip.active{{background:var(--teal);color:white;border-color:var(--teal)}}.plot-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.plot-card{{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:white;box-shadow:0 6px 20px rgba(20,40,36,.05)}}.plot-open{{display:block;width:100%;padding:0;border:0;background:#fafafa;cursor:zoom-in}}.plot-card img{{width:100%;height:290px;object-fit:contain;display:block}}.plot-copy{{padding:17px}}.plot-copy span{{color:var(--teal)}}.plot-copy h3{{margin:.35em 0}}.plot-copy p{{color:var(--muted);margin-bottom:0}}.context-layout{{display:grid;grid-template-columns:290px 1fr;gap:20px}}select{{width:100%;padding:10px;border:1px solid var(--line);border-radius:8px;background:white}}canvas{{width:100%;height:auto;border:1px solid var(--line);border-radius:10px;background:white}}#contextText,#responseList{{font-size:.88rem;color:var(--muted)}}table{{width:100%;border-collapse:collapse;font-size:.86rem}}th,td{{padding:8px;border-bottom:1px solid var(--line);text-align:left}}th{{position:sticky;top:43px;background:#eaf1ef}}.table-wrap{{max-height:530px;overflow:auto;border:1px solid var(--line);border-radius:10px}}code{{background:var(--soft);padding:2px 5px;border-radius:4px}}dialog{{width:min(1100px,95vw);border:0;border-radius:14px;padding:16px;box-shadow:0 25px 80px #0008}}dialog img{{width:100%;max-height:78vh;object-fit:contain}}dialog button{{float:right;border:0;background:#eee;border-radius:50%;width:34px;height:34px;cursor:pointer}}footer{{padding:35px 64px;color:var(--muted)}}@media(max-width:760px){{header,section,footer{{padding:32px 22px}}.stats,.finding-grid,.plot-grid{{grid-template-columns:1fr}}.context-layout{{grid-template-columns:1fr}}nav a{{display:none}}}}
</style></head><body><nav><strong>Joint efficiency explorer</strong><a href='#results'>Results</a><a href='#plots'>Plots</a><a href='#contexts'>Contexts</a><a href='#models'>Models</a></nav><main>
<header><div class='eyebrow'>All-79 child language · conditional joint analysis</div><h1>Longer is not always worse.</h1><p>Response effort is modeled as an adaptive choice under conversational uncertainty, while predictability is tested at fixed exact effort. Every observed utterance is located inside its own complete 100-response generated cloud.</p><div class='stats'><div class='stat'><b>1,122,396</b>child utterances</div><div class='stat'><b>645,524</b>contexts</div><div class='stat'><b>64.55M</b>Qwen responses</div><div class='stat'><b>15 / 15</b>GAMMs passed</div></div></header>
<section id='results'><div class='eyebrow'>Main results</div><h2>A conditional story, not a shortest-answer story</h2><p class='lede'>The adjusted results distinguish absolute length, length relative to the response distribution, and contextual Mistral surprisal at the same exact length.</p><div class='finding-grid'>
<article class='finding'><b>Absolute effort</b><h3>Higher entropy predicts a small length increase</h3><p>At 42 months, entropy p10→p90 changes pooled predicted length from {m1_all.from_response:.2f} to {m1_all.to_response:.2f} words: ratio {ratio_text(m1_all)}. PBM is {ratio_text(m1_pbm)}; the other-58 interval is {ratio_text(m1_non)}.</p></article>
<article class='finding'><b>Relative effort</b><h3>The entropy response reverses with age</h3><p>At 42 months, the pooled effort-percentile odds ratio is {ratio_text(m4_all)}; PBM and other-58 fits have the same negative direction. Near 18 months it is positive. Children do not increasingly lengthen relative to Qwen at every age.</p></article>
<article class='finding'><b>Fixed effort</b><h3>Common short utterances become more predictable</h3><p>For two-word utterances, the supported-range age contrast is {diff_text(m3_all)} pooled, {diff_text(m3_pbm)} in discovery, and {diff_text(m3_non)} in confirmation. Sparse long lengths are not generalized.</p></article>
<article class='finding'><b>Exact-length cloud</b><h3>Generated alternatives are a reference, not intentions</h3><p>{headline['exact_length_supported_rows']:,} observations have at least five exact-length generated comparisons. Under high entropy, the child-minus-Qwen median k3 gap declines by {abs(m5_high.response_difference):.2f} bits across the supported age range.</p></article></div>
<div class='guard'><strong>Interpretation boundary.</strong> Lower Mistral surprisal means more scorer-predictable form, not more Shannon information transmitted. Exact-string response entropy is not semantic uncertainty. Raw Qwen nondominance is secondary, not proof of a Pareto optimum, and the generated response set does not preserve intended meaning.</div></section>
<section id='plots'><div class='eyebrow'>Visual evidence</div><h2>Plot browser</h2><p class='lede'>Choose a family, then click any figure to inspect it at full resolution. Plotting reads frozen metric and model artifacts and performs no fitting.</p><div class='chips'><button class='chip active' data-group='all'>All</button><button class='chip' data-group='adaptation'>Length adaptation</button><button class='chip' data-group='information'>Fixed effort</button><button class='chip' data-group='cloud'>Joint cloud</button><button class='chip' data-group='heterogeneity'>Children</button><button class='chip' data-group='robustness'>Robustness</button><button class='chip' data-group='diagnostics'>Diagnostics</button></div><div class='plot-grid'>{plot_cards}</div></section>
<section id='contexts'><div class='eyebrow'>Context microscope</div><h2>Inspect complete 100-response clouds</h2><p class='lede'>These eight audited examples show exactly what the generated comparison means. Select a context to inspect the child response and all alternatives.</p><div class='context-layout'><aside><label for='contextSelect'>Child context</label><select id='contextSelect'></select><h3>Observed child response</h3><div id='contextText'></div><h3>Nearest generated forms</h3><div id='responseList'></div></aside><canvas id='contextCanvas' width='820' height='530'></canvas></div></section>
<section id='models'><div class='eyebrow'>Registered models</div><h2>Discovery and confirmation remain separate</h2><p class='lede'>All 79 is pooled descriptive. Brown, Manchester, and Providence form PBM discovery; the other 58 children form confirmation. Every formula controls stable child identity and allows child-specific age and entropy responses.</p><div class='table-wrap'><table><thead><tr><th>Sample role</th><th>Model</th><th>Family</th><th>Rows</th><th>Deviance explained</th><th>Status</th></tr></thead><tbody>{model_rows}</tbody></table></div></section>
<section><div class='eyebrow'>Bayes sidecar</div><h2>A decomposition, not the regression engine</h2><p class='lede'>The corrected PBM product separates a leave-corpus-out prior from whole-utterance context evidence and normalizes only over each supplied matched candidate set. It is not an all-79 posterior over possible utterances, and it is not a Bayesian hierarchical GAMM.</p></section>
<footer>Independent pipeline: datasets → metrics → models → plots → report → audit. This browser document is generated entirely from saved local artifacts.</footer></main>
<dialog id='modal'><button id='closeModal'>×</button><img id='modalImage' alt='Expanded plot'><p id='modalCaption'></p></dialog>
<script>const DATA={embedded};const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];$$('.chip').forEach(b=>b.onclick=()=>{{$$('.chip').forEach(x=>x.classList.remove('active'));b.classList.add('active');const g=b.dataset.group;$$('.plot-card').forEach(c=>c.hidden=g!=='all'&&c.dataset.group!==g)}});const modal=$('#modal');$$('.plot-open').forEach(b=>b.onclick=()=>{{$('#modalImage').src=b.dataset.src;$('#modalCaption').textContent=b.dataset.caption;modal.showModal()}});$('#closeModal').onclick=()=>modal.close();
const sel=$('#contextSelect'),canvas=$('#contextCanvas'),ctx=canvas.getContext('2d');DATA.contexts.sort((a,b)=>a.age_months-b.age_months).forEach((c,i)=>{{const o=document.createElement('option');o.value=c.context_id;o.textContent=`${{c.age_bin}} · ${{c.child_key}} · ${{c.age_months.toFixed(1)}} mo`;sel.appendChild(o)}});function drawContext(){{const id=sel.value,c=DATA.contexts.find(x=>x.context_id===id),rows=DATA.responses.filter(x=>x.context_id===id),q=rows.filter(x=>x.source==='qwen'),child=rows.find(x=>x.source==='observed_child');const xs=rows.map(x=>x.word_count),ys=rows.map(x=>x.k3_sum_bits),xmin=Math.min(...xs)-.5,xmax=Math.max(...xs)+.5,ymin=Math.min(...ys)-3,ymax=Math.max(...ys)+3,px=x=>55+(x-xmin)/(xmax-xmin||1)*735,py=y=>475-(y-ymin)/(ymax-ymin||1)*420;ctx.clearRect(0,0,820,530);ctx.fillStyle='white';ctx.fillRect(0,0,820,530);ctx.strokeStyle='#d9e1df';for(let i=0;i<6;i++){{const y=55+i*84;ctx.beginPath();ctx.moveTo(55,y);ctx.lineTo(790,y);ctx.stroke()}};q.forEach(r=>{{ctx.fillStyle='rgba(110,120,125,.38)';ctx.beginPath();ctx.arc(px(r.word_count),py(r.k3_sum_bits),4,0,Math.PI*2);ctx.fill()}});const colors={{random:'#d73027',unigram:'#f59e0b',bigram:'#2ca25f',trigram:'#2563eb'}};rows.filter(r=>colors[r.source]).forEach(r=>{{ctx.strokeStyle=colors[r.source];ctx.lineWidth=2;const x=px(r.word_count),y=py(r.k3_sum_bits);ctx.beginPath();ctx.moveTo(x-6,y-6);ctx.lineTo(x+6,y+6);ctx.moveTo(x+6,y-6);ctx.lineTo(x-6,y+6);ctx.stroke()}});ctx.fillStyle='#111';ctx.beginPath();ctx.arc(px(child.word_count),py(child.k3_sum_bits),9,0,Math.PI*2);ctx.fill();ctx.font='13px system-ui';ctx.fillText('Word effort →',360,518);ctx.save();ctx.translate(15,330);ctx.rotate(-Math.PI/2);ctx.fillText('Mistral k3 surprisal →',0,0);ctx.restore();ctx.fillText('● child    · Qwen    × n-gram/random',520,25);$('#contextText').innerHTML=`<strong>“${{child.target_text||'(text unavailable)'}}”</strong><br>${{child.word_count}} words · ${{child.k3_sum_bits.toFixed(2)}} k3 bits<br>effort percentile ${{c.effort_percentile_in_qwen.toFixed(3)}} · k3 percentile ${{c.k3_percentile_in_qwen.toFixed(3)}}`;const nearest=[...q].sort((a,b)=>(Math.abs(a.word_count-child.word_count)+Math.abs(a.k3_sum_bits-child.k3_sum_bits)/10)-(Math.abs(b.word_count-child.word_count)+Math.abs(b.k3_sum_bits-child.k3_sum_bits)/10)).slice(0,5);$('#responseList').innerHTML=nearest.map(r=>`<p>“${{r.target_text}}”<br>${{r.word_count}} words · ${{r.k3_sum_bits.toFixed(2)}} bits</p>`).join('')}}sel.onchange=drawContext;drawContext();</script></body></html>"""
    atomic_text(document, args.report_html)

    report_dir = args.output_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    payload_path = report_dir / "report_payload.json"
    atomic_json(payload, payload_path)
    audit = {
        "status": "PASS",
        "figure_cards": len(figure_records),
        "registered_models_rendered": len(registry),
        "interactive_contexts": len(contexts),
        "interactive_responses": len(responses),
    }
    audit_path = report_dir / "report_audit.json"
    atomic_json(audit, audit_path)
    manifest_path = report_dir / "report_manifest.json"
    return write_manifest(
        stage="report", path=manifest_path,
        inputs={"metrics_manifest": metrics_manifest_path, "models_manifest": models_manifest_path, "plots_manifest": plots_manifest_path},
        outputs={"markdown": args.report_md, "html": args.report_html, "payload": payload_path, "audit": audit_path},
        audit=audit,
    )


def run_audit_stage(args: argparse.Namespace) -> dict[str, Any]:
    stage_paths = {
        "datasets": args.output_dir / "datasets/dataset_manifest.json",
        "metrics": args.output_dir / "metrics/metrics_manifest.json",
        "models": args.output_dir / "models/models_manifest.json",
        "plots": args.output_dir / "plots/plots_manifest.json",
        "report": args.output_dir / "report/report_manifest.json",
    }
    manifests = {stage: require_manifest(path, stage) for stage, path in stage_paths.items()}
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, observed: Any, expected: Any) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "observed": str(observed), "expected": str(expected)})

    dataset_audit = manifests["datasets"]["audit"]
    for field, expected in {
        "rows": args.expected_eligible_rows,
        "unique_utterances": args.expected_eligible_rows,
        "contexts": args.expected_contexts,
        "children": args.expected_children,
        "corpora": args.expected_corpora,
    }.items():
        check(f"dataset_{field}", int(dataset_audit[field]) == expected, dataset_audit[field], expected)
    invalid_total = sum(int(value) for key, value in dataset_audit.items() if key.startswith("invalid_"))
    check("dataset_invalid_values", invalid_total == 0, invalid_total, 0)

    metric_audit = manifests["metrics"]["audit"]
    check("metrics_status", metric_audit.get("status") == "PASS", metric_audit.get("status"), "PASS")
    check("qwen_response_scan", int(metric_audit["qwen_responses_scanned"]) == args.expected_qwen_responses, metric_audit["qwen_responses_scanned"], args.expected_qwen_responses)
    check("exact_length_supported", int(metric_audit["exact_length_support_at_least_5"]) > 0, metric_audit["exact_length_support_at_least_5"], "> 0")
    check("raw_nondominance_secondary", metric_audit.get("raw_nondominance_is_secondary") is True, metric_audit.get("raw_nondominance_is_secondary"), True)

    registry = pd.read_csv(manifest_output(manifests["models"], "model_registry"))
    check("registered_models", len(registry) == 15, len(registry), 15)
    check("model_passes", registry.status.eq("PASS").all(), int(registry.status.eq("PASS").sum()), 15)
    check("model_convergence", registry.converged.astype(bool).all(), int(registry.converged.astype(bool).sum()), 15)
    scope_counts = registry.groupby("analysis_scope").size().to_dict()
    check("scope_contract", scope_counts == {"all79": 9, "non_pbm_confirmation": 3, "pbm_discovery": 3}, scope_counts, {"all79": 9, "non_pbm_confirmation": 3, "pbm_discovery": 3})
    for term in ["s(child_key", "s(child_key, age_z", "s(child_key, entropy_z", "s(dataset"]:
        check(f"formula_control_{term}", registry.formula.str.contains(term, regex=False).all(), int(registry.formula.str.contains(term, regex=False).sum()), 15)
    contrasts = pd.read_csv(manifest_output(manifests["models"], "model_contrasts"))
    check("covariance_contrasts", len(contrasts) >= 100 and contrasts.link_se.notna().all(), len(contrasts), ">= 100 finite-SE rows")
    k_diagnostics = pd.read_csv(manifest_output(manifests["models"], "smooth_k_diagnostics"))
    minimum_k = float(k_diagnostics["k.index"].dropna().min())
    check("smooth_basis_k_index", minimum_k > 0.90, f"{minimum_k:.3f}", "> 0.90")

    figures = pd.read_csv(manifest_output(manifests["plots"], "figure_catalog"))
    check("registered_figures", len(figures) == 17, len(figures), 17)
    figure_integrity = True
    for row in figures.itertuples(index=False):
        path = Path(row.path)
        figure_integrity &= path.exists() and path.stat().st_size > 20_000 and path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    check("png_integrity", figure_integrity, figure_integrity, True)

    report_html = manifest_output(manifests["report"], "html")
    report_md = manifest_output(manifests["report"], "markdown")
    document = report_html.read_text(encoding="utf-8")
    markdown = report_md.read_text(encoding="utf-8")
    broken_images = []
    for source in re.findall(r"<img[^>]+src=['\"]([^'\"]+)", document):
        target = (report_html.parent / source).resolve()
        if not target.exists():
            broken_images.append(source)
    check("report_image_links", not broken_images, broken_images, "none")
    for anchor in ["results", "plots", "contexts", "models"]:
        check(f"report_anchor_{anchor}", f"id='{anchor}'" in document, f"id='{anchor}'" in document, True)
    guardrails = {
        "exact_string_not_semantic": "Exact-string response entropy is not semantic uncertainty",
        "meaning_not_preserved": "does not preserve intended meaning",
        "nondominance_secondary": "Raw Qwen nondominance is secondary",
        "pooled_descriptive": "pooled descriptive",
        "discovery": "discovery",
        "confirmation": "confirmation",
        "lower_surprisal_definition": "Lower Mistral surprisal means more scorer-predictable form",
    }
    for name, phrase in guardrails.items():
        check(f"guardrail_{name}", phrase.lower() in document.lower(), phrase if phrase.lower() in document.lower() else "missing", phrase)
    check("markdown_source_substantive", len(markdown.splitlines()) > 100, len(markdown.splitlines()), "> 100 lines")
    scripts = re.findall(r"<script>(.*?)</script>", document, flags=re.DOTALL)
    node = subprocess.run(["node", "--check", "-"], input="\n".join(scripts), text=True, capture_output=True)
    check("javascript_syntax", node.returncode == 0, node.stderr.strip() or "valid", "valid")
    report_audit = manifests["report"]["audit"]
    check("interactive_contexts", int(report_audit["interactive_contexts"]) == 8, report_audit["interactive_contexts"], 8)
    check("interactive_responses", int(report_audit["interactive_responses"]) == 840, report_audit["interactive_responses"], 840)

    audit_dir = args.output_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    checks_frame = pd.DataFrame(checks)
    checks_path = audit_dir / "audit_checks.csv"
    atomic_csv(checks_frame, checks_path)
    failures = checks_frame.loc[checks_frame.status.eq("FAIL"), "check"].tolist()
    final_audit = {
        "status": "PASS" if not failures else "FAIL",
        "completed_at": utc_now(),
        "checks": len(checks),
        "passed": int(checks_frame.status.eq("PASS").sum()),
        "failed": failures,
        "stage_manifest_sha256": {stage: sha256_file(path) for stage, path in stage_paths.items()},
        "scientific_status": {
            "all79": "pooled_descriptive",
            "pbm": "discovery",
            "non_pbm": "confirmation",
            "response_entropy": "exact_string_not_semantic",
            "raw_nondominance": "secondary_not_intended_meaning_optimality",
        },
    }
    final_audit_path = audit_dir / "final_audit.json"
    atomic_json(final_audit, final_audit_path)
    if failures:
        raise RuntimeError(f"final audit failed: {failures}")

    marker = args.output_dir / "FULL79_JOINT_EFFICIENCY_COMPLETE_AND_AUDITED"
    atomic_text(json.dumps(final_audit, indent=2, sort_keys=True) + "\n", marker)
    manifest_path = audit_dir / "audit_manifest.json"
    return write_manifest(
        stage="audit", path=manifest_path,
        inputs=stage_paths,
        outputs={"checks": checks_path, "final_audit": final_audit_path, "completion_marker": marker},
        audit={"status": "PASS", "checks": len(checks), "passed": len(checks), "failed": []},
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["datasets", "metrics", "models", "plots", "report", "audit", "all"], default="all")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--upstream-dir", type=Path, default=UPSTREAM)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIGURES)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--qwen-root", type=Path, default=DEFAULT_QWEN_ROOT)
    parser.add_argument("--bayes-scores", type=Path, default=DEFAULT_BAYES)
    parser.add_argument("--temp-dir", type=Path, default=Path("/tmp"))
    parser.add_argument("--duckdb-memory-limit", default="6GB")
    parser.add_argument("--model-threads", type=int, default=4)
    parser.add_argument("--bootstrap-draws", type=int, default=500)
    parser.add_argument("--bootstrap-seed", type=int, default=20260825)
    parser.add_argument("--expected-eligible-rows", type=int, default=1_122_396)
    parser.add_argument("--expected-contexts", type=int, default=645_524)
    parser.add_argument("--expected-qwen-responses", type=int, default=64_552_400)
    parser.add_argument("--expected-children", type=int, default=79)
    parser.add_argument("--expected-corpora", type=int, default=13)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stages = ["datasets", "metrics", "models", "plots", "report", "audit"] if args.stage == "all" else [args.stage]
    for stage in stages:
        print(f"[{stage}] starting", flush=True)
        if stage == "datasets":
            run_datasets_stage(args)
        elif stage == "metrics":
            run_metrics_stage(args)
        elif stage == "models":
            run_models_stage(args)
        elif stage == "plots":
            run_plots_stage(args)
        elif stage == "report":
            run_report_stage(args)
        elif stage == "audit":
            run_audit_stage(args)
        print(f"[{stage}] complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
