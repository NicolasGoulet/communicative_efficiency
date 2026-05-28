import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "cleaning"

from prepare_datasets import (  # noqa: E402
    ChatUnit,
    DATASETS,
    DEFAULT_RAW_ROOTS,
    PREPARED_CHAT_COLUMNS,
    age_from_filename_stem,
    age_from_parent_month_dir,
    caretaker_speakers_for_unit,
    discover_dataset_units,
    process_input_path,
    read_session_metadata,
)


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestPrepareDatasets(unittest.TestCase):
    def test_known_dataset_registry_includes_mpi_eva_manchester(self):
        self.assertIn("MPI-EVA-Manchester", DATASETS)
        self.assertIn("MPI-EVA-Manchester", DEFAULT_RAW_ROOTS)

    def test_known_dataset_registry_includes_new_longitudinal_candidates(self):
        for dataset in ("Belfast", "Wells", "Champaign", "EHS", "Cummings"):
            self.assertIn(dataset, DATASETS)
            self.assertIn(dataset, DEFAULT_RAW_ROOTS)

    def test_known_dataset_registry_includes_strict_naturalistic_downloads(self):
        for dataset in ("Lara", "Sachs", "Weist", "Kuczaj", "Post", "Demetras1", "Forrester"):
            self.assertIn(dataset, DATASETS)
            self.assertIn(dataset, DEFAULT_RAW_ROOTS)

    # Use case: several strict naturalistic corpora store all CHAT files for
    # one target child directly in the corpus root rather than under a child
    # subfolder. These direct files should be grouped as a single child unit.
    def test_direct_root_dataset_discovery_groups_root_files_as_one_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "020424.cha").write_text("@Begin\n", encoding="utf-8")
            (base / "020500.cha").write_text("@Begin\n", encoding="utf-8")
            (base / "media").mkdir()
            (base / "media" / "ignored.cha").write_text("@Begin\n", encoding="utf-8")

            units = discover_dataset_units("Kuczaj", base)

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].child_id, "Abe")
        self.assertEqual(units[0].source_group, "Kuczaj")
        self.assertEqual([path.name for path in units[0].files], ["020424.cha", "020500.cha"])

    # Use case: Lara includes a grandmother speaker as a primary caregiver in
    # the raw CHAT headers, so preprocessing should not drop that context.
    def test_lara_grandmother_tier_is_kept_as_caretaker(self):
        lara_unit = ChatUnit(
            child_id="Lara",
            files=[],
            base_dir=Path("Lara"),
            dataset="Lara",
            source_group="Lara",
        )
        brown_unit = ChatUnit(
            child_id="Adam",
            files=[],
            base_dir=Path("Brown"),
            dataset="Brown",
            source_group="Brown",
        )

        self.assertEqual(caretaker_speakers_for_unit(lara_unit), ("MOT", "FAT", "ELS"))
        self.assertEqual(caretaker_speakers_for_unit(brown_unit), ("MOT", "FAT"))

    # Use case: Champaign and EHS store measurement/context folders first and
    # child IDs second, so files must be grouped by stem across folders.
    def test_measurement_folder_discovery_groups_files_by_child_id_across_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for folder in ("21P", "24P"):
                (base / folder).mkdir()
            (base / "21P" / "01G.cha").write_text("@Begin\n", encoding="utf-8")
            (base / "24P" / "01G.cha").write_text("@Begin\n", encoding="utf-8")
            (base / "24P" / "02B.cha").write_text("@Begin\n", encoding="utf-8")

            champaign_units = discover_dataset_units("Champaign", base)
            ehs_units = discover_dataset_units("EHS", base)

        by_child = {unit.child_id: unit for unit in champaign_units}
        self.assertEqual(sorted(by_child), ["01G", "02B"])
        self.assertEqual(len(by_child["01G"].files), 2)
        self.assertEqual(len(by_child["02B"].files), 1)
        self.assertEqual(by_child["01G"].source_group, "Champaign")
        self.assertEqual(by_child["01G"].base_dir, base)
        self.assertEqual(sorted(unit.child_id for unit in ehs_units), ["01G", "02B"])
        self.assertEqual({unit.source_group for unit in ehs_units}, {"EHS"})

    # Use case: MPI-EVA-Manchester filenames encode recording age when the
    # CHAT @ID line leaves CHI age blank, e.g. 020500b.cha means 2;05.00.
    def test_age_from_filename_stem_supports_mpi_eva_manchester_age_codes(self):
        self.assertEqual(age_from_filename_stem(Path("030400.cha")), ("3;04.00", 40.0))
        self.assertEqual(age_from_filename_stem(Path("020500b.cha")), ("2;05.00", 29.0))
        self.assertEqual(age_from_filename_stem(Path("050113.cha")), ("5;01.13", 61.433))
        self.assertEqual(age_from_filename_stem(Path("not_an_age.cha")), ("", None))
        self.assertEqual(age_from_filename_stem(Path("031299.cha")), ("", None))

    # Use case: Champaign's folder name can encode the nominal measurement age
    # when the transcript-level CHI @ID age is blank.
    def test_age_from_parent_month_dir_supports_champaign_measurement_folders(self):
        self.assertEqual(age_from_parent_month_dir(Path("21P/05G.cha")), ("1;09.00", 21.0))
        self.assertEqual(age_from_parent_month_dir(Path("30X/13B.cha")), ("2;06.00", 30.0))
        self.assertEqual(age_from_parent_month_dir(Path("24-mot/0169.cha")), ("2;00.00", 24.0))
        self.assertEqual(age_from_parent_month_dir(Path("PD16/030400.cha")), ("", None))

    # Use case: blank CHI age in the @ID tier should not make otherwise valid
    # MPI-EVA-Manchester sessions disappear from age-bin analyses.
    def test_read_session_metadata_falls_back_to_filename_age_when_chi_age_is_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            cha_path = Path(tmp) / "030400.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@Begin",
                        "@ID:\teng|MPI-EVA-Manchester|CHI|||||Target_Child|||",
                        "*CHI:\thello .",
                    ]
                ),
                encoding="utf-8",
            )

            metadata = read_session_metadata(cha_path)

        self.assertEqual(metadata["age_raw"], "3;04.00")
        self.assertEqual(metadata["age_months"], 40.0)
        self.assertEqual(metadata["sex"], "")

    # Use case: if neither @ID nor filename carries an age, Champaign-style
    # parent measurement folders still keep the row age-binnable.
    def test_read_session_metadata_falls_back_to_parent_month_dir_when_needed(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "21P"
            folder.mkdir()
            cha_path = folder / "05G.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@Begin",
                        "@ID:\teng|Champaign|CHI||female|||Target_Child|||",
                        "*CHI:\thello .",
                    ]
                ),
                encoding="utf-8",
            )

            metadata = read_session_metadata(cha_path)

        self.assertEqual(metadata["age_raw"], "1;09.00")
        self.assertEqual(metadata["age_months"], 21.0)
        self.assertEqual(metadata["sex"], "female")

    # Use case: EHS sometimes leaves CHI @ID age/sex blank but records them in
    # header comments.
    def test_read_session_metadata_falls_back_to_header_age_and_sex_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            cha_path = Path(tmp) / "0538.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@Begin",
                        "@ID:\teng|EHS|CHI|||||Target_Child|||",
                        "@Comment:\tage is 5;1.15",
                        "@Comment:\tsex is female",
                        "*CHI:\thello .",
                    ]
                ),
                encoding="utf-8",
            )

            metadata = read_session_metadata(cha_path)

        self.assertEqual(metadata["age_raw"], "5;1.15")
        self.assertEqual(metadata["age_months"], 61.5)
        self.assertEqual(metadata["sex"], "female")

    # Use case: run the new prepare pipeline on one realistic CHAT file and get
    # the two normal analysis files plus the optional combined inspection file.
    def test_process_input_path_writes_chi_caretakers_and_testing_csv(self):
        input_path = FIXTURE_DIR / "brown_tic_tac_toe_sample.cha"

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            written = process_input_path(input_path, output_root, testing=True)

            child_dir = output_root / "brown_tic_tac_toe_sample"
            chi_rows = read_rows(child_dir / "chi.csv")
            caretaker_rows = read_rows(child_dir / "caretakers.csv")
            testing_rows = read_rows(child_dir / "testing.csv")

            with (child_dir / "chi.csv").open(newline="", encoding="utf-8") as fh:
                headers = csv.DictReader(fh).fieldnames

        self.assertEqual(written, {"children": 1, "rows": 18})
        self.assertEqual(headers, PREPARED_CHAT_COLUMNS)
        self.assertEqual(len(chi_rows), 13)
        self.assertEqual(len(caretaker_rows), 5)
        self.assertEqual(len(testing_rows), 18)
        self.assertEqual({row["speaker"] for row in caretaker_rows}, {"MOT"})
        self.assertNotIn("GAI", {row["speaker"] for row in testing_rows})

        self.assertEqual(testing_rows[0]["dataset"], "")
        self.assertEqual(testing_rows[0]["child_id"], "brown_tic_tac_toe_sample")
        self.assertEqual(testing_rows[0]["session_id"], "1")
        self.assertEqual(testing_rows[0]["age_raw"], "5;00.16")
        self.assertEqual(testing_rows[0]["age_months"], "60.533")
        self.assertEqual(testing_rows[0]["reference_line"], "brown_tic_tac_toe_sample.cha:14")
        self.assertEqual(testing_rows[0]["utterance_clean"], "hi.")

        letter_rows = {
            row["reference_line"]: (row["utterance"], row["utterance_clean"])
            for row in testing_rows
            if "@l" in row["utterance"]
        }
        self.assertEqual(
            letter_rows,
            {
                "brown_tic_tac_toe_sample.cha:57": ("zero or a o@l .", "zero or a o."),
                "brown_tic_tac_toe_sample.cha:60": ("zero or an o@l ?", "zero or an o?"),
                "brown_tic_tac_toe_sample.cha:66": ("no (.) zero or an x@l .", "no zero or an x."),
                "brown_tic_tac_toe_sample.cha:69": ("zero or a x@l ?", "zero or a x?"),
                "brown_tic_tac_toe_sample.cha:75": ("y(ou) want zero or a x@l ?", "y want zero or a x?"),
            },
        )

    # Use case: keep the raw/cleaned rows even when cleaning removes all lexical
    # material, so any later filtering decision is visible and testable.
    def test_process_input_path_keeps_empty_cleaned_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cha_path = base / "toy.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@ID:\teng|Toy|CHI|2;00.00|female|||",
                        "*CHI:\txxx ?",
                        "*MOT:\t0 .",
                    ]
                ),
                encoding="utf-8",
            )

            process_input_path(cha_path, base / "out", testing=True)
            child_dir = base / "out" / "toy"
            chi_rows = read_rows(child_dir / "chi.csv")
            caretaker_rows = read_rows(child_dir / "caretakers.csv")
            testing_rows = read_rows(child_dir / "testing.csv")

        self.assertEqual([row["cleaned_is_empty"] for row in testing_rows], ["1", "1"])
        self.assertEqual([row["utterance_clean"] for row in testing_rows], ["", ""])
        self.assertEqual([row["reference_line"] for row in testing_rows], ["toy.cha:2", "toy.cha:3"])
        self.assertEqual(chi_rows[0]["utterance"], "xxx ?")
        self.assertEqual(chi_rows[0]["utterance_clean"], "")
        self.assertEqual(caretaker_rows[0]["utterance"], "0 .")
        self.assertEqual(caretaker_rows[0]["utterance_clean"], "")

    # Use case: prepare_datasets uses the shared cleaner, so word-like CHAT
    # special form markers should survive in utterance_clean without the marker
    # suffix.
    def test_process_input_path_keeps_requested_special_form_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cha_path = base / "toy.cha"
            cha_path.write_text(
                "\n".join(
                    [
                        "@ID:\teng|Toy|CHI|2;00.00|female|||",
                        "*CHI:\tbunko@f gumma@c younz@d abame@b uhhuh@i .",
                        "*MOT:\tp@ls abcd@k breaked@n aga@p goobarumba@wp ?",
                    ]
                ),
                encoding="utf-8",
            )

            process_input_path(cha_path, base / "out", testing=True)
            child_dir = base / "out" / "toy"
            testing_rows = read_rows(child_dir / "testing.csv")

        self.assertEqual(
            [row["utterance_clean"] for row in testing_rows],
            [
                "bunko gumma younz abame uhhuh.",
                "p abcd breaked aga goobarumba?",
            ],
        )


if __name__ == "__main__":
    unittest.main()
