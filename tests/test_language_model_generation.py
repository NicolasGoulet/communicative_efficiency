import json
import random
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from add_random_and_unigram_utterances import (
    PAD_TOKEN,
    BigramSampler,
    UniformSampler,
    WeightedSampler,
    load_bigram_probs,
    load_unigram_counts,
    load_vocab,
    normalize_counts,
    normalize_vocab_list,
    normalize_vocab_token,
)


ALLOWED_AT_TAGS = {"b", "c", "o"}


class TestLanguageModelGeneration(unittest.TestCase):
    def test_normalize_vocab_token_keeps_only_simple_lexical_tokens(self):
        self.assertEqual(normalize_vocab_token("dog@c", ALLOWED_AT_TAGS), "dog")
        self.assertIsNone(normalize_vocab_token("y@l", ALLOWED_AT_TAGS))
        self.assertIsNone(normalize_vocab_token("0cookie", ALLOWED_AT_TAGS))
        self.assertIsNone(normalize_vocab_token("&-uh", ALLOWED_AT_TAGS))
        self.assertIsNone(normalize_vocab_token("<dog>", ALLOWED_AT_TAGS))

    def test_normalize_vocab_list_deduplicates_after_cleaning(self):
        vocab = ["dog@c", "dog", "cat", "cat@b", "y@l", "xxx"]

        cleaned = normalize_vocab_list(vocab, ALLOWED_AT_TAGS)

        self.assertEqual(cleaned, ["dog", "cat"])

    def test_normalize_counts_aggregates_matching_stems(self):
        raw_counts = {"dog@c": 2, "dog": 3, "dog@b": 4, "y@l": 100, "0milk": 9}

        cleaned_counts = normalize_counts(raw_counts, ALLOWED_AT_TAGS)

        self.assertEqual(cleaned_counts, {"dog": 9})

    def test_uniform_sampler_returns_requested_length(self):
        sampler = UniformSampler(["red"])

        words = sampler.sample_n(random.Random(1), 3)

        self.assertEqual(words, ["red", "red", "red"])

    def test_weighted_sampler_can_be_made_deterministic_with_one_word(self):
        sampler = WeightedSampler({"only": 10})

        words = sampler.sample_n(random.Random(1), 4)

        self.assertEqual(words, ["only", "only", "only", "only"])

    def test_bigram_sampler_uses_context_then_backs_off_to_unigram(self):
        backoff = WeightedSampler({"fallback": 1})
        bigrams = {
            PAD_TOKEN: {"hello": 1.0},
            "hello": {"world": 1.0},
        }
        sampler = BigramSampler(bigrams, unigram_backoff=backoff)

        words = sampler.sample_sequence(random.Random(1), 3)

        self.assertEqual(words, ["hello", "world", "fallback"])

    def test_load_model_files_from_tiny_dictionary_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin_006-011"
            bin_dir.mkdir()

            (bin_dir / "vocab.txt").write_text("apple@c\napple\ny@l\n&-uh\n", encoding="utf-8")
            (bin_dir / "unigram_counts.json").write_text(
                json.dumps({"apple@c": 2, "apple": 1, "y@l": 99}),
                encoding="utf-8",
            )
            (bin_dir / "bigram_probs.json").write_text(
                json.dumps({PAD_TOKEN: {"apple": 1.0}}),
                encoding="utf-8",
            )

            vocab = load_vocab(root, "006-011", ALLOWED_AT_TAGS, True, True)
            unigram_counts = load_unigram_counts(root, "006-011", ALLOWED_AT_TAGS, True, True)
            bigram_probs = load_bigram_probs(root, "006-011")

        self.assertEqual(vocab, ["apple"])
        self.assertEqual(unigram_counts, {"apple": 3})
        self.assertEqual(bigram_probs, {PAD_TOKEN: {"apple": 1.0}})


if __name__ == "__main__":
    unittest.main()
