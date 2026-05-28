import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from extract_child_metadata_summary import (  # noqa: E402
    OUTPUT_COLUMNS,
    parse_chat_header,
    parse_chat_id_line,
    summarize_child_folder,
    write_metadata_summary,
)


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class TestExtractChildMetadataSummary(unittest.TestCase):
    def test_parse_chat_id_line_extracts_standard_child_fields(self):
        parsed = parse_chat_id_line("@ID:\teng|Toy|CHI|2;03.04|female|TD|working|Target_Child|mother_college|custom")

        self.assertEqual(parsed["language"], "eng")
        self.assertEqual(parsed["corpus"], "Toy")
        self.assertEqual(parsed["code"], "CHI")
        self.assertEqual(parsed["age"], "2;03.04")
        self.assertEqual(parsed["sex"], "female")
        self.assertEqual(parsed["group"], "TD")
        self.assertEqual(parsed["ses"], "working")
        self.assertEqual(parsed["role"], "Target_Child")
        self.assertEqual(parsed["education"], "mother_college")
        self.assertEqual(parsed["custom"], "custom")

    def test_parse_chat_header_collects_demographic_header_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            cha = Path(tmp) / "sample.cha"
            cha.write_text(
                "\n".join(
                    [
                        "@Begin",
                        "@Participants:\tCHI Target_Child, MOT Mother",
                        "@ID:\teng|Toy|CHI|2;03.04|female|TD|middle|Target_Child|||",
                        "@Birth of CHI:\t01-JAN-2020",
                        "@Date:\t05-APR-2022",
                        "@Location:\tHome",
                        "@Situation:\tbirthday party with family",
                        "@Types:\tlong, toyplay, TD",
                        "@Comment:\tSES is middle class",
                        "*CHI:\thello .",
                    ]
                ),
                encoding="utf-8",
            )

            parsed = parse_chat_header(cha)

        self.assertEqual(parsed["chi_id_age_values"], {"2;03.04"})
        self.assertEqual(parsed["chi_id_sex_values"], {"female"})
        self.assertEqual(parsed["chi_id_group_values"], {"TD"})
        self.assertEqual(parsed["chi_id_ses_values"], {"middle"})
        self.assertEqual(parsed["birth_of_chi_values"], {"01-JAN-2020"})
        self.assertEqual(parsed["date_values"], {"05-APR-2022"})
        self.assertEqual(parsed["location_values"], {"Home"})
        self.assertEqual(parsed["types_values"], {"long, toyplay, TD"})
        self.assertIn("@Comment: SES is middle class", parsed["demographic_header_values"])
        self.assertNotIn("@Situation: birthday party with family", parsed["demographic_header_values"])

    def test_summarize_child_folder_counts_rows_headers_and_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            child_dir = base / "data" / "preprocessed_data" / "ToySet" / "Ada"
            raw_base = base / "data" / "raw_data" / "ToySet"
            raw_base.mkdir(parents=True)
            (raw_base / "session1.cha").write_text(
                "\n".join(
                    [
                        "@Begin",
                        "@Participants:\tCHI Target_Child, MOT Mother",
                        "@ID:\teng|ToySet|CHI|2;00.00|female|TD|low|Target_Child|||",
                        "@Date:\t01-JAN-2022",
                        "@Location:\tHome",
                        "@Types:\tlong, toyplay, TD",
                        "*CHI:\thi .",
                    ]
                ),
                encoding="utf-8",
            )
            rows = [
                {
                    "dataset": "ToySet",
                    "child_id": "Ada",
                    "source_group": "ToySet",
                    "session_id": "1",
                    "age_raw": "2;00.00",
                    "age_months": "24",
                    "sex": "female",
                    "file": "session1.cha",
                    "line_no": "10",
                    "reference_line": "session1.cha:10",
                    "utt_id": "1",
                    "utt_id_role": "1",
                    "speaker": "CHI",
                    "utterance": "hi .",
                    "utterance_clean": "hi.",
                    "cleaned_is_empty": "0",
                },
                {
                    "dataset": "ToySet",
                    "child_id": "Ada",
                    "source_group": "ToySet",
                    "session_id": "1",
                    "age_raw": "2;00.00",
                    "age_months": "",
                    "sex": "female",
                    "file": "session1.cha",
                    "line_no": "11",
                    "reference_line": "session1.cha:11",
                    "utt_id": "2",
                    "utt_id_role": "2",
                    "speaker": "CHI",
                    "utterance": "xxx .",
                    "utterance_clean": "",
                    "cleaned_is_empty": "1",
                },
            ]
            write_csv(child_dir / "chi.csv", rows)
            caretaker_rows = [dict(rows[0], speaker="MOT", utterance_clean="look.", utt_id="1")]
            write_csv(child_dir / "caretakers.csv", caretaker_rows)
            for filename in (
                "chi.ngram_generated.csv",
                "chi.shared_caretaker_contexts.csv",
                "caretakers.shared_caretaker_contexts.csv",
                "chi.surprisal_scoring.csv",
                "caretakers.surprisal_scoring.csv",
            ):
                (child_dir / filename).write_text("dummy\n", encoding="utf-8")

            summary = summarize_child_folder(
                child_dir,
                grouping={"ToySet": {"analysis_group": "naturalistic", "include_in_default_naturalistic": "1"}},
                raw_base=raw_base,
            )

        self.assertEqual(summary["dataset"], "ToySet")
        self.assertEqual(summary["child_id"], "Ada")
        self.assertEqual(summary["analysis_group"], "naturalistic")
        self.assertEqual(summary["stage0_ready"], 1)
        self.assertEqual(summary["scoring_ready"], 1)
        self.assertEqual(summary["child_rows"], 2)
        self.assertEqual(summary["child_nonempty_utterances"], 1)
        self.assertEqual(summary["caretaker_nonempty_utterances"], 1)
        self.assertEqual(summary["child_missing_age_rows"], 1)
        self.assertEqual(summary["age_months_min"], 24.0)
        self.assertEqual(summary["age_months_max"], 24.0)
        self.assertEqual(summary["sex_values"], "female")
        self.assertEqual(summary["chi_id_ses_values"], "low")
        self.assertEqual(summary["participant_values"], "CHI Target_Child, MOT Mother")
        self.assertEqual(summary["caretaker_speaker_values"], "MOT")
        self.assertEqual(summary["raw_header_files_read"], 1)
        self.assertEqual(summary["raw_files_missing"], 0)

    def test_write_metadata_summary_uses_exact_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.csv"
            write_metadata_summary(path, [{"dataset": "ToySet", "child_id": "Ada"}])
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                header = next(reader)
                row = next(reader)

        self.assertEqual(header, OUTPUT_COLUMNS)
        self.assertEqual(row[OUTPUT_COLUMNS.index("dataset")], "ToySet")
        self.assertEqual(row[OUTPUT_COLUMNS.index("child_id")], "Ada")


if __name__ == "__main__":
    unittest.main()
