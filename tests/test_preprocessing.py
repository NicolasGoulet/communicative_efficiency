import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from prepare_datasets import clean_and_count_words, clean_chat_for_counts, collect_child


class TestUtterancePreprocessing(unittest.TestCase):
    def test_clean_chat_removes_common_childes_markup(self):
        raw = "<I want> cookies [=! laughs] (quietly) &-uh dog@c y@l 0milk xxx +..."

        cleaned = clean_chat_for_counts(raw)

        self.assertEqual(cleaned, "I want cookies dog")

    def test_clean_and_count_words_counts_cleaned_words(self):
        raw = "dog@c y@l I can't ."

        cleaned, word_count, n_alpha_words = clean_and_count_words(raw)

        self.assertEqual(cleaned, "dog I can't")
        self.assertEqual(word_count, 3)
        self.assertEqual(n_alpha_words, 3)

    def test_collect_child_reads_a_tiny_chat_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            child_dir = base_dir / "ToyChild"
            child_dir.mkdir()
            cha_path = child_dir / "session1.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@Begin",
                        "@ID:\teng|Toy|CHI|2;03.15|female|||",
                        "*CHI:\t<I want> milk@c y@l [=! whines] .",
                        "%mor:\tpro|I v|want n|milk .",
                        "*MOT:\t&-uh look@c at dog .",
                        "%mor:\tv|look prep|at n|dog .",
                        "*FAT:\t0cookie okay .",
                        "@End",
                    ]
                ),
                encoding="utf-8",
            )

            payload, missing_ages = collect_child(
                base_dir=base_dir,
                child_dir=child_dir,
                emit_session_counts=True,
            )

        self.assertEqual(missing_ages, [])
        self.assertEqual(payload["sessions"][0]["age_m"], 27.5)

        chi_row = payload["utts"]["CHI"][0]
        self.assertEqual(chi_row["utterance_clean"], "I want milk")
        self.assertEqual(chi_row["word_count"], 3)
        self.assertEqual(chi_row["morph_count"], 3)

        mot_row = payload["utts"]["MOT"][0]
        self.assertEqual(mot_row["utterance_clean"], "look at dog")

        fat_row = payload["utts"]["FAT"][0]
        self.assertEqual(fat_row["utterance_clean"], "okay")


if __name__ == "__main__":
    unittest.main()
