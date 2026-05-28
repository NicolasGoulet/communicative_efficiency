import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from plot_diagnostic_analyses import (  # noqa: E402
    DEFAULT_AGE_BIN_MONTHS,
    aggregate_group_summary,
    make_dataset_summary,
    phenomenon_age_summary_from_frames,
    plot_age_bin_denominators,
    plot_combined_age_denominator_and_rates,
)


class TestPlotDiagnosticAnalyses(unittest.TestCase):
    def test_aggregate_group_summary_computes_rates(self):
        special = pd.DataFrame(
            [
                {
                    "dataset": "Toy",
                    "speaker_group": "CHILD",
                    "total_usable_utterances": 100,
                    "utterances_with_target_special_form": 10,
                    "target_special_form_token_occurrences": 12,
                }
            ]
        )
        fillers = pd.DataFrame(
            [
                {
                    "dataset": "Toy",
                    "speaker_group": "CHILD",
                    "total_usable_utterances": 100,
                    "utterances_with_filler": 20,
                    "filler_token_occurrences": 25,
                }
            ]
        )
        shortenings = pd.DataFrame(
            [
                {
                    "dataset": "Toy",
                    "speaker_group": "CHILD",
                    "total_usable_utterances": 100,
                    "utterances_with_shortening": 5,
                    "shortening_token_occurrences": 6,
                }
            ]
        )

        summary = aggregate_group_summary(special, fillers, shortenings)

        rates = dict(zip(summary["phenomenon"], summary["utterance_rate"]))
        self.assertEqual(rates["Special forms"], 0.10)
        self.assertEqual(rates["Fillers"], 0.20)
        self.assertEqual(rates["Shortenings"], 0.05)

    def test_make_dataset_summary_preserves_dataset_split(self):
        special = pd.DataFrame(
            [
                {
                    "dataset": "ToyA",
                    "speaker_group": "CHILD",
                    "total_usable_utterances": 100,
                    "utterances_with_target_special_form": 10,
                    "target_special_form_token_occurrences": 12,
                },
                {
                    "dataset": "ToyB",
                    "speaker_group": "CARETAKERS",
                    "total_usable_utterances": 50,
                    "utterances_with_target_special_form": 5,
                    "target_special_form_token_occurrences": 9,
                },
            ]
        )
        fillers = pd.DataFrame(
            [
                {
                    "dataset": "ToyA",
                    "speaker_group": "CHILD",
                    "total_usable_utterances": 100,
                    "utterances_with_filler": 20,
                    "filler_token_occurrences": 25,
                }
            ]
        )
        shortenings = pd.DataFrame(
            [
                {
                    "dataset": "ToyA",
                    "speaker_group": "CHILD",
                    "total_usable_utterances": 100,
                    "utterances_with_shortening": 5,
                    "shortening_token_occurrences": 6,
                }
            ]
        )

        summary = make_dataset_summary(special, fillers, shortenings)

        special_rows = summary[summary["phenomenon"] == "Special forms"]
        self.assertEqual(set(special_rows["dataset"]), {"ToyA", "ToyB"})
        self.assertIn("utterance_rate", summary.columns)

    def test_phenomenon_age_summary_from_frames_uses_per_utterance_denominators(self):
        special_rows = pd.DataFrame(
            [
                {"speaker_group": "CHILD", "age_bin": "24_30", "has_target_special_form": 1},
                {"speaker_group": "CHILD", "age_bin": "24_30", "has_target_special_form": 0},
                {"speaker_group": "CARETAKERS", "age_bin": "24_30", "has_target_special_form": 0},
            ]
        )
        filler_rows = pd.DataFrame(
            [
                {"speaker_group": "CHILD", "age_bin": "24_30", "has_filler": 1},
                {"speaker_group": "CHILD", "age_bin": "24_30", "has_filler": 1},
                {"speaker_group": "CARETAKERS", "age_bin": "24_30", "has_filler": 0},
            ]
        )
        shortening_rows = pd.DataFrame(
            [
                {"speaker_group": "CHILD", "age_bin": "24_30", "has_shortening": 0},
                {"speaker_group": "CHILD", "age_bin": "24_30", "has_shortening": 1},
                {"speaker_group": "CARETAKERS", "age_bin": "24_30", "has_shortening": 1},
            ]
        )

        summary = phenomenon_age_summary_from_frames(special_rows, filler_rows, shortening_rows)

        child_special = summary[
            (summary["speaker_group"] == "CHILD")
            & (summary["phenomenon"] == "Special forms")
        ].iloc[0]
        child_fillers = summary[
            (summary["speaker_group"] == "CHILD")
            & (summary["phenomenon"] == "Fillers")
        ].iloc[0]
        self.assertEqual(child_special["total_usable_utterances"], 2)
        self.assertEqual(child_special["utterance_rate"], 0.5)
        self.assertEqual(child_fillers["utterance_rate"], 1.0)

    def test_default_age_bins_are_six_months(self):
        self.assertEqual(DEFAULT_AGE_BIN_MONTHS, 6)

    def test_plot_age_bin_denominators_writes_png_and_pdf(self):
        summary = pd.DataFrame(
            [
                {
                    "speaker_group": "CHILD",
                    "age_bin": "24_30",
                    "age_mid": 27.0,
                    "total_usable_utterances": 10,
                    "phenomenon": "Special forms",
                },
                {
                    "speaker_group": "CARETAKERS",
                    "age_bin": "24_30",
                    "age_mid": 27.0,
                    "total_usable_utterances": 20,
                    "phenomenon": "Special forms",
                },
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            plot_age_bin_denominators(summary, out_dir)

            self.assertTrue((out_dir / "age_bin_scorable_utterance_counts.png").exists())
            self.assertTrue((out_dir / "age_bin_scorable_utterance_counts.pdf").exists())

    def test_plot_combined_age_denominator_and_rates_writes_png_and_pdf(self):
        summary = pd.DataFrame(
            [
                {
                    "speaker_group": group,
                    "age_bin": "24_30",
                    "age_mid": 27.0,
                    "total_usable_utterances": 10,
                    "utterances_with_phenomenon": 2,
                    "phenomenon": phenomenon,
                    "utterance_rate": 0.2,
                }
                for group in ("CHILD", "CARETAKERS")
                for phenomenon in ("Special forms", "Fillers", "Shortenings")
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            plot_combined_age_denominator_and_rates(summary, out_dir)

            self.assertTrue((out_dir / "age_bin_counts_and_phenomenon_rates.png").exists())
            self.assertTrue((out_dir / "age_bin_counts_and_phenomenon_rates.pdf").exists())


if __name__ == "__main__":
    unittest.main()
