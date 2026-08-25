import json
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from build_full79_joint_efficiency_analysis import (  # noqa: E402
    AGE_BINS,
    MODEL_SCRIPT,
    _bootstrap_child_age,
    parse_args,
    require_manifest,
    run_datasets_stage,
)


def write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    connection.register("frame", frame)
    connection.execute("COPY frame TO ? (FORMAT PARQUET)", [str(path)])
    connection.close()


class Full79JointEfficiencyAnalysisTests(unittest.TestCase):
    def test_dataset_stage_freezes_one_observed_row_per_utterance(self):
        with tempfile.TemporaryDirectory(prefix="joint-efficiency-dataset-") as temporary:
            root = Path(temporary)
            upstream = root / "upstream"
            output = root / "output"
            (upstream / "audit").mkdir(parents=True)
            (upstream / "audit/final_audit.json").write_text(
                json.dumps({"status": "PASS_CORE_LSTM_PENDING", "problems": []}),
                encoding="utf-8",
            )
            normalized = pd.DataFrame(
                {
                    "utterance_id": [f"u{index}" for index in range(4)],
                    "context_id": [f"c{index}" for index in range(4)],
                    "dataset": ["A", "A", "B", "B"],
                    "child_key": ["A/a", "A/a", "B/b", "B/b"],
                    "session_id": [1, 2, 1, 2],
                    "age_months": [18.0, 24.0, 30.0, 36.0],
                    "age_bin": list(AGE_BINS[:4]),
                    "word_count": [1, 2, 3, 4],
                    "k0_sum_bits": [20.0, 30.0, 40.0, 50.0],
                    "k3_sum_bits": [15.0, 22.0, 31.0, 39.0],
                    "k3_mean_bits_per_token": [7.5, 5.5, 5.2, 4.9],
                    "context_support_bits": [5.0, 8.0, 9.0, 11.0],
                    "z_effort": [-1.0, -0.2, 0.3, 1.1],
                    "z_k3": [-0.8, -0.1, 0.4, 0.9],
                    "effort_percentile_in_qwen": [0.2, 0.4, 0.6, 0.8],
                    "k3_percentile_in_qwen": [0.3, 0.5, 0.7, 0.9],
                    "source": ["observed_child"] * 4,
                }
            )
            contexts = pd.DataFrame(
                {
                    "context_id": [f"c{index}" for index in range(4)],
                    "context_word_count": [5, 6, 7, 8],
                    "unique_response_count": [90, 91, 92, 93],
                    "top_response_probability": [0.05] * 4,
                    "exact_string_entropy_bits": [2.0, 2.5, 3.0, 3.5],
                    "qwen_mean_word_count": [2.0, 2.5, 3.5, 4.5],
                    "qwen_sd_word_count": [1.0] * 4,
                    "qwen_median_word_count": [2.0, 2.0, 3.0, 4.0],
                    "qwen_p10_word_count": [1.0] * 4,
                    "qwen_p90_word_count": [4.0, 5.0, 6.0, 7.0],
                    "qwen_min_word_count": [1] * 4,
                    "qwen_max_word_count": [8] * 4,
                    "qwen_mean_k0_sum_bits": [30.0] * 4,
                    "qwen_mean_k3_sum_bits": [24.0] * 4,
                    "qwen_sd_k3_sum_bits": [5.0] * 4,
                    "qwen_median_k3_sum_bits": [23.0] * 4,
                    "qwen_p10_k3_sum_bits": [12.0] * 4,
                    "qwen_p90_k3_sum_bits": [40.0] * 4,
                    "qwen_mean_k3_bits_per_token": [5.0] * 4,
                    "qwen_mean_context_support_bits": [6.0] * 4,
                }
            )
            write_parquet(normalized, upstream / "metrics/candidate_context_normalized.parquet")
            write_parquet(contexts, upstream / "metrics/qwen_context_metrics.parquet")
            write_parquet(pd.DataFrame({"placeholder": [1]}), upstream / "datasets/non_lstm_candidates.parquet")

            args = parse_args(
                [
                    "--stage", "datasets",
                    "--upstream-dir", str(upstream),
                    "--output-dir", str(output),
                    "--temp-dir", str(root),
                    "--expected-eligible-rows", "4",
                    "--expected-contexts", "4",
                    "--expected-children", "2",
                    "--expected-corpora", "2",
                ]
            )
            manifest = run_datasets_stage(args)
            self.assertEqual(manifest["audit"]["status"], "PASS")
            self.assertEqual(manifest["audit"]["rows"], 4)
            result = duckdb.connect().execute(
                "SELECT child_words_minus_qwen_mean, effort_percentile_open FROM read_parquet(?) ORDER BY utterance_id",
                [manifest["outputs"]["analysis_rows"]["path"]],
            ).fetchdf()
            self.assertAlmostEqual(result.iloc[0].child_words_minus_qwen_mean, -1.0)
            self.assertTrue(result.effort_percentile_open.between(0, 1).all())

            Path(manifest["outputs"]["audit"]["path"]).write_text("stale", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "stale datasets output"):
                require_manifest(output / "datasets/dataset_manifest.json", "datasets")

    def test_child_bootstrap_is_child_balanced_and_reproducible(self):
        frame = pd.DataFrame(
            {
                "child_key": ["a", "b", "a", "b"],
                "age_bin": [AGE_BINS[0], AGE_BINS[0], AGE_BINS[1], AGE_BINS[1]],
                "metric": [1.0, 3.0, 2.0, 4.0],
            }
        )
        first = _bootstrap_child_age(frame, metrics=["metric"], draws=100, seed=17)
        second = _bootstrap_child_age(frame, metrics=["metric"], draws=100, seed=17)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first.estimate.tolist(), [2.0, 3.0])
        self.assertTrue((first.children == 2).all())

    def test_registered_r_engine_keeps_scope_and_estimand_guardrails(self):
        source = MODEL_SCRIPT.read_text(encoding="utf-8")
        for phrase in [
            "mgcv",
            "bam(",
            "pbm_discovery",
            "non_pbm_confirmation",
            "m1_length_primary",
            "m3_information_k3_total",
            "m4_effort_percentile",
            "m5_exact_length_k3_gap",
            "m6_raw_nondominated",
            "s(child_key, entropy_z, bs='re')",
            "model_contrasts",
        ]:
            self.assertIn(phrase, source)


if __name__ == "__main__":
    unittest.main()
