#!/usr/bin/env python3
"""Assemble and fit downstream caregiver-response utility models.

This workflow consumes audited scorer outputs only.  It never fits models
during dataset construction and never pools raw bits across scorer tokenizers.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF = PROJECT_ROOT / "results/downstream_caregiver_response_handoff/full_20260827"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/downstream_caregiver_response_analysis"
CONDITIONS = (
    "unconditional",
    "base_context",
    "matched_child",
    "shuffled_child",
    "child_only",
)
CORE_CONDITIONS = ("unconditional", "base_context", "matched_child", "child_only")
SCOPES = ("pbm_discovery", "non_pbm_confirmation", "all79_descriptive")
OUTCOMES = (
    "downstream_gain_bits",
    "matched_over_shuffled_bits",
    "child_only_gain_bits",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bool_series(values: pd.Series) -> pd.Series:
    return values.astype(str).str.strip().str.lower().isin({"1", "true", "t", "yes"})


def _atomic_csv_gz(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                frame.to_csv(text, index=False, lineterminator="\n")
    os.replace(temporary, path)


def _read_inventory(handoff_root: Path) -> pd.DataFrame:
    audit = json.loads((handoff_root / "audit.json").read_text(encoding="utf-8"))
    if audit.get("status") != "PASS":
        raise ValueError("downstream handoff audit is not PASS")
    marker = handoff_root / "BUILD_COMPLETE_AND_AUDITED"
    if not marker.is_file():
        raise ValueError("downstream handoff completion marker is missing")
    inventory = pd.read_csv(handoff_root / "dataset_inventory.csv", keep_default_na=False)
    if len(inventory) != int(audit["totals"]["datasets"]):
        raise ValueError("downstream handoff inventory count changed")
    return inventory


def _score_path(score_root: Path, dataset: str, condition: str) -> Path:
    return score_root / dataset / condition / "caregiver_response_surprisal/utterances.csv.gz"


def assemble_scorer_dataset(
    *,
    handoff_root: Path,
    score_root: Path,
    scorer_key: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    inventory = _read_inventory(handoff_root)
    assembled: list[pd.DataFrame] = []
    condition_rows: Counter[str] = Counter()
    for item in inventory.to_dict("records"):
        dataset = str(item["dataset"])
        source_path = handoff_root / str(item["input_relpath"])
        if sha256_file(source_path) != str(item["sha256"]):
            raise ValueError(f"handoff input SHA-256 changed: {dataset}")
        source = pd.read_csv(source_path, dtype=str, keep_default_na=False)
        if len(source) != int(item["rows"]):
            raise ValueError(f"handoff input row count changed: {dataset}")
        if source["response_pair_id"].duplicated().any():
            raise ValueError(f"duplicate response pair IDs in handoff: {dataset}")
        base_columns = [
            "response_pair_id", "dataset", "child_id", "child_key", "sample_group",
            "session_id", "age_months", "age_bin", "file", "line_no",
            "next_caregiver_line_no", "target_text_sha256", "child_text_sha256",
            "child_word_count", "child_character_count", "response_word_count",
            "response_character_count", "base_context_word_count", "primary_eligible",
            "sensitivity_eligible", "shuffle_available", "shuffle_match_level",
            "previous_caretaker_question_type", "child_question_type",
            "next_caregiver_question_type", "exact_imitation_candidate",
            "contained_imitation_candidate", "child_backchannel_candidate",
            "session_reading_candidate", "session_routine_candidate",
            "repair_sequence_candidate", "next_caregiver_clarification_candidate",
            "next_caregiver_acknowledgement_candidate",
        ]
        joined = source[base_columns].copy()
        for condition in CONDITIONS:
            path = _score_path(score_root, dataset, condition)
            if not path.is_file():
                raise FileNotFoundError(f"missing score table: {path}")
            marker = path.parent / "CONTRACT_COMPLETE"
            if not marker.is_file():
                raise ValueError(f"score contract marker missing: {marker}")
            scored = pd.read_csv(path, dtype=str, keep_default_na=False)
            if len(scored) != len(source):
                raise ValueError(f"score row count mismatch: {scorer_key}/{dataset}/{condition}")
            if scored["utterance_id"].duplicated().any():
                raise ValueError(f"duplicate scored response IDs: {scorer_key}/{dataset}/{condition}")
            if set(scored["utterance_id"]) != set(source["response_pair_id"]):
                raise ValueError(f"scored response identity mismatch: {scorer_key}/{dataset}/{condition}")
            score = scored[
                ["utterance_id", "target_text", "score_status", "context_available", "utterance_sum_bits"]
            ].copy()
            score["target_text_sha256_scored"] = score["target_text"].map(
                lambda value: hashlib.sha256(" ".join(str(value).split()).encode()).hexdigest()
            )
            score = score.rename(
                columns={
                    "utterance_id": "response_pair_id",
                    "score_status": f"{condition}_status",
                    "context_available": f"{condition}_context_available",
                    "utterance_sum_bits": f"{condition}_bits",
                    "target_text_sha256_scored": f"{condition}_target_sha256",
                }
            ).drop(columns="target_text")
            joined = joined.merge(score, on="response_pair_id", how="left", validate="one_to_one")
            if not (joined[f"{condition}_target_sha256"] == joined["target_text_sha256"]).all():
                raise ValueError(f"scored target text mismatch: {scorer_key}/{dataset}/{condition}")
            condition_rows[condition] += len(score)
        assembled.append(joined)

    frame = pd.concat(assembled, ignore_index=True)
    for condition in CONDITIONS:
        frame[f"{condition}_bits"] = pd.to_numeric(frame[f"{condition}_bits"], errors="coerce")
    core_scored = np.logical_and.reduce(
        [(frame[f"{condition}_status"] == "scored").to_numpy() for condition in CORE_CONDITIONS]
    )
    primary = pd.to_numeric(frame["primary_eligible"], errors="coerce").fillna(0).astype(int).eq(1)
    if not bool(core_scored[primary.to_numpy()].all()):
        raise ValueError(f"primary rows have missing core scores for {scorer_key}")
    frame["downstream_gain_bits"] = frame["base_context_bits"] - frame["matched_child_bits"]
    frame["matched_over_shuffled_bits"] = frame["shuffled_child_bits"] - frame["matched_child_bits"]
    frame["child_only_gain_bits"] = frame["unconditional_bits"] - frame["child_only_bits"]
    frame.insert(0, "scorer_key", scorer_key)
    audit = {
        "status": "PASS",
        "scorer_key": scorer_key,
        "rows": len(frame),
        "primary_rows": int(primary.sum()),
        "core_complete_primary_rows": int(core_scored[primary.to_numpy()].sum()),
        "shuffle_scored_rows": int((frame["shuffled_child_status"] == "scored").sum()),
        "condition_rows": dict(condition_rows),
    }
    return frame, audit


def _scope_frame(frame: pd.DataFrame, scope: str) -> pd.DataFrame:
    primary = pd.to_numeric(frame["primary_eligible"], errors="coerce").fillna(0).astype(int).eq(1)
    if scope == "pbm_discovery":
        return frame[primary & frame["sample_group"].eq("pbm_discovery")].copy()
    if scope == "non_pbm_confirmation":
        return frame[primary & frame["sample_group"].eq("non_pbm_confirmation")].copy()
    if scope == "all79_descriptive":
        return frame[primary].copy()
    raise ValueError(f"unknown scope: {scope}")


def make_model_cells(frame: pd.DataFrame, outcome: str) -> pd.DataFrame:
    working = frame.copy()
    for column in ("age_months", "child_word_count", "response_word_count"):
        working[column] = pd.to_numeric(working[column], errors="coerce")
    working[outcome] = pd.to_numeric(working[outcome], errors="coerce")
    working = working.dropna(subset=[outcome, "age_months", "child_word_count", "response_word_count"])
    working["child_words_top12"] = working["child_word_count"].clip(upper=12).astype(int)
    working["response_words_top12"] = working["response_word_count"].clip(upper=12).astype(int)
    working["age_c"] = working["age_months"] - 39.0
    group = [
        "dataset", "child_key", "age_bin", "child_words_top12",
        "response_words_top12",
    ]
    cells = (
        working.groupby(group, observed=True, dropna=False)
        .agg(outcome_mean=(outcome, "mean"), age_c=("age_c", "mean"), source_rows=(outcome, "size"))
        .reset_index()
    )
    return cells


def fit_primary_cell_model(cells: pd.DataFrame) -> tuple[dict[str, object], pd.DataFrame]:
    if cells["child_key"].nunique() < 2:
        raise ValueError("primary model requires at least two children")
    formula = (
        "outcome_mean ~ age_c + C(child_words_top12) + "
        "C(response_words_top12) + C(child_key)"
    )
    fitted = smf.wls(formula, data=cells, weights=cells["source_rows"]).fit(
        cov_type="cluster", cov_kwds={"groups": cells["child_key"]}
    )
    coefficients = pd.DataFrame(
        {
            "term": fitted.params.index,
            "estimate": fitted.params.values,
            "std_error": fitted.bse.values,
            "ci_low": fitted.conf_int()[0].values,
            "ci_high": fitted.conf_int()[1].values,
            "p_value": fitted.pvalues.values,
        }
    )
    age = coefficients[coefficients["term"] == "age_c"]
    if len(age) != 1:
        raise ValueError("primary age coefficient is missing")
    age_row = age.iloc[0]
    summary = {
        "status": "PASS",
        "formula": formula,
        "estimator": "opportunity_weighted_cell_wls_child_clustered",
        "cells": len(cells),
        "source_rows": int(cells["source_rows"].sum()),
        "children": int(cells["child_key"].nunique()),
        "corpora": int(cells["dataset"].nunique()),
        "age_estimate": float(age_row["estimate"]),
        "age_std_error": float(age_row["std_error"]),
        "age_ci_low": float(age_row["ci_low"]),
        "age_ci_high": float(age_row["ci_high"]),
        "age_p_value": float(age_row["p_value"]),
    }
    return summary, coefficients


def bootstrap_age_slope(
    cells: pd.DataFrame,
    *,
    reps: int,
    seed: int,
) -> pd.DataFrame:
    if reps < 1:
        return pd.DataFrame(columns=["replicate", "age_estimate", "status"])
    children = sorted(cells["child_key"].unique())
    rng = np.random.default_rng(seed)
    rows = []
    for replicate in range(reps):
        draw = rng.choice(children, size=len(children), replace=True)
        pieces = []
        for position, child in enumerate(draw):
            part = cells[cells["child_key"] == child].copy()
            part["child_key"] = f"bootstrap_{position:04d}"
            pieces.append(part)
        sample = pd.concat(pieces, ignore_index=True)
        try:
            summary, _ = fit_primary_cell_model(sample)
            rows.append({"replicate": replicate, "age_estimate": summary["age_estimate"], "status": "PASS"})
        except Exception as exc:  # retained explicitly for audit
            rows.append({"replicate": replicate, "age_estimate": np.nan, "status": f"FAIL:{exc}"})
    return pd.DataFrame(rows)


def fit_registered_models(
    frame: pd.DataFrame,
    *,
    bootstrap_reps: int = 1000,
    seed: int = 20260827,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    registry = []
    coefficient_frames = []
    bootstrap_frames = []
    scorer_key = str(frame["scorer_key"].iloc[0])
    for scope_index, scope in enumerate(SCOPES):
        scoped = _scope_frame(frame, scope)
        for outcome_index, outcome in enumerate(OUTCOMES):
            cells = make_model_cells(scoped, outcome)
            summary, coefficients = fit_primary_cell_model(cells)
            model_id = f"{scorer_key}__{scope}__{outcome}"
            registry.append({"model_id": model_id, "scorer_key": scorer_key, "scope": scope, "outcome": outcome, **summary})
            coefficients.insert(0, "model_id", model_id)
            coefficient_frames.append(coefficients)
            draws = bootstrap_age_slope(
                cells,
                reps=bootstrap_reps,
                seed=seed + scope_index * 100 + outcome_index,
            )
            draws.insert(0, "model_id", model_id)
            bootstrap_frames.append(draws)
    return (
        pd.DataFrame(registry),
        pd.concat(coefficient_frames, ignore_index=True),
        pd.concat(bootstrap_frames, ignore_index=True),
    )


def parse_score_roots(values: Sequence[str]) -> dict[str, Path]:
    roots = {}
    for value in values:
        if "=" not in value:
            raise ValueError("--score-root requires SCORER=PATH")
        scorer, raw_path = value.split("=", 1)
        scorer = scorer.strip()
        if not scorer or scorer in roots:
            raise ValueError(f"invalid or duplicate scorer root: {scorer!r}")
        roots[scorer] = Path(raw_path).expanduser().resolve()
    return roots


def run_datasets(*, handoff_root: Path, score_roots: Mapping[str, Path], output_dir: Path) -> None:
    if not score_roots:
        raise ValueError("datasets stage requires at least one --score-root")
    audits = []
    for scorer, root in sorted(score_roots.items()):
        frame, audit = assemble_scorer_dataset(
            handoff_root=handoff_root,
            score_root=root,
            scorer_key=scorer,
        )
        path = output_dir / "datasets" / f"{scorer}.response_utility.csv.gz"
        _atomic_csv_gz(frame, path)
        audit["output"] = str(path)
        audit["output_sha256"] = sha256_file(path)
        audits.append(audit)
    audit_path = output_dir / "datasets/dataset_audit.json"
    audit_path.write_text(json.dumps({"status": "PASS", "scorers": audits}, indent=2, sort_keys=True) + "\n")
    (output_dir / "datasets/DATASETS_COMPLETE").write_text(f"{sha256_file(audit_path)}\n")


def run_models(*, output_dir: Path, bootstrap_reps: int) -> None:
    marker = output_dir / "datasets/DATASETS_COMPLETE"
    if not marker.is_file():
        raise ValueError("datasets stage is incomplete")
    paths = sorted((output_dir / "datasets").glob("*.response_utility.csv.gz"))
    if not paths:
        raise ValueError("no assembled scorer datasets found")
    registry_frames = []
    coefficient_frames = []
    bootstrap_frames = []
    for path in paths:
        frame = pd.read_csv(path, keep_default_na=False)
        registry, coefficients, bootstraps = fit_registered_models(
            frame,
            bootstrap_reps=bootstrap_reps,
        )
        registry_frames.append(registry)
        coefficient_frames.append(coefficients)
        bootstrap_frames.append(bootstraps)
    models_dir = output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    registry = pd.concat(registry_frames, ignore_index=True)
    coefficients = pd.concat(coefficient_frames, ignore_index=True)
    bootstraps = pd.concat(bootstrap_frames, ignore_index=True)
    registry.to_csv(models_dir / "model_registry.csv", index=False)
    coefficients.to_csv(models_dir / "coefficients.csv", index=False)
    _atomic_csv_gz(bootstraps, models_dir / "child_bootstrap_draws.csv.gz")
    audit = {
        "status": "PASS" if registry["status"].eq("PASS").all() else "FAIL",
        "models": len(registry),
        "models_passed": int(registry["status"].eq("PASS").sum()),
        "bootstrap_requested_per_model": bootstrap_reps,
        "bootstrap_failures": int((bootstraps["status"] != "PASS").sum()),
    }
    if audit["status"] != "PASS" or audit["bootstrap_failures"]:
        raise ValueError(f"registered model audit failed: {audit}")
    audit_path = models_dir / "models_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    (models_dir / "MODELS_COMPLETE").write_text(f"{sha256_file(audit_path)}\n")


def run_audit(*, output_dir: Path) -> None:
    required = [
        output_dir / "datasets/DATASETS_COMPLETE",
        output_dir / "models/MODELS_COMPLETE",
        output_dir / "datasets/dataset_audit.json",
        output_dir / "models/models_audit.json",
        output_dir / "models/model_registry.csv",
        output_dir / "models/coefficients.csv",
        output_dir / "models/child_bootstrap_draws.csv.gz",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"analysis artifacts missing: {missing}")
    registry = pd.read_csv(output_dir / "models/model_registry.csv")
    expected = registry["scorer_key"].nunique() * len(SCOPES) * len(OUTCOMES)
    if len(registry) != expected or not registry["status"].eq("PASS").all():
        raise ValueError("registered model inventory is incomplete")
    audit = {
        "status": "PASS",
        "models": len(registry),
        "scorers": sorted(registry["scorer_key"].unique()),
        "artifact_sha256": {
            path.relative_to(output_dir).as_posix(): sha256_file(path)
            for path in required[2:]
        },
    }
    final_path = output_dir / "final_audit.json"
    final_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    (output_dir / "DOWNSTREAM_RESPONSE_EFFICIENCY_COMPLETE_AND_AUDITED").write_text(
        f"{sha256_file(final_path)}\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("datasets", "models", "audit", "all"), default="all")
    parser.add_argument("--handoff-root", type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument("--score-root", action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bootstrap-reps", type=int, default=1000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    score_roots = parse_score_roots(args.score_root)
    if args.stage in {"datasets", "all"}:
        run_datasets(handoff_root=args.handoff_root, score_roots=score_roots, output_dir=args.output_dir)
    if args.stage in {"models", "all"}:
        run_models(output_dir=args.output_dir, bootstrap_reps=args.bootstrap_reps)
    if args.stage in {"audit", "all"}:
        run_audit(output_dir=args.output_dir)


if __name__ == "__main__":
    main()
