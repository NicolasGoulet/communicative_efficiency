import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_age_word_dicts import ChildUnit, bin_label, bin_start, build_dicts, tokenize


class TestVocabularyBuilding(unittest.TestCase):
    def test_tokenize_extracts_simple_words(self):
        tokens = tokenize("Dog, dog! I can't.", lowercase=True)

        self.assertEqual(tokens, ["dog", "dog", "i", "can't"])

    def test_age_bin_helpers_make_readable_labels(self):
        start = bin_start(age_months=13.2, bin_months=6, min_age_months=6.0)

        self.assertEqual(start, 12)
        self.assertEqual(bin_label(start, bin_months=6), "012-017")

    def test_build_dicts_writes_counts_probs_and_vocab(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            child_dir = tmp_dir / "data" / "ToySet" / "ToyChild"
            child_dir.mkdir(parents=True)

            child_utts_csv = child_dir / "child_utts.csv"
            session_index_csv = child_dir / "session_index.csv"

            with child_utts_csv.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["session_id", "utterance_clean"])
                writer.writeheader()
                writer.writerow({"session_id": 1, "utterance_clean": "Dog dog cat"})
                writer.writerow({"session_id": 2, "utterance_clean": "Cat runs"})

            with session_index_csv.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["session_id", "age_months"])
                writer.writeheader()
                writer.writerow({"session_id": 1, "age_months": 7})
                writer.writerow({"session_id": 2, "age_months": 13})

            unit = ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=child_dir,
                child_utts_csv=child_utts_csv,
                session_index_csv=session_index_csv,
            )
            out_dir = tmp_dir / "dicts"

            build_dicts(
                units=[unit],
                out_dir=out_dir,
                bin_months=6,
                min_age_months=6.0,
                max_age_months=18.0,
                by_child=False,
                lowercase=True,
                min_token_len=1,
                text_col="utterance_clean",
            )

            counts_006 = json.loads((out_dir / "bin_006-011" / "counts.json").read_text())
            counts_012 = json.loads((out_dir / "bin_012-017" / "counts.json").read_text())
            vocab_006 = (out_dir / "bin_006-011" / "vocab.txt").read_text().splitlines()

        self.assertEqual(counts_006, {"cat": 1, "dog": 2})
        self.assertEqual(counts_012, {"cat": 1, "runs": 1})
        self.assertEqual(vocab_006, ["dog", "cat"])


if __name__ == "__main__":
    unittest.main()
