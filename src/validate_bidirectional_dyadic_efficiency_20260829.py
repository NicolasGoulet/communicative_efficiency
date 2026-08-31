#!/usr/bin/env python3
"""Focused robustness checks for the registered bidirectional k3 models."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd


AGE_BINS = ["006-023", "024-029", "030-035", "036-041", "042-047", "048-053", "054-059", "060-065"]
AGE_MIDS = np.array([14.5, 26.5, 32.5, 38.5, 44.5, 50.5, 56.5, 62.5])
FAMILIES = ("F1", "F2", "F3")
SCOPES = ("pbm_discovery", "non_pbm_confirmation", "all79_descriptive")
SUPPORTED_BINS = {
    "pbm_discovery": AGE_BINS[:6],
    "non_pbm_confirmation": AGE_BINS[1:],
    "all79_descriptive": AGE_BINS,
}


def atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    frame.to_csv(temporary, index=False, lineterminator="\n")
    os.replace(temporary, path)


def load_family(path: Path, family_id: str, scope: str) -> pd.DataFrame:
    where = "" if scope == "all79_descriptive" else f"WHERE sample_group='{scope}'"
    if family_id == "F1":
        columns = "c_k3_bits AS outcome, a0_k3_within AS predictor, ln(1+a0_words) AS control_a0, c_word_top12"
    elif family_id == "F2":
        columns = "ln(1+c_words) AS outcome, a0_k3_within AS predictor, ln(1+a0_words) AS control_a0, c_word_top12"
    else:
        columns = "ln(1+a1_words) AS outcome, c_k3_within AS predictor, ln(1+a0_words) AS control_a0, ln(1+c_words) AS control_c, a0_k3_within AS control_a0_k3, c_word_top12"
    connection = duckdb.connect()
    frame = connection.execute(
        f"""SELECT child_key, dataset, child_session_key, age_bin, {columns}
            FROM read_parquet(?) {where} ORDER BY dataset, child_key, child_session_key""",
        [str(path)],
    ).fetchdf()
    connection.close()
    frame["age_bin"] = pd.Categorical(frame.age_bin, categories=AGE_BINS, ordered=True)
    return frame


def demean(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    means = frame.groupby("child_session_key", observed=True)[columns].transform("mean")
    return frame[columns] - means


def design_matrix(
    frame: pd.DataFrame,
    family_id: str,
    scope: str,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    y = demean(frame, ["outcome"])["outcome"].to_numpy(float)
    predictor = demean(frame, ["predictor"])["predictor"].to_numpy(float)
    age_codes = frame.age_bin.cat.codes.to_numpy()
    supported = SUPPORTED_BINS[scope]
    supported_indices = [AGE_BINS.index(label) for label in supported]
    interactions = np.column_stack([
        predictor * (age_codes == index) for index in supported_indices
    ])
    names = [f"coupling_{label}" for label in supported]
    controls: list[np.ndarray] = []
    if family_id == "F1":
        word = pd.get_dummies(frame.c_word_top12.astype(str), drop_first=True, dtype=float)
        word_frame = pd.DataFrame(word, index=frame.index)
        word_centered = word_frame - word_frame.groupby(frame.child_session_key, observed=True).transform("mean")
        controls.append(word_centered.to_numpy(float))
        names.extend([f"word_{column}" for column in word.columns])
    continuous = ["control_a0"]
    if family_id == "F3":
        continuous.extend(["control_c", "control_a0_k3"])
    centered = demean(frame, continuous)
    controls.append(centered.to_numpy(float))
    names.extend(continuous)
    x = np.column_stack([interactions, *controls])
    keep = np.nanstd(x, axis=0) > 1e-12
    x = x[:, keep]
    names = [name for name, retained in zip(names, keep) if retained]
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("non-finite validation design")
    if np.linalg.matrix_rank(x) != x.shape[1]:
        raise ValueError(f"rank-deficient {family_id} validation design")
    return x, y, names


def solve_system(xtx: np.ndarray, xty: np.ndarray) -> np.ndarray:
    return np.linalg.solve(xtx, xty)


def child_sufficient_statistics(
    frame: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[list[str], np.ndarray, np.ndarray, list[str]]:
    children = sorted(frame.child_key.unique())
    child_values = frame.child_key.to_numpy()
    xtx = np.empty((len(children), x.shape[1], x.shape[1]))
    xty = np.empty((len(children), x.shape[1]))
    corpora: list[str] = []
    for index, child in enumerate(children):
        selected = child_values == child
        xi = x[selected]
        xtx[index] = xi.T @ xi
        xty[index] = xi.T @ y[selected]
        corpus = frame.loc[selected, "dataset"].unique()
        if len(corpus) != 1:
            raise ValueError(f"child spans corpora: {child}")
        corpora.append(str(corpus[0]))
    return children, xtx, xty, corpora


def whole_child_bootstrap(
    xtx: np.ndarray,
    xty: np.ndarray,
    *,
    strata: list[str],
    seed: int,
    replicates: int,
) -> tuple[np.ndarray, np.ndarray]:
    point = solve_system(xtx.sum(axis=0), xty.sum(axis=0))
    rng = np.random.default_rng(seed)
    draws = np.full((replicates, xty.shape[1]), np.nan)
    successes = 0
    stratum_array = np.asarray(strata)
    stratum_indices = [np.flatnonzero(stratum_array == value) for value in sorted(set(strata))]
    for replicate in range(replicates):
        selected = np.concatenate([
            rng.choice(indices, size=len(indices), replace=True)
            for indices in stratum_indices
        ])
        try:
            draws[replicate] = solve_system(xtx[selected].sum(axis=0), xty[selected].sum(axis=0))
            successes += 1
        except np.linalg.LinAlgError:
            continue
    return point, draws[:successes]


def simple_age_slopes(
    frame: pd.DataFrame,
    predictor: np.ndarray | None = None,
    bins: np.ndarray | None = None,
    outcome: np.ndarray | None = None,
) -> np.ndarray:
    pred = demean(frame, ["predictor"])["predictor"].to_numpy(float) if predictor is None else predictor
    centered_outcome = (
        demean(frame, ["outcome"])["outcome"].to_numpy(float)
        if outcome is None else outcome
    )
    codes = frame.age_bin.cat.codes.to_numpy() if bins is None else bins
    numerator = np.bincount(codes, weights=pred * centered_outcome, minlength=len(AGE_BINS))
    denominator = np.bincount(codes, weights=pred * pred, minlength=len(AGE_BINS))
    slopes = np.divide(
        numerator,
        denominator,
        out=np.full(len(AGE_BINS), np.nan),
        where=denominator > 0,
    )
    return slopes


def permutation_diagnostics(
    frame: pd.DataFrame,
    *,
    seed: int,
    replicates: int,
) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    predictor = demean(frame, ["predictor"])["predictor"].to_numpy(float)
    outcome = demean(frame, ["outcome"])["outcome"].to_numpy(float)
    bins = frame.age_bin.cat.codes.to_numpy()
    observed = simple_age_slopes(frame, predictor, bins, outcome)
    valid = np.isfinite(observed)
    observed_pairing = float(np.sqrt(np.mean(observed[valid] ** 2)))
    observed_trend = float(np.polyfit(AGE_MIDS[valid], observed[valid], 1)[0])
    session_indices = [indices for indices in frame.groupby("child_session_key", observed=True).indices.values()]
    session_bins = np.array([bins[indices[0]] for indices in session_indices])
    pairing_null = np.empty(replicates)
    group_age_null = np.empty(replicates)
    row_age_null = np.empty(replicates)
    for replicate in range(replicates):
        shuffled = predictor.copy()
        for indices in session_indices:
            shuffled[indices] = rng.permutation(shuffled[indices])
        values = simple_age_slopes(frame, shuffled, bins, outcome)
        pairing_null[replicate] = np.sqrt(np.nanmean(values ** 2))

        permuted_session_bins = rng.permutation(session_bins)
        group_bins = bins.copy()
        for indices, code in zip(session_indices, permuted_session_bins):
            group_bins[indices] = code
        values = simple_age_slopes(frame, predictor, group_bins, outcome)
        available = np.isfinite(values)
        group_age_null[replicate] = np.polyfit(AGE_MIDS[available], values[available], 1)[0]

        values = simple_age_slopes(frame, predictor, rng.permutation(bins), outcome)
        available = np.isfinite(values)
        row_age_null[replicate] = np.polyfit(AGE_MIDS[available], values[available], 1)[0]
    two_sided = lambda null, value: float((1 + np.sum(np.abs(null) >= abs(value))) / (len(null) + 1))
    upper = lambda null, value: float((1 + np.sum(null >= value)) / (len(null) + 1))
    return [
        {
            "test": "within_session_turn_shuffle",
            "observed_statistic": observed_pairing,
            "null_mean": float(pairing_null.mean()),
            "p_value": upper(pairing_null, observed_pairing),
        },
        {
            "test": "session_level_age_scramble",
            "observed_statistic": observed_trend,
            "null_mean": float(group_age_null.mean()),
            "p_value": two_sided(group_age_null, observed_trend),
        },
        {
            "test": "row_level_age_scramble",
            "observed_statistic": observed_trend,
            "null_mean": float(row_age_null.mean()),
            "p_value": two_sided(row_age_null, observed_trend),
        },
    ]


def run_validation(
    *,
    input_path: Path,
    contract_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("status") != "frozen_pre_fit":
        raise ValueError("validation requires the frozen contract")
    replicates = int(contract["validation"]["whole_child_bootstrap_replicates"])
    seed = int(contract["validation"]["whole_child_bootstrap_seed"])
    bootstrap_rows: list[dict[str, Any]] = []
    influence_rows: list[dict[str, Any]] = []
    equalized_rows: list[dict[str, Any]] = []
    permutation_rows: list[dict[str, Any]] = []
    minimum_success = 1.0
    for family_index, family_id in enumerate(FAMILIES):
        for scope_index, scope in enumerate(SCOPES):
            frame = load_family(input_path, family_id, scope)
            x, y, names = design_matrix(frame, family_id, scope)
            children, xtx, xty, corpora = child_sufficient_statistics(frame, x, y)
            point, draws = whole_child_bootstrap(
                xtx, xty, strata=corpora,
                seed=seed + family_index * 100 + scope_index,
                replicates=replicates,
            )
            success_fraction = len(draws) / replicates
            minimum_success = min(minimum_success, success_fraction)
            for age_index, age_bin in enumerate(AGE_BINS):
                if f"coupling_{age_bin}" not in names:
                    continue
                coefficient = names.index(f"coupling_{age_bin}")
                bootstrap_rows.append({
                    "family_id": family_id,
                    "scope": scope,
                    "age_bin": age_bin,
                    "estimate": point[coefficient],
                    "bootstrap_q025": np.quantile(draws[:, coefficient], .025),
                    "bootstrap_q975": np.quantile(draws[:, coefficient], .975),
                    "bootstrap_replicates": len(draws),
                    "children": len(children),
                })
            if scope == "all79_descriptive":
                corpus_array = np.asarray(corpora)
                for corpus in sorted(set(corpora)):
                    keep = corpus_array != corpus
                    estimate = solve_system(xtx[keep].sum(axis=0), xty[keep].sum(axis=0))
                    for age_bin in AGE_BINS:
                        term = f"coupling_{age_bin}"
                        if term in names:
                            influence_rows.append({
                                "family_id": family_id,
                                "omitted_corpus": corpus,
                                "age_bin": age_bin,
                                "estimate": estimate[names.index(term)],
                            })
                counts = frame.age_bin.value_counts().reindex(AGE_BINS).to_dict()
                weights = frame.age_bin.astype(str).map({key: 1 / value for key, value in counts.items()}).to_numpy(float)
                weighted_x = x * np.sqrt(weights[:, None])
                weighted_y = y * np.sqrt(weights)
                equalized = solve_system(weighted_x.T @ weighted_x, weighted_x.T @ weighted_y)
                for age_bin in AGE_BINS:
                    term = f"coupling_{age_bin}"
                    if term in names:
                        equalized_rows.append({
                            "family_id": family_id,
                            "age_bin": age_bin,
                            "estimate": equalized[names.index(term)],
                        })
                for record in permutation_diagnostics(
                    frame, seed=seed + 1000 + family_index, replicates=replicates
                ):
                    permutation_rows.append({"family_id": family_id, "scope": scope, **record, "replicates": replicates})
    bootstrap = pd.DataFrame(bootstrap_rows)
    influence = pd.DataFrame(influence_rows)
    equalized = pd.DataFrame(equalized_rows)
    permutations = pd.DataFrame(permutation_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_csv(bootstrap, output_dir / "whole_child_bootstrap_age_bin_slopes.csv")
    atomic_csv(influence, output_dir / "leave_one_corpus_out.csv")
    atomic_csv(equalized, output_dir / "equalized_age_slopes.csv")
    atomic_csv(permutations, output_dir / "permutation_tests.csv")
    confirmation: dict[str, bool] = {}
    for family_id in FAMILIES:
        view = bootstrap[
            (bootstrap.family_id == family_id)
            & (bootstrap.scope == "non_pbm_confirmation")
        ].copy()
        excludes = ((view.bootstrap_q025 > 0) | (view.bootstrap_q975 < 0)).tolist()
        confirmation[family_id] = any(left and right for left, right in zip(excludes, excludes[1:]))
    problems: list[str] = []
    if minimum_success < float(contract["validation"]["minimum_successful_bootstrap_fraction"]):
        problems.append("whole-child bootstrap success fraction below gate")
    if len(influence) != 3 * 13 * 8:
        problems.append("leave-one-corpus inventory mismatch")
    if len(permutations) != 9:
        problems.append("permutation inventory mismatch")
    audit = {
        "status": "PASS" if not problems else "FAIL",
        "bootstrap_rows": len(bootstrap),
        "minimum_bootstrap_success_fraction": minimum_success,
        "leave_one_corpus_rows": len(influence),
        "equalized_age_rows": len(equalized),
        "permutation_tests": len(permutations),
        "confirmation_by_binned_bootstrap": confirmation,
        "problems": problems,
    }
    atomic_json(audit, output_dir / "validation_audit.json")
    if problems:
        raise RuntimeError("validation audit failed: " + "; ".join(problems))
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_validation(input_path=args.input, contract_path=args.contract, output_dir=args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
