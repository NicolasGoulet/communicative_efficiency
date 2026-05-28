import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from create_big_cleaned_dataset import (  # noqa: E402
    CHILD_BASELINE_COLUMNS,
    MANIFEST_COLUMNS,
    count_child_utterances_by_month,
    copy_stage0_files,
    create_big_cleaned_dataset,
    filter_child_scoring_files_for_complete_baselines,
    select_datasets,
    write_manifest,
)
from build_age_word_dicts import ChildUnit  # noqa: E402


BASE_FIELDS = [
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


def write_csv(path: Path, rows, fieldnames=BASE_FIELDS):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def write_grouping(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dataset", "analysis_group", "include_in_default_naturalistic", "reason"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "dataset": "ToySet",
                "analysis_group": "naturalistic_caregiver_child",
                "include_in_default_naturalistic": "1",
                "reason": "test naturalistic corpus",
            }
        )
        writer.writerow(
            {
                "dataset": "ProbeSet",
                "analysis_group": "clinical_probe",
                "include_in_default_naturalistic": "0",
                "reason": "test excluded corpus",
            }
        )


def stage0_rows(dataset="ToySet", child="Ada"):
    child_row = {
        "dataset": dataset,
        "child_id": child,
        "source_group": dataset,
        "session_id": "1",
        "age_raw": "0;07.00",
        "age_months": "7",
        "sex": "female",
        "file": "session1.cha",
        "line_no": "10",
        "reference_line": "session1.cha:10",
        "utt_id": "2",
        "utt_id_role": "1",
        "speaker": "CHI",
        "utterance": "more milk .",
        "utterance_clean": "more milk.",
        "cleaned_is_empty": "0",
    }
    caretaker_row = dict(
        child_row,
        line_no="5",
        reference_line="session1.cha:5",
        utt_id="1",
        speaker="MOT",
        utterance="want some .",
        utterance_clean="want some.",
    )
    return child_row, caretaker_row


class TestCreateBigCleanedDataset(unittest.TestCase):
    def test_select_datasets_uses_default_naturalistic_grouping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "preprocessed"
            write_grouping(root / "groups.csv")
            child_row, caretaker_row = stage0_rows("ToySet", "Ada")
            write_csv(source / "ToySet" / "Ada" / "chi.csv", [child_row])
            write_csv(source / "ToySet" / "Ada" / "caretakers.csv", [caretaker_row])
            child_row, caretaker_row = stage0_rows("ProbeSet", "Bea")
            write_csv(source / "ProbeSet" / "Bea" / "chi.csv", [child_row])
            write_csv(source / "ProbeSet" / "Bea" / "caretakers.csv", [caretaker_row])

            selected = select_datasets(
                data_dir=source,
                grouping_csv=root / "groups.csv",
                selection="default_naturalistic",
            )

        self.assertEqual(selected, ["ToySet"])

    def test_copy_stage0_files_copies_only_cleaned_base_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_child = root / "source" / "ToySet" / "Ada"
            child_row, caretaker_row = stage0_rows()
            write_csv(source_child / "chi.csv", [child_row])
            write_csv(source_child / "caretakers.csv", [caretaker_row])
            (source_child / "chi.ngram_generated.csv").write_text("old artifact\n", encoding="utf-8")
            unit = ChildUnit(
                dataset="ToySet",
                child="Ada",
                folder=source_child,
                chi_csv=source_child / "chi.csv",
                caretakers_csv=source_child / "caretakers.csv",
            )

            copied = copy_stage0_files([unit], root / "big" / "preprocessed_data")

            copied_child = copied[0].folder
            self.assertTrue((copied_child / "chi.csv").exists())
            self.assertTrue((copied_child / "caretakers.csv").exists())
            self.assertFalse((copied_child / "chi.ngram_generated.csv").exists())

    def test_count_child_utterances_by_month_uses_nonempty_numeric_child_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            child_dir = Path(tmp) / "ToySet" / "Ada"
            row, caretaker_row = stage0_rows()
            write_csv(
                child_dir / "chi.csv",
                [
                    dict(row, age_months="18.9", utterance_clean="more milk."),
                    dict(row, age_months="18.1", utterance_clean="again."),
                    dict(row, age_months="", utterance_clean="missing age."),
                    dict(row, age_months="19", utterance_clean=""),
                ],
            )
            write_csv(child_dir / "caretakers.csv", [caretaker_row])
            unit = ChildUnit(
                dataset="ToySet",
                child="Ada",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )

            counts = count_child_utterances_by_month([unit])

        self.assertEqual(counts, {18: 2})

    def test_write_manifest_uses_exact_columns_and_counts_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            child_dir = Path(tmp) / "ToySet" / "Ada"
            child_row, caretaker_row = stage0_rows()
            write_csv(child_dir / "chi.csv", [child_row])
            write_csv(child_dir / "caretakers.csv", [caretaker_row])
            write_csv(child_dir / "chi.surprisal_scoring.csv", [child_row])
            write_csv(child_dir / "caretakers.surprisal_scoring.csv", [caretaker_row])
            unit = ChildUnit(
                dataset="ToySet",
                child="Ada",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )

            rows = write_manifest(Path(tmp) / "manifest.csv", [unit])
            with (Path(tmp) / "manifest.csv").open(newline="", encoding="utf-8") as handle:
                parsed = list(csv.reader(handle))

        self.assertEqual(parsed[0], MANIFEST_COLUMNS)
        self.assertEqual(rows[0]["chi_rows"], 1)
        self.assertEqual(rows[0]["caretaker_rows"], 1)
        self.assertEqual(rows[0]["child_scoring_rows"], 1)
        self.assertEqual(rows[0]["caretaker_scoring_rows"], 1)

    def test_filter_child_scoring_files_drops_rows_without_all_baselines(self):
        with tempfile.TemporaryDirectory() as tmp:
            child_dir = Path(tmp) / "ToySet" / "Ada"
            rows = [
                {
                    "dataset": "ToySet",
                    "child_id": "Ada",
                    "source_group": "ToySet",
                    "session_id": "1",
                    "age_months": "7",
                    "file": "session1.cha",
                    "line_no": "10",
                    "utt_id": "1",
                    "context_k1": "want some.",
                    "context_k2": "want some.",
                    "context_k3": "want some.",
                    "chi_utterance_clean": "more milk.",
                    "random_model_utterance_bin6": "milk more.",
                    "unigram_model_utterance_bin6": "more more.",
                    "bigram_model_utterance_bin6": "more milk.",
                    "trigram_model_utterance_bin6": "more milk.",
                },
                {
                    "dataset": "ToySet",
                    "child_id": "Ada",
                    "source_group": "ToySet",
                    "session_id": "1",
                    "age_months": "",
                    "file": "session1.cha",
                    "line_no": "12",
                    "utt_id": "2",
                    "context_k1": "want some.",
                    "context_k2": "want some.",
                    "context_k3": "want some.",
                    "chi_utterance_clean": "again.",
                    "random_model_utterance_bin6": "",
                    "unigram_model_utterance_bin6": "",
                    "bigram_model_utterance_bin6": "",
                    "trigram_model_utterance_bin6": "",
                },
            ]
            write_csv(
                child_dir / "chi.surprisal_scoring.csv",
                rows,
                fieldnames=[
                    "dataset",
                    "child_id",
                    "source_group",
                    "session_id",
                    "age_months",
                    "file",
                    "line_no",
                    "utt_id",
                    "context_k1",
                    "context_k2",
                    "context_k3",
                    "chi_utterance_clean",
                    *CHILD_BASELINE_COLUMNS,
                ],
            )
            unit = ChildUnit(
                dataset="ToySet",
                child="Ada",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )

            dropped = filter_child_scoring_files_for_complete_baselines([unit])
            with (child_dir / "chi.surprisal_scoring.csv").open(newline="", encoding="utf-8") as handle:
                kept = list(csv.DictReader(handle))

        self.assertEqual(dropped, 1)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["line_no"], "10")

    def test_create_big_cleaned_dataset_builds_generated_context_and_scoring_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "preprocessed"
            output = root / "big_cleaned"
            write_grouping(root / "groups.csv")
            child_row, caretaker_row = stage0_rows()
            write_csv(source / "ToySet" / "Ada" / "chi.csv", [child_row])
            write_csv(source / "ToySet" / "Ada" / "caretakers.csv", [caretaker_row])

            rows = create_big_cleaned_dataset(
                source_data_dir=source,
                output_root=output,
                grouping_csv=root / "groups.csv",
                selection="default_naturalistic",
                bin_months=6,
                ks=[1, 2, 3],
                min_age_months=0,
                max_age_months=24,
                seed=1,
            )

            child_dir = output / "preprocessed_data" / "ToySet" / "Ada"
            with (child_dir / "chi.surprisal_scoring.csv").open(newline="", encoding="utf-8") as handle:
                child_scoring = list(csv.DictReader(handle))
            with (child_dir / "caretakers.surprisal_scoring.csv").open(newline="", encoding="utf-8") as handle:
                caretaker_scoring = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["scoring_ready"], 1)
            self.assertTrue((output / "age_ngram_dicts" / "bin6" / "bin_006-011" / "vocab.txt").exists())
            self.assertEqual(child_scoring[0]["chi_utterance_clean"], "more milk.")
        self.assertEqual(child_scoring[0]["context_k1"], "want some.")
        self.assertTrue(child_scoring[0]["random_model_utterance_bin6"])
        self.assertEqual(caretaker_scoring[0]["caretaker_utterance_clean"], "want some.")

    def test_create_big_cleaned_dataset_can_use_threshold_early_bins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "preprocessed"
            output = root / "big_cleaned"
            write_grouping(root / "groups.csv")
            child_row, caretaker_row = stage0_rows()
            write_csv(source / "ToySet" / "Ada" / "chi.csv", [child_row])
            write_csv(source / "ToySet" / "Ada" / "caretakers.csv", [caretaker_row])

            create_big_cleaned_dataset(
                source_data_dir=source,
                output_root=output,
                grouping_csv=root / "groups.csv",
                selection="default_naturalistic",
                bin_months=6,
                binning_strategy="threshold_early_20k",
                early_threshold=20_000,
                ks=[1, 2, 3],
                min_age_months=0,
                max_age_months=24,
                seed=1,
            )

            self.assertTrue((output / "age_ngram_dicts" / "custom_early_20000" / "age_bins.json").exists())
            self.assertTrue((output / "age_ngram_dicts" / "custom_early_20000" / "bin_006-023").exists())

    def test_create_big_cleaned_dataset_can_use_merged_006_023_bins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "preprocessed"
            output = root / "big_cleaned"
            write_grouping(root / "groups.csv")
            child_row, caretaker_row = stage0_rows()
            write_csv(
                source / "ToySet" / "Ada" / "chi.csv",
                [dict(child_row, age_months="7"), dict(child_row, age_months="24", line_no="20", utt_id="3")],
            )
            write_csv(source / "ToySet" / "Ada" / "caretakers.csv", [caretaker_row])

            create_big_cleaned_dataset(
                source_data_dir=source,
                output_root=output,
                grouping_csv=root / "groups.csv",
                selection="default_naturalistic",
                bin_months=6,
                binning_strategy="merged_early_006_023",
                ks=[1, 2, 3],
                min_age_months=0,
                max_age_months=24,
                seed=1,
            )

            self.assertTrue((output / "age_ngram_dicts" / "merged_early_006_023" / "age_bins.json").exists())
            self.assertTrue((output / "age_ngram_dicts" / "merged_early_006_023" / "bin_006-023").exists())
            self.assertTrue((output / "age_ngram_dicts" / "merged_early_006_023" / "bin_024-029").exists())


if __name__ == "__main__":
    unittest.main()
