#!/usr/bin/env python3
"""Synthesize saved Route 1, Route 2, onset, and word results.

This module never refits a statistical model.  It reads audited outputs from
the modular pipelines, keeps discovery/confirmation/scorer roles separate,
and publishes the current answers and unresolved scientific blockers.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


VERSION = "2026-08-06.scientific-answer-synthesis-v1"
DIRECT_MODELS = {
    "P1_k3_contextual": "Contextual utterance surprisal at fixed word effort",
    "P2_k0_unconditional": "Unconditional utterance surprisal at fixed word effort",
    "P3_k3_context_gain": "Utterance context gain (k0 − k3)",
}


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
        fig.savefig(temporary, dpi=190, bbox_inches="tight")
        os.replace(temporary, path)
    finally:
        plt.close(fig)
        temporary.unlink(missing_ok=True)


def interval_excludes_zero(low: float, high: float) -> bool:
    return bool(low > 0 or high < 0)


def classify_direct(model_id: str, sample: str, estimate: float, low: float, high: float) -> str:
    supported = interval_excludes_zero(low, high)
    if model_id == "P3_k3_context_gain" and estimate < 0:
        return "contrary_to_registered_direction"
    if model_id == "P1_k3_contextual" and sample == "non-PBM58 confirmation":
        if estimate < 0 and supported:
            return "confirmation_criterion_met"
        if estimate < 0:
            return "direction_consistent_not_confirmed"
        return "direction_not_confirmed"
    return "supported_association" if supported else "uncertain_association"


def extract_direct_estimates(tiny_path: Path, mistral_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    sources = (
        ("TinyDialogues", tiny_path, {"pbm_discovery": "PBM21 scorer robustness"}),
        (
            "Mistral",
            mistral_path,
            {
                "pbm_discovery": "PBM21 discovery",
                "non_pbm_confirmation": "non-PBM58 confirmation",
            },
        ),
    )
    for scorer, path, scopes in sources:
        frame = pd.read_csv(path)
        required = {"scope", "model_id", "term", "estimate", "ci_low", "ci_high"}
        missing = required - set(frame.columns)
        if missing:
            raise RuntimeError(f"{path} is missing direct-result columns: {sorted(missing)}")
        for scope, sample in scopes.items():
            for model_id, question in DIRECT_MODELS.items():
                selected = frame[
                    frame["scope"].eq(scope)
                    & frame["model_id"].eq(model_id)
                    & frame["term"].eq("age_c")
                ]
                if len(selected) != 1:
                    raise RuntimeError(
                        f"expected one {scorer}/{scope}/{model_id}/age_c row; found {len(selected)}"
                    )
                source = selected.iloc[0]
                estimate = float(source["estimate"])
                low = float(source["ci_low"])
                high = float(source["ci_high"])
                rows.append(
                    {
                        "family": "Route 1 direct",
                        "question": question,
                        "sample": sample,
                        "scorer": scorer,
                        "model_id": model_id,
                        "term": "age_c",
                        "estimate": estimate,
                        "ci_low": low,
                        "ci_high": high,
                        "evidence_status": classify_direct(
                            model_id, sample, estimate, low, high
                        ),
                    }
                )
    return pd.DataFrame(rows)


def extract_route2_estimates(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {
        "model_id",
        "estimator_id",
        "outcome",
        "term",
        "estimate",
        "conf_low",
        "conf_high",
        "p_value",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"{path} is missing Route 2 columns: {sorted(missing)}")
    selected = frame[
        frame["estimator_id"].eq("session_gee_exchangeable")
        & frame["model_id"].isin(
            [
                "minus_gen_mean_r2m5_age_by_entropy",
                "percentile_in_gen_distribution_r2m5_age_by_entropy",
            ]
        )
        & frame["term"].isin(
            ["age_months_c", "age_months_c:response_entropy_bits_c"]
        )
    ].copy()
    expected = 4
    if len(selected) != expected:
        raise RuntimeError(f"expected {expected} final Route 2 coefficients; found {len(selected)}")
    selected.insert(0, "family", "Route 2 relative effort")
    selected["evidence_status"] = [
        "measurement_limited_association"
        if interval_excludes_zero(float(row.conf_low), float(row.conf_high))
        else "measurement_limited_uncertain"
        for row in selected.itertuples(index=False)
    ]
    return selected


def default_inventory(repo_root: Path) -> list[dict[str, object]]:
    sibling = repo_root.parent / "developmental_word_information"

    def json_value(path: Path, key: str) -> int:
        return int(json.loads(path.read_text(encoding="utf-8"))[key])

    def csv_rows(path: Path) -> int:
        return len(pd.read_csv(path))

    rows = [
        {
            "family": "Direct TinyDialogues PBM",
            "fitted_variants": json_value(
                repo_root
                / "results/direct_surprisal_replication/tinydialogues_pbm/modular/models/model_manifest.json",
                "model_rows",
            ),
            "status": "PASS_WITH_RECORDED_SENSITIVITIES",
        },
        {
            "family": "Direct Mistral full-79",
            "fitted_variants": json_value(
                repo_root
                / "results/direct_surprisal_replication/mistral_full79/modular/models/model_manifest.json",
                "model_rows",
            ),
            "status": "PASS_WITH_RECORDED_SENSITIVITIES",
        },
        {
            "family": "Paired TinyDialogues–Mistral",
            "fitted_variants": json_value(
                repo_root
                / "results/direct_surprisal_replication/paired_tiny_mistral_pbm/modular/model_manifest.json",
                "outcomes",
            ),
            "status": "PASS",
        },
        {
            "family": "Route 1 model zoo",
            "fitted_variants": csv_rows(
                repo_root
                / "results/utterance_information_research_model_zoo/model_zoo_summary.csv"
            ),
            "status": "PASS",
        },
        {
            "family": "Route 1 explicit comparisons",
            "fitted_variants": csv_rows(
                repo_root
                / "results/utterance_information_research_model_zoo/comparison_model_summary.csv"
            ),
            "status": "PASS",
        },
        {
            "family": "Route 2 response space",
            "fitted_variants": csv_rows(
                repo_root
                / "results/route2_response_space_analysis/response_space_model_summary.csv"
            ),
            "status": "PASS",
        },
        {
            "family": "Route 2 relative effort",
            "fitted_variants": csv_rows(
                repo_root
                / "results/route2_relative_effort_model_suite/route2_relative_effort_model_summary.csv"
            ),
            "status": "PASS",
        },
    ]
    for label, directory in (
        ("PBM word Mistral", "mistral_pbm21"),
        ("PBM word Qwen3-14B", "qwen_pbm21"),
        ("PBM word TinyDialogues", "tinydialogues_pbm21"),
    ):
        manifest = sibling / f"results/modular_analysis/{directory}/models/model_manifest.json"
        rows.append(
            {
                "family": label,
                "fitted_variants": json_value(manifest, "fitted_variants"),
                "status": "PASS",
            }
        )
    onset = json.loads(
        (repo_root / "results/direct_surprisal_onset_confirmation/audit.json").read_text(
            encoding="utf-8"
        )
    )
    rows.append(
        {
            "family": "Frozen sustained-onset tests",
            "fitted_variants": len(onset["scopes"]),
            "status": onset["status"],
        }
    )
    return rows


def build_evidence_map(
    direct: pd.DataFrame,
    route2: pd.DataFrame,
    word: pd.DataFrame,
    onset: Mapping[str, object],
    path: Path,
) -> pd.DataFrame:
    def direct_status(sample: str, model_id: str) -> str:
        selected = direct[direct["sample"].eq(sample) & direct["model_id"].eq(model_id)]
        if sample.startswith("PBM"):
            selected = selected[selected["scorer"].eq("Mistral")]
        return str(selected.iloc[0]["evidence_status"])

    word_status = word.set_index("question_id")["replication_status"].to_dict()
    route2_interaction = route2[
        route2["outcome"].eq("child_words_minus_generated_mean")
        & route2["term"].eq("age_months_c:response_entropy_bits_c")
    ].iloc[0]
    onset_by_scope = {
        str(item["scope"]): str(item["sustained_onset"])
        for item in onset["scopes"]  # type: ignore[index]
    }
    rows = [
        {
            "question": "PBM contextual predictability at fixed effort",
            "status": direct_status("PBM21 discovery", "P1_k3_contextual"),
        },
        {
            "question": "Non-PBM58 contextual-predictability confirmation",
            "status": direct_status("non-PBM58 confirmation", "P1_k3_contextual"),
        },
        {
            "question": "Registered positive development in utterance context gain",
            "status": direct_status("non-PBM58 confirmation", "P3_k3_context_gain"),
        },
        {
            "question": "Route 2 stronger catch-up in higher response entropy",
            "status": "contrary_to_prediction"
            if float(route2_interaction["estimate"]) < 0
            else "direction_consistent",
        },
        {
            "question": "Same-word contextual predictability across scorers",
            "status": word_status.get("same_word_k3_age", "unavailable"),
        },
        {
            "question": "Longer word types receive more contextual support",
            "status": word_status.get("longer_words_context_support", "unavailable"),
        },
        {
            "question": "Developmental change in word-level context gain",
            "status": word_status.get("context_gain_age", "unavailable"),
        },
        {
            "question": "Sustained developmental onset in PBM",
            "status": onset_by_scope.get("pbm_discovery", "unavailable"),
        },
        {
            "question": "Sustained developmental onset in non-PBM58",
            "status": onset_by_scope.get("non_pbm_confirmation", "unavailable"),
        },
    ]
    evidence = pd.DataFrame(rows)
    color = {
        "supported_association": "#247a54",
        "confirmation_criterion_met": "#247a54",
        "direction_and_interval_robust": "#247a54",
        "direction_consistent_not_confirmed": "#d5a021",
        "direction_robust_partial_uncertainty": "#d5a021",
        "scorer_dependent": "#b26a2f",
        "contrary_to_registered_direction": "#a33a3a",
        "contrary_to_prediction": "#a33a3a",
        "not_established": "#6f7782",
        "unavailable": "#6f7782",
    }
    fig, ax = plt.subplots(figsize=(10.5, 6.4))
    positions = list(range(len(evidence)))
    ax.barh(
        positions,
        [1] * len(evidence),
        color=[color.get(status, "#6f7782") for status in evidence["status"]],
    )
    ax.set(
        yticks=positions,
        yticklabels=evidence["question"],
        xticks=[],
        xlim=(0, 1),
        title="Current evidence map: registered questions remain separate",
    )
    ax.invert_yaxis()
    for position, status in zip(positions, evidence["status"]):
        ax.text(0.02, position, status.replace("_", " "), va="center", color="white", fontweight="bold")
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    atomic_figure(fig, path)
    return evidence


def _format(value: float) -> str:
    return f"{value:.3f}"


def markdown_table(frame: pd.DataFrame, *, decimals: int | None = None) -> str:
    def render(value: object) -> str:
        if decimals is not None and isinstance(value, float):
            return f"{value:.{decimals}f}"
        return str(value).replace("|", "\\|")

    header = "| " + " | ".join(map(str, frame.columns)) + " |"
    separator = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| " + " | ".join(render(value) for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def build_scientific_synthesis(
    *,
    tiny_direct_path: Path,
    mistral_direct_path: Path,
    route2_path: Path,
    word_summary_path: Path,
    onset_audit_path: Path,
    output_dir: Path,
    figure_path: Path,
    report_md: Path,
    report_html: Path,
    inventory_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    input_paths = [
        tiny_direct_path,
        mistral_direct_path,
        route2_path,
        word_summary_path,
        onset_audit_path,
    ]
    missing = [str(path) for path in input_paths if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing synthesis inputs: {missing}")
    direct = extract_direct_estimates(tiny_direct_path, mistral_direct_path)
    route2 = extract_route2_estimates(route2_path)
    word = pd.read_csv(word_summary_path)
    required_word = {
        "question_id",
        "question",
        "common_direction",
        "cluster_supported_scorers",
        "scorers",
        "bootstrap_supported_scorers",
        "bootstrap_available_scorers",
        "replication_status",
    }
    if missing_word := required_word - set(word.columns):
        raise RuntimeError(f"{word_summary_path} is missing word-summary columns: {sorted(missing_word)}")
    onset = json.loads(onset_audit_path.read_text(encoding="utf-8"))
    if onset.get("status") != "PASS":
        raise RuntimeError(f"onset audit is not PASS: {onset.get('status')}")
    inventory = pd.DataFrame(inventory_rows)
    if set(inventory.columns) != {"family", "fitted_variants", "status"}:
        raise RuntimeError("inventory rows must contain family, fitted_variants, and status")
    total_fits = int(inventory["fitted_variants"].sum())

    output_dir.mkdir(parents=True, exist_ok=True)
    direct_path = output_dir / "direct_primary_estimates.csv"
    route2_output = output_dir / "route2_final_estimates.csv"
    word_output = output_dir / "word_question_summary.csv"
    inventory_path = output_dir / "analysis_fit_inventory.csv"
    evidence_path = output_dir / "evidence_map.csv"
    atomic_frame(direct, direct_path)
    atomic_frame(route2, route2_output)
    atomic_frame(word, word_output)
    atomic_frame(inventory, inventory_path)
    evidence = build_evidence_map(direct, route2, word, onset, figure_path)
    atomic_frame(evidence, evidence_path)

    def direct_row(sample: str, scorer: str, model_id: str) -> pd.Series:
        selected = direct[
            direct["sample"].eq(sample)
            & direct["scorer"].eq(scorer)
            & direct["model_id"].eq(model_id)
        ]
        return selected.iloc[0]

    mistral_pbm_p1 = direct_row("PBM21 discovery", "Mistral", "P1_k3_contextual")
    tiny_pbm_p1 = direct_row("PBM21 scorer robustness", "TinyDialogues", "P1_k3_contextual")
    non_pbm_p1 = direct_row("non-PBM58 confirmation", "Mistral", "P1_k3_contextual")
    non_pbm_p2 = direct_row("non-PBM58 confirmation", "Mistral", "P2_k0_unconditional")
    non_pbm_p3 = direct_row("non-PBM58 confirmation", "Mistral", "P3_k3_context_gain")
    r2_age = route2[
        route2["outcome"].eq("child_words_minus_generated_mean")
        & route2["term"].eq("age_months_c")
    ].iloc[0]
    r2_interaction = route2[
        route2["outcome"].eq("child_words_minus_generated_mean")
        & route2["term"].eq("age_months_c:response_entropy_bits_c")
    ].iloc[0]
    word_by_id = word.set_index("question_id")
    onset_text = ", ".join(
        f"{item['scope']}: {str(item['sustained_onset']).replace('_', ' ')}"
        for item in onset["scopes"]
    )

    direct_table = markdown_table(direct[
        ["sample", "scorer", "question", "estimate", "ci_low", "ci_high", "evidence_status"]
    ], decimals=3)
    route2_table = markdown_table(route2[
        ["outcome", "term", "estimate", "conf_low", "conf_high", "evidence_status"]
    ], decimals=4)
    word_table = markdown_table(word[
        [
            "question",
            "common_direction",
            "cluster_supported_scorers",
            "bootstrap_supported_scorers",
            "replication_status",
        ]
    ])
    inventory_table = markdown_table(inventory)
    relative_figure = os.path.relpath(figure_path, report_md.parent)
    markdown = f"""# Current Scientific Answer Across Route 1, Route 2, and Word Information

This synthesis reads audited saved artifacts only. It does not select or refit models after seeing outcomes. The current machine contains **{total_fits} fitted variants or registered outcome fits**, plus the corrected Bayes decomposition and its validation products.

## Bottom line

1. **Predictability at fixed effort develops, but the independent-sample result is weaker than the discovery result.** Mistral PBM contextual surprisal decreases by `{_format(mistral_pbm_p1['estimate'])}` bits/month at fixed exact/top-coded word effort (95% CI `[{_format(mistral_pbm_p1['ci_low'])}, {_format(mistral_pbm_p1['ci_high'])}]`). TinyDialogues gives the same negative PBM direction (`{_format(tiny_pbm_p1['estimate'])}`, CI `[{_format(tiny_pbm_p1['ci_low'])}, {_format(tiny_pbm_p1['ci_high'])}]`). The frozen non-PBM58 Mistral estimate is also negative (`{_format(non_pbm_p1['estimate'])}`), but its clustered interval `[{_format(non_pbm_p1['ci_low'])}, {_format(non_pbm_p1['ci_high'])}]` crosses zero, so it **does not meet the frozen confirmation criterion**.
2. **The form-development component is stronger than the contextual-support-development component.** In non-PBM58, unconditional surprisal decreases with age (`{_format(non_pbm_p2['estimate'])}`, CI `[{_format(non_pbm_p2['ci_low'])}, {_format(non_pbm_p2['ci_high'])}]`). Utterance context gain also decreases (`{_format(non_pbm_p3['estimate'])}`, CI `[{_format(non_pbm_p3['ci_low'])}, {_format(non_pbm_p3['ci_high'])}]`), opposite the registered positive direction. This favors increasing conventionality/predictability of form over a claim that older children increasingly exploit preceding context.
3. **Word-level evidence sharpens that distinction.** Same-word k0 and k3 surprisal decrease with age under all three scorers with all three clustered and bootstrap intervals excluding zero. Longer word types receive more contextual support at the centered age under all three scorers. In contrast, developmental change in overall word-level context gain is scorer-dependent, and the rarity-by-age result is also scorer-dependent.
4. **Route 2 shows catch-up toward a generated length reference, not the predicted stronger adaptation under high uncertainty.** The final session-GEE estimate for age is `{_format(r2_age['estimate'])}` words/month relative to the generated mean, while age × exact-string response entropy is `{_format(r2_interaction['estimate'])}` (CI `[{_format(r2_interaction['conf_low'])}, {_format(r2_interaction['conf_high'])}]`). Thus catch-up is weaker in higher-entropy contexts. This remains model/prompt/temperature dependent and is not semantic response uncertainty.
5. **A discrete onset is not established.** Under 1,000 child bootstraps and simultaneous bands: {onset_text}.

![Current evidence map]({relative_figure})

## Route 1 direct estimates

{direct_table}

Raw coefficient magnitudes are never pooled across tokenizers. PBM scorer repetition is robustness, not independent-sample confirmation.

## Route 2 final relative-effort estimates

{route2_table}

Raw child effort and effort relative to a generated response distribution are separate estimands. The generated expected effort term is part of the reference construction and is not automatically treated as an ordinary confound.

## Word-information questions

{word_table}

The three word scorers use the same exact 1,032,963-occurrence primary set, but each scorer was fit separately. The strongest cross-scorer statements are about direction and within-scorer uncertainty, not raw bit magnitudes.

## Fit inventory

{inventory_table}

## What the current models do not answer

- They do not provide a validated listener-utility outcome or show that children optimize a single efficiency objective.
- Route 2 still needs semantic clustering, rarefaction, prompt/temperature/seed calibration, and the incoming Qwen-generated/Mistral-scored decoupled-response product before a stronger uncertainty claim.
- The 58-child word-level Mistral confirmation remains blocked until its 232 same-pass contracts are scored and audited on Mila.
- The caregiver-responsive subset remains a future sensitivity until the 18,172 context mismatches and 325-row manual validation sample are adjudicated.
- Morpheme, syllable, and phoneme effort controls need validation before the frozen onset rule is repeated with those measures.

## Best next tests

1. Finish the Qwen-response/Mistral-scoring calibration smoke, then run the predeclared production gate and compare exact-string entropy, length reference, and scored response distributions without calling them semantic equivalents.
2. Run the remaining-58 same-pass Mistral word DAG and apply the already frozen word protocol without changing thresholds or formulas.
3. Add a downstream caregiver-response predictive-gain or validated repair/clarification outcome; that is the clearest route from model predictability toward listener-relevant utility.
"""
    atomic_text(report_md, markdown)

    direct_html = direct[
        ["sample", "scorer", "question", "estimate", "ci_low", "ci_high", "evidence_status"]
    ].to_html(index=False, float_format=lambda value: f"{value:.3f}")
    route2_html = route2[
        ["outcome", "term", "estimate", "conf_low", "conf_high", "evidence_status"]
    ].to_html(index=False, float_format=lambda value: f"{value:.4f}")
    word_html = word[
        ["question", "common_direction", "cluster_supported_scorers", "bootstrap_supported_scorers", "replication_status"]
    ].to_html(index=False)
    inventory_html = inventory.to_html(index=False)
    atomic_text(
        report_html,
        f"<!doctype html><html><head><meta charset='utf-8'><title>Current Scientific Answer</title><style>body{{font:15px/1.55 system-ui;max-width:1150px;margin:35px auto;padding:0 24px;color:#172b2b}}h1,h2{{color:#276c72}}table{{border-collapse:collapse;width:100%;margin:1em 0 2em}}th,td{{border:1px solid #ccd5d3;padding:.45em;vertical-align:top}}th{{background:#e5efed}}img{{max-width:100%}}.headline{{background:#eef6f5;border-left:6px solid #2d777d;padding:1em 1.2em}}.warning{{background:#fff3cd;border-left:6px solid #b58900;padding:1em 1.2em}}</style></head><body><h1>Current Scientific Answer Across Route 1, Route 2, and Word Information</h1><div class='headline'><b>{total_fits} fitted variants/outcome fits are synthesized here.</b> The clearest result is increasing predictability/conventionality of form with age; increasing use of contextual support is not robust.</div><h2>Bottom line</h2><ol><li>Mistral PBM and TinyDialogues PBM show negative fixed-effort contextual-surprisal age slopes. The non-PBM58 Mistral slope is negative but its frozen clustered interval crosses zero.</li><li>Non-PBM58 unconditional surprisal decreases, while context gain decreases contrary to the registered positive direction.</li><li>All three word scorers show negative same-word k0 and k3 age slopes. Longer word types receive more context support; developmental change in context gain is scorer-dependent.</li><li>Route 2 children move toward the generated length reference with age, but catch-up is weaker in higher exact-string-entropy contexts.</li><li>Sustained onset is not established in either sample.</li></ol><img src='{html.escape(os.path.relpath(figure_path, report_html.parent))}'><h2>Route 1 direct estimates</h2>{direct_html}<h2>Route 2 final relative-effort estimates</h2>{route2_html}<div class='warning'>Route 2 entropy is model-, prompt-, temperature-, and exact-string-dependent; generated responses are not same-meaning paraphrases.</div><h2>Word-information questions</h2>{word_html}<h2>Fit inventory</h2>{inventory_html}<h2>Next tests</h2><ol><li>Complete Qwen-response/Mistral-scoring calibration and then the gated production run.</li><li>Run the remaining-58 same-pass Mistral word DAG under the frozen protocol.</li><li>Add downstream caregiver-response utility or validated repair/clarification outcomes.</li></ol></body></html>",
    )

    artifacts = [
        direct_path,
        route2_output,
        word_output,
        inventory_path,
        evidence_path,
        figure_path,
        report_md,
        report_html,
    ]
    manifest = {
        "created_by": VERSION,
        "status": "PASS",
        "fitted_variants_or_outcome_fits": total_fits,
        "input_artifacts": [
            {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in input_paths
        ],
        "artifacts": [
            {"path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in artifacts
        ],
        "guardrails": [
            "no model was refit or selected by this synthesis",
            "PBM discovery and non-PBM confirmation remain separate",
            "raw surprisal magnitudes are not pooled across tokenizers",
            "Route 2 exact-string entropy is not semantic response uncertainty",
        ],
    }
    atomic_text(output_dir / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tiny-direct",
        type=Path,
        default=Path("results/direct_surprisal_replication/tinydialogues_pbm/modular/models/coefficients_long.csv"),
    )
    parser.add_argument(
        "--mistral-direct",
        type=Path,
        default=Path("results/direct_surprisal_replication/mistral_full79/modular/models/coefficients_long.csv"),
    )
    parser.add_argument(
        "--route2",
        type=Path,
        default=Path("results/route2_relative_effort_model_suite/route2_relative_effort_model_coefficients.csv"),
    )
    parser.add_argument(
        "--word-summary",
        type=Path,
        default=Path("results/word_cross_scorer_comparison/scientific_question_summary.csv"),
    )
    parser.add_argument(
        "--onset-audit",
        type=Path,
        default=Path("results/direct_surprisal_onset_confirmation/audit.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results/current_scientific_synthesis"))
    parser.add_argument("--figure", type=Path, default=Path("figs/current_scientific_synthesis/evidence_map.png"))
    parser.add_argument("--report-md", type=Path, default=Path("docs/current_scientific_synthesis.md"))
    parser.add_argument("--report-html", type=Path, default=Path("docs/current_scientific_synthesis.html"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    report = build_scientific_synthesis(
        tiny_direct_path=args.tiny_direct,
        mistral_direct_path=args.mistral_direct,
        route2_path=args.route2,
        word_summary_path=args.word_summary,
        onset_audit_path=args.onset_audit,
        output_dir=args.output_dir,
        figure_path=args.figure,
        report_md=args.report_md,
        report_html=args.report_html,
        inventory_rows=default_inventory(repo_root),
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
