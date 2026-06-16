import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_route1_corrected_baseline_atlas import (
    EFFORT_SPECS,
    add_corrected_predictors,
    audit_source_coverage,
    build_report_plan,
    build_child_structure_manifest,
    build_model_spec,
    build_primary_manifest,
    child_structure,
    fit_spec_row,
    model_family,
    prepare_model_frame,
    question_type,
    run_fit_atlas,
    run_preflight,
    run_smoke_fits,
    write_manifests,
)


def toy_route1_rows() -> pd.DataFrame:
    rows = []
    contexts = {
        0: "what do you want?",
        1: "do you want milk?",
        2: "this is nice.",
        3: "which one is blue?",
    }
    for child_idx, child in enumerate(["Ada", "Ben", "Cara"]):
        for session_idx, age in enumerate([18, 24, 30, 36, 42, 48]):
            utt = f"{child}-{session_idx}"
            effort = 2 + (session_idx % 4)
            context = contexts[(session_idx + child_idx) % len(contexts)]
            for variant, offset in {
                "real": 0.0,
                "random": 4.0,
                "unigram": 2.5,
                "bigram": 1.5,
                "trigram": 0.5,
                "lstm_additive_k3_same_length": 1.0,
            }.items():
                rows.append(
                    {
                        "score_id": f"{utt}-{variant}",
                        "utterance_id": utt,
                        "dataset": "Toy",
                        "child_id": child,
                        "session_id": f"s{session_idx}",
                        "age_months": age,
                        "age_bin": "006-023" if age < 24 else "024-029" if age < 30 else "030-035",
                        "role": "child",
                        "target_variant": variant,
                        "context_k": "k3",
                        "context_text": context,
                        "context_entropy_bits": 5.0 + 0.1 * session_idx + 0.2 * child_idx,
                        "sum_bits": 10 + 0.4 * age + 2.0 * effort + child_idx + offset,
                        "nb_words": effort,
                        "nb_morphemes": effort + 1,
                        "nb_syllables_cmu_or_pkg": effort + 1,
                        "nb_syllables_pkg": effort + 1,
                        "nb_phonemes": 3 * effort + 2,
                    }
                )
    return pd.DataFrame(rows)


class CorrectedRoute1BaselineAtlasTests(unittest.TestCase):
    def test_question_type_classifies_parent_contexts(self):
        self.assertEqual(question_type("what do you want?"), "wh-question")
        self.assertEqual(question_type("Do you want milk?"), "yes/no question")
        self.assertEqual(question_type("this is nice."), "not question")
        self.assertEqual(question_type("ready?"), "other question")
        self.assertEqual(question_type(""), "empty/no context")

    def test_primary_manifest_repeats_full_ladder_independently_by_source(self):
        manifest = build_primary_manifest(
            target_sources=("real", "random", "unigram", "bigram", "trigram", "lstm_additive_k3_same_length"),
            context_ks=("k3",),
            effort_specs=(EFFORT_SPECS[0],),
        )

        self.assertEqual(set(manifest["target_source"]), {"real", "random", "unigram", "bigram", "trigram", "lstm_additive_k3_same_length"})
        counts = manifest.groupby("target_source")["model_id"].nunique()
        self.assertTrue((counts == 17).all())
        self.assertEqual(set(manifest["stage"]), {"source_specific_primary"})
        m1 = manifest[manifest["model_id"].eq("M1")].iloc[0]
        m2 = manifest[manifest["model_id"].eq("M2")].iloc[0]
        self.assertNotIn("C(child_id)", m1["statsmodels_formula"])
        self.assertIn("C(child_id)", m2["statsmodels_formula"])
        self.assertIn("M15", set(manifest["model_id"]))

    def test_corrected_formulas_keep_hierarchy_and_child_structures_separate(self):
        effort = EFFORT_SPECS[0]
        m6_cs1 = build_model_spec(
            family=model_family("M6"),
            effort=effort,
            target_source="real",
            context_k="k3",
            structure=child_structure("CS1"),
            stage="test",
        )
        formula = m6_cs1.statsmodels_formula

        self.assertIn("age_c * effort_c", formula)
        self.assertIn("context_entropy_c", formula)
        self.assertIn("age_c:context_entropy_c", formula)
        self.assertIn("effort_c:context_entropy_c", formula)
        self.assertIn("parent_context_effort_c", formula)
        self.assertIn("C(question_type)", formula)
        self.assertIn("C(child_id)", formula)

        cs4 = build_model_spec(
            family=model_family("M3"),
            effort=effort,
            target_source="real",
            context_k="k3",
            structure=child_structure("CS4"),
            stage="test",
        )
        self.assertNotIn("C(child_id)", cs4.statsmodels_formula)
        self.assertEqual(cs4.random_effects, "1")

        cs6 = build_model_spec(
            family=model_family("M3"),
            effort=effort,
            target_source="real",
            context_k="k3",
            structure=child_structure("CS6"),
            stage="test",
        )
        self.assertIn("age_within_child_c * effort_c", cs6.statsmodels_formula)
        self.assertIn("C(child_id)", cs6.statsmodels_formula)
        self.assertNotIn("child_mean_age_c", cs6.statsmodels_formula)

        cs7 = build_model_spec(
            family=model_family("M3"),
            effort=effort,
            target_source="real",
            context_k="k3",
            structure=child_structure("CS7"),
            stage="test",
        )
        self.assertIn("age_within_child_c * effort_c", cs7.statsmodels_formula)
        self.assertIn("child_mean_age_c", cs7.statsmodels_formula)
        self.assertNotIn("C(child_id)", cs7.statsmodels_formula)

    def test_extended_formulas_keep_lower_order_terms(self):
        effort = EFFORT_SPECS[0]
        m8 = build_model_spec(
            family=model_family("M8"),
            effort=effort,
            target_source="real",
            context_k="k3",
            structure=child_structure("CS1"),
            stage="test",
        )
        self.assertIn("age_c * effort_c", m8.statsmodels_formula)
        self.assertIn("I(age_c ** 2)", m8.statsmodels_formula)
        self.assertIn("I(age_c ** 2):effort_c", m8.statsmodels_formula)

        m10 = build_model_spec(
            family=model_family("M10"),
            effort=effort,
            target_source="real",
            context_k="k3",
            structure=child_structure("CS1"),
            stage="test",
        )
        self.assertIn("C(age_bin) * effort_c", m10.statsmodels_formula)

        m15 = build_model_spec(
            family=model_family("M15"),
            effort=effort,
            target_source="real",
            context_k="k3",
            structure=child_structure("CS1"),
            stage="test",
        )
        formula = m15.statsmodels_formula
        self.assertIn("age_c * effort_c", formula)
        self.assertIn("context_entropy_c", formula)
        self.assertIn("parent_context_effort_c", formula)
        self.assertIn("C(question_type)", formula)
        self.assertIn("age_c:context_entropy_c", formula)
        self.assertIn("effort_c:parent_context_effort_c", formula)
        self.assertIn("context_entropy_c:C(question_type)", formula)

    def test_child_structure_manifest_keeps_fixed_and_random_variants_labeled(self):
        manifest = build_child_structure_manifest(
            target_sources=("real",),
            context_ks=("k3",),
            effort_specs=(EFFORT_SPECS[0],),
        )

        self.assertEqual(set(manifest["stage"]), {"child_structure_sensitivity"})
        self.assertEqual(set(manifest["child_structure"]), {"CS0", "CS0c", "CS1", "CS2", "CS3", "CS4", "CS5", "CS6", "CS7"})
        self.assertEqual(set(manifest["model_id"]), {"M1", "M2", "M3", "M4a", "M4b", "M4c", "M5", "M6"})
        random_rows = manifest[manifest["child_structure"].isin(["CS4", "CS5"])]
        self.assertFalse(random_rows["statsmodels_formula"].str.contains("C\\(child_id\\)", regex=True).any())
        mundlak_rows = manifest[manifest["child_structure"].eq("CS7")]
        self.assertTrue(mundlak_rows["statsmodels_formula"].str.contains("child_mean_age_c").all())
        self.assertFalse(mundlak_rows["statsmodels_formula"].str.contains("C\\(child_id\\)", regex=True).any())

    def test_add_corrected_predictors_adds_parent_effort_and_question_type(self):
        frame = add_corrected_predictors(pd.DataFrame({"target_variant": ["real"], "context_text": ["what do you want?"]}))

        self.assertEqual(frame.loc[0, "target_source"], "real")
        self.assertEqual(str(frame.loc[0, "question_type"]), "wh-question")
        self.assertEqual(int(frame.loc[0, "parent_context_nb_words"]), 4)
        self.assertIn("parent_context_nb_phonemes", frame.columns)

    def test_prepare_model_frame_centers_corrected_predictors(self):
        spec = build_model_spec(
            family=model_family("M5"),
            effort=EFFORT_SPECS[0],
            target_source="real",
            context_k="k3",
            structure=child_structure("CS1"),
            stage="test",
        )

        model_frame, error = prepare_model_frame(toy_route1_rows(), spec)

        self.assertEqual(error, "")
        self.assertIn("parent_context_effort_c", model_frame.columns)
        self.assertIn("context_entropy_c", model_frame.columns)
        self.assertIn("question_type", model_frame.columns)
        self.assertAlmostEqual(float(model_frame["age_c"].mean()), 0.0, places=8)
        self.assertAlmostEqual(float(model_frame["effort_c"].mean()), 0.0, places=8)
        self.assertEqual(set(model_frame["target_source"]), {"real"})

    def test_audit_source_coverage_reports_each_child_source(self):
        audit = audit_source_coverage(toy_route1_rows())

        self.assertEqual(set(audit["target_source"]), {"real", "random", "unigram", "bigram", "trigram", "lstm_additive_k3_same_length"})
        real = audit[audit["target_source"].eq("real")].iloc[0]
        self.assertEqual(int(real["rows"]), 18)
        self.assertEqual(int(real["children"]), 3)
        self.assertEqual(int(real["missing_sum_bits_rows"]), 0)

    def test_smoke_fit_runs_bounded_source_specific_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy.csv"
            toy_route1_rows().to_csv(path, index=False)

            summary = run_smoke_fits(
                input_csv=path,
                output_dir=root / "out",
                max_rows=1000,
                target_sources=("real", "random"),
                context_ks=("k3",),
                effort_cols=("nb_words",),
                child_structures=("CS0c", "CS1"),
                model_ids=("M1", "M2", "M3"),
                chunksize=20,
            )

            self.assertEqual(set(summary["target_source"]), {"real", "random"})
            self.assertEqual(set(summary["model_id"]), {"M1", "M2", "M3"})
            self.assertTrue((root / "out" / "smoke_fit_summary.csv").exists())
            self.assertTrue((summary["status"] == "fit").any())

    def test_fit_spec_row_records_skip_reason_for_missing_entropy(self):
        frame = toy_route1_rows()
        frame["context_entropy_bits"] = frame["context_entropy_bits"].astype(object)
        frame.loc[frame["target_variant"].eq("real"), "context_entropy_bits"] = ""
        spec = build_model_spec(
            family=model_family("M4b"),
            effort=EFFORT_SPECS[0],
            target_source="real",
            context_k="k3",
            structure=child_structure("CS1"),
            stage="test",
        )

        row = fit_spec_row(frame, spec)

        self.assertEqual(row["status"], "skipped")
        self.assertEqual(row["error"], "no complete rows")

    def test_report_plan_keeps_source_reports_and_comparison_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = build_report_plan(
                output_dir=Path(tmp),
                target_sources=("real", "random", "lstm_additive_k3_same_length"),
                context_ks=("k3",),
                effort_specs=(EFFORT_SPECS[0],),
                model_ids=("M1", "M2", "M7"),
            )

        source_reports = plan[plan["report_type"].eq("source_specific_atlas")]
        self.assertEqual(set(source_reports["target_source"]), {"real", "random", "lstm_additive_k3_same_length"})
        self.assertEqual(len(plan[plan["report_type"].eq("pooled_source_comparison")]), 1)
        self.assertTrue(plan["markdown_path"].str.contains("pooled_source_comparison").any())

    def test_manifest_stage_writes_report_plan_and_launch_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_manifests(Path(tmp))

            self.assertTrue(paths["report_plan"].exists())
            self.assertTrue(paths["launch_commands"].exists())
            launch = paths["launch_commands"].read_text(encoding="utf-8")
            self.assertIn("--stage preflight", launch)
            self.assertIn("--stage fit-atlas", launch)
            self.assertIn("lstm_additive_k3_same_length", launch)
            self.assertIn("full_child_structure_sensitivity", launch)
            self.assertIn("CS0,CS0c,CS1,CS2,CS3,CS4,CS5,CS6,CS7", launch)

    def test_preflight_writes_audit_manifests_and_report_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy.csv"
            toy_route1_rows().to_csv(path, index=False)

            outputs = run_preflight(
                input_csv=path,
                output_dir=root / "preflight",
                target_sources=("real", "random"),
                context_ks=("k3",),
                effort_cols=("nb_words",),
                model_ids=("M1", "M2", "M7"),
                chunksize=20,
                max_rows=1000,
            )

            self.assertTrue(outputs["primary_manifest"].exists())
            self.assertTrue(outputs["source_audit"].exists())
            self.assertTrue(outputs["report_plan"].exists())
            manifest = pd.read_csv(outputs["primary_manifest"])
            self.assertEqual(set(manifest["model_id"]), {"M1", "M2", "M7"})

    def test_fit_atlas_writes_independent_source_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy.csv"
            toy_route1_rows().to_csv(path, index=False)

            summary = run_fit_atlas(
                input_csv=path,
                output_dir=root / "fit",
                target_sources=("real", "random"),
                context_ks=("k3",),
                effort_cols=("nb_words",),
                child_structures=("primary",),
                model_ids=("M1", "M2", "M7"),
                chunksize=20,
                max_rows=1000,
            )

            self.assertEqual(set(summary["target_source"]), {"real", "random"})
            self.assertTrue((root / "fit" / "real_model_summary.csv").exists())
            self.assertTrue((root / "fit" / "random_model_summary.csv").exists())
            self.assertTrue((root / "fit" / "reports" / "real_route1_corrected_atlas.md").exists())
            self.assertTrue((root / "fit" / "reports" / "random_route1_corrected_atlas.md").exists())

    def test_entropy_models_skip_cleanly_when_entropy_column_is_absent(self):
        frame = toy_route1_rows().drop(columns=["context_entropy_bits"])
        spec = build_model_spec(
            family=model_family("M4b"),
            effort=EFFORT_SPECS[0],
            target_source="real",
            context_k="k3",
            structure=child_structure("CS1"),
            stage="test",
        )

        row = fit_spec_row(frame, spec)

        self.assertEqual(row["status"], "skipped")
        self.assertEqual(row["error"], "no complete rows")


if __name__ == "__main__":
    unittest.main()
