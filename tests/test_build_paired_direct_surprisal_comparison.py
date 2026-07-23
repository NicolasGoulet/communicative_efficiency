import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_direct_surprisal_model_suite import READ_COLUMNS
from src.build_paired_direct_surprisal_comparison import build_pair, run_comparison
from tests.test_build_direct_surprisal_model_suite import toy_wide_rows


def paired_fixture(scorer_id: str, score_multiplier: float = 1.0) -> pd.DataFrame:
    frame = toy_wide_rows().copy()
    frame["scorer_id"] = scorer_id
    frame["file"] = frame["session_id"].map(lambda value: f"session_{value}.cha")
    frame["line_no"] = frame.groupby("file").cumcount().astype(str)
    frame["utt_id"] = frame["utterance_id"]
    for column in ["context_k1", "context_k2", "context_k3"]:
        frame[f"{column}_sha256"] = f"shared-{column}"
    for mode in ["real", "random", "unigram", "bigram", "trigram"]:
        frame[f"{mode}_target_text_sha256"] = frame["utterance_id"].map(
            lambda value: f"{mode}-{value}"
        )
    for column in frame.columns:
        if column in READ_COLUMNS and (
            column.endswith("sum_bits")
            or "context_gain" in column
            or "minus_real" in column
        ):
            frame[column] = pd.to_numeric(frame[column]) * score_multiplier
    return frame


class PairedDirectSurprisalComparisonTests(unittest.TestCase):
    def test_run_comparison_requires_exact_identity_and_writes_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left_path = root / "left.csv.gz"
            right_path = root / "right.csv.gz"
            paired_fixture("tiny", 0.5).to_csv(left_path, index=False)
            paired_fixture("mistral", 1.0).to_csv(right_path, index=False)

            audit = run_comparison(
                left_path=left_path,
                right_path=right_path,
                output_dir=root / "output",
                report_md=root / "report.md",
                report_html=root / "report.html",
                left_suffix="tiny",
                right_suffix="mistral",
                bootstrap_reps=2,
                bootstrap_seed=77,
            )

            self.assertEqual(audit["join_status"], "PASS")
            self.assertEqual(audit["join_mismatches"], 0)
            slopes = pd.read_csv(root / "output" / "paired_slope_bootstrap_summary.csv")
            self.assertEqual(len(slopes), 3)
            self.assertTrue((slopes["successful_reps"] == 2).all())
            correlations = pd.read_csv(root / "output" / "paired_correlations.csv")
            overall = correlations[correlations["scope"].eq("all_pbm")]
            self.assertTrue((overall["pearson"].round(8) == 1.0).all())

    def test_build_pair_records_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left_path = root / "left.csv.gz"
            right_path = root / "right.csv.gz"
            left = paired_fixture("tiny")
            right = paired_fixture("mistral")
            right.loc[right.index[0], "real_target_text_sha256"] = "changed"
            left.to_csv(left_path, index=False)
            right.to_csv(right_path, index=False)

            _, mismatches, _, _ = build_pair(
                left_path,
                right_path,
                left_suffix="tiny",
                right_suffix="mistral",
            )

            self.assertEqual(len(mismatches), 1)
            self.assertEqual(mismatches.iloc[0]["field"], "real_target_text_sha256")


if __name__ == "__main__":
    unittest.main()
