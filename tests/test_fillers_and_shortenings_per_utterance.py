import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from fillers_and_shortenings_per_utterance import (  # noqa: E402
    analyze_units,
    extract_fillers,
    extract_shortenings,
    write_outputs,
)
from prepare_datasets import ChatUnit  # noqa: E402


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestFillersAndShorteningsPerUtterance(unittest.TestCase):
    def test_extract_fillers_normalizes_common_chat_variants(self):
        fillers = extract_fillers("&-uh &-er:r hmmmm uhuh uhhuh@i mhm &=laughs .")

        self.assertEqual(
            [(filler.raw_token, filler.filler_type, filler.normalized) for filler in fillers],
            [
                ("&-uh", "uh", "uh"),
                ("&-er:r", "er", "err"),
                ("hmmmm", "hmm", "hmmmm"),
                ("uhuh", "uhuh", "uhuh"),
                ("uhhuh@i", "uhuh", "uhhuh"),
                ("mhm", "mhm", "mhm"),
            ],
        )

    def test_extract_shortenings_keeps_only_letter_parentheses(self):
        shortenings = extract_shortenings("y(ou) an(d) (be)cause (.) okay .")

        self.assertEqual(
            [
                (
                    shortening.raw_token,
                    shortening.observed_form,
                    shortening.expanded_form,
                    shortening.parenthetical_text,
                )
                for shortening in shortenings
            ],
            [
                ("y(ou)", "y", "you", "ou"),
                ("an(d)", "an", "and", "d"),
                ("(be)cause", "cause", "because", "be"),
            ],
        )

    def test_analyze_units_counts_only_scorable_utterances_by_speaker_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cha_path = base / "toy.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@ID:\teng|Toy|CHI|2;00.00|female|||",
                        "*CHI:\t&-uh y(ou) go .",
                        "*CHI:\t(.) .",
                        "*MOT:\thmmmm an(d) then ?",
                    ]
                ),
                encoding="utf-8",
            )
            unit = ChatUnit(
                child_id="Toy",
                files=[cha_path],
                base_dir=base,
                dataset="ToyDataset",
            )

            filler_rows, shortening_rows, filler_examples, shortening_examples = analyze_units([unit])

        self.assertEqual(len(filler_rows), 2)
        child = next(row for row in filler_rows if row["speaker_group"] == "CHILD")
        caretaker = next(row for row in filler_rows if row["speaker_group"] == "CARETAKERS")
        self.assertEqual(child["n_filler_tokens"], 1)
        self.assertEqual(child["n_filler_uh"], 1)
        self.assertEqual(caretaker["n_filler_hmm"], 1)

        child_short = next(row for row in shortening_rows if row["speaker_group"] == "CHILD")
        caretaker_short = next(row for row in shortening_rows if row["speaker_group"] == "CARETAKERS")
        self.assertEqual(child_short["shortening_raw_tokens"], "y(ou)")
        self.assertEqual(caretaker_short["shortening_raw_tokens"], "an(d)")
        self.assertEqual(len(filler_examples), 2)
        self.assertEqual(len(shortening_examples), 2)

    def test_write_outputs_creates_group_summaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cha_path = base / "toy.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@ID:\teng|Toy|CHI|2;00.00|female|||",
                        "*CHI:\tuh y(ou) .",
                    ]
                ),
                encoding="utf-8",
            )
            unit = ChatUnit(
                child_id="Toy",
                files=[cha_path],
                base_dir=base,
                dataset="ToyDataset",
            )
            filler_rows, shortening_rows, filler_examples, shortening_examples = analyze_units([unit])
            out_dir = base / "out"

            write_outputs(
                out_dir,
                filler_rows=filler_rows,
                shortening_rows=shortening_rows,
                filler_examples=filler_examples,
                shortening_examples=shortening_examples,
                filler_types=("uh",),
                datasets=("ToyDataset",),
                speakers=("CHI",),
                raw_bases={"ToyDataset": base},
                age_bin_width=6,
                include_unscorable=False,
                min_cleaned_words=1,
            )

            filler_summary = read_rows(out_dir / "fillers_by_dataset_speaker_group.csv")
            shortening_summary = read_rows(out_dir / "shortenings_by_dataset_speaker_group.csv")

        self.assertEqual(filler_summary[0]["speaker_group"], "CHILD")
        self.assertEqual(filler_summary[0]["utterances_with_filler"], "1")
        self.assertEqual(shortening_summary[0]["utterances_with_shortening"], "1")


if __name__ == "__main__":
    unittest.main()
