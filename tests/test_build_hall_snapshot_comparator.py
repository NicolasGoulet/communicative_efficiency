from __future__ import annotations

import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from src.build_hall_snapshot_comparator import build_snapshot_comparator


def write_csv(path: Path, rows: list[dict[str, object]], *, compressed: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if compressed else open
    with opener(path, "wt", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class HallSnapshotComparatorTests(unittest.TestCase):
    def test_selects_one_outcome_blind_nearest_age_session_per_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            hall = root / "hall.csv"
            trajectories = root / "trajectory.csv.gz"
            output = root / "selection.csv"
            audit_path = root / "audit.json"
            write_csv(
                hall,
                [
                    {"child_id": "h1", "age_months": 57, "primary_eligible": 1},
                    {"child_id": "h2", "age_months": 54, "primary_eligible": 1},
                    {"child_id": "h4", "age_months": 57, "primary_eligible": 1},
                    {"child_id": "h3", "age_months": 60, "primary_eligible": 0},
                ],
            )
            rows = [
                {"role": "child", "scope": "pbm_discovery", "dataset": "A", "child_id": "one", "child_key": "A/one", "session_id": "s1", "age_months": 55, "age_bin": "054-059", "utterances": 10},
                {"role": "child", "scope": "pbm_discovery", "dataset": "A", "child_id": "one", "child_key": "A/one", "session_id": "s2", "age_months": 57, "age_bin": "054-059", "utterances": 8},
                {"role": "child", "scope": "pbm_discovery", "dataset": "A", "child_id": "one", "child_key": "A/one", "session_id": "s2", "age_months": 57, "age_bin": "054-059", "utterances": 7},
                {"role": "child", "scope": "pbm_discovery", "dataset": "A", "child_id": "one", "child_key": "A/one", "session_id": "s3", "age_months": 57, "age_bin": "054-059", "utterances": 100},
                {"role": "child", "scope": "non_pbm_confirmation", "dataset": "B", "child_id": "two", "child_key": "B/two", "session_id": "s9", "age_months": 59, "age_bin": "054-059", "utterances": 11},
                {"role": "child", "scope": "non_pbm_confirmation", "dataset": "B", "child_id": "two", "child_key": "B/two", "session_id": "old", "age_months": 53, "age_bin": "048-053", "utterances": 100},
                {"role": "child", "scope": "all79_descriptive", "dataset": "A", "child_id": "one", "child_key": "A/one", "session_id": "s2", "age_months": 57, "age_bin": "054-059", "utterances": 15},
                {"role": "caretaker", "scope": "pbm_discovery", "dataset": "A", "child_id": "adult", "child_key": "A/adult", "session_id": "s1", "age_months": 57, "age_bin": "054-059", "utterances": 99},
            ]
            write_csv(trajectories, rows, compressed=True)

            audit = build_snapshot_comparator(
                hall_metadata=hall,
                trajectory_input=trajectories,
                output_csv=output,
                audit_json=audit_path,
            )

            with output.open(newline="", encoding="utf-8") as handle:
                selected = list(csv.DictReader(handle))
            saved = json.loads(audit_path.read_text(encoding="utf-8"))

        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(saved, audit)
        self.assertEqual(audit["hall_primary_target_age_months"], 57.0)
        self.assertEqual(len(selected), 2)
        by_child = {row["child_key"]: row for row in selected}
        self.assertEqual(by_child["A/one"]["session_id"], "s2")
        self.assertEqual(by_child["A/one"]["utterances"], "15")
        self.assertEqual(by_child["B/two"]["session_id"], "s9")
        self.assertEqual(by_child["B/two"]["distance_from_target_months"], "2.0")


if __name__ == "__main__":
    unittest.main()
