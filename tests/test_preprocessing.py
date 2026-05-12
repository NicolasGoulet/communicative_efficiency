import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from prepare_datasets import (
    build_cleaned_export_rows,
    clean_and_count_words,
    clean_chat_for_counts,
    collect_child,
    count_morphemes_from_mor,
    count_utt_syllables,
    syllables_basic,
    syllables_le,
    syllables_lenient,
    syllables_strict_y,
    write_cleaned_utterance_exports,
)


class TestUtterancePreprocessing(unittest.TestCase):
    def test_clean_chat_removes_common_childes_markup(self):
        raw = "<I want> cookies [=! laughs] (quietly) &-uh dog@c y@l 0milk xxx +..."

        cleaned = clean_chat_for_counts(raw)

        self.assertEqual(cleaned, "I want cookies uh dog.")

    def test_clean_and_count_words_counts_cleaned_words(self):
        raw = "dog@c y@l I can't ."

        cleaned, word_count, n_alpha_words = clean_and_count_words(raw)

        self.assertEqual(cleaned, "dog I can't.")
        self.assertEqual(word_count, 3)
        self.assertEqual(n_alpha_words, 3)

    def test_clean_chat_preserves_terminal_period_from_retracing_marker(self):
        cleaned = clean_chat_for_counts("two +//. 2965221_2967008")

        self.assertEqual(cleaned, "two.")

    def test_clean_chat_preserves_terminal_question_and_exclamation_marks(self):
        self.assertEqual(clean_chat_for_counts("now ?"), "now?")
        self.assertEqual(clean_chat_for_counts("wow !"), "wow!")

    def test_clean_chat_does_not_keep_punctuation_without_words(self):
        self.assertEqual(clean_chat_for_counts("0 ."), "")
        self.assertEqual(clean_chat_for_counts("xxx ?"), "")
        self.assertEqual(clean_chat_for_counts("&~um +..."), "")

    def test_clean_chat_preserves_hall_uh_filler(self):
        # Hall/WhitePro/zoe.cha:537
        raw = "I wonder , &-uh , sit Kate ."

        cleaned, word_count, n_alpha_words = clean_and_count_words(raw)

        self.assertEqual(cleaned, "I wonder uh sit Kate.")
        self.assertEqual(word_count, 5)
        self.assertEqual(n_alpha_words, 5)

    def test_clean_chat_preserves_hall_er_filler_variant(self):
        # Hall/WhitePro/zoe.cha:276
        raw = "&-er:r (.) now I'll try to shoot it ."

        cleaned, word_count, n_alpha_words = clean_and_count_words(raw)

        self.assertEqual(cleaned, "er now I'll try to shoot it.")
        self.assertEqual(word_count, 7)
        self.assertEqual(n_alpha_words, 7)

    def test_syllable_strategies_on_short_reference_words(self):
        self.assertEqual(syllables_basic("cat"), 1)
        self.assertEqual(syllables_lenient("cat"), 1)
        self.assertEqual(syllables_strict_y("cat"), 1)
        self.assertEqual(syllables_le("cat"), 1)

    def test_syllable_strategies_show_their_different_rules(self):
        self.assertEqual(syllables_basic("cake"), 1)
        self.assertEqual(syllables_lenient("cake"), 2)
        self.assertEqual(syllables_strict_y("cake"), 1)
        self.assertEqual(syllables_le("cake"), 1)

        self.assertEqual(syllables_basic("table"), 1)
        self.assertEqual(syllables_lenient("table"), 2)
        self.assertEqual(syllables_strict_y("table"), 1)
        self.assertEqual(syllables_le("table"), 2)

    def test_syllable_strategies_cover_y_ed_and_es_examples(self):
        self.assertEqual(syllables_basic("baby"), 2)
        self.assertEqual(syllables_strict_y("baby"), 2)
        self.assertEqual(syllables_le("wanted"), 3)
        self.assertEqual(syllables_le("wishes"), 2)

    def test_count_utterance_syllables_adds_word_level_counts(self):
        counts = count_utt_syllables("baby wanted table.")

        self.assertEqual(
            counts,
            {
                "utt_syllables_basic": 5,
                "utt_syllables_lenient": 6,
                "utt_syllables_strictY": 5,
                "utt_syllables_le": 7,
                "n_alpha_words": 3,
            },
        )

    def test_count_morphemes_counts_plain_roots(self):
        mor_line = "%mor:\tpro|I v|want n|cookie ."

        self.assertEqual(count_morphemes_from_mor(mor_line), 3)

    def test_count_morphemes_adds_selected_affix_codes(self):
        mor_line = "%mor:\tn|dog-PL n|child-POSS v|walk-PAST ."

        self.assertEqual(count_morphemes_from_mor(mor_line), 6)

    def test_count_morphemes_handles_tilde_linked_subtokens(self):
        mor_line = "%mor:\tv|paint-PAST~n|brush-PL ."

        self.assertEqual(count_morphemes_from_mor(mor_line), 4)

    def test_count_morphemes_handles_empty_or_non_mor_lines(self):
        self.assertEqual(count_morphemes_from_mor("%mor:\t."), 0)
        self.assertIsNone(count_morphemes_from_mor("not a mor line"))

    def test_complex_hall_example_cleaning_and_morpheme_count(self):
        raw_utterance = (
            "&~u:h no because when I finish all the school recording I'll take it "
            "off an(d) then &-uh just before she comes home ."
        )
        mor_line = (
            "%mor:\tintj|no sconj|because adv|when pron|I-Prs-Nom-S1 "
            "verb|finish-Fin-Ind-Pres-S1 det|all-Def det|the-Def-Art "
            "noun|school noun|recording pron|I-Prs-Nom-S1~aux|will-Fin-S "
            "verb|take-Inf-S pron|it-Prs-Acc-S3 adp|off cconj|and adv|then "
            "adv|just sconj|before pron|she-Prs-Nom-S3 "
            "verb|come-Fin-Ind-Pres-S3 adv|home ."
        )

        cleaned, word_count, n_alpha_words = clean_and_count_words(raw_utterance)
        morpheme_count = count_morphemes_from_mor(mor_line)

        self.assertEqual(
            cleaned,
            "no because when I finish all the school recording I'll take it off "
            "an then uh just before she comes home.",
        )
        self.assertEqual(word_count, 21)
        self.assertEqual(n_alpha_words, 21)
        self.assertEqual(morpheme_count, 21)

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
                        "*CHI:\t0 .",
                        "%mor:\t0 .",
                        "*CHI:\t<I want> milk@c y@l [=! whines] .",
                        "%mor:\tpro|I v|want n|milk .",
                        "*MOT:\t&-uh look@c at dog .",
                        "%mor:\tv|look prep|at n|dog .",
                        "*FAT:\t0cookie okay !",
                        "*FAT:\txxx ?",
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
        self.assertEqual(len(payload["utts"]["CHI"]), 1)
        self.assertEqual(len(payload["utts"]["FAT"]), 1)

        chi_row = payload["utts"]["CHI"][0]
        self.assertEqual(chi_row["utterance"], "<I want> milk@c y@l [=! whines] .")
        self.assertEqual(chi_row["utterance_clean"], "I want milk.")
        self.assertEqual(chi_row["word_count"], 3)
        self.assertEqual(chi_row["morph_count"], 3)

        mot_row = payload["utts"]["MOT"][0]
        self.assertEqual(mot_row["utterance"], "&-uh look@c at dog .")
        self.assertEqual(mot_row["utterance_clean"], "uh look at dog.")

        fat_row = payload["utts"]["FAT"][0]
        self.assertEqual(fat_row["utterance_clean"], "okay!")

    def test_cleaned_export_rows_keep_counts_and_provenance(self):
        payload = {
            "sex": "female",
            "source_group": "ToyGroup",
            "sessions": [{"id": 1, "age": "2;03.15", "age_m": 27.5, "path": "Toy/session1.cha"}],
            "utts": {
                "CHI": [
                    {
                        "utt_id": 1,
                        "child_id": "ToyChild",
                        "session_id": 1,
                        "utterance": "&-uh look .",
                        "utterance_clean": "uh look.",
                        "word_count": 2,
                        "morph_count": 2,
                        "utt_syllables_basic": 2,
                        "utt_syllables_lenient": 2,
                        "utt_syllables_strictY": 2,
                        "utt_syllables_le": 2,
                        "n_alpha_words": 2,
                        "source_group": "ToyGroup",
                        "file": "Toy/session1.cha",
                        "line_no": 10,
                    }
                ],
                "MOT": [],
                "FAT": [],
            },
        }

        rows = build_cleaned_export_rows("ToyDataset", {"ToyChild": payload})
        exported = rows["chi"][0]

        self.assertEqual(exported["dataset"], "ToyDataset")
        self.assertEqual(exported["speaker"], "CHI")
        self.assertEqual(exported["child_id"], "ToyChild")
        self.assertEqual(exported["age_raw"], "2;03.15")
        self.assertEqual(exported["age_months"], 27.5)
        self.assertEqual(exported["utterance_clean"], "uh look.")
        self.assertEqual(exported["word_count"], 2)
        self.assertEqual(exported["file"], "Toy/session1.cha")
        self.assertEqual(exported["line_no"], 10)

    def test_write_cleaned_utterance_exports_creates_role_csvs(self):
        payload = {
            "sex": "female",
            "source_group": "",
            "sessions": [{"id": 1, "age": "2;03.15", "age_m": 27.5, "path": "Toy/session1.cha"}],
            "utts": {
                "CHI": [],
                "MOT": [
                    {
                        "utt_id": 1,
                        "child_id": "ToyChild",
                        "session_id": 1,
                        "utterance": "&-um hi .",
                        "utterance_clean": "um hi.",
                        "word_count": 2,
                        "morph_count": 2,
                        "utt_syllables_basic": 2,
                        "utt_syllables_lenient": 2,
                        "utt_syllables_strictY": 2,
                        "utt_syllables_le": 2,
                        "n_alpha_words": 2,
                        "source_group": "",
                        "file": "Toy/session1.cha",
                        "line_no": 20,
                    }
                ],
                "FAT": [],
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            write_cleaned_utterance_exports("ToyDataset", output_root, {"ToyChild": payload})

            dataset_dir = output_root / "ToyDataset"
            self.assertTrue((dataset_dir / "chi.csv").exists())
            self.assertTrue((dataset_dir / "mot.csv").exists())
            self.assertTrue((dataset_dir / "fat.csv").exists())
            self.assertTrue((dataset_dir / "caretakers.csv").exists())

            with (dataset_dir / "caretakers.csv").open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["speaker"], "MOT")
        self.assertEqual(rows[0]["utt_id_role"], "1")
        self.assertEqual(rows[0]["utterance_clean"], "um hi.")


if __name__ == "__main__":
    unittest.main()
