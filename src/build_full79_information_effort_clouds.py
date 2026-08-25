#!/usr/bin/env python3
"""Build the all-79 model-by-exact-length-by-age information atlas.

The workflow is deliberately staged and resumable:

``datasets -> metrics -> models -> plots -> report -> audit``

Qwen responses and Mistral scores are immutable upstream inputs.  The primary
plotting unit is one mean-information cell per model, exact word length, and
age bin; adjusted fixed-length trajectories control stable child identity.
Plotting and reporting consume only frozen local products.  A full-79 additive
LSTM is a separate gated source: when its audited scored handoff is absent,
every core product is completed and ``CORE_CLOUDS_COMPLETE_LSTM_PENDING`` is
written, but the all-source completion marker is not.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import json
import math
import os
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from patsy import build_design_matrices

try:
    from render_markdown_report import render_markdown_file
except ModuleNotFoundError:  # pragma: no cover - package import
    from src.render_markdown_report import render_markdown_file


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WIDE = ROOT / "results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz"
DEFAULT_WIDE_MANIFEST = ROOT / "results/direct_surprisal_replication/mistral_full79/manifest.json"
DEFAULT_QWEN_ROOT = (
    ROOT
    / "results/external/compute_surprisal_mila/"
    "qwen_response_mistral_full100_20260817_f5dd5aa"
)
DEFAULT_OUTPUT = ROOT / "results/full79_information_effort_clouds"
DEFAULT_FIGURES = ROOT / "figs/full79_information_effort_clouds"
DEFAULT_REPORT_MD = ROOT / "docs/full79_information_effort_clouds.md"
DEFAULT_REPORT_HTML = ROOT / "docs/full79_information_effort_clouds.html"

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
PRECISE_AGES = (18, 24, 30, 36, 42, 48, 54, 60)
FIXED_LENGTHS = tuple(range(1, 13))
LENGTH_GROUPS = ((1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12))
WORD_PATTERN = r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:'[A-Za-zÀ-ÖØ-öø-ÿ]+)*"
WORD_PATTERN_SQL = WORD_PATTERN.replace("'", "''")

SOURCE_LABELS = {
    "observed_child": "observed child",
    "qwen": "Qwen free-length responses",
    "random": "random baseline",
    "unigram": "unigram baseline",
    "bigram": "bigram baseline",
    "trigram": "trigram baseline",
    "lstm": "additive LSTM baseline",
}
SOURCE_ORDER = tuple(SOURCE_LABELS)
SOURCE_COLORS = {
    "observed_child": "#08306b",
    "qwen": "#bdbdbd",
    "random": "#d62728",
    "unigram": "#ff7f0e",
    "bigram": "#2ca02c",
    "trigram": "#1f77b4",
    "lstm": "#9467bd",
}
BASELINE_PREFIXES = {
    "observed_child": "real",
    "random": "random",
    "unigram": "unigram",
    "bigram": "bigram",
    "trigram": "trigram",
}

MODEL_OUTCOMES = (
    "word_count",
    "k3_sum_bits",
    "k3_mean_bits_per_token",
    "k0_sum_bits",
    "context_support_bits",
    "word_effort_difference_vs_observed",
    "z_effort",
    "z_k3",
    "effort_percentile_in_qwen",
    "k3_percentile_in_qwen",
)


@dataclass(frozen=True)
class ExpectedCounts:
    real_source_rows: int = 1_140_695
    eligible_real_rows: int = 1_122_396
    qwen_contexts: int = 645_524
    qwen_responses: int = 64_552_400
    qwen_core_responses: int = 48_414_300
    qwen_extension_responses: int = 16_138_100
    qwen_responses_per_context: int = 100
    qwen_core_per_context: int = 75
    qwen_extension_per_context: int = 25
    children: int = 79
    corpora: int = 13
    shards: int = 512


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def stable_seed(label: str) -> int:
    return int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)


def atomic_json(payload: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(
        temporary,
        index=False,
        compression="gzip" if path.name.endswith(".gz") else None,
        lineterminator="\n",
    )
    os.replace(temporary, path)


def require_file(path: Path, label: str) -> None:
    if not path.is_file() or path.stat().st_size <= 0:
        raise FileNotFoundError(f"{label} is missing or empty: {path}")


def require_equal(actual: int, expected: int, label: str) -> None:
    if int(actual) != int(expected):
        raise RuntimeError(f"expected {expected:,} {label}, found {actual:,}")


def git_state() -> dict[str, Any]:
    def run(args: Sequence[str]) -> str:
        result = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    commit = run(["git", "rev-parse", "HEAD"])
    status = run(["git", "status", "--short"])
    return {"commit": commit, "worktree_dirty": bool(status), "status_lines": status.splitlines()}


def write_schema(path: Path, columns: Mapping[str, str], *, primary_key: Sequence[str], description: str) -> None:
    atomic_json(
        {
            "description": description,
            "columns": dict(columns),
            "primary_key": list(primary_key),
            "schema_sha256": stable_hash({"columns": dict(columns), "primary_key": list(primary_key)}),
        },
        path,
    )


def stage_manifest(
    *,
    stage: str,
    inputs: Mapping[str, Path],
    outputs: Mapping[str, Path],
    metadata: Mapping[str, Any],
    destination: Path,
) -> dict[str, Any]:
    payload = {
        "status": "COMPLETE",
        "stage": stage,
        "created_at": utc_now(),
        "controller": str(Path(__file__)),
        "controller_sha256": sha256_file(Path(__file__)),
        "git": git_state(),
        "inputs": {
            key: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for key, path in inputs.items()
        },
        "outputs": {
            key: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for key, path in outputs.items()
        },
        **dict(metadata),
    }
    atomic_json(payload, destination)
    return payload


def require_stage_manifest(path: Path, expected_stage: str) -> dict[str, Any]:
    require_file(path, f"{expected_stage} manifest")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "COMPLETE" or payload.get("stage") != expected_stage:
        raise RuntimeError(f"invalid {expected_stage} manifest: {path}")
    for family in ("inputs", "outputs"):
        for label, item in payload.get(family, {}).items():
            product = Path(item["path"])
            require_file(product, f"{expected_stage} {family[:-1]} {label}")
            if sha256_file(product) != item["sha256"]:
                raise RuntimeError(f"stale {expected_stage} manifest: {label} changed")
    return payload


def _qwen_files(root: Path, relative: str, prefix: str) -> list[Path]:
    return sorted((root / relative).glob(f"{prefix}_*.csv.gz"))


def validate_qwen_handoff(root: Path, expected: ExpectedCounts, *, verify_hashes: bool) -> tuple[pd.DataFrame, dict[str, Any]]:
    markers = [root / name for name in ("CORE75_COMPLETE", "EXTENSION25_COMPLETE", "FULL100_AVAILABLE")]
    for marker in markers:
        require_file(marker, marker.name)
    families = {
        "prepared_core75": ("prepared/inputs/core75", "responses"),
        "prepared_extension25": ("prepared/inputs/extension25", "responses"),
        "processed_core75": ("processed/core75", "scored"),
        "processed_extension25": ("processed/extension25", "scored"),
        "context_means_full100": ("context_means/full100", "context_means"),
    }
    family_files = {key: _qwen_files(root, relative, prefix) for key, (relative, prefix) in families.items()}
    for key, files in family_files.items():
        require_equal(len(files), expected.shards, f"{key} shards")

    rows: list[dict[str, Any]] = []
    contract_totals = {"core75": 0, "extension25": 0}
    for tier in ("core75", "extension25"):
        prepared = family_files[f"prepared_{tier}"]
        processed = family_files[f"processed_{tier}"]
        for shard, (input_path, output_path) in enumerate(zip(prepared, processed)):
            contract_path = output_path.with_name(output_path.name + ".contract.json")
            require_file(contract_path, f"{tier} shard contract")
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            if contract.get("status") != "PASS" or contract.get("selection_tiers") != [tier]:
                raise RuntimeError(f"invalid Qwen scoring contract: {contract_path}")
            input_hash = sha256_file(input_path) if verify_hashes else "not_rehashed"
            output_hash = sha256_file(output_path) if verify_hashes else "not_rehashed"
            if verify_hashes and input_hash != contract.get("input_sha256"):
                raise RuntimeError(f"Qwen prepared input hash mismatch: {input_path}")
            if verify_hashes and output_hash != contract.get("output_sha256"):
                raise RuntimeError(f"Qwen processed output hash mismatch: {output_path}")
            n_rows = int(contract["rows"])
            contract_totals[tier] += n_rows
            rows.append(
                {
                    "tier": tier,
                    "shard": shard,
                    "prepared_path": str(input_path),
                    "processed_path": str(output_path),
                    "contract_path": str(contract_path),
                    "rows": n_rows,
                    "contexts": int(contract["contexts"]),
                    "prepared_sha256": contract["input_sha256"],
                    "processed_sha256": contract["output_sha256"],
                    "rehash_verified": bool(verify_hashes),
                    "status": contract["status"],
                }
            )
    require_equal(contract_totals["core75"], expected.qwen_core_responses, "contracted Qwen core75 rows")
    require_equal(
        contract_totals["extension25"], expected.qwen_extension_responses, "contracted Qwen extension25 rows"
    )
    full_audit = root / "reports/full100/full100_audit.json"
    require_file(full_audit, "full100 upstream audit")
    upstream = json.loads(full_audit.read_text(encoding="utf-8"))
    if upstream.get("status") != "PASS" or not upstream.get("core75_and_extension25_disjoint"):
        raise RuntimeError("upstream full100 Qwen audit does not pass the disjoint-union contract")
    return pd.DataFrame(rows), {
        "root": str(root.resolve()),
        "markers": {marker.name: sha256_file(marker) for marker in markers},
        "families": {key: len(files) for key, files in family_files.items()},
        "contract_rows": contract_totals,
        "full100_audit": str(full_audit),
        "full100_audit_sha256": sha256_file(full_audit),
        "raw_hashes_reverified": bool(verify_hashes),
    }


def required_lstm_contract() -> dict[str, Any]:
    return {
        "status": "ABSENT_PENDING",
        "source": "additive full-79 same-length LSTM conditioned on k3 caregiver context",
        "required_top_level_marker": "COMPLETE_AND_AUDITED",
        "required_identity_columns": [
            "row_uid",
            "utterance_id",
            "dataset",
            "child_id",
            "session_id",
            "age_months",
            "age_bin",
            "file",
            "line_no",
            "utt_id",
        ],
        "required_candidate_columns": [
            "generated_utterance",
            "generated_word_count",
            "target_word_count",
            "context_k3",
            "target_text_sha256",
            "context_k3_sha256",
            "baseline_run_id",
            "source_model",
            "sample_index",
        ],
        "required_score_columns": [
            "k0_sum_bits",
            "k0_mean_bits_per_token",
            "k0_n_eval_tokens",
            "k3_sum_bits",
            "k3_mean_bits_per_token",
            "k3_n_eval_tokens",
        ],
        "required_provenance": [
            "scorer_model",
            "model_revision",
            "tokenizer_revision",
            "scoring_dtype",
            "scoring_code_revision",
        ],
        "required_audits": [
            "79 children and 13 corpora",
            "unique row_uid",
            "no empty generated targets",
            "same generated and observed word length",
            "finite k0/k3 scores and positive evaluation-token counts",
            "exact k3 context alignment",
            "per-file hashes and exact join totals",
        ],
        "known_historical_join_warning": (
            "generation input historically had 1,140,218 rows while the direct table has "
            "1,140,695 after a 477-row Naima patch; overlap must be audited"
        ),
        "prohibited_substitute": "PBM-only additive LSTM products",
    }


def discover_lstm_handoff(explicit_root: Path | None) -> tuple[Path | None, dict[str, Any]]:
    candidates: list[Path] = []
    if explicit_root is not None:
        candidates.append(explicit_root)
    candidates.extend(
        [
            ROOT.parent
            / "generate_baselines_mila/results/mila_runs/full79_lstm_additive_k3_same_length/"
            "20260722_full79_lstm_v1",
            ROOT / "results/external/compute_surprisal_mila/full79_lstm_additive_k3_same_length",
        ]
    )
    for candidate in candidates:
        marker = candidate / "COMPLETE_AND_AUDITED"
        if marker.is_file() and marker.stat().st_size > 0:
            return candidate, {
                "status": "AVAILABLE_UNINGESTED",
                "root": str(candidate.resolve()),
                "marker": str(marker),
                "marker_sha256": sha256_file(marker),
            }
    return None, {
        **required_lstm_contract(),
        "searched_roots": [str(path) for path in candidates],
        "note": "No full-79 audited scored LSTM handoff exists; the PBM-only product was not used.",
    }


def candidate_usecols(columns: Iterable[str]) -> list[str]:
    required = {
        "dataset",
        "child_id",
        "child_key",
        "session_id",
        "age_months",
        "age_bin",
        "file",
        "line_no",
        "utt_id",
        "utterance_id",
        "context_k3",
        "context_k3_sha256",
    }
    for prefix in BASELINE_PREFIXES.values():
        required.update(
            {
                f"{prefix}_target_text",
                f"{prefix}_nb_words",
                f"{prefix}_k0_sum_bits",
                f"{prefix}_k0_mean_bits_per_token",
                f"{prefix}_k0_n_eval_tokens",
                f"{prefix}_k3_sum_bits",
                f"{prefix}_k3_mean_bits_per_token",
                f"{prefix}_k3_n_eval_tokens",
            }
        )
    missing = required - set(columns)
    if missing:
        raise KeyError(f"real-child wide table missing required columns: {sorted(missing)}")
    return sorted(required)


def _candidate_frame(chunk: pd.DataFrame, source: str, prefix: str) -> pd.DataFrame:
    identity = [
        "dataset",
        "child_id",
        "child_key",
        "session_id",
        "age_months",
        "age_bin",
        "file",
        "line_no",
        "utt_id",
        "utterance_id",
        "context_k3",
        "context_k3_sha256",
    ]
    out = chunk[identity].copy()
    out["source"] = source
    out["source_label"] = SOURCE_LABELS[source]
    out["target_text"] = chunk[f"{prefix}_target_text"]
    out["word_count"] = pd.to_numeric(chunk[f"{prefix}_nb_words"], errors="coerce")
    for context in ("k0", "k3"):
        out[f"{context}_sum_bits"] = pd.to_numeric(chunk[f"{prefix}_{context}_sum_bits"], errors="coerce")
        out[f"{context}_mean_bits_per_token"] = pd.to_numeric(
            chunk[f"{prefix}_{context}_mean_bits_per_token"], errors="coerce"
        )
        out[f"{context}_n_eval_tokens"] = pd.to_numeric(
            chunk[f"{prefix}_{context}_n_eval_tokens"], errors="coerce"
        )
    out["context_support_bits"] = out["k0_sum_bits"] - out["k3_sum_bits"]
    out["context_id"] = out["context_k3_sha256"].astype(str).str.slice(0, 24)
    out["candidate_key"] = out["utterance_id"].astype(str) + "::" + source
    out["child_key"] = out["dataset"].astype(str) + "/" + out["child_id"].astype(str)
    for column in ("age_months", "session_id", "line_no", "utt_id"):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def extract_candidates(
    input_wide: Path,
    output_parquet: Path,
    *,
    chunksize: int,
    expected: ExpectedCounts,
) -> dict[str, Any]:
    require_file(input_wide, "all-79 real-child wide table")
    columns = pd.read_csv(input_wide, nrows=0).columns.tolist()
    usecols = candidate_usecols(columns)
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="full79_candidates_", dir="/tmp") as temporary:
        connection = duckdb.connect(str(Path(temporary) / "candidates.duckdb"))
        initialized = False
        source_rows = 0
        eligible_rows = 0
        blank_context_rows = 0
        blank_target_rows = 0
        for chunk_index, chunk in enumerate(
            pd.read_csv(
                input_wide,
                usecols=usecols,
                dtype=str,
                keep_default_na=False,
                chunksize=chunksize,
                low_memory=False,
            )
        ):
            source_rows += len(chunk)
            context_ok = chunk["context_k3"].astype(str).str.strip().ne("")
            target_ok = chunk["real_target_text"].astype(str).str.strip().ne("")
            blank_context_rows += int((~context_ok).sum())
            blank_target_rows += int((~target_ok).sum())
            kept = chunk[context_ok & target_ok].copy()
            eligible_rows += len(kept)
            long = pd.concat(
                [_candidate_frame(kept, source, prefix) for source, prefix in BASELINE_PREFIXES.items()],
                ignore_index=True,
            )
            connection.register("candidate_chunk", long)
            if not initialized:
                connection.execute("CREATE TABLE candidates AS SELECT * FROM candidate_chunk")
                initialized = True
            else:
                connection.execute("INSERT INTO candidates SELECT * FROM candidate_chunk")
            connection.unregister("candidate_chunk")
            print(
                f"[datasets] candidate chunk={chunk_index + 1} source_rows={source_rows:,} "
                f"eligible={eligible_rows:,}",
                flush=True,
            )
        require_equal(source_rows, expected.real_source_rows, "wide-table source rows")
        require_equal(eligible_rows, expected.eligible_real_rows, "eligible real-child rows")
        stats = connection.execute(
            """
            SELECT count(*) AS rows,
                   count(DISTINCT candidate_key) AS unique_keys,
                   count(DISTINCT child_key) AS children,
                   count(DISTINCT dataset) AS corpora,
                   count(DISTINCT context_id) AS contexts,
                   sum(CASE WHEN k3_sum_bits IS NULL OR NOT isfinite(k3_sum_bits) THEN 1 ELSE 0 END) AS nonfinite_k3,
                   sum(CASE WHEN k0_sum_bits IS NULL OR NOT isfinite(k0_sum_bits) THEN 1 ELSE 0 END) AS nonfinite_k0,
                   sum(CASE WHEN word_count IS NULL OR word_count < 0 THEN 1 ELSE 0 END) AS invalid_effort
            FROM candidates
            """
        ).fetchone()
        require_equal(stats[0], expected.eligible_real_rows * len(BASELINE_PREFIXES), "non-LSTM candidate rows")
        require_equal(stats[1], stats[0], "unique candidate keys")
        require_equal(stats[2], expected.children, "candidate children")
        require_equal(stats[3], expected.corpora, "candidate corpora")
        require_equal(stats[4], expected.qwen_contexts, "candidate Qwen contexts")
        temporary_parquet = output_parquet.with_name(f".{output_parquet.name}.tmp.{os.getpid()}")
        connection.execute(
            "COPY (SELECT * FROM candidates ORDER BY utterance_id, source) TO ? "
            "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)",
            [str(temporary_parquet)],
        )
        connection.close()
        os.replace(temporary_parquet, output_parquet)
    return {
        "source_rows": source_rows,
        "eligible_real_rows": eligible_rows,
        "candidate_rows": int(stats[0]),
        "candidate_unique_keys": int(stats[1]),
        "children": int(stats[2]),
        "corpora": int(stats[3]),
        "contexts": int(stats[4]),
        "nonfinite_k3_rows": int(stats[5]),
        "nonfinite_k0_rows": int(stats[6]),
        "invalid_effort_rows": int(stats[7]),
        "excluded_blank_context_rows": blank_context_rows,
        "excluded_blank_target_rows": blank_target_rows,
    }


def run_datasets_stage(args: argparse.Namespace, expected: ExpectedCounts) -> dict[str, Any]:
    datasets_dir = args.output_dir / "datasets"
    schemas_dir = args.output_dir / "schemas"
    datasets_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)
    require_file(args.wide_manifest, "all-79 wide-table manifest")
    wide_contract = json.loads(args.wide_manifest.read_text(encoding="utf-8"))
    require_equal(int(wide_contract["child_rows"]), expected.real_source_rows, "manifest child rows")
    require_equal(int(wide_contract["children"]), expected.children, "manifest children")
    require_equal(len(wide_contract["datasets"]), expected.corpora, "manifest corpora")

    inventory, qwen_contract = validate_qwen_handoff(
        args.qwen_root,
        expected,
        verify_hashes=not args.skip_qwen_raw_rehash,
    )
    inventory_path = datasets_dir / "qwen_input_inventory.csv"
    atomic_csv(inventory, inventory_path)

    candidates_path = datasets_dir / "non_lstm_candidates.parquet"
    candidate_audit = extract_candidates(
        args.input_wide,
        candidates_path,
        chunksize=args.chunksize,
        expected=expected,
    )
    candidate_audit_path = datasets_dir / "candidate_extraction_audit.json"
    atomic_json(candidate_audit, candidate_audit_path)

    lstm_root, lstm_gate = discover_lstm_handoff(args.lstm_root)
    # Scored ingestion is intentionally refused until the handoff schema and
    # audit exist.  Merely finding a generation marker is not enough.
    if lstm_root is not None:
        lstm_gate["status"] = "AVAILABLE_REQUIRES_SCORED_SCHEMA_VALIDATION"
        lstm_gate["ingested"] = False
    lstm_gate_path = datasets_dir / "lstm_gate.json"
    atomic_json(lstm_gate, lstm_gate_path)
    lstm_schema_path = schemas_dir / "required_full79_lstm_scored_handoff.json"
    atomic_json(required_lstm_contract(), lstm_schema_path)

    candidate_schema_path = schemas_dir / "non_lstm_candidates.schema.json"
    write_schema(
        candidate_schema_path,
        {
            "candidate_key": "string",
            "utterance_id": "string",
            "context_id": "string",
            "dataset": "string",
            "child_key": "string",
            "age_months": "float",
            "age_bin": "string",
            "source": "enum",
            "target_text": "string",
            "word_count": "float",
            "k0_sum_bits": "float",
            "k3_sum_bits": "float",
            "k3_mean_bits_per_token": "float",
            "context_support_bits": "float",
        },
        primary_key=["candidate_key"],
        description="All eligible observed, random, unigram, bigram, and trigram candidates.",
    )
    qwen_contract_path = datasets_dir / "qwen_handoff_contract.json"
    atomic_json(qwen_contract, qwen_contract_path)
    source_colors_path = datasets_dir / "source_style_contract.json"
    atomic_json(
        {
            "source_order": list(SOURCE_ORDER),
            "labels": SOURCE_LABELS,
            "colors": SOURCE_COLORS,
            "observed_marker": "black_star_or_black_outline",
            "qwen_layer": "light_gray_density_plus_sample",
        },
        source_colors_path,
    )
    manifest_path = datasets_dir / "dataset_manifest.json"
    return stage_manifest(
        stage="datasets",
        inputs={"wide": args.input_wide, "wide_manifest": args.wide_manifest, "full100_audit": Path(qwen_contract["full100_audit"])},
        outputs={
            "candidates": candidates_path,
            "candidate_audit": candidate_audit_path,
            "qwen_inventory": inventory_path,
            "qwen_contract": qwen_contract_path,
            "lstm_gate": lstm_gate_path,
            "lstm_schema": lstm_schema_path,
            "candidate_schema": candidate_schema_path,
            "source_style": source_colors_path,
        },
        metadata={
            "expected": asdict(expected),
            "candidate_audit": candidate_audit,
            "qwen_contract": qwen_contract,
            "lstm_status": lstm_gate["status"],
            "pooled_all79_only": True,
        },
        destination=manifest_path,
    )


def configure_duckdb(connection: duckdb.DuckDBPyConnection, temporary_dir: Path, memory_limit: str) -> None:
    temporary_dir.mkdir(parents=True, exist_ok=True)
    connection.execute(f"SET memory_limit='{memory_limit}'")
    connection.execute("SET threads TO 4")
    connection.execute("SET preserve_insertion_order=false")
    connection.execute("SET temp_directory=?", [str(temporary_dir)])


def sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def sql_list(values: Sequence[str | Path]) -> str:
    return "[" + ",".join(sql_literal(value) for value in values) + "]"


def _copy_query(connection: duckdb.DuckDBPyConnection, query: str, path: Path, parameters: Sequence[Any] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    copy = f"COPY ({query}) TO ? (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000)"
    connection.execute(copy, [*(parameters or []), str(temporary)])
    os.replace(temporary, path)


def _csv_from_query(connection: duckdb.DuckDBPyConnection, query: str, path: Path) -> None:
    frame = connection.execute(query).fetchdf()
    atomic_csv(frame, path)


def materialize_qwen_base(
    connection: duckdb.DuckDBPyConnection,
    qwen_root: Path,
) -> None:
    core = [str(path) for path in _qwen_files(qwen_root, "processed/core75", "scored")]
    extension = [str(path) for path in _qwen_files(qwen_root, "processed/extension25", "scored")]
    connection.execute(
        f"""
        CREATE TABLE qwen_base AS
        SELECT response_id, setting_id, context_id, context_text,
               context_word_count::INTEGER AS context_word_count,
               datasets, child_ids, child_count::INTEGER AS child_count,
               n_target_rows::INTEGER AS n_target_rows,
               selected_sample_index::INTEGER AS selected_sample_index,
               target_text, 'core75'::VARCHAR AS tier,
               source_shard::INTEGER AS source_shard,
               len(regexp_extract_all(target_text, '{WORD_PATTERN_SQL}'))::INTEGER AS word_count,
               sum_bits_k0::DOUBLE AS k0_sum_bits,
               n_eval_tokens_k0::INTEGER AS k0_n_eval_tokens,
               sum_bits_k3::DOUBLE AS k3_sum_bits,
               n_eval_tokens_k3::INTEGER AS k3_n_eval_tokens,
               mean_bits_per_token_k3::DOUBLE AS k3_mean_bits_per_token,
               context_support_bits::DOUBLE AS context_support_bits
        FROM read_csv_auto({sql_list(core)}, header=true, union_by_name=true)
        UNION ALL
        SELECT response_id, setting_id, context_id, context_text,
               context_word_count::INTEGER, datasets, child_ids,
               child_count::INTEGER, n_target_rows::INTEGER,
               selected_sample_index::INTEGER, target_text, 'extension25'::VARCHAR,
               source_shard::INTEGER,
               len(regexp_extract_all(target_text, '{WORD_PATTERN_SQL}'))::INTEGER,
               sum_bits_k0::DOUBLE, n_eval_tokens_k0::INTEGER,
               sum_bits_k3::DOUBLE, n_eval_tokens_k3::INTEGER,
               mean_bits_per_token_k3::DOUBLE, context_support_bits::DOUBLE
        FROM read_csv_auto({sql_list(extension)}, header=true, union_by_name=true)
        """,
    )


def run_metrics_stage(args: argparse.Namespace, expected: ExpectedCounts) -> dict[str, Any]:
    dataset_manifest_path = args.output_dir / "datasets/dataset_manifest.json"
    dataset_manifest = require_stage_manifest(dataset_manifest_path, "datasets")
    candidates_path = Path(dataset_manifest["outputs"]["candidates"]["path"])
    metrics_dir = args.output_dir / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(args.duckdb_temp_dir) if args.duckdb_temp_dir else Path("/tmp")
    with tempfile.TemporaryDirectory(prefix="full79_cloud_metrics_", dir=temporary_root) as temp_name:
        temporary = Path(temp_name)
        connection = duckdb.connect(str(temporary / "metrics.duckdb"))
        configure_duckdb(connection, temporary / "spill", args.duckdb_memory_limit)
        connection.execute(
            f"CREATE VIEW candidates AS SELECT * FROM read_parquet({sql_literal(candidates_path)})"
        )
        connection.execute(
            """
            CREATE TABLE row_map AS
            SELECT utterance_id, context_id, dataset, child_key, age_months, age_bin
            FROM candidates WHERE source='observed_child'
            """
        )
        print("[metrics] materializing the immutable full100 Qwen union", flush=True)
        materialize_qwen_base(connection, args.qwen_root)

        integrity = connection.execute(
            """
            SELECT count(*) AS responses,
                   count(DISTINCT context_id) AS contexts,
                   count(DISTINCT response_id) AS unique_response_ids,
                   count(DISTINCT CASE WHEN tier='core75' THEN response_id END) AS unique_core_ids,
                   count(DISTINCT CASE WHEN tier='extension25' THEN response_id END) AS unique_extension_ids,
                   sum(CASE WHEN tier='core75' THEN 1 ELSE 0 END) AS core_rows,
                   sum(CASE WHEN tier='extension25' THEN 1 ELSE 0 END) AS extension_rows,
                   sum(CASE WHEN split_part(response_id, '::', 1) <> context_id THEN 1 ELSE 0 END) AS response_context_mismatches,
                   sum(CASE WHEN NOT isfinite(k0_sum_bits) OR NOT isfinite(k3_sum_bits)
                                 OR NOT isfinite(k3_mean_bits_per_token)
                                 OR NOT isfinite(context_support_bits) THEN 1 ELSE 0 END) AS nonfinite_rows,
                   sum(CASE WHEN word_count = 0 THEN 1 ELSE 0 END) AS zero_word_rows,
                   sum(CASE WHEN word_count IS NULL OR word_count < 0 THEN 1 ELSE 0 END) AS invalid_word_rows,
                   sum(CASE WHEN k0_n_eval_tokens <= 0 OR k3_n_eval_tokens <= 0 THEN 1 ELSE 0 END) AS nonpositive_eval_token_rows,
                   max(word_count) AS maximum_word_count,
                   max(k3_n_eval_tokens) AS maximum_mistral_eval_tokens
            FROM qwen_base
            """
        ).fetchone()
        require_equal(integrity[0], expected.qwen_responses, "scanned Qwen responses")
        require_equal(integrity[1], expected.qwen_contexts, "scanned Qwen contexts")
        require_equal(integrity[2], expected.qwen_responses, "unique Qwen response ids")
        require_equal(integrity[3], expected.qwen_core_responses, "unique core75 response ids")
        require_equal(integrity[4], expected.qwen_extension_responses, "unique extension25 response ids")
        require_equal(integrity[5], expected.qwen_core_responses, "core75 rows")
        require_equal(integrity[6], expected.qwen_extension_responses, "extension25 rows")
        require_equal(integrity[7], 0, "Qwen response/context id mismatches")
        require_equal(integrity[8], 0, "nonfinite Qwen score rows")
        require_equal(integrity[10], 0, "invalid Qwen word-count rows")
        require_equal(integrity[11], 0, "nonpositive Qwen evaluation-token rows")

        print("[metrics] computing exact context summaries and exact-string entropy", flush=True)
        connection.execute(
            """
            CREATE TABLE response_type_counts AS
            SELECT context_id, target_text, count(*)::INTEGER AS n
            FROM qwen_base GROUP BY context_id, target_text
            """
        )
        connection.execute(
            """
            CREATE TABLE response_entropy AS
            SELECT context_id,
                   count(*)::INTEGER AS unique_response_count,
                   max(n) / 100.0 AS top_response_probability,
                   -sum((n / 100.0) * log2(n / 100.0)) AS exact_string_entropy_bits
            FROM response_type_counts GROUP BY context_id
            """
        )
        connection.execute(
            """
            CREATE TABLE qwen_context_metrics AS
            SELECT q.context_id,
                   any_value(q.context_text) AS context_text,
                   any_value(q.context_word_count) AS context_word_count,
                   any_value(q.datasets) AS datasets,
                   any_value(q.child_ids) AS child_ids,
                   count(*)::INTEGER AS qwen_responses,
                   count(DISTINCT q.response_id)::INTEGER AS unique_response_ids,
                   sum(CASE WHEN q.tier='core75' THEN 1 ELSE 0 END)::INTEGER AS core75_responses,
                   sum(CASE WHEN q.tier='extension25' THEN 1 ELSE 0 END)::INTEGER AS extension25_responses,
                   avg(q.word_count) AS qwen_mean_word_count,
                   stddev_samp(q.word_count) AS qwen_sd_word_count,
                   median(q.word_count) AS qwen_median_word_count,
                   quantile_cont(q.word_count, 0.1) AS qwen_p10_word_count,
                   quantile_cont(q.word_count, 0.9) AS qwen_p90_word_count,
                   min(q.word_count) AS qwen_min_word_count,
                   max(q.word_count) AS qwen_max_word_count,
                   avg(q.k0_sum_bits) AS qwen_mean_k0_sum_bits,
                   stddev_samp(q.k0_sum_bits) AS qwen_sd_k0_sum_bits,
                   median(q.k0_sum_bits) AS qwen_median_k0_sum_bits,
                   avg(q.k3_sum_bits) AS qwen_mean_k3_sum_bits,
                   stddev_samp(q.k3_sum_bits) AS qwen_sd_k3_sum_bits,
                   median(q.k3_sum_bits) AS qwen_median_k3_sum_bits,
                   quantile_cont(q.k3_sum_bits, 0.1) AS qwen_p10_k3_sum_bits,
                   quantile_cont(q.k3_sum_bits, 0.9) AS qwen_p90_k3_sum_bits,
                   avg(q.k3_mean_bits_per_token) AS qwen_mean_k3_bits_per_token,
                   stddev_samp(q.k3_mean_bits_per_token) AS qwen_sd_k3_bits_per_token,
                   avg(q.context_support_bits) AS qwen_mean_context_support_bits,
                   stddev_samp(q.context_support_bits) AS qwen_sd_context_support_bits,
                   e.unique_response_count,
                   e.top_response_probability,
                   e.exact_string_entropy_bits
            FROM qwen_base q JOIN response_entropy e USING (context_id)
            GROUP BY q.context_id, e.unique_response_count, e.top_response_probability,
                     e.exact_string_entropy_bits
            """
        )
        context_checks = connection.execute(
            """
            SELECT count(*),
                   sum(qwen_responses <> 100),
                   sum(unique_response_ids <> 100),
                   sum(core75_responses <> 75),
                   sum(extension25_responses <> 25),
                   sum(qwen_sd_word_count IS NULL OR qwen_sd_word_count=0),
                   sum(qwen_sd_k3_sum_bits IS NULL OR qwen_sd_k3_sum_bits=0)
            FROM qwen_context_metrics
            """
        ).fetchone()
        require_equal(context_checks[0], expected.qwen_contexts, "Qwen context metric rows")
        for index, label in enumerate(
            ["contexts not at 100", "context duplicate response ids", "contexts not at core75", "contexts not at extension25"],
            start=1,
        ):
            require_equal(context_checks[index], 0, label)

        qwen_context_path = metrics_dir / "qwen_context_metrics.parquet"
        _copy_query(connection, "SELECT * FROM qwen_context_metrics ORDER BY context_id", qwen_context_path)

        reference_files = [
            str(path) for path in _qwen_files(args.qwen_root, "context_means/full100", "context_means")
        ]
        connection.execute(
            f"CREATE VIEW upstream_context_means AS SELECT * FROM "
            f"read_csv_auto({sql_list(reference_files)}, header=true, union_by_name=true)"
        )
        mean_validation = connection.execute(
            """
            SELECT count(*) AS joined,
                   sum(u.context_id IS NULL) AS missing_upstream,
                   max(abs(q.qwen_mean_k0_sum_bits-u.expected_k0_utterance_surprisal_bits)) AS max_k0_diff,
                   max(abs(q.qwen_mean_k3_sum_bits-u.expected_k3_utterance_surprisal_bits)) AS max_k3_diff,
                   max(abs(q.qwen_mean_context_support_bits-u.expected_context_support_bits)) AS max_support_diff
            FROM qwen_context_metrics q LEFT JOIN upstream_context_means u USING (context_id)
            """
        ).fetchone()
        require_equal(mean_validation[0], expected.qwen_contexts, "context-mean validation rows")
        require_equal(mean_validation[1], 0, "context means missing upstream")
        if max(float(mean_validation[2]), float(mean_validation[3]), float(mean_validation[4])) > 1e-9:
            raise RuntimeError(f"recomputed Qwen context means differ from upstream: {mean_validation}")

        row_join = connection.execute(
            """
            SELECT count(*) AS eligible,
                   sum(q.context_id IS NULL) AS unmatched,
                   count(DISTINCT r.context_id) AS contexts,
                   count(DISTINCT r.child_key) AS children,
                   count(DISTINCT r.dataset) AS corpora
            FROM row_map r LEFT JOIN qwen_context_metrics q USING (context_id)
            """
        ).fetchone()
        require_equal(row_join[0], expected.eligible_real_rows, "eligible real rows in Qwen join")
        require_equal(row_join[1], 0, "eligible real rows unmatched to Qwen")
        require_equal(row_join[2], expected.qwen_contexts, "joined real contexts")
        require_equal(row_join[3], expected.children, "joined children")
        require_equal(row_join[4], expected.corpora, "joined corpora")

        print("[metrics] computing context-normalized candidate coordinates and exact observed percentiles", flush=True)
        connection.execute(
            """
            CREATE TABLE qwen_arrays AS
            SELECT context_id, list(word_count) AS word_counts, list(k3_sum_bits) AS k3_scores
            FROM qwen_base GROUP BY context_id
            """
        )
        normalized_path = metrics_dir / "candidate_context_normalized.parquet"
        _copy_query(
            connection,
            """
            WITH normalized_base AS (
              SELECT c.candidate_key, c.utterance_id, c.context_id, c.dataset, c.child_key,
                     c.session_id, c.age_months, c.age_bin, c.source, c.source_label,
                     c.word_count, c.k0_sum_bits, c.k3_sum_bits, c.k3_mean_bits_per_token,
                     c.context_support_bits,
                     c.word_count-o.word_count AS word_effort_difference_vs_observed,
                     c.word_count-q.qwen_mean_word_count AS word_effort_difference_vs_qwen,
                     CASE WHEN q.qwen_sd_word_count > 0
                          THEN (c.word_count-q.qwen_mean_word_count)/q.qwen_sd_word_count END AS z_effort,
                     CASE WHEN q.qwen_sd_k3_sum_bits > 0
                          THEN (c.k3_sum_bits-q.qwen_mean_k3_sum_bits)/q.qwen_sd_k3_sum_bits END AS z_k3,
                     (len(list_filter(a.word_counts, x -> x < c.word_count)) +
                      0.5*len(list_filter(a.word_counts, x -> x = c.word_count))) / 100.0
                       AS effort_percentile_in_qwen,
                     CASE WHEN c.k3_sum_bits IS NOT NULL AND isfinite(c.k3_sum_bits) THEN
                       (len(list_filter(a.k3_scores, x -> x < c.k3_sum_bits)) +
                        0.5*len(list_filter(a.k3_scores, x -> x = c.k3_sum_bits))) / 100.0
                     END AS k3_percentile_in_qwen,
                     q.qwen_mean_word_count, q.qwen_sd_word_count,
                     q.qwen_mean_k3_sum_bits, q.qwen_sd_k3_sum_bits,
                     q.exact_string_entropy_bits
              FROM candidates c
              JOIN qwen_context_metrics q USING (context_id)
              JOIN qwen_arrays a USING (context_id)
              JOIN candidates o ON c.utterance_id=o.utterance_id AND o.source='observed_child'
            )
            SELECT *,
                   CASE WHEN source='observed_child' THEN effort_percentile_in_qwen END
                     AS observed_effort_percentile_in_qwen,
                   CASE WHEN source='observed_child' THEN k3_percentile_in_qwen END
                     AS observed_k3_percentile_in_qwen
            FROM normalized_base
            """,
            normalized_path,
        )
        connection.execute("DROP TABLE qwen_arrays")
        connection.execute(
            f"CREATE VIEW normalized AS SELECT * FROM read_parquet({sql_literal(normalized_path)})"
        )

        normalized_audit = connection.execute(
            """
            SELECT count(*) AS rows,
                   count(DISTINCT candidate_key) AS unique_keys,
                   sum(qwen_sd_word_count IS NULL OR qwen_sd_word_count=0) AS z_effort_excluded_rows,
                   sum(qwen_sd_k3_sum_bits IS NULL OR qwen_sd_k3_sum_bits=0) AS z_k3_excluded_rows,
                   sum(word_count IS NULL OR NOT isfinite(word_count)) AS nonfinite_effort,
                   sum(k3_sum_bits IS NULL OR NOT isfinite(k3_sum_bits)) AS nonfinite_k3,
                   sum(k0_sum_bits IS NULL OR NOT isfinite(k0_sum_bits)) AS nonfinite_k0,
                   sum(source='observed_child' AND observed_effort_percentile_in_qwen IS NULL) AS missing_effort_percentiles,
                   sum(source='observed_child' AND observed_k3_percentile_in_qwen IS NULL) AS missing_k3_percentiles,
                   sum(effort_percentile_in_qwen < 0 OR effort_percentile_in_qwen > 1) AS invalid_effort_percentiles,
                   sum(k3_percentile_in_qwen < 0 OR k3_percentile_in_qwen > 1) AS invalid_k3_percentiles
            FROM normalized
            """
        ).fetchone()

        print("[metrics] freezing pooled age/source cells and paired contrasts", flush=True)
        connection.execute(
            """
            CREATE TABLE qwen_opportunities AS
            SELECT r.utterance_id, r.context_id, r.dataset, r.child_key, r.age_months, r.age_bin,
                   'qwen'::VARCHAR AS source,
                   q.qwen_mean_word_count AS word_count,
                   q.qwen_mean_k3_sum_bits AS k3_sum_bits,
                   q.qwen_mean_k3_bits_per_token AS k3_mean_bits_per_token,
                   q.qwen_mean_k0_sum_bits AS k0_sum_bits,
                   q.qwen_mean_context_support_bits AS context_support_bits,
                   q.qwen_mean_word_count-o.word_count AS word_effort_difference_vs_observed,
                   0.0::DOUBLE AS z_effort,
                   0.0::DOUBLE AS z_k3,
                   0.5::DOUBLE AS effort_percentile_in_qwen,
                   0.5::DOUBLE AS k3_percentile_in_qwen
            FROM row_map r JOIN qwen_context_metrics q USING (context_id)
            JOIN normalized o ON r.utterance_id=o.utterance_id AND o.source='observed_child'
            """
        )
        model_cells_path = metrics_dir / "pooled_child_age_source_cells.parquet"
        _copy_query(
            connection,
            """
            WITH all_sources AS (
              SELECT utterance_id, context_id, dataset, child_key, age_months, age_bin, source,
                     word_count, k3_sum_bits, k3_mean_bits_per_token, k0_sum_bits,
                     context_support_bits, word_effort_difference_vs_observed, z_effort, z_k3,
                     effort_percentile_in_qwen, k3_percentile_in_qwen
              FROM normalized
              UNION ALL SELECT * FROM qwen_opportunities
            )
            SELECT dataset, child_key, age_months, age_bin, source, count(*)::INTEGER AS n_rows,
                   avg(word_count) AS mean_word_count, median(word_count) AS median_word_count,
                   avg(k3_sum_bits) AS mean_k3_sum_bits, median(k3_sum_bits) AS median_k3_sum_bits,
                   avg(k3_mean_bits_per_token) AS mean_k3_mean_bits_per_token,
                   median(k3_mean_bits_per_token) AS median_k3_mean_bits_per_token,
                   avg(k0_sum_bits) AS mean_k0_sum_bits, median(k0_sum_bits) AS median_k0_sum_bits,
                   avg(context_support_bits) AS mean_context_support_bits,
                   median(context_support_bits) AS median_context_support_bits,
                   avg(word_effort_difference_vs_observed) AS mean_word_effort_difference_vs_observed,
                   median(word_effort_difference_vs_observed) AS median_word_effort_difference_vs_observed,
                   avg(z_effort) AS mean_z_effort, median(z_effort) AS median_z_effort,
                   avg(z_k3) AS mean_z_k3, median(z_k3) AS median_z_k3,
                   avg(effort_percentile_in_qwen) AS mean_effort_percentile_in_qwen,
                   median(effort_percentile_in_qwen) AS median_effort_percentile_in_qwen,
                   avg(k3_percentile_in_qwen) AS mean_k3_percentile_in_qwen,
                   median(k3_percentile_in_qwen) AS median_k3_percentile_in_qwen
            FROM all_sources GROUP BY dataset, child_key, age_months, age_bin, source
            """,
            model_cells_path,
        )
        contrast_cells_path = metrics_dir / "pooled_child_age_contrast_cells.parquet"
        _copy_query(
            connection,
            """
            WITH observed AS (SELECT * FROM normalized WHERE source='observed_child'),
            comparator AS (
              SELECT utterance_id, source, word_count, k3_sum_bits, k3_mean_bits_per_token,
                     k0_sum_bits, context_support_bits, z_effort, z_k3,
                     effort_percentile_in_qwen, k3_percentile_in_qwen
              FROM normalized WHERE source<>'observed_child'
              UNION ALL
              SELECT utterance_id, source, word_count, k3_sum_bits, k3_mean_bits_per_token,
                     k0_sum_bits, context_support_bits, z_effort, z_k3,
                     effort_percentile_in_qwen, k3_percentile_in_qwen FROM qwen_opportunities
            ), paired AS (
              SELECT o.dataset, o.child_key, o.age_months, o.age_bin, c.source AS comparator,
                     o.word_count-c.word_count AS word_count,
                     o.k3_sum_bits-c.k3_sum_bits AS k3_sum_bits,
                     o.k3_mean_bits_per_token-c.k3_mean_bits_per_token AS k3_mean_bits_per_token,
                     o.k0_sum_bits-c.k0_sum_bits AS k0_sum_bits,
                     o.context_support_bits-c.context_support_bits AS context_support_bits,
                     (o.word_count-c.word_count) AS word_effort_difference_vs_observed,
                     o.z_effort-c.z_effort AS z_effort,
                     o.z_k3-c.z_k3 AS z_k3,
                     o.effort_percentile_in_qwen-c.effort_percentile_in_qwen AS effort_percentile_in_qwen,
                     o.k3_percentile_in_qwen-c.k3_percentile_in_qwen AS k3_percentile_in_qwen
              FROM observed o JOIN comparator c USING (utterance_id)
            )
            SELECT dataset, child_key, age_months, age_bin, comparator, count(*)::INTEGER AS n_rows,
                   avg(word_count) AS mean_word_count, median(word_count) AS median_word_count,
                   avg(k3_sum_bits) AS mean_k3_sum_bits, median(k3_sum_bits) AS median_k3_sum_bits,
                   avg(k3_mean_bits_per_token) AS mean_k3_mean_bits_per_token,
                   median(k3_mean_bits_per_token) AS median_k3_mean_bits_per_token,
                   avg(k0_sum_bits) AS mean_k0_sum_bits, median(k0_sum_bits) AS median_k0_sum_bits,
                   avg(context_support_bits) AS mean_context_support_bits,
                   median(context_support_bits) AS median_context_support_bits,
                   avg(word_effort_difference_vs_observed) AS mean_word_effort_difference_vs_observed,
                   median(word_effort_difference_vs_observed) AS median_word_effort_difference_vs_observed,
                   avg(z_effort) AS mean_z_effort, median(z_effort) AS median_z_effort,
                   avg(z_k3) AS mean_z_k3, median(z_k3) AS median_z_k3,
                   avg(effort_percentile_in_qwen) AS mean_effort_percentile_in_qwen,
                   median(effort_percentile_in_qwen) AS median_effort_percentile_in_qwen,
                   avg(k3_percentile_in_qwen) AS mean_k3_percentile_in_qwen,
                   median(k3_percentile_in_qwen) AS median_k3_percentile_in_qwen
            FROM paired GROUP BY dataset, child_key, age_months, age_bin, comparator
            """,
            contrast_cells_path,
        )

        age_summary_path = metrics_dir / "age_bin_source_summary.csv"
        _csv_from_query(
            connection,
            """
            WITH cells AS (SELECT * FROM read_parquet('""" + str(model_cells_path).replace("'", "''") + """'))
            SELECT age_bin, source, sum(n_rows)::BIGINT AS n_rows,
                   count(*)::INTEGER AS child_age_cells, count(DISTINCT child_key)::INTEGER AS children,
                   avg(mean_word_count) AS mean_word_count,
                   avg(mean_k3_sum_bits) AS mean_k3_sum_bits,
                   avg(mean_k3_mean_bits_per_token) AS mean_k3_bits_per_token,
                   avg(mean_k0_sum_bits) AS mean_k0_sum_bits,
                   avg(mean_context_support_bits) AS mean_context_support_bits,
                   avg(mean_z_effort) AS mean_z_effort, avg(mean_z_k3) AS mean_z_k3,
                   avg(mean_effort_percentile_in_qwen) AS mean_effort_percentile_in_qwen,
                   avg(mean_k3_percentile_in_qwen) AS mean_k3_percentile_in_qwen
            FROM cells GROUP BY age_bin, source
            ORDER BY CASE age_bin
              WHEN '006-023' THEN 1 WHEN '024-029' THEN 2 WHEN '030-035' THEN 3 WHEN '036-041' THEN 4
              WHEN '042-047' THEN 5 WHEN '048-053' THEN 6 WHEN '054-059' THEN 7 WHEN '060-065' THEN 8 END,
              CASE source WHEN 'observed_child' THEN 1 WHEN 'qwen' THEN 2 WHEN 'random' THEN 3
              WHEN 'unigram' THEN 4 WHEN 'bigram' THEN 5 WHEN 'trigram' THEN 6 ELSE 7 END
            """,
            age_summary_path,
        )

        source_counts_path = metrics_dir / "source_row_counts.csv"
        _csv_from_query(
            connection,
            """
            SELECT source, count(*)::BIGINT AS candidate_rows,
                   count(DISTINCT utterance_id)::BIGINT AS utterances,
                   count(DISTINCT child_key)::INTEGER AS children,
                   count(DISTINCT dataset)::INTEGER AS corpora,
                   sum(CASE WHEN k3_sum_bits IS NULL OR NOT isfinite(k3_sum_bits) THEN 1 ELSE 0 END)::BIGINT AS nonfinite_k3,
                   sum(CASE WHEN k0_sum_bits IS NULL OR NOT isfinite(k0_sum_bits) THEN 1 ELSE 0 END)::BIGINT AS nonfinite_k0
            FROM normalized GROUP BY source
            UNION ALL
            SELECT 'qwen', count(*)::BIGINT, count(DISTINCT utterance_id)::BIGINT,
                   count(DISTINCT child_key)::INTEGER, count(DISTINCT dataset)::INTEGER, 0, 0
            FROM qwen_opportunities ORDER BY source
            """,
            source_counts_path,
        )

        print("[metrics] computing complete word-length distributions", flush=True)
        connection.execute(
            "CREATE TABLE qwen_length_by_context AS SELECT context_id, CAST(word_count AS INTEGER) AS word_count, "
            "count(*)::BIGINT AS n, sum(k3_sum_bits) AS sum_k3_sum_bits, "
            "sum(k3_mean_bits_per_token) AS sum_k3_bits_per_token, "
            "sum(k0_sum_bits) AS sum_k0_sum_bits, "
            "sum(context_support_bits) AS sum_context_support_bits "
            "FROM qwen_base GROUP BY context_id, word_count"
        )
        print("[metrics] freezing exact model-by-length-by-age cells", flush=True)
        length_age_cells_path = metrics_dir / "child_age_model_length_cells.parquet"
        _copy_query(
            connection,
            f"""
            WITH candidate_cells AS (
              SELECT dataset, child_key, age_months, age_bin, source,
                     CAST(word_count AS INTEGER) AS word_count,
                     count(*)::BIGINT AS n_rows,
                     count(k3_sum_bits)::BIGINT AS n_k3_rows,
                     avg(k3_sum_bits) AS mean_k3_sum_bits,
                     avg(k3_mean_bits_per_token) AS mean_k3_bits_per_token,
                     avg(k0_sum_bits) AS mean_k0_sum_bits,
                     avg(context_support_bits) AS mean_context_support_bits
              FROM normalized
              WHERE word_count BETWEEN {min(FIXED_LENGTHS)} AND {max(FIXED_LENGTHS)}
              GROUP BY dataset, child_key, age_months, age_bin, source, CAST(word_count AS INTEGER)
            ), qwen_cells AS (
              SELECT r.dataset, r.child_key, r.age_months, r.age_bin,
                     'qwen'::VARCHAR AS source, q.word_count,
                     sum(q.n)::BIGINT AS n_rows,
                     sum(q.n)::BIGINT AS n_k3_rows,
                     sum(q.sum_k3_sum_bits)/sum(q.n) AS mean_k3_sum_bits,
                     sum(q.sum_k3_bits_per_token)/sum(q.n) AS mean_k3_bits_per_token,
                     sum(q.sum_k0_sum_bits)/sum(q.n) AS mean_k0_sum_bits,
                     sum(q.sum_context_support_bits)/sum(q.n) AS mean_context_support_bits
              FROM row_map r JOIN qwen_length_by_context q USING (context_id)
              WHERE q.word_count BETWEEN {min(FIXED_LENGTHS)} AND {max(FIXED_LENGTHS)}
              GROUP BY r.dataset, r.child_key, r.age_months, r.age_bin, q.word_count
            )
            SELECT * FROM candidate_cells UNION ALL SELECT * FROM qwen_cells
            ORDER BY source, word_count, age_months, dataset, child_key
            """,
            length_age_cells_path,
        )
        connection.execute(
            f"CREATE VIEW length_age_cells AS SELECT * FROM read_parquet({sql_literal(length_age_cells_path)})"
        )
        length_age_summary_path = metrics_dir / "age_bin_model_length_summary.csv"
        _csv_from_query(
            connection,
            """
            SELECT source, age_bin, word_count,
                   sum(n_rows)::BIGINT AS n_rows,
                   sum(n_k3_rows)::BIGINT AS n_k3_rows,
                   count(*)::INTEGER AS child_age_cells,
                   count(DISTINCT child_key)::INTEGER AS children,
                   sum(age_months*n_k3_rows)/sum(n_k3_rows) AS mean_age_months,
                   sum(mean_k3_sum_bits*n_k3_rows)/sum(n_k3_rows) AS mean_k3_sum_bits,
                   sum(mean_k3_bits_per_token*n_k3_rows)/sum(n_k3_rows) AS mean_k3_bits_per_token,
                   sum(mean_k0_sum_bits*n_k3_rows)/sum(n_k3_rows) AS mean_k0_sum_bits,
                   sum(mean_context_support_bits*n_k3_rows)/sum(n_k3_rows) AS mean_context_support_bits
            FROM length_age_cells
            WHERE n_k3_rows > 0
            GROUP BY source, age_bin, word_count
            ORDER BY source, word_count,
              CASE age_bin
                WHEN '006-023' THEN 1 WHEN '024-029' THEN 2 WHEN '030-035' THEN 3
                WHEN '036-041' THEN 4 WHEN '042-047' THEN 5 WHEN '048-053' THEN 6
                WHEN '054-059' THEN 7 WHEN '060-065' THEN 8 END
            """,
            length_age_summary_path,
        )
        length_age_checks = connection.execute(
            """
            SELECT count(*) AS rows,
                   count(DISTINCT (dataset, child_key, age_months, source, word_count)) AS unique_keys,
                   count(DISTINCT source) AS sources,
                   min(word_count) AS minimum_length,
                   max(word_count) AS maximum_length,
                   sum(n_rows <= 0 OR n_k3_rows <= 0) AS invalid_weight_rows,
                   sum(mean_k3_sum_bits IS NULL OR NOT isfinite(mean_k3_sum_bits)) AS invalid_k3_cells
            FROM length_age_cells
            """
        ).fetchone()
        length_path = metrics_dir / "length_distribution_by_age_source.csv.gz"
        length_query = """
            WITH candidate_lengths AS (
              SELECT n.age_bin, n.source, CAST(n.word_count AS INTEGER) AS word_count, count(*)::BIGINT AS n
              FROM normalized n GROUP BY n.age_bin, n.source, CAST(n.word_count AS INTEGER)
            ), qwen_lengths AS (
              SELECT r.age_bin, 'qwen'::VARCHAR AS source, q.word_count,
                     sum(q.n)::BIGINT AS n
              FROM row_map r JOIN qwen_length_by_context q USING (context_id)
              GROUP BY r.age_bin, q.word_count
            )
            SELECT * FROM candidate_lengths UNION ALL SELECT * FROM qwen_lengths
            ORDER BY age_bin, source, word_count
        """
        atomic_csv(connection.execute(length_query).fetchdf(), length_path)

        print("[metrics] freezing reproducible response-level plot/browser samples", flush=True)
        connection.execute(
            """
            CREATE TABLE qwen_sample AS
            WITH sampled AS (
              SELECT * FROM qwen_base WHERE hash(response_id, 20260824) % 100 < 2
            ), joined AS (
              SELECT r.utterance_id, r.dataset, r.child_key, r.age_months, r.age_bin,
                     s.response_id, s.context_id, s.target_text, s.word_count,
                     s.k0_sum_bits, s.k3_sum_bits, s.k3_mean_bits_per_token,
                     s.context_support_bits,
                     (s.word_count-q.qwen_mean_word_count)/NULLIF(q.qwen_sd_word_count,0) AS z_effort,
                     (s.k3_sum_bits-q.qwen_mean_k3_sum_bits)/NULLIF(q.qwen_sd_k3_sum_bits,0) AS z_k3,
                     row_number() OVER (
                       PARTITION BY r.age_bin, r.dataset
                       ORDER BY hash(s.response_id, r.utterance_id, 20260824)
                     ) AS sample_rank
              FROM sampled s JOIN row_map r USING (context_id)
              JOIN qwen_context_metrics q USING (context_id)
            )
            SELECT * EXCLUDE(sample_rank) FROM joined WHERE sample_rank <= 1200
            """
        )
        plot_sample_path = metrics_dir / "plot_sample.csv.gz"
        candidate_sample = connection.execute(
            """
            WITH ranked AS (
              SELECT n.*, row_number() OVER (
                PARTITION BY n.age_bin, n.dataset, n.source ORDER BY hash(n.candidate_key, 20260824)
              ) AS sample_rank
              FROM normalized n WHERE isfinite(n.k3_sum_bits) AND isfinite(n.word_count)
            )
            SELECT utterance_id, dataset, child_key, age_months, age_bin, source,
                   candidate_key AS point_id, '' AS response_id, context_id, '' AS target_text,
                   word_count, k0_sum_bits, k3_sum_bits, k3_mean_bits_per_token,
                   context_support_bits, z_effort, z_k3,
                   effort_percentile_in_qwen, k3_percentile_in_qwen
            FROM ranked WHERE sample_rank <= 500
            """
        ).fetchdf()
        qwen_sample = connection.execute(
            """
            SELECT utterance_id, dataset, child_key, age_months, age_bin, 'qwen' AS source,
                   response_id AS point_id, response_id, context_id, target_text,
                   word_count, k0_sum_bits, k3_sum_bits, k3_mean_bits_per_token,
                   context_support_bits, z_effort, z_k3,
                   NULL::DOUBLE AS effort_percentile_in_qwen,
                   NULL::DOUBLE AS k3_percentile_in_qwen FROM qwen_sample
            """
        ).fetchdf()
        plot_sample = pd.concat([candidate_sample, qwen_sample], ignore_index=True)
        atomic_csv(plot_sample, plot_sample_path)
        browser_sample_path = metrics_dir / "browser_sample.csv.gz"
        browser_parts = []
        for source, group in plot_sample.groupby("source", sort=False):
            limit = 32_000 if source == "qwen" else 12_000
            browser_parts.append(group.sample(n=min(len(group), limit), random_state=20260824))
        atomic_csv(pd.concat(browser_parts, ignore_index=True), browser_sample_path)

        gallery_contexts = connection.execute(
            """
            WITH eligible AS (
              SELECT n.context_id, n.utterance_id, n.age_bin, n.age_months, n.dataset,
                     n.child_key, n.effort_percentile_in_qwen,
                     n.k3_percentile_in_qwen, n.word_count, n.k3_sum_bits,
                     count(*) OVER (PARTITION BY n.context_id) AS context_rows,
                     median(n.effort_percentile_in_qwen) OVER (PARTITION BY n.age_bin) AS age_median_effort_percentile,
                     median(n.k3_percentile_in_qwen) OVER (PARTITION BY n.age_bin) AS age_median_k3_percentile
              FROM normalized n
              WHERE n.source='observed_child'
                AND n.effort_percentile_in_qwen IS NOT NULL
                AND n.k3_percentile_in_qwen IS NOT NULL
                AND n.qwen_sd_word_count > 0
                AND n.qwen_sd_k3_sum_bits > 0
            ), ranked AS (
              SELECT *, row_number() OVER (
                PARTITION BY age_bin
                ORDER BY context_rows,
                         abs(effort_percentile_in_qwen-age_median_effort_percentile) +
                         abs(k3_percentile_in_qwen-age_median_k3_percentile),
                         hash(utterance_id, 20260824)
              ) AS rn
              FROM eligible
            )
            SELECT context_id, utterance_id, age_bin, age_months, dataset, child_key,
                   context_rows, effort_percentile_in_qwen, k3_percentile_in_qwen,
                   word_count AS observed_word_count, k3_sum_bits AS observed_k3_sum_bits
            FROM ranked WHERE rn=1 ORDER BY age_bin
            """
        ).fetchdf()
        gallery_ids = gallery_contexts["context_id"].astype(str).tolist()
        connection.register("gallery_ids", pd.DataFrame({"context_id": gallery_ids}))
        connection.register("gallery_contexts", gallery_contexts)
        gallery_qwen = connection.execute(
            """
            SELECT q.context_id, q.response_id AS candidate_key, 'qwen' AS source,
                   q.target_text, q.word_count, q.k0_sum_bits, q.k3_sum_bits,
                   q.k3_mean_bits_per_token, q.context_support_bits, q.selected_sample_index,
                   q.tier
            FROM qwen_base q JOIN gallery_ids g USING (context_id)
            """
        ).fetchdf()
        gallery_candidates = connection.execute(
            """
            SELECT c.context_id, c.candidate_key, c.source, c.target_text, c.word_count,
                   c.k0_sum_bits, c.k3_sum_bits, c.k3_mean_bits_per_token,
                   c.context_support_bits, NULL::INTEGER AS selected_sample_index,
                   ''::VARCHAR AS tier
            FROM candidates c JOIN gallery_ids g USING (context_id)
            JOIN gallery_contexts gc ON c.utterance_id=gc.utterance_id
            """
        ).fetchdf()
        gallery_path = metrics_dir / "gallery_responses.csv.gz"
        atomic_csv(pd.concat([gallery_qwen, gallery_candidates], ignore_index=True), gallery_path)
        gallery_contexts_path = metrics_dir / "gallery_contexts.csv"
        atomic_csv(gallery_contexts, gallery_contexts_path)

        token_cap_path = metrics_dir / "qwen_token_cap_diagnostics.json"
        token_cap = {
            "generator_max_new_tokens": 96,
            "selected_qwen_responses": expected.qwen_responses,
            "maximum_cleaned_word_count": int(integrity[12]),
            "maximum_mistral_evaluation_tokens": int(integrity[13]),
            "direct_hit_max_new_tokens_rows": None,
            "direct_hit_max_new_tokens_proportion": None,
            "status": "NOT_IDENTIFIABLE_FROM_SCORED_HANDOFF",
            "reason": (
                "The full100 scoring handoff retains target text and Mistral evaluation-token counts but strips "
                "Qwen generated_token_count and hit_max_new_tokens. Mistral evaluation tokens cannot be used as "
                "Qwen generation tokens. The upstream qwen_child_response_contract_v3 rejects responses that "
                "hit the cap without an end-of-turn boundary, but exact any-cap incidence among accepted rows is unavailable."
            ),
            "protocol_no_boundary_before_cap_selected_rate": 0.0,
            "interpretation": "Length tails are reported exactly; cap incidence is an explicit unavailable field, not imputed.",
        }
        atomic_json(token_cap, token_cap_path)

        audit = {
            "status": "PASS_CORE_METRICS",
            "qwen": {
                "responses": int(integrity[0]),
                "contexts": int(integrity[1]),
                "unique_response_ids": int(integrity[2]),
                "core75_rows": int(integrity[5]),
                "extension25_rows": int(integrity[6]),
                "response_context_mismatches": int(integrity[7]),
                "nonfinite_rows": int(integrity[8]),
                "zero_word_rows": int(integrity[9]),
                "invalid_word_rows": int(integrity[10]),
                "nonpositive_eval_token_rows": int(integrity[11]),
                "contexts_with_zero_or_undefined_word_sd": int(context_checks[5]),
                "contexts_with_zero_or_undefined_k3_sd": int(context_checks[6]),
                "upstream_context_mean_max_abs_differences": {
                    "k0": float(mean_validation[2]),
                    "k3": float(mean_validation[3]),
                    "context_support": float(mean_validation[4]),
                },
            },
            "real_qwen_join": {
                "eligible_real_rows": int(row_join[0]),
                "unmatched_real_rows": int(row_join[1]),
                "contexts": int(row_join[2]),
                "children": int(row_join[3]),
                "corpora": int(row_join[4]),
            },
            "normalized_candidates": {
                "rows": int(normalized_audit[0]),
                "unique_keys": int(normalized_audit[1]),
                "z_effort_excluded_rows": int(normalized_audit[2]),
                "z_k3_excluded_rows": int(normalized_audit[3]),
                "nonfinite_effort_rows": int(normalized_audit[4]),
                "nonfinite_k3_rows": int(normalized_audit[5]),
                "nonfinite_k0_rows": int(normalized_audit[6]),
                "missing_observed_effort_percentiles": int(normalized_audit[7]),
                "missing_observed_k3_percentiles": int(normalized_audit[8]),
                "invalid_effort_percentiles": int(normalized_audit[9]),
                "invalid_k3_percentiles": int(normalized_audit[10]),
            },
            "model_length_age_cells": {
                "rows": int(length_age_checks[0]),
                "unique_keys": int(length_age_checks[1]),
                "sources": int(length_age_checks[2]),
                "minimum_length": int(length_age_checks[3]),
                "maximum_length": int(length_age_checks[4]),
                "invalid_weight_rows": int(length_age_checks[5]),
                "invalid_k3_cells": int(length_age_checks[6]),
                "fixed_lengths": list(FIXED_LENGTHS),
                "unit": "one child-age-model-exact-length cell",
            },
            "token_cap": token_cap,
        }
        audit_path = metrics_dir / "metric_audit.json"
        atomic_json(audit, audit_path)
        connection.close()

    schema_path = args.output_dir / "schemas/context_normalized_candidates.schema.json"
    write_schema(
        schema_path,
        {
            "candidate_key": "string",
            "source": "enum",
            "word_count": "float",
            "k3_sum_bits": "float",
            "z_effort": "float|null when Qwen within-context SD is zero/undefined",
            "z_k3": "float|null when Qwen within-context SD is zero/undefined",
            "effort_percentile_in_qwen": "float [0,1], exact midrank for every candidate",
            "k3_percentile_in_qwen": "float [0,1], exact midrank for every finite-score candidate",
            "observed_effort_percentile_in_qwen": "float [0,1], observed only",
            "observed_k3_percentile_in_qwen": "float [0,1], observed only",
        },
        primary_key=["candidate_key"],
        description="Observed and same-length non-LSTM candidates normalized to their exact Qwen100 context.",
    )
    outputs = {
        "qwen_context_metrics": qwen_context_path,
        "normalized_candidates": normalized_path,
        "model_cells": model_cells_path,
        "contrast_cells": contrast_cells_path,
        "age_summary": age_summary_path,
        "source_counts": source_counts_path,
        "length_distribution": length_path,
        "length_age_cells": length_age_cells_path,
        "length_age_summary": length_age_summary_path,
        "plot_sample": plot_sample_path,
        "browser_sample": browser_sample_path,
        "gallery_responses": gallery_path,
        "gallery_contexts": gallery_contexts_path,
        "token_cap_diagnostics": token_cap_path,
        "metric_audit": audit_path,
        "normalized_schema": schema_path,
    }
    return stage_manifest(
        stage="metrics",
        inputs={"dataset_manifest": dataset_manifest_path, "candidates": candidates_path},
        outputs=outputs,
        metadata={"expected": asdict(expected), "audit": audit, "lstm_included": False},
        destination=metrics_dir / "metrics_manifest.json",
    )


def _weighted_quadratic_fit(ages: np.ndarray, values: np.ndarray, weights: np.ndarray) -> np.ndarray | None:
    finite = np.isfinite(ages) & np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if finite.sum() < 4 or np.unique(ages[finite]).size < 3:
        return None
    scaled = (ages[finite] - 39.0) / 12.0
    design = np.column_stack([np.ones(finite.sum()), scaled, scaled**2])
    root_weight = np.sqrt(weights[finite])
    try:
        coefficients, _, rank, _ = np.linalg.lstsq(design * root_weight[:, None], values[finite] * root_weight, rcond=None)
    except np.linalg.LinAlgError:
        return None
    return coefficients if rank == 3 else None


def _predict_quadratic(coefficients: np.ndarray, ages: Sequence[float]) -> np.ndarray:
    scaled = (np.asarray(ages, dtype=float) - 39.0) / 12.0
    return coefficients[0] + coefficients[1] * scaled + coefficients[2] * scaled**2


def fit_child_bootstrap_trajectories(
    cells: pd.DataFrame,
    *,
    source_column: str,
    draws: int,
    seed: int,
    precise_ages: Sequence[int] = PRECISE_AGES,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Fit pooled quadratic age trajectories with whole-child resampling."""

    required = {"child_key", "age_months", source_column}
    missing = required - set(cells.columns)
    if missing:
        raise KeyError(f"trajectory cells missing columns: {sorted(missing)}")
    children = np.array(sorted(cells["child_key"].astype(str).unique()))
    child_codes = pd.Categorical(cells["child_key"].astype(str), categories=children).codes
    ages = pd.to_numeric(cells["age_months"], errors="coerce").to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    bootstrap_child_weights = rng.multinomial(len(children), np.repeat(1 / len(children), len(children)), size=draws)
    estimate_rows: list[dict[str, Any]] = []
    coefficient_rows: list[dict[str, Any]] = []
    failures = 0
    for source in sorted(cells[source_column].dropna().astype(str).unique(), key=lambda x: SOURCE_ORDER.index(x) if x in SOURCE_ORDER else 99):
        source_mask = cells[source_column].astype(str).eq(source).to_numpy()
        for outcome in MODEL_OUTCOMES:
            for summary in ("mean", "median"):
                column = f"{summary}_{outcome}"
                if column not in cells.columns:
                    continue
                values = pd.to_numeric(cells[column], errors="coerce").to_numpy(dtype=float)
                mask = source_mask & np.isfinite(ages) & np.isfinite(values)
                point = _weighted_quadratic_fit(ages[mask], values[mask], np.ones(mask.sum()))
                if point is None:
                    failures += 1
                    continue
                point_predictions = _predict_quadratic(point, precise_ages)
                bootstrap_predictions: list[np.ndarray] = []
                for child_weights in bootstrap_child_weights:
                    row_weights = child_weights[child_codes[mask]]
                    fit = _weighted_quadratic_fit(ages[mask], values[mask], row_weights)
                    if fit is not None:
                        bootstrap_predictions.append(_predict_quadratic(fit, precise_ages))
                if bootstrap_predictions:
                    matrix = np.vstack(bootstrap_predictions)
                    lows = np.quantile(matrix, 0.025, axis=0)
                    highs = np.quantile(matrix, 0.975, axis=0)
                else:
                    lows = np.repeat(np.nan, len(precise_ages))
                    highs = np.repeat(np.nan, len(precise_ages))
                for age, estimate, low, high in zip(precise_ages, point_predictions, lows, highs):
                    estimate_rows.append(
                        {
                            "source": source,
                            "outcome": outcome,
                            "summary": summary,
                            "age_months": age,
                            "estimate": float(estimate),
                            "ci_low": float(low),
                            "ci_high": float(high),
                            "bootstrap_successes": len(bootstrap_predictions),
                            "bootstrap_requested": draws,
                            "children": int(pd.Series(cells.loc[mask, "child_key"]).nunique()),
                            "child_age_cells": int(mask.sum()),
                            "model": "unweighted child-age-cell quadratic age trajectory",
                        }
                    )
                for term, value in zip(("intercept_at_39_months", "age_years_centered", "age_years_centered_squared"), point):
                    coefficient_rows.append(
                        {
                            "source": source,
                            "outcome": outcome,
                            "summary": summary,
                            "term": term,
                            "estimate": float(value),
                            "children": int(pd.Series(cells.loc[mask, "child_key"]).nunique()),
                            "child_age_cells": int(mask.sum()),
                        }
                    )
    return pd.DataFrame(estimate_rows), pd.DataFrame(coefficient_rows), {
        "sources": int(cells[source_column].nunique()),
        "children": len(children),
        "bootstrap_draws": draws,
        "trajectory_fit_failures": failures,
        "age_basis": "1 + ((age_months-39)/12) + ((age_months-39)/12)^2",
        "cell_weighting": "one vote per child-age-source cell",
        "uncertainty": "whole-child nonparametric bootstrap percentile interval",
    }


def marginal_fixed_length_predictions(
    result: Any,
    data: pd.DataFrame,
    *,
    source: str,
    outcome: str,
    specification: str,
    ages: Sequence[int],
) -> pd.DataFrame:
    """Average child-fixed prediction design rows at each exact age/length slice."""

    children = sorted(data["child_key"].astype(str).unique())
    design_info = result.model.data.design_info
    parameters = np.asarray(result.params, dtype=float)
    covariance = np.asarray(result.cov_params(), dtype=float)
    rows: list[dict[str, Any]] = []
    for age in ages:
        age_c = (float(age) - 39.0) / 12.0
        for length in FIXED_LENGTHS:
            new_data = pd.DataFrame(
                {
                    "age_months": float(age),
                    "age_c": age_c,
                    "age_c2": age_c**2,
                    "word_count": int(length),
                    "child_key": children,
                }
            )
            design = np.asarray(
                build_design_matrices([design_info], new_data, return_type="dataframe")[0],
                dtype=float,
            )
            marginal_design = design.mean(axis=0)
            estimate = float(marginal_design @ parameters)
            variance = float(marginal_design @ covariance @ marginal_design)
            standard_error = math.sqrt(max(0.0, variance)) if np.isfinite(variance) else np.nan
            rows.append(
                {
                    "source": source,
                    "outcome": outcome,
                    "specification": specification,
                    "age_months": int(age),
                    "word_count": int(length),
                    "estimate": estimate,
                    "standard_error": standard_error,
                    "ci_low": estimate - 1.96 * standard_error,
                    "ci_high": estimate + 1.96 * standard_error,
                    "children_marginalized": len(children),
                }
            )
    return pd.DataFrame(rows)


def fit_fixed_length_model_suite(
    cells: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Fit the fixed-length regression suite that underlies the 2D/3D atlas."""

    data = cells.copy()
    data = data[
        data["word_count"].isin(FIXED_LENGTHS)
        & pd.to_numeric(data["n_k3_rows"], errors="coerce").gt(0)
    ].copy()
    data["age_c"] = (pd.to_numeric(data["age_months"], errors="coerce") - 39.0) / 12.0
    data["age_c2"] = data["age_c"] ** 2
    data["word_count"] = pd.to_numeric(data["word_count"], errors="raise").astype(int)
    data["child_key"] = data["child_key"].astype(str)
    data["source"] = data["source"].astype(str)
    age_min = max(6, int(math.floor(float(data["age_months"].min()))))
    age_max = min(65, int(math.ceil(float(data["age_months"].max()))))
    prediction_ages = tuple(range(age_min, age_max + 1))
    specifications = (
        (
            "primary_linear_exact_length_child_fe",
            "mean_k3_sum_bits",
            "mean_k3_sum_bits ~ age_c + C(word_count) + C(child_key)",
            True,
        ),
        (
            "quadratic_age_exact_length_child_fe",
            "mean_k3_sum_bits",
            "mean_k3_sum_bits ~ age_c + age_c2 + C(word_count) + C(child_key)",
            True,
        ),
        (
            "age_bin_exact_length_child_fe",
            "mean_k3_sum_bits",
            "mean_k3_sum_bits ~ C(age_bin, Treatment(reference='006-023')) + C(word_count) + C(child_key)",
            False,
        ),
        (
            "age_by_length_child_fe",
            "mean_k3_sum_bits",
            "mean_k3_sum_bits ~ age_c * C(word_count) + C(child_key)",
            False,
        ),
        (
            "bits_per_token_linear_exact_length_child_fe",
            "mean_k3_bits_per_token",
            "mean_k3_bits_per_token ~ age_c + C(word_count) + C(child_key)",
            False,
        ),
    )
    coefficient_frames: list[pd.DataFrame] = []
    prediction_frames: list[pd.DataFrame] = []
    registry_rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for source in SOURCE_ORDER:
        if source == "lstm":
            continue
        source_data = data[data["source"].eq(source)].dropna(
            subset=["age_months", "word_count", "child_key", "n_k3_rows"]
        ).copy()
        for specification, outcome, formula, save_predictions in specifications:
            fit_data = source_data.dropna(subset=[outcome]).copy()
            try:
                result = smf.wls(formula, data=fit_data, weights=fit_data["n_k3_rows"]).fit(
                    cov_type="cluster", cov_kwds={"groups": fit_data["child_key"]}
                )
            except Exception as error:  # pragma: no cover - audited production failure path
                failures.append({"source": source, "specification": specification, "error": repr(error)})
                continue
            interval = result.conf_int()
            coefficient_frames.append(
                pd.DataFrame(
                    {
                        "source": source,
                        "outcome": outcome,
                        "specification": specification,
                        "term": result.params.index,
                        "estimate": np.asarray(result.params, dtype=float),
                        "standard_error": np.asarray(result.bse, dtype=float),
                        "ci_low": np.asarray(interval.iloc[:, 0], dtype=float),
                        "ci_high": np.asarray(interval.iloc[:, 1], dtype=float),
                        "p_value": np.asarray(result.pvalues, dtype=float),
                        "child_age_length_cells": len(fit_data),
                        "weighted_rows": int(fit_data["n_k3_rows"].sum()),
                        "children": int(fit_data["child_key"].nunique()),
                        "r_squared": float(result.rsquared),
                    }
                )
            )
            if save_predictions:
                prediction_frames.append(
                    marginal_fixed_length_predictions(
                        result,
                        fit_data,
                        source=source,
                        outcome=outcome,
                        specification=specification,
                        ages=prediction_ages,
                    )
                )
            registry_rows.append(
                {
                    "source": source,
                    "specification": specification,
                    "outcome": outcome,
                    "formula": formula,
                    "estimator": "opportunity-weighted WLS",
                    "uncertainty": "child-clustered sandwich covariance",
                    "status": "PASS",
                    "cells": len(fit_data),
                    "weighted_rows": int(fit_data["n_k3_rows"].sum()),
                    "children": int(fit_data["child_key"].nunique()),
                }
            )

    joint_data = data.dropna(subset=["mean_k3_sum_bits"]).copy()
    source_totals = joint_data.groupby("source", observed=True)["n_k3_rows"].transform("sum")
    joint_data["source_balanced_weight"] = joint_data["n_k3_rows"] / source_totals
    joint_specification = "joint_age_by_model_exact_length_child_fe"
    joint_formula = (
        "mean_k3_sum_bits ~ age_c * C(source, Treatment(reference='observed_child')) + "
        "C(source, Treatment(reference='observed_child')) * C(word_count) + C(child_key)"
    )
    try:
        joint_result = smf.wls(
            joint_formula, data=joint_data, weights=joint_data["source_balanced_weight"]
        ).fit(cov_type="cluster", cov_kwds={"groups": joint_data["child_key"]})
        joint_interval = joint_result.conf_int()
        coefficient_frames.append(
            pd.DataFrame(
                {
                    "source": "all_sources",
                    "outcome": "mean_k3_sum_bits",
                    "specification": joint_specification,
                    "term": joint_result.params.index,
                    "estimate": np.asarray(joint_result.params, dtype=float),
                    "standard_error": np.asarray(joint_result.bse, dtype=float),
                    "ci_low": np.asarray(joint_interval.iloc[:, 0], dtype=float),
                    "ci_high": np.asarray(joint_interval.iloc[:, 1], dtype=float),
                    "p_value": np.asarray(joint_result.pvalues, dtype=float),
                    "child_age_length_cells": len(joint_data),
                    "weighted_rows": int(joint_data["n_k3_rows"].sum()),
                    "children": int(joint_data["child_key"].nunique()),
                    "r_squared": float(joint_result.rsquared),
                }
            )
        )
        registry_rows.append(
            {
                "source": "all_sources",
                "specification": joint_specification,
                "outcome": "mean_k3_sum_bits",
                "formula": joint_formula,
                "estimator": "source-balanced opportunity-weighted WLS",
                "uncertainty": "child-clustered sandwich covariance",
                "status": "PASS",
                "cells": len(joint_data),
                "weighted_rows": int(joint_data["n_k3_rows"].sum()),
                "children": int(joint_data["child_key"].nunique()),
            }
        )
    except Exception as error:  # pragma: no cover - audited production failure path
        failures.append({"source": "all_sources", "specification": joint_specification, "error": repr(error)})

    coefficients = pd.concat(coefficient_frames, ignore_index=True) if coefficient_frames else pd.DataFrame()
    predictions = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    registry = pd.DataFrame(registry_rows)
    expected_fits = (len(SOURCE_ORDER) - 1) * len(specifications) + 1
    audit = {
        "status": "PASS" if not failures and len(registry) == expected_fits else "FAIL",
        "expected_fits": expected_fits,
        "completed_fits": len(registry),
        "failures": failures,
        "sources": sorted(data["source"].unique().tolist()),
        "fixed_lengths": list(FIXED_LENGTHS),
        "age_grid": [age_min, age_max],
        "prediction_rows": len(predictions),
        "coefficient_rows": len(coefficients),
        "primary_estimand": (
            "within-source age association in Mistral k3 total bits at exact word length, "
            "with child identity controlled"
        ),
        "joint_weighting": "each source receives equal total model weight; opportunity weights retained within source",
    }
    if audit["status"] != "PASS":
        raise RuntimeError(f"fixed-length model suite failed: {audit}")
    return predictions, coefficients, registry, audit


def run_models_stage(args: argparse.Namespace) -> dict[str, Any]:
    metrics_manifest_path = args.output_dir / "metrics/metrics_manifest.json"
    metrics_manifest = require_stage_manifest(metrics_manifest_path, "metrics")
    model_cells_path = Path(metrics_manifest["outputs"]["model_cells"]["path"])
    contrast_cells_path = Path(metrics_manifest["outputs"]["contrast_cells"]["path"])
    length_age_cells_path = Path(metrics_manifest["outputs"]["length_age_cells"]["path"])
    connection = duckdb.connect()
    cells = connection.execute("SELECT * FROM read_parquet(?)", [str(model_cells_path)]).fetchdf()
    contrasts = connection.execute("SELECT * FROM read_parquet(?)", [str(contrast_cells_path)]).fetchdf()
    length_age_cells = connection.execute(
        "SELECT * FROM read_parquet(?)", [str(length_age_cells_path)]
    ).fetchdf()
    connection.close()
    models_dir = args.output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"[models] fitting {len(cells):,} pooled child-age-source cells", flush=True)
    trajectories, coefficients, trajectory_audit = fit_child_bootstrap_trajectories(
        cells,
        source_column="source",
        draws=args.bootstrap_draws,
        seed=args.bootstrap_seed,
    )
    contrast_estimates, contrast_coefficients, contrast_audit = fit_child_bootstrap_trajectories(
        contrasts.rename(columns={"comparator": "source"}),
        source_column="source",
        draws=args.bootstrap_draws,
        seed=args.bootstrap_seed + 1,
    )
    contrast_estimates = contrast_estimates.rename(columns={"source": "comparator"})
    contrast_coefficients = contrast_coefficients.rename(columns={"source": "comparator"})
    print(
        f"[models] fitting fixed-length suite on {len(length_age_cells):,} model-length-age cells",
        flush=True,
    )
    fixed_predictions, fixed_coefficients, fixed_registry, fixed_audit = fit_fixed_length_model_suite(
        length_age_cells
    )
    trajectory_path = models_dir / "precise_age_source_trajectories.csv"
    coefficient_path = models_dir / "continuous_age_coefficients.csv"
    contrast_path = models_dir / "precise_age_observed_minus_source_contrasts.csv"
    contrast_coefficient_path = models_dir / "continuous_age_contrast_coefficients.csv"
    fixed_prediction_path = models_dir / "fixed_length_prediction_lines.csv.gz"
    fixed_coefficient_path = models_dir / "fixed_length_model_coefficients.csv.gz"
    fixed_registry_path = models_dir / "fixed_length_model_registry.csv"
    atomic_csv(trajectories, trajectory_path)
    atomic_csv(coefficients, coefficient_path)
    atomic_csv(contrast_estimates, contrast_path)
    atomic_csv(contrast_coefficients, contrast_coefficient_path)
    atomic_csv(fixed_predictions, fixed_prediction_path)
    atomic_csv(fixed_coefficients, fixed_coefficient_path)
    atomic_csv(fixed_registry, fixed_registry_path)
    registry = pd.DataFrame(
        [
            {
                "model_family": family,
                "outcome": outcome,
                "summary": summary,
                "age_basis": "quadratic continuous age centered at 39 months and scaled by 12",
                "prediction_ages": ",".join(map(str, PRECISE_AGES)),
                "uncertainty": "whole-child bootstrap percentile 95% interval",
                "sample": "all 79 children pooled",
            }
            for family in ("source_trajectory", "observed_minus_source_contrast")
            for outcome in MODEL_OUTCOMES
            for summary in ("mean", "median")
        ]
    )
    registry_path = models_dir / "model_registry.csv"
    atomic_csv(registry, registry_path)
    audit = {
        "status": "PASS",
        "pooled_all79_only": True,
        "source_trajectories": trajectory_audit,
        "observed_minus_source_contrasts": contrast_audit,
        "trajectory_rows": len(trajectories),
        "contrast_rows": len(contrast_estimates),
        "requested_ages": list(PRECISE_AGES),
        "raw_cross_section_claim_prohibited": True,
        "interpretation": (
            "Exact-month estimates are predictions from continuous quadratic age models; "
            "they are not independent raw cross-sections."
        ),
        "fixed_length_suite": fixed_audit,
    }
    audit_path = models_dir / "model_audit.json"
    atomic_json(audit, audit_path)
    return stage_manifest(
        stage="models",
        inputs={
            "metrics_manifest": metrics_manifest_path,
            "model_cells": model_cells_path,
            "contrast_cells": contrast_cells_path,
            "length_age_cells": length_age_cells_path,
        },
        outputs={
            "trajectories": trajectory_path,
            "coefficients": coefficient_path,
            "contrasts": contrast_path,
            "contrast_coefficients": contrast_coefficient_path,
            "fixed_length_predictions": fixed_prediction_path,
            "fixed_length_coefficients": fixed_coefficient_path,
            "fixed_length_registry": fixed_registry_path,
            "registry": registry_path,
            "model_audit": audit_path,
        },
        metadata={"audit": audit, "lstm_included": False},
        destination=models_dir / "models_manifest.json",
    )


def _source_marker(source: str) -> str:
    return {
        "observed_child": "*",
        "qwen": "o",
        "random": "X",
        "unigram": "P",
        "bigram": "s",
        "trigram": "D",
        "lstm": "^",
    }.get(source, "o")


def _source_size(source: str) -> float:
    return 180 if source == "observed_child" else 58


def add_covariance_ellipse(
    ax: Any,
    x: Sequence[float],
    y: Sequence[float],
    *,
    color: str,
    level: float = 0.80,
    linewidth: float = 1.5,
    alpha: float = 0.12,
) -> None:
    """Add a descriptive covariance ellipse; it is not a confidence region."""

    values = np.column_stack([pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")])
    values = values[np.isfinite(values).all(axis=1)]
    if len(values) < 3:
        return
    covariance = np.cov(values, rowvar=False)
    if not np.isfinite(covariance).all() or np.linalg.matrix_rank(covariance) < 2:
        return
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    if (eigenvalues <= 0).any():
        return
    # Chi-square quantile with two degrees of freedom: q = -2 log(1-level).
    radius = math.sqrt(-2.0 * math.log(1.0 - level))
    width, height = 2.0 * radius * np.sqrt(eigenvalues)
    angle = math.degrees(math.atan2(eigenvectors[1, 0], eigenvectors[0, 0]))
    ellipse = Ellipse(
        xy=values.mean(axis=0),
        width=width,
        height=height,
        angle=angle,
        facecolor=color,
        edgecolor=color,
        linewidth=linewidth,
        alpha=alpha,
        zorder=1,
    )
    ax.add_patch(ellipse)


def _axis_limits(sample: pd.DataFrame, x: str, y: str) -> tuple[tuple[float, float], tuple[float, float]]:
    xs = pd.to_numeric(sample[x], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    ys = pd.to_numeric(sample[y], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return (
        (max(0.0, float(xs.quantile(0.001)) - 0.5), float(xs.quantile(0.995)) * 1.05),
        (max(0.0, float(ys.quantile(0.001)) - 1.0), float(ys.quantile(0.995)) * 1.05),
    )


def plot_population_atlas(gallery: pd.DataFrame, gallery_contexts: pd.DataFrame, path: Path) -> None:
    """Plot one exact 100-response Qwen cloud and child point per age bin."""

    qwen_and_observed = gallery[gallery["source"].isin(["qwen", "observed_child"])].copy()
    x_values = pd.to_numeric(gallery["word_count"], errors="coerce").dropna()
    y_values = pd.to_numeric(qwen_and_observed["k3_sum_bits"], errors="coerce").dropna()
    xlim = (0.0, max(2.0, float(x_values.max()) * 1.08))
    ylim = (0.0, max(5.0, float(y_values.max()) * 1.10))
    context_lookup = gallery_contexts.set_index("age_bin")
    fig, axes = plt.subplots(2, 4, figsize=(18, 9.5), sharex=True, sharey=True, constrained_layout=True)
    for ax, age_bin in zip(axes.ravel(), AGE_BINS):
        if age_bin not in context_lookup.index:
            ax.set_visible(False)
            continue
        meta = context_lookup.loc[age_bin]
        context_id = str(meta["context_id"])
        child_label = str(meta["child_key"]).rsplit("/", 1)[-1]
        context_label = textwrap.shorten(
            " ".join(str(meta.get("context_text", "")).split()), width=52, placeholder="…"
        )
        panel = gallery[gallery["context_id"].astype(str).eq(context_id)]
        qwen = panel[panel["source"].eq("qwen")].dropna(subset=["word_count", "k3_sum_bits"])
        if not qwen.empty:
            ax.scatter(
                qwen["word_count"], qwen["k3_sum_bits"],
                s=22, color=SOURCE_COLORS["qwen"], alpha=0.58,
                edgecolors="white", linewidths=0.25, zorder=2,
            )
            add_covariance_ellipse(
                ax, qwen["word_count"], qwen["k3_sum_bits"],
                color="#969696", level=0.80, linewidth=1.4, alpha=0.14,
            )
        for source in ("observed_child", "random", "unigram", "bigram", "trigram", "lstm"):
            rows = panel[panel["source"].eq(source)].dropna(subset=["word_count", "k3_sum_bits"])
            if rows.empty:
                continue
            row = rows.iloc[0]
            actual_y = float(row["k3_sum_bits"])
            plotted_y = min(actual_y, ylim[1] * 0.965)
            ax.scatter(
                [float(row["word_count"])], [plotted_y],
                color=SOURCE_COLORS[source], marker=_source_marker(source),
                s=_source_size(source), linewidths=1.2,
                edgecolors="white", label=SOURCE_LABELS[source], zorder=6,
            )
            if actual_y > ylim[1]:
                ax.annotate(
                    f"↑ {actual_y:.0f}",
                    (float(row["word_count"]), plotted_y),
                    xytext=(0, -14), textcoords="offset points",
                    ha="center", fontsize=7, color=SOURCE_COLORS[source],
                )
        ax.text(
            0.02, 0.98,
            f"{meta['dataset']} · {child_label} · age {float(meta['age_months']):.1f} months\n"
            f"context: {context_label}\nQwen n={len(qwen)} · "
            f"child rank: effort {100*float(meta['effort_percentile_in_qwen']):.0f}%, "
            f"k3 {100*float(meta['k3_percentile_in_qwen']):.0f}%",
            transform=ax.transAxes, va="top", fontsize=7.6,
            bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "none", "pad": 2},
            zorder=10,
        )
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_title(age_bin)
        ax.set_xlabel("Cleaned word count")
        ax.set_ylabel("Mistral k3 total surprisal (bits)")
    legend_sources = ("qwen", "observed_child", "random", "unigram", "bigram", "trigram", "lstm")
    handles = [
        Line2D(
            [0], [0], marker=_source_marker(source), linestyle="none",
            markerfacecolor=SOURCE_COLORS[source], markeredgecolor="white",
            markersize=11 if source == "observed_child" else 7,
            label=SOURCE_LABELS[source],
        )
        for source in legend_sources
        if source != "lstm" or gallery["source"].eq("lstm").any()
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=6, frameon=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def plot_normalized_atlas(sample: pd.DataFrame, path: Path) -> None:
    """Plot the child-position density and comparison medians on bounded percentile axes."""

    fig, axes = plt.subplots(2, 4, figsize=(18, 9.5), sharex=True, sharey=True, constrained_layout=True)
    for ax, age_bin in zip(axes.ravel(), AGE_BINS):
        panel = sample[
            sample["age_bin"].astype(str).eq(age_bin)
            & ~sample["source"].eq("qwen")
        ].dropna(subset=["effort_percentile_in_qwen", "k3_percentile_in_qwen"])
        observed = panel[panel["source"].eq("observed_child")]
        if not observed.empty:
            ax.hexbin(
                observed["effort_percentile_in_qwen"], observed["k3_percentile_in_qwen"],
                gridsize=22, extent=(0, 1, 0, 1), mincnt=1, bins="log",
                cmap="Blues", linewidths=0, alpha=0.82, zorder=1,
            )
        ax.scatter(
            [0.5], [0.5], s=58, marker="o", color=SOURCE_COLORS["qwen"],
            edgecolors="white", linewidths=1.0, zorder=5,
        )
        for source in ("observed_child", "random", "unigram", "bigram", "trigram", "lstm"):
            group = panel[panel["source"].eq(source)]
            if group.empty:
                continue
            ax.scatter(
                [group["effort_percentile_in_qwen"].median()],
                [group["k3_percentile_in_qwen"].median()],
                s=_source_size(source) * 0.82, marker=_source_marker(source),
                color=SOURCE_COLORS[source], edgecolors="white", linewidths=1.0,
                zorder=6,
            )
        observed_n = int(panel["source"].eq("observed_child").sum())
        ax.axhline(0.5, color="#888", lw=0.8, linestyle="--")
        ax.axvline(0.5, color="#888", lw=0.8, linestyle="--")
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_title(age_bin)
        ax.text(
            0.02, 0.98, f"display sample n={observed_n:,}", transform=ax.transAxes,
            va="top", fontsize=8, color="#222",
            bbox={"facecolor": "white", "alpha": 0.82, "edgecolor": "none", "pad": 1.5}, zorder=8,
        )
        ax.set_xlabel("Effort percentile within same-context Qwen100")
        ax.set_ylabel("k3-surprisal percentile within same-context Qwen100")
    legend_sources = ("qwen", "observed_child", "random", "unigram", "bigram", "trigram", "lstm")
    handles = [
        Line2D(
            [0], [0], marker=_source_marker(source), linestyle="none",
            markerfacecolor=SOURCE_COLORS[source], markeredgecolor="white",
            markersize=10 if source == "observed_child" else 7,
            label=(
                "observed-child density + median" if source == "observed_child"
                else "Qwen reference center" if source == "qwen"
                else SOURCE_LABELS[source]
            ),
        )
        for source in legend_sources
        if source != "lstm" or sample["source"].eq("lstm").any()
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=6, frameon=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def plot_z_diagnostic(sample: pd.DataFrame, path: Path) -> None:
    """Retain requested z coordinates as a clearly secondary, robustly clipped diagnostic."""

    fig, axes = plt.subplots(2, 4, figsize=(18, 9.5), sharex=True, sharey=True, constrained_layout=True)
    for ax, age_bin in zip(axes.ravel(), AGE_BINS):
        panel = sample[
            sample["age_bin"].astype(str).eq(age_bin)
            & ~sample["source"].eq("qwen")
        ].dropna(subset=["z_effort", "z_k3"])
        for source in ("observed_child", "random", "unigram", "bigram", "trigram", "lstm"):
            group = panel[panel["source"].eq(source)]
            if group.empty:
                continue
            if len(group) > 600:
                group = group.sample(600, random_state=stable_seed(f"z-{age_bin}-{source}"))
            ax.scatter(
                group["z_effort"].clip(-4, 4), group["z_k3"].clip(-4, 4),
                s=7, alpha=0.07, color=SOURCE_COLORS[source], linewidths=0,
            )
            ax.scatter(
                [group["z_effort"].median()], [group["z_k3"].median()],
                s=_source_size(source) * 0.65, marker=_source_marker(source),
                color=SOURCE_COLORS[source], edgecolors="white", linewidths=1.0,
                zorder=5, label=SOURCE_LABELS[source],
            )
        ax.axhline(0, color="#888", lw=0.8, linestyle="--")
        ax.axvline(0, color="#888", lw=0.8, linestyle="--")
        ax.set_xlim(-4.1, 4.1)
        ax.set_ylim(-4.1, 4.1)
        ax.set_title(age_bin)
        ax.set_xlabel("z effort (clipped for display)")
        ax.set_ylabel("z k3 surprisal (clipped for display)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="outside lower center", ncol=5, frameon=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def _plot_trajectory_panel(
    ax: Any,
    frame: pd.DataFrame,
    outcome: str,
    summary: str,
    ylabel: str,
    *,
    sources: Sequence[str] = SOURCE_ORDER,
) -> None:
    panel = frame[frame["outcome"].eq(outcome) & frame["summary"].eq(summary)]
    for source in sources:
        group = panel[panel["source"].eq(source)].sort_values("age_months")
        if group.empty:
            continue
        ax.plot(group["age_months"], group["estimate"], color=SOURCE_COLORS[source], marker=_source_marker(source), linewidth=2.6 if source == "observed_child" else 1.7, label=SOURCE_LABELS[source])
        ax.fill_between(group["age_months"], group["ci_low"], group["ci_high"], color=SOURCE_COLORS[source], alpha=0.13)
    ax.set_xlabel("Age in months (continuous-model estimate)")
    ax.set_ylabel(ylabel)
    ax.set_xticks(PRECISE_AGES)


def plot_precise_trajectories(trajectories: pd.DataFrame, primary_path: Path, sensitivity_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.4), constrained_layout=True)
    _plot_trajectory_panel(
        axes[0], trajectories, "effort_percentile_in_qwen", "mean",
        "Estimated mean effort percentile",
        sources=("observed_child", "qwen"),
    )
    _plot_trajectory_panel(
        axes[1], trajectories, "k3_percentile_in_qwen", "mean",
        "Estimated mean k3-surprisal percentile",
    )
    for ax in axes.ravel():
        ax.axhline(0.5, color="#777", linestyle="--", linewidth=1)
        ax.set_ylim(-0.03, 1.03)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=6, frameon=False)
    primary_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(primary_path, dpi=190)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
    _plot_trajectory_panel(axes[0, 0], trajectories, "k3_sum_bits", "mean", "k3 total surprisal (bits)")
    _plot_trajectory_panel(axes[0, 1], trajectories, "k3_mean_bits_per_token", "mean", "k3 bits per Mistral token")
    _plot_trajectory_panel(axes[1, 0], trajectories, "k0_sum_bits", "mean", "Unconditional k0 total surprisal (bits)")
    _plot_trajectory_panel(axes[1, 1], trajectories, "context_support_bits", "mean", "Context support: k0 − k3 (bits)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=6, frameon=False)
    fig.savefig(sensitivity_path, dpi=190)
    plt.close(fig)


def plot_contrasts(contrasts: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
    for ax, outcome, ylabel in (
        (axes[0, 0], "effort_percentile_in_qwen", "Observed minus source effort percentile"),
        (axes[0, 1], "k3_percentile_in_qwen", "Observed minus source k3 percentile"),
        (axes[1, 0], "word_count", "Observed minus source cleaned words"),
        (axes[1, 1], "k3_sum_bits", "Observed minus source k3 total bits"),
    ):
        panel = contrasts[contrasts["outcome"].eq(outcome) & contrasts["summary"].eq("mean")]
        for source in ("qwen", "random", "unigram", "bigram", "trigram", "lstm"):
            group = panel[panel["comparator"].eq(source)].sort_values("age_months")
            if group.empty:
                continue
            ax.plot(group["age_months"], group["estimate"], color=SOURCE_COLORS[source], marker="o", label=SOURCE_LABELS[source])
            ax.fill_between(group["age_months"], group["ci_low"], group["ci_high"], color=SOURCE_COLORS[source], alpha=0.13)
        ax.axhline(0, color="#333", linestyle="--", linewidth=1)
        ax.set_xlabel("Age in months (continuous-model estimate)")
        ax.set_ylabel(ylabel)
        ax.set_xticks(PRECISE_AGES)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=5, frameon=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def plot_length_distributions(lengths: pd.DataFrame, path: Path) -> None:
    totals = lengths.groupby(["age_bin", "source"], observed=True)["n"].transform("sum")
    lengths = lengths.copy()
    lengths["proportion"] = lengths["n"] / totals
    cumulative = lengths.sort_values("word_count").groupby(["age_bin", "source"], observed=True)["proportion"].cumsum()
    support = lengths.loc[cumulative.le(0.995), "word_count"]
    xmax = max(12, int(support.max())) if not support.empty else 20
    fig, axes = plt.subplots(2, 4, figsize=(18, 9.5), sharex=True, sharey=True, constrained_layout=True)
    for ax, age_bin in zip(axes.ravel(), AGE_BINS):
        panel = lengths[lengths["age_bin"].astype(str).eq(age_bin)]
        for source in SOURCE_ORDER:
            group = panel[panel["source"].eq(source)].sort_values("word_count")
            if group.empty:
                continue
            ax.step(group["word_count"], group["proportion"], where="mid", color=SOURCE_COLORS[source], linewidth=2.4 if source == "observed_child" else 1.4, label=SOURCE_LABELS[source])
        ax.set_xlim(0, xmax)
        ax.set_title(age_bin)
        ax.set_xlabel("Cleaned word count")
        ax.set_ylabel("Proportion")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=6, frameon=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def _length_colors() -> dict[int, Any]:
    colormap = matplotlib.colormaps.get_cmap("viridis")
    return {length: colormap((length - 1) / (max(FIXED_LENGTHS) - 1)) for length in FIXED_LENGTHS}


def plot_fixed_length_age_atlas(
    summaries: pd.DataFrame,
    predictions: pd.DataFrame,
    path: Path,
) -> None:
    """Mirror the earlier fixed-effort atlas: model rows, length-group columns."""

    colors = _length_colors()
    sources = [source for source in SOURCE_ORDER if source != "lstm"]
    primary = predictions[
        predictions["specification"].eq("primary_linear_exact_length_child_fe")
        & predictions["outcome"].eq("mean_k3_sum_bits")
    ]
    fig, axes = plt.subplots(
        len(sources), len(LENGTH_GROUPS), figsize=(18, 24), sharex=True, sharey="row",
        constrained_layout=True,
    )
    for row_index, source in enumerate(sources):
        source_summary = summaries[summaries["source"].eq(source)]
        source_prediction = primary[primary["source"].eq(source)]
        for column_index, lengths in enumerate(LENGTH_GROUPS):
            ax = axes[row_index, column_index]
            for length in lengths:
                raw = source_summary[source_summary["word_count"].eq(length)].sort_values("mean_age_months")
                fitted = source_prediction[source_prediction["word_count"].eq(length)].sort_values("age_months")
                if not fitted.empty:
                    ax.plot(
                        fitted["age_months"], fitted["estimate"], color=colors[length],
                        linewidth=2.0, label=f"{SOURCE_LABELS[source]} · length {length}", zorder=2,
                    )
                    ax.fill_between(
                        fitted["age_months"], fitted["ci_low"], fitted["ci_high"],
                        color=colors[length], alpha=0.07, linewidth=0, zorder=1,
                    )
                if not raw.empty:
                    ax.scatter(
                        raw["mean_age_months"], raw["mean_k3_sum_bits"],
                        color=colors[length], s=28, edgecolors="white", linewidths=0.7,
                        zorder=4,
                    )
            ax.set_title(
                f"{SOURCE_LABELS[source]} | lengths {lengths[0]}–{lengths[-1]}",
                fontsize=11,
            )
            ax.grid(alpha=0.22)
            if row_index == len(sources) - 1:
                ax.set_xlabel("Age in months")
            if column_index == 0:
                ax.set_ylabel("Mistral k3 total surprisal (bits)")
            ax.legend(fontsize=6.8, frameon=False, loc="best")
    fig.suptitle(
        "All-79 fixed-length information trajectories\n"
        "points = raw age-bin means; lines/ribbons = child-controlled regression predictions (95% CI)",
        fontsize=17,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_fixed_length_nonlinear_check(
    summaries: pd.DataFrame,
    predictions: pd.DataFrame,
    path: Path,
) -> None:
    colors = _length_colors()
    representative_lengths = (1, 4, 8, 12)
    sources = [source for source in SOURCE_ORDER if source != "lstm"]
    fig, axes = plt.subplots(2, 3, figsize=(18, 10), sharex=True, sharey=False, constrained_layout=True)
    for ax, source in zip(axes.ravel(), sources):
        source_summary = summaries[summaries["source"].eq(source)]
        for length in representative_lengths:
            raw = source_summary[source_summary["word_count"].eq(length)].sort_values("mean_age_months")
            if not raw.empty:
                ax.scatter(
                    raw["mean_age_months"], raw["mean_k3_sum_bits"], color=colors[length],
                    s=24, edgecolors="white", linewidths=0.6, zorder=4,
                )
            for specification, linestyle in (
                ("primary_linear_exact_length_child_fe", "-"),
                ("quadratic_age_exact_length_child_fe", "--"),
            ):
                fitted = predictions[
                    predictions["source"].eq(source)
                    & predictions["specification"].eq(specification)
                    & predictions["word_count"].eq(length)
                ].sort_values("age_months")
                if not fitted.empty:
                    ax.plot(
                        fitted["age_months"], fitted["estimate"], color=colors[length],
                        linestyle=linestyle, linewidth=2.0,
                    )
        ax.set_title(SOURCE_LABELS[source])
        ax.set_xlabel("Age in months")
        ax.set_ylabel("Mistral k3 total surprisal (bits)")
        ax.grid(alpha=0.22)
    length_handles = [
        Line2D([0], [0], color=colors[length], linewidth=2.5, label=f"length {length}")
        for length in representative_lengths
    ]
    style_handles = [
        Line2D([0], [0], color="#333", linewidth=2.5, linestyle="-", label="linear age"),
        Line2D([0], [0], color="#333", linewidth=2.5, linestyle="--", label="quadratic age"),
        Line2D([0], [0], color="#333", marker="o", linestyle="none", label="raw age-bin mean"),
    ]
    fig.legend(handles=[*length_handles, *style_handles], loc="outside lower center", ncol=7, frameon=False)
    fig.suptitle("Fixed-length nonlinear-age check (panel-specific y scales)", fontsize=16)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_fixed_length_coefficients(coefficients: pd.DataFrame, path: Path) -> None:
    sources = [source for source in SOURCE_ORDER if source != "lstm"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5), constrained_layout=True)
    panels = (
        ("primary_linear_exact_length_child_fe", "mean_k3_sum_bits", "Adjusted k3-total age slope (bits/month)"),
        (
            "bits_per_token_linear_exact_length_child_fe",
            "mean_k3_bits_per_token",
            "Adjusted k3 bits/token age slope (bits/token/month)",
        ),
    )
    for ax, (specification, outcome, xlabel) in zip(axes, panels):
        selected = coefficients[
            coefficients["specification"].eq(specification)
            & coefficients["outcome"].eq(outcome)
            & coefficients["term"].eq("age_c")
        ].set_index("source")
        for position, source in enumerate(sources):
            if source not in selected.index:
                continue
            row = selected.loc[source]
            estimate = float(row["estimate"]) / 12.0
            low = float(row["ci_low"]) / 12.0
            high = float(row["ci_high"]) / 12.0
            ax.errorbar(
                estimate, position, xerr=[[estimate - low], [high - estimate]],
                fmt=_source_marker(source), color=SOURCE_COLORS[source], markersize=8,
                capsize=3, linewidth=1.6,
            )
        ax.axvline(0, color="#555", linestyle="--", linewidth=1)
        ax.set_yticks(range(len(sources)), [SOURCE_LABELS[source] for source in sources])
        ax.set_xlabel(xlabel)
        ax.grid(axis="x", alpha=0.22)
        ax.invert_yaxis()
    fig.suptitle("Length- and child-controlled linear age coefficients with child-clustered 95% CIs")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_model_length_age_3d(
    summaries: pd.DataFrame,
    predictions: pd.DataFrame,
    path: Path,
) -> None:
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    fig = plt.figure(figsize=(17, 12), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    primary = predictions[
        predictions["specification"].eq("primary_linear_exact_length_child_fe")
        & predictions["outcome"].eq("mean_k3_sum_bits")
    ]
    for source in (item for item in SOURCE_ORDER if item != "lstm"):
        raw_source = summaries[summaries["source"].eq(source)]
        fitted_source = primary[primary["source"].eq(source)]
        ax.scatter(
            raw_source["mean_age_months"], raw_source["word_count"], raw_source["mean_k3_sum_bits"],
            color=SOURCE_COLORS[source], s=18, alpha=0.78, depthshade=False,
            label=SOURCE_LABELS[source],
        )
        for length in FIXED_LENGTHS:
            raw_line = raw_source[raw_source["word_count"].eq(length)].sort_values("mean_age_months")
            fit_line = fitted_source[fitted_source["word_count"].eq(length)].sort_values("age_months")
            if not raw_line.empty:
                ax.plot(
                    raw_line["mean_age_months"], raw_line["word_count"], raw_line["mean_k3_sum_bits"],
                    color=SOURCE_COLORS[source], alpha=0.24, linewidth=0.9,
                )
            if not fit_line.empty:
                ax.plot(
                    fit_line["age_months"], fit_line["word_count"], fit_line["estimate"],
                    color=SOURCE_COLORS[source], alpha=0.55, linewidth=1.1,
                )
    ax.set_xlabel("Age in months", labelpad=10)
    ax.set_ylabel("Exact cleaned-word length", labelpad=10)
    ax.set_zlabel("Mistral k3 total surprisal (bits)", labelpad=10)
    ax.set_yticks(FIXED_LENGTHS)
    ax.view_init(elev=24, azim=-56)
    ax.set_title(
        "All model × exact length × age information in one 3D plot\n"
        "points = raw age-bin cells; lines = within-length raw and adjusted age trajectories",
        pad=22,
    )
    ax.legend(loc="upper left", bbox_to_anchor=(0.01, 0.98), frameon=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=190)
    plt.close(fig)


def write_model_length_age_3d(summaries: pd.DataFrame, path: Path) -> None:
    fields = [
        "source", "age_bin", "mean_age_months", "word_count", "mean_k3_sum_bits",
        "n_rows", "children",
    ]
    points = summaries[fields].rename(
        columns={"mean_age_months": "x", "word_count": "y", "mean_k3_sum_bits": "z"}
    ).to_dict(orient="records")
    payload = json.dumps(points, ensure_ascii=False).replace("</", "<\\/")
    colors = json.dumps(SOURCE_COLORS)
    labels = json.dumps(SOURCE_LABELS)
    document = f"""<!doctype html><html><head><meta charset='utf-8'><title>Model × length × age atlas</title>
<style>body{{font-family:system-ui;margin:0;background:#fafafa;color:#222}}header{{padding:16px 22px;background:#fff;border-bottom:1px solid #ddd}}.controls{{display:flex;gap:12px;flex-wrap:wrap;padding:12px 22px;background:#fff}}select,input{{padding:6px}}canvas{{display:block;margin:auto;background:white;border:1px solid #ddd}}#tip{{position:fixed;display:none;background:#111;color:white;padding:6px 8px;border-radius:4px;font-size:12px;pointer-events:none}}.note{{padding:8px 22px;font-size:13px}}</style></head><body>
<header><h1>All model × exact length × age cells</h1><div>Every point is one raw age-bin average. x = age; y = exact length; z = Mistral k3 total surprisal.</div></header>
<div class='controls'><label>Model <select id='source'></select></label><label>Length <select id='length'></select></label><label>Age bin <select id='age'></select></label><label>Rotation <input id='rotation' type='range' min='-80' max='80' value='28'></label></div>
<canvas id='cloud' width='1240' height='760'></canvas><div id='tip'></div><div class='note' id='count'></div>
<script>const P={payload},COL={colors},LAB={labels};const C=document.getElementById('cloud'),X=C.getContext('2d');const controls={{source:document.getElementById('source'),age_bin:document.getElementById('age'),y:document.getElementById('length')}};
function fill(s,key){{const vals=[...new Set(P.map(p=>p[key]))].sort((a,b)=>String(a).localeCompare(String(b),undefined,{{numeric:true}}));s.innerHTML='<option value="">All</option>'+vals.map(v=>`<option>${{v}}</option>`).join('')}}fill(controls.source,'source');fill(controls.age_bin,'age_bin');fill(controls.y,'y');let drawn=[];
function render(){{const f=P.filter(p=>(!controls.source.value||p.source===controls.source.value)&&(!controls.age_bin.value||p.age_bin===controls.age_bin.value)&&(!controls.y.value||String(p.y)===controls.y.value));X.clearRect(0,0,C.width,C.height);X.fillStyle='white';X.fillRect(0,0,C.width,C.height);if(!f.length)return;const rot=Number(document.getElementById('rotation').value)*Math.PI/180;const range=k=>{{const a=f.map(p=>Number(p[k])).filter(Number.isFinite);return [Math.min(...a),Math.max(...a)]}},rx=range('x'),ry=range('y'),rz=range('z');const norm=(v,r)=>(Number(v)-r[0])/(r[1]-r[0]||1);const project=p=>{{let a=norm(p.x,rx)-.5,b=norm(p.y,ry)-.5;const u=a*Math.cos(rot)-b*Math.sin(rot),d=a*Math.sin(rot)+b*Math.cos(rot);return [620+u*870,650-norm(p.z,rz)*530-d*170]}};const groups={{}};f.forEach(p=>{{const k=p.source+'|'+p.y;(groups[k]??=[]).push(p)}});Object.values(groups).forEach(g=>{{g.sort((a,b)=>a.x-b.x);X.strokeStyle=COL[g[0].source];X.globalAlpha=.34;X.lineWidth=1.2;X.beginPath();g.forEach((p,i)=>{{const q=project(p);if(i)X.lineTo(q[0],q[1]);else X.moveTo(q[0],q[1])}});X.stroke()}});drawn=[];f.forEach(p=>{{const q=project(p);drawn.push([q[0],q[1],p]);X.globalAlpha=.82;X.fillStyle=COL[p.source];X.beginPath();X.arc(q[0],q[1],3.3,0,Math.PI*2);X.fill()}});X.globalAlpha=1;X.fillStyle='#222';X.font='13px system-ui';X.fillText('age →',565,744);X.save();X.translate(20,470);X.rotate(-Math.PI/2);X.fillText('Mistral k3 total surprisal →',0,0);X.restore();X.fillText('exact length projection',1025,680);document.getElementById('count').textContent=`Showing ${{f.length}} exact model × length × age-bin cells.`}}
Object.values(controls).forEach(s=>s.onchange=render);document.getElementById('rotation').oninput=render;C.onmousemove=e=>{{const r=C.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;let hit=null,d=70;drawn.forEach(a=>{{const q=(a[0]-x)**2+(a[1]-y)**2;if(q<d){{d=q;hit=a[2]}}}});const t=document.getElementById('tip');if(hit){{t.style.display='block';t.style.left=e.clientX+12+'px';t.style.top=e.clientY+12+'px';t.textContent=`${{LAB[hit.source]}} | length ${{hit.y}} | ${{hit.age_bin}} | age ${{Number(hit.x).toFixed(1)}} | k3 ${{Number(hit.z).toFixed(2)}} | n ${{Number(hit.n_rows).toLocaleString()}}`}}else t.style.display='none'}};render();</script></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")


def write_interactive_3d(sample: pd.DataFrame, path: Path) -> None:
    fields = ["source", "dataset", "child_key", "age_bin", "word_count", "k3_sum_bits", "age_months"]
    clean = sample[fields].replace([np.inf, -np.inf], np.nan).dropna().copy()
    clean = clean.rename(columns={"word_count": "x", "k3_sum_bits": "y", "age_months": "z"})
    points = clean.to_dict(orient="records")
    payload = json.dumps(points, ensure_ascii=False).replace("</", "<\\/")
    colors = json.dumps(SOURCE_COLORS)
    labels = json.dumps(SOURCE_LABELS)
    document = f"""<!doctype html><html><head><meta charset='utf-8'><title>All-79 interactive information-effort cloud</title>
<style>body{{font-family:system-ui;margin:0;background:#fafafa;color:#222}}header{{padding:16px 22px;background:#fff;border-bottom:1px solid #ddd}}.controls{{display:flex;gap:10px;flex-wrap:wrap;padding:12px 22px;background:#fff}}select{{padding:6px}}canvas{{display:block;margin:auto;background:white;border:1px solid #ddd}}#tip{{position:fixed;display:none;background:#111;color:white;padding:6px 8px;border-radius:4px;font-size:12px;pointer-events:none}}.note{{padding:8px 22px;font-size:13px}}</style></head><body>
<header><h1>Pooled all-79 information-effort-age cloud</h1><div>x = cleaned words; y = Mistral k3 total surprisal; z = child age. The browser uses a fixed, reproducible stratified sample.</div></header>
<div class='controls'><label>Corpus <select id='dataset'></select></label><label>Child <select id='child'></select></label><label>Age bin <select id='age'></select></label><label>Source <select id='source'></select></label><label>Rotation <input id='rotation' type='range' min='-70' max='70' value='25'></label></div>
<canvas id='cloud' width='1180' height='720'></canvas><div id='tip'></div><div class='note' id='count'></div>
<script>const P={payload},COL={colors},LAB={labels};const canvas=document.getElementById('cloud'),ctx=canvas.getContext('2d');
const selects={{dataset:document.getElementById('dataset'),child:document.getElementById('child'),age_bin:document.getElementById('age'),source:document.getElementById('source')}};
function fill(s,key){{const vals=[...new Set(P.map(p=>p[key]))].sort();s.innerHTML='<option value="">All</option>'+vals.map(v=>`<option>${{v}}</option>`).join('')}}fill(selects.dataset,'dataset');fill(selects.child,'child_key');fill(selects.age_bin,'age_bin');fill(selects.source,'source');
let drawn=[];function render(){{const f=P.filter(p=>(!selects.dataset.value||p.dataset===selects.dataset.value)&&(!selects.child.value||p.child_key===selects.child.value)&&(!selects.age_bin.value||p.age_bin===selects.age_bin.value)&&(!selects.source.value||p.source===selects.source.value));ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);if(!f.length)return;const rot=Number(document.getElementById('rotation').value)*Math.PI/180;const lim=(k,q)=>{{const a=f.map(p=>p[k]).sort((a,b)=>a-b);return [a[0],a[Math.min(a.length-1,Math.floor(a.length*q))]]}};const lx=lim('x',.995),ly=lim('y',.995),lz=lim('z',1);const norm=(v,l)=>Math.max(0,Math.min(1,(v-l[0])/(l[1]-l[0]||1)));drawn=[];f.forEach(p=>{{let x=norm(p.x,lx)-.5,z=norm(p.z,lz)-.5;const xr=x*Math.cos(rot)-z*Math.sin(rot),zr=x*Math.sin(rot)+z*Math.cos(rot);const sx=590+xr*850,sy=630-norm(p.y,ly)*540-zr*180;drawn.push([sx,sy,p]);ctx.globalAlpha=p.source==='qwen'?.13:.46;ctx.fillStyle=COL[p.source];ctx.beginPath();ctx.arc(sx,sy,p.source==='observed_child'?2.8:1.7,0,Math.PI*2);ctx.fill()}});ctx.globalAlpha=1;ctx.fillStyle='#222';ctx.font='13px system-ui';ctx.fillText('cleaned word effort →',470,706);ctx.save();ctx.translate(18,430);ctx.rotate(-Math.PI/2);ctx.fillText('Mistral k3 total surprisal →',0,0);ctx.restore();ctx.fillText('age projection',1010,665);document.getElementById('count').textContent=`Showing ${{f.length.toLocaleString()}} sampled points. Qwen is a light-gray sampled layer; exact context summaries remain in the saved metrics.`}}
Object.values(selects).forEach(s=>s.onchange=render);document.getElementById('rotation').oninput=render;canvas.onmousemove=e=>{{const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;let hit=null,d=64;drawn.forEach(a=>{{const q=(a[0]-x)**2+(a[1]-y)**2;if(q<d){{d=q;hit=a[2]}}}});const t=document.getElementById('tip');if(hit){{t.style.display='block';t.style.left=e.clientX+12+'px';t.style.top=e.clientY+12+'px';t.textContent=`${{LAB[hit.source]}} | ${{hit.dataset}} | ${{hit.child_key}} | age ${{hit.z.toFixed(1)}} | words ${{hit.x}} | k3 ${{hit.y.toFixed(2)}}`}}else t.style.display='none'}};render();</script></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")


def write_context_galleries(
    gallery: pd.DataFrame,
    context_metrics: pd.DataFrame,
    gallery_contexts: pd.DataFrame,
    output_dir: Path,
) -> tuple[Path, list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale_page in output_dir.glob("context_*.html"):
        stale_page.unlink()
    metadata = gallery_contexts.merge(context_metrics, on="context_id", how="left", validate="one_to_one")
    context_lookup = metadata.set_index("context_id")
    pages: list[Path] = []
    index_rows: list[str] = []
    for context_id, group in gallery.groupby("context_id", sort=True):
        meta = context_lookup.loc[context_id]
        xmax = max(1.0, float(pd.to_numeric(group["word_count"], errors="coerce").max()))
        reference = group[group["source"].isin(["qwen", "observed_child"])]
        ymax = max(1.0, float(pd.to_numeric(reference["k3_sum_bits"], errors="coerce").max()) * 1.08)
        circles = []
        ordered = group.assign(
            source_order=group["source"].map({source: index for index, source in enumerate(SOURCE_ORDER)})
        ).sort_values(["source_order", "selected_sample_index"], na_position="last")
        for row in ordered.itertuples(index=False):
            x = 55 + 820 * float(row.word_count) / xmax
            actual_y = float(row.k3_sum_bits)
            clipped_y = min(actual_y, ymax)
            y = 535 - 480 * clipped_y / ymax
            color = SOURCE_COLORS.get(str(row.source), "#777")
            radius = 8 if str(row.source) == "observed_child" else (3 if str(row.source) == "qwen" else 6)
            opacity = ".58" if str(row.source) == "qwen" else ".92"
            stroke = "white" if str(row.source) != "qwen" else "none"
            title = html.escape(f"{SOURCE_LABELS.get(str(row.source), row.source)} | {row.target_text} | words={row.word_count} | k3={row.k3_sum_bits:.3f}")
            circles.append(
                f"<circle cx='{x:.2f}' cy='{y:.2f}' r='{radius}' fill='{color}' "
                f"fill-opacity='{opacity}' stroke='{stroke}' stroke-width='1.5'><title>{title}</title></circle>"
            )
            if actual_y > ymax:
                circles.append(f"<text x='{x:.2f}' y='{y + 17:.2f}' text-anchor='middle' font-size='11' fill='{color}'>↑</text>")
        table_rows = "".join(
            f"<tr><td>{html.escape(SOURCE_LABELS.get(str(row.source), str(row.source)))}</td><td>{html.escape(str(row.target_text))}</td><td>{row.word_count}</td><td>{row.k3_sum_bits:.4f}</td><td>{row.k3_mean_bits_per_token:.4f}</td></tr>"
            for row in group.sort_values(["source", "selected_sample_index"], na_position="last").itertuples(index=False)
        )
        legend = " ".join(
            f"<span><i style='background:{SOURCE_COLORS[source]}'></i>{html.escape(SOURCE_LABELS[source])}</span>"
            for source in SOURCE_ORDER
            if source != "lstm" or group["source"].eq("lstm").any()
        )
        page = output_dir / f"context_{context_id}.html"
        page.write_text(
            f"<!doctype html><meta charset='utf-8'><title>Context {context_id}</title><style>body{{font-family:system-ui;max-width:1100px;margin:30px auto;color:#222}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:5px;text-align:left}}th{{position:sticky;top:0;background:white}}svg{{border:1px solid #ddd;background:white;max-width:100%;height:auto}}.legend{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0}}.legend i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}}</style>"
            f"<h1>{html.escape(str(meta['age_bin']))}: one caregiver-context response cloud</h1>"
            f"<p><strong>{html.escape(str(meta['dataset']))} · {html.escape(str(meta['child_key']))}</strong>, age {float(meta['age_months']):.1f} months. Child within-Qwen ranks: effort {100*float(meta['effort_percentile_in_qwen']):.0f}%, k3 surprisal {100*float(meta['k3_percentile_in_qwen']):.0f}%.</p>"
            f"<p><strong>Caregiver context:</strong> {html.escape(str(meta['context_text']))}</p><div class='legend'>{legend}</div>"
            f"<p>Gray points are all 100 Qwen alternatives for this exact context. Dark blue is the observed child response. Hover for source and response text. Up-arrows mark fixed-effort baseline points above the Qwen/child display range; their exact values remain in the table.</p>"
            f"<svg width='920' height='580' viewBox='0 0 920 580'><line x1='55' y1='535' x2='875' y2='535' stroke='#555'/><line x1='55' y1='55' x2='55' y2='535' stroke='#555'/>{''.join(circles)}<text x='55' y='553' font-size='11'>0</text><text x='875' y='553' text-anchor='end' font-size='11'>{xmax:.0f}</text><text x='50' y='535' text-anchor='end' font-size='11'>0</text><text x='50' y='62' text-anchor='end' font-size='11'>{ymax:.0f}</text><text x='380' y='570'>Cleaned word count</text><text transform='translate(15 360) rotate(-90)'>Mistral k3 total surprisal (bits)</text></svg>"
            f"<table><thead><tr><th>Source</th><th>Response text</th><th>Words</th><th>k3 bits</th><th>k3 bits/token</th></tr></thead><tbody>{table_rows}</tbody></table>",
            encoding="utf-8",
        )
        pages.append(page)
        index_rows.append(
            f"<li><a href='{page.name}'>{html.escape(str(meta['age_bin']))}</a> — "
            f"{html.escape(str(meta['dataset']))} · {html.escape(str(meta['child_key']))}, "
            f"age {float(meta['age_months']):.1f}: {html.escape(str(meta['context_text']))}</li>"
        )
    index = output_dir / "index.html"
    index.write_text(
        "<!doctype html><meta charset='utf-8'><title>All-79 per-context galleries</title><style>body{font-family:system-ui;max-width:1000px;margin:30px auto}li{margin:10px}</style><h1>One exact response cloud per age bin</h1><p>Each page contains the complete set of 100 Qwen responses for one caregiver context, the observed child response, and available same-length baselines.</p><ul>" + "".join(index_rows) + "</ul>",
        encoding="utf-8",
    )
    return index, pages


def run_plots_stage(args: argparse.Namespace) -> dict[str, Any]:
    metrics_manifest_path = args.output_dir / "metrics/metrics_manifest.json"
    models_manifest_path = args.output_dir / "models/models_manifest.json"
    metrics = require_stage_manifest(metrics_manifest_path, "metrics")
    models = require_stage_manifest(models_manifest_path, "models")
    summaries = pd.read_csv(metrics["outputs"]["length_age_summary"]["path"])
    lengths = pd.read_csv(metrics["outputs"]["length_distribution"]["path"])
    predictions = pd.read_csv(models["outputs"]["fixed_length_predictions"]["path"])
    coefficients = pd.read_csv(models["outputs"]["fixed_length_coefficients"]["path"])
    key_columns = ["source", "age_bin", "word_count"]
    expected_cells = (len(SOURCE_ORDER) - 1) * len(AGE_BINS) * len(FIXED_LENGTHS)
    grid_contract = {
        "rows": len(summaries),
        "unique_keys": int(summaries[key_columns].drop_duplicates().shape[0]),
        "expected_complete_grid_rows": expected_cells,
        "sources": int(summaries["source"].nunique()),
        "age_bins": int(summaries["age_bin"].nunique()),
        "lengths": int(summaries["word_count"].nunique()),
        "complete_model_length_age_grid": len(summaries) == expected_cells,
        "finite_information": bool(np.isfinite(summaries["mean_k3_sum_bits"]).all()),
        "positive_counts": bool(summaries["n_k3_rows"].gt(0).all()),
    }
    if (
        grid_contract["rows"] != grid_contract["unique_keys"]
        or not grid_contract["complete_model_length_age_grid"]
        or not grid_contract["finite_information"]
        or not grid_contract["positive_counts"]
    ):
        raise RuntimeError(f"invalid model-length-age plotting grid: {grid_contract}")

    args.fig_dir.mkdir(parents=True, exist_ok=True)
    obsolete_paths = (
        "population_age_bin_atlas.png", "context_normalized_age_bin_atlas.png",
        "context_normalized_z_diagnostic.png", "precise_age_primary_trajectories.png",
        "precise_age_total_and_sensitivity_trajectories.png",
        "precise_age_observed_minus_source_contrasts.png", "interactive_3d.html",
    )
    for obsolete_name in obsolete_paths:
        obsolete_path = args.fig_dir / obsolete_name
        if obsolete_path.exists():
            obsolete_path.unlink()
    obsolete_galleries = args.fig_dir / "galleries"
    if obsolete_galleries.exists():
        shutil.rmtree(obsolete_galleries)

    atlas_path = args.fig_dir / "model_length_age_fixed_effort_atlas.png"
    nonlinear_path = args.fig_dir / "model_length_age_nonlinear_check.png"
    coefficient_path = args.fig_dir / "model_length_age_regression_coefficients.png"
    three_d_path = args.fig_dir / "model_length_age_all_models_3d.png"
    interactive_path = args.fig_dir / "model_length_age_all_models_3d.html"
    length_path = args.fig_dir / "length_distributions_by_age_bin.png"
    plot_fixed_length_age_atlas(summaries, predictions, atlas_path)
    plot_fixed_length_nonlinear_check(summaries, predictions, nonlinear_path)
    plot_fixed_length_coefficients(coefficients, coefficient_path)
    plot_model_length_age_3d(summaries, predictions, three_d_path)
    write_model_length_age_3d(summaries, interactive_path)
    plot_length_distributions(lengths, length_path)
    products = {
        "fixed_length_atlas": atlas_path,
        "nonlinear_check": nonlinear_path,
        "regression_coefficients": coefficient_path,
        "model_length_age_3d": three_d_path,
        "interactive_model_length_age_3d": interactive_path,
        "length_distributions": length_path,
    }
    audit = pd.DataFrame(
        [
            {"product": key, "path": str(path), "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else 0, "sha256": sha256_file(path) if path.is_file() else ""}
            for key, path in products.items()
        ]
    )
    if not audit["exists"].all() or (audit["bytes"] <= 0).any():
        raise RuntimeError("plot audit found a missing or empty product")
    audit_path = args.output_dir / "plots/plot_audit.csv"
    atomic_csv(audit, audit_path)
    outputs = {**products, "plot_audit": audit_path}
    return stage_manifest(
        stage="plots",
        inputs={"metrics_manifest": metrics_manifest_path, "models_manifest": models_manifest_path},
        outputs=outputs,
        metadata={
            "figures": 5,
            "interactive_views": 1,
            "model_length_age_grid": grid_contract,
            "lstm_included": False,
        },
        destination=args.output_dir / "plots/plots_manifest.json",
    )


def markdown_table(frame: pd.DataFrame, *, max_rows: int = 40, digits: int = 4) -> str:
    if frame.empty:
        return "_No rows._"
    shown = frame.head(max_rows).copy()
    values: list[list[str]] = []
    for row in shown.itertuples(index=False, name=None):
        rendered = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                rendered.append("" if pd.isna(value) else f"{float(value):.{digits}g}")
            else:
                rendered.append(str(value).replace("|", "\\|").replace("\n", " "))
        values.append(rendered)
    header = "| " + " | ".join(shown.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(shown.columns)) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in values]
    return "\n".join([header, separator, *rows])


def relative_doc_link(path: Path, report: Path) -> str:
    return os.path.relpath(path, report.parent).replace(os.sep, "/")


def select_report_estimate(frame: pd.DataFrame, **matches: Any) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for column, value in matches.items():
        mask &= frame[column].eq(value)
    selected = frame.loc[mask]
    if len(selected) != 1:
        raise RuntimeError(f"Expected one saved estimate for {matches}; found {len(selected)}")
    return selected.iloc[0]


def format_report_estimate(row: pd.Series, digits: int = 2) -> str:
    return (
        f"{float(row['estimate']):.{digits}f} "
        f"[95% bootstrap interval {float(row['ci_low']):.{digits}f}, "
        f"{float(row['ci_high']):.{digits}f}]"
    )


def run_report_stage(args: argparse.Namespace) -> dict[str, Any]:
    metrics_manifest_path = args.output_dir / "metrics/metrics_manifest.json"
    models_manifest_path = args.output_dir / "models/models_manifest.json"
    plots_manifest_path = args.output_dir / "plots/plots_manifest.json"
    metrics = require_stage_manifest(metrics_manifest_path, "metrics")
    models = require_stage_manifest(models_manifest_path, "models")
    plots = require_stage_manifest(plots_manifest_path, "plots")
    source_counts = pd.read_csv(metrics["outputs"]["source_counts"]["path"])
    summaries = pd.read_csv(metrics["outputs"]["length_age_summary"]["path"])
    coefficients = pd.read_csv(models["outputs"]["fixed_length_coefficients"]["path"])
    registry = pd.read_csv(models["outputs"]["fixed_length_registry"]["path"])
    metric_audit = json.loads(Path(metrics["outputs"]["metric_audit"]["path"]).read_text(encoding="utf-8"))
    token_cap = json.loads(Path(metrics["outputs"]["token_cap_diagnostics"]["path"]).read_text(encoding="utf-8"))
    lstm_gate = json.loads((args.output_dir / "datasets/lstm_gate.json").read_text(encoding="utf-8"))
    primary_slopes = coefficients[
        coefficients["specification"].eq("primary_linear_exact_length_child_fe")
        & coefficients["outcome"].eq("mean_k3_sum_bits")
        & coefficients["term"].eq("age_c")
    ][["source", "estimate", "ci_low", "ci_high", "p_value", "children", "weighted_rows", "r_squared"]].copy()
    for column in ("estimate", "ci_low", "ci_high"):
        primary_slopes[column] = primary_slopes[column] / 12.0
    primary_slopes = primary_slopes.rename(
        columns={
            "source": "model",
            "estimate": "bits_per_month",
            "ci_low": "ci_low_bits_per_month",
            "ci_high": "ci_high_bits_per_month",
        }
    )
    bits_per_token_slopes = coefficients[
        coefficients["specification"].eq("bits_per_token_linear_exact_length_child_fe")
        & coefficients["outcome"].eq("mean_k3_bits_per_token")
        & coefficients["term"].eq("age_c")
    ][["source", "estimate", "ci_low", "ci_high", "p_value"]].copy()
    for column in ("estimate", "ci_low", "ci_high"):
        bits_per_token_slopes[column] = bits_per_token_slopes[column] / 12.0
    bits_per_token_slopes = bits_per_token_slopes.rename(
        columns={
            "source": "model",
            "estimate": "bits_per_token_per_month",
            "ci_low": "ci_low",
            "ci_high": "ci_high",
        }
    )
    nonlinear_terms = coefficients[
        coefficients["specification"].eq("quadratic_age_exact_length_child_fe")
        & coefficients["term"].isin(["age_c", "age_c2"])
    ][["source", "term", "estimate", "ci_low", "ci_high", "p_value"]]
    joint_age_terms = coefficients[
        coefficients["specification"].eq("joint_age_by_model_exact_length_child_fe")
        & coefficients["term"].str.contains("age_c", regex=False)
    ][["term", "estimate", "ci_low", "ci_high", "p_value"]]
    figure_links = {key: relative_doc_link(Path(item["path"]), args.report_md) for key, item in plots["outputs"].items() if key != "plot_audit"}
    lines = [
        "# All-79 Model × Length × Age Information Atlas",
        "",
        "The analysis unit is now exactly the requested cell: **one information value per model, exact utterance length, and child-age bin**. The 2D figure reproduces the earlier fixed-effort design, and the 3D figure contains the same complete grid in one view.",
        "",
        "## Main fixed-length 2D figure",
        "",
        "- x-axis: child age in months.",
        "- y-axis: mean contextual Mistral k3 total surprisal.",
        "- rows: observed child, Qwen, random, unigram, bigram, and trigram models.",
        "- columns: exact lengths 1–4, 5–8, and 9–12, matching the earlier atlas.",
        "- each colored line: one exact cleaned-word length.",
        "- points: raw average for that model × length × age bin.",
        "- lines and ribbons: adjusted regression prediction and child-clustered 95% confidence interval.",
        "- y-scales are shared within each model row so each length trajectory remains readable; the 3D figure below supplies the common cross-model scale.",
        "",
        f"![Model by exact-length age atlas]({figure_links['fixed_length_atlas']})",
        "",
        "## Regression specification and checks",
        "",
        "The primary model is fit separately for every source on all eligible child-age-length cells:",
        "",
        "`mean k3 total bits ~ continuous age + exact length + child identity`",
        "",
        "Fits use opportunity-weighted WLS and child-clustered covariance. The plotted fixed-length slices are predictions from the full fit; they are not twelve separately selected regressions. Separate registered checks add quadratic age, categorical age bins, age-by-length interactions, a bits/token outcome, and a source-balanced joint age-by-model fit.",
        "",
        f"![Linear versus nonlinear fixed-length predictions]({figure_links['nonlinear_check']})",
        "",
        f"![Length-controlled regression coefficients]({figure_links['regression_coefficients']})",
        "",
        "Primary adjusted age slopes in total bits per month:",
        "",
        markdown_table(primary_slopes, max_rows=20),
        "",
        "Bits-per-token sensitivity slopes:",
        "",
        markdown_table(bits_per_token_slopes, max_rows=20),
        "",
        "Quadratic-age terms:",
        "",
        markdown_table(nonlinear_terms, max_rows=20),
        "",
        "Joint age-by-model terms from the source-balanced comparison (observed child is the reference model):",
        "",
        markdown_table(joint_age_terms, max_rows=20),
        "",
        "Registered model suite:",
        "",
        markdown_table(registry[["source", "specification", "outcome", "formula", "cells", "children"]], max_rows=40),
        "",
        "## All information in one 3D plot",
        "",
        "Every point below is one raw `model × exact length × age-bin` average. Lines connect age values at the same model and length; adjusted regression lines are superimposed with greater opacity.",
        "",
        f"![Complete model-length-age 3D atlas]({figure_links['model_length_age_3d']})",
        "",
        f"[Open the filterable rotating 3D version]({figure_links['interactive_model_length_age_3d']})",
        "",
        "## Coverage",
        "",
        f"The frozen plotting grid contains **{len(summaries):,} unique cells**: 6 models × 12 exact lengths × 8 age bins. The underlying audit covers **{metric_audit['qwen']['responses']:,} Qwen responses**, **{metric_audit['qwen']['contexts']:,} contexts**, **{metric_audit['real_qwen_join']['eligible_real_rows']:,} observed opportunities**, **{metric_audit['real_qwen_join']['children']} children**, and **{metric_audit['real_qwen_join']['corpora']} corpora**.",
        "",
        markdown_table(source_counts),
        "",
        f"![Complete length distributions]({figure_links['length_distributions']})",
        "",
        f"The longest accepted Qwen response contains **{token_cap['maximum_cleaned_word_count']} cleaned words**, but the fixed-effort atlas deliberately restricts its comparable slices to exact lengths 1–12, matching the earlier plots.",
        "",
        "## LSTM gate",
        "",
        "The audited full-79 additive same-length LSTM score handoff is still absent, so it is not drawn as though complete. The six available models are fully analyzed; the completion state remains `CORE_CLOUDS_COMPLETE_LSTM_PENDING`.",
        "",
        f"Gate status: `{lstm_gate['status']}`.",
        "",
        "## Interpretation boundaries",
        "",
        "- Lower Mistral surprisal means greater scorer predictability, not more Shannon information transmitted.",
        "- Exact length is controlled in the regressions; longer utterances are not compared to shorter utterances as though total bits were length-free.",
        "- Qwen is a free-length generated reference; random and n-gram candidates do not preserve the child's intended meaning.",
        "- Regression lines describe adjusted observational associations. They do not establish semantic utility, a Pareto frontier, or optimization.",
        "- All 79 children are pooled; these are not split discovery/confirmation estimates.",
    ]
    # The report may be manually edited between turns; read the current file
    # immediately before replacing it through the deterministic builder.
    if args.report_md.exists():
        args.report_md.read_text(encoding="utf-8")
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render_markdown_file(args.report_md, args.report_html)
    return stage_manifest(
        stage="report",
        inputs={
            "metrics_manifest": metrics_manifest_path,
            "models_manifest": models_manifest_path,
            "plots_manifest": plots_manifest_path,
        },
        outputs={"report_markdown": args.report_md, "report_html": args.report_html},
        metadata={"pooled_all79_only": True, "lstm_included": False, "token_cap_incidence_available": False},
        destination=args.output_dir / "report/report_manifest.json",
    )


def run_audit_stage(args: argparse.Namespace, expected: ExpectedCounts) -> dict[str, Any]:
    manifest_paths = {
        "datasets": args.output_dir / "datasets/dataset_manifest.json",
        "metrics": args.output_dir / "metrics/metrics_manifest.json",
        "models": args.output_dir / "models/models_manifest.json",
        "plots": args.output_dir / "plots/plots_manifest.json",
        "report": args.output_dir / "report/report_manifest.json",
    }
    manifests = {stage: require_stage_manifest(path, stage) for stage, path in manifest_paths.items()}
    metric_audit = json.loads(Path(manifests["metrics"]["outputs"]["metric_audit"]["path"]).read_text(encoding="utf-8"))
    source_counts = pd.read_csv(manifests["metrics"]["outputs"]["source_counts"]["path"])
    lstm_gate = json.loads((args.output_dir / "datasets/lstm_gate.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    checks = {
        "qwen_contexts": metric_audit["qwen"]["contexts"] == expected.qwen_contexts,
        "qwen_responses": metric_audit["qwen"]["responses"] == expected.qwen_responses,
        "qwen_unique_response_ids": metric_audit["qwen"]["unique_response_ids"] == expected.qwen_responses,
        "qwen_core75": metric_audit["qwen"]["core75_rows"] == expected.qwen_core_responses,
        "qwen_extension25": metric_audit["qwen"]["extension25_rows"] == expected.qwen_extension_responses,
        "qwen_core_extension_disjoint": metric_audit["qwen"]["unique_response_ids"] == metric_audit["qwen"]["core75_rows"] + metric_audit["qwen"]["extension25_rows"],
        "qwen_finite_scores": metric_audit["qwen"]["nonfinite_rows"] == 0,
        "qwen_finite_nonnegative_effort": metric_audit["qwen"]["invalid_word_rows"] == 0,
        "qwen_positive_eval_tokens": metric_audit["qwen"]["nonpositive_eval_token_rows"] == 0,
        "real_eligible_rows": metric_audit["real_qwen_join"]["eligible_real_rows"] == expected.eligible_real_rows,
        "real_unmatched_rows": metric_audit["real_qwen_join"]["unmatched_real_rows"] == 0,
        "children": metric_audit["real_qwen_join"]["children"] == expected.children,
        "corpora": metric_audit["real_qwen_join"]["corpora"] == expected.corpora,
        "normalized_unique_keys": metric_audit["normalized_candidates"]["rows"] == metric_audit["normalized_candidates"]["unique_keys"],
        "observed_effort_percentiles_complete": metric_audit["normalized_candidates"]["missing_observed_effort_percentiles"] == 0,
        "observed_k3_percentiles_complete": metric_audit["normalized_candidates"]["missing_observed_k3_percentiles"] == 0,
        "effort_percentiles_bounded": metric_audit["normalized_candidates"]["invalid_effort_percentiles"] == 0,
        "k3_percentiles_bounded": metric_audit["normalized_candidates"]["invalid_k3_percentiles"] == 0,
        "model_length_age_cells_unique": (
            metric_audit["model_length_age_cells"]["rows"]
            == metric_audit["model_length_age_cells"]["unique_keys"]
        ),
        "model_length_age_sources_complete": metric_audit["model_length_age_cells"]["sources"] == 6,
        "model_length_age_lengths_1_to_12": (
            metric_audit["model_length_age_cells"]["minimum_length"] == min(FIXED_LENGTHS)
            and metric_audit["model_length_age_cells"]["maximum_length"] == max(FIXED_LENGTHS)
        ),
        "model_length_age_cells_finite": metric_audit["model_length_age_cells"]["invalid_k3_cells"] == 0,
        "model_length_age_cells_positive_weights": metric_audit["model_length_age_cells"]["invalid_weight_rows"] == 0,
        "complete_model_length_age_plot_grid": manifests["plots"]["model_length_age_grid"]["complete_model_length_age_grid"],
        "fixed_length_model_suite_passed": manifests["models"]["audit"]["fixed_length_suite"]["status"] == "PASS",
        "pooled_all79_only": all(manifest.get("pooled_all79_only", True) for manifest in manifests.values()),
    }
    for label, passed in checks.items():
        if not passed:
            problems.append(label)
    expected_core_sources = {"observed_child", "qwen", "random", "unigram", "bigram", "trigram"}
    actual_sources = set(source_counts["source"].astype(str))
    if actual_sources != expected_core_sources:
        problems.append(f"source set mismatch: {sorted(actual_sources)}")
    if (source_counts["candidate_rows"] != expected.eligible_real_rows).any():
        problems.append("one or more opportunity-weighted source row counts differ from eligible real rows")
    candidate_exclusions = {
        row.source: {"nonfinite_k3": int(row.nonfinite_k3), "nonfinite_k0": int(row.nonfinite_k0)}
        for row in source_counts.itertuples(index=False)
    }
    direct_token_cap_available = metric_audit["token_cap"]["direct_hit_max_new_tokens_proportion"] is not None
    limitation = {
        "qwen_token_cap_incidence": {
            "status": "UNAVAILABLE_IN_CANONICAL_HANDOFF",
            "direct_incidence_available": direct_token_cap_available,
            "protocol_no_boundary_before_cap_selected_rate": 0.0,
            "reason": metric_audit["token_cap"]["reason"],
        },
        "lstm": {
            "status": lstm_gate["status"],
            "included": False,
            "all_source_marker_allowed": False,
        },
    }
    all_source_marker = args.output_dir / "FULL79_INFORMATION_EFFORT_CLOUDS_COMPLETE_AND_AUDITED"
    if all_source_marker.exists():
        problems.append("all-source completion marker exists even though LSTM is pending")
    product_paths: list[Path] = []
    for manifest in manifests.values():
        product_paths.extend(Path(item["path"]) for item in manifest["outputs"].values())
    product_paths.extend(manifest_paths.values())
    unique_products = sorted(set(product_paths), key=str)
    product_hashes = {
        str(path): {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in unique_products
    }
    audit = {
        "status": "PASS_CORE_LSTM_PENDING" if not problems else "FAIL",
        "analysis": "pooled all-79 joint information-effort clouds",
        "completed_at": utc_now(),
        "git": git_state(),
        "controller_sha256": sha256_file(Path(__file__)),
        "expected": asdict(expected),
        "checks": checks,
        "problems": problems,
        "source_counts": source_counts.to_dict(orient="records"),
        "candidate_score_exclusions": candidate_exclusions,
        "zero_sd_exclusions": {
            "contexts_word_effort": metric_audit["qwen"]["contexts_with_zero_or_undefined_word_sd"],
            "contexts_k3": metric_audit["qwen"]["contexts_with_zero_or_undefined_k3_sd"],
            "candidate_rows_z_effort": metric_audit["normalized_candidates"]["z_effort_excluded_rows"],
            "candidate_rows_z_k3": metric_audit["normalized_candidates"]["z_k3_excluded_rows"],
        },
        "limitations": limitation,
        "input_bindings": {stage: {"manifest": str(path), "sha256": sha256_file(path)} for stage, path in manifest_paths.items()},
        "product_hashes": product_hashes,
        "interpretation_guardrails": [
            "pooled descriptive developmental association",
            "exact word length controlled in fixed-effort regressions",
            "raw points are one model-by-length-by-age-bin average",
            "generated responses do not preserve child intended meaning",
            "same-length baselines cannot test optimal effort",
            "no Pareto/frontier/semantic-choice-set claim",
        ],
    }
    audit_dir = args.output_dir / "audit"
    audit_path = audit_dir / "final_audit.json"
    atomic_json(audit, audit_path)
    if problems:
        raise RuntimeError(f"final core audit failed: {problems}")
    marker = args.output_dir / "CORE_CLOUDS_COMPLETE_LSTM_PENDING"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        "PASS_CORE_LSTM_PENDING\n"
        f"AUDIT_SHA256={sha256_file(audit_path)}\n"
        f"GIT_COMMIT={audit['git']['commit']}\n"
        f"CONTROLLER_SHA256={audit['controller_sha256']}\n"
        f"QWEN_CONTEXTS={expected.qwen_contexts}\n"
        f"QWEN_RESPONSES={expected.qwen_responses}\n"
        f"ELIGIBLE_REAL_ROWS={expected.eligible_real_rows}\n"
        "LSTM_INCLUDED=0\n"
        f"TIMESTAMP={audit['completed_at']}\n",
        encoding="utf-8",
    )
    return audit


def expected_from_args(args: argparse.Namespace) -> ExpectedCounts:
    return ExpectedCounts(
        real_source_rows=args.expected_real_source_rows,
        eligible_real_rows=args.expected_eligible_real_rows,
        qwen_contexts=args.expected_qwen_contexts,
        qwen_responses=args.expected_qwen_responses,
        qwen_core_responses=args.expected_qwen_core_responses,
        qwen_extension_responses=args.expected_qwen_extension_responses,
        qwen_responses_per_context=args.expected_qwen_responses_per_context,
        qwen_core_per_context=args.expected_qwen_core_per_context,
        qwen_extension_per_context=args.expected_qwen_extension_per_context,
        children=args.expected_children,
        corpora=args.expected_corpora,
        shards=args.expected_shards,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["datasets", "metrics", "models", "plots", "report", "audit", "all"], default="all")
    parser.add_argument("--input-wide", type=Path, default=DEFAULT_WIDE)
    parser.add_argument("--wide-manifest", type=Path, default=DEFAULT_WIDE_MANIFEST)
    parser.add_argument("--qwen-root", type=Path, default=DEFAULT_QWEN_ROOT)
    parser.add_argument("--lstm-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIGURES)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--chunksize", type=int, default=50_000)
    parser.add_argument("--bootstrap-draws", type=int, default=500)
    parser.add_argument("--bootstrap-seed", type=int, default=20260824)
    parser.add_argument("--duckdb-memory-limit", default="6GB")
    parser.add_argument("--duckdb-temp-dir", type=Path, default=None)
    parser.add_argument("--skip-qwen-raw-rehash", action="store_true", help="Smoke/test only: trust per-shard contracts instead of rehashing 3 GB of inputs.")
    parser.add_argument("--expected-real-source-rows", type=int, default=1_140_695)
    parser.add_argument("--expected-eligible-real-rows", type=int, default=1_122_396)
    parser.add_argument("--expected-qwen-contexts", type=int, default=645_524)
    parser.add_argument("--expected-qwen-responses", type=int, default=64_552_400)
    parser.add_argument("--expected-qwen-core-responses", type=int, default=48_414_300)
    parser.add_argument("--expected-qwen-extension-responses", type=int, default=16_138_100)
    parser.add_argument("--expected-qwen-responses-per-context", type=int, default=100)
    parser.add_argument("--expected-qwen-core-per-context", type=int, default=75)
    parser.add_argument("--expected-qwen-extension-per-context", type=int, default=25)
    parser.add_argument("--expected-children", type=int, default=79)
    parser.add_argument("--expected-corpora", type=int, default=13)
    parser.add_argument("--expected-shards", type=int, default=512)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    expected = expected_from_args(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stages = ["datasets", "metrics", "models", "plots", "report", "audit"] if args.stage == "all" else [args.stage]
    for stage in stages:
        print(f"[{stage}] starting", flush=True)
        if stage == "datasets":
            run_datasets_stage(args, expected)
        elif stage == "metrics":
            run_metrics_stage(args, expected)
        elif stage == "models":
            run_models_stage(args)
        elif stage == "plots":
            run_plots_stage(args)
        elif stage == "report":
            run_report_stage(args)
        elif stage == "audit":
            run_audit_stage(args, expected)
        print(f"[{stage}] complete", flush=True)
    print(f"[OK] stage={args.stage} output={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
