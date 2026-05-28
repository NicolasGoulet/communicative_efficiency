import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from utterance_count_strategies import (
    PROBE_COLUMNS,
    build_probe,
    count_morphemes_clitic_split,
    count_morphemes_suffix_heuristic,
    count_morphemes_words,
    count_utterance,
    count_words_regex,
    count_words_whitespace,
    select_probe_rows,
    word_syllables_final_le,
    word_syllables_silent_e,
    word_syllables_vowel_groups,
    word_syllables_no_y,
)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "dataset",
        "child_id",
        "source_group",
        "session_id",
        "age_months",
        "file",
        "line_no",
        "utt_id",
        "speaker",
        "utterance_clean",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestUtteranceCountStrategies(unittest.TestCase):
    def test_word_counts_include_apostrophes_and_expose_whitespace_disagreements(self):
        self.assertEqual(count_words_regex("I can't go."), 3)
        self.assertEqual(count_words_whitespace("I can't go."), 3)
        self.assertEqual(count_words_regex("red-blue."), 2)
        self.assertEqual(count_words_whitespace("red-blue."), 1)

    def test_morpheme_counts_have_word_clitic_and_suffix_strategies(self):
        self.assertEqual(count_morphemes_words("I'm walking dogs."), 3)
        self.assertEqual(count_morphemes_clitic_split("I'm walking dogs."), 4)
        self.assertEqual(count_morphemes_suffix_heuristic("I'm walking dogs."), 6)

    def test_morpheme_suffix_strategy_does_not_count_common_exceptions(self):
        self.assertEqual(count_morphemes_suffix_heuristic("this is his."), 3)
        self.assertEqual(count_morphemes_suffix_heuristic("cats walked."), 4)

    def test_syllable_word_strategies_are_explicit_about_silent_e_and_final_le(self):
        self.assertEqual(word_syllables_vowel_groups("cake"), 2)
        self.assertEqual(word_syllables_silent_e("cake"), 1)
        self.assertEqual(word_syllables_silent_e("little"), 1)
        self.assertEqual(word_syllables_final_le("little"), 2)

    def test_syllable_no_y_strategy_differs_for_y_words(self):
        self.assertEqual(word_syllables_vowel_groups("happy"), 2)
        self.assertEqual(word_syllables_no_y("happy"), 1)

    def test_count_utterance_returns_all_strategy_counts(self):
        result = count_utterance("I'm walking dogs.")

        self.assertEqual(result.word_count_regex, 3)
        self.assertEqual(result.morpheme_count_words, 3)
        self.assertEqual(result.morpheme_count_clitic_split, 4)
        self.assertEqual(result.morpheme_count_suffix_heuristic, 6)
        self.assertGreater(result.count_strategy_disagreement, 0)

    def test_select_probe_rows_prioritizes_disagreement_then_fills_randomly(self):
        rows = [
            {
                "dataset": "Toy",
                "child_id": "A",
                "source_csv": "chi.csv",
                "source_row": i,
                "count_strategy_disagreement": score,
            }
            for i, score in enumerate([0, 5, 1, 4, 0, 3])
        ]

        selected = select_probe_rows(rows, sample_size=4, seed=1)

        selected_ids = {row["source_row"] for row in selected}
        self.assertIn(1, selected_ids)
        self.assertIn(3, selected_ids)
        self.assertEqual(len(selected), 4)

    def test_build_probe_writes_exact_schema_with_real_source_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            child_dir = base / "Brown" / "ToyChild"
            common = {
                "dataset": "Brown",
                "child_id": "ToyChild",
                "source_group": "",
                "session_id": "1",
                "age_months": "24.0",
                "file": "ToyChild/a.cha",
            }
            write_csv(
                child_dir / "chi.csv",
                [
                    {
                        **common,
                        "line_no": "10",
                        "utt_id": "1",
                        "speaker": "CHI",
                        "utterance_clean": "I'm walking dogs.",
                    },
                    {
                        **common,
                        "line_no": "20",
                        "utt_id": "2",
                        "speaker": "CHI",
                        "utterance_clean": "!!!",
                    },
                ],
            )
            write_csv(
                child_dir / "caretakers.csv",
                [
                    {
                        **common,
                        "line_no": "5",
                        "utt_id": "1",
                        "speaker": "MOT",
                        "utterance_clean": "red-blue.",
                    }
                ],
            )
            output = base / "probe.csv"

            rows = build_probe(
                data_dir=base,
                datasets=("Brown",),
                speakers=("CHI", "MOT", "FAT"),
                sample_size=10,
                seed=1,
                min_words=1,
                output_csv=output,
            )

            with output.open(newline="", encoding="utf-8") as handle:
                parsed = list(csv.reader(handle))
            with output.open(newline="", encoding="utf-8") as handle:
                dict_rows = list(csv.DictReader(handle))

        self.assertEqual(parsed[0], PROBE_COLUMNS)
        self.assertFalse(any(header == "" for header in parsed[0]))
        self.assertTrue(all(len(row) == len(parsed[0]) for row in parsed))
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(dict_rows), 2)
        self.assertEqual(dict_rows[0]["dataset"], "Brown")
        self.assertIn("word_count_regex", dict_rows[0])
        self.assertNotEqual(dict_rows[0]["utterance_clean"], "")


if __name__ == "__main__":
    unittest.main()
