#!/usr/bin/env python3
"""Build the full-79 Qwen Route 2 analysis without regenerating responses.

The completed Qwen run is treated as an immutable upstream handoff.  This
controller extracts compact generated-response effort features, joins them to
the completed full-79 real-child Mistral table, fits a deliberately broad
exploratory model registry in three fixed scopes, and audits structural
completion.  It never generates or scores language-model responses and never
selects a preferred result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from build_response_entropy_manifest import context_id, normalize_context
    from build_response_space_analysis_suite import add_centered_columns, read_response_space_table
    from build_route2_relative_effort_model_suite import (
        Route2Spec,
        add_route2_relative_columns,
        fit_models,
    )
    from build_route2_response_space_table import (
        load_entropy_features,
        load_generated_effort_summary,
        merge_route2_table,
    )
except ModuleNotFoundError:  # pragma: no cover - package import
    from src.build_response_entropy_manifest import context_id, normalize_context
    from src.build_response_space_analysis_suite import add_centered_columns, read_response_space_table
    from src.build_route2_relative_effort_model_suite import (
        Route2Spec,
        add_route2_relative_columns,
        fit_models,
    )
    from src.build_route2_response_space_table import (
        load_entropy_features,
        load_generated_effort_summary,
        merge_route2_table,
    )


ROOT = Path(__file__).resolve().parents[1]
PBM_DATASETS = frozenset({"Brown", "Manchester", "Providence"})
DEFAULT_WIDE = ROOT / "results/direct_surprisal_replication/mistral_full79/child_direct_surprisal_wide.csv.gz"
DEFAULT_OUTPUT = ROOT / "results/full79_qwen_route2_analysis"
DEFAULT_QWEN_RUN = (
    ROOT
    / "results/external/compute_surprisal_mila/"
    "qwen_response_mistral_full100_20260817_f5dd5aa"
)
DEFAULT_COMPUTE_REPO = ROOT.parent / "compute_surprisal_mila"
QWEN_PROMPT = "QwenSystemNaturalistic"
QWEN_TEMPERATURE = 1.0
ESTIMATORS_PER_SPEC = 4


@dataclass(frozen=True)
class ExpectedCounts:
    """Frozen production counts, overridable only for tests and explicit smokes."""

    shards: int = 512
    responses: int = 64_552_400
    unique_contexts: int = 645_524
    children: int = 79
    datasets: int = 13
    eligible_rows: int = 1_122_396
    pbm_children: int = 21
    other_children: int = 58


WIDE_COLUMNS = [
    "dataset",
    "child_id",
    "child_key",
    "sample_group",
    "session_id",
    "age_months",
    "age_months_source",
    "age_bin",
    "file",
    "line_no",
    "utt_id",
    "utterance_id",
    "context_k3",
    "real_target_text",
    "real_nb_words",
    "real_nb_characters",
    "real_k0_sum_bits",
    "real_k0_mean_bits_per_token",
    "real_k0_n_eval_tokens",
    "real_k3_sum_bits",
    "real_k3_mean_bits_per_token",
    "real_k3_n_eval_tokens",
    "real_context_gain_k3",
]

NUMERIC_BASE_COLUMNS = [
    "age_months",
    "line_no",
    "utt_id",
    "nb_words",
    "nb_characters",
    "real_k0_sum_bits",
    "real_k0_mean_bits_per_token",
    "real_k0_n_eval_tokens",
    "real_k3_sum_bits",
    "real_k3_mean_bits_per_token",
    "real_k3_n_eval_tokens",
    "real_context_gain_k3",
    "route2_context_word_count",
]


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 for one file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_payload_sha256(payload: object) -> str:
    """Hash a JSON-serializable contract."""

    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def atomic_json(payload: object, path: Path) -> None:
    """Atomically write formatted JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    """Atomically write CSV, preserving gzip when requested."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    compression = "gzip" if path.name.endswith(".gz") else None
    frame.to_csv(temporary, index=False, compression=compression, lineterminator="\n")
    os.replace(temporary, path)


def require_file(path: Path, label: str) -> None:
    if not path.is_file() or path.stat().st_size <= 0:
        raise FileNotFoundError(f"{label} is missing or empty: {path}")


def require_equal(actual: int, expected: int, label: str) -> None:
    if int(actual) != int(expected):
        raise RuntimeError(f"expected {expected:,} {label}, found {actual:,}")


def _audit_total(audit: pd.DataFrame, column: str) -> int:
    total = audit[audit["shard_index"].astype(str).eq("TOTAL")]
    if total.empty or column not in total.columns:
        raise RuntimeError(f"generated effort audit has no TOTAL {column}")
    return int(pd.to_numeric(total.iloc[-1][column], errors="raise"))


def validate_generation_handoff(
    *,
    run_root: Path,
    marker: Path,
    expected: ExpectedCounts = ExpectedCounts(),
) -> dict[str, Any]:
    """Refuse incomplete, stale, or count-incompatible Qwen handoffs."""

    require_file(marker, "PRODUCTION_COMPLETE marker")
    merged = run_root / "merged"
    entropy_path = merged / "context_response_entropy_features.csv.gz"
    effort_path = merged / "generated_response_effort_summary_by_context.csv.gz"
    effort_audit_path = merged / "generated_response_effort_summary_audit.csv"
    require_file(entropy_path, "Qwen response-entropy features")
    require_file(effort_path, "Qwen generated-effort summary")
    require_file(effort_audit_path, "Qwen generated-effort audit")

    audit = pd.read_csv(effort_audit_path, dtype=str, keep_default_na=False)
    ok_shards = audit[
        audit["status"].astype(str).eq("ok")
        & ~audit["shard_index"].astype(str).eq("TOTAL")
    ]
    require_equal(len(ok_shards), expected.shards, "completed generation shards")
    selected_rows = _audit_total(audit, "selected_rows")
    feature_rows = _audit_total(audit, "feature_rows")
    require_equal(selected_rows, expected.responses, "selected responses")
    require_equal(feature_rows, expected.unique_contexts, "generated-effort context rows")

    entropy_ids = pd.read_csv(entropy_path, usecols=["context_id"], dtype=str, keep_default_na=False)
    effort_ids = pd.read_csv(effort_path, usecols=["context_id"], dtype=str, keep_default_na=False)
    require_equal(len(entropy_ids), expected.unique_contexts, "response-entropy context rows")
    require_equal(entropy_ids["context_id"].nunique(), expected.unique_contexts, "unique response-entropy contexts")
    require_equal(len(effort_ids), expected.unique_contexts, "generated-effort context rows")
    require_equal(effort_ids["context_id"].nunique(), expected.unique_contexts, "unique generated-effort contexts")
    if set(entropy_ids["context_id"]) != set(effort_ids["context_id"]):
        raise RuntimeError("response-entropy and generated-effort context sets differ")

    return {
        "status": "PASS",
        "run_root": str(run_root),
        "marker": str(marker),
        "marker_sha256": sha256_file(marker),
        "entropy_features": str(entropy_path),
        "entropy_features_sha256": sha256_file(entropy_path),
        "effort_summary": str(effort_path),
        "effort_summary_sha256": sha256_file(effort_path),
        "effort_audit": str(effort_audit_path),
        "effort_audit_sha256": sha256_file(effort_audit_path),
        "shards": len(ok_shards),
        "selected_responses": selected_rows,
        "contexts": feature_rows,
    }


def extract_full79_base_rows(
    *,
    input_wide: Path,
    output_csv: Path,
    chunksize: int,
    expected: ExpectedCounts = ExpectedCounts(),
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Extract the real-child k3 rows used to build the Qwen manifest."""

    require_file(input_wide, "full-79 real-child wide table")
    available = pd.read_csv(input_wide, nrows=0).columns.tolist()
    missing = set(WIDE_COLUMNS) - set(available)
    if missing:
        raise KeyError(f"{input_wide} missing required columns: {sorted(missing)}")

    kept: list[pd.DataFrame] = []
    source_rows = 0
    excluded_blank_context_rows = 0
    excluded_blank_target_rows = 0
    for chunk in pd.read_csv(
        input_wide,
        usecols=WIDE_COLUMNS,
        dtype=str,
        keep_default_na=False,
        chunksize=chunksize,
        low_memory=False,
    ):
        source_rows += len(chunk)
        chunk["context_text"] = chunk["context_k3"].map(normalize_context)
        chunk["target_utterance_clean"] = chunk["real_target_text"].map(normalize_context)
        context_present = chunk["context_text"].ne("")
        target_present = chunk["target_utterance_clean"].ne("")
        excluded_blank_context_rows += int((~context_present).sum())
        excluded_blank_target_rows += int((~target_present).sum())
        out = chunk[context_present & target_present].copy()
        if out.empty:
            continue
        out["child_name"] = out["child_id"].astype(str)
        out["child_id"] = out["dataset"].astype(str) + "/" + out["child_name"]
        if "child_key" in out.columns:
            mismatches = int(out["child_key"].astype(str).ne(out["child_id"]).sum())
            if mismatches:
                raise RuntimeError(f"wide table contains {mismatches} child-key mismatches")
        out["child_key"] = out["child_id"]
        out["sample_group"] = np.where(
            out["dataset"].isin(PBM_DATASETS),
            "pbm_discovery",
            "non_pbm_confirmation",
        )
        out["analysis_scope"] = np.where(
            out["dataset"].isin(PBM_DATASETS),
            "original_21",
            "other_58",
        )
        out["score_id"] = out["utterance_id"].astype(str)
        out["nb_words"] = out["real_nb_words"]
        out["nb_characters"] = out["real_nb_characters"]
        out["response_entropy_context_id"] = out["context_text"].map(context_id)
        out["route2_context_word_count"] = out["context_text"].map(lambda text: len(str(text).split()))
        out = out.drop(columns=["context_k3", "real_target_text", "real_nb_words", "real_nb_characters"])
        for column in NUMERIC_BASE_COLUMNS:
            if column in out.columns:
                out[column] = pd.to_numeric(out[column], errors="coerce")
        kept.append(out)

    frame = pd.concat(kept, ignore_index=True) if kept else pd.DataFrame()
    if frame.empty:
        raise RuntimeError("full-79 Route 2 base extraction produced no eligible rows")
    duplicate_ids = int(frame["utterance_id"].duplicated().sum())
    if duplicate_ids:
        raise RuntimeError(f"full-79 Route 2 base contains {duplicate_ids} duplicate utterance ids")

    children = int(frame["child_id"].nunique())
    datasets = int(frame["dataset"].nunique())
    contexts = int(frame["response_entropy_context_id"].nunique())
    require_equal(children, expected.children, "eligible children")
    require_equal(datasets, expected.datasets, "eligible corpora")
    require_equal(len(frame), expected.eligible_rows, "eligible real-child rows")
    require_equal(contexts, expected.unique_contexts, "eligible unique contexts")
    atomic_csv(frame, output_csv)
    audit = {
        "status": "PASS",
        "input_wide": str(input_wide),
        "input_wide_sha256": sha256_file(input_wide),
        "source_rows": source_rows,
        "eligible_rows": len(frame),
        "eligible_children": children,
        "eligible_datasets": datasets,
        "eligible_unique_contexts": contexts,
        "excluded_blank_context_rows": excluded_blank_context_rows,
        "excluded_blank_target_rows": excluded_blank_target_rows,
        "pbm_children": int(frame.loc[frame["analysis_scope"].eq("original_21"), "child_id"].nunique()),
        "other_children": int(frame.loc[frame["analysis_scope"].eq("other_58"), "child_id"].nunique()),
        "output_csv": str(output_csv),
        "output_sha256": sha256_file(output_csv),
    }
    return frame, audit


def split_scope_tables(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return disjoint original/other scopes plus their descriptive union."""

    required = {"analysis_scope", "utterance_id"}
    missing = required - set(frame.columns)
    if missing:
        raise KeyError(f"full-79 table missing scope columns: {sorted(missing)}")
    original = frame[frame["analysis_scope"].eq("original_21")].copy()
    other = frame[frame["analysis_scope"].eq("other_58")].copy()
    overlap = set(original["utterance_id"]) & set(other["utterance_id"])
    if overlap:
        raise RuntimeError(f"original-21 and other-58 scopes overlap on {len(overlap)} utterances")
    union = pd.concat([original, other], ignore_index=True)
    if len(union) != len(frame) or set(union["utterance_id"]) != set(frame["utterance_id"]):
        raise RuntimeError("original-21 and other-58 scopes do not exactly partition all-79 rows")
    return {"original_21": original, "other_58": other, "all_79": union}


OUTCOMES = [
    ("nb_words", "raw_child_words", "continuous"),
    ("child_words_minus_generated_mean", "minus_generated_mean", "continuous"),
    ("child_words_z_vs_generated", "z_vs_generated", "continuous"),
    ("child_words_percentile_in_generated_distribution", "percentile_in_generated", "continuous"),
    ("child_words_ratio_to_generated_mean", "ratio_to_generated_mean", "continuous"),
    ("child_shorter_than_generated_median", "shorter_than_generated_median", "binary"),
    ("child_longer_than_generated_p90", "longer_than_generated_p90", "binary"),
]


def full79_model_specs() -> list[Route2Spec]:
    """Return the complete, non-selective exploratory model registry."""

    specs: list[Route2Spec] = []
    for outcome, prefix, outcome_type in OUTCOMES:
        rows = [
            (
                "m0_simple_age",
                "M0 simple age association",
                f"{outcome} ~ age_months_c",
                ("age_months_c",),
            ),
            (
                "m1_corpus_adjusted",
                "M1 age with corpus adjustment",
                f"{outcome} ~ age_months_c + C(dataset)",
                ("age_months_c",),
            ),
            (
                "m2_child_identity",
                "M2 age controlling stable child identity",
                f"{outcome} ~ age_months_c + C(child_id)",
                ("age_months_c",),
            ),
            (
                "m3_response_uncertainty",
                "M3 add exact-string response uncertainty",
                f"{outcome} ~ age_months_c + response_entropy_bits_c + C(child_id)",
                ("age_months_c", "response_entropy_bits_c"),
            ),
            (
                "m4_context_demand",
                "M4 add generated demand and context length",
                f"{outcome} ~ age_months_c + generated_expected_words_c + route2_context_word_count_c + C(child_id)",
                ("age_months_c", "generated_expected_words_c", "route2_context_word_count_c"),
            ),
            (
                "m5_uncertainty_context",
                "M5 response uncertainty and context length",
                f"{outcome} ~ age_months_c + response_entropy_bits_c + route2_context_word_count_c + C(child_id)",
                ("age_months_c", "response_entropy_bits_c", "route2_context_word_count_c"),
            ),
            (
                "m6_generated_reference",
                "M6 include the generated reference as a separate sensitivity",
                f"{outcome} ~ age_months_c + response_entropy_bits_c + generated_expected_words_c + route2_context_word_count_c + C(child_id)",
                ("age_months_c", "response_entropy_bits_c", "generated_expected_words_c", "route2_context_word_count_c"),
            ),
            (
                "m7_age_by_response_uncertainty",
                "M7 age × response uncertainty without generated reference",
                f"{outcome} ~ age_months_c + response_entropy_bits_c + age_months_c:response_entropy_bits_c + route2_context_word_count_c + C(child_id)",
                ("age_months_c", "response_entropy_bits_c", "route2_context_word_count_c"),
            ),
            (
                "m8_age_by_uncertainty_with_reference",
                "M8 age × response uncertainty with generated reference",
                f"{outcome} ~ age_months_c + response_entropy_bits_c + age_months_c:response_entropy_bits_c + generated_expected_words_c + route2_context_word_count_c + C(child_id)",
                ("age_months_c", "response_entropy_bits_c", "generated_expected_words_c", "route2_context_word_count_c"),
            ),
            (
                "m9_quadratic_age",
                "M9 quadratic age sensitivity",
                f"{outcome} ~ age_months_c + I(age_months_c ** 2) + response_entropy_bits_c + age_months_c:response_entropy_bits_c + route2_context_word_count_c + C(child_id)",
                ("age_months_c", "response_entropy_bits_c", "route2_context_word_count_c"),
            ),
            (
                "m10_age_bins",
                "M10 age bins sensitivity",
                f"{outcome} ~ C(age_bin) + response_entropy_bits_c + route2_context_word_count_c + C(child_id)",
                ("response_entropy_bits_c", "route2_context_word_count_c"),
            ),
        ]
        for model_suffix, label, formula, required in rows:
            specs.append(
                Route2Spec(
                    model_id=f"{prefix}_{model_suffix}",
                    model_label=label,
                    outcome=outcome,
                    outcome_type=outcome_type,
                    formula=formula,
                    required_cols=required,
                )
            )
    return specs


def scope_role(scope: str) -> str:
    return {
        "original_21": "discovery",
        "other_58": "separate-sample estimate",
        "all_79": "pooled descriptive coverage",
    }[scope]


def run_feature_stage(
    *,
    run_root: Path,
    marker: Path,
    output_dir: Path,
    compute_repo: Path,
    expected: ExpectedCounts,
) -> dict[str, Any]:
    """Build the word-effort distribution summary from frozen Qwen samples."""

    require_file(marker, "PRODUCTION_COMPLETE marker")
    entropy_path = run_root / "merged/context_response_entropy_features.csv.gz"
    require_file(entropy_path, "Qwen response-entropy features")
    if (output_dir / "features_manifest.json").exists():
        try:
            return require_fresh_feature_manifest(output_dir, run_root, marker)
        except (FileNotFoundError, RuntimeError, KeyError, json.JSONDecodeError):
            pass
    effort_path = run_root / "merged/generated_response_effort_summary_by_context.csv.gz"
    effort_audit = run_root / "merged/generated_response_effort_summary_audit.csv"
    rebuild_effort = not effort_path.exists() or not effort_audit.exists()
    if not rebuild_effort:
        try:
            validate_generation_handoff(run_root=run_root, marker=marker, expected=expected)
        except (FileNotFoundError, RuntimeError, KeyError, ValueError):
            rebuild_effort = True
    if rebuild_effort:
        builder = compute_repo / "src/build_response_entropy_effort_summary.py"
        require_file(builder, "compute-repository effort summarizer")
        command = [
            sys.executable,
            str(builder),
            "--run-root",
            str(run_root),
            "--output-dir",
            str(run_root / "merged"),
            "--expected-num-shards",
            str(expected.shards),
        ]
        subprocess.run(command, cwd=compute_repo, check=True)
    audit = validate_generation_handoff(run_root=run_root, marker=marker, expected=expected)
    audit.update(
        {
            "stage": "features",
            "prompt_variant": QWEN_PROMPT,
            "temperature": QWEN_TEMPERATURE,
            "expected": asdict(expected),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    atomic_json(audit, output_dir / "features_manifest.json")
    return audit


def require_fresh_feature_manifest(output_dir: Path, run_root: Path, marker: Path) -> dict[str, Any]:
    path = output_dir / "features_manifest.json"
    require_file(path, "features-stage manifest")
    payload = json.loads(path.read_text(encoding="utf-8"))
    checks = {
        "marker_sha256": marker,
        "entropy_features_sha256": run_root / "merged/context_response_entropy_features.csv.gz",
        "effort_summary_sha256": run_root / "merged/generated_response_effort_summary_by_context.csv.gz",
        "effort_audit_sha256": run_root / "merged/generated_response_effort_summary_audit.csv",
    }
    for key, source in checks.items():
        require_file(source, key)
        if payload.get(key) != sha256_file(source):
            raise RuntimeError(f"stale features-stage manifest: {key} changed")
    return payload


def run_dataset_stage(
    *,
    input_wide: Path,
    run_root: Path,
    marker: Path,
    output_dir: Path,
    expected: ExpectedCounts,
    chunksize: int,
) -> dict[str, Any]:
    """Build the full child-row Route 2 table and frozen scope partitions."""

    feature_manifest = require_fresh_feature_manifest(output_dir, run_root, marker)
    if (output_dir / "dataset_manifest.json").exists():
        try:
            current = require_fresh_dataset_manifest(output_dir)
            if current.get("input_wide_sha256") == sha256_file(input_wide):
                return current
        except (FileNotFoundError, RuntimeError, KeyError, json.JSONDecodeError):
            pass
    dataset_dir = output_dir / "datasets"
    base_path = dataset_dir / "full79_real_child_k3_base.csv.gz"
    base, extraction_audit = extract_full79_base_rows(
        input_wide=input_wide,
        output_csv=base_path,
        chunksize=chunksize,
        expected=expected,
    )
    entropy, entropy_audit = load_entropy_features(
        run_root / "merged/context_response_entropy_features.csv.gz",
        prompt_variant=QWEN_PROMPT,
        temperature=QWEN_TEMPERATURE,
    )
    effort, effort_audit = load_generated_effort_summary(
        run_root / "merged/generated_response_effort_summary_by_context.csv.gz",
        prompt_variant=QWEN_PROMPT,
        temperature=QWEN_TEMPERATURE,
    )
    entropy_keep = [
        "response_entropy_context_id",
        "response_entropy_setting_id",
        "response_entropy_prompt_variant",
        "response_entropy_temperature",
        "response_valid_selected_count",
        "response_invalid_selected_count",
        "response_unique_response_count",
        "response_entropy_empirical_bits",
        "response_entropy_bits",
        "response_top_probability_selected",
        "response_rejection_rate",
        "response_fallback_used",
    ]
    entropy = entropy[[column for column in entropy_keep if column in entropy.columns]].copy()
    effort_keep = [
        "response_entropy_context_id",
        "generated_setting_id",
        "generated_prompt_variant",
        "generated_temperature",
        "generated_valid_selected_rows_observed",
        "generated_invalid_selected_rows_observed",
        "generated_valid_sample_words_n",
        "generated_valid_sample_words_mean",
        "generated_valid_sample_words_sd",
        "generated_valid_sample_words_median",
        "generated_valid_sample_words_p10",
        "generated_valid_sample_words_p90",
        "generated_valid_sample_words_iqr",
        "generated_valid_word_count_entropy_bits",
        "generated_valid_word_count_hist_json",
        "generated_valid_response_top_probability",
        "generated_fallback_used",
        "generated_invalid_selected_top_rejection_reason",
    ]
    effort = effort[[column for column in effort_keep if column in effort.columns]].copy()
    table, join_audit = merge_route2_table(
        route1_rows=base,
        entropy_features=entropy,
        generated_effort=effort,
    )
    if int(join_audit["missing_response_entropy_rows"]) != 0:
        raise RuntimeError(f"full-79 join has {join_audit['missing_response_entropy_rows']} missing entropy rows")
    if int(join_audit["missing_generated_effort_rows"]) != 0:
        raise RuntimeError(f"full-79 join has {join_audit['missing_generated_effort_rows']} missing effort rows")
    require_equal(len(table), expected.eligible_rows, "joined child rows")

    full_path = dataset_dir / "full79_qwen_route2_child_rows.csv.gz"
    atomic_csv(table, full_path)
    scopes = split_scope_tables(table)
    scope_paths: dict[str, str] = {}
    scope_counts: dict[str, Any] = {}
    for scope, frame in scopes.items():
        path = dataset_dir / f"{scope}_qwen_route2_child_rows.csv.gz"
        atomic_csv(frame, path)
        scope_paths[scope] = str(path)
        scope_counts[scope] = {
            "rows": len(frame),
            "children": int(frame["child_id"].nunique()),
            "datasets": int(frame["dataset"].nunique()),
            "contexts": int(frame["response_entropy_context_id"].nunique()),
            "sha256": sha256_file(path),
        }
    require_equal(scope_counts["original_21"]["children"], expected.pbm_children, "original-sample children")
    require_equal(scope_counts["other_58"]["children"], expected.other_children, "other-sample children")
    require_equal(scope_counts["all_79"]["children"], expected.children, "pooled children")

    manifest = {
        "status": "PASS",
        "stage": "datasets",
        "input_wide": str(input_wide),
        "input_wide_sha256": extraction_audit["input_wide_sha256"],
        "feature_manifest_sha256": sha256_file(output_dir / "features_manifest.json"),
        "feature_stage": feature_manifest,
        "extraction_audit": extraction_audit,
        "entropy_audit": entropy_audit,
        "effort_audit": effort_audit,
        "join_audit": join_audit,
        "full_table": str(full_path),
        "full_table_sha256": sha256_file(full_path),
        "scope_paths": scope_paths,
        "scope_counts": scope_counts,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(manifest, output_dir / "dataset_manifest.json")
    atomic_csv(
        pd.DataFrame(
            [
                {"scope": scope, "analysis_role": scope_role(scope), **counts}
                for scope, counts in scope_counts.items()
            ]
        ),
        output_dir / "scope_registry.csv",
    )
    return manifest


def require_fresh_dataset_manifest(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "dataset_manifest.json"
    require_file(path, "dataset-stage manifest")
    payload = json.loads(path.read_text(encoding="utf-8"))
    input_wide = Path(payload["input_wide"])
    require_file(input_wide, "dataset-stage real-child input")
    if sha256_file(input_wide) != payload["input_wide_sha256"]:
        raise RuntimeError("stale dataset-stage manifest: real-child input changed")
    feature_manifest = output_dir / "features_manifest.json"
    require_file(feature_manifest, "features-stage manifest")
    if sha256_file(feature_manifest) != payload["feature_manifest_sha256"]:
        raise RuntimeError("stale dataset-stage manifest: features manifest changed")
    for scope, source_text in payload.get("scope_paths", {}).items():
        source = Path(source_text)
        require_file(source, f"{scope} dataset")
        expected_hash = payload["scope_counts"][scope]["sha256"]
        if sha256_file(source) != expected_hash:
            raise RuntimeError(f"stale dataset-stage manifest: {scope} table changed")
    return payload


def _checkpoint_paths(output_dir: Path, scope: str, model_id: str) -> dict[str, Path]:
    root = output_dir / "models/checkpoints" / scope
    return {
        "summary": root / f"{model_id}.summary.csv",
        "coefficients": root / f"{model_id}.coefficients.csv",
        "manifest": root / f"{model_id}.manifest.json",
    }


def _checkpoint_is_current(
    paths: Mapping[str, Path],
    dataset_sha: str,
    spec_sha: str,
    code_sha: str,
) -> bool:
    if not all(path.is_file() and path.stat().st_size > 0 for path in paths.values()):
        return False
    try:
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        manifest.get("dataset_sha256") == dataset_sha
        and manifest.get("spec_sha256") == spec_sha
        and manifest.get("controller_sha256") == code_sha
    )


def _prediction_grid(frame: pd.DataFrame, result: Any, spec: Route2Spec, estimator_id: str) -> pd.DataFrame:
    ages = np.linspace(frame["age_months"].quantile(0.02), frame["age_months"].quantile(0.98), 40)
    if "response_entropy_bits" in frame.columns and "response_entropy" in spec.model_id:
        entropy_levels = frame["response_entropy_bits"].quantile([0.10, 0.50, 0.90]).dropna().tolist()
    elif "uncertainty" in spec.model_id:
        entropy_levels = frame["response_entropy_bits"].quantile([0.10, 0.50, 0.90]).dropna().tolist()
    else:
        entropy_levels = [float(frame["response_entropy_bits"].mean())]
    child_id = str(frame["child_id"].mode().iloc[0])
    child_dataset = str(frame.loc[frame["child_id"].eq(child_id), "dataset"].mode().iloc[0])
    centers = {
        column: float(pd.to_numeric(frame[column], errors="coerce").mean())
        for column in ["age_months", "response_entropy_bits", "generated_expected_words", "route2_context_word_count"]
    }
    rows: list[dict[str, Any]] = []
    for entropy in entropy_levels:
        for age in ages:
            row = {
                "age_months": age,
                "age_months_c": age - centers["age_months"],
                "response_entropy_bits": entropy,
                "response_entropy_bits_c": entropy - centers["response_entropy_bits"],
                "generated_expected_words": centers["generated_expected_words"],
                "generated_expected_words_c": 0.0,
                "route2_context_word_count": centers["route2_context_word_count"],
                "route2_context_word_count_c": 0.0,
                "child_id": child_id,
                "dataset": child_dataset,
                "response_entropy_level": entropy,
                "estimator_id": estimator_id,
            }
            rows.append(row)
    grid = pd.DataFrame(rows)
    grid[f"predicted_{spec.outcome}"] = result.predict(grid)
    return grid


def _save_prediction_plot(grid: pd.DataFrame, spec: Route2Spec, scope: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    outcome_column = f"predicted_{spec.outcome}"
    for level, group in grid.groupby("response_entropy_level", sort=True):
        label = f"response uncertainty {level:.2f} bits" if grid["response_entropy_level"].nunique() > 1 else "fitted line"
        ax.plot(group["age_months"], group[outcome_column], linewidth=2.1, label=label)
    if spec.outcome == "child_words_minus_generated_mean":
        ax.axhline(0, color="#333333", linewidth=1, linestyle="--")
    ax.set_xlabel("Age in months")
    ax.set_ylabel(spec.outcome.replace("_", " "))
    ax.set_title(f"{scope.replace('_', ' ')} · {spec.model_label}")
    ax.legend(frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _fit_one_checkpoint(
    *,
    frame: pd.DataFrame,
    scope: str,
    spec: Route2Spec,
    dataset_sha: str,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    spec_payload = asdict(spec)
    spec_sha = stable_payload_sha256(spec_payload)
    code_sha = sha256_file(Path(__file__))
    paths = _checkpoint_paths(output_dir, scope, spec.model_id)
    if _checkpoint_is_current(paths, dataset_sha, spec_sha, code_sha):
        return pd.read_csv(paths["summary"]), pd.read_csv(paths["coefficients"])

    results = fit_models(frame, spec)
    summaries: list[dict[str, Any]] = []
    coefficients: list[pd.DataFrame] = []
    prediction_products: list[str] = []
    for summary, coef, fitted in results:
        raw_estimator = str(summary.get("estimator_id", ""))
        has_child_fixed_effect = "C(child_id)" in spec.formula
        estimator = raw_estimator
        if not has_child_fixed_effect:
            estimator = estimator.replace("row_ols_child_fe_cluster", "row_ols_child_cluster")
            estimator = estimator.replace("row_logit_child_fe_cluster", "row_logit_child_cluster")
        summary = {
            "scope": scope,
            "analysis_role": scope_role(scope),
            "generator": "Qwen3-14B",
            "generator_prompt": QWEN_PROMPT,
            "generator_temperature": QWEN_TEMPERATURE,
            **summary,
        }
        summary["estimator_id"] = estimator
        summary["child_fixed_effect"] = has_child_fixed_effect
        if fitted is not None:
            converged = getattr(fitted, "converged", None)
            summary["converged"] = bool(converged) if converged is not None else True
            if converged is False:
                summary["status"] = "fit_nonconverged"
            covariance = getattr(fitted, "cov_re", None)
            if covariance is not None:
                try:
                    eigenvalues = np.linalg.eigvalsh(np.asarray(covariance, dtype=float))
                    summary["random_effect_covariance_min_eigenvalue"] = float(np.min(eigenvalues))
                    summary["random_effect_covariance_boundary"] = bool(np.min(eigenvalues) < 1e-8)
                except (TypeError, ValueError, np.linalg.LinAlgError):
                    pass
        if spec.outcome_type == "binary" and str(summary.get("estimator_id", "")).startswith("session_"):
            summary["binary_session_interpretation"] = "linear-probability sensitivity"
        summaries.append(summary)
        if not coef.empty:
            coef = coef.copy()
            coef["estimator_id"] = estimator
            coef.insert(0, "scope", scope)
            coef.insert(1, "analysis_role", scope_role(scope))
            coefficients.append(coef)
        if fitted is not None and any(token in spec.model_id for token in ["m0_simple_age", "m7_age_by", "m8_age_by"]):
            if estimator in {
                "row_ols_child_cluster",
                "row_logit_child_cluster",
                "row_ols_child_fe_cluster",
                "row_logit_child_fe_cluster",
                "session_gee_exchangeable",
            }:
                try:
                    grid = _prediction_grid(frame, fitted, spec, estimator)
                    stem = f"{scope}__{spec.model_id}__{estimator}"
                    grid_path = output_dir / "models/predictions" / f"{stem}.csv"
                    plot_path = output_dir / "plots" / f"{stem}.png"
                    atomic_csv(grid, grid_path)
                    _save_prediction_plot(grid, spec, scope, plot_path)
                    prediction_products.extend([str(grid_path), str(plot_path)])
                except Exception as error:  # prediction failure is recorded, not hidden
                    summary["prediction_status"] = f"failed:{type(error).__name__}:{error}"

    summary_frame = pd.DataFrame(summaries)
    coefficient_columns = [
        "scope",
        "analysis_role",
        "model_id",
        "model_label",
        "estimator_id",
        "level",
        "outcome",
        "outcome_type",
        "term",
        "estimate",
        "std_error",
        "p_value",
        "conf_low",
        "conf_high",
    ]
    coef_frame = pd.concat(coefficients, ignore_index=True) if coefficients else pd.DataFrame(columns=coefficient_columns)
    atomic_csv(summary_frame, paths["summary"])
    atomic_csv(coef_frame, paths["coefficients"])
    atomic_json(
        {
            "status": "ATTEMPTED",
            "scope": scope,
            "analysis_role": scope_role(scope),
            "dataset_sha256": dataset_sha,
            "spec": spec_payload,
            "spec_sha256": spec_sha,
            "controller_sha256": code_sha,
            "estimators_attempted": len(summary_frame),
            "prediction_products": prediction_products,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        },
        paths["manifest"],
    )
    return summary_frame, coef_frame


def run_model_stage(*, output_dir: Path, model_ids: Sequence[str] | None = None) -> dict[str, Any]:
    """Fit every registered model in each immutable sample scope."""

    dataset_manifest = require_fresh_dataset_manifest(output_dir)
    registry = full79_model_specs()
    if model_ids:
        wanted = set(model_ids)
        known = {spec.model_id for spec in registry}
        unknown = wanted - known
        if unknown:
            raise ValueError(f"unknown model ids: {sorted(unknown)}")
        specs = [spec for spec in registry if spec.model_id in wanted]
    else:
        specs = registry
    inventory = pd.DataFrame(
        [
            {
                **asdict(spec),
                "interpretation": (
                    "exploratory model-ladder result; do not select by p-value or replace the fixed scope comparison"
                ),
            }
            for spec in specs
        ]
    )
    atomic_csv(inventory, output_dir / "model_registry.csv")

    all_summaries: list[pd.DataFrame] = []
    all_coefficients: list[pd.DataFrame] = []
    for scope in ["original_21", "other_58", "all_79"]:
        source = Path(dataset_manifest["scope_paths"][scope])
        dataset_sha = dataset_manifest["scope_counts"][scope]["sha256"]
        frame = add_route2_relative_columns(read_response_space_table(source))
        add_centered_columns(
            frame,
            ["age_months", "response_entropy_bits", "generated_expected_words", "route2_context_word_count"],
        )
        for index, spec in enumerate(specs, start=1):
            print(f"[models] scope={scope} spec={index}/{len(specs)} {spec.model_id}", flush=True)
            summary, coefficients = _fit_one_checkpoint(
                frame=frame,
                scope=scope,
                spec=spec,
                dataset_sha=dataset_sha,
                output_dir=output_dir,
            )
            all_summaries.append(summary)
            all_coefficients.append(coefficients)

    summaries = pd.concat(all_summaries, ignore_index=True)
    coefficients = pd.concat(all_coefficients, ignore_index=True)
    summaries_path = output_dir / "models/model_summaries.csv"
    coefficients_path = output_dir / "models/model_coefficients.csv"
    atomic_csv(summaries, summaries_path)
    atomic_csv(coefficients, coefficients_path)
    manifest = {
        "status": "COMPLETE",
        "stage": "models",
        "dataset_manifest_sha256": sha256_file(output_dir / "dataset_manifest.json"),
        "model_registry_sha256": sha256_file(output_dir / "model_registry.csv"),
        "controller_sha256": sha256_file(Path(__file__)),
        "registered_specs_per_scope": len(specs),
        "complete_registry": not bool(model_ids),
        "scopes": ["original_21", "other_58", "all_79"],
        "estimators_per_spec": ESTIMATORS_PER_SPEC,
        "attempted_fits": len(summaries),
        "successful_fits": int(summaries["status"].eq("fit").sum()),
        "recorded_nonfits": int((~summaries["status"].eq("fit")).sum()),
        "model_summaries": str(summaries_path),
        "model_summaries_sha256": sha256_file(summaries_path),
        "model_coefficients": str(coefficients_path),
        "model_coefficients_sha256": sha256_file(coefficients_path),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(manifest, output_dir / "model_manifest.json")
    return manifest


def run_audit_stage(*, output_dir: Path, expected: ExpectedCounts) -> dict[str, Any]:
    """Audit structural completion without interpreting or selecting estimates."""

    dataset = require_fresh_dataset_manifest(output_dir)
    model_manifest_path = output_dir / "model_manifest.json"
    require_file(model_manifest_path, "model-stage manifest")
    model_manifest = json.loads(model_manifest_path.read_text(encoding="utf-8"))
    if not model_manifest.get("complete_registry", False):
        raise RuntimeError("model-stage manifest is a limited smoke, not the complete registry")
    summaries_path = Path(model_manifest["model_summaries"])
    coefficients_path = Path(model_manifest["model_coefficients"])
    require_file(summaries_path, "model summaries")
    require_file(coefficients_path, "model coefficients")
    if sha256_file(summaries_path) != model_manifest["model_summaries_sha256"]:
        raise RuntimeError("stale model manifest: model summaries changed")
    if sha256_file(coefficients_path) != model_manifest["model_coefficients_sha256"]:
        raise RuntimeError("stale model manifest: model coefficients changed")

    summaries = pd.read_csv(summaries_path)
    specs = full79_model_specs()
    expected_attempts = len(specs) * ESTIMATORS_PER_SPEC * 3
    require_equal(len(summaries), expected_attempts, "attempted scope/spec/estimator fits")
    for scope, child_count in [
        ("original_21", expected.pbm_children),
        ("other_58", expected.other_children),
        ("all_79", expected.children),
    ]:
        scope_rows = summaries[summaries["scope"].eq(scope)]
        require_equal(len(scope_rows), len(specs) * ESTIMATORS_PER_SPEC, f"{scope} model attempts")
        observed = dataset["scope_counts"][scope]["children"]
        require_equal(observed, child_count, f"{scope} dataset children")

    product_paths = [
        output_dir / "features_manifest.json",
        output_dir / "dataset_manifest.json",
        output_dir / "scope_registry.csv",
        output_dir / "model_registry.csv",
        output_dir / "model_manifest.json",
        summaries_path,
        coefficients_path,
    ]
    product_paths.extend(sorted((output_dir / "plots").glob("*.png")))
    hashes = {str(path): sha256_file(path) for path in product_paths if path.is_file()}
    audit = {
        "status": "PASS",
        "analysis": "full-79 Qwen Route 2 exploratory model registry",
        "sample_roles": {
            "original_21": "discovery",
            "other_58": "separate-sample estimate",
            "all_79": "pooled descriptive coverage",
        },
        "registered_specs_per_scope": len(specs),
        "attempted_fits": len(summaries),
        "successful_fits": int(summaries["status"].eq("fit").sum()),
        "recorded_nonfits": int((~summaries["status"].eq("fit")).sum()),
        "plots": len(list((output_dir / "plots").glob("*.png"))),
        "product_hashes": hashes,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "interpretation_guardrail": "No model is selected or promoted by this pipeline; all-79 estimates are descriptive.",
    }
    atomic_json(audit, output_dir / "audit.json")
    marker = output_dir / "FULL79_QWEN_ROUTE2_COMPLETE_AND_AUDITED"
    marker.write_text(
        "PASS\n"
        f"AUDIT_SHA256={sha256_file(output_dir / 'audit.json')}\n"
        f"ATTEMPTED_FITS={len(summaries)}\n"
        f"SUCCESSFUL_FITS={audit['successful_fits']}\n"
        f"RECORDED_NONFITS={audit['recorded_nonfits']}\n"
        f"TIMESTAMP={audit['completed_at']}\n",
        encoding="utf-8",
    )
    return audit


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["features", "datasets", "models", "audit", "all"], default="all")
    parser.add_argument("--qwen-run-root", type=Path, default=DEFAULT_QWEN_RUN)
    parser.add_argument("--generation-marker", type=Path, default=None)
    parser.add_argument("--input-wide", type=Path, default=DEFAULT_WIDE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--compute-repo", type=Path, default=DEFAULT_COMPUTE_REPO)
    parser.add_argument("--chunksize", type=int, default=200_000)
    parser.add_argument("--expected-shards", type=int, default=512)
    parser.add_argument("--expected-responses", type=int, default=64_552_400)
    parser.add_argument("--expected-contexts", type=int, default=645_524)
    parser.add_argument("--expected-children", type=int, default=79)
    parser.add_argument("--expected-datasets", type=int, default=13)
    parser.add_argument("--expected-eligible-rows", type=int, default=1_122_396)
    parser.add_argument("--expected-pbm-children", type=int, default=21)
    parser.add_argument("--expected-other-children", type=int, default=58)
    parser.add_argument(
        "--model-ids",
        default="",
        help="Comma-separated smoke-only subset. Omit for the complete production registry.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    model_ids = [value.strip() for value in args.model_ids.split(",") if value.strip()]
    if model_ids and args.stage in {"all", "audit"}:
        raise SystemExit("--model-ids is smoke-only and cannot be combined with all/audit")
    marker = args.generation_marker or (args.qwen_run_root / "PRODUCTION_COMPLETE")
    expected = ExpectedCounts(
        shards=args.expected_shards,
        responses=args.expected_responses,
        unique_contexts=args.expected_contexts,
        children=args.expected_children,
        datasets=args.expected_datasets,
        eligible_rows=args.expected_eligible_rows,
        pbm_children=args.expected_pbm_children,
        other_children=args.expected_other_children,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.stage in {"features", "all"}:
        run_feature_stage(
            run_root=args.qwen_run_root,
            marker=marker,
            output_dir=args.output_dir,
            compute_repo=args.compute_repo,
            expected=expected,
        )
    if args.stage in {"datasets", "all"}:
        run_dataset_stage(
            input_wide=args.input_wide,
            run_root=args.qwen_run_root,
            marker=marker,
            output_dir=args.output_dir,
            expected=expected,
            chunksize=args.chunksize,
        )
    if args.stage in {"models", "all"}:
        run_model_stage(output_dir=args.output_dir, model_ids=model_ids or None)
    if args.stage in {"audit", "all"}:
        run_audit_stage(output_dir=args.output_dir, expected=expected)
    print(f"[OK] stage={args.stage} output={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
