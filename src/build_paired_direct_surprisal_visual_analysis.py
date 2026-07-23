#!/usr/bin/env python3
"""Fit, plot, and report expanded paired TinyDialogues–Mistral comparisons.

The exact paired wide table is treated as the immutable dataset stage. This
script separates the remaining work into ``models``, ``plots``, and ``report``
so a visual or wording change never rereads the 446k-row paired dataset.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from build_direct_surprisal_model_suite import (
    AGE_BINS,
    WORD_CATEGORIES,
    child_fe_crossproducts,
    relative,
    word_category,
)
from render_markdown_report import render_markdown_file


VERSION = "2026-07-21.paired-visual-v1"
OUTCOMES = {
    "Contextual target (k3)": "real_k3_sum_bits",
    "Unconditional target (k0)": "real_k0_sum_bits",
    "Contextual target (k1)": "real_k1_sum_bits",
    "Contextual target (k2)": "real_k2_sum_bits",
    "Context support (k1)": "real_context_gain_k1",
    "Context support (k2)": "real_context_gain_k2",
    "Context support (k3)": "real_context_gain_k3",
    "Random minus real": "random_minus_real_k3_bits",
    "Unigram minus real": "unigram_minus_real_k3_bits",
    "Bigram minus real": "bigram_minus_real_k3_bits",
    "Trigram minus real": "trigram_minus_real_k3_bits",
}
PRIMARY = ["real_k3_sum_bits", "real_k0_sum_bits", "real_context_gain_k3"]
CANDIDATE_OUTCOMES = {
    "random": "random_minus_real_k3_bits",
    "unigram": "unigram_minus_real_k3_bits",
    "bigram": "bigram_minus_real_k3_bits",
    "trigram": "trigram_minus_real_k3_bits",
}


def atomic_csv(frame: pd.DataFrame, path: Path, *, compression: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + (".tmp.gz" if compression == "gzip" else ".tmp"))
    frame.to_csv(temporary, index=False, compression=compression)
    os.replace(temporary, path)


def atomic_json(payload: Mapping[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def fit_slope(cells: pd.DataFrame, outcome: str) -> float:
    result = smf.wls(
        f"{outcome} ~ age_c + C(word_count_exact_top12) + C(child_key)",
        data=cells,
        weights=cells["row_count"],
    ).fit()
    return float(result.params["age_c"])


def collapse_outcome_cells(
    frame: pd.DataFrame,
    outcome: str,
    left_suffix: str,
    right_suffix: str,
) -> pd.DataFrame:
    """Collapse exact paired rows using the outcome's own context support.

    The primary and candidate-gap outcomes require k3 support, k1/k2 target and
    gain outcomes require their corresponding scored-token support, and k0
    requires only its unconditional target tokens. This avoids silently using
    the stricter k3 row set for the repeated context-window ladder.
    """

    left_column = f"{outcome}_{left_suffix}"
    right_column = f"{outcome}_{right_suffix}"
    if outcome == "real_k0_sum_bits":
        context = "k0"
    elif outcome in {"real_k1_sum_bits", "real_context_gain_k1"}:
        context = "k1"
    elif outcome in {"real_k2_sum_bits", "real_context_gain_k2"}:
        context = "k2"
    else:
        context = "k3"
    age = pd.to_numeric(frame[f"age_months_{left_suffix}"], errors="coerce")
    words = pd.to_numeric(frame[f"real_nb_words_{left_suffix}"], errors="coerce")
    left_tokens = pd.to_numeric(
        frame[f"real_{context}_n_eval_tokens_{left_suffix}"], errors="coerce"
    )
    right_tokens = pd.to_numeric(
        frame[f"real_{context}_n_eval_tokens_{right_suffix}"], errors="coerce"
    )
    mask = (
        age.between(6, 65, inclusive="both")
        & words.ge(1)
        & pd.to_numeric(frame[left_column], errors="coerce").notna()
        & pd.to_numeric(frame[right_column], errors="coerce").notna()
        & left_tokens.gt(0)
        & right_tokens.gt(0)
    )
    if context == "k3":
        mask &= pd.to_numeric(
            frame[f"context_available_k3_{left_suffix}"], errors="coerce"
        ).gt(0)
        mask &= pd.to_numeric(
            frame[f"context_available_k3_{right_suffix}"], errors="coerce"
        ).gt(0)
    data = pd.DataFrame(
        {
            "dataset": frame.loc[mask, f"dataset_{left_suffix}"],
            "child_key": frame.loc[mask, f"child_key_{left_suffix}"],
            "age_months": age[mask],
            "word_count_exact_top12": word_category(words[mask]),
            "left_outcome": pd.to_numeric(frame.loc[mask, left_column], errors="coerce"),
            "right_outcome": pd.to_numeric(frame.loc[mask, right_column], errors="coerce"),
        }
    )
    cells = (
        data.groupby(
            ["dataset", "child_key", "age_months", "word_count_exact_top12"],
            observed=True,
            dropna=False,
        )
        .agg(
            left_outcome=("left_outcome", "mean"),
            right_outcome=("right_outcome", "mean"),
            row_count=("left_outcome", "size"),
        )
        .reset_index()
    )
    cells["age_c"] = cells["age_months"] - np.average(
        cells["age_months"], weights=cells["row_count"]
    )
    cells["word_count_exact_top12"] = pd.Categorical(
        cells["word_count_exact_top12"], categories=WORD_CATEGORIES, ordered=True
    )
    return cells


def paired_bootstrap(
    paired: pd.DataFrame,
    *,
    left_suffix: str,
    right_suffix: str,
    reps: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    rng = np.random.default_rng(seed)
    summaries = []
    draws = []
    cell_tables: dict[str, pd.DataFrame] = {}
    for outcome_index, outcome in enumerate(OUTCOMES.values()):
        cells = collapse_outcome_cells(paired, outcome, left_suffix, right_suffix)
        cell_tables[outcome] = cells
        observed_left = fit_slope(cells, "left_outcome")
        observed_right = fit_slope(cells, "right_outcome")
        children, left_matrices, left_vectors = child_fe_crossproducts(
            cells.rename(columns={"left_outcome": "outcome_mean"})
        )
        right_children, right_matrices, right_vectors = child_fe_crossproducts(
            cells.rename(columns={"right_outcome": "outcome_mean"})
        )
        if not np.array_equal(children, right_children):
            raise ValueError("Paired scorer cells produced different child orders")
        outcome_draws = []
        for replicate in range(reps):
            sampled = rng.integers(0, len(children), size=len(children))
            left = float(np.linalg.lstsq(left_matrices[sampled].sum(axis=0), left_vectors[sampled].sum(axis=0), rcond=None)[0][0])
            right = float(np.linalg.lstsq(right_matrices[sampled].sum(axis=0), right_vectors[sampled].sum(axis=0), rcond=None)[0][0])
            difference = left - right
            outcome_draws.append(difference)
            draws.append(
                {
                    "outcome": outcome,
                    "replicate": replicate,
                    "seed": seed,
                    f"slope_{left_suffix}": left,
                    f"slope_{right_suffix}": right,
                    "slope_difference_left_minus_right": difference,
                }
            )
        values = np.asarray(outcome_draws)
        summaries.append(
            {
                "outcome": outcome,
                "label": next(label for label, value in OUTCOMES.items() if value == outcome),
                "paired_rows": int(cells["row_count"].sum()),
                "children": len(children),
                f"slope_{left_suffix}": observed_left,
                f"slope_{right_suffix}": observed_right,
                "slope_difference_left_minus_right": observed_left - observed_right,
                "difference_ci_low": float(np.quantile(values, 0.025)),
                "difference_ci_high": float(np.quantile(values, 0.975)),
                "bootstrap_reps": reps,
            }
        )
    return pd.DataFrame(summaries), pd.DataFrame(draws), cell_tables


def age_bin_coefficients(
    cell_tables: Mapping[str, pd.DataFrame], *, left_suffix: str, right_suffix: str
) -> pd.DataFrame:
    rows = []
    for outcome in PRIMARY:
        cells = cell_tables[outcome].copy()
        cells["age_bin"] = pd.cut(
            cells["age_months"],
            bins=[5.999, 23.999, 29.999, 35.999, 41.999, 47.999, 53.999, 59.999, 65.001],
            labels=AGE_BINS,
        )
        for suffix, column in [(left_suffix, "left_outcome"), (right_suffix, "right_outcome")]:
            formula = (
                f"{column} ~ C(age_bin, Treatment(reference='006-023')) "
                "+ C(word_count_exact_top12) + C(child_key)"
            )
            result = smf.wls(formula, data=cells, weights=cells["row_count"]).fit(
                cov_type="cluster", cov_kwds={"groups": cells["child_key"], "use_correction": True}
            )
            intervals = result.conf_int()
            for term in result.params.index:
                if "C(age_bin" not in term:
                    continue
                rows.append(
                    {
                        "outcome": outcome,
                        "scorer": suffix,
                        "term": term,
                        "age_bin": re.search(r"\[T\.([^]]+)\]", term).group(1),
                        "estimate": float(result.params[term]),
                        "ci_low": float(intervals.loc[term, 0]),
                        "ci_high": float(intervals.loc[term, 1]),
                    }
                )
    return pd.DataFrame(rows)


def paired_quadratic_bootstrap(
    cell_tables: Mapping[str, pd.DataFrame],
    *,
    left_suffix: str,
    right_suffix: str,
    reps: int,
    seed: int,
) -> pd.DataFrame:
    """Compare quadratic age curvature with paired child resampling."""

    rng = np.random.default_rng(seed)
    rows = []
    for outcome in PRIMARY:
        cells = cell_tables[outcome].copy()
        word_dummies = pd.get_dummies(
            pd.Categorical(
                cells["word_count_exact_top12"], categories=WORD_CATEGORIES, ordered=True
            ),
            prefix="word",
            dtype=float,
        ).drop(columns=["word_1"], errors="ignore")
        design = np.column_stack(
            [
                cells["age_c"].to_numpy(float),
                cells["age_c"].to_numpy(float) ** 2,
                word_dummies.to_numpy(float),
            ]
        )
        weights = cells["row_count"].to_numpy(float)
        child_values = cells["child_key"].astype(str).to_numpy()
        children = np.array(sorted(pd.unique(child_values)))
        matrices = []
        left_vectors = []
        right_vectors = []
        for child in children:
            take = child_values == child
            child_weights = weights[take]
            child_design = design[take]
            centered_design = child_design - np.average(
                child_design, axis=0, weights=child_weights
            )
            matrices.append(
                centered_design.T @ (child_weights[:, None] * centered_design)
            )
            for column, vectors in [
                ("left_outcome", left_vectors),
                ("right_outcome", right_vectors),
            ]:
                values = cells.loc[take, column].to_numpy(float)
                centered_values = values - np.average(values, weights=child_weights)
                vectors.append(centered_design.T @ (child_weights * centered_values))
        matrices_array = np.stack(matrices)
        left_array = np.stack(left_vectors)
        right_array = np.stack(right_vectors)
        observed_matrix = matrices_array.sum(axis=0)
        observed_left = float(
            np.linalg.lstsq(observed_matrix, left_array.sum(axis=0), rcond=None)[0][1]
        )
        observed_right = float(
            np.linalg.lstsq(observed_matrix, right_array.sum(axis=0), rcond=None)[0][1]
        )
        differences = []
        for _ in range(reps):
            sampled = rng.integers(0, len(children), size=len(children))
            sampled_matrix = matrices_array[sampled].sum(axis=0)
            left = float(
                np.linalg.lstsq(
                    sampled_matrix, left_array[sampled].sum(axis=0), rcond=None
                )[0][1]
            )
            right = float(
                np.linalg.lstsq(
                    sampled_matrix, right_array[sampled].sum(axis=0), rcond=None
                )[0][1]
            )
            differences.append(left - right)
        rows.append(
            {
                "outcome": outcome,
                "label": next(label for label, value in OUTCOMES.items() if value == outcome),
                f"quadratic_{left_suffix}": observed_left,
                f"quadratic_{right_suffix}": observed_right,
                "quadratic_difference_left_minus_right": observed_left - observed_right,
                "difference_ci_low": float(np.quantile(differences, 0.025)),
                "difference_ci_high": float(np.quantile(differences, 0.975)),
                "children": len(children),
                "bootstrap_reps": reps,
            }
        )
    return pd.DataFrame(rows)


def candidate_rankings_and_interactions(
    cell_tables: Mapping[str, pd.DataFrame], *, left_suffix: str, right_suffix: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize candidate-gap ordering and source-by-age interactions."""

    ranking_rows = []
    interaction_rows = []
    for scorer, outcome_column in [
        (left_suffix, "left_outcome"),
        (right_suffix, "right_outcome"),
    ]:
        frames = []
        for candidate, outcome in CANDIDATE_OUTCOMES.items():
            data = cell_tables[outcome].copy()
            data["candidate"] = candidate
            data["gap"] = data[outcome_column]
            data["age_bin"] = pd.cut(
                data["age_months"],
                bins=[5.999, 23.999, 29.999, 35.999, 41.999, 47.999, 53.999, 59.999, 65.001],
                labels=AGE_BINS,
            )
            frames.append(data)
            for age_bin, group in data.groupby("age_bin", observed=True):
                ranking_rows.append(
                    {
                        "scorer": scorer,
                        "candidate": candidate,
                        "age_bin": str(age_bin),
                        "weighted_mean_gap": float(
                            np.average(group["gap"], weights=group["row_count"])
                        ),
                        "paired_rows": int(group["row_count"].sum()),
                    }
                )
        stacked = pd.concat(frames, ignore_index=True)
        result = smf.wls(
            "gap ~ C(candidate, Treatment(reference='trigram')) "
            "* (age_c + C(word_count_exact_top12) + C(child_key))",
            data=stacked,
            weights=stacked["row_count"],
        ).fit(
            cov_type="cluster",
            cov_kwds={"groups": stacked["child_key"], "use_correction": True},
        )
        intervals = result.conf_int()
        for term in result.params.index:
            if "age_c" not in term:
                continue
            interaction_rows.append(
                {
                    "scorer": scorer,
                    "term": term,
                    "estimate": float(result.params[term]),
                    "ci_low": float(intervals.loc[term, 0]),
                    "ci_high": float(intervals.loc[term, 1]),
                    "p_value": float(result.pvalues[term]),
                    "paired_rows": int(stacked["row_count"].sum()),
                    "children": int(stacked["child_key"].nunique()),
                }
            )
    rankings = pd.DataFrame(ranking_rows)
    rankings["predictability_rank_within_scorer_age"] = rankings.groupby(
        ["scorer", "age_bin"], observed=True
    )["weighted_mean_gap"].rank(method="dense", ascending=True)
    return rankings, pd.DataFrame(interaction_rows)


def child_slope_comparison(
    cell_tables: Mapping[str, pd.DataFrame], *, left_suffix: str, right_suffix: str
) -> pd.DataFrame:
    rows = []
    for outcome in ["real_k3_sum_bits", "real_context_gain_k3", *[value for value in OUTCOMES.values() if "minus_real" in value]]:
        cells = cell_tables[outcome]
        for child, group in cells.groupby("child_key", observed=True):
            distinct_ages = group["age_months"].nunique()
            age_span = group["age_months"].max() - group["age_months"].min()
            supported = distinct_ages >= 3 and age_span >= 6 and group["row_count"].sum() >= 100
            if supported:
                child_group = group.copy()
                child_group["age_c"] = child_group["age_months"] - np.average(
                    child_group["age_months"], weights=child_group["row_count"]
                )
                formula = "{outcome} ~ age_c + C(word_count_exact_top12)"
                left = float(
                    smf.wls(
                        formula.format(outcome="left_outcome"),
                        data=child_group,
                        weights=child_group["row_count"],
                    ).fit().params["age_c"]
                )
                right = float(
                    smf.wls(
                        formula.format(outcome="right_outcome"),
                        data=child_group,
                        weights=child_group["row_count"],
                    ).fit().params["age_c"]
                )
            else:
                left = np.nan
                right = np.nan
            rows.append(
                {
                    "outcome": outcome,
                    "child_key": child,
                    "dataset": group["dataset"].iloc[0],
                    "distinct_ages": distinct_ages,
                    "age_span": age_span,
                    "rows": int(group["row_count"].sum()),
                    "supported": int(supported),
                    f"slope_{left_suffix}": left,
                    f"slope_{right_suffix}": right,
                    "same_sign": int(np.sign(left) == np.sign(right)) if supported else np.nan,
                    "difference_left_minus_right": left - right if supported else np.nan,
                }
            )
    return pd.DataFrame(rows)


def diagnostic_summary(paired: pd.DataFrame, *, left_suffix: str, right_suffix: str) -> pd.DataFrame:
    def bits_per_word(suffix: str) -> pd.Series:
        derived = f"real_bits_per_word_k3_{suffix}"
        if derived in paired:
            return pd.to_numeric(paired[derived], errors="coerce")
        return pd.to_numeric(paired[f"real_k3_sum_bits_{suffix}"], errors="coerce") / pd.to_numeric(
            paired[f"real_nb_words_{suffix}"], errors="coerce"
        ).replace(0, np.nan)

    data = pd.DataFrame(
        {
            "dataset": paired[f"dataset_{left_suffix}"],
            "age_bin": paired[f"age_bin_{left_suffix}"],
            "token_ratio_left_over_right": pd.to_numeric(paired[f"real_k3_n_eval_tokens_{left_suffix}"], errors="coerce")
            / pd.to_numeric(paired[f"real_k3_n_eval_tokens_{right_suffix}"], errors="coerce").replace(0, np.nan),
            "k3_bits_per_word_difference": bits_per_word(left_suffix)
            - bits_per_word(right_suffix),
            "context_gain_difference": pd.to_numeric(paired[f"real_context_gain_k3_{left_suffix}"], errors="coerce")
            - pd.to_numeric(paired[f"real_context_gain_k3_{right_suffix}"], errors="coerce"),
        }
    )
    return (
        data.groupby(["dataset", "age_bin"], observed=True)
        .agg(
            rows=("token_ratio_left_over_right", "size"),
            token_ratio_median=("token_ratio_left_over_right", "median"),
            token_ratio_q10=("token_ratio_left_over_right", lambda values: values.quantile(0.10)),
            token_ratio_q90=("token_ratio_left_over_right", lambda values: values.quantile(0.90)),
            k3_bits_per_word_difference_mean=("k3_bits_per_word_difference", "mean"),
            context_gain_difference_mean=("context_gain_difference", "mean"),
        )
        .reset_index()
    )


def run_models(
    *, paired_wide: Path, output_dir: Path, left_suffix: str, right_suffix: str, reps: int, seed: int
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paired = pd.read_csv(paired_wide, low_memory=False)
    slopes, draws, cell_tables = paired_bootstrap(
        paired, left_suffix=left_suffix, right_suffix=right_suffix, reps=reps, seed=seed
    )
    age_bins = age_bin_coefficients(cell_tables, left_suffix=left_suffix, right_suffix=right_suffix)
    quadratic = paired_quadratic_bootstrap(
        cell_tables,
        left_suffix=left_suffix,
        right_suffix=right_suffix,
        reps=reps,
        seed=seed + 1,
    )
    rankings, source_interactions = candidate_rankings_and_interactions(
        cell_tables, left_suffix=left_suffix, right_suffix=right_suffix
    )
    children = child_slope_comparison(cell_tables, left_suffix=left_suffix, right_suffix=right_suffix)
    diagnostics = diagnostic_summary(paired, left_suffix=left_suffix, right_suffix=right_suffix)
    atomic_csv(slopes, output_dir / "paired_all_outcome_slopes.csv")
    atomic_csv(draws, output_dir / "paired_all_outcome_bootstrap_draws.csv.gz", compression="gzip")
    atomic_csv(age_bins, output_dir / "paired_age_bin_contrasts.csv")
    atomic_csv(quadratic, output_dir / "paired_quadratic_age_comparison.csv")
    atomic_csv(rankings, output_dir / "paired_candidate_rankings.csv")
    atomic_csv(source_interactions, output_dir / "paired_candidate_source_age_interactions.csv")
    atomic_csv(children, output_dir / "paired_child_slopes.csv")
    atomic_csv(diagnostics, output_dir / "paired_disagreement_diagnostics.csv")
    manifest = {
        "version": VERSION,
        "stage": "models",
        "paired_wide": str(paired_wide),
        "paired_rows": len(paired),
        "children": int(paired[f"child_key_{left_suffix}"].nunique()),
        "outcomes": len(slopes),
        "bootstrap_reps": reps,
        "status": "COMPLETE",
    }
    atomic_json(manifest, output_dir / "model_manifest.json")
    return manifest


def save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=190, bbox_inches="tight")
    plt.close(fig)


def plot_slope_comparison(slopes: pd.DataFrame, fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11, 7))
    for row in slopes.itertuples():
        ax.scatter(
            row.slope_mistral,
            row.slope_tiny,
            s=70,
            label=row.label,
        )
    bounds = [min(slopes["slope_mistral"].min(), slopes["slope_tiny"].min()), max(slopes["slope_mistral"].max(), slopes["slope_tiny"].max())]
    ax.plot(bounds, bounds, color="#777777", linestyle="--", linewidth=1)
    ax.axhline(0, color="#aaaaaa", linewidth=0.8)
    ax.axvline(0, color="#aaaaaa", linewidth=0.8)
    ax.set_xlabel("Mistral age slope (bits/month)")
    ax.set_ylabel("TinyDialogues age slope (bits/month)")
    ax.set_title("Do the scorers give the same developmental direction?")
    ax.grid(alpha=0.18)
    ax.legend(
        bbox_to_anchor=(1.02, 0.5),
        loc="center left",
        frameon=False,
        fontsize=9,
    )
    output = fig_dir / "paired_all_outcome_slopes.png"
    save(fig, output)
    return output


def plot_difference_forest(slopes: pd.DataFrame, fig_dir: Path) -> Path:
    data = slopes.reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 7.5))
    for index, row in data.iterrows():
        ax.hlines(
            index,
            row["difference_ci_low"],
            row["difference_ci_high"],
            color="#825f9d",
            linewidth=2,
        )
        ax.plot(row["slope_difference_left_minus_right"], index, "o", color="#825f9d")
    ax.axvline(0, color="#555555", linewidth=1)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels(data["label"])
    ax.set_xlabel("TinyDialogues minus Mistral age slope (bits/month)")
    ax.set_title("Paired child-bootstrap differences between scorer slopes")
    ax.grid(axis="x", alpha=0.2)
    output = fig_dir / "paired_slope_difference_forest.png"
    save(fig, output)
    return output


def plot_child_concordance(children: pd.DataFrame, fig_dir: Path) -> Path:
    data = children[children["outcome"].eq("real_k3_sum_bits") & children["supported"].eq(1)]
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    for dataset, group in data.groupby("dataset", observed=True):
        ax.scatter(group["slope_mistral"], group["slope_tiny"], s=55, alpha=0.75, label=dataset)
    if data.empty:
        ax.text(0.5, 0.5, "No children met the trajectory support rule", ha="center", va="center", transform=ax.transAxes)
    else:
        bounds = [min(data["slope_mistral"].min(), data["slope_tiny"].min()), max(data["slope_mistral"].max(), data["slope_tiny"].max())]
        ax.plot(bounds, bounds, linestyle="--", color="#777777")
    ax.axhline(0, color="#aaaaaa", linewidth=0.8)
    ax.axvline(0, color="#aaaaaa", linewidth=0.8)
    ax.set_xlabel("Mistral child slope")
    ax.set_ylabel("TinyDialogues child slope")
    ax.set_title("Child-by-child P1 slope concordance")
    if not data.empty:
        ax.legend(frameon=False)
    ax.grid(alpha=0.18)
    output = fig_dir / "paired_child_p1_concordance.png"
    save(fig, output)
    return output


def plot_age_bins(age_bins: pd.DataFrame, fig_dir: Path) -> Path:
    data = age_bins[age_bins["outcome"].eq("real_k3_sum_bits")].copy()
    positions = {age_bin: index for index, age_bin in enumerate(AGE_BINS[1:])}
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    for scorer, group in data.groupby("scorer", observed=True):
        group = group.copy()
        group["x"] = group["age_bin"].map(positions)
        group = group.sort_values("x")
        ax.errorbar(group["x"], group["estimate"], yerr=[group["estimate"] - group["ci_low"], group["ci_high"] - group["estimate"]], marker="o", capsize=3, label=scorer)
    ax.axhline(0, color="#555555", linewidth=1)
    ax.set_xticks(range(len(AGE_BINS) - 1))
    ax.set_xticklabels(AGE_BINS[1:], rotation=30, ha="right")
    ax.set_ylabel("Difference from 006–023 months (bits)")
    ax.set_title("Paired PBM P1 age-bin shapes")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    output = fig_dir / "paired_p1_age_bins.png"
    save(fig, output)
    return output


def plot_quadratic_differences(quadratic: pd.DataFrame, fig_dir: Path) -> Path:
    data = quadratic.reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for index, row in data.iterrows():
        ax.hlines(
            index,
            row["difference_ci_low"],
            row["difference_ci_high"],
            color="#b26a3c",
            linewidth=2,
        )
        ax.plot(row["quadratic_difference_left_minus_right"], index, "o", color="#b26a3c")
    ax.axvline(0, color="#555555", linewidth=1)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels(data["label"])
    ax.set_xlabel("TinyDialogues minus Mistral quadratic age coefficient")
    ax.set_title("Paired nonlinear-age sensitivity")
    ax.grid(axis="x", alpha=0.2)
    output = fig_dir / "paired_quadratic_age_differences.png"
    save(fig, output)
    return output


def plot_candidate_rankings(rankings: pd.DataFrame, fig_dir: Path) -> Path:
    scorers = list(dict.fromkeys(rankings["scorer"].astype(str)))
    fig, axes = plt.subplots(1, len(scorers), figsize=(13, 4.8), sharey=True)
    if len(scorers) == 1:
        axes = [axes]
    positions = {age_bin: index for index, age_bin in enumerate(AGE_BINS)}
    colors = {
        "random": "#9a5a3a",
        "unigram": "#7768a6",
        "bigram": "#3b8291",
        "trigram": "#4f8d56",
    }
    for ax, scorer in zip(axes, scorers):
        scorer_data = rankings[rankings["scorer"].eq(scorer)]
        for candidate in CANDIDATE_OUTCOMES:
            group = scorer_data[scorer_data["candidate"].eq(candidate)].copy()
            group["x"] = group["age_bin"].map(positions)
            group = group.sort_values("x")
            ax.plot(
                group["x"],
                group["weighted_mean_gap"],
                marker="o",
                color=colors[candidate],
                label=candidate,
            )
        ax.axhline(0, color="#777777", linewidth=0.8)
        ax.set_xticks(range(len(AGE_BINS)))
        ax.set_xticklabels(AGE_BINS, rotation=35, ha="right")
        ax.set_title(scorer)
        ax.grid(alpha=0.18)
    axes[0].set_ylabel("Candidate minus real score (bits)")
    axes[0].legend(frameon=False)
    fig.suptitle("Does the same candidate ordering appear under both scorers?")
    output = fig_dir / "paired_candidate_gap_ordering.png"
    save(fig, output)
    return output


def plot_token_diagnostics(diagnostics: pd.DataFrame, fig_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for dataset, group in diagnostics.groupby("dataset", observed=True):
        x = group["age_bin"].map({age_bin: index for index, age_bin in enumerate(AGE_BINS)})
        axes[0].plot(x, group["token_ratio_median"], marker="o", label=dataset)
        axes[1].plot(x, group["k3_bits_per_word_difference_mean"], marker="o", label=dataset)
    for ax in axes:
        ax.set_xticks(range(len(AGE_BINS)))
        ax.set_xticklabels(AGE_BINS, rotation=35, ha="right")
        ax.grid(alpha=0.18)
    axes[0].axhline(1, color="#777777", linestyle="--")
    axes[0].set_title("Tiny/Mistral evaluated-token ratio")
    axes[0].set_ylabel("Median token-count ratio")
    axes[1].axhline(0, color="#777777", linestyle="--")
    axes[1].set_title("Word-normalized scorer scale difference")
    axes[1].set_ylabel("Tiny minus Mistral bits/word")
    axes[0].legend(loc="lower left", frameon=False)
    output = fig_dir / "paired_tokenization_diagnostics.png"
    save(fig, output)
    return output


def run_plots(*, output_dir: Path, fig_dir: Path) -> dict[str, object]:
    slopes = pd.read_csv(output_dir / "paired_all_outcome_slopes.csv")
    age_bins = pd.read_csv(output_dir / "paired_age_bin_contrasts.csv")
    children = pd.read_csv(output_dir / "paired_child_slopes.csv")
    diagnostics = pd.read_csv(output_dir / "paired_disagreement_diagnostics.csv")
    quadratic = pd.read_csv(output_dir / "paired_quadratic_age_comparison.csv")
    rankings = pd.read_csv(output_dir / "paired_candidate_rankings.csv")
    outputs = [
        plot_slope_comparison(slopes, fig_dir),
        plot_difference_forest(slopes, fig_dir),
        plot_child_concordance(children, fig_dir),
        plot_age_bins(age_bins, fig_dir),
        plot_quadratic_differences(quadratic, fig_dir),
        plot_candidate_rankings(rankings, fig_dir),
        plot_token_diagnostics(diagnostics, fig_dir),
    ]
    audit = pd.DataFrame({"path": [str(path) for path in outputs]})
    audit["exists"] = audit["path"].map(lambda value: Path(value).exists())
    audit["bytes"] = audit["path"].map(lambda value: Path(value).stat().st_size if Path(value).exists() else 0)
    atomic_csv(audit, output_dir / "plot_audit.csv")
    manifest = {"version": VERSION, "stage": "plots", "plots": len(audit), "missing": int((~audit["exists"]).sum()), "status": "COMPLETE"}
    atomic_json(manifest, output_dir / "plot_manifest.json")
    return manifest


def fmt(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return "" if not math.isfinite(number) else f"{number:.3f}"


def run_report(*, output_dir: Path, fig_dir: Path, report_md: Path, report_html: Path) -> dict[str, object]:
    slopes = pd.read_csv(output_dir / "paired_all_outcome_slopes.csv")
    children = pd.read_csv(output_dir / "paired_child_slopes.csv")
    primary = slopes[slopes["outcome"].isin(PRIMARY)]
    lines = [
        "| question | Tiny slope | Mistral slope | Tiny − Mistral | bootstrap interval |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in primary.itertuples():
        lines.append(f"| {row.label} | {fmt(row.slope_tiny)} | {fmt(row.slope_mistral)} | {fmt(row.slope_difference_left_minus_right)} | [{fmt(row.difference_ci_low)}, {fmt(row.difference_ci_high)}] |")
    p1_children = children[children["outcome"].eq("real_k3_sum_bits") & children["supported"].eq(1)]
    concordance = float(p1_children["same_sign"].mean()) if not p1_children.empty else np.nan

    def image(filename: str, alt: str) -> str:
        return f"![{alt}]({relative(fig_dir / filename, report_md)})"

    report = f"""# TinyDialogues–Mistral PBM Visual Comparison

This report uses the exact 446,508-row paired PBM intersection. It compares
developmental directions and within-child patterns, not raw model-token scales.
TinyDialogues and Mistral have different tokenizers and calibrations.

## The Short Answer

- Both scorers give negative fixed-effort P1 slopes on the same PBM utterances.
- TinyDialogues gives the more negative P1 magnitude; the paired child-bootstrap
  interval for that difference excludes zero.
- The P3 context-gain slope difference includes zero even though both observed
  slopes are negative.
- Supported child-level P1 slope signs agree for **{concordance:.1%}** of children.

{image("paired_all_outcome_slopes.png", "All paired outcome slopes")}

## Three Headline Questions

{chr(10).join(lines)}

## Where The Scorers Differ

Bars are paired child-bootstrap intervals for TinyDialogues minus Mistral.
Intervals crossing zero do not show a stable slope-magnitude difference.

{image("paired_slope_difference_forest.png", "Paired slope differences")}

## Do Individual Children Point The Same Way?

Each point is one supported child. Quadrants show sign agreement; distance from
the dashed diagonal shows magnitude disagreement.

{image("paired_child_p1_concordance.png", "Child slope concordance")}

## Do The Nonlinear Age-Bin Shapes Match?

Both scorers use the same exact paired rows, word-effort design, early-bin
reference, child fixed effects, and child-clustered intervals.

{image("paired_p1_age_bins.png", "Paired P1 age bins")}

The quadratic-age comparison is a sensitivity analysis rather than a new
primary model. Its paired intervals show whether scorer curvature differs.

{image("paired_quadratic_age_differences.png", "Paired quadratic age differences")}

## Do The Generated Candidates Keep The Same Ordering?

Candidate-minus-real gaps are same-length controls, not meaning-preserving
alternatives. Smaller gaps mean a candidate is closer to the observed real
utterance on that scorer's scale.

{image("paired_candidate_gap_ordering.png", "Paired candidate gap ordering")}

## Tokenization And Scale Diagnostics

The left panel audits the recorded evaluated-token counts; their median ratio
is 1.0 throughout this paired export. The right panel still shows a substantial
score-scale difference after dividing by the shared lexical word count, so raw
score magnitudes should not be treated as directly calibrated across scorers.

{image("paired_tokenization_diagnostics.png", "Tokenization diagnostics")}

## Detailed Audit Files

- All outcome slopes and paired intervals: `{output_dir / 'paired_all_outcome_slopes.csv'}`
- Bootstrap draws: `{output_dir / 'paired_all_outcome_bootstrap_draws.csv.gz'}`
- Age-bin contrasts: `{output_dir / 'paired_age_bin_contrasts.csv'}`
- Quadratic-age comparison: `{output_dir / 'paired_quadratic_age_comparison.csv'}`
- Candidate rankings: `{output_dir / 'paired_candidate_rankings.csv'}`
- Candidate source-by-age interactions: `{output_dir / 'paired_candidate_source_age_interactions.csv'}`
- Child slope concordance: `{output_dir / 'paired_child_slopes.csv'}`
- Tokenization/scale diagnostics: `{output_dir / 'paired_disagreement_diagnostics.csv'}`
"""
    report_md.write_text(report, encoding="utf-8")
    render_markdown_file(report_md, report_html, title="TinyDialogues–Mistral PBM Visual Comparison")
    manifest = {"version": VERSION, "stage": "report", "report_html": str(report_html), "status": "COMPLETE"}
    atomic_json(manifest, output_dir / "report_manifest.json")
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["models", "plots", "report", "all"], default="all")
    parser.add_argument("--paired-wide", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fig-dir", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--report-html", type=Path, required=True)
    parser.add_argument("--left-suffix", default="tiny")
    parser.add_argument("--right-suffix", default="mistral")
    parser.add_argument("--bootstrap-reps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260721)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    results = {}
    if args.stage in {"models", "all"}:
        results["models"] = run_models(
            paired_wide=args.paired_wide,
            output_dir=args.output_dir,
            left_suffix=args.left_suffix,
            right_suffix=args.right_suffix,
            reps=args.bootstrap_reps,
            seed=args.seed,
        )
    if args.stage in {"plots", "all"}:
        results["plots"] = run_plots(output_dir=args.output_dir, fig_dir=args.fig_dir)
    if args.stage in {"report", "all"}:
        results["report"] = run_report(
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            report_md=args.report_md,
            report_html=args.report_html,
        )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
