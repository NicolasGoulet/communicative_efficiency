import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from build_full79_qwen_route2_analysis import (  # noqa: E402
    ExpectedCounts,
    extract_full79_base_rows,
    full79_model_specs,
    run_dataset_stage,
    run_feature_stage,
    run_model_stage,
    split_scope_tables,
    validate_generation_handoff,
)
from build_response_entropy_manifest import context_id  # noqa: E402


class Full79QwenRoute2AnalysisTests(unittest.TestCase):
    def test_extracts_real_rows_and_preserves_discovery_confirmation_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wide = root / "wide.csv.gz"
            output = root / "base.csv.gz"
            rows = [
                wide_row("Brown", "Adam", "u1", "hello there", "yes", 24, 1),
                wide_row("Manchester", "Anne", "u2", "want some juice", "more juice", 30, 2),
                wide_row("Belfast", "Barbara", "u3", "look at that", "a dog", 36, 2),
                wide_row("Wells", "Abigail", "u4", "", "missing context", 42, 2),
            ]
            pd.DataFrame(rows).to_csv(wide, index=False)

            frame, audit = extract_full79_base_rows(
                input_wide=wide,
                output_csv=output,
                chunksize=2,
                expected=ExpectedCounts(children=3, datasets=3, eligible_rows=3, unique_contexts=3),
            )

            self.assertEqual(len(frame), 3)
            self.assertEqual(audit["excluded_blank_context_rows"], 1)
            self.assertEqual(set(frame["sample_group"]), {"pbm_discovery", "non_pbm_confirmation"})
            self.assertEqual(set(frame["analysis_scope"]), {"original_21", "other_58"})
            self.assertEqual(frame.loc[frame["utterance_id"].eq("u1"), "child_id"].iloc[0], "Brown/Adam")
            self.assertEqual(
                frame.loc[frame["utterance_id"].eq("u3"), "response_entropy_context_id"].iloc[0],
                context_id("look at that"),
            )
            self.assertTrue(output.exists())

    def test_scope_split_is_disjoint_and_all79_is_union(self):
        frame = pd.DataFrame(
            {
                "analysis_scope": ["original_21", "original_21", "other_58"],
                "utterance_id": ["a", "b", "c"],
            }
        )

        scopes = split_scope_tables(frame)

        self.assertEqual(set(scopes), {"original_21", "other_58", "all_79"})
        self.assertEqual(set(scopes["original_21"]["utterance_id"]), {"a", "b"})
        self.assertEqual(set(scopes["other_58"]["utterance_id"]), {"c"})
        self.assertEqual(set(scopes["all_79"]["utterance_id"]), {"a", "b", "c"})

    def test_generation_handoff_refuses_missing_marker_and_wrong_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_root = root / "generation"
            merged = run_root / "merged"
            merged.mkdir(parents=True)
            marker = root / "PRODUCTION_COMPLETE"
            entropy = merged / "context_response_entropy_features.csv.gz"
            effort = merged / "generated_response_effort_summary_by_context.csv.gz"
            effort_audit = merged / "generated_response_effort_summary_audit.csv"
            write_feature_tables(entropy, effort)
            pd.DataFrame(
                [
                    {"shard_index": "0", "status": "ok", "selected_rows": 200, "feature_rows": 2},
                    {"shard_index": "TOTAL", "status": "total", "selected_rows": 200, "feature_rows": 2},
                ]
            ).to_csv(effort_audit, index=False)
            expected = ExpectedCounts(shards=1, responses=200, unique_contexts=2)

            with self.assertRaisesRegex(FileNotFoundError, "PRODUCTION_COMPLETE"):
                validate_generation_handoff(run_root=run_root, marker=marker, expected=expected)

            marker.write_text("PASS\n", encoding="utf-8")
            validate_generation_handoff(run_root=run_root, marker=marker, expected=expected)

            wrong = ExpectedCounts(shards=1, responses=201, unique_contexts=2)
            with self.assertRaisesRegex(RuntimeError, "selected responses"):
                validate_generation_handoff(run_root=run_root, marker=marker, expected=wrong)

    def test_model_registry_contains_simple_adjusted_complex_and_nonlinear_models(self):
        specs = full79_model_specs()
        labels = {spec.model_label for spec in specs}
        formulas = {spec.model_id: spec.formula for spec in specs}

        self.assertTrue(any("simple age association" in label for label in labels))
        self.assertTrue(any("stable child identity" in label for label in labels))
        self.assertTrue(any("generated reference" in label for label in labels))
        self.assertTrue(any("age × response uncertainty" in label for label in labels))
        self.assertTrue(any("quadratic age" in label for label in labels))
        self.assertTrue(any("age bins" in label for label in labels))
        self.assertIn("C(child_id)", formulas["minus_generated_mean_m2_child_identity"])
        self.assertIn(
            "age_months_c:response_entropy_bits_c",
            formulas["minus_generated_mean_m7_age_by_response_uncertainty"],
        )
        self.assertNotIn("context_entropy_bits", "\n".join(formulas.values()))

    def test_controller_rejects_invalid_stage(self):
        result = subprocess.run(
            [sys.executable, str(SRC / "build_full79_qwen_route2_analysis.py"), "--stage", "nonsense"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_limited_model_registry_cannot_request_final_audit(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SRC / "build_full79_qwen_route2_analysis.py"),
                "--stage",
                "all",
                "--model-ids",
                "raw_child_words_m0_simple_age",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("smoke-only", result.stderr)

    def test_background_launcher_is_gated_and_never_regenerates_responses(self):
        launcher = ROOT / "scripts/run_full79_qwen_route2_background.sh"
        text = launcher.read_text(encoding="utf-8")

        self.assertIn("20260716_185726", text)
        self.assertIn("PRODUCTION_COMPLETE", text)
        self.assertIn("rsync -avhP", text)
        self.assertIn("nohup env", text)
        self.assertIn("--stage all", text)
        self.assertNotIn("submit_qwen_full79_production", text)
        self.assertNotIn("generate_response_entropy_qwen", text)

    def test_representative_smoke_uses_production_feature_join_and_fit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_root = root / "qwen"
            output = root / "analysis"
            wide = root / "wide.csv.gz"
            marker = run_root / "PRODUCTION_COMPLETE"
            rows, contexts = smoke_wide_rows()
            pd.DataFrame(rows).to_csv(wide, index=False)
            write_generation_run(run_root, contexts, samples_per_context=4)
            marker.write_text("PASS\n", encoding="utf-8")
            expected = ExpectedCounts(
                shards=1,
                responses=len(contexts) * 4,
                unique_contexts=len(contexts),
                children=4,
                datasets=4,
                eligible_rows=len(rows),
                pbm_children=2,
                other_children=2,
            )

            run_feature_stage(
                run_root=run_root,
                marker=marker,
                output_dir=output,
                compute_repo=ROOT.parent / "compute_surprisal_mila",
                expected=expected,
            )
            dataset = run_dataset_stage(
                input_wide=wide,
                run_root=run_root,
                marker=marker,
                output_dir=output,
                expected=expected,
                chunksize=17,
            )
            models = run_model_stage(
                output_dir=output,
                model_ids=[
                    "raw_child_words_m0_simple_age",
                    "minus_generated_mean_m2_child_identity",
                    "minus_generated_mean_m7_age_by_response_uncertainty",
                ],
            )

            self.assertEqual(dataset["scope_counts"]["all_79"]["children"], 4)
            self.assertEqual(models["attempted_fits"], 36)
            self.assertFalse(models["complete_registry"])
            self.assertTrue((output / "models/model_coefficients.csv").exists())


def wide_row(dataset, child, utterance_id, context, target, age, words):
    return {
        "dataset": dataset,
        "child_id": child,
        "child_key": f"{dataset}/{child}",
        "sample_group": "pbm_discovery" if dataset in {"Brown", "Manchester", "Providence"} else "non_pbm_confirmation",
        "session_id": "1",
        "age_months": str(age),
        "age_months_source": "scored_age_months",
        "age_bin": "024-029",
        "file": f"{child}/one.cha",
        "line_no": "1",
        "utt_id": "1",
        "utterance_id": utterance_id,
        "context_k3": context,
        "real_target_text": target,
        "real_nb_words": str(words),
        "real_nb_characters": str(len(target)),
        "real_k0_sum_bits": "4.0",
        "real_k0_mean_bits_per_token": "2.0",
        "real_k0_n_eval_tokens": "2",
        "real_k3_sum_bits": "3.0",
        "real_k3_mean_bits_per_token": "1.5",
        "real_k3_n_eval_tokens": "2",
        "real_context_gain_k3": "1.0",
    }


def write_feature_tables(entropy: Path, effort: Path) -> None:
    entropy_rows = []
    effort_rows = []
    for index, context in enumerate(["hello there", "look at that"]):
        cid = context_id(context)
        entropy_rows.append(
            {
                "setting_id": f"s{index}",
                "context_id": cid,
                "context_text": context,
                "prompt_variant": "QwenSystemNaturalistic",
                "temperature": "1.0",
                "selected_sample_count": "100",
                "valid_selected_count": "100",
                "invalid_selected_count": "0",
                "unique_response_count_valid_only": "10",
                "empirical_response_entropy_bits_valid_only": "3.0",
                "miller_madow_entropy_bits_valid_only": "3.1",
            }
        )
        effort_rows.append(
            {
                "setting_id": f"s{index}",
                "context_id": cid,
                "context_text": context,
                "prompt_variant": "QwenSystemNaturalistic",
                "temperature": "1.0",
                "valid_sample_words_mean": "2.0",
            }
        )
    pd.DataFrame(entropy_rows).to_csv(entropy, index=False)
    pd.DataFrame(effort_rows).to_csv(effort, index=False)


def smoke_wide_rows():
    rows = []
    contexts = []
    children = [
        ("Brown", "Adam"),
        ("Manchester", "Anne"),
        ("Belfast", "Barbara"),
        ("Wells", "Abigail"),
    ]
    for child_index, (dataset, child) in enumerate(children):
        for session in range(8):
            age = 18 + child_index * 2 + session * 3
            for utterance in range(2):
                context = f"context {dataset} {child} session {session} utterance {utterance}"
                target = "yes please" if utterance == 0 else "more red blocks"
                rows.append(
                    wide_row(
                        dataset,
                        child,
                        f"{dataset}-{child}-{session}-{utterance}",
                        context,
                        target,
                        age,
                        2 + utterance,
                    )
                )
                rows[-1]["session_id"] = str(session)
                rows[-1]["age_bin"] = "024-029" if age < 30 else "030-035"
                contexts.append(context)
    return rows, contexts


def write_generation_run(run_root: Path, contexts, *, samples_per_context: int) -> None:
    shard = run_root / "shard_outputs/shard_00000"
    merged = run_root / "merged"
    manifests = run_root / "manifests"
    shard.mkdir(parents=True)
    merged.mkdir(parents=True)
    manifests.mkdir(parents=True)
    pd.DataFrame([{"shard_index": 0}]).to_csv(manifests / "tasks.tsv", sep="\t", index=False)
    selected = []
    summaries = []
    entropy = []
    for index, context in enumerate(contexts):
        cid = context_id(context)
        setting = f"setting-{index}"
        for repetition in range(samples_per_context):
            selected.append(
                {
                    "setting_id": setting,
                    "context_id": cid,
                    "context_text": context,
                    "prompt_variant": "QwenSystemNaturalistic",
                    "temperature": "1.0",
                    "accepted": "1",
                    "sampled_response_text": "yes" if repetition % 2 == 0 else "more blocks please",
                }
            )
        summaries.append(
            {
                "setting_id": setting,
                "attempts": samples_per_context,
                "accepted_valid_samples": samples_per_context,
                "invalid_attempts": 0,
                "selected_samples": samples_per_context,
                "invalid_fallback_selected": 0,
                "reached_target_valid_samples": True,
                "exhausted_attempt_cap": False,
                "fallback_used": False,
                "rejection_rate": 0,
            }
        )
        entropy.append(
            {
                "setting_id": setting,
                "context_id": cid,
                "context_text": context,
                "prompt_variant": "QwenSystemNaturalistic",
                "temperature": "1.0",
                "selected_sample_count": samples_per_context,
                "valid_selected_count": samples_per_context,
                "invalid_selected_count": 0,
                "unique_response_count_valid_only": 2,
                "empirical_response_entropy_bits_valid_only": 1.0,
                "miller_madow_entropy_bits_valid_only": 1.1,
            }
        )
    pd.DataFrame(selected).to_csv(shard / "selected_samples.csv.gz", index=False)
    pd.DataFrame(summaries).to_csv(shard / "setting_summary.csv", index=False)
    pd.DataFrame(entropy).to_csv(merged / "context_response_entropy_features.csv.gz", index=False)


if __name__ == "__main__":
    unittest.main()
