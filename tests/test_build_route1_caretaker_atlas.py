import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_route1_caretaker_atlas import (
    EFFORT_SPECS,
    add_caretaker_predictors,
    audit_caretaker_rows,
    build_caretaker_manifest,
    build_caretaker_model_spec,
    caretaker_model_family,
    prepare_caretaker_model_frame,
    read_caretaker_rows,
    run_caretaker_preflight,
    run_caretaker_smoke_fit,
)


def toy_caretaker_rows() -> pd.DataFrame:
    rows = []
    contexts = {
        "k0": [""],
        "k1": ["what?", "do you want it now?", "this is nice today."],
        "k2": ["do you want milk?", "do you want the red cup?", "can you put it here for me?"],
        "k3": ["this is nice. ready?", "this is very nice. are you ready?", "look at that blue block."],
    }
    for child_idx, child in enumerate(["Ada", "Ben", "Cara"]):
        for session_idx, age in enumerate([18, 22, 26, 30, 34, 38, 42, 46]):
            for context_idx, context_k in enumerate(["k0", "k1", "k2", "k3"]):
                effort = 3 + ((session_idx + child_idx + context_idx) % 5)
                common = {
                    "score_id": f"{child}-{session_idx}-{context_k}",
                    "utterance_id": f"{child}-{session_idx}",
                    "dataset": "Toy",
                    "child_id": child,
                    "session_id": f"s{session_idx}",
                    "age_months": age,
                    "age_bin": "006-023" if age < 24 else "024-029" if age < 30 else "030-035",
                    "file": f"{child}.cha",
                    "line_no": str(100 + session_idx),
                    "speaker": "MOT" if session_idx % 2 == 0 else "FAT",
                    "context_k": context_k,
                    "context_text": contexts[context_k][(session_idx + child_idx) % len(contexts[context_k])],
                    "nb_words": effort,
                    "nb_morphemes": effort + 1,
                    "nb_syllables_cmu_or_pkg": effort + 1,
                    "nb_syllables_pkg": effort + 1,
                    "nb_phonemes": 3 * effort + 1,
                }
                rows.append(
                    {
                        **common,
                        "role": "caretaker",
                        "target_variant": "caretaker",
                        "target_source": "caretaker",
                        "sum_bits": 8.0 + 0.25 * age + 1.2 * effort + 0.7 * context_idx + child_idx,
                    }
                )
                rows.append(
                    {
                        **common,
                        "score_id": f"{child}-{session_idx}-{context_k}-child",
                        "role": "child",
                        "target_variant": "real",
                        "target_source": "real",
                        "sum_bits": 4.0 + 0.1 * age + effort,
                    }
                )
    return pd.DataFrame(rows)


class CaretakerRoute1AtlasTests(unittest.TestCase):
    def test_caretaker_manifest_is_entropy_free_and_hierarchical(self):
        manifest = build_caretaker_manifest(
            context_ks=("k1",),
            effort_specs=(EFFORT_SPECS[0],),
            model_ids=("CM1", "CM2", "CM3", "CM4a", "CM4c", "CM5", "CM6"),
        )

        formulas = "\n".join(manifest["statsmodels_formula"].astype(str))
        self.assertNotIn("context_entropy", formulas)
        cm3 = manifest[manifest["model_id"].eq("CM3")].iloc[0]
        cm6 = manifest[manifest["model_id"].eq("CM6")].iloc[0]
        self.assertIn("age_c * effort_c", cm3["statsmodels_formula"])
        self.assertIn("C(child_id)", cm3["statsmodels_formula"])
        self.assertIn("preceding_context_effort_c", cm6["statsmodels_formula"])
        self.assertIn("C(question_type)", cm6["statsmodels_formula"])
        self.assertIn("age_c:preceding_context_effort_c", cm6["statsmodels_formula"])
        self.assertIn("effort_c:preceding_context_effort_c", cm6["statsmodels_formula"])

    def test_read_caretaker_rows_filters_role_source_and_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "toy.csv"
            toy_caretaker_rows().to_csv(path, index=False)

            rows = read_caretaker_rows(path, chunksize=17, max_rows=None, context_ks=("k1", "k3"))

        self.assertEqual(set(rows["role"]), {"caretaker"})
        self.assertEqual(set(rows["target_source"]), {"caretaker"})
        self.assertEqual(set(rows["context_k"]), {"k1", "k3"})
        self.assertEqual(len(rows), 3 * 8 * 2)

    def test_add_caretaker_predictors_labels_question_type_and_context_effort(self):
        frame = add_caretaker_predictors(
            pd.DataFrame({"target_variant": ["caretaker"], "context_text": ["what do you want?"]})
        )

        self.assertEqual(frame.loc[0, "target_source"], "caretaker")
        self.assertEqual(str(frame.loc[0, "question_type"]), "wh-question")
        self.assertEqual(int(frame.loc[0, "preceding_context_nb_words"]), 4)
        self.assertIn("preceding_context_nb_phonemes", frame.columns)

    def test_prepare_caretaker_model_frame_centers_predictors(self):
        spec = build_caretaker_model_spec(
            family=caretaker_model_family("CM5"),
            effort=EFFORT_SPECS[0],
            context_k="k1",
            stage="test",
        )

        model_frame, error = prepare_caretaker_model_frame(toy_caretaker_rows(), spec)

        self.assertEqual(error, "")
        self.assertEqual(set(model_frame["role"]), {"caretaker"})
        self.assertEqual(set(model_frame["target_source"]), {"caretaker"})
        self.assertIn("preceding_context_effort_c", model_frame.columns)
        self.assertIn("question_type", model_frame.columns)
        self.assertAlmostEqual(float(model_frame["age_c"].mean()), 0.0, places=8)
        self.assertAlmostEqual(float(model_frame["effort_c"].mean()), 0.0, places=8)

    def test_audit_and_preflight_write_caretaker_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy.csv"
            toy_caretaker_rows().to_csv(path, index=False)

            audit_paths = audit_caretaker_rows(
                path,
                output_dir=root / "audit",
                chunksize=19,
                max_rows=1000,
                context_ks=("k0", "k1", "k2", "k3"),
            )
            outputs = run_caretaker_preflight(
                input_csv=path,
                output_dir=root / "preflight",
                context_ks=("k0", "k1", "k2", "k3"),
                effort_cols=("nb_words",),
                model_ids=("CM1", "CM2", "CM3"),
                chunksize=19,
                max_rows=1000,
            )

            context_audit = pd.read_csv(audit_paths["context_audit"])
            manifest = pd.read_csv(outputs["manifest"])
            launch = outputs["launch_commands"].read_text(encoding="utf-8")
            child_context_audit_exists = outputs["child_context_audit"].exists()

        self.assertEqual(set(context_audit["context_k"]), {"k0", "k1", "k2", "k3"})
        self.assertTrue(child_context_audit_exists)
        self.assertEqual(set(manifest["model_id"]), {"CM1", "CM2", "CM3"})
        self.assertNotIn("context_entropy", "\n".join(manifest["statsmodels_formula"]))
        self.assertIn("--stage fit-atlas", launch)
        self.assertIn("--context-ks k0,k1,k2,k3", launch)

    def test_smoke_fit_runs_entropy_free_caretaker_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "toy.csv"
            rows = toy_caretaker_rows()
            rows = pd.concat(
                [rows[rows["context_k"].eq(context_k)] for context_k in ["k1", "k2", "k3", "k0"]],
                ignore_index=True,
            )
            rows.to_csv(path, index=False)

            summary = run_caretaker_smoke_fit(
                input_csv=path,
                output_dir=root / "smoke",
                max_rows=24,
                context_ks=("k1", "k2", "k3"),
                effort_cols=("nb_words",),
                model_ids=("CM1", "CM2", "CM3", "CM4a", "CM4c"),
                chunksize=17,
            )
            summary_path_exists = (root / "smoke" / "caretaker_smoke_fit_summary.csv").exists()

        self.assertEqual(set(summary["model_id"]), {"CM1", "CM2", "CM3", "CM4a", "CM4c"})
        self.assertEqual(set(summary["context_k"]), {"k1", "k2", "k3"})
        self.assertNotIn("context_entropy", "\n".join(summary["statsmodels_formula"]))
        fits_by_context = summary[summary["status"].eq("fit")].groupby("context_k").size()
        self.assertEqual(set(fits_by_context.index), {"k1", "k2", "k3"})
        self.assertTrue(summary_path_exists)


if __name__ == "__main__":
    unittest.main()
