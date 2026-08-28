import copy
import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from build_bayesian_route1_route2_20260828 import (  # noqa: E402
    AGE_SHAPES,
    DEFAULT_CONTRACT,
    MODEL_FAMILIES,
    PRIOR_SETS,
    SAMPLE_SCOPES,
    add_rank200,
    aggregate_route1_cells,
    audit_completion_inventory,
    audit_route1_pairs,
    build_registered_fit_inventory,
    build_pilot_stop_report,
    estimate_shared_bootstrap_slopes,
    load_and_validate_contract,
    project_registered_fits,
    render_report_from_saved_payload,
    run_plots_stage,
    require_manifest,
    synthetic_likelihood_recovery,
    validate_contract_payload,
    write_manifest,
)


def route1_fixture() -> pd.DataFrame:
    rows = []
    values = {
        "u1": (20.0, 18.0, 16.0, 15.0),
        "u2": (24.0, 21.0, 19.0, 17.0),
        "u3": (30.0, 27.0, 25.0, 23.0),
    }
    for utterance_id, bits in values.items():
        for condition, value in zip(("k0", "k1", "k2", "k3"), bits):
            rows.append(
                {
                    "utterance_id": utterance_id,
                    "dataset": "Brown",
                    "child_key": "Brown/Adam",
                    "session_id": 1 if utterance_id != "u3" else 2,
                    "age_months": 27.0 if utterance_id != "u3" else 30.0,
                    "word_count_top12": "2",
                    "condition": condition,
                    "mean_bits": value,
                }
            )
    return pd.DataFrame(rows)


class BayesianRouteProgramTests(unittest.TestCase):
    def test_pilot_report_diagnostic_prose_is_derived_from_saved_records(self):
        payload = {
            "decision": {
                "status": "STOP_UNSAFE",
                "all_problems": ["cpu gate"],
                "projection_summary": {
                    "total_projected_cpu_hours": 8312.0,
                    "maximum_single_fit_wall_hours": 33.5,
                    "maximum_peak_memory_gb": 2.8,
                    "total_projected_output_gb": 84.8,
                },
            },
            "data_audit": {
                "route1_rows": 1,
                "route1_long_rows": 4,
                "route1_cells": 4,
                "route1_cell_n_sum": 4,
                "route2_rows": 1,
                "route2_children": 1,
                "route2_corpora": 1,
                "rank_zero_endpoints": 0,
                "rank_one_endpoints": 0,
                "rank200_max_error": 0.0,
            },
            "synthetic_audit": {
                "observed_synthetic_fits": ["B1"],
                "expected_synthetic_fits": ["B1"],
            },
            "pilot_records": [
                {
                    "fit_id": f"B{index}_pilot",
                    "elapsed_seconds": 1.0,
                    "rhat_max": 1.01,
                    "ess_bulk_min": 100.0,
                    "divergences": 0,
                    "peak_rss_kb": 1024,
                }
                for index in range(1, 8)
            ],
            "family_projection": [{
                "model_family": "B1",
                "registered_fits": 1,
                "projected_cpu_hours": 1.0,
                "maximum_wall_hours": 1.0,
                "projected_output_gb": 1.0,
            }],
            "guardrails": ["Pilot coefficients are not results."],
            "git": {"branch": "test", "head": "abc"},
            "starting_git_sha": "abc",
            "source_paper_sha256": "def",
        }
        report = build_pilot_stop_report(payload)
        self.assertIn("All seven representative pilot fits produced zero", report)
        self.assertNotIn("B5 produced one divergent", report)

    def test_real_pilot_backend_forces_fresh_fits_and_clears_exact_fit_directories(self):
        backend = (ROOT / "src/fit_bayesian_route1_route2_models.R").read_text(
            encoding="utf-8"
        )
        self.assertIn('file_refit = "always"', backend)
        self.assertNotIn('file_refit = "on_change"', backend)
        self.assertGreaterEqual(
            backend.count("unlink(fit_dir, recursive = TRUE, force = TRUE)"), 2
        )

    def test_frozen_contract_has_complete_scopes_models_priors_and_queries(self):
        contract = load_and_validate_contract(DEFAULT_CONTRACT)
        self.assertEqual(tuple(contract["sample_scopes"]), SAMPLE_SCOPES)
        self.assertEqual(tuple(contract["model_families"]), MODEL_FAMILIES)
        self.assertEqual(tuple(contract["age_shapes"]), AGE_SHAPES)
        self.assertEqual(tuple(contract["prior_sets"]), PRIOR_SETS)
        self.assertEqual(contract["starting_git_sha"], "f52a7f102dd87a6a566ef72bbf24519efda16202")
        self.assertEqual(contract["source_paper"]["sha256"], "cecf8f0e696c3b95a3b4033352e484e3c0b863560959c793e8d67ebd957f1957")
        for family in MODEL_FAMILIES:
            record = contract["families"][family]
            self.assertTrue(record["formula"])
            self.assertTrue(record["contrasts"])
            self.assertTrue(record["diagnostics"])
            self.assertTrue(record["synthetic_truth"])
        for scale in ("bits_six_month", "words_six_month", "rank_percentile_six_month"):
            self.assertGreater(contract["ropes"][scale], 0)

    def test_contract_fails_closed_on_scope_drift_or_missing_prior(self):
        contract = load_and_validate_contract(DEFAULT_CONTRACT)
        changed = copy.deepcopy(contract)
        changed["scope_datasets"]["pbm_discovery"].remove("Providence")
        with self.assertRaisesRegex(ValueError, "scope_datasets"):
            validate_contract_payload(changed)
        changed = copy.deepcopy(contract)
        del changed["priors"]["skeptical"]
        with self.assertRaisesRegex(ValueError, "prior"):
            validate_contract_payload(changed)

    def test_route1_pairing_requires_one_complete_k0_k3_set_per_identity(self):
        frame = route1_fixture()
        audit = audit_route1_pairs(frame)
        self.assertEqual(audit["utterances"], 3)
        self.assertEqual(audit["long_rows"], 12)
        duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit_route1_pairs(duplicated)
        missing = frame.drop(frame.index[0])
        with self.assertRaisesRegex(ValueError, "complete k0-k3"):
            audit_route1_pairs(missing)

    def test_exact_cell_aggregation_matches_mean_sd_count_and_se(self):
        frame = route1_fixture()
        cells, audit = aggregate_route1_cells(frame)
        target = cells.loc[
            (cells.session_id == 1) & (cells.condition == "k0")
        ].iloc[0]
        self.assertEqual(target.cell_n, 2)
        self.assertAlmostEqual(target.cell_mean_bits, 22.0)
        self.assertAlmostEqual(target.cell_sd_bits, np.sqrt(8.0))
        self.assertAlmostEqual(target.cell_se_bits, 2.0)
        self.assertEqual(audit["raw_long_rows"], int(cells.cell_n.sum()))
        reconstructed = float(np.average(cells.cell_mean_bits, weights=cells.cell_n))
        self.assertAlmostEqual(reconstructed, float(frame.mean_bits.mean()))

    def test_rank200_preserves_literal_endpoints_and_rejects_non_grid_values(self):
        frame = pd.DataFrame(
            {"effort_percentile_in_qwen": [0.0, 0.005, 0.5, 0.995, 1.0]}
        )
        ranked, audit = add_rank200(frame)
        self.assertEqual(ranked.rank200.tolist(), [0, 1, 100, 199, 200])
        self.assertEqual(audit["zero_endpoints"], 1)
        self.assertEqual(audit["one_endpoints"], 1)
        self.assertEqual(ranked.effort_percentile_in_qwen.tolist(), frame.effort_percentile_in_qwen.tolist())
        with self.assertRaisesRegex(ValueError, "rank200"):
            add_rank200(pd.DataFrame({"effort_percentile_in_qwen": [0.333]}))

    def test_hash_bound_manifest_rejects_stale_outputs_and_predecessors(self):
        with tempfile.TemporaryDirectory(prefix="bayesian-route-manifest-") as temporary:
            root = Path(temporary)
            predecessor = root / "predecessor.json"
            predecessor.write_text('{"stage":"contract"}\n', encoding="utf-8")
            output = root / "data.csv"
            output.write_text("x\n1\n", encoding="utf-8")
            manifest_path = root / "dataset_manifest.json"
            write_manifest(
                stage="datasets",
                manifest_path=manifest_path,
                inputs={"contract_manifest": predecessor},
                outputs={"data": output},
                audit={"status": "PASS"},
            )
            require_manifest(manifest_path, "datasets")
            output.write_text("x\n2\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "stale datasets output"):
                require_manifest(manifest_path, "datasets")
            output.write_text("x\n1\n", encoding="utf-8")
            predecessor.write_text('{"stage":"changed"}\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "stale datasets input"):
                require_manifest(manifest_path, "datasets")

    def test_deterministic_synthetic_recovery_covers_every_likelihood_family(self):
        result = synthetic_likelihood_recovery(seed=20260828)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(set(result["families"]), set(MODEL_FAMILIES))
        for family, record in result["families"].items():
            self.assertEqual(record["status"], "PASS", family)
            self.assertFalse(record["problems"], family)
        self.assertLess(result["families"]["B1"]["max_context_error"], 0.35)
        self.assertLess(result["families"]["B2"]["dispersion_age_error"], 0.15)
        self.assertLess(result["families"]["B3"]["max_count_coefficient_error"], 0.12)
        self.assertLess(result["families"]["B4"]["endpoint_probability_error"], 0.03)
        self.assertLess(result["families"]["B5"]["correlation_error"], 0.08)

    def test_b5_shared_bootstrap_preserves_dimensions_and_cross_outcome_covariance(self):
        rng = np.random.default_rng(20260828)
        rows = []
        for child_number, dataset in ((1, "Brown"), (2, "Providence")):
            for row_number in range(120):
                age = rng.normal()
                entropy = rng.normal()
                words = rng.integers(1, 5)
                rows.append({
                    "utterance_id": f"u{child_number}_{row_number}",
                    "child_key": f"child_{child_number}",
                    "dataset": dataset,
                    "age_z": age,
                    "word_count_top12": str(words),
                    "k3_bits": 25 - 0.4 * age + 0.8 * words + rng.normal(scale=0.5),
                    "child_words": rng.poisson(np.exp(0.8 + 0.1 * age - 0.2 * age * entropy)),
                    "entropy_z": entropy,
                    "context_words_z": rng.normal(),
                })
        frame = pd.DataFrame(rows)
        slopes, audit = estimate_shared_bootstrap_slopes(
            frame, bootstrap_draws=30, seed=20260828
        )
        self.assertEqual(len(slopes), 2)
        self.assertTrue(audit["shared_resampling"])
        for row in slopes.itertuples(index=False):
            determinant = row.r1_se**2 * row.r2_se**2 - row.r1_r2_cov**2
            self.assertGreater(determinant, 0)
        duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "duplicated"):
            estimate_shared_bootstrap_slopes(duplicated, bootstrap_draws=30)

    def test_resource_projection_covers_every_registered_fit(self):
        contract = load_and_validate_contract(DEFAULT_CONTRACT)
        pilot_ids = [
            "B1_pilot", "B2_pilot", "B3_primary_pilot", "B3_qwen_adjusted_pilot",
            "B4_beta_binomial_pilot", "B4_zoib_pilot", "B5_pilot",
        ]
        pilot = pd.DataFrame({
            "fit_id": pilot_ids,
            "elapsed_seconds": [60.0] * len(pilot_ids),
            "rows": [600, 1200, 1200, 1200, 1200, 1200, 24],
            "output_bytes": [1_000_000] * len(pilot_ids),
            "peak_rss_kb": [1_000_000] * len(pilot_ids),
            "minimum_bulk_ess_per_hour": [1000.0] * len(pilot_ids),
            "chains": [2] * len(pilot_ids),
            "sampling": [250] * len(pilot_ids),
        })
        scope_counts = []
        for family in ("B1", "B2", "B3", "B4"):
            for scope, rows in zip(SAMPLE_SCOPES, (400_000, 600_000, 1_000_000)):
                scope_counts.append({"model_family": family, "sample_scope": scope, "rows": rows})
        projection, summary = project_registered_fits(pilot, contract, scope_counts)
        self.assertEqual(len(projection), len(build_registered_fit_inventory(contract)))
        self.assertEqual(projection.fit_id.nunique(), len(projection))
        self.assertTrue(np.isfinite(projection.projected_wall_hours).all())
        self.assertEqual(summary["registered_fits"], len(projection))

    def test_fit_inventory_is_formula_invariant_across_scopes(self):
        contract = load_and_validate_contract(DEFAULT_CONTRACT)
        inventory = build_registered_fit_inventory(contract)
        expected = len(MODEL_FAMILIES) * len(SAMPLE_SCOPES) * len(AGE_SHAPES) * len(PRIOR_SETS)
        self.assertGreaterEqual(len(inventory), expected)
        grouped = inventory.groupby(["model_family", "variant", "age_shape", "prior_set"])
        for _, rows in grouped:
            self.assertEqual(set(rows.sample_scope), set(SAMPLE_SCOPES))
            self.assertEqual(rows.formula_sha256.nunique(), 1)

    def test_report_renderer_cannot_call_backend_or_refit(self):
        with tempfile.TemporaryDirectory(prefix="bayesian-route-report-") as temporary:
            path = Path(temporary) / "report.md"
            payload = {
                "program_status": "PILOT_STOP",
                "stage_status": {"contract": "PASS", "real-pilot": "STOP"},
                "pilot_decision": "unsafe projected runtime",
                "scientific_guardrails": ["Lower surprisal means greater scorer predictability."],
            }
            with mock.patch(
                "build_bayesian_route1_route2_20260828.run_r_backend",
                side_effect=AssertionError("report attempted a fit"),
            ):
                render_report_from_saved_payload(payload, path)
            self.assertIn("PILOT_STOP", path.read_text(encoding="utf-8"))

    def test_plot_stage_consumes_saved_tables_without_calling_backend(self):
        with tempfile.TemporaryDirectory(prefix="bayesian-route-plots-") as temporary:
            root = Path(temporary)
            output = root / "results"
            synthesis = output / "synthesis"
            pilot = output / "real-pilot"
            synthesis.mkdir(parents=True)
            pilot.mkdir(parents=True)
            family_path = synthesis / "resource_projection_by_family.csv"
            pilot_path = pilot / "fit_records.csv"
            pd.DataFrame({
                "model_family": ["B1", "B5"],
                "projected_cpu_hours": [100.0, 5.0],
            }).to_csv(family_path, index=False)
            pd.DataFrame({
                "fit_id": ["B1_pilot", "B5_pilot"],
                "rhat_max": [1.01, 1.02],
                "divergences": [0, 1],
            }).to_csv(pilot_path, index=False)
            synthesis_audit = synthesis / "audit.json"
            synthesis_audit.write_text('{"status":"PASS"}\n', encoding="utf-8")
            write_manifest(
                stage="synthesis",
                manifest_path=synthesis / "synthesis_manifest.json",
                inputs={},
                outputs={"audit": synthesis_audit},
                audit={"status": "PASS"},
            )
            args = argparse.Namespace(
                output_dir=output,
                figures_dir=root / "figures",
                temp_dir=root / "tmp",
            )
            with mock.patch(
                "build_bayesian_route1_route2_20260828.run_r_backend",
                side_effect=AssertionError("plot attempted a fit"),
            ):
                run_plots_stage(args)
            self.assertTrue((root / "figures/pilot_projected_cpu_hours_by_family.png").exists())

    def test_final_audit_refuses_missing_model_scope_sensitivity_or_diagnostics(self):
        contract = load_and_validate_contract(DEFAULT_CONTRACT)
        expected = build_registered_fit_inventory(contract)
        complete = expected.assign(
            fit_status="PASS",
            rhat_max=1.001,
            ess_bulk_min=500.0,
            ess_tail_min=400.0,
            divergences=0,
            treedepth_saturated=0,
            energy_bfmi_min=0.5,
            ppc_status="PASS",
            loo_status="PASS",
            influence_status="PASS",
        )
        self.assertEqual(audit_completion_inventory(complete, contract)["status"], "PASS")
        missing = complete.iloc[:-1].copy()
        result = audit_completion_inventory(missing, contract)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("missing registered fit" in problem for problem in result["problems"]))
        broken = complete.copy()
        broken.loc[0, "divergences"] = 1
        result = audit_completion_inventory(broken, contract)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("diagnostic" in problem for problem in result["problems"]))


if __name__ == "__main__":
    unittest.main()
