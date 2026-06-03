import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_age_word_dicts import ChildUnit
from generate_lstm_utterances import LSTMConfig, LSTMExample
from custom_age_bins import AgeBin, write_age_bins_config
from run_lstm_baseline_pipeline import (  # noqa: E402
    LSTMAgeBinning,
    build_additive_bin_runs,
    build_child_scoring_rows_with_lstm,
    discover_units_from_manifest,
    examples_for_additive_training_bin,
    examples_in_target_bin,
    load_pipeline_config,
    lstm_config_from_mapping,
    merge_lstm_columns_into_context,
    normalize_variants,
    run_lstm_baseline_pipeline,
)


def write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


STAGE0_COLUMNS = [
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_raw",
    "age_months",
    "sex",
    "file",
    "line_no",
    "reference_line",
    "utt_id",
    "utt_id_role",
    "speaker",
    "utterance",
    "utterance_clean",
    "cleaned_is_empty",
]


class TestLSTMBaselinePipeline(unittest.TestCase):
    def test_normalize_variants_rejects_unknown_variant(self):
        self.assertEqual([variant.name for variant in normalize_variants(["same_length"])], ["same_length"])
        with self.assertRaises(ValueError):
            normalize_variants(["not_a_variant"])

    def test_normalize_variants_accepts_configured_variant_objects(self):
        variants = normalize_variants(
            [
                {
                    "name": "free_length",
                    "output_column": "lstm_free_length_utterance_12tok",
                    "generation_length_mode": "free_until_eos",
                    "max_generated_tokens": 12,
                    "min_generated_tokens": 2,
                }
            ]
        )

        self.assertEqual(variants[0].name, "free_length")
        self.assertEqual(variants[0].output_column, "lstm_free_length_utterance_12tok")
        self.assertEqual(variants[0].max_generated_tokens, 12)
        self.assertEqual(variants[0].min_generated_tokens, 2)

    def test_lstm_config_from_mapping_rejects_unknown_fields(self):
        with self.assertRaises(ValueError):
            lstm_config_from_mapping({"not_a_real_hyperparam": 1}, LSTMConfig())

    def test_load_pipeline_config_builds_editable_hyperparameter_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            bins_path = Path(tmp) / "age_bins.json"
            write_age_bins_config(
                bins_path,
                bins=[AgeBin(6, 23), AgeBin(24, 29)],
                strategy="toy_merged_early",
            )
            config_path = Path(tmp) / "lstm_config.json"
            payload = {
                "manifest": "data/big_cleaned_dataset/default_naturalistic_merged_006_023/manifest.csv",
                "data_dir": "data/big_cleaned_dataset/default_naturalistic_merged_006_023/preprocessed_data",
                "output_dir": "results/lstm_baselines/test_config",
                "datasets": ["Brown"],
                "variants": [
                    {
                        "name": "same_length",
                        "output_column": "lstm_same_length_test",
                        "generation_length_mode": "same_as_child",
                        "max_generated_tokens": 99,
                        "min_generated_tokens": 1,
                    }
                ],
                "age_binning": {
                    "mode": "additive_age_bins",
                    "bins_config": str(bins_path),
                },
                "dry_run": True,
                "model": {
                    "architecture": "seq2seq_lstm",
                    "context_utterances": 2,
                    "max_context_tokens": 40,
                    "embedding_dim": 64,
                    "hidden_dim": 128,
                    "batch_size": 16,
                    "epochs": 1,
                    "device": "cuda",
                },
            }
            config_path.write_text(json.dumps(payload), encoding="utf-8")

            settings = load_pipeline_config(config_path)

        self.assertEqual(settings["datasets"], ["Brown"])
        self.assertTrue(settings["dry_run"])
        self.assertEqual([variant.name for variant in settings["variants"]], ["same_length"])
        self.assertEqual(settings["variants"][0].output_column, "lstm_same_length_test")
        self.assertEqual(settings["variants"][0].max_generated_tokens, 99)
        self.assertEqual(settings["config"].context_utterances, 2)
        self.assertEqual(settings["config"].max_context_tokens, 40)
        self.assertEqual(settings["config"].embedding_dim, 64)
        self.assertEqual(settings["config"].device, "cuda")
        self.assertEqual(settings["age_binning"].mode, "additive_age_bins")
        self.assertEqual(settings["age_binning"].bins_config, str(bins_path))

    def test_additive_bin_helpers_use_cumulative_training_and_target_only_generation(self):
        unit = ChildUnit(
            dataset="Toy",
            child="Ada",
            folder=Path("Ada"),
            chi_csv=Path("Ada/chi.csv"),
            caretakers_csv=Path("Ada/caretakers.csv"),
        )
        examples = [
            LSTMExample(unit=unit, row_index=0, age_months=10.0, context_tokens=("a",), child_tokens=("early",)),
            LSTMExample(unit=unit, row_index=1, age_months=25.0, context_tokens=("b",), child_tokens=("mid",)),
            LSTMExample(unit=unit, row_index=2, age_months=31.0, context_tokens=("c",), child_tokens=("late",)),
        ]
        bins = [AgeBin(6, 23), AgeBin(24, 29), AgeBin(30, 35)]

        self.assertEqual(
            [example.row_index for example in examples_in_target_bin(examples, bins[1])],
            [1],
        )
        self.assertEqual(
            [example.row_index for example in examples_for_additive_training_bin(examples, bins[1], bins)],
            [0, 1],
        )
        runs = build_additive_bin_runs(examples, bins)

        self.assertEqual([len(run.train_examples) for run in runs], [1, 2, 3])
        self.assertEqual([len(run.target_examples) for run in runs], [1, 1, 1])

    def test_discover_units_from_manifest_uses_absolute_manifest_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            child_dir = base / "data" / "ToySet" / "Ada"
            chi_csv = child_dir / "chi.csv"
            caretakers_csv = child_dir / "caretakers.csv"
            chi_csv.parent.mkdir(parents=True)
            chi_csv.write_text("dataset,child_id\n", encoding="utf-8")
            caretakers_csv.write_text("dataset,child_id\n", encoding="utf-8")
            manifest = base / "manifest.csv"
            write_csv(
                manifest,
                ["dataset", "child_id", "chi_csv", "caretakers_csv"],
                [
                    {
                        "dataset": "ToySet",
                        "child_id": "Ada",
                        "chi_csv": str(chi_csv),
                        "caretakers_csv": str(caretakers_csv),
                    }
                ],
            )

            units = discover_units_from_manifest(manifest)

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].dataset, "ToySet")
        self.assertEqual(units[0].child, "Ada")
        self.assertEqual(units[0].chi_csv, chi_csv)
        self.assertEqual(units[0].caretakers_csv, caretakers_csv)

    def test_merge_lstm_columns_into_context_preserves_rows_and_order(self):
        context = pd.DataFrame(
            [
                {
                    "dataset": "Toy",
                    "child_id": "Ada",
                    "session_id": "1",
                    "file": "a.cha",
                    "line_no": "10",
                    "utt_id": "1",
                    "utterance_clean": "more.",
                },
                {
                    "dataset": "Toy",
                    "child_id": "Ada",
                    "session_id": "1",
                    "file": "a.cha",
                    "line_no": "12",
                    "utt_id": "2",
                    "utterance_clean": "milk.",
                },
            ]
        )
        generated = pd.DataFrame(
            [
                {
                    "dataset": "Toy",
                    "child_id": "Ada",
                    "session_id": "1",
                    "file": "a.cha",
                    "line_no": "10",
                    "utt_id": "1",
                    "lstm_same_length_utterance": "want.",
                },
                {
                    "dataset": "Toy",
                    "child_id": "Ada",
                    "session_id": "1",
                    "file": "a.cha",
                    "line_no": "12",
                    "utt_id": "2",
                    "lstm_same_length_utterance": "some.",
                },
            ]
        )

        merged = merge_lstm_columns_into_context(context, generated, ["lstm_same_length_utterance"])

        self.assertEqual(len(merged), 2)
        self.assertEqual(list(merged["utterance_clean"]), ["more.", "milk."])
        self.assertEqual(list(merged["lstm_same_length_utterance"]), ["want.", "some."])

    def test_build_child_scoring_rows_with_lstm_adds_lstm_columns(self):
        context = pd.DataFrame(
            [
                {
                    "dataset": "Toy",
                    "child_id": "Ada",
                    "source_group": "Toy",
                    "session_id": "1",
                    "age_months": "24",
                    "file": "a.cha",
                    "line_no": "10",
                    "utt_id": "1",
                    "context_k1": "want some",
                    "context_k2": "do you want some",
                    "context_k3": "",
                    "utterance_clean": "more.",
                    "random_model_utterance_bin6": "cat.",
                    "unigram_model_utterance_bin6": "dog.",
                    "bigram_model_utterance_bin6": "milk.",
                    "trigram_model_utterance_bin6": "more.",
                    "lstm_same_length_utterance": "want.",
                }
            ]
        )

        rows = build_child_scoring_rows_with_lstm(context, ["lstm_same_length_utterance"])

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["chi_utterance_clean"], "more.")
        self.assertEqual(rows[0]["lstm_same_length_utterance"], "want.")

    def test_build_child_scoring_rows_with_lstm_can_keep_age_bin_metadata(self):
        context = pd.DataFrame(
            [
                {
                    "dataset": "Toy",
                    "child_id": "Ada",
                    "source_group": "Toy",
                    "session_id": "1",
                    "age_months": "24",
                    "file": "a.cha",
                    "line_no": "10",
                    "utt_id": "1",
                    "context_k1": "want some",
                    "context_k2": "",
                    "context_k3": "",
                    "utterance_clean": "more.",
                    "lstm_age_bin": "024-029",
                    "lstm_same_length_utterance": "want.",
                }
            ]
        )

        rows = build_child_scoring_rows_with_lstm(
            context,
            ["lstm_same_length_utterance"],
            extra_columns=["lstm_age_bin"],
        )

        self.assertEqual(rows[0]["lstm_age_bin"], "024-029")

    def test_dry_run_pipeline_validates_examples_without_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            child_dir = base / "preprocessed_data" / "ToySet" / "Ada"
            chi_csv = child_dir / "chi.csv"
            caretakers_csv = child_dir / "caretakers.csv"
            row_base = {
                "dataset": "ToySet",
                "child_id": "Ada",
                "source_group": "ToySet",
                "session_id": "1",
                "age_raw": "2;00.00",
                "age_months": "24",
                "sex": "female",
                "file": "a.cha",
                "line_no": "10",
                "reference_line": "a.cha:10",
                "utt_id": "1",
                "utt_id_role": "1",
                "utterance": "more .",
                "cleaned_is_empty": "0",
            }
            write_csv(chi_csv, STAGE0_COLUMNS, [{**row_base, "speaker": "CHI", "utterance_clean": "more milk."}])
            write_csv(
                caretakers_csv,
                STAGE0_COLUMNS,
                [{**row_base, "speaker": "MOT", "utterance_clean": "want some?", "line_no": "5"}],
            )
            manifest = base / "manifest.csv"
            write_csv(
                manifest,
                ["dataset", "child_id", "chi_csv", "caretakers_csv"],
                [
                    {
                        "dataset": "ToySet",
                        "child_id": "Ada",
                        "chi_csv": str(chi_csv),
                        "caretakers_csv": str(caretakers_csv),
                    }
                ],
            )

            output_dir = base / "lstm_out"
            summary = run_lstm_baseline_pipeline(
                manifest_path=manifest,
                data_dir=base / "preprocessed_data",
                output_dir=output_dir,
                variants=normalize_variants(["same_length"]),
                dry_run=True,
                config=LSTMConfig(
                    data_dir=str(base / "preprocessed_data"),
                    datasets=("ToySet",),
                    output_dir=str(output_dir),
                    min_age_months=0,
                    max_age_months=120,
                ),
            )

            self.assertTrue(summary["dry_run"])
            self.assertEqual(summary["units"], 1)
            self.assertEqual(summary["train_examples"], 1)
            self.assertTrue((output_dir / "dry_run_summary.json").exists())

    def test_additive_age_bin_dry_run_reports_cumulative_training_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            child_dir = base / "preprocessed_data" / "ToySet" / "Ada"
            chi_csv = child_dir / "chi.csv"
            caretakers_csv = child_dir / "caretakers.csv"
            rows = []
            for idx, (age, line_no, text) in enumerate(
                [(10, "10", "early word."), (25, "20", "middle word."), (31, "30", "later word.")],
                start=1,
            ):
                rows.append(
                    {
                        "dataset": "ToySet",
                        "child_id": "Ada",
                        "source_group": "ToySet",
                        "session_id": "1",
                        "age_raw": "",
                        "age_months": str(age),
                        "sex": "",
                        "file": "a.cha",
                        "line_no": line_no,
                        "reference_line": f"a.cha:{line_no}",
                        "utt_id": str(idx),
                        "utt_id_role": str(idx),
                        "speaker": "CHI",
                        "utterance": text,
                        "utterance_clean": text,
                        "cleaned_is_empty": "0",
                    }
                )
            write_csv(chi_csv, STAGE0_COLUMNS, rows)
            write_csv(
                caretakers_csv,
                STAGE0_COLUMNS,
                [
                    {**rows[0], "speaker": "MOT", "utterance_clean": "context early", "line_no": "5"},
                    {**rows[1], "speaker": "MOT", "utterance_clean": "context middle", "line_no": "15"},
                    {**rows[2], "speaker": "MOT", "utterance_clean": "context later", "line_no": "25"},
                ],
            )
            manifest = base / "manifest.csv"
            write_csv(
                manifest,
                ["dataset", "child_id", "chi_csv", "caretakers_csv"],
                [
                    {
                        "dataset": "ToySet",
                        "child_id": "Ada",
                        "chi_csv": str(chi_csv),
                        "caretakers_csv": str(caretakers_csv),
                    }
                ],
            )
            bins_path = base / "age_bins.json"
            write_age_bins_config(
                bins_path,
                bins=[AgeBin(6, 23), AgeBin(24, 29), AgeBin(30, 35)],
                strategy="toy",
            )
            output_dir = base / "lstm_additive_out"

            summary = run_lstm_baseline_pipeline(
                manifest_path=manifest,
                data_dir=base / "preprocessed_data",
                output_dir=output_dir,
                variants=normalize_variants(["same_length"]),
                dry_run=True,
                config=LSTMConfig(
                    data_dir=str(base / "preprocessed_data"),
                    datasets=("ToySet",),
                    output_dir=str(output_dir),
                    min_age_months=0,
                    max_age_months=120,
                ),
                age_binning=LSTMAgeBinning(mode="additive_age_bins", bins_config=str(bins_path)),
            )

            payload = json.loads((output_dir / "dry_run_summary.json").read_text(encoding="utf-8"))

        self.assertTrue(summary["dry_run"])
        self.assertEqual(summary["age_binning_mode"], "additive_age_bins")
        self.assertEqual(summary["age_bins"], 3)
        self.assertEqual(
            [(row["label"], row["train_examples"], row["target_examples"]) for row in payload["additive_age_bins"]],
            [("006-023", 1, 1), ("024-029", 2, 1), ("030-035", 3, 1)],
        )


if __name__ == "__main__":
    unittest.main()
