import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_age_word_dicts import ChildUnit
from create_shared_caretaker_contexts import (
    DEFAULT_GENERATED_COLUMNS,
    iter_context_rows_for_unit,
    output_columns,
    write_context_files_for_unit,
)


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


BASE_FIELDS_WITH_ROLE_ID = [
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


CHI_GENERATED_FIELDS = [
    column for column in BASE_FIELDS_WITH_ROLE_ID if column != "utt_id_role"
] + DEFAULT_GENERATED_COLUMNS


class TestSharedCaretakerContexts(unittest.TestCase):
    def build_unit(self, tmp_dir: Path) -> ChildUnit:
        child_dir = tmp_dir / "ToySet" / "ToyChild"
        write_csv(
            child_dir / "caretakers.csv",
            [
                {
                    "dataset": "ToySet",
                    "child_id": "ToyChild",
                    "source_group": "",
                    "session_id": "1",
                    "age_raw": "2;00.00",
                    "age_months": "24.0",
                    "sex": "female",
                    "file": "ToyChild/a.cha",
                    "line_no": "5",
                    "reference_line": "ToyChild/a.cha:5",
                    "utt_id": "1",
                    "utt_id_role": "1",
                    "speaker": "MOT",
                    "utterance": "want some ?",
                    "utterance_clean": "want some?",
                    "cleaned_is_empty": "0",
                },
                {
                    "dataset": "ToySet",
                    "child_id": "ToyChild",
                    "source_group": "",
                    "session_id": "1",
                    "age_raw": "2;00.00",
                    "age_months": "24.0",
                    "sex": "female",
                    "file": "ToyChild/a.cha",
                    "line_no": "25",
                    "reference_line": "ToyChild/a.cha:25",
                    "utt_id": "4",
                    "utt_id_role": "2",
                    "speaker": "FAT",
                    "utterance": "do it .",
                    "utterance_clean": "do it.",
                    "cleaned_is_empty": "0",
                },
            ],
            BASE_FIELDS_WITH_ROLE_ID,
        )
        write_csv(
            child_dir / "chi.ngram_generated.csv",
            [
                {
                    "dataset": "ToySet",
                    "child_id": "ToyChild",
                    "source_group": "ToySet",
                    "session_id": "1",
                    "age_raw": "2;00.00",
                    "age_months": "24.0",
                    "sex": "female",
                    "file": "ToyChild/a.cha",
                    "line_no": "10",
                    "reference_line": "ToyChild/a.cha:10",
                    "utt_id": "2",
                    "speaker": "CHI",
                    "utterance": "more milk .",
                    "utterance_clean": "more milk.",
                    "cleaned_is_empty": "0",
                    "random_model_utterance_bin6": "red blue.",
                    "unigram_model_utterance_bin6": "more more.",
                    "bigram_model_utterance_bin6": "more milk.",
                    "trigram_model_utterance_bin6": "more milk.",
                },
                {
                    "dataset": "ToySet",
                    "child_id": "ToyChild",
                    "source_group": "ToySet",
                    "session_id": "1",
                    "age_raw": "2;00.00",
                    "age_months": "24.0",
                    "sex": "female",
                    "file": "ToyChild/a.cha",
                    "line_no": "30",
                    "reference_line": "ToyChild/a.cha:30",
                    "utt_id": "5",
                    "speaker": "CHI",
                    "utterance": "again .",
                    "utterance_clean": "again.",
                    "cleaned_is_empty": "0",
                    "random_model_utterance_bin6": "green.",
                    "unigram_model_utterance_bin6": "again.",
                    "bigram_model_utterance_bin6": "it.",
                    "trigram_model_utterance_bin6": "again.",
                },
            ],
            CHI_GENERATED_FIELDS,
        )
        return ChildUnit(
            dataset="ToySet",
            child="ToyChild",
            folder=child_dir,
            chi_csv=child_dir / "chi.csv",
            caretakers_csv=child_dir / "caretakers.csv",
        )

    def test_iter_context_rows_uses_same_caretaker_context_for_child_generated_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = self.build_unit(Path(tmp))

            rows = list(iter_context_rows_for_unit(unit, ks=[1, 2, 3]))

        self.assertEqual([row["line_no"] for row in rows], ["5", "10", "25", "30"])
        self.assertEqual([row["speaker"] for row in rows], ["MOT", "CHI", "FAT", "CHI"])

        first_child = rows[1]
        self.assertEqual(first_child["speaker_group"], "CHILD")
        self.assertEqual(first_child["utterance_clean"], "more milk.")
        self.assertEqual(first_child["random_model_utterance_bin6"], "red blue.")
        self.assertEqual(first_child["trigram_model_utterance_bin6"], "more milk.")
        self.assertEqual(first_child["context_k1"], "want some?")
        self.assertEqual(first_child["context_k2"], "want some?")
        self.assertEqual(first_child["context_k3"], "want some?")

        caretaker = rows[2]
        self.assertEqual(caretaker["speaker_group"], "CARETAKER")
        self.assertEqual(caretaker["utterance_clean"], "do it.")
        self.assertEqual(caretaker["random_model_utterance_bin6"], "")
        self.assertEqual(caretaker["context_k1"], "want some?")

        second_child = rows[3]
        self.assertEqual(second_child["context_k1"], "do it.")
        self.assertEqual(second_child["context_k2"], "want some? do it.")
        self.assertEqual(second_child["context_k3"], "want some? do it.")

    def test_write_role_specific_context_csvs_have_exact_headers_and_no_role_id_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            unit = self.build_unit(base)

            summary = write_context_files_for_unit(unit, ks=[1, 2, 3])

            child_output = unit.folder / "chi.shared_caretaker_contexts.csv"
            caretaker_output = unit.folder / "caretakers.shared_caretaker_contexts.csv"
            with child_output.open(newline="", encoding="utf-8") as handle:
                child_parsed = list(csv.reader(handle))
            with child_output.open(newline="", encoding="utf-8") as handle:
                child_rows = list(csv.DictReader(handle))
            with caretaker_output.open(newline="", encoding="utf-8") as handle:
                caretaker_parsed = list(csv.reader(handle))
            with caretaker_output.open(newline="", encoding="utf-8") as handle:
                caretaker_rows = list(csv.DictReader(handle))

        self.assertEqual(summary["child_rows"], 2)
        self.assertEqual(summary["caretaker_rows"], 2)
        self.assertEqual(child_parsed[0], output_columns(DEFAULT_GENERATED_COLUMNS, [1, 2, 3], "CHILD"))
        self.assertEqual(caretaker_parsed[0], output_columns(DEFAULT_GENERATED_COLUMNS, [1, 2, 3], "CARETAKER"))
        self.assertNotIn("utt_id_role", child_parsed[0])
        self.assertNotIn("utt_id_role", caretaker_parsed[0])
        self.assertNotIn("random_model_utterance_bin6", caretaker_parsed[0])
        self.assertFalse(any(header == "" for header in child_parsed[0]))
        self.assertFalse(any(header == "" for header in caretaker_parsed[0]))
        self.assertTrue(all(len(row) == len(child_parsed[0]) for row in child_parsed))
        self.assertTrue(all(len(row) == len(caretaker_parsed[0]) for row in caretaker_parsed))
        self.assertEqual(child_rows[0]["speaker"], "CHI")
        self.assertEqual(child_rows[0]["utterance"], "more milk .")
        self.assertEqual(child_rows[0]["utterance_clean"], "more milk.")
        self.assertEqual(child_rows[0]["context_k1"], "want some?")
        self.assertEqual(caretaker_rows[0]["speaker"], "MOT")
        self.assertEqual(caretaker_rows[0]["context_k1"], "")


if __name__ == "__main__":
    unittest.main()
