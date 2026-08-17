from __future__ import annotations

import csv
import hashlib
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from src.build_hall_mila_handoff import build_hall_mila_handoff


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class HallMilaHandoffTests(unittest.TestCase):
    def test_builds_deterministic_audited_four_context_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "source"
            output_one = root / "one"
            output_two = root / "two"
            scoring = source / "hall_child_snapshot_scoring.csv"
            metadata = source / "hall_child_metadata.csv"
            inventory = source / "hall_file_inventory.csv"
            preprocessing_audit = source / "hall_preprocessing_audit.json"
            comparator = source / "hall_comparison_snapshot_manifest.csv"
            comparator_audit = source / "hall_comparison_snapshot_audit.json"

            write_csv(
                scoring,
                [
                    {
                        "dataset": "Hall", "child_id": "ali", "source_group": "BlackPro",
                        "race": "Black", "social_class": "UC", "stratum": "Black_UC",
                        "demographic_source": "chi_id", "primary_eligible": 1,
                        "sensitivity_eligible": 1, "age_raw": "4;09.", "age_months": 57,
                        "sex": "female", "file": "BlackPro/ali.cha", "line_no": 10,
                        "utterance_id": "Hall|ali|10", "situation_id": 1,
                        "situation_text": "home", "setting_auto": "home",
                        "setting_review_required": 0, "previous_main_speaker": "MOT",
                        "previous_main_role_group": "adult_interlocutor", "child_after_adult": 1,
                        "context_k1": "hello.", "context_k2": "hello.",
                        "context_k3": "hello.", "chi_utterance_clean": "hi.",
                        "nb_words": 1, "nb_characters": 3,
                    },
                    {
                        "dataset": "Hall", "child_id": "rog", "source_group": "BlackWork",
                        "race": "Black", "social_class": "WC", "stratum": "Black_WC",
                        "demographic_source": "source_group_inferred", "primary_eligible": 0,
                        "sensitivity_eligible": 1, "age_raw": "4;09.", "age_months": 57,
                        "sex": "male", "file": "BlackWork/rog.cha", "line_no": 20,
                        "utterance_id": "Hall|rog|20", "situation_id": 1,
                        "situation_text": "school", "setting_auto": "school",
                        "setting_review_required": 0, "previous_main_speaker": "MCH",
                        "previous_main_role_group": "child_peer", "child_after_adult": 0,
                        "context_k1": "", "context_k2": "", "context_k3": "",
                        "chi_utterance_clean": "ball.", "nb_words": 1, "nb_characters": 5,
                    },
                ],
            )
            write_csv(metadata, [{"child_id": "ali"}, {"child_id": "rog"}])
            write_csv(inventory, [{"child_id": "ali"}, {"child_id": "rog"}])
            write_csv(comparator, [{"child_key": "Brown/Adam", "session_id": 1}])
            preprocessing_audit.write_text(
                json.dumps({"status": "PASS", "counts": {"files": 2, "main_tier_rows": 4}}),
                encoding="utf-8",
            )
            comparator_audit.write_text(
                json.dumps({"status": "PASS", "selected_children": 1}), encoding="utf-8"
            )
            sources = {
                "scoring": scoring,
                "metadata": metadata,
                "inventory": inventory,
                "preprocessing_audit": preprocessing_audit,
                "comparator": comparator,
                "comparator_audit": comparator_audit,
            }
            expected = {
                "source_files": 2,
                "main_tier_rows": 4,
                "scoring_rows": 2,
                "primary_rows": 1,
                "children": 2,
                "primary_children": 1,
                "sensitivity_children": 2,
                "child_after_adult_rows": 1,
                "rows_with_context": 1,
                "comparator_children": 1,
            }

            first = build_hall_mila_handoff(
                sources=sources,
                output_dir=output_one,
                expected_counts=expected,
                package_id="toy_hall_v1",
            )
            second = build_hall_mila_handoff(
                sources=sources,
                output_dir=output_two,
                expected_counts=expected,
                package_id="toy_hall_v1",
            )

            archive_one = Path(first["archive_path"])
            archive_two = Path(second["archive_path"])
            digest_one = hashlib.sha256(archive_one.read_bytes()).hexdigest()
            digest_two = hashlib.sha256(archive_two.read_bytes()).hexdigest()
            with tarfile.open(archive_one, "r:gz") as bundle:
                names = sorted(bundle.getnames())
                contracts = list(
                    csv.DictReader(
                        line.decode("utf-8")
                        for line in bundle.extractfile(
                            "toy_hall_v1/contracts/scoring_contracts.csv"
                        ).readlines()
                    )
                )
                manifest = json.load(
                    bundle.extractfile("toy_hall_v1/handoff_manifest.json")
                )

        self.assertEqual(first["status"], "PASS")
        self.assertEqual(second["status"], "PASS")
        self.assertEqual(digest_one, digest_two)
        self.assertEqual(first["archive_sha256"], digest_one)
        self.assertIn("toy_hall_v1/inputs/hall_child_snapshot_scoring.csv", names)
        self.assertIn("toy_hall_v1/contracts/scoring_contracts.csv", names)
        self.assertEqual([row["context_id"] for row in contracts], ["k0", "k1", "k2", "k3"])
        self.assertEqual(contracts[0]["context_column"], "")
        self.assertEqual(contracts[-1]["context_column"], "context_k3")
        self.assertEqual(manifest["expected_scored_rows"], 8)
        self.assertEqual(manifest["input_audit"]["blank_targets"], 0)
        self.assertEqual(manifest["input_audit"]["duplicate_utterance_ids"], 0)


if __name__ == "__main__":
    unittest.main()
