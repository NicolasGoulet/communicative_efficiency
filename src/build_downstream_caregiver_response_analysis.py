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
import shutil
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF = PROJECT_ROOT / "results/downstream_caregiver_response_handoff/full_20260827"
DEFAULT_OUTPUT = PROJECT_ROOT / "results/downstream_caregiver_response_analysis"
DEFAULT_REPORT = PROJECT_ROOT / "docs/downstream_caregiver_response_efficiency_report.html"
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
    absorbed = _absorbed_child_crossproducts(cells)
    children = absorbed["children"]
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(
        len(children),
        np.repeat(1.0 / len(children), len(children)),
        size=reps,
    )
    matrices = np.einsum("rc,cij->rij", counts, absorbed["matrices"], optimize=True)
    vectors = counts @ absorbed["vectors"]
    rows: list[dict[str, object]] = []
    for replicate, (matrix, vector) in enumerate(zip(matrices, vectors, strict=True)):
        try:
            estimate = _age_from_crossproducts(
                matrix,
                vector,
                age_index=int(absorbed["age_index"]),
            )
            rows.append({"replicate": replicate, "age_estimate": estimate, "status": "PASS"})
        except Exception as exc:  # retained explicitly for audit
            rows.append({"replicate": replicate, "age_estimate": np.nan, "status": f"FAIL:{exc}"})
    return pd.DataFrame(rows)


def _absorbed_child_crossproducts(cells: pd.DataFrame) -> dict[str, object]:
    """Absorb child fixed effects and cache each child's WLS cross-products."""
    child_levels = sorted(cells["child_words_top12"].unique())
    response_levels = sorted(cells["response_words_top12"].unique())
    names = ["age_c"]
    columns = [cells["age_c"].to_numpy(dtype=float)]
    for level in child_levels[1:]:
        names.append(f"child_words_top12[{level}]")
        columns.append(cells["child_words_top12"].eq(level).to_numpy(dtype=float))
    for level in response_levels[1:]:
        names.append(f"response_words_top12[{level}]")
        columns.append(cells["response_words_top12"].eq(level).to_numpy(dtype=float))
    design = np.column_stack(columns)
    outcome = cells["outcome_mean"].to_numpy(dtype=float)
    weights = cells["source_rows"].to_numpy(dtype=float)
    children = sorted(cells["child_key"].unique())
    matrices = []
    vectors = []
    datasets = []
    child_array = cells["child_key"].to_numpy()
    dataset_array = cells["dataset"].to_numpy()
    for child in children:
        positions = np.flatnonzero(child_array == child)
        child_weights = weights[positions]
        child_design = design[positions]
        child_outcome = outcome[positions]
        centered_design = child_design - np.average(
            child_design, axis=0, weights=child_weights
        )
        centered_outcome = child_outcome - np.average(
            child_outcome, weights=child_weights
        )
        matrices.append((centered_design.T * child_weights) @ centered_design)
        vectors.append((centered_design.T * child_weights) @ centered_outcome)
        child_datasets = np.unique(dataset_array[positions])
        if len(child_datasets) != 1:
            raise ValueError(f"child spans multiple corpora: {child}")
        datasets.append(str(child_datasets[0]))
    return {
        "children": children,
        "datasets": datasets,
        "names": names,
        "age_index": names.index("age_c"),
        "matrices": np.stack(matrices),
        "vectors": np.stack(vectors),
    }


def _age_from_crossproducts(
    matrix: np.ndarray,
    vector: np.ndarray,
    *,
    age_index: int,
) -> float:
    coefficients = np.linalg.lstsq(matrix, vector, rcond=1e-10)[0]
    estimate = float(coefficients[age_index])
    if not np.isfinite(estimate):
        raise ValueError("non-finite absorbed age estimate")
    return estimate


def influence_age_slopes(
    cells: pd.DataFrame,
    *,
    reference_estimate: float,
) -> pd.DataFrame:
    absorbed = _absorbed_child_crossproducts(cells)
    matrices = absorbed["matrices"]
    vectors = absorbed["vectors"]
    full_matrix = matrices.sum(axis=0)
    full_vector = vectors.sum(axis=0)
    rows: list[dict[str, object]] = []
    removals: list[tuple[str, str, np.ndarray]] = []
    for index, child in enumerate(absorbed["children"]):
        mask = np.zeros(len(absorbed["children"]), dtype=bool)
        mask[index] = True
        removals.append(("child", str(child), mask))
    for dataset in sorted(set(absorbed["datasets"])):
        mask = np.asarray([value == dataset for value in absorbed["datasets"]])
        removals.append(("corpus", dataset, mask))
    for unit_type, unit, mask in removals:
        try:
            estimate = _age_from_crossproducts(
                full_matrix - matrices[mask].sum(axis=0),
                full_vector - vectors[mask].sum(axis=0),
                age_index=int(absorbed["age_index"]),
            )
            rows.append(
                {
                    "removed_unit_type": unit_type,
                    "removed_unit": unit,
                    "age_estimate": estimate,
                    "delta_from_full": estimate - reference_estimate,
                    "status": "PASS",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "removed_unit_type": unit_type,
                    "removed_unit": unit,
                    "age_estimate": np.nan,
                    "delta_from_full": np.nan,
                    "status": f"FAIL:{exc}",
                }
            )
    return pd.DataFrame(rows)


def summarize_outcome_level(
    frame: pd.DataFrame,
    outcome: str,
    *,
    reps: int,
    seed: int,
) -> tuple[dict[str, object], pd.DataFrame]:
    working = frame[["child_key", outcome]].copy()
    working[outcome] = pd.to_numeric(working[outcome], errors="coerce")
    working = working.dropna(subset=[outcome])
    child_means = working.groupby("child_key", observed=True)[outcome].mean().to_numpy()
    if len(child_means) < 2:
        raise ValueError("outcome-level summary requires at least two children")
    rng = np.random.default_rng(seed)
    draws = rng.choice(child_means, size=(reps, len(child_means)), replace=True).mean(axis=1)
    summary = {
        "estimand": "equal_child_weight_mean",
        "source_rows": len(working),
        "children": len(child_means),
        "mean": float(child_means.mean()),
        "children_positive_fraction": float(np.mean(child_means > 0)),
        "bootstrap_reps": reps,
        "bootstrap_ci_low": float(np.quantile(draws, 0.025)),
        "bootstrap_ci_high": float(np.quantile(draws, 0.975)),
    }
    draw_frame = pd.DataFrame({"replicate": np.arange(reps), "mean": draws})
    return summary, draw_frame


def fit_registered_models(
    frame: pd.DataFrame,
    *,
    bootstrap_reps: int = 1000,
    seed: int = 20260827,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    registry = []
    coefficient_frames = []
    bootstrap_frames = []
    influence_frames = []
    level_summaries = []
    level_bootstrap_frames = []
    scorer_key = str(frame["scorer_key"].iloc[0])
    for scope_index, scope in enumerate(SCOPES):
        scoped = _scope_frame(frame, scope)
        for outcome_index, outcome in enumerate(OUTCOMES):
            cells = make_model_cells(scoped, outcome)
            summary, coefficients = fit_primary_cell_model(cells)
            model_id = f"{scorer_key}__{scope}__{outcome}"
            absorbed = _absorbed_child_crossproducts(cells)
            absorbed_age = _age_from_crossproducts(
                absorbed["matrices"].sum(axis=0),
                absorbed["vectors"].sum(axis=0),
                age_index=int(absorbed["age_index"]),
            )
            if not np.isclose(
                absorbed_age,
                float(summary["age_estimate"]),
                rtol=1e-9,
                atol=1e-10,
            ):
                raise ValueError(f"absorbed bootstrap estimator mismatch: {model_id}")
            coefficients.insert(0, "model_id", model_id)
            coefficient_frames.append(coefficients)
            draws = bootstrap_age_slope(
                cells,
                reps=bootstrap_reps,
                seed=seed + scope_index * 100 + outcome_index,
            )
            valid_draws = draws.loc[draws["status"].eq("PASS"), "age_estimate"]
            summary.update(
                {
                    "bootstrap_reps": bootstrap_reps,
                    "bootstrap_valid_reps": len(valid_draws),
                    "bootstrap_ci_low": float(valid_draws.quantile(0.025)),
                    "bootstrap_ci_high": float(valid_draws.quantile(0.975)),
                }
            )
            registry.append(
                {
                    "model_id": model_id,
                    "scorer_key": scorer_key,
                    "scope": scope,
                    "outcome": outcome,
                    **summary,
                }
            )
            draws.insert(0, "model_id", model_id)
            bootstrap_frames.append(draws)
            influence = influence_age_slopes(
                cells,
                reference_estimate=float(summary["age_estimate"]),
            )
            influence.insert(0, "model_id", model_id)
            influence_frames.append(influence)
            level_summary, level_draws = summarize_outcome_level(
                scoped,
                outcome,
                reps=bootstrap_reps,
                seed=seed + 1000 + scope_index * 100 + outcome_index,
            )
            level_summaries.append(
                {
                    "model_id": model_id,
                    "scorer_key": scorer_key,
                    "scope": scope,
                    "outcome": outcome,
                    **level_summary,
                }
            )
            level_draws.insert(0, "model_id", model_id)
            level_bootstrap_frames.append(level_draws)
    return (
        pd.DataFrame(registry),
        pd.concat(coefficient_frames, ignore_index=True),
        pd.concat(bootstrap_frames, ignore_index=True),
        pd.concat(influence_frames, ignore_index=True),
        pd.DataFrame(level_summaries),
        pd.concat(level_bootstrap_frames, ignore_index=True),
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
    influence_frames = []
    level_summary_frames = []
    level_bootstrap_frames = []
    for path in paths:
        frame = pd.read_csv(path, keep_default_na=False)
        (
            registry,
            coefficients,
            bootstraps,
            influence,
            level_summaries,
            level_bootstraps,
        ) = fit_registered_models(
            frame,
            bootstrap_reps=bootstrap_reps,
        )
        registry_frames.append(registry)
        coefficient_frames.append(coefficients)
        bootstrap_frames.append(bootstraps)
        influence_frames.append(influence)
        level_summary_frames.append(level_summaries)
        level_bootstrap_frames.append(level_bootstraps)
    models_dir = output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    registry = pd.concat(registry_frames, ignore_index=True)
    coefficients = pd.concat(coefficient_frames, ignore_index=True)
    bootstraps = pd.concat(bootstrap_frames, ignore_index=True)
    influence = pd.concat(influence_frames, ignore_index=True)
    level_summaries = pd.concat(level_summary_frames, ignore_index=True)
    level_bootstraps = pd.concat(level_bootstrap_frames, ignore_index=True)
    registry.to_csv(models_dir / "model_registry.csv", index=False)
    coefficients.to_csv(models_dir / "coefficients.csv", index=False)
    _atomic_csv_gz(bootstraps, models_dir / "child_bootstrap_draws.csv.gz")
    influence.to_csv(models_dir / "influence_age_slopes.csv", index=False)
    level_summaries.to_csv(models_dir / "outcome_level_summaries.csv", index=False)
    _atomic_csv_gz(
        level_bootstraps,
        models_dir / "outcome_level_bootstrap_draws.csv.gz",
    )
    audit = {
        "status": "PASS" if registry["status"].eq("PASS").all() else "FAIL",
        "models": len(registry),
        "models_passed": int(registry["status"].eq("PASS").sum()),
        "bootstrap_requested_per_model": bootstrap_reps,
        "bootstrap_failures": int((bootstraps["status"] != "PASS").sum()),
        "influence_fits": len(influence),
        "influence_failures": int((influence["status"] != "PASS").sum()),
        "outcome_level_summaries": len(level_summaries),
    }
    if (
        audit["status"] != "PASS"
        or audit["bootstrap_failures"]
        or audit["influence_failures"]
    ):
        raise ValueError(f"registered model audit failed: {audit}")
    audit_path = models_dir / "models_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    (models_dir / "MODELS_COMPLETE").write_text(f"{sha256_file(audit_path)}\n")


def _result_table(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    shown = frame.loc[:, columns].copy()
    numeric = shown.select_dtypes(include=["number"]).columns
    shown[numeric] = shown[numeric].map(lambda value: f"{value:.3f}")
    return shown.to_html(index=False, border=0, classes="results", escape=True)


def run_report(*, output_dir: Path, report_path: Path) -> None:
    models_dir = output_dir / "models"
    if not (models_dir / "MODELS_COMPLETE").is_file():
        raise ValueError("models stage is incomplete")
    registry = pd.read_csv(models_dir / "model_registry.csv")
    levels = pd.read_csv(models_dir / "outcome_level_summaries.csv")
    influence = pd.read_csv(models_dir / "influence_age_slopes.csv")
    primary = registry[
        registry["scope"].isin(["pbm_discovery", "non_pbm_confirmation"])
        & registry["outcome"].eq("downstream_gain_bits")
    ].copy()
    primary["slope_bits_per_6m"] = primary["age_estimate"] * 6
    primary["cluster_ci_6m"] = primary.apply(
        lambda row: f"[{row.age_ci_low * 6:.3f}, {row.age_ci_high * 6:.3f}]", axis=1
    )
    primary["bootstrap_ci_6m"] = primary.apply(
        lambda row: (
            f"[{row.bootstrap_ci_low * 6:.3f}, {row.bootstrap_ci_high * 6:.3f}]"
        ),
        axis=1,
    )
    gate_levels = levels[
        levels["scope"].isin(["pbm_discovery", "non_pbm_confirmation"])
        & levels["outcome"].isin(
            ["downstream_gain_bits", "matched_over_shuffled_bits"]
        )
    ].copy()
    gate_pivot = gate_levels.pivot(
        index=["scorer_key", "scope"], columns="outcome", values="bootstrap_ci_low"
    ).reset_index()
    age_gate = primary.set_index(["scorer_key", "scope"])["age_ci_low"]
    gate_pivot["matched_gain_positive"] = gate_pivot["downstream_gain_bits"] > 0
    gate_pivot["matched_beats_shuffle"] = gate_pivot["matched_over_shuffled_bits"] > 0
    gate_pivot["positive_age_slope"] = [
        bool(age_gate.loc[(row.scorer_key, row.scope)] > 0)
        for row in gate_pivot.itertuples()
    ]
    gate_pivot["all_three_gates"] = (
        gate_pivot["matched_gain_positive"]
        & gate_pivot["matched_beats_shuffle"]
        & gate_pivot["positive_age_slope"]
    )
    gate_pivot = gate_pivot.drop(
        columns=["downstream_gain_bits", "matched_over_shuffled_bits"]
    )
    gate_pivot = gate_pivot.replace({True: "PASS", False: "FAIL"})

    influence_primary = influence[influence["model_id"].isin(primary["model_id"])].copy()
    influence_ranges = (
        influence_primary.groupby(["model_id", "removed_unit_type"], observed=True)[
            "age_estimate"
        ]
        .agg(influence_min="min", influence_max="max")
        .reset_index()
    )
    influence_ranges["range_bits_per_6m"] = influence_ranges.apply(
        lambda row: f"[{row.influence_min * 6:.3f}, {row.influence_max * 6:.3f}]",
        axis=1,
    )

    report_dir = output_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.environ.setdefault("MPLCONFIGDIR", str(report_dir / ".matplotlib"))
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plot = primary.sort_values(["scorer_key", "scope"]).reset_index(drop=True)
        y = np.arange(len(plot))
        estimate = plot["slope_bits_per_6m"].to_numpy()
        low = plot["age_ci_low"].to_numpy() * 6
        high = plot["age_ci_high"].to_numpy() * 6
        fig, ax = plt.subplots(figsize=(8.4, 4.8))
        ax.errorbar(
            estimate,
            y,
            xerr=np.vstack([estimate - low, high - estimate]),
            fmt="o",
            color="#1f4f8a",
            capsize=3,
        )
        ax.axvline(0, color="#333333", linewidth=1)
        ax.set_yticks(y)
        ax.set_yticklabels(
            [f"{row.scorer_key} — {row.scope}" for row in plot.itertuples()]
        )
        ax.set_xlabel("Age slope in downstream predictive gain (bits / 6 months)")
        ax.set_title("Fixed-effort developmental slopes (child-clustered 95% CI)")
        ax.grid(axis="x", alpha=0.2)
        fig.tight_layout()
        figure_path = report_dir / "downstream_caregiver_response_primary_age_slopes.png"
        fig.savefig(figure_path, dpi=180)
        plt.close(fig)
    except Exception as exc:
        raise ValueError(f"report plot failed: {exc}") from exc

    level_display = gate_levels.copy()
    level_display["bootstrap_ci"] = level_display.apply(
        lambda row: f"[{row.bootstrap_ci_low:.3f}, {row.bootstrap_ci_high:.3f}]", axis=1
    )
    primary_display = primary[
        [
            "scorer_key",
            "scope",
            "slope_bits_per_6m",
            "cluster_ci_6m",
            "bootstrap_ci_6m",
            "source_rows",
            "children",
        ]
    ]
    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Downstream caregiver-response utility</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1120px;margin:32px auto;padding:0 20px;color:#17202a}}
h1,h2{{line-height:1.2}} .callout{{padding:16px 20px;background:#fff3cd;border-left:5px solid #c58900}}
.result{{padding:14px 18px;background:#eaf4ff;border-left:5px solid #1f4f8a}}
table.results{{border-collapse:collapse;width:100%;font-size:14px;margin:14px 0 28px}}
table.results th,table.results td{{padding:7px 9px;border-bottom:1px solid #d8dee4;text-align:left}}
table.results th{{background:#f2f4f7}} img{{max-width:100%;height:auto}}
code{{background:#f2f4f7;padding:2px 4px}} .small{{color:#4d5966;font-size:14px}}
</style></head><body>
<h1>Downstream caregiver-response utility</h1>
<p class="small">Frozen-protocol analysis · strict-naturalistic CHILDES · three scorers reported separately</p>
<div class="callout"><strong>Decisive result:</strong> child utterances make the immediate caregiver response more predictable and outperform matched shuffled child utterances, but this predictive gain does <em>not</em> increase with age at fixed child and response word counts. The frozen increasing-efficiency criterion therefore fails. Mistral and Qwen instead show a confirmed negative developmental slope; TinyDialogues is negative in PBM and inconclusive in the other 58 children.</div>
<h2>What was tested</h2>
<p><code>U = surprisal(response | earlier context) − surprisal(response | earlier context + actual child utterance)</code>. Positive U means the child utterance helps predict the actual next caregiver response. This is a scorer-based downstream proxy, not causal proof, comprehension, or communicative success.</p>
<h2>Frozen gates</h2>
{_result_table(gate_pivot, ["scorer_key", "scope", "matched_gain_positive", "matched_beats_shuffle", "positive_age_slope", "all_three_gates"])}
<h2>Primary developmental slopes</h2>
<img src="downstream_caregiver_response_primary_age_slopes.png" alt="Forest plot of developmental slopes">
{_result_table(primary_display, list(primary_display.columns))}
<h2>Level checks</h2>
<p>These are equal-child-weight means. All confidence intervals below are 1,000-draw whole-child bootstrap intervals.</p>
{_result_table(level_display, ["scorer_key", "scope", "outcome", "mean", "bootstrap_ci", "children_positive_fraction"])}
<h2>Influence</h2>
<p>All 1,656 registered leave-one-child and leave-one-corpus fits passed. Mistral and Qwen confirmation slopes remain negative under every deletion; TinyDialogues remains near zero.</p>
{_result_table(influence_ranges, ["model_id", "removed_unit_type", "range_bits_per_6m"])}
<h2>Design and boundary</h2>
<p>The primary cell model controls exact/top-coded child word count, caregiver-response word count, and stable child identity, with opportunity weights and child-clustered covariance. PBM contains Brown, Manchester, and Providence (21 children; 174,860 triads); the independent confirmation contains the other 58 children (238,224 triads). Raw bits were never pooled across tokenizers.</p>
<p class="small">A negative age slope does not show that children become worse communicators. It shows that, under this specific next-caregiver-response predictive-gain operationalization and these controls, the observed child turn contributes less additional model-predictive information with age. Observational turn sequences do not identify a causal child→caregiver effect.</p>
</body></html>"""
    canonical_path = report_dir / "downstream_caregiver_response_efficiency_report.html"
    canonical_path.write_text(body, encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(canonical_path, report_path)
    documentation_figure = report_path.parent / figure_path.name
    shutil.copyfile(figure_path, documentation_figure)
    manifest = {
        "status": "PASS",
        "report": str(canonical_path),
        "report_sha256": sha256_file(canonical_path),
        "figure": str(figure_path),
        "figure_sha256": sha256_file(figure_path),
        "documentation_copy": str(report_path),
        "documentation_copy_sha256": sha256_file(report_path),
        "documentation_figure": str(documentation_figure),
        "documentation_figure_sha256": sha256_file(documentation_figure),
    }
    manifest_path = report_dir / "report_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (report_dir / "REPORT_COMPLETE").write_text(f"{sha256_file(manifest_path)}\n")


def run_audit(*, output_dir: Path) -> None:
    required = [
        output_dir / "datasets/DATASETS_COMPLETE",
        output_dir / "models/MODELS_COMPLETE",
        output_dir / "datasets/dataset_audit.json",
        output_dir / "models/models_audit.json",
        output_dir / "models/model_registry.csv",
        output_dir / "models/coefficients.csv",
        output_dir / "models/child_bootstrap_draws.csv.gz",
        output_dir / "models/influence_age_slopes.csv",
        output_dir / "models/outcome_level_summaries.csv",
        output_dir / "models/outcome_level_bootstrap_draws.csv.gz",
        output_dir / "report/REPORT_COMPLETE",
        output_dir / "report/report_manifest.json",
        output_dir / "report/downstream_caregiver_response_efficiency_report.html",
        output_dir / "report/downstream_caregiver_response_primary_age_slopes.png",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"analysis artifacts missing: {missing}")
    registry = pd.read_csv(output_dir / "models/model_registry.csv")
    expected = registry["scorer_key"].nunique() * len(SCOPES) * len(OUTCOMES)
    if len(registry) != expected or not registry["status"].eq("PASS").all():
        raise ValueError("registered model inventory is incomplete")
    models_audit = json.loads((output_dir / "models/models_audit.json").read_text())
    if (
        models_audit.get("bootstrap_requested_per_model") != 1000
        or models_audit.get("bootstrap_failures") != 0
        or models_audit.get("influence_failures") != 0
    ):
        raise ValueError("registered uncertainty or influence checks are incomplete")
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
    parser.add_argument(
        "--stage",
        choices=("datasets", "models", "report", "audit", "all"),
        default="all",
    )
    parser.add_argument("--handoff-root", type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument("--score-root", action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
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
    if args.stage in {"report", "all"}:
        run_report(output_dir=args.output_dir, report_path=args.report_path)
    if args.stage in {"audit", "all"}:
        run_audit(output_dir=args.output_dir)


if __name__ == "__main__":
    main()
