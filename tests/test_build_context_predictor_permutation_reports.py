import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_context_predictor_permutation_reports import (
    attach_context_size_counts,
    context_counts,
    fit_context_permutation_models,
    run_all,
)


def toy_context_rows() -> pd.DataFrame:
    rows = []
    contexts = {
        "k0": "",
        "k1": "do you like it",
        "k2": "look at this do you like it",
        "k3": "look at this what do you see do you like it",
    }
    for k, context in contexts.items():
        for idx in range(18):
            child = "Ada" if idx % 2 == 0 else "Ben"
            age = 12 + idx
            effort = 1 + idx % 5
            context_size = len(context.split())
            rows.append(
                {
                    "score_id": f"{k}-{idx}",
                    "utterance_id": f"utt-{k}-{idx}",
                    "dataset": "Toy",
                    "child_id": child,
                    "session_id": f"s{idx}",
                    "age_months": age,
                    "age_bin": "006-023" if age < 24 else "024-029",
                    "role": "child",
                    "target_variant": "real",
                    "context_k": k,
                    "context_text": context,
                    "context_entropy_join_status": "no_context_k0" if k == "k0" else "matched_exact",
                    "context_entropy_bits": "" if k == "k0" else 2.0 + 0.08 * idx + 0.03 * context_size,
                    "sum_bits": 12 + 0.5 * age + 3.0 * effort + 0.4 * context_size + (0 if child == "Ada" else 1),
                    "nb_words": effort,
                    "nb_morphemes": effort + 1,
                    "nb_syllables_cmu_or_pkg": effort + 2,
                    "nb_syllables_pkg": effort + 2,
                    "nb_phonemes": 3 * effort + 1,
                }
            )
    return pd.DataFrame(rows)


class ContextPredictorPermutationReportTests(unittest.TestCase):
    def test_context_counts_use_zero_for_empty_context_and_surface_counts_for_text(self):
        self.assertEqual(context_counts(""), (0, 0, 0, 0, 0, 0, 0))

        words, morphemes, syll_cmu_pkg, syll_pkg, phonemes, syll_fb, g2p_fb = context_counts("do you like it")

        self.assertEqual(words, 4)
        self.assertEqual(morphemes, 4)
        self.assertGreaterEqual(syll_cmu_pkg, 4)
        self.assertGreaterEqual(syll_pkg, 4)
        self.assertGreaterEqual(phonemes, 4)
        self.assertEqual(syll_fb, 0)
        self.assertEqual(g2p_fb, 0)

    def test_k0_models_do_not_invent_context_predictors(self):
        measured, _counts = attach_context_size_counts(toy_context_rows())

        records = fit_context_permutation_models(measured, context_k="k0")

        baseline = [row for row in records if row.context_predictor_family == "baseline"]
        context_models = [row for row in records if row.context_predictor_family != "baseline"]
        self.assertTrue(any(row.status == "fit" for row in baseline))
        self.assertTrue(all(row.status == "skipped" for row in context_models))
        self.assertTrue(any("no variation" in row.error or "no complete rows" in row.error for row in context_models))

    def test_full_builder_writes_separate_k_reports_and_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "toy.csv"
            toy_context_rows().to_csv(input_csv, index=False)

            outputs = run_all(
                input_csv=input_csv,
                output_dir=root / "results",
                fig_dir=root / "figs",
                doc_dir=root / "docs",
                context_ks=("k0", "k1", "k2", "k3"),
                chunksize=20,
            )

            self.assertTrue(outputs["audit"].exists())
            self.assertTrue(outputs["compare_html"].exists())
            self.assertTrue(outputs["k0_html"].exists())
            self.assertTrue(outputs["k3_html"].exists())
            text = outputs["compare_md"].read_text(encoding="utf-8")
            self.assertIn("K0-K3 Comparison", text)
            self.assertIn("mean_delta_r2", text)
            summary = pd.read_csv(outputs["model_summary"])
            self.assertIn("context_size_coef", summary.columns)
            self.assertIn("context_entropy_coef", summary.columns)


if __name__ == "__main__":
    unittest.main()
