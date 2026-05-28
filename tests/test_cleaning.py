import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "cleaning"

from cleaning import (  # noqa: E402
    CLEANED_CHAT_COLUMNS,
    clean_chat_utterance,
    iter_cleaned_chat_rows,
    write_cleaned_chat_csv,
)


class TestFocusedChatCleaning(unittest.TestCase):
    # Use case: clean one raw CHAT utterance in isolation before testing files.
    def test_clean_chat_utterance_removes_common_childes_markup(self):
        raw = "<I want> cookies [=! laughs] (quietly) &-uh dog@c y@l 0milk xxx +..."

        cleaned = clean_chat_utterance(raw)

        self.assertEqual(cleaned, "I want cookies uh dog y.")

    # Use case: @l marks letter names in CHAT, which are valid discourse in
    # games and spelling talk, so keep the letter itself.
    def test_clean_chat_utterance_keeps_letter_marker(self):
        self.assertEqual(clean_chat_utterance("zero or a o@l ."), "zero or a o.")
        self.assertEqual(clean_chat_utterance("zero or a x@l ?"), "zero or a x?")

    # Use case: CHAT special form markers can mark word-like material that
    # should remain available for scoring after the transcription marker is
    # stripped.
    def test_clean_chat_utterance_keeps_requested_special_form_markers(self):
        raw = (
            "bunko@f gumma@c younz@d abame@b uhhuh@i b@l p@ls "
            "abcd@k breaked@n dumpf@n$v aga@p woofwoof@o goobarumba@wp ."
        )

        cleaned = clean_chat_utterance(raw)

        self.assertEqual(
            cleaned,
            "bunko gumma younz abame uhhuh b p abcd breaked dumpf aga woofwoof goobarumba.",
        )

    # Use case: preserve real sentence-final punctuation but do not emit
    # punctuation-only cleaned utterances.
    def test_clean_chat_utterance_keeps_terminal_punctuation_with_timing_suffix(self):
        self.assertEqual(clean_chat_utterance("two +//. 2965221_2967008"), "two.")
        self.assertEqual(clean_chat_utterance("now ?"), "now?")
        self.assertEqual(clean_chat_utterance("0 ."), "")

    # Use case: parse a small CHAT file, keep raw and cleaned text side by side,
    # join simple continuation lines, ignore dependent tiers, ignore speakers
    # outside the requested family, and make empty-cleaned rows explicit.
    def test_iter_cleaned_chat_rows_keeps_raw_and_cleaned_main_tiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            child_dir = base_dir / "Toy"
            child_dir.mkdir()
            cha_path = child_dir / "session1.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@Begin",
                        "*CHI:\t<I want>",
                        "\tmilk@c y@l [=! whines] .",
                        "%mor:\tpro|I v|want n|milk .",
                        "*MOT:\t0 .",
                        "*INV:\tthis speaker is ignored .",
                        "*FAT:\t&-um okay !",
                        "@End",
                    ]
                ),
                encoding="utf-8",
            )

            rows = list(iter_cleaned_chat_rows(cha_path, base_dir=base_dir))

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["file"], "Toy/session1.cha")
        self.assertEqual(rows[0]["line_no"], 2)
        self.assertEqual(rows[0]["speaker"], "CHI")
        self.assertEqual(rows[0]["utterance"], "<I want> milk@c y@l [=! whines] .")
        self.assertEqual(rows[0]["utterance_clean"], "I want milk y.")
        self.assertEqual(rows[0]["cleaned_is_empty"], 0)

        self.assertEqual(rows[1]["speaker"], "MOT")
        self.assertEqual(rows[1]["utterance"], "0 .")
        self.assertEqual(rows[1]["utterance_clean"], "")
        self.assertEqual(rows[1]["cleaned_is_empty"], 1)

        self.assertEqual(rows[2]["speaker"], "FAT")
        self.assertEqual(rows[2]["utterance_clean"], "um okay!")

    # Use case: let future runs focus on one speaker class without changing the
    # core parser.
    def test_iter_cleaned_chat_rows_can_filter_speakers(self):
        with tempfile.TemporaryDirectory() as tmp:
            cha_path = Path(tmp) / "toy.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "*CHI:\tchild words .",
                        "*MOT:\tmother words .",
                        "*FAT:\tfather words .",
                    ]
                ),
                encoding="utf-8",
            )

            rows = list(iter_cleaned_chat_rows(cha_path, speakers=("CHI",)))

        self.assertEqual([row["speaker"] for row in rows], ["CHI"])
        self.assertEqual(rows[0]["utterance_clean"], "child words.")

    # Use case: write a stable minimal CSV schema for downstream preprocessing
    # steps and manual inspection.
    def test_write_cleaned_chat_csv_uses_minimal_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            cha_path = base_dir / "toy.cha"
            out_path = base_dir / "toy.csv"
            cha_path.write_text(
                "\n".join(
                    [
                        "*CHI:\t<I want> milk .",
                        "*MOT:\txxx ?",
                    ]
                ),
                encoding="utf-8",
            )

            written = write_cleaned_chat_csv(cha_path, out_path, base_dir=base_dir)

            with out_path.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
                headers = reader.fieldnames

        self.assertEqual(written, 2)
        self.assertEqual(headers, CLEANED_CHAT_COLUMNS)
        self.assertEqual(rows[0]["utterance"], "<I want> milk .")
        self.assertEqual(rows[0]["utterance_clean"], "I want milk.")
        self.assertEqual(rows[1]["utterance_clean"], "")
        self.assertEqual(rows[1]["cleaned_is_empty"], "1")

    # Use case: validate a realistic Brown CHAT excerpt supplied during
    # development, including headers, dependent tiers, ignored investigator
    # speakers, pauses, retracing markers, unintelligible material, fillers, and
    # letter-coded @ forms.
    def test_brown_tic_tac_toe_fixture_contents(self):
        cha_path = FIXTURE_DIR / "brown_tic_tac_toe_sample.cha"

        rows = list(iter_cleaned_chat_rows(cha_path, base_dir=FIXTURE_DIR))

        self.assertEqual(
            [(row["line_no"], row["speaker"], row["utterance"], row["utterance_clean"]) for row in rows],
            [
                (14, "CHI", "hi .", "hi."),
                (19, "CHI", "okay (.) play tic-tac-toe with me .", "okay play tic-tac-toe with me."),
                (23, "CHI", "how you make it now ?", "how you make it now?"),
                (27, "MOT", "two down (.) and two across .", "two down and two across."),
                (30, "CHI", "two down ?", "two down?"),
                (33, "MOT", "make a space (.) yeah (.) this way .", "make a space yeah this way."),
                (36, "CHI", "think every [/] every (.) xxx .", "think every every."),
                (42, "CHI", "first you .", "first you."),
                (45, "CHI", "you want zero or (.) &-um .", "you want zero or um."),
                (48, "CHI", "(.) what ?", "what?"),
                (51, "CHI", "you know how to play it ?", "you know how to play it?"),
                (57, "CHI", "zero or a o@l .", "zero or a o."),
                (60, "MOT", "zero or an o@l ?", "zero or an o?"),
                (63, "CHI", "yeah .", "yeah."),
                (66, "MOT", "no (.) zero or an x@l .", "no zero or an x."),
                (69, "CHI", "zero or a x@l ?", "zero or a x?"),
                (72, "MOT", "mhm .", "mhm."),
                (75, "CHI", "y(ou) want zero or a x@l ?", "y want zero or a x?"),
            ],
        )
        self.assertNotIn("GAI", {row["speaker"] for row in rows})


if __name__ == "__main__":
    unittest.main()
