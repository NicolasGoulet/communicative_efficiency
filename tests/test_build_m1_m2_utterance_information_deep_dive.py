import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_m1_m2_utterance_information_deep_dive import (
    EFFORT_MEASURES,
    assign_effort_level,
    build_packet,
    clean_modeling_rows,
    expanded_fit_summary_rows,
    fit_all_models,
    fit_expanded_models,
    fit_m4_models,
    fit_saturated_models,
    m4_summary_rows,
    model_fit_rows,
    read_modeling_rows,
    render_packet_report_from_outputs,
    run_expanded_plot_analysis,
    run_line_variant_analysis,
    run_m5_m6_analysis,
    saturated_summary_rows,
    variable_importance_rows,
)


def toy_route1_rows() -> pd.DataFrame:
    rows = []
    for child_idx, child in enumerate(["Ada", "Ben", "Cara"]):
        for i, age in enumerate([18, 24, 30, 36, 42, 48]):
            words = 1 + (i % 3)
            morphemes = words + (i % 2)
            syll_cmu = words + 1
            syll_pkg = words + 2
            phonemes = words * 3 + i
            child_offset = child_idx * 4.0
            rows.append(
                {
                    "score_id": f"{child}-{i}",
                    "utterance_id": f"u-{child}-{i}",
                    "dataset": "ToySet",
                    "child_id": child,
                    "session_id": f"s-{i}",
                    "age_months": str(age),
                    "age_bin": "024-029" if age < 30 else "030-035",
                    "role": "child",
                    "target_variant": "real",
                    "context_k": "k3",
                    "context_text": "what do you want now?",
                    "context_entropy_join_status": "matched",
                    "context_entropy_token_count": "5",
                    "context_entropy_bits": str(4.0 + 0.1 * age + child_idx),
                    "context_next_top1_prob": str(0.5 - 0.01 * i),
                    "sum_bits": 10 + 0.5 * age + 3.0 * words + child_offset,
                    "nb_words": words,
                    "nb_morphemes": morphemes,
                    "nb_syllables_cmu_or_pkg": syll_cmu,
                    "nb_syllables_pkg": syll_pkg,
                    "nb_phonemes": phonemes,
                }
            )
    rows.append(
        {
            "score_id": "ignored-random",
            "utterance_id": "u-random",
            "dataset": "ToySet",
            "child_id": "Ada",
            "session_id": "s-x",
            "age_months": "24",
            "age_bin": "024-029",
            "role": "child",
            "target_variant": "random",
            "context_k": "k3",
            "context_text": "what do you want now?",
            "context_entropy_join_status": "matched",
            "context_entropy_token_count": "5",
            "context_entropy_bits": "5.0",
            "context_next_top1_prob": "0.4",
            "sum_bits": 999,
            "nb_words": 1,
            "nb_morphemes": 1,
            "nb_syllables_cmu_or_pkg": 1,
            "nb_syllables_pkg": 1,
            "nb_phonemes": 1,
        }
    )
    return pd.DataFrame(rows)


class M1M2UtteranceInformationDeepDiveTests(unittest.TestCase):
    def test_read_modeling_rows_keeps_only_real_child_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "route1.csv"
            toy_route1_rows().to_csv(path, index=False)

            out = read_modeling_rows(path, context_k="k3", chunksize=5)

            self.assertEqual(len(out), 18)
            self.assertEqual(set(out["target_variant"]), {"real"})
            self.assertEqual(set(out["role"]), {"child"})
            self.assertEqual(set(out["context_k"]), {"k3"})

    def test_clean_modeling_rows_drops_nonpositive_effort_rows(self):
        frame = toy_route1_rows().head(2).copy()
        frame.loc[0, "nb_words"] = 0

        out = clean_modeling_rows(frame)

        self.assertEqual(len(out), 1)
        self.assertGreater(out["nb_words"].iloc[0], 0)

    def test_fit_all_models_creates_m1_m2_for_each_effort_measure(self):
        frame = clean_modeling_rows(toy_route1_rows().iloc[:18])

        bundles = fit_all_models(frame)
        summary = model_fit_rows(bundles)

        self.assertEqual(len(bundles), len(EFFORT_MEASURES) * 2)
        self.assertEqual(set(summary["model_id"]), {"M1", "M2"})
        self.assertTrue(any("C(child_id)" in bundle.formula for bundle in bundles if bundle.model_id == "M2"))

    def test_variable_importance_contains_child_identity_only_for_m2(self):
        frame = clean_modeling_rows(toy_route1_rows().iloc[:18])

        importance = variable_importance_rows(frame)

        self.assertIn("Age in months", set(importance["importance_term"]))
        self.assertIn("Child identity", set(importance[importance["model_id"].eq("M2")]["importance_term"]))
        self.assertNotIn("Child identity", set(importance[importance["model_id"].eq("M1")]["importance_term"]))

    def test_expanded_models_include_m3_age_by_effort_interaction(self):
        frame = clean_modeling_rows(toy_route1_rows().iloc[:18])

        bundles = fit_expanded_models(frame, include_slow=False)
        summary = expanded_fit_summary_rows(bundles)
        m3 = summary[summary["approach_id"].eq("M3")]

        self.assertFalse(m3.empty)
        self.assertTrue(m3["readable_formula"].str.contains("age \\* effort", regex=True).any())
        self.assertIn("age_effort_coef", summary.columns)
        self.assertTrue(m3["age_effort_coef"].notna().any())

    def test_m4_models_use_context_entropy_rows(self):
        frame = clean_modeling_rows(toy_route1_rows().iloc[:18])

        bundles, m4_frame = fit_m4_models(frame)
        summary = m4_summary_rows(bundles)

        self.assertFalse(m4_frame.empty)
        self.assertIn("context_entropy_c", m4_frame.columns)
        self.assertEqual(set(summary["model_id"]), {"M4a", "M4b", "M4c", "M4d", "M4e"})
        self.assertEqual(set(summary["effort_label"]), {label for _, label in EFFORT_MEASURES})
        self.assertTrue((summary["status"] == "fit").any())
        self.assertIn("entropy_coef", summary.columns)
        self.assertTrue(summary["formula"].str.contains("sum_bits").all())

    def test_saturated_models_include_m5_m6(self):
        frame = clean_modeling_rows(toy_route1_rows().iloc[:18])

        bundles, saturated_frame = fit_saturated_models(frame)
        summary = saturated_summary_rows(bundles)

        self.assertFalse(saturated_frame.empty)
        self.assertIn("effort_level", saturated_frame.columns)
        self.assertEqual(set(summary["effort_label"]), {label for _, label in EFFORT_MEASURES})
        self.assertEqual(set(summary["model_id"]), {"M5", "M6"})
        self.assertTrue(summary["formula"].str.contains("context_entropy").all())
        self.assertTrue(summary["formula"].str.contains("C\\(effort_level\\)", regex=True).all())
        self.assertTrue(summary["formula"].str.contains("C\\(child_id\\)", regex=True).all())
        forbidden_combo = "nb_words_c + nb_morphemes_c"
        self.assertFalse(summary["formula"].str.contains(forbidden_combo, regex=False).any())

    def test_assign_effort_level_creates_ordered_low_mid_high_labels(self):
        levels = assign_effort_level(pd.Series([1, 2, 3, 4, 5, 6]))

        self.assertEqual(list(levels.cat.categories), ["low effort", "mid effort", "high effort"])
        self.assertIn("low effort", set(levels.astype(str)))
        self.assertIn("mid effort", set(levels.astype(str)))
        self.assertIn("high effort", set(levels.astype(str)))

    def test_build_packet_writes_report_and_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "route1.csv"
            output_dir = root / "results"
            fig_dir = root / "figs"
            md_path = root / "report.md"
            html_path = root / "report.html"
            toy_route1_rows().to_csv(input_csv, index=False)

            outputs = build_packet(
                input_csv=input_csv,
                output_dir=output_dir,
                fig_dir=fig_dir,
                md_path=md_path,
                html_path=html_path,
                context_k="k3",
                chunksize=4,
            )

            self.assertTrue(outputs["html"].exists())
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Internal Review", md_text)
            self.assertIn("Model 1: Pooled Age + Continuous Effort", md_text)
            self.assertIn("Model 2: Age + Continuous Effort + Child Identity", md_text)
            self.assertIn("Model 3: Age by Continuous Effort", md_text)
            self.assertIn("Model 4: Context Entropy Predicting Total Information", md_text)
            self.assertIn("Model 5: Context Entropy + Low/Mid/High Effort Identity", md_text)
            self.assertIn("Model 6: Age, Context, and Effort-Level Interactions", md_text)
            self.assertIn("Shared Reading Rules", md_text)
            self.assertIn("A **subvariant** is a real model change", md_text)
            self.assertIn("A **diagnostic view** is not a new model", md_text)
            self.assertIn("Model 1 Subvariants", md_text)
            self.assertIn("Model 4 Subvariants", md_text)
            self.assertIn("Model 6 Diagnostic Views", md_text)
            self.assertIn("For OLS versus child-clustered OLS, the mean", md_text)
            self.assertIn("95% confidence interval", md_text)
            self.assertIn("context_entropy_bits", md_text)
            self.assertIn("Takeaway:", md_text)
            self.assertIn("How to read the plot", md_text)
            self.assertIn("pooled trend", md_text)
            self.assertIn("low/mid/high effort", md_text)
            self.assertIn("Companion view", md_text)
            self.assertIn("standard error", md_text)
            self.assertIn("age:effort", md_text)
            self.assertIn("age_effort_coef", md_text)
            self.assertIn("not sampled full-response entropy", md_text)
            self.assertNotIn("all effort measures, context entropy, context length", md_text)
            self.assertTrue((output_dir / "model_fit_summary.csv").exists())
            self.assertTrue((output_dir / "model_coefficients.csv").exists())
            self.assertTrue((output_dir / "expanded_model_family_summary.csv").exists())
            self.assertTrue((output_dir / "m3_interaction_adjusted_age_predictions.csv").exists())
            self.assertTrue((output_dir / "m4_context_entropy_model_summary.csv").exists())
            self.assertTrue((output_dir / "m4_context_entropy_coefficients.csv").exists())
            self.assertTrue((output_dir / "m4_context_entropy_adjusted_predictions.csv").exists())
            self.assertTrue((output_dir / "m5_m6_saturated_model_summary.csv").exists())
            self.assertTrue((output_dir / "m5_m6_saturated_coefficients.csv").exists())
            self.assertTrue((output_dir / "m5_m6_saturated_adjusted_age_predictions.csv").exists())
            self.assertTrue((fig_dir / "m1_m2_age_coefficients_by_effort.png").exists())
            self.assertTrue((fig_dir / "m1_coefficients_by_effort_version.png").exists())
            self.assertTrue((fig_dir / "m2_coefficients_by_effort_version.png").exists())
            self.assertTrue((fig_dir / "m1_expanded_age_coefficients.png").exists())
            self.assertTrue((fig_dir / "m2_expanded_age_coefficients.png").exists())
            self.assertTrue((fig_dir / "m3_expanded_interaction_coefficients.png").exists())
            self.assertTrue((fig_dir / "m4_context_entropy_descriptive_bins.png").exists())
            self.assertTrue((fig_dir / "m4_context_entropy_adjusted_predictions.png").exists())
            self.assertTrue((fig_dir / "m4_context_entropy_coefficients.png").exists())
            self.assertTrue((fig_dir / "m5_m6_saturated_adjusted_age_predictions.png").exists())
            self.assertTrue((fig_dir / "m5_effort_level_adjusted_age_predictions.png").exists())
            self.assertTrue((fig_dir / "m6_effort_level_adjusted_age_predictions.png").exists())
            self.assertTrue((fig_dir / "m5_m6_effort_level_average_age_predictions.png").exists())
            self.assertTrue((fig_dir / "m5_m6_saturated_selected_coefficients.png").exists())
            self.assertTrue((fig_dir / "m1_ols_adjusted_age_lines.png").exists())
            self.assertTrue((fig_dir / "m2_gee_gaussian_adjusted_age_lines.png").exists())
            self.assertTrue((fig_dir / "m3_ols_interaction_interaction_age_lines.png").exists())

            report_only_md = root / "report_only.md"
            report_only_html = root / "report_only.html"
            input_csv.unlink()
            rerendered = render_packet_report_from_outputs(
                output_dir=output_dir,
                fig_dir=fig_dir,
                md_path=report_only_md,
                html_path=report_only_html,
                context_k="k3",
            )

            self.assertTrue(rerendered["html"].exists())
            self.assertIn("Model 6", report_only_md.read_text(encoding="utf-8"))

    def test_run_m5_m6_analysis_updates_only_effort_level_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "route1.csv"
            output_dir = root / "results"
            fig_dir = root / "figs"
            toy_route1_rows().to_csv(input_csv, index=False)

            run_m5_m6_analysis(
                input_csv=input_csv,
                output_dir=output_dir,
                fig_dir=fig_dir,
                context_k="k3",
                chunksize=4,
            )

            summary = pd.read_csv(output_dir / "m5_m6_saturated_model_summary.csv")
            self.assertEqual(set(summary["model_id"]), {"M5", "M6"})
            self.assertTrue(summary["formula"].str.contains("C\\(effort_level\\)", regex=True).all())
            self.assertTrue(summary[summary["model_id"].eq("M6")]["formula"].str.contains("age_c \\* C\\(effort_level\\)", regex=True).all())
            self.assertTrue((fig_dir / "m5_effort_level_adjusted_age_predictions.png").exists())
            self.assertTrue((fig_dir / "m6_effort_level_adjusted_age_predictions.png").exists())
            self.assertTrue((fig_dir / "m5_m6_effort_level_average_age_predictions.png").exists())

    def test_run_line_variant_analysis_writes_companion_plots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "route1.csv"
            output_dir = root / "results"
            fig_dir = root / "figs"
            toy_route1_rows().to_csv(input_csv, index=False)

            run_line_variant_analysis(
                input_csv=input_csv,
                output_dir=output_dir,
                fig_dir=fig_dir,
                context_k="k3",
                chunksize=4,
            )

            self.assertTrue((output_dir / "m1_m2_low_mid_high_effort_adjusted_age_predictions.csv").exists())
            self.assertTrue((output_dir / "m4_effort_quantile_adjusted_predictions.csv").exists())
            self.assertTrue((output_dir / "m5_m6_effort_level_average_age_predictions.csv").exists())
            self.assertTrue((fig_dir / "m1_low_mid_high_effort_adjusted_age_predictions.png").exists())
            self.assertTrue((fig_dir / "m2_low_mid_high_effort_adjusted_age_predictions.png").exists())
            self.assertTrue((fig_dir / "m4_effort_quantile_adjusted_predictions.png").exists())

    def test_run_expanded_plot_analysis_writes_model_confidence_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "route1.csv"
            output_dir = root / "results"
            fig_dir = root / "figs"
            toy_route1_rows().to_csv(input_csv, index=False)

            run_expanded_plot_analysis(
                input_csv=input_csv,
                output_dir=output_dir,
                fig_dir=fig_dir,
                context_k="k3",
                chunksize=4,
            )

            predictions = pd.read_csv(output_dir / "expanded_adjusted_age_predictions.csv")
            self.assertIn("pred_ci_low", predictions.columns)
            self.assertIn("pred_ci_high", predictions.columns)
            self.assertTrue((fig_dir / "m1_ols_adjusted_age_lines.png").exists())
            self.assertTrue((fig_dir / "m1_ols_cluster_adjusted_age_lines.png").exists())


if __name__ == "__main__":
    unittest.main()
