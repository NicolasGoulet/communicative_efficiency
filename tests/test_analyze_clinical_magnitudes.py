import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from analyze_clinical_magnitudes import (  # noqa: E402
    clinical_group,
    clinical_population,
    collect_unit_session_records,
    complete_age_bin_table,
    fixed_age_bin_label,
    missing_age_table,
)


def write_stage0(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
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
        "utt_id_role",
        "speaker",
        "utterance",
        "utterance_clean",
        "cleaned_is_empty",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


class TestAnalyzeClinicalMagnitudes(unittest.TestCase):
    def test_clinical_group_labels_requested_conditions_and_controls(self):
        self.assertEqual(
            clinical_group({"is_control": "0", "clinical_status": "autism", "clinical_dataset": "Toy_Autism"}),
            "Autism",
        )
        self.assertEqual(clinical_group({"is_control": "0", "clinical_status": "down_syndrome"}), "Down syndrome")
        self.assertEqual(clinical_group({"is_control": "0", "clinical_dataset": "Nicholas_HL"}), "Hearing loss")
        self.assertEqual(clinical_group({"is_control": "0", "clinical_dataset": "Feldman_SLI"}), "Focal lesions")
        self.assertEqual(clinical_group({"is_control": "0", "clinical_status": "late_talker"}), "Other clinical")
        self.assertEqual(clinical_group({"is_control": "1", "clinical_status": "typically_developing"}), "New TD controls")
        self.assertEqual(clinical_population({"is_control": "1"}), "New TD controls")
        self.assertEqual(clinical_population({"is_control": "0"}), "Clinical")

    def test_fixed_age_bin_label_uses_six_month_bins_starting_at_month_six(self):
        self.assertEqual(fixed_age_bin_label("6.0"), "006-011")
        self.assertEqual(fixed_age_bin_label("11.99"), "006-011")
        self.assertEqual(fixed_age_bin_label("12"), "012-017")
        self.assertEqual(fixed_age_bin_label("156.0"), "156-161")
        self.assertEqual(fixed_age_bin_label(""), "")

    def test_collect_unit_session_records_counts_nonempty_child_and_caretaker_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            common = {
                "dataset": "Toy",
                "child_id": "Ada",
                "source_group": "Toy",
                "session_id": "1",
                "age_raw": "2;00.00",
                "age_months": "24",
                "sex": "female",
                "file": "session1.cha",
                "line_no": "1",
                "reference_line": "session1.cha:1",
                "utt_id": "1",
                "utt_id_role": "1",
                "utterance": "hi .",
                "cleaned_is_empty": "0",
            }
            write_stage0(
                base / "chi.csv",
                [
                    {**common, "speaker": "CHI", "utterance_clean": "hi."},
                    {**common, "speaker": "CHI", "utterance_clean": ""},
                ],
            )
            write_stage0(
                base / "caretakers.csv",
                [
                    {**common, "speaker": "MOT", "utterance_clean": "look."},
                    {**common, "speaker": "MOT", "utterance_clean": "there."},
                ],
            )

            [record] = collect_unit_session_records(
                "Toy",
                "Ada",
                base / "chi.csv",
                base / "caretakers.csv",
                source_type="clinical_new",
                population="Clinical",
                analysis_group="Other clinical",
            )

        self.assertEqual(record["child_utterances"], 1)
        self.assertEqual(record["caretaker_utterances"], 2)
        self.assertEqual(record["total_utterances"], 3)
        self.assertEqual(record["age_bin_6m"], "024-029")

    def test_complete_age_bin_table_keeps_zero_rows_for_empty_requested_groups(self):
        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "age_bin_6m": "024-029",
                    "analysis_group": "Down syndrome",
                    "child_id": "Ada",
                    "unit_label": "Toy/Ada",
                    "file": "s1.cha",
                    "session_label": "Toy/Ada/s1.cha",
                    "child_utterances": 2,
                    "caretaker_utterances": 3,
                    "total_utterances": 5,
                }
            ]
        )

        table = complete_age_bin_table(
            df,
            group_column="analysis_group",
            group_order=["Autism", "Down syndrome"],
        )
        autism_total = table[
            (table["analysis_group"] == "Autism")
            & (table["age_bin_6m"] == "024-029")
            & (table["role"] == "total")
        ].iloc[0]
        ds_total = table[
            (table["analysis_group"] == "Down syndrome")
            & (table["age_bin_6m"] == "024-029")
            & (table["role"] == "total")
        ].iloc[0]

        self.assertEqual(autism_total["utterances"], 0)
        self.assertEqual(ds_total["utterances"], 5)

    def test_missing_age_table_reports_unbinned_utterances(self):
        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "age_bin_6m": "",
                    "analysis_group": "Other clinical",
                    "child_id": "Ada",
                    "unit_label": "Toy/Ada",
                    "file": "s1.cha",
                    "session_label": "Toy/Ada/s1.cha",
                    "child_utterances": 2,
                    "caretaker_utterances": 0,
                    "total_utterances": 2,
                }
            ]
        )

        table = missing_age_table(df, group_column="analysis_group", group_order=["Autism", "Other clinical"])
        other_child = table[(table["analysis_group"] == "Other clinical") & (table["role"] == "child")].iloc[0]
        autism_child = table[(table["analysis_group"] == "Autism") & (table["role"] == "child")].iloc[0]

        self.assertEqual(other_child["utterances"], 2)
        self.assertEqual(other_child["n_sessions"], 1)
        self.assertEqual(autism_child["utterances"], 0)


if __name__ == "__main__":
    unittest.main()
