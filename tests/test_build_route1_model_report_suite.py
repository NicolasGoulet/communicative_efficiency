import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_route1_model_report_suite import (
    ZOO_CARD_DEFS,
    build_baseline_deltas,
    coerce_and_derive,
    fit_comparison_models,
    load_zoo_data_from_outputs,
    plot_zoo_model_card_figures,
    question_type,
    read_zoo_data,
    run_suite_modeling_from_outputs,
    run_suite_analysis,
)


def toy_long_rows() -> pd.DataFrame:
    rows = []
    entropy_cols = {
        "context_entropy_join_status": "matched",
        "context_entropy_token_count": 5,
        "context_entropy_bits": 6.5,
        "context_next_top1_prob": 0.22,
        "context_next_top5_mass": 0.51,
        "context_next_top10_mass": 0.63,
        "context_next_top50_mass": 0.82,
        "context_next_argmax_bits": 2.18,
    }
    for child_idx, child in enumerate(["Ada", "Ben", "Cara"]):
        for session_id, age in enumerate([18, 24, 30, 36], start=1):
            utt_id = f"{child}-{session_id}"
            base = {
                "utterance_id": utt_id,
                "dataset": "ToySet",
                "child_id": child,
                "session_id": str(session_id),
                "age_months": age,
                "age_bin": "006-023" if age < 24 else "024-029" if age < 30 else "030-035",
                "context_k": "k3",
                "context_text": "what do you want?" if session_id % 2 else "the red one.",
                "mean_bits_per_token": 5.0,
                "n_eval_tokens": 3,
                "nb_words": 2 + session_id % 2,
                "nb_morphemes": 3 + session_id % 2,
                "nb_syllables_cmu_or_pkg": 3 + session_id % 2,
                "nb_syllables_pkg": 3 + session_id % 2,
                "nb_phonemes": 8 + session_id,
                "cmu_oov_word_count": 0,
                "syllable_pkg_fallback_word_count": 0,
                "g2p_fallback_word_count": 0,
                "same_word_count_as_child_real": 1,
                "delta_nb_morphemes_vs_child_real": 0,
                "delta_nb_syllables_cmu_or_pkg_vs_child_real": 0,
                "delta_nb_syllables_pkg_vs_child_real": 0,
                "delta_nb_phonemes_vs_child_real": 0,
                **entropy_cols,
            }
            for variant, offset in {
                "real": 0.0,
                "random": -4.0,
                "unigram": -2.0,
                "bigram": -1.0,
                "trigram": -0.5,
            }.items():
                sum_bits = 20 + age * 0.25 + child_idx + offset
                rows.append(
                    {
                        **base,
                        "score_id": f"{utt_id}-{variant}",
                        "role": "child",
                        "target_variant": variant,
                        "sum_bits": sum_bits,
                        "bits_per_word": sum_bits / base["nb_words"],
                        "bits_per_morpheme": sum_bits / base["nb_morphemes"],
                        "bits_per_syllable_cmu_or_pkg": sum_bits / base["nb_syllables_cmu_or_pkg"],
                        "bits_per_syllable_pkg": sum_bits / base["nb_syllables_pkg"],
                        "bits_per_phoneme": sum_bits / base["nb_phonemes"],
                    }
                )
            caretaker_bits = 30 + age * 0.1
            rows.append(
                {
                    **base,
                    "score_id": f"{utt_id}-caretaker",
                    "role": "caretaker",
                    "target_variant": "caretaker",
                    "sum_bits": caretaker_bits,
                    "bits_per_word": caretaker_bits / base["nb_words"],
                    "bits_per_morpheme": caretaker_bits / base["nb_morphemes"],
                    "bits_per_syllable_cmu_or_pkg": caretaker_bits / base["nb_syllables_cmu_or_pkg"],
                    "bits_per_syllable_pkg": caretaker_bits / base["nb_syllables_pkg"],
                    "bits_per_phoneme": caretaker_bits / base["nb_phonemes"],
                }
            )
    return pd.DataFrame(rows)


class Route1ModelReportSuiteTests(unittest.TestCase):
    def test_question_type_classifies_common_contexts(self):
        self.assertEqual(question_type("what do you want?"), "wh-question")
        self.assertEqual(question_type("do you want milk?"), "yes/no question")
        self.assertEqual(question_type("this is nice."), "not question")

    def test_coerce_and_derive_adds_context_and_age_predictors(self):
        frame = coerce_and_derive(toy_long_rows().head(3))

        self.assertIn("context_word_count", frame.columns)
        self.assertIn("context_question_type", frame.columns)
        self.assertIn("age_after_24", frame.columns)
        self.assertTrue((frame["context_word_count"] > 0).all())

    def test_build_baseline_deltas_uses_row_matched_variants(self):
        clean = coerce_and_derive(toy_long_rows()[toy_long_rows()["role"].eq("child")])

        deltas = build_baseline_deltas(clean)

        self.assertIn("delta_sum_bits_real_minus_random", deltas.columns)
        self.assertIn("delta_bits_per_word_real_minus_trigram", deltas.columns)
        self.assertTrue((deltas["delta_sum_bits_real_minus_random"].round(6) == 4.0).all())

    def test_read_zoo_data_writes_bounded_samples_and_deltas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy_route1.csv"
            output_dir = root / "out"
            output_dir.mkdir()
            toy_long_rows().to_csv(path, index=False)

            data = read_zoo_data(path, output_dir, chunksize=20)

            self.assertFalse(data.real_k3.empty)
            self.assertFalse(data.context_real.empty)
            self.assertFalse(data.baseline_k3.empty)
            self.assertFalse(data.baseline_deltas.empty)
            self.assertFalse(data.baseline_trends.empty)
            self.assertFalse(data.role_trends.empty)
            self.assertEqual(set(data.baseline_trends["target_variant"]), {"real", "random", "unigram", "bigram", "trigram"})
            real_early = data.baseline_trends[
                data.baseline_trends["age_bin"].astype(str).eq("006-023")
                & data.baseline_trends["target_variant"].eq("real")
            ].iloc[0]
            self.assertEqual(int(real_early["n_rows"]), 3)
            self.assertAlmostEqual(float(real_early["nb_words_mean"]), 3.0)
            self.assertTrue((output_dir / "baseline_delta_table.csv.gz").exists())
            self.assertTrue((output_dir / "baseline_trends.csv.gz").exists())
            self.assertTrue((output_dir / "role_trends.csv.gz").exists())

    def test_read_zoo_data_allows_absent_scorer_specific_entropy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy_without_entropy.csv"
            output_dir = root / "out"
            output_dir.mkdir()
            frame = toy_long_rows().drop(
                columns=[column for column in toy_long_rows().columns if column.startswith("context_entropy_") or column.startswith("context_next_")]
            )
            frame.to_csv(path, index=False)

            data = read_zoo_data(path, output_dir, chunksize=20)

            self.assertFalse(data.real_k3.empty)
            self.assertFalse(data.context_real.empty)
            self.assertTrue(data.context_real["context_entropy_bits"].isna().all())
            self.assertTrue(data.context_real["context_next_top1_prob"].isna().all())
            self.assertTrue(
                (data.entropy_status["context_entropy_join_status"].fillna("") == "").all()
            )

    def test_fit_comparison_models_writes_pairwise_model_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy_route1.csv"
            output_dir = root / "out"
            output_dir.mkdir()
            toy_long_rows().to_csv(path, index=False)
            data = read_zoo_data(path, output_dir, chunksize=20)

            summary, coefs = fit_comparison_models(data, output_dir)

            self.assertFalse(summary.empty)
            self.assertFalse(coefs.empty)
            model_names = set(summary["model"])
            self.assertIn("Child minus random: total bits | effort=Words", model_names)
            self.assertIn("Trajectory interaction: child vs trigram | effort=Phonemes", model_names)
            self.assertIn("Child vs caretaker: total bits | effort=Syllables: pkg", model_names)
            self.assertGreaterEqual(len(summary), 40)
            self.assertTrue((summary["status"] == "fit").any())
            self.assertTrue((output_dir / "comparison_model_summary.csv").exists())
            self.assertTrue((output_dir / "comparison_model_coefficients.csv").exists())

    def test_model_card_definitions_include_plot_reading_guides(self):
        self.assertGreaterEqual(len(ZOO_CARD_DEFS), 10)
        for card in ZOO_CARD_DEFS:
            with self.subTest(card=card["short"]):
                self.assertTrue(card["model"])
                self.assertTrue(card["question_family"])
                self.assertTrue(card["plot"].endswith(".png"))
                self.assertGreater(len(card["plot_reading"].split()), 8)

    def test_plot_zoo_model_card_figures_writes_card_plots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy_route1.csv"
            output_dir = root / "out"
            fig_dir = root / "figs"
            output_dir.mkdir()
            toy_long_rows().to_csv(path, index=False)
            data = read_zoo_data(path, output_dir, chunksize=20)

            plot_zoo_model_card_figures(data, fig_dir)

            self.assertTrue((fig_dir / "z1_information_child_fe_age.png").exists())
            self.assertTrue((fig_dir / "z7_baseline_comparison.png").exists())
            self.assertTrue((fig_dir / "z11_real_minus_baseline_delta.png").exists())

    def test_run_suite_analysis_outputs_can_be_loaded_without_raw_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy_route1.csv"
            output_dir = root / "out"
            fig_dir = root / "figs"
            toy_long_rows().to_csv(path, index=False)

            outputs = run_suite_analysis(
                input_csv=path,
                output_dir=output_dir,
                fig_dir=fig_dir,
                chunksize=20,
                max_rows=None,
            )
            path.unlink()
            data = load_zoo_data_from_outputs(output_dir)

            self.assertTrue(outputs["zoo_output_dir"].exists())
            self.assertFalse(data.real_k3.empty)
            self.assertFalse(data.baseline_deltas.empty)
            self.assertTrue((output_dir / "comparison_model_summary.csv").exists())
            self.assertTrue((output_dir / "zoo_model_variant_manifest.csv").exists())

    def test_run_suite_analysis_without_entropy_keeps_direct_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy_without_entropy.csv"
            output_dir = root / "out"
            fig_dir = root / "figs"
            frame = toy_long_rows().drop(
                columns=[
                    column
                    for column in toy_long_rows().columns
                    if column.startswith("context_entropy_")
                    or column.startswith("context_next_")
                ]
            )
            frame.to_csv(path, index=False)

            run_suite_analysis(
                input_csv=path,
                output_dir=output_dir,
                fig_dir=fig_dir,
                chunksize=20,
            )

            summary = pd.read_csv(output_dir / "model_zoo_summary.csv")
            direct = summary[
                summary["model"].str.startswith("Z1 Information | child FE", na=False)
            ]
            entropy = summary[
                summary["model"].str.startswith(("Z3 ", "Z4 ", "Z10 "), na=False)
            ]
            direct_context = summary[
                summary["model"].str.startswith(("Z5 ", "Z6 "), na=False)
            ]
            self.assertTrue((direct["status"] == "fit").any())
            self.assertFalse((entropy["status"] == "fit").any())
            self.assertTrue((direct_context["status"] == "fit").any())
            self.assertTrue((fig_dir / "effort_controlled_comparison_model_r2.png").exists())
            self.assertTrue((fig_dir / "z1_family_coefficients.png").exists())
            model_summary = pd.read_csv(output_dir / "model_zoo_summary.csv")
            self.assertGreaterEqual(len(model_summary), 50)
            formulas = model_summary["formula"].fillna("").astype(str)
            combined_effort_formula = formulas.str.contains("nb_words_z \\+ nb_morphemes_z", regex=True)
            self.assertFalse(combined_effort_formula.any())

            rerun_outputs = run_suite_modeling_from_outputs(output_dir=output_dir, fig_dir=fig_dir)
            self.assertTrue(rerun_outputs["zoo_output_dir"].exists())
            self.assertTrue((output_dir / "zoo_model_variant_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
