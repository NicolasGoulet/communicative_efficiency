import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_age_word_dicts import ChildUnit
from custom_age_bins import AgeBin
from generate_lstm_utterances import LSTMConfig, LSTMExample, Vocabulary
from run_lstm_additive_age_context_pipeline import (
    additive_column_name,
    child_output_token_ids,
    cumulative_train_examples,
    run_additive_age_context_pipeline,
    target_bin_examples,
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


class TestLSTMAdditiveAgeContextPipeline(unittest.TestCase):
    def test_additive_column_name_includes_context_and_variant(self):
        self.assertEqual(
            additive_column_name(3, "same_length"),
            "lstm_additive_k3_same_length_utterance",
        )
        self.assertEqual(
            additive_column_name(5, "free_length"),
            "lstm_additive_k5_free_length_utterance",
        )
        with self.assertRaises(ValueError):
            additive_column_name(3, "not_a_variant")

    def test_cumulative_and_target_age_bin_example_selection(self):
        unit = ChildUnit("Toy", "Ada", Path("Ada"), Path("Ada/chi.csv"), Path("Ada/caretakers.csv"))
        examples = [
            LSTMExample(unit, row_index=0, age_months=7.2, context_tokens=(), child_tokens=("a",)),
            LSTMExample(unit, row_index=1, age_months=24.0, context_tokens=(), child_tokens=("b",)),
            LSTMExample(unit, row_index=2, age_months=29.9, context_tokens=(), child_tokens=("c",)),
            LSTMExample(unit, row_index=3, age_months=30.0, context_tokens=(), child_tokens=("d",)),
        ]
        bins = [AgeBin(6, 23), AgeBin(24, 29), AgeBin(30, 35)]

        cumulative = cumulative_train_examples(examples, first_start=6, age_bin=bins[1])
        target = target_bin_examples(examples, bins=bins, age_bin=bins[1])

        self.assertEqual([example.row_index for example in cumulative], [0, 1, 2])
        self.assertEqual([example.row_index for example in target], [1, 2])

    def test_child_output_token_ids_excludes_parent_only_context_words(self):
        unit = ChildUnit("Toy", "Ada", Path("Ada"), Path("Ada/chi.csv"), Path("Ada/caretakers.csv"))
        examples = [
            LSTMExample(
                unit,
                row_index=0,
                age_months=7.0,
                context_tokens=("parentonly", "shared"),
                child_tokens=("childonly", "shared"),
            )
        ]
        vocab = Vocabulary.build(example.context_tokens + example.child_tokens for example in examples)

        allowed_ids = child_output_token_ids(examples, vocab)

        self.assertIn(vocab.token_to_id["childonly"], allowed_ids)
        self.assertIn(vocab.token_to_id["shared"], allowed_ids)
        self.assertNotIn(vocab.token_to_id["parentonly"], allowed_ids)

    def test_dry_run_writes_additive_plan_without_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            child_dir = base / "preprocessed_data" / "Toy" / "Ada"
            row_base = {
                "dataset": "Toy",
                "child_id": "Ada",
                "source_group": "Toy",
                "session_id": "1",
                "age_raw": "",
                "sex": "",
                "file": "a.cha",
                "reference_line": "",
                "utt_id_role": "",
                "utterance": "",
                "cleaned_is_empty": "0",
            }
            write_csv(
                child_dir / "caretakers.csv",
                STAGE0_COLUMNS,
                [
                    {
                        **row_base,
                        "age_months": "7",
                        "line_no": "1",
                        "utt_id": "1",
                        "speaker": "MOT",
                        "utterance_clean": "want some",
                    },
                    {
                        **row_base,
                        "age_months": "24",
                        "line_no": "3",
                        "utt_id": "3",
                        "speaker": "MOT",
                        "utterance_clean": "look here",
                    },
                ],
            )
            write_csv(
                child_dir / "chi.csv",
                STAGE0_COLUMNS,
                [
                    {
                        **row_base,
                        "age_months": "7",
                        "line_no": "2",
                        "utt_id": "2",
                        "speaker": "CHI",
                        "utterance_clean": "more milk",
                    },
                    {
                        **row_base,
                        "age_months": "24",
                        "line_no": "4",
                        "utt_id": "4",
                        "speaker": "CHI",
                        "utterance_clean": "there",
                    },
                ],
            )
            manifest = base / "manifest.csv"
            write_csv(
                manifest,
                ["dataset", "child_id", "chi_csv", "caretakers_csv"],
                [
                    {
                        "dataset": "Toy",
                        "child_id": "Ada",
                        "chi_csv": str(child_dir / "chi.csv"),
                        "caretakers_csv": str(child_dir / "caretakers.csv"),
                    }
                ],
            )

            out_dir = base / "out"
            summary = run_additive_age_context_pipeline(
                manifest_path=manifest,
                datasets=("Toy",),
                output_dir=out_dir,
                context_utterances_values=(3,),
                variants=("same_length",),
                dry_run=True,
                base_config=LSTMConfig(
                    data_dir=str(base / "preprocessed_data"),
                    datasets=("Toy",),
                    output_dir=str(out_dir),
                    context_utterances=3,
                    max_context_tokens=60,
                    min_age_months=6,
                    max_age_months=29.999,
                ),
                bins=[AgeBin(6, 23), AgeBin(24, 29)],
            )

            self.assertTrue(summary["dry_run"])
            self.assertEqual(summary["plan_rows"], 2)
            with (out_dir / "additive_plan_summary.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual([row["age_bin"] for row in rows], ["006-023", "024-029"])
        self.assertEqual([row["train_examples_after_limit"] for row in rows], ["1", "2"])
        self.assertEqual([row["target_examples"] for row in rows], ["1", "1"])


if __name__ == "__main__":
    unittest.main()
