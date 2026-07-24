import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_paired_child_trajectory_overlays import build_pair, run_overlays


def trajectory_fixture(offset: float = 0.0) -> pd.DataFrame:
    rows = []
    for dataset, child in [("Brown", "Adam"), ("Providence", "Alex")]:
        for age in [18.0, 24.0, 30.0]:
            rows.append(
                {
                    "scope": "pbm_discovery",
                    "scorer_id": "toy",
                    "dataset": dataset,
                    "child_id": child,
                    "child_key": f"{dataset}/{child}",
                    "session_id": str(int(age)),
                    "age_months": age,
                    "age_bin": "006-023" if age < 24 else "024-029" if age < 30 else "030-035",
                    "utterances": 100,
                    "adjusted_k3_bits_2_words": 20 - age * 0.1 + offset,
                    "adjusted_k0_bits_2_words": 22 - age * 0.12 + offset,
                    "adjusted_context_gain_k3_2_words": 2 - age * 0.02 + offset,
                }
            )
    return pd.DataFrame(rows)


class PairedChildTrajectoryOverlayTests(unittest.TestCase):
    def test_run_overlays_writes_one_profile_per_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = root / "left.csv.gz"
            right = root / "right.csv.gz"
            trajectory_fixture().to_csv(left, index=False)
            trajectory_fixture(3.0).to_csv(right, index=False)

            audit = run_overlays(
                left_trajectories=left,
                right_trajectories=right,
                output_dir=root / "output",
                fig_dir=root / "figures",
                report_md=root / "report.md",
                report_html=root / "report.html",
                left_suffix="tiny",
                right_suffix="mistral",
                left_label="Tiny",
                right_label="Mistral",
            )

            self.assertEqual(audit["join_status"], "PASS")
            self.assertEqual(audit["child_profiles"], 2)
            self.assertEqual(len(list((root / "figures").glob("*.png"))), 2)
            self.assertTrue((root / "report.html").exists())

    def test_build_pair_fails_when_session_cell_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = root / "left.csv.gz"
            right = root / "right.csv.gz"
            trajectory_fixture().to_csv(left, index=False)
            trajectory_fixture().iloc[:-1].to_csv(right, index=False)

            with self.assertRaisesRegex(ValueError, "Trajectory join failed"):
                build_pair(left, right, "tiny", "mistral")


if __name__ == "__main__":
    unittest.main()
