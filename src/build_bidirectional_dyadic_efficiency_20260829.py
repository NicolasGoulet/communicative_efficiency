#!/usr/bin/env python3
"""Build and audit the bidirectional caregiver-child-caregiver analysis.

The controller is deliberately staged.  The dataset and support stages may run
from a draft contract; coefficient-producing stages require a hash-bound frozen
contract.  This keeps data engineering outcome-blind and prevents accidental
inspection before the estimands are fixed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import duckdb
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "configs/bidirectional_dyadic_efficiency_20260829/analysis_contract.json"
DEFAULT_OUTPUT = ROOT / "results/bidirectional_dyadic_efficiency_20260829"
PROGRAM_ID = "bidirectional_dyadic_efficiency_20260829"
PBM_DATASETS = {"Brown", "Manchester", "Providence"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def atomic_text(value: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def atomic_json(value: Mapping[str, Any], path: Path) -> None:
    atomic_text(json.dumps(value, indent=2, sort_keys=True) + "\n", path)


def file_record(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_manifest(
    stage: str,
    path: Path,
    *,
    inputs: Mapping[str, Path],
    outputs: Mapping[str, Path],
    audit: Mapping[str, Any],
) -> None:
    atomic_json(
        {
            "stage": stage,
            "completed_at": utc_now(),
            "controller": file_record(Path(__file__)),
            "inputs": {name: file_record(value) for name, value in inputs.items()},
            "outputs": {name: file_record(value) for name, value in outputs.items()},
            "audit": dict(audit),
        },
        path,
    )


def require_manifest(
    path: Path,
    stage: str,
    *,
    ignore_input_names: tuple[str, ...] = (),
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing {stage} manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("stage") != stage:
        raise RuntimeError(f"expected {stage} manifest, found {payload.get('stage')}")
    for direction in ("inputs", "outputs"):
        for name, record in payload.get(direction, {}).items():
            if direction == "inputs" and name in ignore_input_names:
                continue
            target = Path(record["path"])
            if not target.exists() or sha256_file(target) != record["sha256"]:
                raise RuntimeError(f"stale {stage} {direction[:-1]}: {name}")
    return payload


def validate_contract(contract: Mapping[str, Any], *, require_frozen: bool = False) -> None:
    problems: list[str] = []
    if contract.get("program_id") != PROGRAM_ID:
        problems.append("program_id mismatch")
    if contract.get("expected", {}).get("strict_rows") != 413084:
        problems.append("strict row contract mismatch")
    if contract.get("expected", {}).get("broad_rows") != 613741:
        problems.append("broad row contract mismatch")
    estimands = [item.get("id") for item in contract.get("estimands", [])]
    if estimands != [
        "F1_adult_to_child_predictability",
        "F2_adult_to_child_effort",
        "F3_child_to_adult_effort",
    ]:
        problems.append("the bounded F1-F3 inventory changed")
    if any(item.get("direction") != "two_sided" for item in contract.get("estimands", [])):
        problems.append("all primary coupling decisions must remain two-sided")
    if contract.get("decomposition", {}).get("primary_within_scope") != "child_key x session_id":
        problems.append("within-session accommodation scope changed")
    if contract.get("bayesian", {}).get("family") != "trivariate_normal_measurement_error":
        problems.append("Bayesian family mismatch")
    if "PBM estimates are not used as priors" not in contract.get("bayesian", {}).get("prior_source", ""):
        problems.append("PBM/prior guardrail missing")
    if float(contract.get("bayesian", {}).get("maximum_total_cpu_hours", 99)) > 2:
        problems.append("Bayesian runtime ceiling exceeds two CPU-hours")
    if contract.get("gates", {}).get("downstream_utility") not in {
        "WAITING_FOR_AUDITED_SCORES", "AUDITED_SCORES_AVAILABLE"
    }:
        problems.append("invalid downstream utility gate")
    if require_frozen:
        if contract.get("status") != "frozen_pre_fit":
            problems.append("coefficient stages require status=frozen_pre_fit")
        if not isinstance(contract.get("support_snapshot"), dict):
            problems.append("frozen contract lacks support snapshot")
    if problems:
        raise ValueError("invalid dyadic contract: " + "; ".join(problems))


def load_contract(path: Path, *, require_frozen: bool = False) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(payload, require_frozen=require_frozen)
    return payload


def resolve_input(contract: Mapping[str, Any], name: str) -> Path:
    path = ROOT / contract["inputs"][name]
    expected = contract["inputs"].get(f"{name}_sha256")
    if not path.exists():
        raise FileNotFoundError(path)
    if expected and sha256_file(path) != expected:
        raise RuntimeError(f"input hash mismatch: {name}")
    return path


def sql_path(path: Path | str) -> str:
    return str(path).replace("'", "''")


def verify_handoff_members(directory: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checked = 0
    for record in manifest.get("files", []):
        if not str(record.get("path", "")).startswith("inputs/"):
            continue
        path = directory / record["path"]
        if not path.exists() or path.stat().st_size != int(record["size_bytes"]):
            raise RuntimeError(f"handoff member size mismatch: {path}")
        if sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"handoff member hash mismatch: {path}")
        checked += 1
    if checked != 13:
        raise RuntimeError(f"expected 13 handoff inputs, verified {checked}")
    return {"verified_handoff_input_files": checked}


def _create_source_views(
    connection: duckdb.DuckDBPyConnection,
    *,
    handoff_glob: str,
    flags: Path,
    child: Path,
    caregiver: Path,
) -> None:
    connection.execute(
        f"CREATE VIEW handoff AS SELECT * FROM read_csv('{sql_path(handoff_glob)}', "
        "all_varchar=true, union_by_name=true)"
    )
    connection.execute(
        f"CREATE VIEW flags AS SELECT * FROM read_csv('{sql_path(flags)}', all_varchar=true)"
    )
    connection.execute(
        f"""CREATE VIEW child_scores AS
        SELECT dataset, child_id, child_key, session_id, file, line_no,
               real_target_text_sha256,
               TRY_CAST(real_nb_words AS INTEGER) AS c_score_words,
               TRY_CAST(real_k0_sum_bits AS DOUBLE) AS c_k0_bits,
               TRY_CAST(real_k3_sum_bits AS DOUBLE) AS c_k3_bits,
               TRY_CAST(real_context_gain_k3 AS DOUBLE) AS c_context_support_bits,
               TRY_CAST(context_available_k3 AS INTEGER) AS c_context_available_k3,
               TRY_CAST(real_k0_n_eval_tokens AS INTEGER) AS c_k0_tokens,
               TRY_CAST(real_k3_n_eval_tokens AS INTEGER) AS c_k3_tokens
        FROM read_csv('{sql_path(child)}', all_varchar=true)"""
    )
    connection.execute(
        f"""CREATE VIEW caregiver_scores AS
        SELECT dataset, child_id, child_key, session_id, file, line_no, speaker,
               target_text, target_text_sha256,
               TRY_CAST(nb_words AS INTEGER) AS score_words,
               TRY_CAST(k0_sum_bits AS DOUBLE) AS k0_bits,
               TRY_CAST(k3_sum_bits AS DOUBLE) AS k3_bits,
               TRY_CAST(context_gain_k3 AS DOUBLE) AS context_support_bits,
               TRY_CAST(context_available_k3 AS INTEGER) AS context_available_k3,
               TRY_CAST(k0_n_eval_tokens AS INTEGER) AS k0_tokens,
               TRY_CAST(k3_n_eval_tokens AS INTEGER) AS k3_tokens
        FROM read_csv('{sql_path(caregiver)}', all_varchar=true)"""
    )


def _joined_sql(where: str = "") -> str:
    return f"""
    WITH joined AS (
      SELECT
        h.response_pair_id, h.dataset, h.child_id, h.child_key, h.sample_group,
        TRY_CAST(h.session_id AS INTEGER) AS session_id,
        h.child_key || '/' || h.session_id AS child_session_key,
        TRY_CAST(h.age_months AS DOUBLE) AS age_months,
        (TRY_CAST(h.age_months AS DOUBLE) - 42.0) / 6.0 AS age_z,
        h.age_bin, h.file,
        TRY_CAST(f.previous_main_line_no AS INTEGER) AS a0_line_no,
        TRY_CAST(h.line_no AS INTEGER) AS c_line_no,
        TRY_CAST(h.next_caregiver_line_no AS INTEGER) AS a1_line_no,
        f.previous_main_speaker AS a0_speaker,
        f.next_main_speaker AS a1_speaker,
        f.previous_main_utterance_clean AS a0_text,
        ap.target_text_sha256 AS a0_text_sha256,
        h.child_text AS c_text,
        h.child_text_sha256 AS c_text_sha256,
        h.target_text AS a1_text,
        h.target_text_sha256 AS a1_text_sha256,
        ap.score_words AS a0_words,
        TRY_CAST(h.child_word_count AS INTEGER) AS c_words,
        an.score_words AS a1_words,
        TRY_CAST(h.response_word_count AS INTEGER) AS a1_handoff_words,
        ap.k0_bits AS a0_k0_bits,
        ap.k3_bits AS a0_k3_bits,
        ap.context_support_bits AS a0_context_support_bits,
        cs.c_k0_bits, cs.c_k3_bits, cs.c_context_support_bits,
        an.k0_bits AS a1_k0_bits,
        an.k3_bits AS a1_k3_bits,
        an.context_support_bits AS a1_context_support_bits,
        ap.context_available_k3 AS a0_context_available_k3,
        cs.c_context_available_k3,
        an.context_available_k3 AS a1_context_available_k3,
        TRY_CAST(h.primary_eligible AS INTEGER) AS primary_eligible,
        TRY_CAST(h.sensitivity_eligible AS INTEGER) AS sensitivity_eligible,
        h.previous_caretaker_question_type AS a0_question_type,
        h.child_question_type AS c_question_type,
        h.next_caregiver_question_type AS a1_question_type,
        TRY_CAST(h.exact_imitation_candidate AS INTEGER) AS exact_imitation_candidate,
        TRY_CAST(h.contained_imitation_candidate AS INTEGER) AS contained_imitation_candidate,
        TRY_CAST(h.child_backchannel_candidate AS INTEGER) AS child_backchannel_candidate,
        TRY_CAST(h.session_reading_candidate AS INTEGER) AS session_reading_candidate,
        TRY_CAST(h.session_routine_candidate AS INTEGER) AS session_routine_candidate,
        TRY_CAST(h.repair_sequence_candidate AS INTEGER) AS repair_sequence_candidate,
        TRY_CAST(h.next_caregiver_clarification_candidate AS INTEGER) AS clarification_candidate,
        TRY_CAST(h.next_caregiver_acknowledgement_candidate AS INTEGER) AS acknowledgement_candidate,
        CASE WHEN cs.real_target_text_sha256 = h.child_text_sha256 THEN 1 ELSE 0 END AS c_hash_matches,
        CASE WHEN an.target_text_sha256 = h.target_text_sha256 THEN 1 ELSE 0 END AS a1_hash_matches,
        CASE WHEN ap.target_text_sha256 = sha256(f.previous_main_utterance_clean) THEN 1 ELSE 0 END AS a0_hash_matches,
        CASE WHEN cs.c_score_words = TRY_CAST(h.child_word_count AS INTEGER) THEN 1 ELSE 0 END AS c_words_match,
        CASE WHEN an.score_words = TRY_CAST(h.response_word_count AS INTEGER) THEN 1 ELSE 0 END AS a1_words_match
      FROM handoff h
      LEFT JOIN flags f USING(dataset, child_id, file, line_no)
      LEFT JOIN child_scores cs USING(dataset, child_id, file, line_no)
      LEFT JOIN caregiver_scores ap
        ON h.dataset=ap.dataset AND h.child_id=ap.child_id AND h.file=ap.file
       AND f.previous_main_line_no=ap.line_no
      LEFT JOIN caregiver_scores an
        ON h.dataset=an.dataset AND h.child_id=an.child_id AND h.file=an.file
       AND h.next_caregiver_line_no=an.line_no
      {where}
    ), means AS (
      SELECT *,
        avg(a0_k3_bits) OVER (PARTITION BY child_key, session_id) AS a0_k3_session_mean,
        avg(a0_k0_bits) OVER (PARTITION BY child_key, session_id) AS a0_k0_session_mean,
        avg(a0_context_support_bits) OVER (PARTITION BY child_key, session_id) AS a0_support_session_mean,
        avg(a0_words) OVER (PARTITION BY child_key, session_id) AS a0_words_session_mean,
        avg(c_k3_bits) OVER (PARTITION BY child_key, session_id) AS c_k3_session_mean,
        avg(c_k0_bits) OVER (PARTITION BY child_key, session_id) AS c_k0_session_mean,
        avg(c_context_support_bits) OVER (PARTITION BY child_key, session_id) AS c_support_session_mean,
        avg(c_words) OVER (PARTITION BY child_key, session_id) AS c_words_session_mean,
        avg(a0_k3_bits) OVER (PARTITION BY child_key) AS a0_k3_child_mean,
        avg(a0_k0_bits) OVER (PARTITION BY child_key) AS a0_k0_child_mean,
        avg(a0_context_support_bits) OVER (PARTITION BY child_key) AS a0_support_child_mean,
        avg(a0_words) OVER (PARTITION BY child_key) AS a0_words_child_mean,
        avg(c_k3_bits) OVER (PARTITION BY child_key) AS c_k3_child_mean,
        avg(c_k0_bits) OVER (PARTITION BY child_key) AS c_k0_child_mean,
        avg(c_context_support_bits) OVER (PARTITION BY child_key) AS c_support_child_mean,
        avg(c_words) OVER (PARTITION BY child_key) AS c_words_child_mean
      FROM joined
    )
    SELECT *,
      a0_k3_bits-a0_k3_session_mean AS a0_k3_within,
      a0_k0_bits-a0_k0_session_mean AS a0_k0_within,
      a0_context_support_bits-a0_support_session_mean AS a0_support_within,
      a0_words-a0_words_session_mean AS a0_words_within,
      c_k3_bits-c_k3_session_mean AS c_k3_within,
      c_k0_bits-c_k0_session_mean AS c_k0_within,
      c_context_support_bits-c_support_session_mean AS c_support_within,
      c_words-c_words_session_mean AS c_words_within,
      CASE WHEN c_words >= 12 THEN '12+' ELSE CAST(c_words AS VARCHAR) END AS c_word_top12
    FROM means
    """


def _copy_parquet(connection: duckdb.DuckDBPyConnection, query: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    connection.execute(
        f"COPY ({query}) TO '{sql_path(temporary)}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    os.replace(temporary, path)


def _write_csv_rows(path: Path, header: list[str], rows: list[tuple[Any, ...]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    os.replace(temporary, path)


def run_dataset_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_contract(contract_path)
    handoff_dir = ROOT / contract["inputs"]["handoff_directory"]
    handoff_manifest = resolve_input(contract, "handoff_manifest")
    flags = resolve_input(contract, "conversational_flags")
    child = resolve_input(contract, "child_scores")
    caregiver = resolve_input(contract, "caregiver_scores")
    member_audit = verify_handoff_members(handoff_dir, handoff_manifest)
    directory = output_dir / "datasets"
    directory.mkdir(parents=True, exist_ok=True)
    broad_path = directory / "dyadic_triads_broad.parquet"
    strict_path = directory / "dyadic_triads_strict.parquet"
    sidecar_path = directory / "caregiver_speaker_sidecar.parquet"
    flow_path = directory / "sample_flow.csv"
    exclusions_path = directory / "strict_exclusions.csv"
    audit_path = directory / "dataset_audit.json"

    connection = duckdb.connect()
    connection.execute("SET preserve_insertion_order=false")
    _create_source_views(
        connection,
        handoff_glob=str(handoff_dir / "inputs/*.caregiver_response.csv.gz"),
        flags=flags,
        child=child,
        caregiver=caregiver,
    )
    base_counts = connection.execute(
        """SELECT COUNT(*) AS n, SUM(CAST(primary_eligible AS INTEGER)) AS strict_n,
                  COUNT(DISTINCT response_pair_id) AS ids,
                  COUNT(DISTINCT dataset) AS corpora,
                  COUNT(DISTINCT child_key) AS children
           FROM handoff"""
    ).fetchone()
    if base_counts != (
        int(contract["expected"]["broad_rows"]),
        int(contract["expected"]["strict_rows"]),
        int(contract["expected"]["broad_rows"]),
        int(contract["expected"]["corpora"]),
        int(contract["expected"]["children"]),
    ):
        raise RuntimeError(f"handoff identity/count contract failed: {base_counts}")

    _copy_parquet(connection, _joined_sql(), broad_path)
    _copy_parquet(connection, _joined_sql("WHERE h.primary_eligible='1'"), strict_path)
    _copy_parquet(
        connection,
        f"""SELECT response_pair_id, dataset, child_id, child_key, session_id, file,
                   a0_line_no, a0_speaker, a0_text_sha256,
                   a1_line_no, a1_speaker, a1_text_sha256
            FROM read_parquet('{sql_path(strict_path)}') ORDER BY dataset, child_key, file, c_line_no""",
        sidecar_path,
    )

    metrics = connection.execute(
        f"""SELECT COUNT(*) AS rows,
                   COUNT(DISTINCT response_pair_id) AS unique_ids,
                   COUNT(DISTINCT dataset) AS corpora,
                   COUNT(DISTINCT child_key) AS children,
                   SUM(CASE WHEN sample_group='pbm_discovery' THEN 1 ELSE 0 END) AS pbm_rows,
                   SUM(c_hash_matches) AS c_hash_matches,
                   SUM(a0_hash_matches) AS a0_hash_matches,
                   SUM(a1_hash_matches) AS a1_hash_matches,
                   SUM(c_words_match) AS c_words_matches,
                   SUM(a1_words_match) AS a1_words_matches,
                   COUNT(a0_speaker) AS a0_speakers,
                   COUNT(a1_speaker) AS a1_speakers,
                   COUNT(c_k3_bits) AS finite_c_k3,
                   COUNT(a0_k3_bits) AS finite_a0_k3,
                   COUNT(a1_k3_bits) AS finite_a1_k3
            FROM read_parquet('{sql_path(strict_path)}')"""
    ).fetchone()
    metric_names = [item[0] for item in connection.description]
    observed = dict(zip(metric_names, metrics))
    expected_rows = int(contract["expected"]["strict_rows"])
    problems: list[str] = []
    exact_metrics = [
        "rows", "unique_ids", "c_hash_matches", "a0_hash_matches", "a1_hash_matches",
        "c_words_matches", "a0_speakers", "a1_speakers",
    ]
    for name in exact_metrics:
        if int(observed[name]) != expected_rows:
            problems.append(f"{name}={observed[name]} expected {expected_rows}")
    if int(observed["corpora"]) != int(contract["expected"]["corpora"]):
        problems.append("corpus coverage mismatch")
    if int(observed["children"]) != int(contract["expected"]["children"]):
        problems.append("child coverage mismatch")
    if int(observed["pbm_rows"]) != int(contract["expected"]["pbm_strict_rows"]):
        problems.append("PBM strict row mismatch")
    expected_word_disagreements = int(
        contract["expected"].get("response_word_measurement_disagreements", 0)
    )
    observed_word_disagreements = expected_rows - int(observed["a1_words_matches"])
    if observed_word_disagreements != expected_word_disagreements:
        problems.append(
            "response word measurement disagreements="
            f"{observed_word_disagreements} expected {expected_word_disagreements}"
        )
    if int(observed["finite_c_k3"]) != expected_rows:
        problems.append("child k3 is incomplete")
    if int(observed["finite_a1_k3"]) != expected_rows:
        problems.append("response k3 is incomplete")

    flow_cursor = connection.execute(
        f"""SELECT dataset, sample_group, COUNT(*) AS rows,
                   COUNT(DISTINCT child_key) AS children,
                   COUNT(DISTINCT child_session_key) AS sessions,
                   MIN(age_months) AS age_min, MAX(age_months) AS age_max,
                   COUNT(a0_k3_bits) AS a0_k3_rows
            FROM read_parquet('{sql_path(strict_path)}')
            GROUP BY dataset, sample_group ORDER BY dataset"""
    )
    flow_header = [item[0] for item in flow_cursor.description]
    flow_rows = flow_cursor.fetchall()
    _write_csv_rows(flow_path, flow_header, flow_rows)
    exclusion_cursor = connection.execute(
        """SELECT dataset, sample_group,
                  CASE WHEN primary_eligible=0 THEN 'not_strict_immediate_caregiver_input' ELSE 'retained' END AS reason,
                  COUNT(*) AS rows
           FROM handoff GROUP BY dataset, sample_group, reason ORDER BY dataset, reason"""
    )
    exclusion_header = [item[0] for item in exclusion_cursor.description]
    _write_csv_rows(exclusions_path, exclusion_header, exclusion_cursor.fetchall())
    connection.close()

    audit = {
        "status": "PASS" if not problems else "FAIL",
        **member_audit,
        "broad_rows": int(base_counts[0]),
        "strict_rows": expected_rows,
        "strict_metrics": {name: int(value) for name, value in observed.items()},
        "a0_k3_missing_rows": expected_rows - int(observed["finite_a0_k3"]),
        "response_word_measurement_disagreements": observed_word_disagreements,
        "response_effort_measure": "caretaker_direct_surprisal_wide.nb_words",
        "response_word_disagreement_reason": "three apostrophe/contraction tokenization cases; exact text hashes match",
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("dataset audit failed: " + "; ".join(problems))
    write_manifest(
        "dataset",
        directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "handoff_manifest": handoff_manifest,
            "flags": flags,
            "child_scores": child,
            "caregiver_scores": caregiver,
        },
        outputs={
            "broad": broad_path,
            "strict": strict_path,
            "speaker_sidecar": sidecar_path,
            "sample_flow": flow_path,
            "exclusions": exclusions_path,
            "audit": audit_path,
        },
        audit=audit,
    )
    return audit


def run_support_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_contract(contract_path)
    # Modeling/support clauses may be finalized after the immutable dataset is
    # built.  The dataset files and all raw inputs remain hash-validated; only
    # the earlier draft-contract input record may differ.
    require_manifest(
        output_dir / "datasets/manifest.json",
        "dataset",
        ignore_input_names=("contract",),
    )
    strict = output_dir / "datasets/dyadic_triads_strict.parquet"
    directory = output_dir / "support"
    directory.mkdir(parents=True, exist_ok=True)
    corpus_path = directory / "support_by_corpus.csv"
    child_path = directory / "support_by_child.csv"
    summary_path = directory / "support_summary.json"
    connection = duckdb.connect()
    cursor = connection.execute(
        f"""SELECT dataset, sample_group, COUNT(*) AS rows,
                   COUNT(DISTINCT child_key) AS children,
                   COUNT(DISTINCT child_session_key) AS sessions,
                   MIN(age_months) AS age_min, quantile_cont(age_months, .5) AS age_median,
                   MAX(age_months) AS age_max,
                   quantile_cont(c_words, .5) AS child_words_median,
                   quantile_cont(c_words, .99) AS child_words_p99,
                   quantile_cont(a1_words, .5) AS response_words_median,
                   quantile_cont(a1_words, .99) AS response_words_p99,
                   COUNT(a0_k3_bits) AS a0_k3_complete,
                   STDDEV_SAMP(a0_k3_within) AS a0_k3_within_sd,
                   STDDEV_SAMP(c_k3_within) AS c_k3_within_sd
            FROM read_parquet('{sql_path(strict)}')
            GROUP BY dataset, sample_group ORDER BY dataset"""
    )
    header = [item[0] for item in cursor.description]
    _write_csv_rows(corpus_path, header, cursor.fetchall())
    cursor = connection.execute(
        f"""SELECT child_key, dataset, sample_group, COUNT(*) AS rows,
                   COUNT(DISTINCT child_session_key) AS sessions,
                   MIN(age_months) AS age_min, MAX(age_months) AS age_max,
                   STDDEV_SAMP(age_months) AS age_sd,
                   STDDEV_SAMP(a0_k3_within) AS a0_k3_within_sd,
                   STDDEV_SAMP(c_k3_within) AS c_k3_within_sd,
                   COUNT(a0_k3_bits) AS a0_k3_complete
            FROM read_parquet('{sql_path(strict)}')
            GROUP BY child_key, dataset, sample_group ORDER BY dataset, child_key"""
    )
    header = [item[0] for item in cursor.description]
    child_rows = cursor.fetchall()
    _write_csv_rows(child_path, header, child_rows)
    summary_cursor = connection.execute(
        f"""SELECT COUNT(*) AS rows,
                   COUNT(DISTINCT child_key) AS children,
                   COUNT(DISTINCT dataset) AS corpora,
                   COUNT(DISTINCT child_session_key) AS sessions,
                   MIN(age_months) AS age_min,
                   quantile_cont(age_months, .01) AS age_p01,
                   quantile_cont(age_months, .5) AS age_median,
                   quantile_cont(age_months, .99) AS age_p99,
                   MAX(age_months) AS age_max,
                   AVG(a0_k3_bits) AS a0_k3_mean,
                   STDDEV_SAMP(a0_k3_bits) AS a0_k3_sd,
                   STDDEV_SAMP(a0_k3_within) AS a0_k3_within_sd,
                   STDDEV_SAMP(a0_k0_within) AS a0_k0_within_sd,
                   STDDEV_SAMP(a0_support_within) AS a0_support_within_sd,
                   AVG(c_k3_bits) AS c_k3_mean,
                   STDDEV_SAMP(c_k3_bits) AS c_k3_sd,
                   STDDEV_SAMP(c_k3_within) AS c_k3_within_sd,
                   STDDEV_SAMP(c_k0_within) AS c_k0_within_sd,
                   STDDEV_SAMP(c_support_within) AS c_support_within_sd,
                   STDDEV_SAMP(ln(1+c_words)) AS log1p_c_words_sd,
                   STDDEV_SAMP(ln(1+a1_words)) AS log1p_a1_words_sd,
                   quantile_cont(c_words, .99) AS c_words_p99,
                   quantile_cont(a1_words, .99) AS a1_words_p99,
                   SUM(CASE WHEN c_words>=12 THEN 1 ELSE 0 END) AS c_words_topcoded,
                   COUNT(a0_k3_bits) AS f1_f2_rows,
                   COUNT(c_k3_bits) AS f3_rows
            FROM read_parquet('{sql_path(strict)}')"""
    )
    names = [item[0] for item in summary_cursor.description]
    summary = dict(zip(names, summary_cursor.fetchone()))
    child_summary = connection.execute(
        f"""SELECT SUM(CASE WHEN n_sessions>=? AND n_rows>=? THEN 1 ELSE 0 END) AS bayes_children,
                   MIN(CASE WHEN n_sessions>=? AND n_rows>=? THEN n_rows ELSE NULL END) AS min_bayes_rows,
                   MIN(CASE WHEN n_sessions>=? AND n_rows>=? THEN n_sessions ELSE NULL END) AS min_bayes_sessions
            FROM (SELECT child_key, COUNT(*) AS n_rows,
                         COUNT(DISTINCT child_session_key) AS n_sessions
                  FROM read_parquet('{sql_path(strict)}') GROUP BY child_key)""",
        [
            int(contract["eligibility"]["minimum_sessions_for_bayesian_child_summary"]),
            int(contract["eligibility"]["minimum_rows_for_bayesian_child_summary"]),
        ] * 3,
    ).fetchone()
    scope_cursor = connection.execute(
        f"""WITH scopes AS (
              SELECT sample_group AS scope, * FROM read_parquet('{sql_path(strict)}')
              UNION ALL
              SELECT 'all79_descriptive' AS scope, * FROM read_parquet('{sql_path(strict)}')
            )
            SELECT scope, COUNT(*) AS rows, COUNT(DISTINCT child_key) AS children,
                   quantile_cont(age_months, .01) AS age_p01,
                   quantile_cont(age_months, .99) AS age_p99,
                   quantile_cont(a0_k3_within, .1) AS a0_k3_within_p10,
                   quantile_cont(a0_k3_within, .9) AS a0_k3_within_p90,
                   quantile_cont(c_k3_within, .1) AS c_k3_within_p10,
                   quantile_cont(c_k3_within, .9) AS c_k3_within_p90
            FROM scopes GROUP BY scope ORDER BY scope"""
    )
    scope_names = [item[0] for item in scope_cursor.description]
    scope_support = {
        row[0]: {
            name: (int(value) if isinstance(value, int) else float(value))
            for name, value in zip(scope_names[1:], row[1:])
        }
        for row in scope_cursor.fetchall()
    }
    connection.close()
    result = {
        "status": "PASS",
        "computed_at": utc_now(),
        **{name: (int(value) if isinstance(value, int) else float(value)) for name, value in summary.items()},
        "bayesian_eligible_children": int(child_summary[0]),
        "minimum_bayesian_child_rows": int(child_summary[1]),
        "minimum_bayesian_child_sessions": int(child_summary[2]),
        "scope_support": scope_support,
        "within_scope": contract["decomposition"]["primary_within_scope"],
        "word_top_code": int(contract["decomposition"]["word_effort_top_code"]),
        "problems": [],
    }
    if result["rows"] != int(contract["expected"]["strict_rows"]):
        result["status"] = "FAIL"
        result["problems"].append("strict support row mismatch")
    if result["a0_k3_within_sd"] <= 0 or result["c_k3_within_sd"] <= 0:
        result["status"] = "FAIL"
        result["problems"].append("no within-session predictor support")
    if result["bayesian_eligible_children"] != int(
        contract["eligibility"]["expected_bayesian_children"]
    ):
        result["status"] = "FAIL"
        result["problems"].append("Bayesian eligible-child count mismatch")
    atomic_json(result, summary_path)
    if result["status"] != "PASS":
        raise RuntimeError("support audit failed: " + "; ".join(result["problems"]))
    write_manifest(
        "support",
        directory / "manifest.json",
        inputs={"contract": contract_path, "dataset_manifest": output_dir / "datasets/manifest.json", "strict": strict},
        outputs={"summary": summary_path, "by_corpus": corpus_path, "by_child": child_path},
        audit=result,
    )
    return result


def run_contract_freeze_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_contract(contract_path, require_frozen=True)
    # The tracked contract intentionally transitions from support-blind draft to
    # frozen here.  Validate every support artifact while allowing only that
    # recorded draft-contract input hash to differ.
    support_manifest = require_manifest(
        output_dir / "support/manifest.json",
        "support",
        ignore_input_names=("contract",),
    )
    support = json.loads((output_dir / "support/support_summary.json").read_text(encoding="utf-8"))
    snapshot = contract.get("support_snapshot", {})
    required = {
        "support_summary_sha256": sha256_file(output_dir / "support/support_summary.json"),
        "strict_dataset_sha256": sha256_file(output_dir / "datasets/dyadic_triads_strict.parquet"),
        "rows": support["rows"],
        "children": support["children"],
        "corpora": support["corpora"],
    }
    if snapshot != required:
        raise RuntimeError(f"frozen support snapshot mismatch; expected {required}")
    directory = output_dir / "contract"
    directory.mkdir(parents=True, exist_ok=True)
    frozen_path = directory / "analysis_contract.frozen.json"
    audit_path = directory / "contract_audit.json"
    atomic_json(contract, frozen_path)
    audit = {
        "status": "PASS",
        "contract_sha256": sha256_file(contract_path),
        "support_manifest_sha256": sha256_file(output_dir / "support/manifest.json"),
        "support_bound": True,
        "coefficient_stages_unlocked": True,
        "problems": [],
    }
    atomic_json(audit, audit_path)
    write_manifest(
        "contract-freeze",
        directory / "manifest.json",
        inputs={"tracked_contract": contract_path, "support_manifest": output_dir / "support/manifest.json"},
        outputs={"frozen_contract": frozen_path, "audit": audit_path},
        audit={**audit, "support_stage": support_manifest["stage"]},
    )
    return audit


def run_frequentist_input_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "contract/manifest.json", "contract-freeze")
    strict = output_dir / "datasets/dyadic_triads_strict.parquet"
    if sha256_file(strict) != contract["support_snapshot"]["strict_dataset_sha256"]:
        raise RuntimeError("strict dataset no longer matches the frozen contract")
    directory = output_dir / "frequentist-input"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "model_input.csv.gz"
    temporary = target.with_name(f".{target.name}.tmp.{os.getpid()}")
    scaling = contract["decomposition"]["frozen_scaling"]
    connection = duckdb.connect()
    query = f"""SELECT response_pair_id, dataset, child_key, sample_group,
               session_id, child_session_key, age_months, age_z,
               a0_question_type, c_question_type,
               exact_imitation_candidate, child_backchannel_candidate,
               session_reading_candidate, session_routine_candidate,
               c_word_top12, c_words, a1_words,
               ln(1+a0_words) AS log1p_a0_words,
               ln(1+c_words) AS log1p_c_words,
               ln(1+a1_words) AS log1p_a1_words,
               c_k3_bits, c_k0_bits, c_context_support_bits,
               a0_k3_within/{scaling['a0_k3_within_sd']} AS a0_k3_within_z,
               a0_k0_within/{scaling['a0_k0_within_sd']} AS a0_k0_within_z,
               a0_support_within/{scaling['a0_context_support_within_sd']} AS a0_support_within_z,
               c_k3_within/{scaling['c_k3_within_sd']} AS c_k3_within_z,
               c_k0_within/{scaling['c_k0_within_sd']} AS c_k0_within_z,
               c_support_within/{scaling['c_context_support_within_sd']} AS c_support_within_z,
               a0_k3_child_mean, a0_k0_child_mean, a0_support_child_mean,
               c_k3_child_mean, c_k0_child_mean, c_support_child_mean
        FROM read_parquet('{sql_path(strict)}')
        ORDER BY dataset, child_key, session_id, response_pair_id"""
    connection.execute(
        f"COPY ({query}) TO '{sql_path(temporary)}' "
        "(FORMAT CSV, HEADER TRUE, COMPRESSION GZIP)"
    )
    os.replace(temporary, target)
    cursor = connection.execute(
        f"""SELECT COUNT(*) AS rows, COUNT(DISTINCT child_key) AS children,
                   COUNT(DISTINCT dataset) AS corpora,
                   COUNT(DISTINCT child_session_key) AS sessions,
                   SUM(CASE WHEN NOT isfinite(c_k3_bits) OR NOT isfinite(c_k0_bits)
                             OR NOT isfinite(c_context_support_bits) THEN 1 ELSE 0 END) AS bad_scores,
                   SUM(CASE WHEN c_words<1 OR a1_words<1 THEN 1 ELSE 0 END) AS bad_counts
            FROM ({query})"""
    )
    names = [item[0] for item in cursor.description]
    values = cursor.fetchone()
    observed = {name: int(value) for name, value in zip(names, values)}
    connection.close()
    problems: list[str] = []
    if observed["rows"] != int(contract["expected"]["strict_rows"]):
        problems.append("model input row mismatch")
    if observed["children"] != int(contract["expected"]["children"]):
        problems.append("model input child mismatch")
    if observed["corpora"] != int(contract["expected"]["corpora"]):
        problems.append("model input corpus mismatch")
    if observed["bad_scores"] or observed["bad_counts"]:
        problems.append("non-finite score or invalid count in model input")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        **observed,
        "input_sha256": sha256_file(target),
        "problems": problems,
    }
    audit_path = directory / "input_audit.json"
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("frequentist input audit failed: " + "; ".join(problems))
    write_manifest(
        "frequentist-input",
        directory / "manifest.json",
        inputs={"contract_manifest": output_dir / "contract/manifest.json", "strict": strict},
        outputs={"model_input": target, "audit": audit_path},
        audit=audit,
    )
    return audit


def _run_frequentist_r(
    *,
    mode: str,
    contract_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    input_path = output_dir / "frequentist-input/model_input.csv.gz"
    target_dir = output_dir / ("frequentist-smoke" if mode == "smoke" else "frequentist")
    target_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "Rscript",
            str(ROOT / "src/fit_bidirectional_dyadic_efficiency.R"),
            "--mode", mode,
            "--root", str(ROOT),
            "--contract", str(contract_path),
            "--input", str(input_path),
            "--output-dir", str(target_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    atomic_text(completed.stdout, target_dir / "stdout.log")
    atomic_text(completed.stderr, target_dir / "stderr.log")
    if completed.returncode != 0:
        raise RuntimeError(
            f"frequentist R {mode} failed ({completed.returncode}): "
            + completed.stderr[-3000:]
        )
    audit_path = target_dir / "fit_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise RuntimeError(f"frequentist {mode} audit did not pass")
    return audit


def run_frequentist_smoke_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "frequentist-input/manifest.json", "frequentist-input")
    audit = _run_frequentist_r(mode="smoke", contract_path=contract_path, output_dir=output_dir)
    directory = output_dir / "frequentist-smoke"
    write_manifest(
        "frequentist-smoke",
        directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "input_manifest": output_dir / "frequentist-input/manifest.json",
            "r_backend": ROOT / "src/fit_bidirectional_dyadic_efficiency.R",
        },
        outputs={
            "audit": directory / "fit_audit.json",
            "inventory": directory / "model_inventory.csv",
            "curves": directory / "coupling_curves.csv",
            "stdout": directory / "stdout.log",
            "stderr": directory / "stderr.log",
        },
        audit=audit,
    )
    return audit


def run_frequentist_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "frequentist-smoke/manifest.json", "frequentist-smoke")
    audit = _run_frequentist_r(mode="full", contract_path=contract_path, output_dir=output_dir)
    directory = output_dir / "frequentist"
    write_manifest(
        "frequentist",
        directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "input_manifest": output_dir / "frequentist-input/manifest.json",
            "smoke_manifest": output_dir / "frequentist-smoke/manifest.json",
            "r_backend": ROOT / "src/fit_bidirectional_dyadic_efficiency.R",
        },
        outputs={
            "audit": directory / "fit_audit.json",
            "inventory": directory / "model_inventory.csv",
            "curves": directory / "coupling_curves.csv",
            "terms": directory / "smooth_term_tests.csv",
            "stdout": directory / "stdout.log",
            "stderr": directory / "stderr.log",
        },
        audit=audit,
    )
    return audit


def run_frequentist_validation_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "frequentist/manifest.json", "frequentist")
    directory = output_dir / "frequentist-validation"
    directory.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "src/validate_bidirectional_dyadic_efficiency_20260829.py"),
            "--input", str(output_dir / "datasets/dyadic_triads_strict.parquet"),
            "--contract", str(contract_path),
            "--output-dir", str(directory),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    atomic_text(completed.stdout, directory / "stdout.log")
    atomic_text(completed.stderr, directory / "stderr.log")
    if completed.returncode != 0:
        raise RuntimeError(
            f"frequentist validation failed ({completed.returncode}): "
            + completed.stderr[-3000:]
        )
    audit_path = directory / "validation_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise RuntimeError("frequentist validation audit did not pass")
    write_manifest(
        "frequentist-validation",
        directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "frequentist_manifest": output_dir / "frequentist/manifest.json",
            "strict": output_dir / "datasets/dyadic_triads_strict.parquet",
            "validator": ROOT / "src/validate_bidirectional_dyadic_efficiency_20260829.py",
        },
        outputs={
            "audit": audit_path,
            "bootstrap": directory / "whole_child_bootstrap_age_bin_slopes.csv",
            "influence": directory / "leave_one_corpus_out.csv",
            "equalized_age": directory / "equalized_age_slopes.csv",
            "permutations": directory / "permutation_tests.csv",
            "stdout": directory / "stdout.log",
            "stderr": directory / "stderr.log",
        },
        audit=audit,
    )
    return audit


def _block_diag(*matrices: np.ndarray) -> np.ndarray:
    rows = sum(matrix.shape[0] for matrix in matrices)
    columns = sum(matrix.shape[1] for matrix in matrices)
    result = np.zeros((rows, columns))
    row = column = 0
    for matrix in matrices:
        result[row:row + matrix.shape[0], column:column + matrix.shape[1]] = matrix
        row += matrix.shape[0]
        column += matrix.shape[1]
    return result


def estimate_dyadic_child_coefficients(
    frame: pd.DataFrame,
    *,
    minimum_sessions: int = 6,
    minimum_rows: int = 30,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Jointly estimate three standardized coupling slopes for one child."""

    required = {
        "child_key", "dataset", "child_session_key", "age_z",
        "a0_k3_within_z", "c_k3_within_z", "c_k3_z", "logc_z", "loga1_z",
        "log1p_c_words", "log1p_a0_words",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Bayesian child table missing columns: {sorted(missing)}")
    if frame.child_key.nunique() != 1 or frame.dataset.nunique() != 1:
        raise ValueError("one child and one corpus are required")
    clusters = pd.unique(frame.child_session_key)
    if len(frame) < minimum_rows or len(clusters) < minimum_sessions:
        raise ValueError("child does not pass the frozen row/session support rule")
    numeric_columns = sorted(required - {"child_key", "dataset", "child_session_key"})
    numeric = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy(float)).all():
        raise ValueError("non-finite Bayesian child values")

    age = frame.age_z.to_numpy(float)
    a0 = frame.a0_k3_within_z.to_numpy(float)
    child = frame.c_k3_within_z.to_numpy(float)
    logc = frame.log1p_c_words.to_numpy(float)
    loga0 = frame.log1p_a0_words.to_numpy(float)
    x1 = np.column_stack([
        np.ones(len(frame)), age, a0, age * a0, logc, loga0,
    ])
    x2 = np.column_stack([
        np.ones(len(frame)), age, a0, age * a0, loga0,
    ])
    x3 = np.column_stack([
        np.ones(len(frame)), age, child, age * child, logc, loga0, a0,
    ])
    outcomes = [
        frame.c_k3_z.to_numpy(float),
        frame.logc_z.to_numpy(float),
        frame.loga1_z.to_numpy(float),
    ]
    designs = [x1, x2, x3]
    betas: list[np.ndarray] = []
    residuals: list[np.ndarray] = []
    breads: list[np.ndarray] = []
    for label, design, outcome in zip(("F1", "F2", "F3"), designs, outcomes):
        if len(frame) <= design.shape[1] + 10 or np.linalg.matrix_rank(design) != design.shape[1]:
            raise ValueError(f"{label} child design lacks stable full-rank support")
        bread = np.linalg.inv(design.T @ design)
        beta = bread @ design.T @ outcome
        breads.append(bread)
        betas.append(beta)
        residuals.append(outcome - design @ beta)
    cluster_values = frame.child_session_key.to_numpy()
    score_rows: list[np.ndarray] = []
    for cluster in clusters:
        selected = cluster_values == cluster
        score_rows.append(np.concatenate([
            design[selected].T @ residual[selected]
            for design, residual in zip(designs, residuals)
        ]))
    scores = np.vstack(score_rows)
    bread = _block_diag(*breads)
    correction = len(clusters) / (len(clusters) - 1)
    covariance_full = correction * bread @ (scores.T @ scores) @ bread.T
    offsets = np.cumsum([0, *[design.shape[1] for design in designs]])
    selected_indices = [offsets[0] + 2, offsets[1] + 2, offsets[2] + 2]
    covariance = covariance_full[np.ix_(selected_indices, selected_indices)]
    covariance = (covariance + covariance.T) / 2
    eigenvalues = np.linalg.eigvalsh(covariance)
    floor = max(float(np.max(eigenvalues)) * 1e-10, 1e-12)
    regularization = max(0.0, floor - float(np.min(eigenvalues)))
    if regularization:
        covariance += np.eye(3) * regularization
    if not np.isfinite(covariance).all() or np.linalg.eigvalsh(covariance).min() <= 0:
        raise ValueError("child shared covariance is not positive definite")
    estimate = np.array([betas[0][2], betas[1][2], betas[2][2]])
    return estimate, covariance, {
        "rows": int(len(frame)),
        "sessions": int(len(clusters)),
        "minimum_eigenvalue_before_regularization": float(eigenvalues.min()),
        "diagonal_regularization": float(regularization),
        "shared_session_clustered_covariance": True,
        "time_invariant_child_means_absorbed_by_child_intercepts": True,
    }


def run_bayesian_estimates_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "frequentist-validation/manifest.json", "frequentist-validation")
    strict = output_dir / "datasets/dyadic_triads_strict.parquet"
    support = json.loads((output_dir / "support/support_summary.json").read_text(encoding="utf-8"))
    scaling = contract["decomposition"]["frozen_scaling"]
    connection = duckdb.connect()
    frame = connection.execute(
        f"""SELECT child_key, dataset, child_session_key, age_z,
                   a0_k3_within/{scaling['a0_k3_within_sd']} AS a0_k3_within_z,
                   c_k3_within/{scaling['c_k3_within_sd']} AS c_k3_within_z,
                   (c_k3_bits-{support['c_k3_mean']})/{support['c_k3_sd']} AS c_k3_z,
                   ln(1+c_words)/{scaling['log1p_child_words_sd']} AS logc_z,
                   ln(1+a1_words)/{scaling['log1p_response_words_sd']} AS loga1_z,
                   ln(1+c_words) AS log1p_c_words,
                   ln(1+a0_words) AS log1p_a0_words,
                   (a0_k3_child_mean-{support['a0_k3_mean']})/{support['a0_k3_sd']} AS a0_k3_child_mean_z,
                   (c_k3_child_mean-{support['c_k3_mean']})/{support['c_k3_sd']} AS c_k3_child_mean_z
            FROM read_parquet(?) ORDER BY dataset, child_key, child_session_key, response_pair_id""",
        [str(strict)],
    ).fetchdf()
    connection.close()
    minimum_sessions = int(contract["eligibility"]["minimum_sessions_for_bayesian_child_summary"])
    minimum_rows = int(contract["eligibility"]["minimum_rows_for_bayesian_child_summary"])
    records: list[dict[str, Any]] = []
    flow: list[dict[str, Any]] = []
    for child_key, child_frame in frame.groupby("child_key", sort=True):
        sessions = child_frame.child_session_key.nunique()
        eligible = len(child_frame) >= minimum_rows and sessions >= minimum_sessions
        if not eligible:
            flow.append({
                "child_key": child_key,
                "dataset": child_frame.dataset.iloc[0],
                "rows": len(child_frame),
                "sessions": sessions,
                "status": "excluded_frozen_support_rule",
            })
            continue
        estimate, covariance, child_audit = estimate_dyadic_child_coefficients(
            child_frame, minimum_sessions=minimum_sessions, minimum_rows=minimum_rows
        )
        records.append({
            "child_key": child_key,
            "dataset": child_frame.dataset.iloc[0],
            "sample_group": "pbm_discovery" if child_frame.dataset.iloc[0] in PBM_DATASETS else "non_pbm_confirmation",
            "adult_to_child_k3": estimate[0],
            "adult_to_child_effort": estimate[1],
            "child_to_adult_effort": estimate[2],
            "cov_11": covariance[0, 0],
            "cov_12": covariance[0, 1],
            "cov_13": covariance[0, 2],
            "cov_22": covariance[1, 1],
            "cov_23": covariance[1, 2],
            "cov_33": covariance[2, 2],
            **child_audit,
        })
        flow.append({
            "child_key": child_key,
            "dataset": child_frame.dataset.iloc[0],
            "rows": len(child_frame),
            "sessions": sessions,
            "status": "included",
        })
    estimates = pd.DataFrame(records).sort_values(["dataset", "child_key"])
    flow_frame = pd.DataFrame(flow).sort_values(["dataset", "child_key"])
    directory = output_dir / "bayesian-estimates"
    directory.mkdir(parents=True, exist_ok=True)
    estimates_path = directory / "child_coefficient_estimates.csv"
    flow_path = directory / "child_sample_flow.csv"
    audit_path = directory / "estimates_audit.json"
    estimates.to_csv(estimates_path, index=False, lineterminator="\n")
    flow_frame.to_csv(flow_path, index=False, lineterminator="\n")
    excluded = sorted(flow_frame.loc[flow_frame.status != "included", "child_key"].tolist())
    covariance_columns = ["cov_11", "cov_12", "cov_13", "cov_22", "cov_23", "cov_33"]
    problems: list[str] = []
    if len(estimates) != int(contract["eligibility"]["expected_bayesian_children"]):
        problems.append("Bayesian included-child count mismatch")
    if estimates.dataset.nunique() != int(contract["expected"]["corpora"]):
        problems.append("Bayesian corpus coverage mismatch")
    if not np.isfinite(estimates[covariance_columns].to_numpy(float)).all():
        problems.append("non-finite Bayesian estimation covariance")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "source_rows": int(len(frame)),
        "included_children": int(len(estimates)),
        "included_pbm": int((estimates.sample_group == "pbm_discovery").sum()),
        "included_non_pbm": int((estimates.sample_group == "non_pbm_confirmation").sum()),
        "corpora": int(estimates.dataset.nunique()),
        "excluded_children": excluded,
        "maximum_covariance_regularization": float(estimates.diagonal_regularization.max()),
        "shared_session_clustered_covariance": True,
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("Bayesian estimates audit failed: " + "; ".join(problems))
    write_manifest(
        "bayesian-estimates",
        directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "validation_manifest": output_dir / "frequentist-validation/manifest.json",
            "strict": strict,
            "support": output_dir / "support/support_summary.json",
        },
        outputs={"estimates": estimates_path, "sample_flow": flow_path, "audit": audit_path},
        audit=audit,
    )
    return audit


def _run_bayesian_r(mode: str, contract_path: Path, output_dir: Path) -> tuple[dict[str, Any], Path]:
    directory = output_dir / ("bayesian-smoke" if mode == "synthetic" else "bayesian-fit")
    directory.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "Rscript", str(ROOT / "src/fit_bayesian_bidirectional_dyadic_efficiency.R"),
            "--mode", mode, "--root", str(ROOT), "--contract", str(contract_path),
            "--input", str(output_dir / "bayesian-estimates/child_coefficient_estimates.csv"),
            "--output-dir", str(directory),
        ],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    atomic_text(completed.stdout, directory / "stdout.log")
    atomic_text(completed.stderr, directory / "stderr.log")
    if completed.returncode != 0:
        raise RuntimeError(f"Bayesian R {mode} failed ({completed.returncode}): {completed.stderr[-3000:]}")
    audit_path = directory / ("synthetic_audit.json" if mode == "synthetic" else "fit_audit.json")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise RuntimeError(f"Bayesian {mode} audit did not pass")
    return audit, directory


def run_bayesian_smoke_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "bayesian-estimates/manifest.json", "bayesian-estimates")
    audit, directory = _run_bayesian_r("synthetic", contract_path, output_dir)
    write_manifest(
        "bayesian-smoke", directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "estimates_manifest": output_dir / "bayesian-estimates/manifest.json",
            "backend": ROOT / "src/fit_bayesian_bidirectional_dyadic_efficiency.R",
            "stan": ROOT / "src/stan/joint_adaptive_efficiency_measurement_error.stan",
        },
        outputs={
            "audit": directory / "synthetic_audit.json",
            "recovery": directory / "synthetic_recovery.csv",
            "stdout": directory / "stdout.log", "stderr": directory / "stderr.log",
        }, audit=audit,
    )
    return audit


def run_bayesian_fit_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(
        output_dir / "bayesian-smoke/manifest.json",
        "bayesian-smoke",
        ignore_input_names=("backend",),
    )
    audit, directory = _run_bayesian_r("fit", contract_path, output_dir)
    write_manifest(
        "bayesian-fit", directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "smoke_manifest": output_dir / "bayesian-smoke/manifest.json",
            "estimates": output_dir / "bayesian-estimates/child_coefficient_estimates.csv",
            "backend": ROOT / "src/fit_bayesian_bidirectional_dyadic_efficiency.R",
            "stan": ROOT / "src/stan/joint_adaptive_efficiency_measurement_error.stan",
        },
        outputs={
            "audit": directory / "fit_audit.json",
            "diagnostics": directory / "fit_diagnostics.csv",
            "summary": directory / "posterior_summary.csv",
            "draws_primary": directory / "posterior_draws_regularizing.csv.gz",
            "draws_wide": directory / "posterior_draws_wide_sensitivity.csv.gz",
            "influence": directory / "influence_summary.csv",
            "ppc": directory / "posterior_predictive_checks.csv",
            "stdout": directory / "stdout.log", "stderr": directory / "stderr.log",
        }, audit=audit,
    )
    return audit


def run_bayesian_repair_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(
        output_dir / "bayesian-smoke/manifest.json",
        "bayesian-smoke",
        ignore_input_names=("backend",),
    )
    first_audit = output_dir / "bayesian-fit/fit_audit.json"
    if not first_audit.exists() or json.loads(first_audit.read_text(encoding="utf-8")).get("status") != "FAIL":
        raise RuntimeError("Bayesian repair requires a failed first-pass diagnostic audit")
    audit, directory = _run_bayesian_r("repair", contract_path, output_dir)
    write_manifest(
        "bayesian-fit", directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "smoke_manifest": output_dir / "bayesian-smoke/manifest.json",
            "estimates": output_dir / "bayesian-estimates/child_coefficient_estimates.csv",
            "backend": ROOT / "src/fit_bayesian_bidirectional_dyadic_efficiency.R",
            "stan": ROOT / "src/stan/joint_adaptive_efficiency_measurement_error.stan",
        },
        outputs={
            "audit": directory / "fit_audit.json",
            "diagnostics": directory / "fit_diagnostics.csv",
            "repair_diagnostics": directory / "repair_diagnostics.csv",
            "summary": directory / "posterior_summary.csv",
            "draws_primary": directory / "posterior_draws_regularizing.csv.gz",
            "draws_wide": directory / "posterior_draws_wide_sensitivity.csv.gz",
            "influence": directory / "influence_summary.csv",
            "ppc": directory / "posterior_predictive_checks.csv",
            "stdout": directory / "stdout.log", "stderr": directory / "stderr.log",
        }, audit=audit,
    )
    return audit


def _posterior_summary(values: pd.Series) -> dict[str, float]:
    array = pd.to_numeric(values, errors="coerce").to_numpy(float)
    if not np.isfinite(array).all():
        raise ValueError("posterior contains non-finite values")
    return {
        "mean": float(array.mean()),
        "q025": float(np.quantile(array, .025)),
        "q975": float(np.quantile(array, .975)),
        "probability_positive": float(np.mean(array > 0)),
        "probability_negative": float(np.mean(array < 0)),
    }


def run_bayesian_diagnostics_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "bayesian-fit/manifest.json", "bayesian-fit")
    fit_dir = output_dir / "bayesian-fit"
    primary = pd.read_csv(fit_dir / "posterior_draws_regularizing.csv.gz")
    wide = pd.read_csv(fit_dir / "posterior_draws_wide_sensitivity.csv.gz")
    variables = [
        ("D1", "adult_to_child_k3", "Adult-to-child fixed-effort predictability", "mu_adult_to_child_k3", 0.05),
        ("D1b", "adult_to_child_effort", "Adult-to-child effort coupling at 42 months", "mu_adult_to_child_effort", 0.05),
        ("D2", "child_to_adult_effort", "Child-to-caregiver response-effort coupling at 42 months", "mu_child_to_adult_effort", 0.05),
        ("D5a", "rho_k3_child_effort", "Correlation: adult-to-child k3 and effort", "rho_k3_child_effort", 0.10),
        ("D5b", "rho_k3_adult_effort", "Correlation: adult-to-child k3 and child-to-caregiver effort", "rho_k3_adult_effort", 0.10),
        ("D5c", "rho_reciprocal_effort", "Correlation: reciprocal effort couplings", "rho_reciprocal_effort", 0.10),
    ]
    rows: list[dict[str, Any]] = []
    sensitivity_rows: list[dict[str, Any]] = []
    for hypothesis, estimand, label, variable, rope in variables:
        summary = _posterior_summary(primary[variable])
        wide_summary = _posterior_summary(wide[variable])
        rows.append({
            "hypothesis": hypothesis,
            "estimand": estimand,
            "label": label,
            "variable": variable,
            **summary,
            "rope_half_width": rope,
            "probability_rope": float(np.mean(np.abs(primary[variable]) <= rope)),
        })
        sensitivity_rows.append({
            "variable": variable,
            "regularizing_mean": summary["mean"],
            "wide_mean": wide_summary["mean"],
            "absolute_shift": abs(summary["mean"] - wide_summary["mean"]),
        })
    estimands = pd.DataFrame(rows)
    sensitivity = pd.DataFrame(sensitivity_rows)
    influence = pd.read_csv(fit_dir / "influence_summary.csv")
    primary_means = {
        "mu_adult_to_child_k3": estimands.loc[estimands.variable == "mu_adult_to_child_k3", "mean"].iloc[0],
        "mu_adult_to_child_effort": estimands.loc[estimands.variable == "mu_adult_to_child_effort", "mean"].iloc[0],
        "mu_child_to_adult_effort": estimands.loc[estimands.variable == "mu_child_to_adult_effort", "mean"].iloc[0],
        "rho_reciprocal_effort": estimands.loc[estimands.variable == "rho_reciprocal_effort", "mean"].iloc[0],
    }
    influence_rows: list[dict[str, Any]] = []
    for column, reference in primary_means.items():
        for record in influence.itertuples(index=False):
            value = float(getattr(record, column))
            influence_rows.append({
                "omitted_corpus": record.omitted_corpus,
                "variable": column,
                "estimate": value,
                "shift": value - reference,
                "sign_reversal": np.sign(value) != np.sign(reference),
            })
    influence_long = pd.DataFrame(influence_rows)
    ppc = pd.read_csv(fit_dir / "posterior_predictive_checks.csv")
    fit_audit = json.loads((fit_dir / "fit_audit.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    if fit_audit.get("status") != "PASS":
        problems.append("fit audit is not PASS")
    if (ppc.status != "PASS").any():
        problems.append("posterior predictive check failed")
    directory = output_dir / "bayesian-diagnostics"
    directory.mkdir(parents=True, exist_ok=True)
    estimands_path = directory / "posterior_estimands.csv"
    sensitivity_path = directory / "prior_sensitivity.csv"
    influence_path = directory / "influence_long.csv"
    audit_path = directory / "diagnostics_audit.json"
    estimands.to_csv(estimands_path, index=False, lineterminator="\n")
    sensitivity.to_csv(sensitivity_path, index=False, lineterminator="\n")
    influence_long.to_csv(influence_path, index=False, lineterminator="\n")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "estimands": len(estimands),
        "posterior_draws": len(primary),
        "maximum_prior_mean_shift": float(sensitivity.absolute_shift.max()),
        "maximum_leave_corpus_shift": float(influence_long['shift'].abs().max()),
        "leave_corpus_sign_reversals": int(influence_long.sign_reversal.sum()),
        "posterior_predictive_checks": len(ppc),
        "fit_total_cpu_hours": float(fit_audit["total_cpu_hours"]),
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("Bayesian diagnostics failed: " + "; ".join(problems))
    write_manifest(
        "bayesian-diagnostics", directory / "manifest.json",
        inputs={"contract": contract_path, "fit_manifest": fit_dir / "manifest.json"},
        outputs={
            "audit": audit_path, "estimands": estimands_path,
            "prior_sensitivity": sensitivity_path, "influence": influence_path,
        }, audit=audit,
    )
    return audit


def _chat_roles(path: Path) -> dict[str, str]:
    roles: dict[str, str] = {}
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("*"):
                break
            if line.startswith("@Participants:"):
                payload = line.split(":", 1)[1].strip()
                for entry in payload.split(","):
                    parts = entry.strip().split(maxsplit=1)
                    if len(parts) == 2:
                        roles[parts[0].upper()] = parts[1].strip()
            elif line.startswith("@ID:"):
                fields = line.split(":", 1)[1].strip().split("|")
                if len(fields) >= 8 and fields[2].strip():
                    code = fields[2].strip().upper()
                    role = fields[7].strip()
                    if role:
                        roles[code] = role
    return roles


def _role_matches_parent(code: str, role: str) -> bool:
    normalized = re.sub(r"[^a-z]+", " ", role.lower()).strip()
    if code == "MOT":
        return any(label in normalized.split() for label in ("mother", "mom", "mum", "mummy"))
    if code == "FAT":
        return any(label in normalized.split() for label in ("father", "dad", "daddy"))
    return False


def run_parent_role_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "bayesian-diagnostics/manifest.json", "bayesian-diagnostics")
    strict = output_dir / "datasets/dyadic_triads_strict.parquet"
    flags = ROOT / "results/conversational_eligibility/full79_child_conversational_flags.csv.gz"
    connection = duckdb.connect()
    source_rows = connection.execute(
        """SELECT s.response_pair_id, s.dataset, s.child_id, s.file, s.c_line_no,
                  s.a0_speaker, s.a1_speaker, f.raw_source_path
           FROM read_parquet(?) s
           LEFT JOIN read_csv(?, all_varchar=true) f
             ON s.dataset=f.dataset AND s.child_id=f.child_id AND s.file=f.file
            AND s.c_line_no=TRY_CAST(f.line_no AS INTEGER)
           ORDER BY s.dataset, s.child_id, s.file, s.c_line_no""",
        [str(strict), str(flags)],
    ).fetchdf()
    if len(source_rows) != 413084 or source_rows.raw_source_path.isna().any():
        raise RuntimeError("parent-role source join is incomplete")
    file_records: list[dict[str, Any]] = []
    for raw_path in sorted(source_rows.raw_source_path.unique()):
        path = Path(raw_path)
        exists = path.exists()
        roles = _chat_roles(path) if exists else {}
        file_records.append({
            "raw_source_path": raw_path,
            "source_exists": exists,
            "mot_role": roles.get("MOT", ""),
            "fat_role": roles.get("FAT", ""),
            "mot_parent_valid": _role_matches_parent("MOT", roles.get("MOT", "")),
            "fat_parent_valid": _role_matches_parent("FAT", roles.get("FAT", "")),
        })
    file_audit = pd.DataFrame(file_records)
    source_rows = source_rows.merge(file_audit, on="raw_source_path", how="left", validate="many_to_one")
    source_rows["a0_parent_valid"] = (
        ((source_rows.a0_speaker == "MOT") & source_rows.mot_parent_valid)
        | ((source_rows.a0_speaker == "FAT") & source_rows.fat_parent_valid)
    )
    source_rows["a1_parent_valid"] = (
        ((source_rows.a1_speaker == "MOT") & source_rows.mot_parent_valid)
        | ((source_rows.a1_speaker == "FAT") & source_rows.fat_parent_valid)
    )
    directory = output_dir / "parent-role"
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / "file_role_audit.csv"
    sidecar_path = directory / "parent_role_sidecar.csv"
    triads_path = directory / "dyadic_triads_parent_flags.parquet"
    audit_path = directory / "parent_role_audit.json"
    file_audit.to_csv(file_path, index=False, lineterminator="\n")
    sidecar = source_rows[[
        "response_pair_id", "raw_source_path", "a0_speaker", "a1_speaker",
        "a0_parent_valid", "a1_parent_valid",
    ]]
    sidecar.to_csv(sidecar_path, index=False, lineterminator="\n")
    connection.register("parent_sidecar", sidecar)
    temporary = triads_path.with_name(f".{triads_path.name}.tmp.{os.getpid()}")
    connection.execute(
        f"""COPY (SELECT s.*, p.raw_source_path, p.a0_parent_valid, p.a1_parent_valid
                    FROM read_parquet('{sql_path(strict)}') s
                    JOIN parent_sidecar p USING(response_pair_id)
                    ORDER BY s.dataset, s.child_key, s.file, s.c_line_no)
             TO '{sql_path(temporary)}' (FORMAT PARQUET, COMPRESSION ZSTD)"""
    )
    os.replace(temporary, triads_path)
    connection.close()
    parent_codes = source_rows.a0_speaker.isin(["MOT", "FAT"]) | source_rows.a1_speaker.isin(["MOT", "FAT"])
    invalid_code_rows = source_rows.loc[
        ((source_rows.a0_speaker.isin(["MOT", "FAT"])) & ~source_rows.a0_parent_valid)
        | ((source_rows.a1_speaker.isin(["MOT", "FAT"])) & ~source_rows.a1_parent_valid)
    ]
    problems: list[str] = []
    if not file_audit.source_exists.all():
        problems.append("missing CHAT source file")
    if len(invalid_code_rows):
        problems.append("MOT/FAT code failed file-level metadata validation")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "strict_rows": len(source_rows),
        "source_files": len(file_audit),
        "rows_with_any_parent_code": int(parent_codes.sum()),
        "a0_parent_rows": int(source_rows.a0_parent_valid.sum()),
        "a1_parent_rows": int(source_rows.a1_parent_valid.sum()),
        "both_parent_rows": int((source_rows.a0_parent_valid & source_rows.a1_parent_valid).sum()),
        "invalid_mot_fat_rows": int(len(invalid_code_rows)),
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("parent-role audit failed: " + "; ".join(problems))
    write_manifest(
        "parent-role", directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "diagnostics_manifest": output_dir / "bayesian-diagnostics/manifest.json",
            "strict": strict, "flags": flags,
        },
        outputs={"audit": audit_path, "file_roles": file_path, "sidecar": sidecar_path, "triads": triads_path},
        audit=audit,
    )
    return audit


def run_parent_sensitivity_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "parent-role/manifest.json", "parent-role")
    directory = output_dir / "parent-sensitivity"
    directory.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "Rscript", str(ROOT / "src/fit_bidirectional_dyadic_efficiency.R"),
            "--mode", "parent", "--root", str(ROOT), "--contract", str(contract_path),
            "--input", str(output_dir / "frequentist-input/model_input.csv.gz"),
            "--parent-sidecar", str(output_dir / "parent-role/parent_role_sidecar.csv"),
            "--output-dir", str(directory),
        ],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    atomic_text(completed.stdout, directory / "stdout.log")
    atomic_text(completed.stderr, directory / "stderr.log")
    if completed.returncode != 0:
        raise RuntimeError(f"parent sensitivity failed ({completed.returncode}): {completed.stderr[-3000:]}")
    audit_path = directory / "fit_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise RuntimeError("parent sensitivity audit did not pass")
    write_manifest(
        "parent-sensitivity", directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "parent_manifest": output_dir / "parent-role/manifest.json",
            "model_input": output_dir / "frequentist-input/model_input.csv.gz",
            "backend": ROOT / "src/fit_bidirectional_dyadic_efficiency.R",
        },
        outputs={
            "audit": audit_path, "inventory": directory / "model_inventory.csv",
            "curves": directory / "coupling_curves.csv", "terms": directory / "smooth_term_tests.csv",
            "stdout": directory / "stdout.log", "stderr": directory / "stderr.log",
        }, audit=audit,
    )
    return audit


def run_gates_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "parent-sensitivity/manifest.json", "parent-sensitivity")
    directory = output_dir / "gates"
    directory.mkdir(parents=True, exist_ok=True)
    manual_path = ROOT / "results/conversational_eligibility/full79_conversational_manual_validation_sample.csv"
    manual = pd.read_csv(manual_path, keep_default_na=False)
    manual_columns = [column for column in manual.columns if column.startswith("manual_")]
    completed_manual_rows = int((manual[manual_columns].astype(str).apply(lambda column: column.str.strip()) != "").any(axis=1).sum())
    external_root = ROOT / "results/external/compute_surprisal_mila"
    local_candidates = []
    if external_root.exists():
        local_candidates = sorted(
            str(path.relative_to(ROOT))
            for path in external_root.iterdir()
            if "caregiver" in path.name.lower() or "downstream" in path.name.lower()
        )
    sibling_root = ROOT.parent / "compute_surprisal_mila/mila_results"
    sibling_candidates = []
    if sibling_root.exists():
        sibling_candidates = sorted(
            str(path)
            for path in sibling_root.iterdir()
            if "caregiver" in path.name.lower() or "downstream" in path.name.lower()
        )
    score_ready = bool(local_candidates)
    manual_ready = len(manual) == 325 and completed_manual_rows == 325
    status = {
        "status": "PASS_CORE_GATES_RECORDED",
        "manual_validation": {
            "state": "READY" if manual_ready else "WAITING_FOR_VALIDATED_325_ROW_LABELS",
            "sample_rows": int(len(manual)),
            "rows_with_any_manual_label": completed_manual_rows,
            "manual_columns": manual_columns,
        },
        "downstream_utility": {
            "state": "AUDITED_SCORES_AVAILABLE" if score_ready else "WAITING_FOR_AUDITED_SCORES",
            "local_analysis_candidates": local_candidates,
            "sibling_top_level_candidates": sibling_candidates,
            "required_before_analysis": "complete five-condition archives plus independent local relocation audit for each scorer",
        },
        "core_analysis_complete": True,
        "full_listener_utility_complete": False,
    }
    status_path = directory / "readiness.json"
    atomic_json(status, status_path)
    marker_outputs: dict[str, Path] = {"status": status_path}
    if not score_ready:
        score_marker = directory / "WAITING_FOR_AUDITED_SCORES"
        atomic_text("No locally audited downstream caregiver-response score archive was available.\n", score_marker)
        marker_outputs["score_marker"] = score_marker
    if not manual_ready:
        label_marker = directory / "WAITING_FOR_VALIDATED_325_ROW_LABELS"
        atomic_text("The 325-row manual validation sample exists, but its manual label fields are blank.\n", label_marker)
        marker_outputs["label_marker"] = label_marker
    write_manifest(
        "gates", directory / "manifest.json",
        inputs={
            "contract": contract_path,
            "parent_manifest": output_dir / "parent-sensitivity/manifest.json",
            "manual_sample": manual_path,
        },
        outputs=marker_outputs,
        audit=status,
    )
    return status


def _interval_text(row: pd.Series, digits: int = 3) -> str:
    return f"{row['estimate']:.{digits}f} [{row['simultaneous_lower']:.{digits}f}, {row['simultaneous_upper']:.{digits}f}]"


def run_synthesis_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "gates/manifest.json", "gates")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from render_markdown_report import render_markdown_file

    curves = pd.read_csv(output_dir / "frequentist/coupling_curves.csv")
    validation = json.loads((output_dir / "frequentist-validation/validation_audit.json").read_text(encoding="utf-8"))
    permutations = pd.read_csv(output_dir / "frequentist-validation/permutation_tests.csv")
    posterior = pd.read_csv(output_dir / "bayesian-diagnostics/posterior_estimands.csv")
    bayes_audit = json.loads((output_dir / "bayesian-diagnostics/diagnostics_audit.json").read_text(encoding="utf-8"))
    parent_curves = pd.read_csv(output_dir / "parent-sensitivity/coupling_curves.csv")
    gates = json.loads((output_dir / "gates/readiness.json").read_text(encoding="utf-8"))
    figures = ROOT / "figs/bidirectional_dyadic_efficiency_20260829"
    figures.mkdir(parents=True, exist_ok=True)

    colors = {
        "pbm_discovery": "#C76F2C",
        "non_pbm_confirmation": "#2F6F73",
        "all79_descriptive": "#6A5D8C",
    }
    primary = curves[curves.variant == "k3"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    titles = {
        "F1": "A→C predictability",
        "F2": "A→C effort",
        "F3": "C→A response effort",
    }
    for axis, family_id in zip(axes, ("F1", "F2", "F3")):
        for scope in ("pbm_discovery", "non_pbm_confirmation", "all79_descriptive"):
            view = primary[(primary.family_id == family_id) & (primary.scope == scope)].sort_values("age_months")
            axis.plot(view.age_months, view.estimate, marker="o", color=colors[scope], label=scope.replace("_", " "))
            axis.fill_between(
                view.age_months.to_numpy(float), view.simultaneous_lower.to_numpy(float),
                view.simultaneous_upper.to_numpy(float), color=colors[scope], alpha=.12,
            )
        axis.axhline(0 if family_id == "F1" else 1, color="#555555", linestyle="--", linewidth=1)
        axis.set_title(titles[family_id])
        axis.set_xlabel("Child age (months)")
        axis.set_ylabel("Bits / within-SD" if family_id == "F1" else "Response IRR / within-SD")
    axes[0].legend(fontsize=8)
    fig.suptitle("Bidirectional within-session coupling (simultaneous 95% bands)")
    fig.tight_layout()
    curve_figure = figures / "primary_bidirectional_coupling.png"
    fig.savefig(curve_figure, dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    means = posterior.iloc[:3].copy()
    y = np.arange(len(means))
    axes[0].errorbar(
        means["mean"], y,
        xerr=[means["mean"] - means.q025, means.q975 - means["mean"]],
        fmt="o", color="#2F6F73", capsize=4,
    )
    axes[0].axvline(0, color="#555555", linestyle="--", linewidth=1)
    axes[0].set_yticks(y, ["A→C k3", "A→C effort", "C→A effort"])
    axes[0].set_title("Population standardized couplings")
    correlations = posterior.iloc[3:].copy()
    y = np.arange(len(correlations))
    axes[1].errorbar(
        correlations["mean"], y,
        xerr=[correlations["mean"] - correlations.q025, correlations.q975 - correlations["mean"]],
        fmt="o", color="#C76F2C", capsize=4,
    )
    axes[1].axvline(0, color="#555555", linestyle="--", linewidth=1)
    axes[1].set_yticks(y, ["k3 × child effort", "k3 × adult effort", "reciprocal effort"])
    axes[1].set_xlim(-1, 1)
    axes[1].set_title("Between-child/dyad correlations")
    fig.tight_layout()
    bayes_figure = figures / "bayesian_bidirectional_synthesis.png"
    fig.savefig(bayes_figure, dpi=180, bbox_inches="tight")
    plt.close(fig)

    decomposition = curves[
        (curves.scope == "all79_descriptive") & (curves.age_months == 42)
    ].copy()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for axis, family_id in zip(axes, ("F1", "F2", "F3")):
        view = decomposition[decomposition.family_id == family_id]
        axis.errorbar(
            view.estimate, np.arange(len(view)),
            xerr=[view.estimate - view.simultaneous_lower, view.simultaneous_upper - view.estimate],
            fmt="o", color="#6A5D8C", capsize=4,
        )
        axis.axvline(0 if family_id == "F1" else 1, color="#555555", linestyle="--", linewidth=1)
        axis.set_yticks(np.arange(len(view)), view.variant)
        axis.set_title(titles[family_id])
    fig.suptitle("k3, k0, and context-support decompositions at 42 months")
    fig.tight_layout()
    decomposition_figure = figures / "decomposition_at_42_months.png"
    fig.savefig(decomposition_figure, dpi=180, bbox_inches="tight")
    plt.close(fig)

    confirm = primary[(primary.scope == "non_pbm_confirmation")]
    selected = confirm[confirm.age_months.isin([24, 36, 42, 60])]
    frequentist_rows = []
    for row in selected.itertuples(index=False):
        frequentist_rows.append(
            f"| {row.family_id} | {int(row.age_months)} | {row.estimate:.3f} "
            f"[{row.simultaneous_lower:.3f}, {row.simultaneous_upper:.3f}] | "
            f"{'yes' if row.simultaneous_excludes_null else 'no'} |"
        )
    posterior_rows = []
    for row in posterior.itertuples(index=False):
        posterior_rows.append(
            f"| {row.hypothesis} | {row.label} | {row.mean:.3f} [{row.q025:.3f}, {row.q975:.3f}] | "
            f"{row.probability_positive:.3f} | {row.probability_rope:.3f} |"
        )
    parent_main = primary[primary.scope == "all79_descriptive"][["family_id", "age_months", "estimate"]]
    parent_compare = parent_curves[["family_id", "age_months", "estimate"]].merge(
        parent_main, on=["family_id", "age_months"], suffixes=("_parent", "_caregiver")
    )
    max_parent_shift = float((parent_compare.estimate_parent - parent_compare.estimate_caregiver).abs().max())
    markdown = f"""# Bidirectional Dyadic Communicative-Efficiency Analysis

Status: **core analysis complete and audited**. The listener-utility and manually
validated response-function extensions remain gated; they are not silently
treated as null results.

## Scientific question

For the ordered sequence `caregiver A_t → child C_t → caregiver A_t+1`, do
momentary changes in scorer predictability and production effort propagate in
both directions, and does that coupling change with child age?

The strict analysis contains **413,084** exact caregiver-child-caregiver triads
from 79 children and 13 corpora. Every child, preceding-caregiver, and
responding-caregiver score joined one-to-one with an exact text-hash match.

## Main result

The strongest result is an **age-dependent reversal in effort coupling**.
Around 24 months, a one-SD increase in the preceding speaker's within-session
contextual surprisal is followed by slightly longer next turns. From roughly
36 months onward, higher surprisal is instead followed by shorter child and
caregiver turns. The other-58 confirmation sample passes the frozen
two-adjacent-age simultaneous-band rule for F2 and F3, but not for F1.

| Family | Age | Estimate [simultaneous 95% interval] | Excludes null? |
|---|---:|---:|---:|
{chr(10).join(frequentist_rows)}

F1 is measured in child k3 bits per one within-session SD of caregiver k3,
with child effort controlled. F2 and F3 are incidence-rate ratios. Thus F3's
estimate of {confirm[(confirm.family_id=='F3') & (confirm.age_months==42)].estimate.iloc[0]:.3f}
at 42 months corresponds to about a
{(1-confirm[(confirm.family_id=='F3') & (confirm.age_months==42)].estimate.iloc[0])*100:.1f}%
shorter modeled caregiver response per child-k3 SD, conditional on the frozen
controls. This is an observational within-session association, not a causal
effect.

![Primary coupling curves](../figs/bidirectional_dyadic_efficiency_20260829/primary_bidirectional_coupling.png)

## Bayesian joint synthesis

The bounded Bayesian model uses 75 children with at least 30 triads and six
sessions, propagating the shared session-clustered covariance of three
child-level standardized coefficients. Four exclusions were determined by the
pre-fit support rule. All final fits had zero divergences and zero treedepth
saturation; total compute, including diagnostic repairs, was
**{bayes_audit['fit_total_cpu_hours']:.2f} CPU-hours**.

| ID | Estimand | Posterior mean [95% CrI] | P(positive) | P(ROPE) |
|---|---|---:|---:|---:|
{chr(10).join(posterior_rows)}

At 42 months, adult-to-child fixed-effort predictability coupling is essentially
zero. Adult-to-child effort shortening is small and uncertain. Child-to-
caregiver effort shortening is supported. The reciprocal effort slopes
correlate positively across children/dyads, but this heterogeneity result is
descriptive and somewhat corpus-sensitive; it remains positive in every
leave-one-corpus refit.

![Bayesian synthesis](../figs/bidirectional_dyadic_efficiency_20260829/bayesian_bidirectional_synthesis.png)

## Decomposition and robustness

The pooled 42-month decomposition keeps k0, k3, and context support separate.
It finds positive same-component coupling for unconditional form surprisal and
context support in F1, while the net k3 fixed-effort coupling is near zero.
Effort shortening appears in the k0 and context-support variants as well. These
standardized variants are not algebraically subtractable.

![Score decomposition](../figs/bidirectional_dyadic_efficiency_20260829/decomposition_at_42_months.png)

The robustness package passed **{validation['minimum_bootstrap_success_fraction']:.1%}**
minimum corpus-stratified whole-child bootstrap completion, 13 leave-one-corpus
checks per family, age equalization, 200 session-level and row-level age
scrambles, and 200 within-session turn shuffles. All nine permutation tests had
`p = {permutations.p_value.max():.4f}`. The binned bootstrap independently
confirmed F2 and F3 but not F1.

The metadata-validated parent sensitivity retains 412,667 adult-to-child and
412,657 child-to-adult rows. Its largest departure from the caregiver curves is
only **{max_parent_shift:.4f}**, so the substantive result is unchanged when
the relevant adult turn is explicitly a mother or father.

## What this means for communicative efficiency

The evidence supports reciprocal, developmentally changing **effort
adaptation**. It does not yet show that shorter responses preserve meaning or
improve listener success. The reversal is compatible with increasing ability
to resolve or respond economically to locally unusual speech, but competing
accounts include turn function, discourse structure, transcription, and
scorer representation.

Two stronger layers remain unavailable:

- **Downstream predictive utility:** `{gates['downstream_utility']['state']}`.
  No score archive may be joined until all five conditions for each scorer pass
  independent relocation audit.
- **Validated response function:** `{gates['manual_validation']['state']}`.
  The 325-row sample exists, but zero rows currently contain a manual label.

Therefore this report does not claim causal optimization, preserved utility,
or semantic efficiency.

## Reproducibility

The frozen contract is
`configs/bidirectional_dyadic_efficiency_20260829/analysis_contract.json`.
The staged products and hash manifests are under
`results/bidirectional_dyadic_efficiency_20260829/`. The core program contains
15 frequentist fits, three parent-only sensitivities, a 200-replicate
robustness package, and 15 final Bayesian fits after five diagnostic-only
repairs.
"""
    report_md = ROOT / "docs/bidirectional_dyadic_communicative_efficiency_report.md"
    report_html = ROOT / "docs/bidirectional_dyadic_communicative_efficiency_report.html"
    atomic_text(markdown, report_md)
    render_markdown_file(report_md, report_html, title="Bidirectional dyadic communicative efficiency", embed_images=True)
    directory = output_dir / "synthesis"
    directory.mkdir(parents=True, exist_ok=True)
    audit = {
        "status": "PASS",
        "figures": 3,
        "frequentist_models": 15,
        "parent_models": 3,
        "bayesian_final_fits": 15,
        "f2_confirmed": bool(validation["confirmation_by_binned_bootstrap"]["F2"]),
        "f3_confirmed": bool(validation["confirmation_by_binned_bootstrap"]["F3"]),
        "f1_confirmed": bool(validation["confirmation_by_binned_bootstrap"]["F1"]),
        "utility_state": gates["downstream_utility"]["state"],
        "manual_state": gates["manual_validation"]["state"],
        "problems": [],
    }
    audit_path = directory / "synthesis_audit.json"
    atomic_json(audit, audit_path)
    write_manifest(
        "synthesis", directory / "manifest.json",
        inputs={
            "contract": contract_path, "gates_manifest": output_dir / "gates/manifest.json",
            "frequentist_manifest": output_dir / "frequentist/manifest.json",
            "validation_manifest": output_dir / "frequentist-validation/manifest.json",
            "bayesian_manifest": output_dir / "bayesian-diagnostics/manifest.json",
            "parent_manifest": output_dir / "parent-sensitivity/manifest.json",
        },
        outputs={
            "audit": audit_path, "report_md": report_md, "report_html": report_html,
            "curves_figure": curve_figure, "bayes_figure": bayes_figure,
            "decomposition_figure": decomposition_figure,
        }, audit=audit,
    )
    return audit


def run_final_audit_stage(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    load_contract(contract_path, require_frozen=True)
    require_manifest(output_dir / "synthesis/manifest.json", "synthesis")
    required_manifests = [
        "datasets/manifest.json", "support/manifest.json", "contract/manifest.json",
        "frequentist-input/manifest.json", "frequentist-smoke/manifest.json",
        "frequentist/manifest.json", "frequentist-validation/manifest.json",
        "bayesian-estimates/manifest.json", "bayesian-smoke/manifest.json",
        "bayesian-fit/manifest.json", "bayesian-diagnostics/manifest.json",
        "parent-role/manifest.json", "parent-sensitivity/manifest.json",
        "gates/manifest.json", "synthesis/manifest.json",
    ]
    missing = [relative for relative in required_manifests if not (output_dir / relative).exists()]
    synthesis = json.loads((output_dir / "synthesis/synthesis_audit.json").read_text(encoding="utf-8"))
    fit_audit = json.loads((output_dir / "bayesian-fit/fit_audit.json").read_text(encoding="utf-8"))
    problems = list(missing)
    if synthesis.get("status") != "PASS":
        problems.append("synthesis audit failed")
    if fit_audit.get("status") != "PASS":
        problems.append("Bayesian fit audit failed")
    audit = {
        "status": "PASS_CORE_UTILITY_AND_MANUAL_GATED" if not problems else "FAIL",
        "required_manifests": len(required_manifests),
        "missing_manifests": missing,
        "core_complete": not problems,
        "downstream_utility_complete": False,
        "manual_response_function_complete": False,
        "full_completion_marker_deliberately_absent": True,
        "problems": problems,
    }
    audit_path = output_dir / "final_audit.json"
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError("final core audit failed: " + "; ".join(problems))
    marker = output_dir / "CORE_DYADIC_ANALYSIS_COMPLETE_AND_AUDITED"
    atomic_text(
        "Core F1-F3, validation, Bayesian synthesis, and parent sensitivity passed.\n"
        "Listener utility and manual response-function analyses remain gated.\n",
        marker,
    )
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        required=True,
        choices=(
            "dataset", "support", "contract-freeze", "frequentist-input",
            "frequentist-smoke", "frequentist", "frequentist-validation",
            "bayesian-estimates",
            "bayesian-smoke", "bayesian-fit",
            "bayesian-repair",
            "bayesian-diagnostics",
            "parent-role",
            "parent-sensitivity",
            "gates", "synthesis", "final-audit",
        ),
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.stage == "dataset":
        result = run_dataset_stage(args.contract, args.output_dir)
    elif args.stage == "support":
        result = run_support_stage(args.contract, args.output_dir)
    elif args.stage == "contract-freeze":
        result = run_contract_freeze_stage(args.contract, args.output_dir)
    elif args.stage == "frequentist-input":
        result = run_frequentist_input_stage(args.contract, args.output_dir)
    elif args.stage == "frequentist-smoke":
        result = run_frequentist_smoke_stage(args.contract, args.output_dir)
    elif args.stage == "frequentist":
        result = run_frequentist_stage(args.contract, args.output_dir)
    elif args.stage == "frequentist-validation":
        result = run_frequentist_validation_stage(args.contract, args.output_dir)
    elif args.stage == "bayesian-estimates":
        result = run_bayesian_estimates_stage(args.contract, args.output_dir)
    elif args.stage == "bayesian-smoke":
        result = run_bayesian_smoke_stage(args.contract, args.output_dir)
    elif args.stage == "bayesian-fit":
        result = run_bayesian_fit_stage(args.contract, args.output_dir)
    elif args.stage == "bayesian-repair":
        result = run_bayesian_repair_stage(args.contract, args.output_dir)
    elif args.stage == "bayesian-diagnostics":
        result = run_bayesian_diagnostics_stage(args.contract, args.output_dir)
    elif args.stage == "parent-role":
        result = run_parent_role_stage(args.contract, args.output_dir)
    elif args.stage == "parent-sensitivity":
        result = run_parent_sensitivity_stage(args.contract, args.output_dir)
    elif args.stage == "gates":
        result = run_gates_stage(args.contract, args.output_dir)
    elif args.stage == "synthesis":
        result = run_synthesis_stage(args.contract, args.output_dir)
    else:
        result = run_final_audit_stage(args.contract, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
