import math
import sys
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_route1_portelance_xu_extension_suite import (  # noqa: E402
    balanced_sample,
    feature_status_table,
    question_type,
    weighted_partial_age_slope,
)


class PortelanceXuExtensionSuiteTests(unittest.TestCase):
    def test_question_type_detects_wh_and_yes_no_questions(self):
        self.assertEqual(question_type("what is that?"), "wh_what")
        self.assertEqual(question_type("how does it go?"), "wh_how")
        self.assertEqual(question_type("do you want milk?"), "yes_no_question")
        self.assertEqual(question_type("look at this."), "statement_or_fragment")

    def test_balanced_sample_caps_each_group(self):
        frame = pd.DataFrame(
            {
                "group": ["a"] * 5 + ["b"] * 2,
                "value": list(range(7)),
            }
        )

        out = balanced_sample(frame, group_cols=["group"], max_per_group=3, seed=1)

        counts = out.groupby("group").size().to_dict()
        self.assertEqual(counts["a"], 3)
        self.assertEqual(counts["b"], 2)

    def test_weighted_partial_age_slope_recovers_downward_signal(self):
        rows = []
        for child in ["c1", "c2"]:
            for age_mid in [10.0, 20.0, 30.0]:
                for effort in [1, 2, 3]:
                    rows.append(
                        {
                            "child_id": child,
                            "age_mid": age_mid,
                            "effort_value": effort,
                            "n": 10,
                            "sum_bits_k3": 50 - 0.5 * age_mid + 2 * effort,
                        }
                    )
        frame = pd.DataFrame(rows)

        slope = weighted_partial_age_slope(frame, "sum_bits_k3")

        self.assertTrue(math.isfinite(slope))
        self.assertLess(slope, 0)

    def test_feature_status_table_lists_unfinished_full_entropy(self):
        table = feature_status_table()

        self.assertIn("Full response-space entropy", set(table["feature"]))
        row = table[table["feature"].eq("Full response-space entropy")].iloc[0]
        self.assertIn("pilot", row["status"])


if __name__ == "__main__":
    unittest.main()
