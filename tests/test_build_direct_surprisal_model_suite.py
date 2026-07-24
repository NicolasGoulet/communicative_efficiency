import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_direct_surprisal_model_suite import (
    PRIMARY_OUTCOMES,
    run_suite,
)


def toy_wide_rows() -> pd.DataFrame:
    rows = []
    children = [
        ("Brown", "Adam", "pbm_discovery"),
        ("Manchester", "Anne", "pbm_discovery"),
        ("Providence", "Alex", "pbm_discovery"),
        ("Belfast", "Barbara", "non_pbm_confirmation"),
        ("Forrester", "Ella", "non_pbm_confirmation"),
        ("Wells", "Abigail", "non_pbm_confirmation"),
    ]
    for child_index, (dataset, child_id, sample_group) in enumerate(children):
        for age in [18, 24, 30, 36]:
            age_bin = (
                "006-023"
                if age < 24
                else "024-029"
                if age < 30
                else "030-035"
                if age < 36
                else "036-041"
            )
            for words in [1, 2, 4]:
                for repetition in range(3):
                    contextual = 16.0 + 1.8 * words - 0.12 * age + child_index * 0.2
                    unconditional = contextual + 1.5 + 0.06 * age
                    rows.append(
                        {
                            "scorer_id": "toy_scorer",
                            "dataset": dataset,
                            "child_id": child_id,
                            "child_key": f"{dataset}/{child_id}",
                            "sample_group": sample_group,
                            "session_id": f"{age:03d}",
                            "age_months": age,
                            "age_bin": age_bin,
                            "utterance_id": f"{child_id}-{age}-{words}-{repetition}",
                            "real_nb_words": words,
                            "real_nb_characters": words * 4,
                            "context_available_k1": 1,
                            "context_available_k2": 1,
                            "context_available_k3": 1,
                            "real_k0_sum_bits": unconditional,
                            "real_k1_sum_bits": contextual + 0.8,
                            "real_k2_sum_bits": contextual + 0.3,
                            "real_k3_sum_bits": contextual,
                            "real_k0_n_eval_tokens": words + 1,
                            "real_k1_n_eval_tokens": words + 1,
                            "real_k2_n_eval_tokens": words + 1,
                            "real_k3_n_eval_tokens": words + 1,
                            "real_context_gain_k1": unconditional - contextual - 0.8,
                            "real_context_gain_k2": unconditional - contextual - 0.3,
                            "real_context_gain_k3": unconditional - contextual,
                            "random_minus_real_k3_bits": 5.0 - 0.01 * age,
                            "unigram_minus_real_k3_bits": 4.0 - 0.01 * age,
                            "bigram_minus_real_k3_bits": 3.0 - 0.01 * age,
                            "trigram_minus_real_k3_bits": 2.0 - 0.01 * age,
                        }
                    )
    return pd.DataFrame(rows)


class DirectSurprisalModelSuiteTests(unittest.TestCase):
    def test_run_suite_separates_discovery_confirmation_and_all79(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "toy_wide.csv.gz"
            output_dir = root / "output"
            fig_dir = root / "figures"
            report_md = root / "report.md"
            report_html = root / "report.html"
            toy_wide_rows().to_csv(input_path, index=False)

            audit = run_suite(
                input_wide=input_path,
                output_dir=output_dir,
                fig_dir=fig_dir,
                report_md=report_md,
                report_html=report_html,
                scorer_label="Toy scorer",
                bootstrap_reps=2,
                bootstrap_seed=123,
            )

            self.assertEqual(
                set(audit["scopes"]),
                {"pbm_discovery", "non_pbm_confirmation", "all79_descriptive"},
            )
            summaries = pd.read_csv(output_dir / "model_summaries.csv")
            primary = summaries[
                summaries["model_id"].isin(PRIMARY_OUTCOMES)
                & summaries["estimator"].eq("exact_cell_wls_child_cluster")
                & summaries["fit_status"].eq("PASS")
            ]
            self.assertEqual(len(primary), 9)
            p1 = primary[primary["model_id"].eq("P1_k3_contextual")]
            p3 = primary[primary["model_id"].eq("P3_k3_context_gain")]
            self.assertTrue((p1["age_estimate"] < 0).all())
            self.assertTrue((p3["age_estimate"] > 0).all())
            profiles = pd.read_csv(output_dir / "child_profile_audit.csv")
            self.assertEqual(profiles["child_key"].nunique(), 6)
            self.assertEqual(len(profiles), 12)
            self.assertTrue(report_md.exists())
            self.assertTrue(report_html.exists())
            self.assertTrue((output_dir / "child_bootstrap_summary.csv").exists())


if __name__ == "__main__":
    unittest.main()
