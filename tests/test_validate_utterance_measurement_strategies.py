import csv
import tempfile
import unittest
from pathlib import Path

import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from validate_utterance_measurement_strategies import (
    REVIEW_COLUMNS,
    count_cmudict_or_syllables_pkg_utterance,
    count_cmudict_g2p_utterance,
    count_cmu_utterance,
    count_mor_tier,
    read_raw_record,
    review_row_dict,
    row_counts,
    token_row_dicts,
)


class TestValidateUtteranceMeasurementStrategies(unittest.TestCase):
    def test_cmudict_counts_syllables_and_phonemes_from_arpabet(self):
        counts = count_cmu_utterance(["play", "checkers"])

        self.assertEqual(counts.cmu_all_words_in_dict, 1)
        self.assertEqual(counts.cmu_oov_count, 0)
        self.assertEqual(counts.cmu_syllable_count, 3)
        self.assertGreaterEqual(counts.cmu_phoneme_count, 7)

    def test_cmudict_flags_oov_words_without_imputing_counts(self):
        counts = count_cmu_utterance(["zzchildword"])

        self.assertEqual(counts.cmu_all_words_in_dict, 0)
        self.assertEqual(counts.cmu_oov_words, "zzchildword")
        self.assertIsNone(counts.cmu_syllable_count)
        self.assertIsNone(counts.cmu_phoneme_count)

    def test_hybrid_g2p_counts_oov_words_as_written(self):
        counts = count_cmudict_g2p_utterance(["oink", "walking"])

        self.assertEqual(counts.hybrid_g2p_fallback_word_count, 1)
        self.assertEqual(counts.hybrid_g2p_fallback_words, "oink")
        self.assertGreaterEqual(counts.hybrid_syllable_count, 2)
        self.assertGreaterEqual(counts.hybrid_phoneme_count, 7)

    def test_syllable_hybrid_uses_syllables_package_for_oov_words(self):
        counts = count_cmudict_or_syllables_pkg_utterance(["firetruck", "boing", "dabadoo"])

        self.assertEqual(counts.fallback_word_count, 3)
        self.assertEqual(counts.syllable_count, 7)
        self.assertEqual(counts.fallback_words, "firetruck;boing;dabadoo")

    def test_syllable_hybrid_falls_back_when_cmudict_has_no_vowel_nucleus(self):
        counts = count_cmudict_or_syllables_pkg_utterance(["hm", "shh"])

        self.assertEqual(counts.syllable_count, 2)
        self.assertEqual(counts.fallback_word_count, 2)
        self.assertEqual(counts.fallback_words, "hm;shh")

    def test_phoneme_hybrid_falls_back_for_unicode_non_g2p_symbol(self):
        counts = count_cmudict_g2p_utterance(["ð"])

        self.assertEqual(counts.hybrid_phoneme_count, 1)
        self.assertEqual(counts.hybrid_syllable_count, 1)
        self.assertEqual(counts.hybrid_g2p_fallback_word_count, 1)

    def test_mor_tier_counts_components_and_overt_bound_morpheme_proxy(self):
        mor = "pron|that-Dem~aux|be-Fin-Ind-Pres-S3 det|a-Ind-Art verb|look-Ger-S noun|eye-Plur ."

        counts = count_mor_tier(mor)

        self.assertEqual(counts.mor_tier_found, 1)
        self.assertEqual(counts.mor_component_count, 5)
        self.assertEqual(counts.mor_mlu_proxy_count, 7)
        self.assertEqual(counts.mor_bound_morpheme_tags, "Ger;Plur")

    def test_read_raw_record_uses_line_number_and_following_mor_tier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cha = root / "Toy" / "Child" / "a.cha"
            cha.parent.mkdir(parents=True)
            cha.write_text(
                "@Begin\n"
                "*CHI:\tplay checkers . \x151_2\x15\n"
                "%xpho:\tpe\n"
                "%mor:\tverb|play-Fin-Imp-S noun|checker-Plur-Acc .\n"
                "*MOT:\tyes .\n",
                encoding="utf-8",
            )

            main, mor = read_raw_record(root, "Toy", "Child/a.cha", "2")

        self.assertEqual(main, "*CHI: play checkers .")
        self.assertEqual(mor, "verb|play-Fin-Imp-S noun|checker-Plur-Acc .")

    def test_row_counts_prefers_mor_for_recommended_morphemes_and_flags_oov(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cha = root / "Toy" / "Child" / "a.cha"
            cha.parent.mkdir(parents=True)
            cha.write_text(
                "@Begin\n"
                "*CHI:\tzzchildword walking .\n"
                "%mor:\tnoun|zzchildword verb|walk-Ger-S .\n",
                encoding="utf-8",
            )
            row = {
                "dataset": "Toy",
                "child_id": "Child",
                "session_id": "1",
                "age_months": "24",
                "file": "Child/a.cha",
                "line_no": "2",
                "utt_id": "1",
                "chi_utterance_clean": "zzchildword walking.",
            }

            counted = row_counts(row, raw_root=root)

        self.assertEqual(counted.recommended_word_count, 2)
        self.assertEqual(counted.recommended_morpheme_count, 3)
        self.assertIsNotNone(counted.recommended_syllable_count)
        self.assertIsNotNone(counted.recommended_phoneme_count)
        self.assertGreater(counted.recommended_syllable_count, 0)
        self.assertGreater(counted.recommended_phoneme_count, 0)
        self.assertIn("cmu_oov", counted.quality_flags)
        self.assertIn("g2p_fallback_used", counted.quality_flags)

    def test_review_rows_put_utterance_and_manual_count_columns_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cha = root / "Toy" / "Child" / "a.cha"
            cha.parent.mkdir(parents=True)
            cha.write_text(
                "@Begin\n"
                "*CHI:\toink walking .\n"
                "%mor:\tchi|oink verb|walk-Ger-S .\n",
                encoding="utf-8",
            )
            row = {
                "dataset": "Toy",
                "child_id": "Child",
                "session_id": "1",
                "age_months": "24",
                "file": "Child/a.cha",
                "line_no": "2",
                "utt_id": "1",
                "chi_utterance_clean": "oink walking.",
            }

            counted = row_counts(row, raw_root=root)
            review = review_row_dict(counted, review_id=1)
            token_rows = token_row_dicts(counted, review_id=1)

        self.assertEqual(REVIEW_COLUMNS[3:7], ["utterance_clean", "indexed_tokens", "auto_words", "manual_words"])
        self.assertEqual(review["utterance_clean"], "oink walking.")
        self.assertEqual(review["auto_words"], 2)
        self.assertEqual(review["manual_words"], "")
        self.assertIn("auto_syllables_cmu_or_pkg", review)
        self.assertIn("auto_syllables_g2p_vowels", review)
        self.assertIn("auto_syllables_pkg", review)
        self.assertEqual(review["manual_syllables"], "")
        self.assertIn("1:oink", review["indexed_tokens"])
        self.assertEqual(len(token_rows), 2)
        self.assertEqual(token_rows[0]["token"], "oink")
        self.assertEqual(token_rows[0]["is_g2p_fallback"], 1)
        self.assertEqual(token_rows[0]["is_syllable_pkg_fallback"], 1)
        self.assertGreater(token_rows[0]["phonemes_cmu_or_g2p"], 0)


if __name__ == "__main__":
    unittest.main()
