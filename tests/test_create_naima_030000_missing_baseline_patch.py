import json
import tempfile
from pathlib import Path
import unittest

import pandas as pd

from src.create_naima_030000_missing_baseline_patch import (
    BASELINE_COLUMNS,
    build_patch_dataframe,
)


class Naima030000MissingBaselinePatchTests(unittest.TestCase):
    def _write_minimal_dict_root(self, root: Path) -> None:
        (root / "bin_036-041").mkdir(parents=True)
        (root / "age_bins.json").write_text(
            json.dumps({"bins": [{"start": 36, "end": 41}]}),
            encoding="utf-8",
        )
        (root / "bin_036-041" / "vocab.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
        (root / "bin_036-041" / "unigram_counts.json").write_text(
            json.dumps({"alpha": 5, "beta": 3, "gamma": 1}),
            encoding="utf-8",
        )
        (root / "bin_036-041" / "bigram_probs.json").write_text(
            json.dumps({"fireflies": {"alpha": 1.0}, "alpha": {"beta": 1.0}}),
            encoding="utf-8",
        )
        (root / "bin_036-041" / "trigram_probs.json").write_text(
            json.dumps({"many": {"fireflies": {"gamma": 1.0}}, "fireflies": {"gamma": {"beta": 1.0}}}),
            encoding="utf-8",
        )

    def _write_scored_real_file(self, path: Path) -> None:
        frame = pd.DataFrame(
            [
                {
                    "dataset": "Providence",
                    "child_id": "Naima",
                    "source_group": "Providence",
                    "session_id": "83",
                    "age_months": "",
                    "file": "Naima/030000.cha",
                    "line_no": "23",
                    "utt_id": "40099",
                    "context_k1": "many fireflies.",
                    "context_k2": "we saw many fireflies.",
                    "context_k3": "outside. we saw many fireflies.",
                    "chi_utterance_clean": "no.",
                    "random_model_utterance_bin6": "",
                    "unigram_model_utterance_bin6": "",
                    "bigram_model_utterance_bin6": "",
                    "trigram_model_utterance_bin6": "",
                },
                {
                    "dataset": "Providence",
                    "child_id": "Naima",
                    "source_group": "Providence",
                    "session_id": "82",
                    "age_months": "35.9",
                    "file": "Naima/029930.cha",
                    "line_no": "9",
                    "utt_id": "39999",
                    "context_k1": "ignored.",
                    "context_k2": "ignored.",
                    "context_k3": "ignored.",
                    "chi_utterance_clean": "ignored.",
                    "random_model_utterance_bin6": "",
                    "unigram_model_utterance_bin6": "",
                    "bigram_model_utterance_bin6": "",
                    "trigram_model_utterance_bin6": "",
                },
            ]
        )
        frame.to_csv(path, index=False)

    def test_build_patch_dataframe_generates_all_four_baselines_from_filename_age(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            dict_root = tmp / "dicts"
            self._write_minimal_dict_root(dict_root)
            scored_real = tmp / "real.csv"
            self._write_scored_real_file(scored_real)

            patch, age_bin, missing_age_rows = build_patch_dataframe(
                scored_real_k0=scored_real,
                dict_root=dict_root,
                seed=7,
            )

        self.assertEqual(age_bin, "036-041")
        self.assertEqual(missing_age_rows, 1)
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch.loc[0, "age_months"], "36")
        self.assertEqual(patch.loc[0, "context_k1"], "many fireflies.")
        for column in BASELINE_COLUMNS:
            self.assertTrue(str(patch.loc[0, column]).strip(), column)
            self.assertTrue(str(patch.loc[0, column]).endswith("."), column)

        self.assertEqual(patch.loc[0, "bigram_model_utterance_bin6"], "alpha.")
        self.assertEqual(patch.loc[0, "trigram_model_utterance_bin6"], "gamma.")


if __name__ == "__main__":
    unittest.main()
