import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPT = SRC / "build_full79_information_effort_clouds.py"
sys.path.insert(0, str(SRC))

from build_full79_information_effort_clouds import (  # noqa: E402
    AGE_BINS,
    PRECISE_AGES,
    fit_child_bootstrap_trajectories,
)


EXPECTED_COLORS = {
    "observed_child": "#08306b",
    "qwen": "#bdbdbd",
    "random": "#d62728",
    "unigram": "#ff7f0e",
    "bigram": "#2ca02c",
    "trigram": "#1f77b4",
    "lstm": "#9467bd",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_full100_fixture(root: Path) -> dict[str, Path | list[str]]:
    qwen_root = root / "qwen_full100"
    wide_path = root / "child_direct_surprisal_wide.csv.gz"
    wide_manifest = root / "wide_manifest.json"
    context_ids: list[str] = []
    wide_rows: list[dict[str, object]] = []
    qwen_rows: list[dict[str, object]] = []

    utterance_index = 0
    source_offsets = {"real": 5.0, "random": 12.0, "unigram": 10.0, "bigram": 8.0, "trigram": 6.0}
    for age_index, (age_bin, age_months) in enumerate(zip(AGE_BINS, PRECISE_AGES)):
        for exact_length in range(1, 13):
            utterance_index += 1
            context_text = f"caregiver context age {age_index} exact length {exact_length}"
            context_sha = hashlib.sha256(context_text.encode("utf-8")).hexdigest()
            context_id = context_sha[:24]
            context_ids.append(context_id)
            child_index = (age_index + exact_length) % 4
            dataset = "CorpusA" if child_index < 2 else "CorpusB"
            child_id = f"Child{child_index + 1}"
            utterance_id = f"utterance-{utterance_index}"
            wide_row: dict[str, object] = {
                "dataset": dataset,
                "child_id": child_id,
                "child_key": f"legacy/{child_id}",
                "session_id": utterance_index,
                "age_months": age_months,
                "age_bin": age_bin,
                "file": f"fixture-{utterance_index}.cha",
                "line_no": utterance_index + 10,
                "utt_id": utterance_index + 100,
                "utterance_id": utterance_id,
                "context_k3": context_text,
                "context_k3_sha256": context_sha,
            }
            for prefix, offset in source_offsets.items():
                k3_score = offset + 1.3 * exact_length - 0.03 * age_months
                target = " ".join([f"{prefix}word"] * exact_length)
                wide_row.update(
                    {
                        f"{prefix}_target_text": target,
                        f"{prefix}_nb_words": exact_length,
                        f"{prefix}_k0_sum_bits": k3_score + 10.0,
                        f"{prefix}_k0_mean_bits_per_token": (k3_score + 10.0) / exact_length,
                        f"{prefix}_k0_n_eval_tokens": exact_length,
                        f"{prefix}_k3_sum_bits": k3_score,
                        f"{prefix}_k3_mean_bits_per_token": k3_score / exact_length,
                        f"{prefix}_k3_n_eval_tokens": exact_length,
                    }
                )
            wide_rows.append(wide_row)

            for sample_index in range(100):
                value = sample_index + 1
                target_text = " ".join(["word"] * value)
                qwen_rows.append(
                    {
                        "response_id": f"{context_id}::{sample_index:03d}",
                        "setting_id": f"{context_id}::fixture",
                        "context_id": context_id,
                        "context_text": context_text,
                        "context_word_count": 6,
                        "datasets": dataset,
                        "child_ids": child_id,
                        "child_count": 1,
                        "n_target_rows": 1,
                        "selected_sample_index": sample_index,
                        "target_text": target_text,
                        "source_shard": 0,
                        "sum_bits_k0": float(value + 10),
                        "mean_bits_per_token_k0": float(value + 10) / value,
                        "n_eval_tokens_k0": value,
                        "sum_bits_k3": float(value),
                        "mean_bits_per_token_k3": 1.0,
                        "n_eval_tokens_k3": value,
                        "context_support_bits": 10.0,
                    }
                )

    pd.DataFrame(wide_rows).to_csv(wide_path, index=False, compression="gzip")
    write_json(
        wide_manifest,
        {"child_rows": 96, "children": 4, "datasets": ["CorpusA", "CorpusB"]},
    )

    all_qwen = pd.DataFrame(qwen_rows)
    tier_specs = (("core75", all_qwen[all_qwen["selected_sample_index"] < 75]),
                  ("extension25", all_qwen[all_qwen["selected_sample_index"] >= 75]))
    prepared_columns = [
        "response_id",
        "setting_id",
        "context_id",
        "context_text",
        "context_word_count",
        "datasets",
        "child_ids",
        "child_count",
        "n_target_rows",
        "selected_sample_index",
        "target_text",
        "source_shard",
    ]
    for tier, frame in tier_specs:
        prepared = qwen_root / "prepared" / "inputs" / tier / "responses_00000_of_00001.csv.gz"
        processed = qwen_root / "processed" / tier / "scored_00000_of_00001.csv.gz"
        prepared.parent.mkdir(parents=True, exist_ok=True)
        processed.parent.mkdir(parents=True, exist_ok=True)
        frame[prepared_columns].to_csv(prepared, index=False, compression="gzip")
        frame.to_csv(processed, index=False, compression="gzip")
        write_json(
            processed.with_name(processed.name + ".contract.json"),
            {
                "status": "PASS",
                "selection_tiers": [tier],
                "input_sha256": sha256_file(prepared),
                "output_sha256": sha256_file(processed),
                "rows": len(frame),
                "contexts": 96,
            },
        )

    context_means = pd.DataFrame(
        {
            "context_id": context_ids,
            "expected_k0_utterance_surprisal_bits": [60.5] * 96,
            "expected_k3_utterance_surprisal_bits": [50.5] * 96,
            "expected_context_support_bits": [10.0] * 96,
        }
    )
    means_path = qwen_root / "context_means" / "full100" / "context_means_00000_of_00001.csv.gz"
    means_path.parent.mkdir(parents=True, exist_ok=True)
    context_means.to_csv(means_path, index=False, compression="gzip")
    for marker in ("CORE75_COMPLETE", "EXTENSION25_COMPLETE", "FULL100_AVAILABLE"):
        (qwen_root / marker).write_text("PASS\n", encoding="utf-8")
    write_json(
        qwen_root / "reports" / "full100" / "full100_audit.json",
        {"status": "PASS", "core75_and_extension25_disjoint": True},
    )
    return {
        "wide": wide_path,
        "wide_manifest": wide_manifest,
        "qwen_root": qwen_root,
        "context_ids": context_ids,
    }


class Full79InformationEffortCloudTests(unittest.TestCase):
    def test_all_stages_on_canonical_full100_fixture(self):
        with tempfile.TemporaryDirectory(prefix="full79-cloud-test-") as temporary:
            root = Path(temporary)
            fixture = make_full100_fixture(root)
            output = root / "output"
            figures = root / "figures"
            report_md = root / "report.md"
            report_html = root / "report.html"
            duckdb_tmp = root / "duckdb_tmp"
            duckdb_tmp.mkdir()
            command = [
                sys.executable,
                str(SCRIPT),
                "--stage",
                "all",
                "--input-wide",
                str(fixture["wide"]),
                "--wide-manifest",
                str(fixture["wide_manifest"]),
                "--qwen-root",
                str(fixture["qwen_root"]),
                "--lstm-root",
                str(root / "absent_lstm"),
                "--output-dir",
                str(output),
                "--fig-dir",
                str(figures),
                "--report-md",
                str(report_md),
                "--report-html",
                str(report_html),
                "--chunksize",
                "4",
                "--bootstrap-draws",
                "20",
                "--bootstrap-seed",
                "11",
                "--duckdb-memory-limit",
                "1GB",
                "--duckdb-temp-dir",
                str(duckdb_tmp),
                "--expected-real-source-rows",
                "96",
                "--expected-eligible-real-rows",
                "96",
                "--expected-qwen-contexts",
                "96",
                "--expected-qwen-responses",
                "9600",
                "--expected-qwen-core-responses",
                "7200",
                "--expected-qwen-extension-responses",
                "2400",
                "--expected-qwen-responses-per-context",
                "100",
                "--expected-qwen-core-per-context",
                "75",
                "--expected-qwen-extension-per-context",
                "25",
                "--expected-children",
                "4",
                "--expected-corpora",
                "2",
                "--expected-shards",
                "1",
            ]
            environment = os.environ.copy()
            environment["MPLCONFIGDIR"] = str(root / "matplotlib")
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=180,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"builder failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )

            pending_marker = output / "CORE_CLOUDS_COMPLETE_LSTM_PENDING"
            self.assertTrue(pending_marker.is_file())
            self.assertIn("PASS_CORE_LSTM_PENDING", pending_marker.read_text(encoding="utf-8"))
            self.assertIn("LSTM_INCLUDED=0", pending_marker.read_text(encoding="utf-8"))
            self.assertFalse(
                (output / "FULL79_INFORMATION_EFFORT_CLOUDS_COMPLETE_AND_AUDITED").exists()
            )

            style = json.loads(
                (output / "datasets" / "source_style_contract.json").read_text(encoding="utf-8")
            )
            self.assertEqual(style["colors"], EXPECTED_COLORS)
            self.assertEqual(style["source_order"], list(EXPECTED_COLORS))

            lstm_schema = json.loads(
                (output / "schemas" / "required_full79_lstm_scored_handoff.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(lstm_schema["status"], "ABSENT_PENDING")
            self.assertEqual(lstm_schema["required_top_level_marker"], "COMPLETE_AND_AUDITED")
            self.assertEqual(
                lstm_schema["required_score_columns"],
                [
                    "k0_sum_bits",
                    "k0_mean_bits_per_token",
                    "k0_n_eval_tokens",
                    "k3_sum_bits",
                    "k3_mean_bits_per_token",
                    "k3_n_eval_tokens",
                ],
            )
            self.assertEqual(lstm_schema["prohibited_substitute"], "PBM-only additive LSTM products")

            connection = duckdb.connect()
            context_row = connection.execute(
                "SELECT * FROM read_parquet(?) WHERE context_id=?",
                [str(output / "metrics" / "qwen_context_metrics.parquet"), fixture["context_ids"][0]],
            ).fetchdf().iloc[0]
            observed = connection.execute(
                "SELECT z_effort, z_k3, effort_percentile_in_qwen, k3_percentile_in_qwen, "
                "observed_effort_percentile_in_qwen, "
                "observed_k3_percentile_in_qwen FROM read_parquet(?) "
                "WHERE utterance_id='utterance-1' AND source='observed_child'",
                [str(output / "metrics" / "candidate_context_normalized.parquet")],
            ).fetchdf().iloc[0]
            connection.close()
            expected_sd = np.std(np.arange(1.0, 101.0), ddof=1)
            expected_real_k3 = 5.0 + 1.3 * 1 - 0.03 * 18
            self.assertAlmostEqual(context_row["qwen_mean_word_count"], 50.5)
            self.assertAlmostEqual(context_row["qwen_sd_word_count"], expected_sd)
            self.assertAlmostEqual(context_row["qwen_mean_k3_sum_bits"], 50.5)
            self.assertAlmostEqual(context_row["exact_string_entropy_bits"], np.log2(100.0))
            self.assertEqual(context_row["unique_response_count"], 100)
            self.assertAlmostEqual(observed["z_effort"], (1 - 50.5) / expected_sd)
            self.assertAlmostEqual(observed["z_k3"], (expected_real_k3 - 50.5) / expected_sd)
            self.assertAlmostEqual(observed["effort_percentile_in_qwen"], 0.005)
            self.assertAlmostEqual(observed["k3_percentile_in_qwen"], 0.05)
            self.assertAlmostEqual(observed["observed_effort_percentile_in_qwen"], 0.005)
            self.assertAlmostEqual(observed["observed_k3_percentile_in_qwen"], 0.05)

            length_age_summary = pd.read_csv(
                output / "metrics" / "age_bin_model_length_summary.csv"
            )
            self.assertEqual(len(length_age_summary), 576)
            self.assertEqual(
                len(length_age_summary[["source", "age_bin", "word_count"]].drop_duplicates()),
                576,
            )
            fixed_registry = pd.read_csv(output / "models" / "fixed_length_model_registry.csv")
            self.assertEqual(len(fixed_registry), 31)
            self.assertTrue(fixed_registry["status"].eq("PASS").all())

            plot_manifest = json.loads(
                (output / "plots" / "plots_manifest.json").read_text(encoding="utf-8")
            )
            required_plot_keys = {
                "fixed_length_atlas",
                "nonlinear_check",
                "regression_coefficients",
                "model_length_age_3d",
                "interactive_model_length_age_3d",
                "length_distributions",
                "plot_audit",
            }
            self.assertEqual(set(plot_manifest["outputs"]), required_plot_keys)
            for item in plot_manifest["outputs"].values():
                product = Path(item["path"])
                self.assertTrue(product.is_file())
                self.assertGreater(product.stat().st_size, 0)
            plot_audit = pd.read_csv(output / "plots" / "plot_audit.csv")
            self.assertTrue(plot_audit["exists"].all())
            self.assertEqual(len(plot_audit), 6)

            for audit_path in (
                output / "datasets" / "candidate_extraction_audit.json",
                output / "metrics" / "metric_audit.json",
                output / "models" / "model_audit.json",
                output / "audit" / "final_audit.json",
            ):
                self.assertTrue(audit_path.is_file())
                self.assertGreater(audit_path.stat().st_size, 0)
            final_audit = json.loads(
                (output / "audit" / "final_audit.json").read_text(encoding="utf-8")
            )
            self.assertEqual(final_audit["status"], "PASS_CORE_LSTM_PENDING")
            self.assertEqual(final_audit["problems"], [])
            self.assertFalse(final_audit["limitations"]["lstm"]["included"])
            self.assertFalse(final_audit["limitations"]["lstm"]["all_source_marker_allowed"])
            self.assertEqual(
                {row["source"]: row["candidate_rows"] for row in final_audit["source_counts"]},
                {source: 96 for source in ("observed_child", "qwen", "random", "unigram", "bigram", "trigram")},
            )

            self.assertTrue(report_md.is_file())
            self.assertTrue(report_html.is_file())
            report_text = report_md.read_text(encoding="utf-8")
            self.assertIn("All-79 Model × Length × Age Information Atlas", report_text)
            self.assertIn("one information value per model, exact utterance length", report_text)
            self.assertIn("points: raw average for that model × length × age bin", report_text)
            self.assertIn("CORE_CLOUDS_COMPLETE_LSTM_PENDING", report_text)
            self.assertIn("Pareto frontier", report_text)

    def test_quadratic_trajectory_is_deterministic_for_fixed_seed(self):
        rows = []
        ages = (18, 36, 60)
        for child_index in range(4):
            for age in ages:
                scaled_age = (age - 39.0) / 12.0
                value = 2.0 + 3.0 * scaled_age + 0.5 * scaled_age**2 + child_index * 0.1
                rows.append(
                    {
                        "child_key": f"Corpus/Child{child_index}",
                        "age_months": age,
                        "source": "observed_child",
                        "mean_word_count": value,
                        "median_word_count": value - 0.25,
                    }
                )
        cells = pd.DataFrame(rows)

        first = fit_child_bootstrap_trajectories(cells, source_column="source", draws=20, seed=73)
        second = fit_child_bootstrap_trajectories(cells, source_column="source", draws=20, seed=73)

        pd.testing.assert_frame_equal(first[0], second[0], check_exact=True)
        pd.testing.assert_frame_equal(first[1], second[1], check_exact=True)
        self.assertEqual(first[2], second[2])
        mean_coefficients = first[1][first[1]["summary"].eq("mean")].set_index("term")["estimate"]
        self.assertAlmostEqual(mean_coefficients["intercept_at_39_months"], 2.15)
        self.assertAlmostEqual(mean_coefficients["age_years_centered"], 3.0)
        self.assertAlmostEqual(mean_coefficients["age_years_centered_squared"], 0.5)
        self.assertTrue((first[0]["bootstrap_requested"] == 20).all())

    def test_cli_rejects_invalid_stage(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--stage", "nonsense"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)


if __name__ == "__main__":
    unittest.main()
