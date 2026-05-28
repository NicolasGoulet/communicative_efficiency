import csv
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from add_random_and_unigram_utterances import (
    BigramSampler,
    CONTEXT_LAST_TWO_COL,
    CONTEXT_P1_COL,
    CONTEXT_P2_COL,
    TrigramSampler,
    UniformSampler,
    WeightedSampler,
    caretaker_context_debug_values,
    load_bigram_probs,
    load_trigram_probs,
    load_unigram_counts,
    load_vocab,
    normalize_counts,
    enforce_generated_output_schema,
    normalize_generated_metadata,
    normalize_vocab_list,
    normalize_vocab_token,
    process,
)
from build_age_word_dicts import ChildUnit
from custom_age_bins import AgeBin, write_age_bins_config


ALLOWED_AT_TAGS = {"b", "c", "d", "f", "i", "k", "l", "ls", "n", "o", "p", "wp"}
EXPECTED_NGRAM_OUTPUT_COLUMNS = [
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
    "speaker",
    "utterance",
    "utterance_clean",
    "cleaned_is_empty",
    CONTEXT_P2_COL,
    CONTEXT_P1_COL,
    CONTEXT_LAST_TWO_COL,
    "random_model_utterance_bin6",
    "unigram_model_utterance_bin6",
    "bigram_model_utterance_bin6",
    "trigram_model_utterance_bin6",
]


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


class TestLanguageModelGeneration(unittest.TestCase):
    def test_normalize_vocab_token_keeps_current_special_form_markers(self):
        self.assertEqual(normalize_vocab_token("dog@c", ALLOWED_AT_TAGS), "dog")
        self.assertEqual(normalize_vocab_token("bunko@f", ALLOWED_AT_TAGS), "bunko")
        self.assertEqual(normalize_vocab_token("p@ls", ALLOWED_AT_TAGS), "p")
        self.assertIsNone(normalize_vocab_token("word@q", ALLOWED_AT_TAGS))
        self.assertIsNone(normalize_vocab_token("0cookie", ALLOWED_AT_TAGS))
        self.assertIsNone(normalize_vocab_token("&-uh", ALLOWED_AT_TAGS))
        self.assertIsNone(normalize_vocab_token("<dog>", ALLOWED_AT_TAGS))

    def test_normalize_vocab_list_deduplicates_after_cleaning(self):
        vocab = ["dog@c", "dog", "cat", "cat@b", "y@l", "xxx"]

        cleaned = normalize_vocab_list(vocab, ALLOWED_AT_TAGS)

        self.assertEqual(cleaned, ["dog", "cat", "y"])

    def test_normalize_counts_aggregates_matching_stems(self):
        raw_counts = {"dog@c": 2, "dog": 3, "dog@b": 4, "y@l": 1, "0milk": 9}

        cleaned_counts = normalize_counts(raw_counts, ALLOWED_AT_TAGS)

        self.assertEqual(cleaned_counts, {"dog": 9, "y": 1})

    def test_uniform_sampler_returns_requested_length(self):
        sampler = UniformSampler(["red"])

        words = sampler.sample_n(random.Random(1), 3)

        self.assertEqual(words, ["red", "red", "red"])

    def test_weighted_sampler_can_be_made_deterministic_with_one_word(self):
        sampler = WeightedSampler({"only": 10})

        words = sampler.sample_n(random.Random(1), 4)

        self.assertEqual(words, ["only", "only", "only", "only"])

    def test_bigram_sampler_uses_caretaker_context_for_first_generated_word(self):
        backoff = WeightedSampler({"fallback": 1})
        sampler = BigramSampler(
            {
                "some": {"more": 1.0},
                "more": {"milk": 1.0},
            },
            unigram_backoff=backoff,
        )

        words = sampler.sample_sequence(random.Random(1), 2, previous_caretaker_tokens=["want", "some"])

        self.assertEqual(words, ["more", "milk"])

    def test_bigram_sampler_backs_off_when_no_caretaker_context_exists(self):
        backoff = WeightedSampler({"fallback": 1})
        sampler = BigramSampler({"some": {"more": 1.0}}, unigram_backoff=backoff)

        words = sampler.sample_sequence(random.Random(1), 1, previous_caretaker_tokens=[])

        self.assertEqual(words, ["fallback"])

    def test_trigram_sampler_uses_p2_p1_then_p1_generated_first_word(self):
        unigram = WeightedSampler({"fallback": 1})
        bigram = BigramSampler({}, unigram_backoff=unigram)
        sampler = TrigramSampler(
            {
                "want": {"some": {"more": 1.0}},
                "some": {"more": {"milk": 1.0}},
            },
            bigram_backoff=bigram,
            unigram_backoff=unigram,
        )

        words = sampler.sample_sequence(random.Random(1), 2, previous_caretaker_tokens=["want", "some"])

        self.assertEqual(words, ["more", "milk"])

    def test_caretaker_context_debug_values_exposes_p2_and_p1(self):
        values = caretaker_context_debug_values(["do", "you", "want", "some"])

        self.assertEqual(values[CONTEXT_P2_COL], "want")
        self.assertEqual(values[CONTEXT_P1_COL], "some")
        self.assertEqual(values[CONTEXT_LAST_TWO_COL], "want some")

    def test_caretaker_context_debug_values_handles_short_contexts(self):
        one_word = caretaker_context_debug_values(["some"])
        no_words = caretaker_context_debug_values([])

        self.assertEqual(one_word[CONTEXT_P2_COL], "")
        self.assertEqual(one_word[CONTEXT_P1_COL], "some")
        self.assertEqual(one_word[CONTEXT_LAST_TWO_COL], "some")
        self.assertEqual(no_words[CONTEXT_LAST_TWO_COL], "")

    def test_normalize_generated_metadata_fills_blank_provenance_without_shifting_columns(self):
        unit = ChildUnit(
            dataset="ToySet",
            child="ToyChild",
            folder=Path("ToyChild"),
            chi_csv=Path("ToyChild/chi.csv"),
            caretakers_csv=Path("ToyChild/caretakers.csv"),
        )
        frame = pd.DataFrame(
            [
                {
                    "dataset": "",
                    "child_id": "",
                    "source_group": "",
                    "file": "ToyChild/a.cha",
                    "line_no": "10",
                    "speaker": "",
                    "utterance_clean": "more milk.",
                }
            ]
        )

        normalized = normalize_generated_metadata(frame, unit)

        self.assertEqual(normalized.loc[0, "dataset"], "ToySet")
        self.assertEqual(normalized.loc[0, "child_id"], "ToyChild")
        self.assertEqual(normalized.loc[0, "source_group"], "ToySet")
        self.assertEqual(normalized.loc[0, "speaker"], "CHI")
        self.assertEqual(normalized.loc[0, "file"], "ToyChild/a.cha")
        self.assertEqual(normalized.loc[0, "line_no"], "10")

    def test_enforce_generated_output_schema_removes_utt_id_role_and_blank_headers(self):
        frame = pd.DataFrame(
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
                    "utt_id": "3",
                    "utt_id_role": "99",
                    "speaker": "CHI",
                    "utterance": "more milk .",
                    "utterance_clean": "more milk.",
                    "cleaned_is_empty": "0",
                    "": "stray",
                    CONTEXT_P2_COL: "want",
                    CONTEXT_P1_COL: "some",
                    CONTEXT_LAST_TWO_COL: "want some",
                    "random_model_utterance_bin6": "milk more.",
                    "unigram_model_utterance_bin6": "more more.",
                    "bigram_model_utterance_bin6": "more milk.",
                    "trigram_model_utterance_bin6": "more milk.",
                }
            ]
        )

        output = enforce_generated_output_schema(frame, [(6, Path("dicts"))], "all")

        self.assertEqual(list(output.columns), EXPECTED_NGRAM_OUTPUT_COLUMNS)
        self.assertNotIn("utt_id_role", output.columns)
        self.assertNotIn("", output.columns)
        self.assertEqual(output.loc[0, "speaker"], "CHI")
        self.assertEqual(output.loc[0, "utterance"], "more milk .")
        self.assertEqual(output.loc[0, "utterance_clean"], "more milk.")

    def test_trigram_sampler_uses_bigram_backoff_for_missing_first_trigram_context(self):
        unigram = WeightedSampler({"fallback": 1})
        bigram = BigramSampler({"some": {"more": 1.0}}, unigram_backoff=unigram)
        sampler = TrigramSampler(
            {"some": {"more": {"milk": 1.0}}},
            bigram_backoff=bigram,
            unigram_backoff=unigram,
        )

        words = sampler.sample_sequence(random.Random(1), 2, previous_caretaker_tokens=["some"])

        self.assertEqual(words, ["more", "milk"])

    def test_load_model_files_from_tiny_dictionary_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin_006-011"
            bin_dir.mkdir()

            (bin_dir / "vocab.txt").write_text("apple@c\napple\ny@l\n&-uh\n", encoding="utf-8")
            (bin_dir / "unigram_counts.json").write_text(
                json.dumps({"apple@c": 2, "apple": 1, "y@l": 1}),
                encoding="utf-8",
            )
            (bin_dir / "bigram_probs.json").write_text(
                json.dumps({"red": {"apple": 1.0}}),
                encoding="utf-8",
            )
            (bin_dir / "trigram_probs.json").write_text(
                json.dumps({"big": {"red": {"apple": 1.0}}}),
                encoding="utf-8",
            )

            vocab = load_vocab(root, "006-011", ALLOWED_AT_TAGS, True, True)
            unigram_counts = load_unigram_counts(root, "006-011", ALLOWED_AT_TAGS, True, True)
            bigram_probs = load_bigram_probs(root, "006-011")
            trigram_probs = load_trigram_probs(root, "006-011")

        self.assertEqual(vocab, ["apple", "y"])
        self.assertEqual(unigram_counts, {"apple": 3, "y": 1})
        self.assertEqual(bigram_probs, {"red": {"apple": 1.0}})
        self.assertEqual(trigram_probs, {"big": {"red": {"apple": 1.0}}})

    def test_process_writes_context_columns_and_generated_columns_without_misalignment(self):
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
                    }
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
                        "utterance_clean": 'more, "milk".',
                    },
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 12,
                        "utt_id": 3,
                        "speaker": "CHI",
                        "age_months": 7,
                        "utterance_clean": "!!!",
                    }
                ],
            )

            dict_root = tmp_dir / "dicts"
            bin_dir = dict_root / "bin_006-011"
            bin_dir.mkdir(parents=True)
            (bin_dir / "vocab.txt").write_text("more\nmilk\n", encoding="utf-8")
            (bin_dir / "unigram_counts.json").write_text(
                json.dumps({"more": 1, "milk": 1}),
                encoding="utf-8",
            )
            (bin_dir / "bigram_probs.json").write_text(
                json.dumps({"some": {"more": 1.0}, "more": {"milk": 1.0}}),
                encoding="utf-8",
            )
            (bin_dir / "trigram_probs.json").write_text(
                json.dumps({"want": {"some": {"more": 1.0}}, "some": {"more": {"milk": 1.0}}}),
                encoding="utf-8",
            )
            unit = ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )

            process(
                units=[unit],
                model_specs=[(6, dict_root)],
                which="all",
                out_mode="sibling",
                seed=1,
                min_age_months=6.0,
            )

            with (child_dir / "chi.ngram_generated.csv").open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                parsed_rows = list(reader)
            with (child_dir / "chi.ngram_generated.csv").open(newline="", encoding="utf-8") as handle:
                output_rows = list(csv.DictReader(handle))

        header_width = len(parsed_rows[0])
        self.assertEqual(parsed_rows[0], EXPECTED_NGRAM_OUTPUT_COLUMNS)
        self.assertTrue(all(len(row) == header_width for row in parsed_rows))
        self.assertNotIn("utt_id_role", parsed_rows[0])
        self.assertFalse(any(header == "" for header in parsed_rows[0]))
        self.assertEqual(len(output_rows), 2)
        self.assertEqual(output_rows[0]["dataset"], "ToySet")
        self.assertEqual(output_rows[0]["child_id"], "ToyChild")
        self.assertEqual(output_rows[0]["source_group"], "ToySet")
        self.assertEqual(output_rows[0]["line_no"], "10")
        self.assertEqual(output_rows[0]["speaker"], "CHI")
        self.assertEqual(output_rows[0]["utterance_clean"], 'more, "milk".')
        self.assertEqual(output_rows[0][CONTEXT_P2_COL], "want")
        self.assertEqual(output_rows[0][CONTEXT_P1_COL], "some")
        self.assertEqual(output_rows[0][CONTEXT_LAST_TWO_COL], "want some")
        self.assertEqual(output_rows[0]["bigram_model_utterance_bin6"], "more milk.")
        self.assertEqual(output_rows[0]["trigram_model_utterance_bin6"], "more milk.")
        self.assertEqual(output_rows[1][CONTEXT_LAST_TWO_COL], "")
        self.assertEqual(output_rows[1]["trigram_model_utterance_bin6"], "")

    def test_process_uses_custom_age_bins_when_dictionary_root_has_config(self):
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
                    }
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
                        "utterance_clean": "more milk.",
                    }
                ],
            )
            dict_root = tmp_dir / "dicts"
            write_age_bins_config(
                dict_root / "age_bins.json",
                bins=[AgeBin(6, 18), AgeBin(19, 23)],
                strategy="threshold_early",
                threshold=20_000,
            )
            bin_dir = dict_root / "bin_006-018"
            bin_dir.mkdir(parents=True)
            (bin_dir / "vocab.txt").write_text("custom\nword\n", encoding="utf-8")
            (bin_dir / "unigram_counts.json").write_text(json.dumps({"custom": 1, "word": 1}), encoding="utf-8")
            (bin_dir / "bigram_probs.json").write_text(json.dumps({"some": {"custom": 1.0}}), encoding="utf-8")
            (bin_dir / "trigram_probs.json").write_text(
                json.dumps({"want": {"some": {"custom": 1.0}}, "some": {"custom": {"word": 1.0}}}),
                encoding="utf-8",
            )
            unit = ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )

            process(
                units=[unit],
                model_specs=[(6, dict_root)],
                which="all",
                out_mode="sibling",
                seed=1,
                min_age_months=0.0,
            )

            with (child_dir / "chi.ngram_generated.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(rows[0]["bigram_model_utterance_bin6"], "custom word.")
        self.assertEqual(rows[0]["trigram_model_utterance_bin6"], "custom word.")


if __name__ == "__main__":
    unittest.main()
