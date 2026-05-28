import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from prepare_datasets import ChatUnit  # noqa: E402
from special_forms_per_utterance import (  # noqa: E402
    DEFAULT_MARKERS,
    analyze_units,
    extract_special_forms,
    write_report,
)


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestSpecialFormsPerUtterance(unittest.TestCase):
    def test_extract_special_forms_keeps_code_and_family(self):
        forms = extract_special_forms(
            "bunko@f p@ls abcd@k dumpf@n$v istemem@s:hu but@q-s word@z:rftd ."
        )

        self.assertEqual(
            [(form.raw_token, form.lexical_base, form.marker_code, form.marker_family) for form in forms],
            [
                ("bunko@f", "bunko", "f", "f"),
                ("p@ls", "p", "ls", "ls"),
                ("abcd@k", "abcd", "k", "k"),
                ("dumpf@n$v", "dumpf", "n", "n"),
                ("istemem@s:hu", "istemem", "s:hu", "s"),
                ("but@q-s", "but", "q-s", "q"),
                ("word@z:rftd", "word", "z:rftd", "z"),
            ],
        )

    def test_analyze_units_counts_special_forms_on_usable_utterances(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cha_path = base / "toy.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@ID:\teng|Toy|CHI|2;00.00|female|||",
                        "*CHI:\tbunko@f gumma@c p@ls .",
                        "*CHI:\txxx ?",
                        "*MOT:\tabcd@k breaked@n aga@p ?",
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

            report = analyze_units([unit], markers=DEFAULT_MARKERS)

        self.assertEqual(len(report.utterance_rows), 2)
        self.assertEqual(report.group_totals[("ToyDataset", "CHI")], 1)
        self.assertEqual(report.group_totals[("ToyDataset", "MOT")], 1)
        self.assertEqual(report.group_marker_token_counts[("ToyDataset", "CHI", "f")], 1)
        self.assertEqual(report.group_marker_token_counts[("ToyDataset", "CHI", "c")], 1)
        self.assertEqual(report.group_marker_token_counts[("ToyDataset", "CHI", "ls")], 1)
        self.assertEqual(report.group_marker_token_counts[("ToyDataset", "MOT", "k")], 1)
        self.assertEqual(report.group_marker_token_counts[("ToyDataset", "MOT", "n")], 1)
        self.assertEqual(report.group_marker_token_counts[("ToyDataset", "MOT", "p")], 1)

        chi_row = next(row for row in report.utterance_rows if row["speaker"] == "CHI")
        self.assertEqual(chi_row["utterance_clean"], "bunko gumma p.")
        self.assertEqual(chi_row["n_target_special_form_tokens"], 3)
        self.assertEqual(chi_row["n_at_f"], 1)
        self.assertEqual(chi_row["n_at_c"], 1)
        self.assertEqual(chi_row["n_at_ls"], 1)

    def test_write_report_outputs_expected_csvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cha_path = base / "toy.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@ID:\teng|Toy|CHI|2;00.00|female|||",
                        "*CHI:\tbunko@f .",
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
            report = analyze_units([unit], markers=("f",))
            out_dir = base / "out"

            write_report(
                report,
                out_dir,
                markers=("f",),
                datasets=("ToyDataset",),
                speakers=("CHI",),
                raw_bases={"ToyDataset": base},
                age_bin_width=6,
                include_empty_cleaned=False,
                min_cleaned_words=1,
                utterance_mode="all",
            )

            utterance_rows = read_rows(out_dir / "special_forms_per_utterance.csv")
            marker_rows = read_rows(out_dir / "special_forms_by_dataset_speaker_marker.csv")

        self.assertEqual(utterance_rows[0]["n_at_f"], "1")
        self.assertEqual(marker_rows[0]["marker"], "f")
        self.assertEqual(marker_rows[0]["utterances_with_marker"], "1")


if __name__ == "__main__":
    unittest.main()
