import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from prepare_clinical_datasets import (  # noqa: E402
    CLINICAL_CHILD_METADATA_COLUMNS,
    ClinicalSpec,
    age_from_filename_stem,
    age_from_numeric_parent_dir,
    build_dataset_metadata_rows,
    caretaker_speakers_for_unit,
    child_id_from_ambrose_filename,
    child_id_from_feldman_filename,
    child_id_from_hooshyar_filename,
    child_id_from_nicholas_filename,
    child_id_from_rescorla_filename,
    child_id_from_rondal_filename,
    discover_units_for_spec,
    is_caregiver_speaker,
    prepare_clinical_datasets,
)


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TestPrepareClinicalDatasets(unittest.TestCase):
    def test_child_id_helpers_match_clinical_corpus_layouts(self):
        self.assertEqual(child_id_from_rondal_filename(Path("ava1.cha")), "ava")
        self.assertEqual(child_id_from_ambrose_filename(Path("13/87FB_14.cha")), "87FB")
        self.assertEqual(child_id_from_hooshyar_filename(Path("story/s042.cha")), "042")
        self.assertEqual(child_id_from_nicholas_filename(Path("hi24f-valencia.cha")), "valencia")
        self.assertEqual(child_id_from_feldman_filename(Path("PC-ac/bea21.cha")), "bea")
        self.assertEqual(child_id_from_feldman_filename(Path("nchi0127.cha")), "nchi01")
        self.assertEqual(child_id_from_rescorla_filename(Path("LT/108/ly2108.cha")), "ly2")
        self.assertEqual(child_id_from_rescorla_filename(Path("LT/36/gr36a.cha")), "gr")

    def test_age_fallbacks_cover_probe_filename_and_measurement_folders(self):
        self.assertEqual(age_from_filename_stem(Path("060921.cha")), ("6;09.21", 81.7))
        self.assertEqual(age_from_filename_stem(Path("041199.cha")), ("", None))
        self.assertEqual(age_from_numeric_parent_dir(Path("LT/108/ale108.cha")), ("9;00.00", 108.0))
        self.assertEqual(age_from_numeric_parent_dir(Path("not_numeric/ale.cha")), ("", None))

    def test_caregiver_detection_uses_chat_roles_without_keeping_investigators_or_siblings(self):
        self.assertTrue(is_caregiver_speaker("MOT", "Mother"))
        self.assertTrue(is_caregiver_speaker("GMA", "Grandmother"))
        self.assertFalse(is_caregiver_speaker("INV", "Investigator"))
        self.assertFalse(is_caregiver_speaker("BRO", "Brother"))

    def test_discovery_groups_ambrose_files_by_child_across_age_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp)
            base = raw_root / "Ambrose" / "HL"
            for folder in ("13", "18"):
                (base / folder).mkdir(parents=True)
            (base / "13" / "87FB_14.cha").write_text("@Begin\n", encoding="utf-8")
            (base / "18" / "87FB_18.cha").write_text("@Begin\n", encoding="utf-8")
            (base / "18" / "90BM_18.cha").write_text("@Begin\n", encoding="utf-8")
            spec = ClinicalSpec("Ambrose_HL", ("Ambrose", "HL"), "Ambrose", "HL", "hearing_loss", 0, "ambrose_age_dirs")

            units = discover_units_for_spec(spec, raw_root)

        by_child = {unit.child_id: unit for unit in units}
        self.assertEqual(sorted(by_child), ["87FB", "90BM"])
        self.assertEqual(len(by_child["87FB"].files), 2)
        self.assertEqual(by_child["87FB"].source_group, "HL")

    def test_prepare_clinical_datasets_writes_stage0_files_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw_root = base / "raw" / "Clinical"
            output_dir = base / "preprocessed_clinical_data"
            child_metadata = base / "clinical_child_metadata_summary.csv"
            dataset_metadata = base / "clinical_dataset_summary.csv"
            corpus_dir = raw_root / "Rondal" / "DS"
            corpus_dir.mkdir(parents=True)
            for name, age, utterance in (
                ("ava1.cha", "10;00.", "hello ."),
                ("ava2.cha", "10;01.", "more ."),
            ):
                (corpus_dir / name).write_text(
                    "\n".join(
                        [
                            "@Begin",
                            "@Participants:\tCHI Target_Child, MOT Mother, INV Investigator",
                            f"@ID:\teng|DS|CHI|{age}|female|DS||Target_Child|||",
                            "@ID:\teng|DS|MOT||female|||Mother|||",
                            "@ID:\teng|DS|INV|||||Investigator|||",
                            "@Comment:\tSES is middle class",
                            "@Types:\tcross, toyplay, DS",
                            f"*CHI:\t{utterance}",
                            "*MOT:\tyes .",
                            "*INV:\tignored .",
                        ]
                    ),
                    encoding="utf-8",
                )

            summary = prepare_clinical_datasets(
                raw_root=raw_root,
                output_dir=output_dir,
                datasets=["Rondal_DS"],
                child_metadata_path=child_metadata,
                dataset_metadata_path=dataset_metadata,
            )
            chi_rows = read_rows(output_dir / "Rondal_DS" / "ava" / "chi.csv")
            caretaker_rows = read_rows(output_dir / "Rondal_DS" / "ava" / "caretakers.csv")
            metadata_rows = read_rows(child_metadata)
            dataset_rows = read_rows(dataset_metadata)

            with (output_dir / "manifest.csv").open(newline="", encoding="utf-8") as handle:
                manifest_header = csv.DictReader(handle).fieldnames

        self.assertEqual(summary["children"], 1)
        self.assertEqual(summary["clinical_children"], 1)
        self.assertEqual(summary["control_children"], 0)
        self.assertEqual([row["utterance_clean"] for row in chi_rows], ["hello.", "more."])
        self.assertEqual({row["speaker"] for row in caretaker_rows}, {"MOT"})
        self.assertEqual(len(caretaker_rows), 2)
        self.assertEqual(manifest_header, CLINICAL_CHILD_METADATA_COLUMNS)
        self.assertEqual(metadata_rows[0]["clinical_dataset"], "Rondal_DS")
        self.assertEqual(metadata_rows[0]["clinical_group"], "DS")
        self.assertEqual(metadata_rows[0]["is_control"], "0")
        self.assertEqual(metadata_rows[0]["child_nonempty_utterances"], "2")
        self.assertEqual(metadata_rows[0]["caretaker_nonempty_utterances"], "2")
        self.assertIn("SES is middle class", metadata_rows[0]["demographic_header_values"])
        self.assertEqual(dataset_rows[0]["n_children"], "1")
        self.assertEqual(dataset_rows[0]["n_clinical_children"], "1")

    def test_dataset_metadata_aggregates_pipe_delimited_values_without_duplicates(self):
        rows = [
            {
                "clinical_dataset": "Toy_TD",
                "corpus": "Toy",
                "clinical_group": "TD",
                "clinical_status": "typically_developing_control",
                "is_control": 1,
                "child_rows": 2,
                "caretaker_rows": 3,
                "child_nonempty_utterances": 2,
                "caretaker_nonempty_utterances": 3,
                "total_nonempty_utterances": 5,
                "n_sessions": 1,
                "n_source_files": 1,
                "age_months_min": 12,
                "age_months_max": 18,
                "sex_values": "female | male",
                "caretaker_speaker_values": "MOT | FAT",
                "types_values": "long, toyplay, TD",
            },
            {
                "clinical_dataset": "Toy_TD",
                "corpus": "Toy",
                "clinical_group": "TD",
                "clinical_status": "typically_developing_control",
                "is_control": 1,
                "child_rows": 1,
                "caretaker_rows": 0,
                "child_nonempty_utterances": 1,
                "caretaker_nonempty_utterances": 0,
                "total_nonempty_utterances": 1,
                "n_sessions": 1,
                "n_source_files": 1,
                "age_months_min": 19,
                "age_months_max": 24,
                "sex_values": "female",
                "caretaker_speaker_values": "MOT",
                "types_values": "long, toyplay, TD",
            },
        ]

        [summary] = build_dataset_metadata_rows(rows)

        self.assertEqual(summary["sex_values"], "female | male")
        self.assertEqual(summary["caretaker_speaker_values"], "FAT | MOT")
        self.assertEqual(summary["types_values"], "long, toyplay, TD")


if __name__ == "__main__":
    unittest.main()
