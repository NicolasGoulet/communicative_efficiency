from __future__ import annotations

import csv
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from build_cross_population_scoring_handoff import build_handoff, clean_cell  # noqa: E402


FIELDS = [
    "dataset", "child_id", "source_group", "session_id", "age_raw", "age_months", "sex",
    "file", "line_no", "reference_line", "utt_id", "utt_id_role", "speaker", "utterance",
    "utterance_clean", "cleaned_is_empty",
]


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class CrossPopulationHandoffTests(unittest.TestCase):
    def test_missing_scalar_is_not_serialized_as_nan_target_text(self) -> None:
        self.assertEqual(clean_cell(float("nan")), "")
        self.assertEqual(clean_cell(None), "")
        self.assertEqual(clean_cell("nan"), "nan")
        self.assertEqual(clean_cell(" child words "), "child words")

    def test_builds_labelled_contexts_and_reuse_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared = root / "data/preprocessed_data/Toy/al"
            common = {
                "dataset": "Toy", "child_id": "al", "source_group": "Toy", "session_id": 1,
                "age_raw": "2;00.", "age_months": 24, "sex": "female", "file": "al.cha",
                "cleaned_is_empty": 0,
            }
            write_rows(
                prepared / "chi.csv",
                [{**common, "line_no": 20, "reference_line": "al.cha:20", "utt_id": 1,
                  "utt_id_role": 1, "speaker": "CHI", "utterance": "ball .", "utterance_clean": "ball."}],
            )
            write_rows(
                prepared / "caretakers.csv",
                [
                    {**common, "line_no": 10, "reference_line": "al.cha:10", "utt_id": 1,
                     "utt_id_role": 1, "speaker": "MOT", "utterance": "look .", "utterance_clean": "look."},
                    {**common, "line_no": 15, "reference_line": "al.cha:15", "utt_id": 2,
                     "utt_id_role": 2, "speaker": "MOT", "utterance": "a ball .", "utterance_clean": "a ball."},
                ],
            )
            metadata = root / "results/metadata"
            metadata.mkdir(parents=True)
            (metadata / "clinical_child_metadata_summary.csv").write_text(
                "clinical_dataset,child_id,clinical_group,clinical_status,is_control\n", encoding="utf-8"
            )
            hall_dir = root / "results/hall_snapshot_preprocessing"
            hall_dir.mkdir(parents=True)
            hall_fields = [
                "dataset", "child_id", "source_group", "age_raw", "age_months", "sex", "file", "line_no",
                "utterance_id", "context_k1", "context_k2", "context_k3", "chi_utterance_clean",
                "primary_eligible", "sensitivity_eligible", "race", "social_class", "setting_auto",
            ]
            with (hall_dir / "hall_child_snapshot_scoring.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=hall_fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "dataset": "Hall", "child_id": "ha", "source_group": "group", "age_raw": "4;09.",
                        "age_months": 57, "sex": "male", "file": "ha.cha", "line_no": 9,
                        "utterance_id": "hall-id", "context_k1": "hi.", "context_k2": "hi.",
                        "context_k3": "hi.", "chi_utterance_clean": "hello.", "primary_eligible": 1,
                        "sensitivity_eligible": 1, "race": "x", "social_class": "y", "setting_auto": "home",
                    }
                )
            config = {
                "schema_version": 1,
                "package_id": "toy_package",
                "contexts": ["k0", "k1", "k2", "k3"],
                "models": [{"model_key": "toy-model", "model_id": "toy/model"}],
                "collections": [
                    {
                        "collection_id": "toy_collection", "prepared_root": "data/preprocessed_data",
                        "analysis_group": "naturalistic_caregiver_child", "population_class": "nonclinical",
                        "speech_setting": "naturalistic", "expected_children": 1, "datasets": ["Toy"],
                    }
                ],
                "hall": {
                    "collection_id": "hall", "analysis_group": "snapshot", "population_class": "nonclinical",
                    "speech_setting": "multi_setting", "input_csv":
                    "results/hall_snapshot_preprocessing/hall_child_snapshot_scoring.csv",
                    "expected_children": 1, "expected_primary_children": 1, "expected_rows": 1,
                },
                "reuse": [{"models": ["toy-model"], "datasets": ["Hall"]}],
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output = root / "output"

            summary = build_handoff(
                config_path=config_path,
                output_dir=output,
                project_root=root,
                build_archive=False,
            )
            with gzip.open(output / "inputs/Toy.child_scoring.csv.gz", "rt", newline="", encoding="utf-8") as handle:
                [toy] = list(csv.DictReader(handle))
            with (output / "model_scoring_plan.csv").open(newline="", encoding="utf-8") as handle:
                plan = list(csv.DictReader(handle))

        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["children"], 2)
        self.assertEqual(toy["context_k1"], "a ball.")
        self.assertEqual(toy["context_k2"], "look. a ball.")
        self.assertEqual({row["dataset"]: row["action"] for row in plan}, {"Toy": "SCORE_PENDING", "Hall": "REUSE_AUDITED"})


if __name__ == "__main__":
    unittest.main()
