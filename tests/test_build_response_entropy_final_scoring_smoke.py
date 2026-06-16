import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_response_entropy_manifest import context_id
from src.build_response_entropy_final_scoring_smoke import (
    compute_entropy_features,
    compute_stability_rows,
    empirical_entropy_bits,
    join_entropy_to_route2_smoke,
    miller_madow_entropy_bits,
    normalize_response_type,
    response_entropy_summary,
    run_scoring_smoke,
    sample_size_rank_correlations,
    split_half_reliability_summary,
)


class ResponseEntropyFinalScoringSmokeTests(unittest.TestCase):
    def test_response_normalization_modes_are_explicit(self):
        self.assertEqual(normalize_response_type("  Riding   a Bike! ", mode="exact"), "Riding a Bike!")
        self.assertEqual(normalize_response_type("  Riding   a Bike! ", mode="casefold"), "riding a bike!")
        self.assertEqual(
            normalize_response_type("  Riding   a Bike! ", mode="casefold_punct_stripped"),
            "riding a bike",
        )
        self.assertEqual(normalize_response_type("", mode="casefold"), "<EMPTY_RESPONSE>")

    def test_entropy_miller_madow_and_top_probability(self):
        counts = {"yes": 3, "no": 1}
        entropy = empirical_entropy_bits(counts)
        expected = -(0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))

        summary = response_entropy_summary(["yes", "yes", "yes", "no"], normalization="casefold")

        self.assertAlmostEqual(entropy, expected)
        self.assertGreater(miller_madow_entropy_bits(entropy, unique_count=2, sample_count=4), entropy)
        self.assertAlmostEqual(float(summary["top_response_probability"]), 0.75)
        self.assertEqual(int(summary["unique_response_count"]), 2)

    def test_stability_split_half_and_downsampling(self):
        accepted = toy_accepted_frame(
            [
                ("ctx1", "Caregiver", 0.5, ["yes", "yes", "no", "no"]),
                ("ctx2", "Caregiver", 0.5, ["ball", "ball", "toy", "toy"]),
                ("ctx1", "Caregiver", 0.7, ["yes", "no", "maybe", "book"]),
                ("ctx2", "Caregiver", 0.7, ["ball", "toy", "book", "car"]),
            ]
        )

        stability = compute_stability_rows(accepted, sample_sizes=[2, 4], normalization="casefold")
        sample_corr = sample_size_rank_correlations(stability, sample_sizes=[2, 4])
        split_half = split_half_reliability_summary(stability)

        self.assertIn("entropy_first_2_bits", stability.columns)
        self.assertIn("split_half_abs_diff_bits", stability.columns)
        self.assertFalse(sample_corr.empty)
        self.assertFalse(split_half.empty)
        self.assertTrue((stability["split_half_first_n"] == 2).all())

    def test_context_join_audit_tracks_missing_and_duplicate_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            features = toy_feature_frame("same words.")
            route1 = root / "route1.csv"
            write_route1(route1)
            out = root / "joined.csv.gz"

            audit, summary = join_entropy_to_route2_smoke(
                route1_input=route1,
                features=features,
                output_csv=out,
                chunksize=2,
                max_output_rows=None,
            )
            joined = pd.read_csv(out)
            duplicate = audit[audit["audit_type"].eq("duplicate_context_window_check")]

            self.assertEqual(summary["eligible_real_child_rows"], 3)
            self.assertEqual(summary["matched_real_child_rows"], 2)
            self.assertEqual(summary["missing_real_child_rows"], 1)
            self.assertEqual(len(joined), 2)
            self.assertEqual(int(duplicate["observed_context_k_count"].max()), 2)
            self.assertTrue(bool(duplicate["deduplicated_by_text"].iloc[0]))

    def test_full_smoke_writes_required_outputs_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "generation"
            route1 = root / "route1.csv"
            write_generation_artifacts(input_dir)
            write_route1(route1)

            paths = run_scoring_smoke(
                input_dir=input_dir,
                route1_input=route1,
                output_dir=root / "out",
                fig_dir=root / "figs",
                report_md=root / "report.md",
                report_html=root / "report.html",
                normalization="casefold",
                sample_sizes=[2, 4],
                chunksize=2,
            )

            self.assertTrue(paths["features"].exists())
            self.assertTrue(paths["stability"].exists())
            self.assertTrue(paths["join_audit"].exists())
            self.assertTrue(paths["temperature_correlations"].exists())
            self.assertTrue(paths["prompt_correlations"].exists())
            self.assertTrue(paths["analysis_smoke"].exists())
            self.assertTrue(paths["model_summary"].exists())
            self.assertTrue(paths["manual_examples"].exists())
            self.assertTrue(paths["report_html"].exists())
            report = paths["report_md"].read_text(encoding="utf-8")
            self.assertIn("What Was Generated Versus What Was Scored", report)
            self.assertIn("Decision Output", report)


def toy_accepted_frame(specs: list[tuple[str, str, float, list[str]]]) -> pd.DataFrame:
    rows = []
    for context_id_value, prompt_variant, temperature, responses in specs:
        for sample_index, response in enumerate(responses):
            rows.append(
                {
                    "setting_id": f"{context_id_value}::{prompt_variant}::T{temperature:g}",
                    "context_id": context_id_value,
                    "context_text": "same words.",
                    "context_word_count": "2",
                    "context_length_bucket": "02_two_to_four",
                    "prompt_variant": prompt_variant,
                    "temperature": str(temperature),
                    "temperature_num": temperature,
                    "sample_index": str(sample_index),
                    "sample_index_num": sample_index,
                    "attempt_index": str(sample_index),
                    "attempt_index_num": sample_index,
                    "sampled_response_text": response,
                    "quality_flags": "",
                }
            )
    return pd.DataFrame(rows)


def toy_feature_frame(context: str) -> pd.DataFrame:
    accepted = toy_accepted_frame([(context_id(context), "Caregiver", 0.5, ["yes", "yes", "no", "maybe"])])
    attempts = accepted.copy()
    attempts["accepted"] = "1"
    attempts["accepted_int"] = 1
    rejections = pd.DataFrame(
        [
            {
                "setting_id": f"{context_id(context)}::Caregiver::T0.5",
                "context_id": context_id(context),
                "prompt_variant": "Caregiver",
                "temperature": "0.5",
                "temperature_num": 0.5,
                "attempts": "4",
                "accepted_samples": "4",
                "rejected_attempts": "0",
                "rejection_rate": "0",
                "target_accepted_samples": "4",
                "max_attempts_per_setting": "8",
                "reached_target": "True",
            }
        ]
    )
    quality = pd.DataFrame(
        [
            {
                "setting_id": f"{context_id(context)}::Caregiver::T0.5",
                "context_id": context_id(context),
                "prompt_variant": "Caregiver",
                "temperature": "0.5",
                "possible_context_copy_attempt_rate": "0",
                "possible_context_copy_accepted_rate": "0",
            }
        ]
    )
    return compute_entropy_features(
        accepted=accepted,
        attempts=attempts,
        rejections=rejections,
        quality=quality,
        normalization="casefold",
    )


def write_generation_artifacts(input_dir: Path) -> None:
    input_dir.mkdir(parents=True)
    context = "same words."
    cid = context_id(context)
    accepted_rows = []
    attempt_rows = []
    settings = [
        ("Caregiver", 0.5, ["yes", "yes", "no", "maybe"]),
        ("Caregiver", 0.7, ["yes", "no", "maybe", "book"]),
        ("Parent", 0.5, ["yes", "yes", "yes", "no"]),
        ("Parent", 0.7, ["ball", "toy", "book", "car"]),
    ]
    for prompt_variant, temperature, responses in settings:
        setting_id = f"{cid}::{prompt_variant}::T{temperature:g}"
        for sample_index, response in enumerate(responses):
            row = {
                "setting_id": setting_id,
                "context_id": cid,
                "context_text": context,
                "context_word_count": "2",
                "context_length_bucket": "02_two_to_four",
                "prompt_variant": prompt_variant,
                "prompt_template": f"{prompt_variant}: {{context}}\nChild:",
                "prompt_text": f"{prompt_variant}: {context}\nChild:",
                "temperature": str(temperature),
                "sample_index": str(sample_index),
                "attempt_index": str(sample_index),
                "quality_flags": "",
                "sampled_response_text": response,
                "raw_generated_text": response + "\n",
                "generated_token_count": "1",
                "hit_max_new_tokens": "0",
                "stopped_by_end_of_turn": "1",
                "model_used": "toy",
                "max_new_tokens": "12",
                "top_p": "0.95",
                "top_k": "0",
                "seed_used": "1",
            }
            accepted_rows.append(row)
            attempt_rows.append({**row, "accepted": "1", "rejection_reason": "", "target_accepted_samples": "4", "max_attempts_per_setting": "8"})
    pd.DataFrame(accepted_rows).to_csv(input_dir / "accepted_samples.csv.gz", index=False, compression="gzip")
    pd.DataFrame(attempt_rows).to_csv(input_dir / "all_attempts.csv.gz", index=False, compression="gzip")

    rejection_rows = []
    quality_rows = []
    for prompt_variant, temperature, responses in settings:
        setting_id = f"{cid}::{prompt_variant}::T{temperature:g}"
        rejection_rows.append(
            {
                "setting_id": setting_id,
                "context_id": cid,
                "prompt_variant": prompt_variant,
                "temperature": str(temperature),
                "attempts": str(len(responses)),
                "accepted_samples": str(len(responses)),
                "rejected_attempts": "0",
                "rejection_rate": "0",
                "target_accepted_samples": "4",
                "max_attempts_per_setting": "8",
                "reached_target": "True",
            }
        )
        quality_rows.append(
            {
                "setting_id": setting_id,
                "context_id": cid,
                "prompt_variant": prompt_variant,
                "temperature": str(temperature),
                "attempts": str(len(responses)),
                "accepted_samples": str(len(responses)),
                "possible_context_copy_attempt_rate": "0",
                "possible_context_copy_accepted_rate": "0",
            }
        )
    pd.DataFrame(rejection_rows).to_csv(input_dir / "rejection_summary_by_setting.csv", index=False)
    pd.DataFrame(quality_rows).to_csv(input_dir / "quality_flags_by_setting.csv", index=False)
    pd.DataFrame(
        [
            {
                "smoke_manifest_row": "0",
                "context_id": cid,
                "context_text": context,
                "context_word_count": "2",
                "prompt_variant": "Caregiver",
                "temperatures": "0.5,0.7",
            }
        ]
    ).to_csv(input_dir / "smoke_manifest.csv", index=False)


def write_route1(path: Path) -> None:
    pd.DataFrame(
        [
            route1_row("s1", "k1", "same words.", "yes"),
            route1_row("s2", "k2", "same words.", "no"),
            route1_row("s3", "k3", "missing words.", "ball"),
        ]
    ).to_csv(path, index=False)


def route1_row(score_id: str, context_k: str, context: str, target: str) -> dict[str, str]:
    return {
        "score_id": score_id,
        "utterance_id": score_id,
        "dataset": "Toy",
        "child_id": "Ada",
        "source_group": "Toy",
        "session_id": "1",
        "age_months": "30",
        "age_bin": "030-035",
        "file": "Ada/030000.cha",
        "line_no": "1",
        "utt_id": score_id,
        "speaker": "CHI",
        "role": "child",
        "target_variant": "real",
        "context_k": context_k,
        "context_col_used": f"context_{context_k}",
        "context_text": context,
        "target_utterance_clean": target,
        "nb_words": "1",
        "nb_morphemes": "1",
        "nb_syllables_cmu_or_pkg": "1",
        "nb_syllables_pkg": "1",
        "nb_phonemes": "3",
    }


if __name__ == "__main__":
    unittest.main()
