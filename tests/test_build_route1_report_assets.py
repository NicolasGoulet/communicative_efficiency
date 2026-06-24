import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_route1_report_assets import (
    age_to_route1_bin,
    build_summary_tables,
    dataframe_to_markdown,
    resolve_age_months,
    route1_age_bins,
    validate_complete_age_coverage,
)
from render_markdown_report import markdown_to_html


class TestRoute1ReportAssets(unittest.TestCase):
    def test_route1_age_bins_start_with_merged_early_bin(self):
        labels = [age_bin.label for age_bin in route1_age_bins()]

        self.assertEqual(
            labels,
            [
                "006-023",
                "024-029",
                "030-035",
                "036-041",
                "042-047",
                "048-053",
                "054-059",
                "060-065",
            ],
        )

    def test_age_to_route1_bin_uses_half_open_boundaries(self):
        self.assertEqual(age_to_route1_bin(6), "006-023")
        self.assertEqual(age_to_route1_bin(23.999), "006-023")
        self.assertEqual(age_to_route1_bin(24), "024-029")
        self.assertEqual(age_to_route1_bin(29.999), "024-029")
        self.assertEqual(age_to_route1_bin(60), "060-065")
        self.assertEqual(age_to_route1_bin(65.999), "060-065")
        self.assertIsNone(age_to_route1_bin(5.999))
        self.assertIsNone(age_to_route1_bin(66))
        self.assertIsNone(age_to_route1_bin(""))

    def test_resolve_age_months_falls_back_to_filename_age(self):
        self.assertEqual(resolve_age_months("", "Naima/030000.cha"), (36.0, "filename_age"))
        self.assertEqual(resolve_age_months("24.5", "Naima/030000.cha"), (24.5, "scored_age_months"))
        self.assertEqual(resolve_age_months("", "Naima/noage.cha"), (None, "missing"))

    def test_build_summary_tables_counts_child_and_caretaker_k0_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "WITHOUT_context" / "k0" / "model" / "ToySet" / "Ada"
            base.mkdir(parents=True)
            self.write_csv(
                base / "chi.surprisal_scoring__real.scored.csv",
                [
                    {"dataset": "ToySet", "child_id": "Ada", "session_id": "s1", "age_months": "23.9", "file": "a.cha", "utt_id": "c1"},
                    {"dataset": "ToySet", "child_id": "Ada", "session_id": "s2", "age_months": "24", "file": "b.cha", "utt_id": "c2"},
                    {"dataset": "ToySet", "child_id": "Ada", "session_id": "s3", "age_months": "", "file": "Ada/030000.cha", "utt_id": "c3"},
                ],
            )
            self.write_csv(
                base / "caretakers.surprisal_scoring__caretaker.scored.csv",
                [
                    {"dataset": "ToySet", "child_id": "Ada", "session_id": "s1", "age_months": "23.9", "file": "a.cha", "utt_id": "p1"},
                    {"dataset": "ToySet", "child_id": "Ada", "session_id": "s1", "age_months": "23.9", "file": "a.cha", "utt_id": "p2"},
                ],
            )

            tables = build_summary_tables(root)

        dataset_summary = tables["dataset_summary"]
        self.assertEqual(dataset_summary.loc[0, "children"], 1)
        self.assertEqual(dataset_summary.loc[0, "child_utterances"], 3)
        self.assertEqual(dataset_summary.loc[0, "caretaker_utterances"], 2)

        coverage = tables["coverage_audit"].set_index("role")
        self.assertEqual(coverage.loc["child", "raw_k0_scored_rows"], 3)
        self.assertEqual(coverage.loc["child", "age_binned_rows"], 3)
        self.assertEqual(coverage.loc["child", "filename_recovered_age_rows"], 1)
        self.assertEqual(coverage.loc["child", "missing_age_after_recovery"], 0)
        self.assertEqual(coverage.loc["child", "outside_route1_age_bins"], 0)
        self.assertEqual(coverage.loc["caretaker", "raw_k0_scored_rows"], 2)
        self.assertEqual(coverage.loc["caretaker", "missing_age_after_recovery"], 0)
        self.assertEqual(coverage.loc["caretaker", "outside_route1_age_bins"], 0)

        age_counts = tables["age_role_counts"]
        child_counts = dict(
            zip(
                age_counts[age_counts["role"] == "child"]["age_bin"],
                age_counts[age_counts["role"] == "child"]["n_utterances"],
            )
        )
        caretaker_counts = dict(
            zip(
                age_counts[age_counts["role"] == "caretaker"]["age_bin"],
                age_counts[age_counts["role"] == "caretaker"]["n_utterances"],
            )
        )
        self.assertEqual(child_counts["006-023"], 1)
        self.assertEqual(child_counts["024-029"], 1)
        self.assertEqual(child_counts["036-041"], 1)
        self.assertEqual(caretaker_counts["006-023"], 2)
        self.assertEqual(caretaker_counts["024-029"], 0)

    def test_dataframe_to_markdown_has_plain_table_shape(self):
        import pandas as pd

        rendered = dataframe_to_markdown(pd.DataFrame([{"A": "x", "B": 2}]))

        self.assertIn("| A | B |", rendered)
        self.assertIn("| x | 2 |", rendered)

    def test_validate_complete_age_coverage_raises_on_row_loss(self):
        import pandas as pd

        audit = pd.DataFrame(
            [
                {
                    "role": "child",
                    "raw_k0_scored_rows": 10,
                    "age_binned_rows": 9,
                    "missing_age_after_recovery": 1,
                    "outside_route1_age_bins": 0,
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "coverage is incomplete"):
            validate_complete_age_coverage(audit)

    def test_markdown_renderer_supports_report_features(self):
        rendered = markdown_to_html(
            "# Title\n\n"
            "A **bold** sentence with `code`.\n\n"
            "| A | B |\n"
            "| --- | --- |\n"
            "| x | y |\n\n"
            "![Alt](../figs/example.png)\n"
            "<div class=\"figure-grid\">\n"
            "<figure><img src=\"../figs/a.png\" alt=\"A\"></figure>\n"
            "</div>\n"
            "<table class=\"plot-layout\">\n"
            "<tr><td colspan=\"2\"><img src=\"../figs/b.png\" alt=\"B\"></td></tr>\n"
            "</table>\n"
        )

        self.assertIn("<h1>Title</h1>", rendered)
        self.assertIn("<strong>bold</strong>", rendered)
        self.assertIn("<code>code</code>", rendered)
        self.assertIn("<table>", rendered)
        self.assertIn('src="../figs/example.png"', rendered)
        self.assertIn('<div class="figure-grid">', rendered)
        self.assertIn('<figure><img src="../figs/a.png" alt="A"></figure>', rendered)
        self.assertIn('<table class="plot-layout">', rendered)
        self.assertIn('<tr><td colspan="2"><img src="../figs/b.png" alt="B"></td></tr>', rendered)

    @staticmethod
    def write_csv(path: Path, rows):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["dataset", "child_id", "session_id", "age_months", "file", "utt_id"],
            )
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
