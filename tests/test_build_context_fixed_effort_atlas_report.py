import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_context_fixed_effort_atlas_report import (
    fixed_effort_bins,
    run_analysis,
    run_report,
)


def toy_context_frame(context_k: str = "k1") -> pd.DataFrame:
    rows = []
    for idx in range(36):
        child = "Ada" if idx % 2 == 0 else "Ben"
        age = 12 + idx
        words = 1 + idx % 12
        morphs = words
        syll = 1 + idx % 14
        phon = 2 + idx % 16
        context_size = 4 + idx % 8
        entropy = 1.4 + 0.04 * idx
        rows.append(
            {
                "score_id": f"{context_k}-{idx}",
                "utterance_id": f"utt-{idx}",
                "dataset": "Toy",
                "child_id": child,
                "session_id": f"s{idx}",
                "age_months": age,
                "age_bin": "006-023" if age < 24 else "024-029",
                "role": "child",
                "target_variant": "real",
                "context_k": context_k,
                "context_entropy_join_status": "matched_exact" if context_k != "k0" else "no_context_k0",
                "context_entropy_bits": entropy if context_k != "k0" else "",
                "sum_bits": 10 + 0.2 * age + 2.0 * words + (0.3 * entropy if context_k != "k0" else 0.0),
                "nb_words": words,
                "nb_morphemes": morphs,
                "nb_syllables_cmu_or_pkg": syll,
                "nb_syllables_pkg": syll,
                "nb_phonemes": phon,
                "context_nb_words": context_size if context_k != "k0" else 0,
                "context_nb_morphemes": context_size if context_k != "k0" else 0,
                "context_nb_syllables_cmu_or_pkg": context_size + 1 if context_k != "k0" else 0,
                "context_nb_syllables_pkg": context_size + 1 if context_k != "k0" else 0,
                "context_nb_phonemes": context_size * 3 if context_k != "k0" else 0,
            }
        )
    return pd.DataFrame(rows)


class ContextFixedEffortAtlasTests(unittest.TestCase):
    def test_fixed_effort_bins_include_requested_word_groups_and_representative_phoneme_groups(self):
        bins = fixed_effort_bins(toy_context_frame())

        word_bins = bins[bins["effort_col"].eq("nb_words")]
        self.assertEqual(list(word_bins["atlas_bin"]), ["1-4", "5-8", "9-12"])
        self.assertEqual(word_bins.iloc[0]["fixed_values"], "1, 2, 3, 4")

        phoneme_bins = bins[bins["effort_col"].eq("nb_phonemes")]
        self.assertEqual(len(phoneme_bins), 3)
        self.assertTrue(all(count >= 3 for count in phoneme_bins["n_fixed_values"]))

    def test_context_fixed_effort_analysis_and_report_write_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            context_out = root / "context"
            out = root / "results"
            figs = root / "figs"
            docs = root / "docs"
            context_out.mkdir()
            toy_context_frame("k0").to_csv(context_out / "route1_real_child_context_measures_k0.csv.gz", index=False)
            toy_context_frame("k1").to_csv(context_out / "route1_real_child_context_measures_k1.csv.gz", index=False)

            outputs = run_analysis(
                context_output_dir=context_out,
                output_dir=out,
                fig_dir=figs,
                context_ks=("k0", "k1"),
                n_points=8,
            )
            report = run_report(
                output_dir=out,
                fig_dir=figs,
                md_path=docs / "context_atlas.md",
                html_path=docs / "context_atlas.html",
            )

            self.assertTrue(outputs["audit"].exists())
            self.assertTrue(outputs["predictions"].exists())
            self.assertTrue(report["html"].exists())
            summary = pd.read_csv(outputs["summary"])
            self.assertIn("CF0", set(summary["model_id"]))
            self.assertIn("CF3", set(summary["model_id"]))
            text = report["md"].read_text(encoding="utf-8")
            self.assertIn("Context Predictors: Fixed-Effort Atlas", text)
            self.assertIn("1-4", text)
            self.assertIn("shaded ribbon", text)


if __name__ == "__main__":
    unittest.main()
