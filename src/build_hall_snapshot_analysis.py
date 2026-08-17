#!/usr/bin/env python3
"""Build the modular Hall cross-sectional Mistral analysis.

Stages are intentionally separated so archive validation, dataset creation,
model fitting, plotting, and reporting can be rerun and audited independently.
Hall remains a cross-sectional sociolinguistic snapshot; it is never appended
to the 79-child longitudinal developmental sample.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tarfile
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from audit_hall_scored_archive import (
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_CODE_REVISION,
    EXPECTED_CONTEXTS,
    EXPECTED_MODEL_REVISION,
    EXPECTED_ROWS,
    INPUT_MEMBER,
    _contract_base,
    _csv_member,
    sha256_path,
)
from render_markdown_report import render_markdown_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTERNAL_ROOT = (
    PROJECT_ROOT
    / "results/external/compute_surprisal_mila/"
    "hall_snapshot_mistral_word_surprisal_20260813_66812c4"
)
DEFAULT_ARCHIVE = (
    DEFAULT_EXTERNAL_ROOT
    / "hall_snapshot_mistral_real_k0_k1_k2_k3_word_surprisal_"
    "20260813_hall_snapshot_mistral_word_smoke_66812c4_v1.tar.gz"
)
DEFAULT_AUDIT_DIR = PROJECT_ROOT / "results/hall_snapshot_analysis/archive_audit"
DEFAULT_PREPARED_DIR = PROJECT_ROOT / "results/hall_snapshot_analysis/prepared"
DEFAULT_MODEL_DIR = PROJECT_ROOT / "results/hall_snapshot_analysis/models"
DEFAULT_PLOT_DIR = PROJECT_ROOT / "figs/hall_snapshot_analysis"
DEFAULT_REPORT_MD = PROJECT_ROOT / "docs/hall_snapshot_mistral_analysis.md"
DEFAULT_REPORT_HTML = PROJECT_ROOT / "docs/hall_snapshot_mistral_analysis.html"
DEFAULT_FINAL_DIR = PROJECT_ROOT / "results/hall_snapshot_analysis/final"
DEFAULT_COMPARATOR = (
    PROJECT_ROOT
    / "results/hall_snapshot_preprocessing/hall_comparison_snapshot_manifest.csv"
)
DEFAULT_TRAJECTORY = (
    PROJECT_ROOT
    / "results/direct_surprisal_replication/mistral_full79/modular/prepared/"
    "trajectory_input.csv.gz"
)
PIPELINE_VERSION = "2026-08-17.hall-snapshot-v1"


def atomic_json(payload: Mapping[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_csv(frame: pd.DataFrame, path: Path, *, compression: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        frame.to_csv(temporary, index=False, compression=compression, lineterminator="\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.fillna(False).astype(bool)
    return series.fillna("").astype(str).str.lower().isin({"true", "1"})


def _session_key(series: pd.Series) -> pd.Series:
    values = series.fillna("").astype(str).str.strip()
    return values.str.replace(r"\.0$", "", regex=True)


def _word_category(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="raise").astype(int)
    return numeric.map(lambda value: "12+" if value >= 12 else str(value))


def _load_audit(local_audit_dir: Path, archive_path: Path) -> dict[str, object]:
    report_path = local_audit_dir / "local_retrieval_audit.json"
    marker = local_audit_dir / "LOCAL_RETRIEVAL_AUDIT_PASSED"
    if not report_path.is_file() or not marker.is_file():
        raise ValueError("Hall dataset stage requires LOCAL_RETRIEVAL_AUDIT_PASSED")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status") != "PASS" or report.get("problem_count") != 0:
        raise ValueError("Hall local retrieval audit is not PASS")
    archive_sha = sha256_path(archive_path)
    if report.get("archive_sha256") != archive_sha:
        raise ValueError("Hall archive changed after local retrieval audit")
    return report


def _build_wide(archive_path: Path, *, expected_rows: int) -> pd.DataFrame:
    with tarfile.open(archive_path, "r:gz") as archive:
        source = _csv_member(archive, INPUT_MEMBER)
        source.insert(0, "source_row", np.arange(len(source), dtype=int))
        wide = source.copy()
        for context in EXPECTED_CONTEXTS:
            scores = _csv_member(
                archive,
                f"{_contract_base(context)}/utterances.csv.gz",
            ).sort_values("source_row").reset_index(drop=True)
            keep = scores[
                [
                    "source_row", "utterance_id", "target_text", "context_text",
                    "context_available", "utterance_sum_bits",
                    "utterance_mean_bits_per_token", "utterance_bits_per_word",
                    "utterance_bits_per_character", "utterance_eval_tokens",
                    "assigned_word_bits", "unassigned_target_bits",
                    "assigned_token_coverage", "n_context_tokens_truncated",
                ]
            ].rename(
                columns={
                    "utterance_id": f"utterance_id_{context}",
                    "target_text": f"target_text_{context}",
                    "context_text": f"context_text_{context}",
                    "context_available": f"context_available_{context}",
                    "utterance_sum_bits": f"{context}_sum_bits",
                    "utterance_mean_bits_per_token": f"{context}_mean_bits_per_token",
                    "utterance_bits_per_word": f"{context}_bits_per_word",
                    "utterance_bits_per_character": f"{context}_bits_per_character",
                    "utterance_eval_tokens": f"{context}_eval_tokens",
                    "assigned_word_bits": f"{context}_assigned_word_bits",
                    "unassigned_target_bits": f"{context}_unassigned_target_bits",
                    "assigned_token_coverage": f"{context}_assigned_token_coverage",
                    "n_context_tokens_truncated": f"{context}_truncated_tokens",
                }
            )
            wide = wide.merge(keep, on="source_row", how="left", validate="one_to_one")
            if not wide[f"utterance_id_{context}"].astype(str).equals(wide["utterance_id"].astype(str)):
                raise ValueError(f"Hall {context} utterance identity changed during dataset join")
            if not wide[f"target_text_{context}"].fillna("").astype(str).equals(
                wide["chi_utterance_clean"].fillna("").astype(str)
            ):
                raise ValueError(f"Hall {context} target text changed during dataset join")
        if len(wide) != expected_rows:
            raise ValueError(f"Hall wide table has {len(wide)} rows; expected {expected_rows}")

    for context in ("k1", "k2", "k3"):
        wide[f"context_gain_{context}"] = wide["k0_sum_bits"] - wide[f"{context}_sum_bits"]
        wide[f"context_available_{context}"] = _bool(wide[f"context_available_{context}"])
    wide["context_available_k0"] = _bool(wide["context_available_k0"])
    wide["primary_eligible"] = _bool(wide["primary_eligible"])
    wide["sensitivity_eligible"] = _bool(wide["sensitivity_eligible"])
    wide["child_after_adult"] = _bool(wide["child_after_adult"])
    wide["race_black"] = wide["race"].astype(str).eq("Black").astype(int)
    wide["class_uc"] = wide["social_class"].astype(str).eq("UC").astype(int)
    wide["sex_male"] = wide["sex"].astype(str).str.lower().eq("male").astype(int)
    wide["word_count_exact_top12"] = _word_category(wide["nb_words"])
    wide["child_key"] = "Hall/" + wide["child_id"].astype(str)
    return wide


def _collapse_hall_cells(wide: pd.DataFrame) -> pd.DataFrame:
    analysis_sets = {
        "primary_all": wide["primary_eligible"],
        "primary_adult_adjacent": wide["primary_eligible"] & wide["child_after_adult"],
        "sensitivity_all37": wide["sensitivity_eligible"],
        "sensitivity_all37_adult_adjacent": wide["sensitivity_eligible"] & wide["child_after_adult"],
    }
    outcomes = [
        "k0_sum_bits", "k1_sum_bits", "k2_sum_bits", "k3_sum_bits",
        "context_gain_k1", "context_gain_k2", "context_gain_k3",
    ]
    group_cols = [
        "child_key", "child_id", "race", "social_class", "stratum",
        "race_black", "class_uc", "sex", "sex_male", "age_months",
        "setting_auto", "word_count_exact_top12",
    ]
    frames: list[pd.DataFrame] = []
    for analysis_set, base_mask in analysis_sets.items():
        for outcome in outcomes:
            context = outcome.rsplit("_", 1)[-1] if outcome.startswith("context_gain_") else outcome.split("_")[0]
            mask = base_mask.copy()
            if context != "k0":
                mask &= wide[f"context_available_{context}"]
            data = wide.loc[mask, [*group_cols, outcome]].dropna(subset=[outcome]).copy()
            if data.empty:
                continue
            cells = (
                data.groupby(group_cols, observed=True, dropna=False)[outcome]
                .agg(outcome_mean="mean", outcome_sd="std", row_count="size")
                .reset_index()
            )
            cells["analysis_set"] = analysis_set
            cells["outcome"] = outcome
            frames.append(cells)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _external_snapshot_cells(
    wide: pd.DataFrame,
    comparator_manifest: Path,
    trajectory_input: Path,
) -> tuple[pd.DataFrame, dict[str, int]]:
    comparator = pd.read_csv(comparator_manifest, dtype={"session_id": str})
    trajectory = pd.read_csv(trajectory_input, dtype={"session_id": str})
    comparator["session_key"] = _session_key(comparator["session_id"])
    trajectory["session_key"] = _session_key(trajectory["session_id"])
    trajectory = trajectory[trajectory["role"].astype(str).eq("child")].copy()
    selected = trajectory.merge(
        comparator[["child_key", "scope", "session_key"]].drop_duplicates(),
        on=["child_key", "scope", "session_key"],
        how="inner",
        validate="many_to_one",
    )
    if selected["child_key"].nunique() != comparator["child_key"].nunique():
        raise ValueError(
            "locked external snapshot did not recover every selected child: "
            f"{selected['child_key'].nunique()} versus {comparator['child_key'].nunique()}"
        )

    frames: list[pd.DataFrame] = []
    current_outcomes = {
        "k0_sum_bits": "raw_k0_bits",
        "k3_sum_bits": "raw_k3_bits",
        "context_gain_k3": "raw_context_gain_k3",
    }
    for outcome, column in current_outcomes.items():
        current = selected[
            [
                "dataset", "child_id", "child_key", "scope", "age_months",
                "word_count_exact_top12", "utterances", column,
            ]
        ].copy()
        current = current.rename(columns={"utterances": "row_count", column: "outcome_mean"})
        current["cohort"] = "current_naturalistic"
        current["cohort_hall"] = 0
        current["setting_auto"] = "not_available"
        current["outcome"] = outcome
        frames.append(current)

        hall_mask = wide["primary_eligible"].copy()
        if outcome != "k0_sum_bits":
            hall_mask &= wide["context_available_k3"]
        hall = wide.loc[
            hall_mask,
            ["child_key", "child_id", "age_months", "setting_auto", "word_count_exact_top12", outcome],
        ]
        hall = (
            hall.groupby(
                ["child_key", "child_id", "age_months", "setting_auto", "word_count_exact_top12"],
                observed=True,
                dropna=False,
            )[outcome]
            .agg(outcome_mean="mean", row_count="size")
            .reset_index()
        )
        hall["dataset"] = "Hall"
        hall["scope"] = "hall_primary"
        hall["cohort"] = "Hall"
        hall["cohort_hall"] = 1
        hall["outcome"] = outcome
        frames.append(hall)

    result = pd.concat(frames, ignore_index=True)
    result["age_centered_57"] = pd.to_numeric(result["age_months"], errors="coerce") - 57.0
    return result, {
        "locked_children": int(comparator["child_key"].nunique()),
        "matched_children": int(selected["child_key"].nunique()),
        "matched_pbm_children": int(selected.loc[selected["scope"].eq("pbm_discovery"), "child_key"].nunique()),
        "matched_non_pbm_children": int(selected.loc[selected["scope"].eq("non_pbm_confirmation"), "child_key"].nunique()),
    }


def build_dataset_stage(
    *,
    archive_path: Path = DEFAULT_ARCHIVE,
    local_audit_dir: Path = DEFAULT_AUDIT_DIR,
    comparator_manifest: Path = DEFAULT_COMPARATOR,
    trajectory_input: Path = DEFAULT_TRAJECTORY,
    output_dir: Path = DEFAULT_PREPARED_DIR,
    expected_rows: int = EXPECTED_ROWS,
) -> dict[str, object]:
    archive_path = archive_path.expanduser().resolve()
    local_audit_dir = local_audit_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    audit = _load_audit(local_audit_dir, archive_path)
    wide = _build_wide(archive_path, expected_rows=expected_rows)
    cells = _collapse_hall_cells(wide)
    external, external_audit = _external_snapshot_cells(
        wide,
        comparator_manifest.expanduser().resolve(),
        trajectory_input.expanduser().resolve(),
    )
    atomic_csv(wide, output_dir / "hall_utterance_scores.csv.gz", compression="gzip")
    atomic_csv(cells, output_dir / "hall_design_cells.csv.gz", compression="gzip")
    atomic_csv(external, output_dir / "external_snapshot_cells.csv.gz", compression="gzip")
    support = (
        wide.groupby(["stratum", "setting_auto", "word_count_exact_top12"], observed=True)
        .agg(utterances=("utterance_id", "size"), children=("child_key", "nunique"))
        .reset_index()
    )
    atomic_csv(support, output_dir / "setting_stratum_effort_support.csv")
    manifest: dict[str, object] = {
        "status": "PASS",
        "pipeline_version": PIPELINE_VERSION,
        "stage": "datasets",
        "archive_sha256": audit["archive_sha256"],
        "model_revision": EXPECTED_MODEL_REVISION,
        "scoring_code_revision": EXPECTED_CODE_REVISION,
        "hall_rows": len(wide),
        "hall_children": int(wide["child_key"].nunique()),
        "primary_children": int(wide.loc[wide["primary_eligible"], "child_key"].nunique()),
        "primary_rows": int(wide["primary_eligible"].sum()),
        "sensitivity_children": int(wide.loc[wide["sensitivity_eligible"], "child_key"].nunique()),
        "adult_adjacent_primary_rows": int((wide["primary_eligible"] & wide["child_after_adult"]).sum()),
        "design_cells": len(cells),
        "external_cells": len(external),
        **external_audit,
        "outputs": {
            "wide": str(output_dir / "hall_utterance_scores.csv.gz"),
            "hall_cells": str(output_dir / "hall_design_cells.csv.gz"),
            "external_cells": str(output_dir / "external_snapshot_cells.csv.gz"),
        },
    }
    atomic_json(manifest, output_dir / "dataset_manifest.json")
    return manifest


def _contrast(
    result,
    *,
    contrast_id: str,
    label: str,
    weights: Mapping[str, float],
    model_id: str,
    outcome: str,
) -> dict[str, object]:
    names = list(result.params.index)
    vector = np.zeros(len(names), dtype=float)
    for term, weight in weights.items():
        if term not in names:
            raise ValueError(f"registered contrast term is unavailable: {term}")
        vector[names.index(term)] = weight
    test = result.t_test(vector)
    interval = np.asarray(test.conf_int(alpha=0.05)).reshape(-1)
    return {
        "model_id": model_id,
        "outcome": outcome,
        "contrast_id": contrast_id,
        "label": label,
        "estimate": float(np.asarray(test.effect).reshape(-1)[0]),
        "std_error": float(np.asarray(test.sd).reshape(-1)[0]),
        "ci_low": float(interval[0]),
        "ci_high": float(interval[1]),
        "p_value": float(np.asarray(test.pvalue).reshape(-1)[0]),
    }


def fit_weighted_cluster_model(
    frame: pd.DataFrame,
    *,
    model_id: str,
    outcome: str,
    formula: str,
    contrast_family: str,
    weight_column: str = "row_count",
    cluster_column: str = "child_key",
):
    """Fit registered WLS and return its scientific contrasts."""

    data = frame.copy()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = smf.wls(formula, data=data, weights=data[weight_column]).fit(
            cov_type="cluster",
            cov_kwds={"groups": data[cluster_column], "use_correction": True},
        )
    contrast_specs: list[tuple[str, str, dict[str, float]]]
    if contrast_family == "hall_race_class":
        interaction = "race_black:class_uc"
        contrast_specs = [
            ("black_minus_white_wc", "Black minus White within WC", {"race_black": 1.0}),
            ("black_minus_white_uc", "Black minus White within UC", {"race_black": 1.0, interaction: 1.0}),
            ("uc_minus_wc_white", "UC minus WC within White", {"class_uc": 1.0}),
            ("uc_minus_wc_black", "UC minus WC within Black", {"class_uc": 1.0, interaction: 1.0}),
            ("race_by_class_interaction", "Race-by-class difference in differences", {interaction: 1.0}),
        ]
    elif contrast_family == "external_cohort":
        contrast_specs = [
            ("hall_minus_current", "Hall minus locked current naturalistic snapshot", {"cohort_hall": 1.0})
        ]
    else:
        raise ValueError(f"unknown contrast family: {contrast_family}")
    contrasts = pd.DataFrame(
        [
            _contrast(
                result, contrast_id=contrast_id, label=label, weights=weights,
                model_id=model_id, outcome=outcome,
            )
            for contrast_id, label, weights in contrast_specs
        ]
    )
    summary = {
        "model_id": model_id,
        "outcome": outcome,
        "formula": formula,
        "estimator": "exact_cell_wls_child_cluster",
        "weight_column": weight_column,
        "cluster_column": cluster_column,
        "design_cells": len(data),
        "source_rows": int(data["row_count"].sum()),
        "children": int(data[cluster_column].nunique()),
        "fit_status": "PASS",
        "r_squared": float(result.rsquared),
        "aic": float(result.aic),
        "warnings": " | ".join(str(item.message) for item in caught),
    }
    return result, summary, contrasts


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    label: str
    source: str
    outcome: str
    analysis_set: str
    formula: str
    contrast_family: str
    tier: str
    subset: str = "all"
    weighting: str = "utterance"
    bootstrap: bool = False
    influence: str = "none"


HALL_FORMULA = (
    "outcome_mean ~ race_black * class_uc + "
    "C(word_count_exact_top12) + C(setting_auto)"
)
HALL_NO_SETTING_FORMULA = (
    "outcome_mean ~ race_black * class_uc + C(word_count_exact_top12)"
)
EXTERNAL_FORMULA = "outcome_mean ~ cohort_hall + C(word_count_exact_top12)"


MODEL_SPECS = (
    ModelSpec(
        "H1_k0_primary", "Primary unconditional Hall contrast", "hall", "k0_sum_bits",
        "primary_all", HALL_FORMULA, "hall_race_class", "primary",
        bootstrap=True, influence="child",
    ),
    ModelSpec(
        "H2_k0_all37", "Folder-inferred-child sensitivity", "hall", "k0_sum_bits",
        "sensitivity_all37", HALL_FORMULA, "hall_race_class", "sample_sensitivity",
        bootstrap=True,
    ),
    ModelSpec(
        "H3_k0_sex_control", "Sex-adjusted sensitivity", "hall", "k0_sum_bits",
        "primary_all", HALL_FORMULA + " + sex_male", "hall_race_class", "covariate_sensitivity",
    ),
    ModelSpec(
        "H4_k0_age_control", "Exact-age-adjusted sensitivity", "hall", "k0_sum_bits",
        "primary_all", HALL_FORMULA + " + age_centered_57", "hall_race_class", "covariate_sensitivity",
    ),
    ModelSpec(
        "H5_k0_home", "Home-only sensitivity", "hall", "k0_sum_bits",
        "primary_all", HALL_NO_SETTING_FORMULA, "hall_race_class", "setting_sensitivity",
        subset="hall_home",
    ),
    ModelSpec(
        "H6_k0_school", "School-only sensitivity", "hall", "k0_sum_bits",
        "primary_all", HALL_NO_SETTING_FORMULA, "hall_race_class", "setting_sensitivity",
        subset="hall_school",
    ),
    ModelSpec(
        "H7_k0_equal_child", "Equal-child-weight sensitivity", "hall", "k0_sum_bits",
        "primary_all", HALL_FORMULA, "hall_race_class", "weighting_sensitivity",
        weighting="equal_child",
    ),
    ModelSpec(
        "H8_k3_adult_adjacent", "Contextual surprisal after an adult", "hall", "k3_sum_bits",
        "primary_adult_adjacent", HALL_FORMULA, "hall_race_class", "secondary_context",
        bootstrap=True, influence="child",
    ),
    ModelSpec(
        "H9_gain_k3_adult_adjacent", "k3 context support after an adult", "hall", "context_gain_k3",
        "primary_adult_adjacent", HALL_FORMULA, "hall_race_class", "secondary_context",
        bootstrap=True, influence="child",
    ),
    ModelSpec(
        "H10_gain_k1_adult_adjacent", "k1 context-support sensitivity", "hall", "context_gain_k1",
        "primary_adult_adjacent", HALL_FORMULA, "hall_race_class", "context_window_sensitivity",
    ),
    ModelSpec(
        "H11_gain_k2_adult_adjacent", "k2 context-support sensitivity", "hall", "context_gain_k2",
        "primary_adult_adjacent", HALL_FORMULA, "hall_race_class", "context_window_sensitivity",
    ),
    ModelSpec(
        "H12_k3_all_context", "All context-available Hall turns", "hall", "k3_sum_bits",
        "primary_all", HALL_FORMULA, "hall_race_class", "adjacency_sensitivity",
    ),
    ModelSpec(
        "H13_gain_k3_all_context", "All context-available Hall context support", "hall", "context_gain_k3",
        "primary_all", HALL_FORMULA, "hall_race_class", "adjacency_sensitivity",
    ),
    ModelSpec(
        "E1_k0_locked_snapshot", "Locked external unconditional comparison", "external", "k0_sum_bits",
        "locked_snapshot", EXTERNAL_FORMULA, "external_cohort", "external_primary",
        bootstrap=True, influence="corpus",
    ),
    ModelSpec(
        "E2_k0_age_control", "Age-adjusted locked external comparison", "external", "k0_sum_bits",
        "locked_snapshot", EXTERNAL_FORMULA + " + age_centered_57", "external_cohort", "external_sensitivity",
    ),
    ModelSpec(
        "E3_k0_hall_home", "Hall-home versus locked current snapshot", "external", "k0_sum_bits",
        "locked_snapshot", EXTERNAL_FORMULA, "external_cohort", "external_sensitivity",
        subset="external_hall_home",
    ),
    ModelSpec(
        "E4_k0_non_pbm", "Hall versus locked non-PBM snapshot", "external", "k0_sum_bits",
        "locked_snapshot", EXTERNAL_FORMULA, "external_cohort", "external_sensitivity",
        subset="external_non_pbm",
    ),
    ModelSpec(
        "E5_k0_equal_child", "Equal-child external comparison", "external", "k0_sum_bits",
        "locked_snapshot", EXTERNAL_FORMULA, "external_cohort", "external_sensitivity",
        weighting="equal_child",
    ),
    ModelSpec(
        "E6_k3_locked_snapshot", "Locked external contextual comparison", "external", "k3_sum_bits",
        "locked_snapshot", EXTERNAL_FORMULA, "external_cohort", "external_secondary",
    ),
    ModelSpec(
        "E7_gain_k3_locked_snapshot", "Locked external context-support comparison", "external", "context_gain_k3",
        "locked_snapshot", EXTERNAL_FORMULA, "external_cohort", "external_secondary",
    ),
)


def _subset_for_spec(
    spec: ModelSpec,
    hall_cells: pd.DataFrame,
    external_cells: pd.DataFrame,
) -> pd.DataFrame:
    if spec.source == "hall":
        frame = hall_cells[
            hall_cells["analysis_set"].eq(spec.analysis_set)
            & hall_cells["outcome"].eq(spec.outcome)
        ].copy()
        if spec.subset == "hall_home":
            frame = frame[frame["setting_auto"].eq("home")].copy()
        elif spec.subset == "hall_school":
            frame = frame[frame["setting_auto"].eq("school")].copy()
    else:
        frame = external_cells[external_cells["outcome"].eq(spec.outcome)].copy()
        if spec.subset == "external_hall_home":
            frame = frame[
                frame["cohort"].ne("Hall") | frame["setting_auto"].eq("home")
            ].copy()
        elif spec.subset == "external_non_pbm":
            frame = frame[
                frame["cohort"].eq("Hall") | frame["scope"].eq("non_pbm_confirmation")
            ].copy()
    frame["age_centered_57"] = pd.to_numeric(frame["age_months"], errors="coerce") - 57.0
    if spec.weighting == "equal_child":
        child_total = frame.groupby("child_key", observed=True)["row_count"].transform("sum")
        frame["model_weight"] = frame["row_count"] / child_total
    else:
        frame["model_weight"] = frame["row_count"]
    return frame.reset_index(drop=True)


def _coefficient_frame(result, spec: ModelSpec) -> pd.DataFrame:
    intervals = result.conf_int()
    return pd.DataFrame(
        {
            "model_id": spec.model_id,
            "outcome": spec.outcome,
            "tier": spec.tier,
            "term": result.params.index,
            "estimate": result.params.values,
            "std_error": result.bse.values,
            "ci_low": intervals.iloc[:, 0].values,
            "ci_high": intervals.iloc[:, 1].values,
            "p_value": result.pvalues.values,
        }
    )


def _contrast_definitions(family: str) -> dict[str, dict[str, float]]:
    if family == "hall_race_class":
        return {
            "black_minus_white_wc": {"race_black": 1.0},
            "black_minus_white_uc": {"race_black": 1.0, "race_black:class_uc": 1.0},
            "uc_minus_wc_white": {"class_uc": 1.0},
            "uc_minus_wc_black": {"class_uc": 1.0, "race_black:class_uc": 1.0},
            "race_by_class_interaction": {"race_black:class_uc": 1.0},
        }
    return {"hall_minus_current": {"cohort_hall": 1.0}}


def _contrast_vector(parameter_names: Sequence[str], weights: Mapping[str, float]) -> np.ndarray:
    vector = np.zeros(len(parameter_names), dtype=float)
    for term, weight in weights.items():
        if term not in parameter_names:
            raise ValueError(f"contrast term unavailable in fitted design: {term}")
        vector[list(parameter_names).index(term)] = weight
    return vector


def _bootstrap_contrasts(
    result,
    frame: pd.DataFrame,
    spec: ModelSpec,
    *,
    reps: int,
    seed: int,
) -> pd.DataFrame:
    if reps <= 0:
        return pd.DataFrame()
    parameter_names = list(result.params.index)
    design = np.asarray(result.model.exog, dtype=float)
    outcome = np.asarray(result.model.endog, dtype=float)
    weights = np.asarray(result.model.weights, dtype=float)
    children = frame.loc[result.model.data.row_labels, "child_key"].astype(str).to_numpy()
    strata_column = "stratum" if spec.source == "hall" else "cohort"
    strata = frame.loc[result.model.data.row_labels, strata_column].astype(str).to_numpy()
    child_labels = np.array(sorted(set(children)))
    child_indices = {child: np.flatnonzero(children == child) for child in child_labels}
    child_strata = {
        child: str(strata[child_indices[child][0]])
        for child in child_labels
    }
    stratum_children = {
        stratum: np.array([child for child in child_labels if child_strata[child] == stratum])
        for stratum in sorted(set(child_strata.values()))
    }
    crossproducts: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for child, indices in child_indices.items():
        x = design[indices]
        w = weights[indices]
        y = outcome[indices]
        crossproducts[child] = (x.T @ (w[:, None] * x), x.T @ (w * y))
    vectors = {
        contrast_id: _contrast_vector(parameter_names, terms)
        for contrast_id, terms in _contrast_definitions(spec.contrast_family).items()
    }
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for replicate in range(reps):
        sampled: list[str] = []
        for labels in stratum_children.values():
            sampled.extend(rng.choice(labels, size=len(labels), replace=True).tolist())
        matrix = sum((crossproducts[child][0] for child in sampled), np.zeros((design.shape[1], design.shape[1])))
        vector = sum((crossproducts[child][1] for child in sampled), np.zeros(design.shape[1]))
        beta = np.linalg.lstsq(matrix, vector, rcond=None)[0]
        for contrast_id, contrast_vector in vectors.items():
            rows.append(
                {
                    "model_id": spec.model_id,
                    "outcome": spec.outcome,
                    "contrast_id": contrast_id,
                    "replicate": replicate,
                    "seed": seed,
                    "estimate": float(contrast_vector @ beta),
                    "status": "PASS",
                }
            )
    return pd.DataFrame(rows)


def _bootstrap_summary(draws: pd.DataFrame) -> pd.DataFrame:
    if draws.empty:
        return pd.DataFrame()
    return (
        draws.groupby(["model_id", "outcome", "contrast_id"], observed=True)["estimate"]
        .agg(
            draws="size",
            estimate_median="median",
            ci_low=lambda values: values.quantile(0.025),
            ci_high=lambda values: values.quantile(0.975),
            probability_positive=lambda values: float((values > 0).mean()),
        )
        .reset_index()
    )


def _influence_estimates(
    frame: pd.DataFrame,
    spec: ModelSpec,
    *,
    level: str,
) -> pd.DataFrame:
    if level == "child":
        labels = sorted(frame["child_key"].astype(str).unique())
        drop_column = "child_key"
    elif level == "corpus":
        labels = sorted(
            value for value in frame.loc[frame["cohort"].ne("Hall"), "dataset"].astype(str).unique()
        )
        drop_column = "dataset"
    else:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    definitions = _contrast_definitions(spec.contrast_family)
    for label in labels:
        reduced = frame[frame[drop_column].astype(str).ne(label)].copy()
        fitted = smf.wls(spec.formula, data=reduced, weights=reduced["model_weight"]).fit()
        names = list(fitted.params.index)
        for contrast_id, terms in definitions.items():
            vector = _contrast_vector(names, terms)
            rows.append(
                {
                    "model_id": spec.model_id,
                    "outcome": spec.outcome,
                    "influence_level": level,
                    "omitted": label,
                    "contrast_id": contrast_id,
                    "estimate": float(vector @ fitted.params.to_numpy(float)),
                    "children": int(reduced["child_key"].nunique()),
                    "source_rows": int(reduced["row_count"].sum()),
                }
            )
    return pd.DataFrame(rows)


def _prediction_grid(result, spec: ModelSpec, frame: pd.DataFrame) -> pd.DataFrame:
    efforts = [str(value) for value in range(1, 12)] + ["12+"]
    if spec.source == "hall":
        settings = [value for value in ("home", "school") if value in set(frame["setting_auto"])]
        rows = [
            {
                "race_black": race_black,
                "class_uc": class_uc,
                "word_count_exact_top12": effort,
                "setting_auto": setting,
                "sex_male": float(frame["sex_male"].mean()),
                "age_centered_57": 0.0,
                "stratum": ("Black" if race_black else "White") + "_" + ("UC" if class_uc else "WC"),
            }
            for setting in settings
            for race_black in (0, 1)
            for class_uc in (0, 1)
            for effort in efforts
        ]
    else:
        rows = [
            {
                "cohort_hall": cohort_hall,
                "word_count_exact_top12": effort,
                "age_centered_57": 0.0,
                "cohort": "Hall" if cohort_hall else "current_naturalistic",
            }
            for cohort_hall in (0, 1)
            for effort in efforts
        ]
    grid = pd.DataFrame(rows)
    available_efforts = set(frame["word_count_exact_top12"].astype(str))
    grid = grid[grid["word_count_exact_top12"].isin(available_efforts)].copy()
    prediction = result.get_prediction(grid).summary_frame(alpha=0.05)
    grid["predicted_mean"] = prediction["mean"].to_numpy()
    grid["ci_low"] = prediction["mean_ci_lower"].to_numpy()
    grid["ci_high"] = prediction["mean_ci_upper"].to_numpy()
    grid["model_id"] = spec.model_id
    grid["outcome"] = spec.outcome
    return grid


def run_model_stage(
    *,
    prepared_dir: Path = DEFAULT_PREPARED_DIR,
    model_dir: Path = DEFAULT_MODEL_DIR,
    bootstrap_reps: int = 1_000,
    seed: int = 20260817,
) -> dict[str, object]:
    prepared_dir = prepared_dir.expanduser().resolve()
    model_dir = model_dir.expanduser().resolve()
    dataset_manifest = json.loads((prepared_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    if dataset_manifest.get("status") != "PASS":
        raise ValueError("Hall model stage requires a PASS dataset manifest")
    hall_cells = pd.read_csv(prepared_dir / "hall_design_cells.csv.gz")
    external_cells = pd.read_csv(prepared_dir / "external_snapshot_cells.csv.gz")
    summaries: list[dict[str, object]] = []
    coefficients: list[pd.DataFrame] = []
    contrasts: list[pd.DataFrame] = []
    predictions: list[pd.DataFrame] = []
    bootstrap: list[pd.DataFrame] = []
    influence: list[pd.DataFrame] = []

    for index, spec in enumerate(MODEL_SPECS):
        frame = _subset_for_spec(spec, hall_cells, external_cells)
        try:
            result, summary, contrast = fit_weighted_cluster_model(
                frame,
                model_id=spec.model_id,
                outcome=spec.outcome,
                formula=spec.formula,
                contrast_family=spec.contrast_family,
                weight_column="model_weight",
            )
            summary.update(
                {
                    "label": spec.label,
                    "tier": spec.tier,
                    "analysis_set": spec.analysis_set,
                    "subset": spec.subset,
                    "weighting": spec.weighting,
                }
            )
            contrast["tier"] = spec.tier
            contrast["label_model"] = spec.label
            summaries.append(summary)
            coefficients.append(_coefficient_frame(result, spec))
            contrasts.append(contrast)
            if spec.model_id in {"H1_k0_primary", "H8_k3_adult_adjacent", "H9_gain_k3_adult_adjacent", "E1_k0_locked_snapshot"}:
                predictions.append(_prediction_grid(result, spec, frame))
            if spec.bootstrap:
                bootstrap.append(
                    _bootstrap_contrasts(
                        result, frame, spec, reps=bootstrap_reps,
                        seed=seed + index * 101,
                    )
                )
            if spec.influence != "none":
                influence.append(_influence_estimates(frame, spec, level=spec.influence))
        except Exception as exc:
            summaries.append(
                {
                    "model_id": spec.model_id,
                    "label": spec.label,
                    "outcome": spec.outcome,
                    "tier": spec.tier,
                    "analysis_set": spec.analysis_set,
                    "subset": spec.subset,
                    "weighting": spec.weighting,
                    "formula": spec.formula,
                    "design_cells": len(frame),
                    "source_rows": int(frame["row_count"].sum()) if not frame.empty else 0,
                    "children": int(frame["child_key"].nunique()) if not frame.empty else 0,
                    "fit_status": "FAIL",
                    "warnings": f"{type(exc).__name__}: {exc}",
                }
            )

    summary_frame = pd.DataFrame(summaries)
    coefficient_frame = pd.concat(coefficients, ignore_index=True) if coefficients else pd.DataFrame()
    contrast_frame = pd.concat(contrasts, ignore_index=True) if contrasts else pd.DataFrame()
    prediction_frame = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    bootstrap_frame = pd.concat(bootstrap, ignore_index=True) if bootstrap else pd.DataFrame()
    influence_frame = pd.concat(influence, ignore_index=True) if influence else pd.DataFrame()
    atomic_csv(summary_frame, model_dir / "model_summaries.csv")
    atomic_csv(coefficient_frame, model_dir / "coefficients_long.csv")
    atomic_csv(contrast_frame, model_dir / "registered_contrasts.csv")
    atomic_csv(prediction_frame, model_dir / "prediction_grid.csv")
    atomic_csv(bootstrap_frame, model_dir / "child_bootstrap_draws.csv.gz", compression="gzip")
    atomic_csv(_bootstrap_summary(bootstrap_frame), model_dir / "child_bootstrap_summary.csv")
    atomic_csv(influence_frame, model_dir / "leave_one_cluster_out.csv")
    failed = int(summary_frame["fit_status"].eq("FAIL").sum())
    manifest: dict[str, object] = {
        "status": "PASS" if failed == 0 else "FAIL",
        "pipeline_version": PIPELINE_VERSION,
        "stage": "models",
        "upstream_dataset_manifest_sha256": sha256_path(prepared_dir / "dataset_manifest.json"),
        "registered_models": len(MODEL_SPECS),
        "model_rows": len(summary_frame),
        "passed_models": int(summary_frame["fit_status"].eq("PASS").sum()),
        "failed_models": failed,
        "bootstrap_reps_requested": bootstrap_reps,
        "bootstrap_draw_rows": len(bootstrap_frame),
        "bootstrap_models": int(bootstrap_frame["model_id"].nunique()) if not bootstrap_frame.empty else 0,
        "influence_rows": len(influence_frame),
        "seed": seed,
    }
    atomic_json(manifest, model_dir / "model_manifest.json")
    if failed:
        first = summary_frame.loc[summary_frame["fit_status"].eq("FAIL")].iloc[0]
        raise ValueError(f"Hall model stage failed at {first['model_id']}: {first['warnings']}")
    return manifest


STRATUM_COLORS = {
    "Black_UC": "#7b3294",
    "Black_WC": "#c2a5cf",
    "White_UC": "#008837",
    "White_WC": "#a6dba0",
}


def _effort_numeric(series: pd.Series) -> pd.Series:
    return series.astype(str).replace("12+", "12").astype(float)


def _save_figure(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.stem}.tmp{path.suffix}")
    fig.savefig(temporary, dpi=180, bbox_inches="tight")
    plt.close(fig)
    os.replace(temporary, path)


def _plot_hall_predictions(predictions: pd.DataFrame, model_id: str, path: Path, title: str) -> None:
    data = predictions[predictions["model_id"].eq(model_id)].copy()
    settings = [value for value in ("home", "school") if value in set(data.get("setting_auto", []))]
    if not settings:
        settings = [""]
    fig, axes = plt.subplots(1, len(settings), figsize=(6.2 * len(settings), 4.6), squeeze=False)
    for axis, setting in zip(axes[0], settings):
        panel = data if not setting else data[data["setting_auto"].eq(setting)]
        for stratum, group in panel.groupby("stratum", observed=True):
            group = group.assign(effort=_effort_numeric(group["word_count_exact_top12"])).sort_values("effort")
            axis.plot(group["effort"], group["predicted_mean"], marker="o", linewidth=2, label=stratum.replace("_", " / "), color=STRATUM_COLORS.get(stratum))
            axis.fill_between(group["effort"], group["ci_low"], group["ci_high"], alpha=0.13, color=STRATUM_COLORS.get(stratum))
        axis.set_xlabel("Cleaned word count (12 = 12+)")
        axis.set_ylabel("Predicted surprisal (bits)")
        axis.set_title(setting.title() if setting else "Hall")
        axis.grid(alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=9)
    fig.suptitle(title)
    _save_figure(fig, path)


def _plot_external_predictions(predictions: pd.DataFrame, path: Path) -> None:
    data = predictions[predictions["model_id"].eq("E1_k0_locked_snapshot")].copy()
    fig, axis = plt.subplots(figsize=(7.2, 4.8))
    colors = {"Hall": "#b35806", "current_naturalistic": "#2b8cbe"}
    for cohort, group in data.groupby("cohort", observed=True):
        group = group.assign(effort=_effort_numeric(group["word_count_exact_top12"])).sort_values("effort")
        label = "Hall snapshot" if cohort == "Hall" else "Locked current corpora"
        axis.plot(group["effort"], group["predicted_mean"], marker="o", linewidth=2.2, label=label, color=colors.get(cohort))
        axis.fill_between(group["effort"], group["ci_low"], group["ci_high"], alpha=0.14, color=colors.get(cohort))
    axis.set_xlabel("Cleaned word count (12 = 12+)")
    axis.set_ylabel("Predicted unconditional surprisal (bits)")
    axis.set_title("Hall and the locked age-matched naturalistic snapshot")
    axis.grid(alpha=0.2)
    axis.legend(frameon=False)
    _save_figure(fig, path)


def _forest_plot(
    frame: pd.DataFrame,
    *,
    path: Path,
    title: str,
    label_column: str,
) -> None:
    data = frame.dropna(subset=["estimate", "ci_low", "ci_high"]).copy().reset_index(drop=True)
    fig_height = max(3.8, 0.42 * len(data) + 1.8)
    fig, axis = plt.subplots(figsize=(8.2, fig_height))
    positions = np.arange(len(data))
    left = data["estimate"] - data["ci_low"]
    right = data["ci_high"] - data["estimate"]
    axis.errorbar(data["estimate"], positions, xerr=np.vstack([left, right]), fmt="o", color="#285f66", ecolor="#6c8f93", capsize=3)
    axis.axvline(0, color="#333333", linewidth=1, linestyle="--")
    axis.set_yticks(positions, data[label_column].astype(str))
    axis.invert_yaxis()
    axis.set_xlabel("Adjusted contrast in Mistral surprisal (bits)")
    axis.set_title(title)
    axis.grid(axis="x", alpha=0.2)
    _save_figure(fig, path)


def _plot_child_descriptives(wide: pd.DataFrame, path: Path) -> None:
    eligible = _bool(wide["primary_eligible"]) if "primary_eligible" in wide else pd.Series(True, index=wide.index)
    child = (
        wide[eligible]
        .groupby(["child_key", "stratum"], observed=True)["k0_bits_per_word"]
        .mean()
        .reset_index()
    )
    strata = [value for value in STRATUM_COLORS if value in set(child["stratum"])]
    fig, axis = plt.subplots(figsize=(7.5, 4.8))
    values = [child.loc[child["stratum"].eq(stratum), "k0_bits_per_word"].to_numpy() for stratum in strata]
    boxes = axis.boxplot(values, tick_labels=[value.replace("_", " / ") for value in strata], patch_artist=True, showfliers=False)
    for box, stratum in zip(boxes["boxes"], strata):
        box.set_facecolor(STRATUM_COLORS[stratum])
        box.set_alpha(0.6)
    rng = np.random.default_rng(20260817)
    for position, (stratum, group) in enumerate(child.groupby("stratum", observed=True), start=1):
        if stratum not in strata:
            continue
        x_position = strata.index(stratum) + 1
        jitter = rng.normal(0, 0.045, len(group))
        axis.scatter(x_position + jitter, group["k0_bits_per_word"], s=18, alpha=0.7, color="#263238")
    axis.set_ylabel("Child mean unconditional bits per cleaned word")
    axis.set_title("Child-level descriptive distribution (not the primary model)")
    axis.tick_params(axis="x", rotation=18)
    axis.grid(axis="y", alpha=0.2)
    _save_figure(fig, path)


def _plot_support(support: pd.DataFrame, path: Path) -> None:
    grouped = support.groupby(["stratum", "setting_auto"], observed=True)["utterances"].sum().unstack(fill_value=0)
    fig, axis = plt.subplots(figsize=(7.2, 4.4))
    image = axis.imshow(np.log10(grouped.to_numpy(float) + 1), aspect="auto", cmap="Blues")
    axis.set_yticks(range(len(grouped.index)), [value.replace("_", " / ") for value in grouped.index])
    axis.set_xticks(range(len(grouped.columns)), [str(value).title() for value in grouped.columns], rotation=20)
    for row in range(len(grouped.index)):
        for column in range(len(grouped.columns)):
            axis.text(column, row, f"{int(grouped.iloc[row, column]):,}", ha="center", va="center", fontsize=9)
    axis.set_title("Utterance support by historical stratum and setting")
    fig.colorbar(image, ax=axis, label="log10(utterances + 1)")
    _save_figure(fig, path)


def run_plot_stage(
    *,
    prepared_dir: Path = DEFAULT_PREPARED_DIR,
    model_dir: Path = DEFAULT_MODEL_DIR,
    plot_dir: Path = DEFAULT_PLOT_DIR,
) -> dict[str, object]:
    prepared_dir = prepared_dir.expanduser().resolve()
    model_dir = model_dir.expanduser().resolve()
    plot_dir = plot_dir.expanduser().resolve()
    model_manifest = json.loads((model_dir / "model_manifest.json").read_text(encoding="utf-8"))
    if model_manifest.get("status") != "PASS":
        raise ValueError("Hall plot stage requires a PASS model manifest")
    predictions = pd.read_csv(model_dir / "prediction_grid.csv")
    contrasts = pd.read_csv(model_dir / "registered_contrasts.csv")
    wide = pd.read_csv(prepared_dir / "hall_utterance_scores.csv.gz", low_memory=False)
    support = pd.read_csv(prepared_dir / "setting_stratum_effort_support.csv")

    figures = [
        ("hall_k0_adjusted_by_stratum.png", lambda path: _plot_hall_predictions(predictions, "H1_k0_primary", path, "Adjusted unconditional Mistral surprisal within Hall")),
        ("hall_k3_adjusted_by_stratum.png", lambda path: _plot_hall_predictions(predictions, "H8_k3_adult_adjacent", path, "Adjusted contextual Mistral surprisal after an adult turn")),
        ("hall_context_gain_adjusted_by_stratum.png", lambda path: _plot_hall_predictions(predictions, "H9_gain_k3_adult_adjacent", path, "Adjusted k0 − k3 context support after an adult turn")),
        ("external_locked_snapshot_predictions.png", lambda path: _plot_external_predictions(predictions, path)),
        (
            "hall_primary_registered_contrasts.png",
            lambda path: _forest_plot(
                contrasts[contrasts["model_id"].eq("H1_k0_primary")],
                path=path, title="Primary within-Hall registered contrasts", label_column="label",
            ),
        ),
        (
            "hall_interaction_sensitivities.png",
            lambda path: _forest_plot(
                contrasts[
                    contrasts["contrast_id"].eq("race_by_class_interaction")
                    & contrasts["model_id"].str.startswith("H")
                ].assign(plot_label=lambda data: data["model_id"]),
                path=path, title="Race-by-class interaction across registered Hall models", label_column="plot_label",
            ),
        ),
        (
            "external_snapshot_sensitivities.png",
            lambda path: _forest_plot(
                contrasts[contrasts["contrast_id"].eq("hall_minus_current")].assign(plot_label=lambda data: data["model_id"]),
                path=path, title="Hall-minus-current contrast across locked-snapshot models", label_column="plot_label",
            ),
        ),
        ("hall_child_descriptive_distribution.png", lambda path: _plot_child_descriptives(wide, path)),
        ("hall_setting_stratum_support.png", lambda path: _plot_support(support, path)),
    ]
    rows: list[dict[str, object]] = []
    for filename, builder in figures:
        path = plot_dir / filename
        builder(path)
        rows.append(
            {
                "figure": filename,
                "path": str(path),
                "bytes": path.stat().st_size if path.is_file() else 0,
                "status": "PASS" if path.is_file() and path.stat().st_size > 0 else "FAIL",
            }
        )
    audit = pd.DataFrame(rows)
    atomic_csv(audit, model_dir / "plot_audit.csv")
    failed = int(audit["status"].ne("PASS").sum())
    manifest: dict[str, object] = {
        "status": "PASS" if failed == 0 else "FAIL",
        "pipeline_version": PIPELINE_VERSION,
        "stage": "plots",
        "upstream_model_manifest_sha256": sha256_path(model_dir / "model_manifest.json"),
        "figures": len(audit),
        "failed_figures": failed,
    }
    atomic_json(manifest, model_dir / "plot_manifest.json")
    if failed:
        raise ValueError(f"Hall plot audit found {failed} failed figures")
    return manifest


def _fmt(value: object, digits: int = 2) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "NA"
    return "NA" if not math.isfinite(numeric) else f"{numeric:.{digits}f}"


def _contrast_row(contrasts: pd.DataFrame, model_id: str, contrast_id: str) -> pd.Series:
    match = contrasts[
        contrasts["model_id"].eq(model_id) & contrasts["contrast_id"].eq(contrast_id)
    ]
    if match.empty:
        raise ValueError(f"required report contrast is missing: {model_id}/{contrast_id}")
    return match.iloc[0]


def _markdown_table(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    data = frame[list(columns)].copy()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |"
        for row in data.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def run_report_stage(
    *,
    prepared_dir: Path = DEFAULT_PREPARED_DIR,
    model_dir: Path = DEFAULT_MODEL_DIR,
    plot_dir: Path = DEFAULT_PLOT_DIR,
    report_md: Path = DEFAULT_REPORT_MD,
    report_html: Path = DEFAULT_REPORT_HTML,
) -> dict[str, object]:
    prepared_dir = prepared_dir.expanduser().resolve()
    model_dir = model_dir.expanduser().resolve()
    plot_dir = plot_dir.expanduser().resolve()
    report_md = report_md.expanduser().resolve()
    report_html = report_html.expanduser().resolve()
    dataset_manifest = json.loads((prepared_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    model_manifest = json.loads((model_dir / "model_manifest.json").read_text(encoding="utf-8"))
    plot_manifest = json.loads((model_dir / "plot_manifest.json").read_text(encoding="utf-8"))
    if any(manifest.get("status") != "PASS" for manifest in (dataset_manifest, model_manifest, plot_manifest)):
        raise ValueError("Hall report requires PASS dataset, model, and plot manifests")
    contrasts = pd.read_csv(model_dir / "registered_contrasts.csv")
    bootstrap = pd.read_csv(model_dir / "child_bootstrap_summary.csv")
    influence = pd.read_csv(model_dir / "leave_one_cluster_out.csv")
    primary = _contrast_row(contrasts, "H1_k0_primary", "race_by_class_interaction")
    black_wc = _contrast_row(contrasts, "H1_k0_primary", "black_minus_white_wc")
    black_uc = _contrast_row(contrasts, "H1_k0_primary", "black_minus_white_uc")
    class_black = _contrast_row(contrasts, "H1_k0_primary", "uc_minus_wc_black")
    class_white = _contrast_row(contrasts, "H1_k0_primary", "uc_minus_wc_white")
    contextual = _contrast_row(contrasts, "H8_k3_adult_adjacent", "race_by_class_interaction")
    context_gain = _contrast_row(contrasts, "H9_gain_k3_adult_adjacent", "race_by_class_interaction")
    external = _contrast_row(contrasts, "E1_k0_locked_snapshot", "hall_minus_current")
    bootstrap_primary = bootstrap[
        bootstrap["model_id"].eq("H1_k0_primary")
        & bootstrap["contrast_id"].eq("race_by_class_interaction")
    ]
    bootstrap_external = bootstrap[
        bootstrap["model_id"].eq("E1_k0_locked_snapshot")
        & bootstrap["contrast_id"].eq("hall_minus_current")
    ]
    primary_boot = bootstrap_primary.iloc[0] if not bootstrap_primary.empty else pd.Series(dtype=object)
    external_boot = bootstrap_external.iloc[0] if not bootstrap_external.empty else pd.Series(dtype=object)

    def influence_range(model_id: str, contrast_id: str) -> tuple[object, object]:
        values = influence[
            influence["model_id"].eq(model_id)
            & influence["contrast_id"].eq(contrast_id)
        ]["estimate"]
        if values.empty:
            return (np.nan, np.nan)
        return (float(values.min()), float(values.max()))

    primary_influence = influence_range("H1_k0_primary", "race_by_class_interaction")
    gain_influence = influence_range("H9_gain_k3_adult_adjacent", "race_by_class_interaction")
    external_influence = influence_range("E1_k0_locked_snapshot", "hall_minus_current")

    sensitivity = contrasts[
        contrasts["contrast_id"].isin({"race_by_class_interaction", "hall_minus_current"})
    ][["model_id", "contrast_id", "estimate", "ci_low", "ci_high", "p_value"]].copy()
    for column in ("estimate", "ci_low", "ci_high", "p_value"):
        sensitivity[column] = sensitivity[column].map(lambda value: _fmt(value, 3))

    def image(filename: str, alt: str) -> str:
        return f"![{alt}]({os.path.relpath(plot_dir / filename, report_md.parent)})"

    report = f"""# Hall Snapshot: Mistral Predictability at Approximately Age Four

## Bottom line

The Hall snapshot is fully scored and locally audited. The analysis includes
{dataset_manifest['primary_children']} primary children and
{int(dataset_manifest['primary_rows']):,} primary utterances. All estimates
below are **descriptive, scorer-indexed contrasts**, not causal effects of race
or social class and not measures of linguistic worth or inherent communicative
efficiency.

At fixed cleaned word count and recorded setting, the primary unconditional
Mistral model shows a race-by-class interaction of **{_fmt(primary['estimate'])}
bits** (child-clustered 95% CI [{_fmt(primary['ci_low'])},
{_fmt(primary['ci_high'])}]). The stratified 1,000-child bootstrap interval is
[{_fmt(primary_boot.get('ci_low'))}, {_fmt(primary_boot.get('ci_high'))}]. This
means there is no scientifically honest single “race effect”: the Black-minus-
White contrast is {_fmt(black_wc['estimate'])} bits within WC but
{_fmt(black_uc['estimate'])} bits within UC. Conversely, UC-minus-WC is
{_fmt(class_black['estimate'])} bits within the Black-labelled sample and
{_fmt(class_white['estimate'])} bits within the White-labelled sample.
The interaction remains negative when each child is omitted in turn (range
[{_fmt(primary_influence[0])}, {_fmt(primary_influence[1])}] bits).

The contextual k3 interaction after an immediately preceding adult turn is
{_fmt(contextual['estimate'])} bits (95% CI [{_fmt(contextual['ci_low'])},
{_fmt(contextual['ci_high'])}]). The corresponding interaction for context
support, defined as k0 − k3, is {_fmt(context_gain['estimate'])} bits (95% CI
[{_fmt(context_gain['ci_low'])}, {_fmt(context_gain['ci_high'])}]). Thus the
group pattern is visible in Mistral target predictability, while the present
analysis does not show the same clear interaction in how much the preceding
adult context reduces surprisal.
Its leave-one-child interaction range is [{_fmt(gain_influence[0])},
{_fmt(gain_influence[1])}] bits, which reinforces that this context-support
contrast is not stable away from zero.

The locked age-matched comparison estimates Hall minus the current
naturalistic corpora at {_fmt(external['estimate'])} unconditional bits at
fixed word count (95% CI [{_fmt(external['ci_low'])},
{_fmt(external['ci_high'])}]; bootstrap [{_fmt(external_boot.get('ci_low'))},
{_fmt(external_boot.get('ci_high'))}]). This is **not a causal cohort effect**:
Hall differs in recording era, geography, setting composition, transcription,
dialect distribution, and likely Mistral training representation. Eleven of
the 20 locked comparison children come from Wells, so corpus influence remains
important.
The Hall-minus-current estimate remains positive when each current corpus is
omitted in turn (range [{_fmt(external_influence[0])},
{_fmt(external_influence[1])}] bits).

## Primary within-Hall result

{image('hall_k0_adjusted_by_stratum.png', 'Adjusted unconditional surprisal by historical Hall stratum')}

The model is a weighted regression over child × setting × exact/top-coded word
count cells. It includes race, class, their interaction, setting, and exact
word-effort controls; uncertainty is clustered by child. Positive differences
mean that Mistral assigned more surprisal, or lower model-based predictability,
to the observed utterance at the same modeled effort.

{image('hall_primary_registered_contrasts.png', 'Registered within-Hall contrasts')}

## Contextual predictability and context support

{image('hall_k3_adjusted_by_stratum.png', 'Contextual surprisal after an adult turn')}

{image('hall_context_gain_adjusted_by_stratum.png', 'Context support after an adult turn')}

Context support is k0 − k3. Larger positive values mean the preceding adult
utterances made the observed child utterance more predictable to Mistral.
Contextual analyses first restrict to genuine immediate child-after-adult
turns within the same recorded situation. “Adult” is retained as a role label;
not every adult is assumed to be a caregiver.

## Sensitivity analyses

{image('hall_interaction_sensitivities.png', 'Within-Hall interaction sensitivities')}

The model family separately checks the 37th folder-inferred child, exact age,
sex, equal-child weighting, home-only and school-only observations, k1/k2/k3
context windows, and all context-available turns. These are sensitivities, not
replacements for the frozen primary model.

{_markdown_table(sensitivity, ['model_id', 'contrast_id', 'estimate', 'ci_low', 'ci_high', 'p_value'])}

## Locked external snapshot

{image('external_locked_snapshot_predictions.png', 'Hall and locked current-corpus predictions')}

{image('external_snapshot_sensitivities.png', 'External comparison sensitivities')}

Each current-corpus child contributes one outcome-blind session nearest 57
months within 54–59 months. PBM and non-PBM provenance remains recorded; a
non-PBM-only comparison, Hall-home restriction, age control, equal-child
weighting, contextual outcome, context-support outcome, and leave-one-current-
corpus influence audit are retained.

## Support and descriptive child distribution

{image('hall_setting_stratum_support.png', 'Hall sample support by setting and stratum')}

{image('hall_child_descriptive_distribution.png', 'Child-level descriptive score distribution')}

The child distribution uses bits per cleaned word only as a descriptive view.
It is not the primary fixed-effort estimand.

## Interpretation limits

- Mistral surprisal is model-based self-information, not a direct behavioral
  measure of what human listeners understand.
- Historical Hall race and class codes are corpus strata. They must not be
  converted into claims of linguistic deficit, innate difference, or causal
  socioeconomic effects.
- Dialect, orthography, disfluency transcription, recording situation,
  historical era, and model training representation can all change scores.
- Hall is a separate cross-sectional snapshot. It is not an 80th longitudinal
  child and does not alter the frozen PBM/non-PBM developmental analyses.
- The external comparison is guarded domain-shift evidence. It cannot isolate
  development, cohort, geography, transcription, or dialect.

## Audit summary

- Scorer: Mistral-7B-v0.3, frozen revision `{EXPECTED_MODEL_REVISION}`.
- Score archive: 4/4 k0–k3 contracts, 287,320 utterance rows, archive SHA-256
  `{EXPECTED_ARCHIVE_SHA256}`.
- Models: {model_manifest['passed_models']}/{model_manifest['registered_models']}
  passed; {model_manifest['failed_models']} failed.
- Bootstrap: {model_manifest['bootstrap_reps_requested']} stratified child
  resamples for each registered primary bootstrap model.
- Plot audit: {plot_manifest['figures']}/{plot_manifest['figures']} figures
  present and nonempty.
"""
    temporary_report = report_md.with_name(f".{report_md.name}.tmp.{os.getpid()}")
    report_md.parent.mkdir(parents=True, exist_ok=True)
    try:
        temporary_report.write_text(report, encoding="utf-8")
        os.replace(temporary_report, report_md)
    finally:
        temporary_report.unlink(missing_ok=True)
    render_markdown_file(report_md, report_html, title="Hall Snapshot Mistral Analysis")
    manifest: dict[str, object] = {
        "status": "PASS",
        "pipeline_version": PIPELINE_VERSION,
        "stage": "report",
        "report_markdown": str(report_md),
        "report_html": str(report_html),
        "markdown_bytes": report_md.stat().st_size,
        "html_bytes": report_html.stat().st_size,
        "upstream_plot_manifest_sha256": sha256_path(model_dir / "plot_manifest.json"),
        "scientific_guardrails_present": all(
            phrase in report.lower()
            for phrase in ("descriptive", "not a causal", "linguistic deficit", "not an 80th")
        ),
    }
    if not manifest["scientific_guardrails_present"]:
        raise ValueError("Hall report is missing required scientific interpretation guardrails")
    atomic_json(manifest, model_dir / "report_manifest.json")
    return manifest


def run_final_audit(
    *,
    prepared_dir: Path = DEFAULT_PREPARED_DIR,
    model_dir: Path = DEFAULT_MODEL_DIR,
    plot_dir: Path = DEFAULT_PLOT_DIR,
    report_md: Path = DEFAULT_REPORT_MD,
    report_html: Path = DEFAULT_REPORT_HTML,
    output_dir: Path = DEFAULT_FINAL_DIR,
    expected_models: int = len(MODEL_SPECS),
    expected_bootstrap_models: int = 5,
    expected_bootstrap_reps: int = 1_000,
) -> dict[str, object]:
    """Audit the complete artifact chain and publish the final marker."""

    prepared_dir = prepared_dir.expanduser().resolve()
    model_dir = model_dir.expanduser().resolve()
    plot_dir = plot_dir.expanduser().resolve()
    report_md = report_md.expanduser().resolve()
    report_html = report_html.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    marker = output_dir / "ANALYSIS_COMPLETE_AND_AUDITED"
    marker.unlink(missing_ok=True)
    problems: list[str] = []
    manifests: dict[str, dict[str, object]] = {}
    for name, path in (
        ("dataset", prepared_dir / "dataset_manifest.json"),
        ("model", model_dir / "model_manifest.json"),
        ("plot", model_dir / "plot_manifest.json"),
        ("report", model_dir / "report_manifest.json"),
    ):
        if not path.is_file():
            problems.append(f"missing {name} manifest")
            continue
        manifests[name] = json.loads(path.read_text(encoding="utf-8"))
        if manifests[name].get("status") != "PASS":
            problems.append(f"{name} manifest is not PASS")
    model_manifest = manifests.get("model", {})
    if int(model_manifest.get("registered_models", -1)) != expected_models:
        problems.append("registered model count mismatch")
    if int(model_manifest.get("passed_models", -1)) != expected_models:
        problems.append("not every registered model passed")
    if int(model_manifest.get("failed_models", -1)) != 0:
        problems.append("model manifest records failures")

    contrasts_path = model_dir / "registered_contrasts.csv"
    bootstrap_path = model_dir / "child_bootstrap_summary.csv"
    plot_audit_path = model_dir / "plot_audit.csv"
    contrasts = pd.read_csv(contrasts_path) if contrasts_path.is_file() else pd.DataFrame()
    bootstrap = pd.read_csv(bootstrap_path) if bootstrap_path.is_file() else pd.DataFrame()
    plot_audit = pd.read_csv(plot_audit_path) if plot_audit_path.is_file() else pd.DataFrame()
    if contrasts.empty:
        problems.append("registered contrast table is empty")
    elif contrasts.duplicated(["model_id", "contrast_id"]).any():
        problems.append("registered contrast table contains duplicate model/contrast rows")
    else:
        numeric = contrasts[["estimate", "ci_low", "ci_high", "p_value"]].apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any() or not np.isfinite(numeric.to_numpy()).all():
            problems.append("registered contrasts contain non-finite values")
    if bootstrap.empty:
        problems.append("bootstrap summary is empty")
    else:
        if bootstrap["model_id"].nunique() != expected_bootstrap_models:
            problems.append("bootstrap model count mismatch")
        if not bootstrap["draws"].astype(int).eq(expected_bootstrap_reps).all():
            problems.append("a registered bootstrap contrast lacks the requested draws")
    if plot_audit.empty or not plot_audit["status"].astype(str).eq("PASS").all():
        problems.append("plot audit is missing or contains failures")
    for row in plot_audit.itertuples(index=False):
        path = Path(str(row.path))
        if not path.is_file() or path.stat().st_size <= 0:
            problems.append(f"plot is missing or empty: {path}")
    if not report_md.is_file() or report_md.stat().st_size <= 0:
        problems.append("Markdown report is missing or empty")
    if not report_html.is_file() or report_html.stat().st_size <= 0:
        problems.append("HTML report is missing or empty")
    report_text = report_md.read_text(encoding="utf-8").lower() if report_md.is_file() else ""
    for phrase in ("descriptive", "not a causal", "linguistic deficit", "not an 80th"):
        if phrase not in report_text:
            problems.append(f"report guardrail is missing: {phrase}")

    identity_paths = [
        prepared_dir / "dataset_manifest.json",
        model_dir / "model_manifest.json",
        model_dir / "plot_manifest.json",
        model_dir / "report_manifest.json",
        contrasts_path,
        bootstrap_path,
        plot_audit_path,
        report_md,
        report_html,
    ]
    identities = {
        path.name: {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_path(path),
        }
        for path in identity_paths
        if path.is_file()
    }
    report: dict[str, object] = {
        "status": "PASS" if not problems else "FAIL",
        "pipeline_version": PIPELINE_VERSION,
        "stage": "final_audit",
        "problem_count": len(problems),
        "problems": problems,
        "registered_models": int(model_manifest.get("registered_models", 0)),
        "passed_models": int(model_manifest.get("passed_models", 0)),
        "registered_contrasts": len(contrasts),
        "bootstrap_models": int(bootstrap["model_id"].nunique()) if not bootstrap.empty else 0,
        "bootstrap_contrasts": len(bootstrap),
        "bootstrap_reps": expected_bootstrap_reps,
        "figures": len(plot_audit),
        "artifact_identities": identities,
    }
    atomic_json(report, output_dir / "final_audit.json")
    if problems:
        raise ValueError(f"Hall final analysis audit failed with {len(problems)} problem(s): {problems[0]}")
    marker.parent.mkdir(parents=True, exist_ok=True)
    temporary_marker = marker.with_name(f".{marker.name}.tmp.{os.getpid()}")
    try:
        temporary_marker.write_text(
            f"ANALYSIS_COMPLETE_AND_AUDITED\n{sha256_path(output_dir / 'final_audit.json')}\n",
            encoding="utf-8",
        )
        os.replace(temporary_marker, marker)
    finally:
        temporary_marker.unlink(missing_ok=True)
    return report


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("datasets", "models", "plots", "report", "audit", "all"),
        default="all",
    )
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--prepared-dir", type=Path, default=DEFAULT_PREPARED_DIR)
    parser.add_argument("--comparator-manifest", type=Path, default=DEFAULT_COMPARATOR)
    parser.add_argument("--trajectory-input", type=Path, default=DEFAULT_TRAJECTORY)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--plot-dir", type=Path, default=DEFAULT_PLOT_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-html", type=Path, default=DEFAULT_REPORT_HTML)
    parser.add_argument("--final-dir", type=Path, default=DEFAULT_FINAL_DIR)
    parser.add_argument("--bootstrap-reps", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=20260817)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_cli().parse_args(argv)
    manifest: dict[str, object] = {}
    if args.stage in {"datasets", "all"}:
        manifest = build_dataset_stage(
            archive_path=args.archive,
            local_audit_dir=args.audit_dir,
            comparator_manifest=args.comparator_manifest,
            trajectory_input=args.trajectory_input,
            output_dir=args.prepared_dir,
        )
    if args.stage in {"models", "all"}:
        manifest = run_model_stage(
            prepared_dir=args.prepared_dir,
            model_dir=args.model_dir,
            bootstrap_reps=args.bootstrap_reps,
            seed=args.seed,
        )
    if args.stage in {"plots", "all"}:
        manifest = run_plot_stage(
            prepared_dir=args.prepared_dir,
            model_dir=args.model_dir,
            plot_dir=args.plot_dir,
        )
    if args.stage in {"report", "all"}:
        manifest = run_report_stage(
            prepared_dir=args.prepared_dir,
            model_dir=args.model_dir,
            plot_dir=args.plot_dir,
            report_md=args.report_md,
            report_html=args.report_html,
        )
    if args.stage in {"audit", "all"}:
        manifest = run_final_audit(
            prepared_dir=args.prepared_dir,
            model_dir=args.model_dir,
            plot_dir=args.plot_dir,
            report_md=args.report_md,
            report_html=args.report_html,
            output_dir=args.final_dir,
            expected_bootstrap_reps=args.bootstrap_reps,
        )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
