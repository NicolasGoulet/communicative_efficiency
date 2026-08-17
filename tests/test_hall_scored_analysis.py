from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.audit_hall_scored_archive import audit_scored_archive
from src.build_hall_snapshot_analysis import (
    build_dataset_stage,
    fit_weighted_cluster_model,
    run_plot_stage,
    run_report_stage,
    run_final_audit,
)


MODEL_REVISION = "caa1feb0e54d415e2df31207e5f4e273e33509b1"
CODE_REVISION = "66812c461e878d3ff52dec542255c2dc537b5ed9"
MODEL_SLUG = "mistralai__Mistral-7B-v0.3__caa1feb0e54d"


def _csv_bytes(frame: pd.DataFrame, *, compressed: bool = False) -> bytes:
    raw = frame.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return gzip.compress(raw, mtime=0) if compressed else raw


def _json_bytes(payload: dict[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_archive(path: Path, *, unsafe_member: bool = False) -> dict[str, int | str]:
    source = pd.DataFrame(
        [
            {
                "dataset": "Hall", "child_id": "h1", "source_group": "BlackPro",
                "race": "Black", "social_class": "UC", "stratum": "Black_UC",
                "demographic_source": "chi_id", "primary_eligible": 1,
                "sensitivity_eligible": 1, "age_raw": "4;09.", "age_months": 57,
                "sex": "male", "file": "BlackPro/h1.cha", "line_no": 10,
                "utterance_id": "Hall|h1|BlackPro/h1.cha|10", "situation_id": 1,
                "situation_text": "home", "setting_auto": "home",
                "setting_review_required": 0, "previous_main_speaker": "MOT",
                "previous_main_role_group": "adult_interlocutor", "child_after_adult": 1,
                "context_k1": "hello", "context_k2": "hello", "context_k3": "hello",
                "chi_utterance_clean": "yes please", "nb_words": 2, "nb_characters": 10,
            },
            {
                "dataset": "Hall", "child_id": "h2", "source_group": "WhiteWork",
                "race": "White", "social_class": "WC", "stratum": "White_WC",
                "demographic_source": "chi_id", "primary_eligible": 1,
                "sensitivity_eligible": 1, "age_raw": "4;08.", "age_months": 56,
                "sex": "female", "file": "WhiteWork/h2.cha", "line_no": 20,
                "utterance_id": "Hall|h2|WhiteWork/h2.cha|20", "situation_id": 2,
                "situation_text": "school", "setting_auto": "school",
                "setting_review_required": 0, "previous_main_speaker": "CHI",
                "previous_main_role_group": "target_child", "child_after_adult": 0,
                "context_k1": "", "context_k2": "", "context_k3": "",
                "chi_utterance_clean": "okay", "nb_words": 1, "nb_characters": 4,
            },
        ]
    )
    source_bytes = _csv_bytes(source)
    members: dict[str, bytes] = {
        "prepared/hall_snapshot_mistral_real_k0_k3_v1/inputs/hall_child_snapshot_scoring.csv": source_bytes,
        "WORD_SURPRISAL_COMPLETE": b"WORD_SURPRISAL_COMPLETE\n",
        "reports/final/FINAL_AUDIT_PASSED": b"FINAL_AUDIT_PASSED\n",
    }
    totals = {"utterance_rows": 0, "word_rows": 0, "token_rows": 0, "allocation_rows": 0}
    for index, context in enumerate(("k0", "k1", "k2", "k3")):
        available = [True, False] if context != "k0" else [True, True]
        sum_bits = [20.0 - index, 10.0]
        utterances = pd.DataFrame(
            {
                "source_row": [0, 1],
                "target_occurrence_id": ["target-0", "target-1"],
                "utterance_score_id": [f"score-{context}-0", f"score-{context}-1"],
                "dataset": ["Hall", "Hall"],
                "child_id": ["h1", "h2"],
                "file": ["BlackPro/h1.cha", "WhiteWork/h2.cha"],
                "line_no": [10, 20],
                "utterance_id": source["utterance_id"],
                "corpus": ["Hall", "Hall"],
                "child": ["all_children", "all_children"],
                "child_key": ["Hall/all_children", "Hall/all_children"],
                "mode": ["real", "real"],
                "context_window": [context, context],
                "context_available": available,
                "target_text": source["chi_utterance_clean"],
                "context_text": (["", ""] if context == "k0" else ["hello", ""]),
                "score_status": ["scored", "scored"],
                "utterance_word_count_cleaned": source["nb_words"],
                "utterance_sum_bits": sum_bits,
                "utterance_mean_bits_per_token": [5.0 - index / 4, 5.0],
                "utterance_bits_per_word": [sum_bits[0] / 2, sum_bits[1]],
                "utterance_bits_per_character": [2.0, 2.5],
                "utterance_eval_tokens": [4, 2],
                "assigned_word_bits": [18.0 - index, 9.0],
                "unassigned_target_bits": [2.0, 1.0],
                "assigned_token_coverage": [0.75, 0.5],
                "n_context_tokens_truncated": [0, 0],
                "model_key": ["mistral-7b-v0.3"] * 2,
                "model_id": ["mistralai/Mistral-7B-v0.3"] * 2,
                "model_revision": [MODEL_REVISION] * 2,
                "tokenizer_revision": [MODEL_REVISION] * 2,
                "scoring_code_revision": [CODE_REVISION] * 2,
                "dtype": ["fp16"] * 2,
                "max_length": [4096] * 2,
                "source_manifest_sha256": ["manifest-sha"] * 2,
                "runtime_sha256": ["runtime-sha"] * 2,
            }
        )
        products = {
            "utterances.csv.gz": _csv_bytes(utterances, compressed=True),
            "words.csv.gz": _csv_bytes(pd.DataFrame({"word_score_id": [f"word-{context}"], "source_row": [0]}), compressed=True),
            "tokens.csv.gz": _csv_bytes(pd.DataFrame({"token_score_id": [f"token-{context}"], "source_row": [0]}), compressed=True),
            "token_word_allocations.csv.gz": _csv_bytes(pd.DataFrame({"allocation_id": [f"allocation-{context}"], "source_row": [0]}), compressed=True),
        }
        base = f"outputs/{MODEL_SLUG}/Hall/all_children/real_{context}.word_surprisal"
        for name, data in products.items():
            members[f"{base}/{name}"] = data
        summary = {
            "status": "COMPLETE", "contract_id": index, "context_window": context,
            "source_rows": 2, "scored_utterance_rows": 2, "utterance_rows": 2,
            "word_rows": 1, "token_rows": 1, "allocation_rows": 1,
            "score_unavailable_context_as_k0": True,
            "source_sha256": _sha(source_bytes),
            "model_key": "mistral-7b-v0.3", "word_level": True,
            "artifacts": {
                name: {"bytes": len(data), "sha256": _sha(data)}
                for name, data in products.items()
            },
            "provenance": {
                "model_id": "mistralai/Mistral-7B-v0.3",
                "model_revision": MODEL_REVISION,
                "scoring_code_revision": CODE_REVISION,
                "dtype": "fp16", "max_length": 4096,
                "runtime_sha256": "runtime-sha",
            },
        }
        members[f"{base}/contract_summary.json"] = _json_bytes(summary)
        members[f"{base}/CONTRACT_COMPLETE"] = b"CONTRACT_COMPLETE\n"
        for key in totals:
            totals[key] += int(summary[key])
    final = {
        "status": "PASS", "problem_count": 0, "audited_contracts": 4,
        "contexts": ["k0", "k1", "k2", "k3"], "model_id": "mistralai/Mistral-7B-v0.3",
        "model_revision": MODEL_REVISION, "code_revision": CODE_REVISION,
        "dtype": "fp16", "batch_size": 16, "max_length": 4096,
        "word_level": True, "blank_context_policy": "score_target_only_and_retain_context_available_false",
        "blank_context_comparison_rows": 3,
        "blank_context_max_abs_mean_bits_diff": 0.0,
        "blank_context_max_abs_sum_bits_diff": 0.0,
        **totals,
    }
    members["reports/final/final_report.json"] = _json_bytes(final)
    if unsafe_member:
        members["../escape.txt"] = b"bad"
    with tarfile.open(path, "w:gz") as archive:
        for name in sorted(members):
            info = tarfile.TarInfo(name)
            info.size = len(members[name])
            archive.addfile(info, io.BytesIO(members[name]))
    return {"archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "source_sha256": _sha(source_bytes), **totals}


class HallScoredArchiveTests(unittest.TestCase):
    def test_relocation_audit_checks_hash_contracts_rows_and_cross_context_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "hall.tar.gz"
            expected = make_archive(archive)
            report = audit_scored_archive(
                archive_path=archive,
                output_dir=root / "audit",
                expected_archive_sha256=str(expected["archive_sha256"]),
                expected_input_sha256=str(expected["source_sha256"]),
                expected_rows=2,
                expected_totals={key: int(expected[key]) for key in ("utterance_rows", "word_rows", "token_rows", "allocation_rows")},
            )
            saved = json.loads((root / "audit/local_retrieval_audit.json").read_text())

        self.assertEqual(report, saved)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["audited_contracts"], 4)
        self.assertEqual(report["blank_context_rows_per_nonzero_context"], 1)
        self.assertEqual(report["problem_count"], 0)

    def test_relocation_audit_rejects_unsafe_tar_member(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "hall.tar.gz"
            expected = make_archive(archive, unsafe_member=True)
            with self.assertRaisesRegex(ValueError, "unsafe archive member"):
                audit_scored_archive(
                    archive_path=archive,
                    output_dir=root / "audit",
                    expected_archive_sha256=str(expected["archive_sha256"]),
                    expected_input_sha256=str(expected["source_sha256"]),
                    expected_rows=2,
                    expected_totals={key: int(expected[key]) for key in ("utterance_rows", "word_rows", "token_rows", "allocation_rows")},
                )

    def test_dataset_stage_joins_scores_and_locks_external_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "hall.tar.gz"
            expected = make_archive(archive)
            audit_dir = root / "audit"
            audit_scored_archive(
                archive_path=archive, output_dir=audit_dir,
                expected_archive_sha256=str(expected["archive_sha256"]),
                expected_input_sha256=str(expected["source_sha256"]), expected_rows=2,
                expected_totals={key: int(expected[key]) for key in ("utterance_rows", "word_rows", "token_rows", "allocation_rows")},
            )
            comparator = root / "comparator.csv"
            pd.DataFrame(
                [{"dataset": "Brown", "child_id": "Adam", "child_key": "Brown/Adam", "scope": "pbm_discovery", "session_id": "s1", "age_months": 57, "age_bin": "054-059", "utterances": 5}]
            ).to_csv(comparator, index=False)
            trajectory = root / "trajectory.csv.gz"
            pd.DataFrame(
                [{"scorer_id": "mistral_full79", "role": "child", "scope": "pbm_discovery", "dataset": "Brown", "child_id": "Adam", "child_key": "Brown/Adam", "session_id": "s1", "age_months": 57, "age_bin": "054-059", "word_count_exact_top12": "2", "raw_k3_bits": 15.0, "utterances": 5, "raw_k0_bits": 18.0, "raw_context_gain_k3": 3.0, "mean_words": 2.0}]
            ).to_csv(trajectory, index=False, compression="gzip")
            manifest = build_dataset_stage(
                archive_path=archive, local_audit_dir=audit_dir,
                comparator_manifest=comparator, trajectory_input=trajectory,
                output_dir=root / "prepared", expected_rows=2,
            )
            wide = pd.read_csv(root / "prepared/hall_utterance_scores.csv.gz")
            external = pd.read_csv(root / "prepared/external_snapshot_cells.csv.gz")

        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(len(wide), 2)
        self.assertEqual(wide.loc[0, "context_gain_k3"], 3.0)
        self.assertEqual(set(external["cohort"]), {"Hall", "current_naturalistic"})

    def test_clustered_wls_exposes_registered_group_contrasts(self) -> None:
        rows = []
        for race_black in (0, 1):
            for class_uc in (0, 1):
                for child in range(3):
                    for effort in ("1", "2"):
                        rows.append(
                            {
                                "child_key": f"{race_black}-{class_uc}-{child}",
                                "race_black": race_black, "class_uc": class_uc,
                                "word_count_exact_top12": effort, "setting_auto": "home",
                                "outcome_mean": 10 + 2 * race_black + 3 * class_uc + 4 * race_black * class_uc + int(effort),
                                "row_count": 5,
                            }
                        )
        result, summary, contrasts = fit_weighted_cluster_model(
            pd.DataFrame(rows), model_id="fixture", outcome="k0_sum_bits",
            formula="outcome_mean ~ race_black * class_uc + C(word_count_exact_top12)",
            contrast_family="hall_race_class",
        )
        del result
        by_name = contrasts.set_index("contrast_id")["estimate"]
        self.assertEqual(summary["fit_status"], "PASS")
        self.assertAlmostEqual(by_name["black_minus_white_wc"], 2.0)
        self.assertAlmostEqual(by_name["black_minus_white_uc"], 6.0)
        self.assertAlmostEqual(by_name["uc_minus_wc_white"], 3.0)
        self.assertAlmostEqual(by_name["uc_minus_wc_black"], 7.0)

    def test_plot_and_report_stages_are_artifact_only_and_guard_interpretation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared = root / "prepared"
            models = root / "models"
            plots = root / "plots"
            prepared.mkdir()
            models.mkdir()
            (prepared / "dataset_manifest.json").write_text(
                json.dumps({"status": "PASS", "hall_rows": 100, "hall_children": 8, "primary_children": 8, "primary_rows": 90, "adult_adjacent_primary_rows": 40, "locked_children": 2, "matched_children": 2}),
                encoding="utf-8",
            )
            (models / "model_manifest.json").write_text(
                json.dumps({"status": "PASS", "registered_models": 20, "passed_models": 20, "failed_models": 0, "bootstrap_reps_requested": 1000}),
                encoding="utf-8",
            )
            pd.DataFrame(
                [
                    {"model_id": "H1_k0_primary", "outcome": "k0_sum_bits", "contrast_id": "black_minus_white_wc", "label": "Black minus White within WC", "estimate": 3.0, "std_error": 0.5, "ci_low": 2.0, "ci_high": 4.0, "p_value": 0.01, "tier": "primary", "label_model": "primary"},
                    {"model_id": "H1_k0_primary", "outcome": "k0_sum_bits", "contrast_id": "black_minus_white_uc", "label": "Black minus White within UC", "estimate": -0.4, "std_error": 0.6, "ci_low": -1.6, "ci_high": 0.8, "p_value": 0.5, "tier": "primary", "label_model": "primary"},
                    {"model_id": "H1_k0_primary", "outcome": "k0_sum_bits", "contrast_id": "uc_minus_wc_black", "label": "UC minus WC within Black", "estimate": -3.5, "std_error": 0.7, "ci_low": -4.9, "ci_high": -2.1, "p_value": 0.001, "tier": "primary", "label_model": "primary"},
                    {"model_id": "H1_k0_primary", "outcome": "k0_sum_bits", "contrast_id": "uc_minus_wc_white", "label": "UC minus WC within White", "estimate": 0.0, "std_error": 0.6, "ci_low": -1.2, "ci_high": 1.2, "p_value": 1.0, "tier": "primary", "label_model": "primary"},
                    {"model_id": "H1_k0_primary", "outcome": "k0_sum_bits", "contrast_id": "race_by_class_interaction", "label": "Race-by-class difference in differences", "estimate": -3.5, "std_error": 0.7, "ci_low": -4.9, "ci_high": -2.1, "p_value": 0.001, "tier": "primary", "label_model": "primary"},
                    {"model_id": "H8_k3_adult_adjacent", "outcome": "k3_sum_bits", "contrast_id": "race_by_class_interaction", "label": "Race-by-class difference in differences", "estimate": -3.0, "std_error": 0.8, "ci_low": -4.6, "ci_high": -1.4, "p_value": 0.01, "tier": "secondary_context", "label_model": "context"},
                    {"model_id": "H9_gain_k3_adult_adjacent", "outcome": "context_gain_k3", "contrast_id": "race_by_class_interaction", "label": "Race-by-class difference in differences", "estimate": -0.2, "std_error": 0.4, "ci_low": -1.0, "ci_high": 0.6, "p_value": 0.6, "tier": "secondary_context", "label_model": "gain"},
                    {"model_id": "E1_k0_locked_snapshot", "outcome": "k0_sum_bits", "contrast_id": "hall_minus_current", "label": "Hall minus current", "estimate": 3.1, "std_error": 0.5, "ci_low": 2.1, "ci_high": 4.1, "p_value": 0.001, "tier": "external_primary", "label_model": "external"},
                ]
            ).to_csv(models / "registered_contrasts.csv", index=False)
            pd.DataFrame(
                [
                    {"model_id": "H1_k0_primary", "outcome": "k0_sum_bits", "contrast_id": "race_by_class_interaction", "draws": 1000, "estimate_median": -3.5, "ci_low": -5.0, "ci_high": -2.0, "probability_positive": 0.0},
                    {"model_id": "E1_k0_locked_snapshot", "outcome": "k0_sum_bits", "contrast_id": "hall_minus_current", "draws": 1000, "estimate_median": 3.1, "ci_low": 2.0, "ci_high": 4.0, "probability_positive": 1.0},
                ]
            ).to_csv(models / "child_bootstrap_summary.csv", index=False)
            pd.DataFrame(
                [{"model_id": "H1_k0_primary", "fit_status": "PASS", "source_rows": 90, "children": 8}]
            ).to_csv(models / "model_summaries.csv", index=False)
            pd.DataFrame(
                [{"model_id": "H1_k0_primary", "contrast_id": "race_by_class_interaction", "influence_level": "child", "omitted": "Hall/h1", "estimate": -3.4}]
            ).to_csv(models / "leave_one_cluster_out.csv", index=False)
            prediction_rows = []
            for model_id in ("H1_k0_primary", "H8_k3_adult_adjacent", "H9_gain_k3_adult_adjacent"):
                for setting in ("home", "school"):
                    for stratum_index, stratum in enumerate(("Black_UC", "Black_WC", "White_UC", "White_WC")):
                        for effort in ("1", "2"):
                            prediction_rows.append({"model_id": model_id, "outcome": "k0_sum_bits", "setting_auto": setting, "stratum": stratum, "word_count_exact_top12": effort, "predicted_mean": 10 + stratum_index + int(effort), "ci_low": 9 + stratum_index + int(effort), "ci_high": 11 + stratum_index + int(effort)})
            for cohort_index, cohort in enumerate(("Hall", "current_naturalistic")):
                for effort in ("1", "2"):
                    prediction_rows.append({"model_id": "E1_k0_locked_snapshot", "outcome": "k0_sum_bits", "cohort": cohort, "word_count_exact_top12": effort, "predicted_mean": 10 + cohort_index + int(effort), "ci_low": 9 + cohort_index + int(effort), "ci_high": 11 + cohort_index + int(effort)})
            pd.DataFrame(prediction_rows).to_csv(models / "prediction_grid.csv", index=False)
            pd.DataFrame(
                [{"child_key": "Hall/h1", "stratum": "Black_UC", "k0_bits_per_word": 4.0}, {"child_key": "Hall/h2", "stratum": "White_WC", "k0_bits_per_word": 3.0}]
            ).to_csv(prepared / "hall_utterance_scores.csv.gz", index=False, compression="gzip")
            pd.DataFrame(
                [{"stratum": "Black_UC", "setting_auto": "home", "word_count_exact_top12": "1", "utterances": 10, "children": 2}]
            ).to_csv(prepared / "setting_stratum_effort_support.csv", index=False)
            plot_manifest = run_plot_stage(prepared_dir=prepared, model_dir=models, plot_dir=plots)
            report_manifest = run_report_stage(
                prepared_dir=prepared, model_dir=models, plot_dir=plots,
                report_md=root / "report.md", report_html=root / "report.html",
            )
            final_audit = run_final_audit(
                prepared_dir=prepared, model_dir=models, plot_dir=plots,
                report_md=root / "report.md", report_html=root / "report.html",
                output_dir=root / "final", expected_models=20,
                expected_bootstrap_models=2, expected_bootstrap_reps=1000,
            )
            report_text = (root / "report.md").read_text(encoding="utf-8")
            final_marker_present = (root / "final/ANALYSIS_COMPLETE_AND_AUDITED").is_file()

        self.assertEqual(plot_manifest["status"], "PASS")
        self.assertGreaterEqual(plot_manifest["figures"], 5)
        self.assertEqual(report_manifest["status"], "PASS")
        self.assertEqual(final_audit["status"], "PASS")
        self.assertTrue(final_marker_present)
        self.assertIn("descriptive", report_text.lower())
        self.assertIn("not a causal", report_text.lower())


if __name__ == "__main__":
    unittest.main()
