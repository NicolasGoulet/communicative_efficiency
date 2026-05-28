import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from new_create_parallel_data import is_generated_variant_column, load_chi_with_generated_variants


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestParallelDataCreation(unittest.TestCase):
    def test_is_generated_variant_column_recognizes_ngram_and_lstm_outputs(self):
        self.assertTrue(is_generated_variant_column("random_model_utterance_bin6"))
        self.assertTrue(is_generated_variant_column("trigram_model_utterance_bin12"))
        self.assertTrue(is_generated_variant_column("lstm_model_utterance"))
        self.assertFalse(is_generated_variant_column("utterance_clean"))

    def test_load_chi_with_generated_variants_merges_ngram_and_lstm_siblings(self):
        with tempfile.TemporaryDirectory() as tmp:
            child_dir = Path(tmp) / "ToyChild"
            child_dir.mkdir()
            base_fields = ["session_id", "utterance_clean"]
            write_csv(
                child_dir / "chi.csv",
                [{"session_id": 1, "utterance_clean": "real words"}],
                base_fields,
            )
            write_csv(
                child_dir / "chi.ngram_generated.csv",
                [
                    {
                        "session_id": 1,
                        "utterance_clean": "real words",
                        "bigram_model_utterance_bin6": "ngram words",
                    }
                ],
                base_fields + ["bigram_model_utterance_bin6"],
            )
            write_csv(
                child_dir / "chi.lstm_generated.csv",
                [
                    {
                        "session_id": 1,
                        "utterance_clean": "real words",
                        "lstm_model_utterance": "lstm words",
                    }
                ],
                base_fields + ["lstm_model_utterance"],
            )

            merged, source_by_column = load_chi_with_generated_variants(child_dir)

        self.assertEqual(merged.loc[0, "utterance_clean"], "real words")
        self.assertEqual(merged.loc[0, "bigram_model_utterance_bin6"], "ngram words")
        self.assertEqual(merged.loc[0, "lstm_model_utterance"], "lstm words")
        self.assertEqual(source_by_column["bigram_model_utterance_bin6"], "chi.ngram_generated.csv")
        self.assertEqual(source_by_column["lstm_model_utterance"], "chi.lstm_generated.csv")

    def test_load_chi_with_generated_variants_rejects_misaligned_row_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            child_dir = Path(tmp) / "ToyChild"
            child_dir.mkdir()
            fields = ["session_id", "utterance_clean"]
            write_csv(
                child_dir / "chi.csv",
                [{"session_id": 1, "utterance_clean": "one"}],
                fields,
            )
            write_csv(
                child_dir / "chi.lstm_generated.csv",
                [
                    {"session_id": 1, "utterance_clean": "one", "lstm_model_utterance": "a"},
                    {"session_id": 2, "utterance_clean": "two", "lstm_model_utterance": "b"},
                ],
                fields + ["lstm_model_utterance"],
            )

            with self.assertRaises(ValueError):
                load_chi_with_generated_variants(child_dir)


if __name__ == "__main__":
    unittest.main()
