import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_age_word_dicts import (
    ChildUnit,
    bin_label,
    bin_start,
    build_dicts,
    contextual_bigram_pairs,
    contextual_trigram_triples,
    load_child_utterance_contexts,
    tokenize,
)
from custom_age_bins import AgeBin


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "session_id",
        "file",
        "line_no",
        "utt_id",
        "speaker",
        "age_months",
        "utterance_clean",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestVocabularyBuilding(unittest.TestCase):
    def test_tokenize_extracts_words_without_terminal_punctuation(self):
        tokens = tokenize("Dog, dog! I can't.", lowercase=True)

        self.assertEqual(tokens, ["dog", "dog", "i", "can't"])

    def test_age_bin_helpers_make_readable_six_month_labels(self):
        start = bin_start(age_months=13.2, bin_months=6, min_age_months=6.0)

        self.assertEqual(start, 12)
        self.assertEqual(bin_label(start, bin_months=6), "012-017")

    def test_contextual_bigram_pairs_use_last_caretaker_word_for_first_child_word(self):
        pairs = contextual_bigram_pairs(
            child_tokens=["more", "milk"],
            previous_caretaker_tokens=["want", "some"],
        )

        self.assertEqual(pairs, [("some", "more"), ("more", "milk")])

    def test_contextual_bigram_pairs_do_not_invent_context_when_no_caretaker_exists(self):
        pairs = contextual_bigram_pairs(
            child_tokens=["more", "milk"],
            previous_caretaker_tokens=[],
        )

        self.assertEqual(pairs, [("more", "milk")])

    def test_contextual_trigram_triples_use_p2_p1_then_p1_c1_at_child_boundary(self):
        triples = contextual_trigram_triples(
            child_tokens=["want", "more", "milk"],
            previous_caretaker_tokens=["do", "you"],
        )

        self.assertEqual(
            triples,
            [
                ("do", "you", "want"),
                ("you", "want", "more"),
                ("want", "more", "milk"),
            ],
        )

    def test_contextual_trigram_triples_handle_one_word_caretaker_context(self):
        triples = contextual_trigram_triples(
            child_tokens=["want", "more", "milk"],
            previous_caretaker_tokens=["you"],
        )

        self.assertEqual(
            triples,
            [
                ("you", "want", "more"),
                ("want", "more", "milk"),
            ],
        )

    def test_load_child_utterance_contexts_uses_latest_prior_caretaker_within_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            child_dir = Path(tmp) / "ToySet" / "ToyChild"
            write_csv(
                child_dir / "caretakers.csv",
                [
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 5,
                        "utt_id": 1,
                        "speaker": "MOT",
                        "age_months": 7,
                        "utterance_clean": "want some",
                    },
                    {
                        "session_id": 2,
                        "file": "b.cha",
                        "line_no": 5,
                        "utt_id": 1,
                        "speaker": "MOT",
                        "age_months": 13,
                        "utterance_clean": "please go",
                    },
                ],
            )
            write_csv(
                child_dir / "chi.csv",
                [
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 10,
                        "utt_id": 2,
                        "speaker": "CHI",
                        "age_months": 7,
                        "utterance_clean": "more milk",
                    },
                    {
                        "session_id": 2,
                        "file": "b.cha",
                        "line_no": 10,
                        "utt_id": 2,
                        "speaker": "CHI",
                        "age_months": 13,
                        "utterance_clean": "play now",
                    },
                ],
            )
            unit = ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )

            contexts = load_child_utterance_contexts(unit)

        self.assertEqual([ctx.child_tokens for ctx in contexts], [("more", "milk"), ("play", "now")])
        self.assertEqual(
            [ctx.previous_caretaker_tokens for ctx in contexts],
            [("want", "some"), ("please", "go")],
        )

    def test_build_dicts_writes_additive_unigram_bigram_and_trigram_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            child_dir = tmp_dir / "data" / "ToySet" / "ToyChild"
            write_csv(
                child_dir / "caretakers.csv",
                [
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 5,
                        "utt_id": 1,
                        "speaker": "MOT",
                        "age_months": 7,
                        "utterance_clean": "want some",
                    },
                    {
                        "session_id": 2,
                        "file": "b.cha",
                        "line_no": 5,
                        "utt_id": 1,
                        "speaker": "MOT",
                        "age_months": 13,
                        "utterance_clean": "please go",
                    },
                ],
            )
            write_csv(
                child_dir / "chi.csv",
                [
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 10,
                        "utt_id": 2,
                        "speaker": "CHI",
                        "age_months": 7,
                        "utterance_clean": "more milk",
                    },
                    {
                        "session_id": 2,
                        "file": "b.cha",
                        "line_no": 10,
                        "utt_id": 2,
                        "speaker": "CHI",
                        "age_months": 13,
                        "utterance_clean": "play now",
                    },
                ],
            )
            unit = ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )
            out_dir = tmp_dir / "dicts"

            build_dicts(
                units=[unit],
                out_dir=out_dir,
                bin_months=6,
                min_age_months=6.0,
                max_age_months=18.0,
                by_child=False,
            )

            counts_006 = json.loads((out_dir / "bin_006-011" / "unigram_counts.json").read_text())
            counts_012 = json.loads((out_dir / "bin_012-017" / "unigram_counts.json").read_text())
            bigrams_012 = json.loads((out_dir / "bin_012-017" / "bigram_counts.json").read_text())
            trigrams_012 = json.loads((out_dir / "bin_012-017" / "trigram_counts.json").read_text())
            summary = (out_dir / "summary.csv").read_text()

        self.assertEqual(counts_006, {"milk": 1, "more": 1})
        self.assertEqual(counts_012, {"milk": 1, "more": 1, "now": 1, "play": 1})
        self.assertEqual(bigrams_012["some"], {"more": 1})
        self.assertEqual(bigrams_012["go"], {"play": 1})
        self.assertEqual(trigrams_012["want"]["some"], {"more": 1})
        self.assertEqual(trigrams_012["go"]["play"], {"now": 1})
        self.assertIn("True", summary)

    def test_build_dicts_uses_custom_age_bin_labels_when_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            child_dir = tmp_dir / "data" / "ToySet" / "ToyChild"
            write_csv(
                child_dir / "caretakers.csv",
                [
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 5,
                        "utt_id": 1,
                        "speaker": "MOT",
                        "age_months": 18,
                        "utterance_clean": "want some",
                    },
                    {
                        "session_id": 2,
                        "file": "b.cha",
                        "line_no": 5,
                        "utt_id": 1,
                        "speaker": "MOT",
                        "age_months": 20,
                        "utterance_clean": "please go",
                    },
                ],
            )
            write_csv(
                child_dir / "chi.csv",
                [
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 10,
                        "utt_id": 2,
                        "speaker": "CHI",
                        "age_months": 18,
                        "utterance_clean": "more milk",
                    },
                    {
                        "session_id": 2,
                        "file": "b.cha",
                        "line_no": 10,
                        "utt_id": 2,
                        "speaker": "CHI",
                        "age_months": 20,
                        "utterance_clean": "play now",
                    },
                ],
            )
            unit = ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )
            out_dir = tmp_dir / "dicts"

            build_dicts(
                units=[unit],
                out_dir=out_dir,
                age_bins=[AgeBin(6, 18), AgeBin(19, 23)],
                age_bin_strategy="threshold_early",
                age_bin_threshold=20_000,
            )

            counts_006_018 = json.loads((out_dir / "bin_006-018" / "unigram_counts.json").read_text())
            counts_019_023 = json.loads((out_dir / "bin_019-023" / "unigram_counts.json").read_text())
            config = json.loads((out_dir / "age_bins.json").read_text())
            summary = (out_dir / "summary.csv").read_text()

        self.assertEqual(counts_006_018, {"milk": 1, "more": 1})
        self.assertEqual(counts_019_023, {"milk": 1, "more": 1, "now": 1, "play": 1})
        self.assertEqual(config["bins"][0]["label"], "006-018")
        self.assertIn("threshold_early", summary)


if __name__ == "__main__":
    unittest.main()
