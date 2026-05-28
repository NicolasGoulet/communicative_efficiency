import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_age_word_dicts import ChildUnit
from create_minimal_surprisal_scoring_csvs import (
    CARETAKER_OUTPUT_COLUMNS,
    CHILD_OUTPUT_COLUMNS,
    build_caretaker_scoring_rows,
    build_child_scoring_rows,
    write_scoring_files_for_unit,
)


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


class TestMinimalSurprisalScoringCSVs(unittest.TestCase):
    def build_unit(self, tmp_dir: Path) -> ChildUnit:
        child_dir = tmp_dir / "ToySet" / "ToyChild"
        child_context_columns = [
            "dataset",
            "child_id",
            "source_group",
            "session_id",
            "age_months",
            "file",
            "line_no",
            "utt_id",
            "utt_id_role",
            "speaker",
            "utterance",
            "utterance_clean",
            "random_model_utterance_bin6",
            "unigram_model_utterance_bin6",
            "bigram_model_utterance_bin6",
            "trigram_model_utterance_bin6",
            "context_k1",
            "context_k2",
            "context_k3",
            "",
        ]
        write_csv(
            child_dir / "chi.shared_caretaker_contexts.csv",
            child_context_columns,
            [
                {
                    "dataset": "ToySet",
                    "child_id": "ToyChild",
                    "source_group": "",
                    "session_id": "1",
                    "age_months": "24.0",
                    "file": "ToyChild/a.cha",
                    "line_no": "10",
                    "utt_id": "2",
                    "utt_id_role": "99",
                    "speaker": "CHI",
                    "utterance": "more milk .",
                    "utterance_clean": "more milk.",
                    "random_model_utterance_bin6": "red blue.",
                    "unigram_model_utterance_bin6": "more more.",
                    "bigram_model_utterance_bin6": "more milk.",
                    "trigram_model_utterance_bin6": "more milk.",
                    "context_k1": "want some?",
                    "context_k2": "want some?",
                    "context_k3": "want some?",
                    "": "stray",
                },
                {
                    "dataset": "ToySet",
                    "child_id": "ToyChild",
                    "source_group": "",
                    "session_id": "1",
                    "age_months": "24.0",
                    "file": "ToyChild/a.cha",
                    "line_no": "11",
                    "utt_id": "3",
                    "utt_id_role": "100",
                    "speaker": "CHI",
                    "utterance": "xxx .",
                    "utterance_clean": "",
                    "random_model_utterance_bin6": "",
                    "unigram_model_utterance_bin6": "",
                    "bigram_model_utterance_bin6": "",
                    "trigram_model_utterance_bin6": "",
                    "context_k1": "want some?",
                    "context_k2": "want some?",
                    "context_k3": "want some?",
                    "": "stray",
                },
            ],
        )

        caretaker_context_columns = [
            "dataset",
            "child_id",
            "source_group",
            "session_id",
            "age_months",
            "file",
            "line_no",
            "utt_id",
            "utt_id_role",
            "speaker",
            "utterance",
            "utterance_clean",
            "context_k1",
            "context_k2",
            "context_k3",
        ]
        write_csv(
            child_dir / "caretakers.shared_caretaker_contexts.csv",
            caretaker_context_columns,
            [
                {
                    "dataset": "ToySet",
                    "child_id": "ToyChild",
                    "source_group": "",
                    "session_id": "1",
                    "age_months": "24.0",
                    "file": "ToyChild/a.cha",
                    "line_no": "5",
                    "utt_id": "1",
                    "utt_id_role": "1",
                    "speaker": "MOT",
                    "utterance": "want some ?",
                    "utterance_clean": "want some?",
                    "context_k1": "",
                    "context_k2": "",
                    "context_k3": "",
                },
                {
                    "dataset": "ToySet",
                    "child_id": "ToyChild",
                    "source_group": "",
                    "session_id": "1",
                    "age_months": "24.0",
                    "file": "ToyChild/a.cha",
                    "line_no": "6",
                    "utt_id": "2",
                    "utt_id_role": "2",
                    "speaker": "MOT",
                    "utterance": "0 .",
                    "utterance_clean": "",
                    "context_k1": "want some?",
                    "context_k2": "want some?",
                    "context_k3": "want some?",
                },
            ],
        )

        return ChildUnit(
            dataset="ToySet",
            child="ToyChild",
            folder=child_dir,
            chi_csv=child_dir / "chi.csv",
            caretakers_csv=child_dir / "caretakers.csv",
        )

    def test_build_child_scoring_rows_renames_target_and_drops_empty_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = self.build_unit(Path(tmp))
            import pandas as pd

            df = pd.read_csv(unit.folder / "chi.shared_caretaker_contexts.csv", dtype=str, keep_default_na=False)
            rows = build_child_scoring_rows(df)

        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), set(CHILD_OUTPUT_COLUMNS))
        self.assertEqual(rows[0]["source_group"], "ToySet")
        self.assertEqual(rows[0]["chi_utterance_clean"], "more milk.")
        self.assertEqual(rows[0]["random_model_utterance_bin6"], "red blue.")
        self.assertEqual(rows[0]["context_k1"], "want some?")

    def test_build_caretaker_scoring_rows_renames_target_and_drops_empty_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = self.build_unit(Path(tmp))
            import pandas as pd

            df = pd.read_csv(
                unit.folder / "caretakers.shared_caretaker_contexts.csv",
                dtype=str,
                keep_default_na=False,
            )
            rows = build_caretaker_scoring_rows(df)

        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]), set(CARETAKER_OUTPUT_COLUMNS))
        self.assertEqual(rows[0]["source_group"], "ToySet")
        self.assertEqual(rows[0]["speaker"], "MOT")
        self.assertEqual(rows[0]["caretaker_utterance_clean"], "want some?")

    def test_write_scoring_files_for_unit_has_exact_headers_and_no_extra_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = self.build_unit(Path(tmp))

            summary = write_scoring_files_for_unit(unit)

            child_output = unit.folder / "chi.surprisal_scoring.csv"
            caretaker_output = unit.folder / "caretakers.surprisal_scoring.csv"
            with child_output.open(newline="", encoding="utf-8") as handle:
                child_rows = list(csv.reader(handle))
            with caretaker_output.open(newline="", encoding="utf-8") as handle:
                caretaker_rows = list(csv.reader(handle))

        self.assertEqual(summary["child_rows"], 1)
        self.assertEqual(summary["caretaker_rows"], 1)
        self.assertEqual(child_rows[0], CHILD_OUTPUT_COLUMNS)
        self.assertEqual(caretaker_rows[0], CARETAKER_OUTPUT_COLUMNS)
        self.assertNotIn("utt_id_role", child_rows[0])
        self.assertNotIn("utt_id_role", caretaker_rows[0])
        self.assertFalse(any(header == "" for header in child_rows[0]))
        self.assertFalse(any(header == "" for header in caretaker_rows[0]))
        self.assertTrue(all(len(row) == len(child_rows[0]) for row in child_rows))
        self.assertTrue(all(len(row) == len(caretaker_rows[0]) for row in caretaker_rows))
        self.assertEqual(child_rows[1][CHILD_OUTPUT_COLUMNS.index("chi_utterance_clean")], "more milk.")
        self.assertEqual(
            caretaker_rows[1][CARETAKER_OUTPUT_COLUMNS.index("caretaker_utterance_clean")],
            "want some?",
        )


if __name__ == "__main__":
    unittest.main()
