import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_response_entropy_manifest import build_manifest, context_id, normalize_context
from src.attach_response_entropy_features import attach_response_entropy_features
from src.sample_context_responses import (
    append_rows,
    clean_generated_response,
    clean_generated_response_with_audit,
    completed_context_temperatures,
    format_prompt,
    resolve_model_source,
)
from src.summarize_response_entropy_samples import (
    canonical_response,
    empirical_entropy_bits,
    miller_madow_entropy_bits,
    summarize_samples,
)


class ResponseLevelContextEntropyTests(unittest.TestCase):
    def test_context_normalization_and_id_are_stable(self):
        self.assertEqual(normalize_context("  what   do you like ? "), "what do you like ?")
        self.assertEqual(context_id("what do you like ?"), context_id(" what  do you like ? "))

    def test_empirical_entropy_matches_known_counts(self):
        counts = {"riding a bike": 3, "reading a book": 1}

        entropy = empirical_entropy_bits(counts)

        expected = -(0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))
        self.assertAlmostEqual(entropy, expected)
        self.assertGreater(miller_madow_entropy_bits(entropy, unique_count=2, sample_count=4), entropy)

    def test_canonical_response_modes(self):
        self.assertEqual(canonical_response("  Riding   a Bike ", mode="exact"), "Riding a Bike")
        self.assertEqual(canonical_response("  Riding   a Bike ", mode="casefold"), "riding a bike")
        self.assertEqual(canonical_response("", mode="exact"), "<EMPTY_RESPONSE>")

    def test_prompt_format_and_boundary_cleaning(self):
        self.assertEqual(format_prompt("what do you like?", "Caregiver: {context}\nChild:"), "Caregiver: what do you like?\nChild:")
        self.assertEqual(clean_generated_response("riding a bike\nCaregiver: okay"), "riding a bike")
        cleaned, stopped, marker = clean_generated_response_with_audit("riding a bike\nCaregiver: okay")
        self.assertEqual(cleaned, "riding a bike")
        self.assertTrue(stopped)
        self.assertEqual(marker, "Caregiver:")

    def test_model_dir_none_uses_shared_huggingface_cache(self):
        self.assertEqual(resolve_model_source("mistral", None), ("mistral", None))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache_dir = root / "cache"
            cache_dir.mkdir()
            self.assertEqual(resolve_model_source("mistral", cache_dir), ("mistral", str(cache_dir)))
            snapshot = root / "snapshot"
            snapshot.mkdir()
            (snapshot / "config.json").write_text("{}", encoding="utf-8")
            self.assertEqual(resolve_model_source("mistral", snapshot), (str(snapshot), None))

    def test_response_sampler_appends_and_detects_complete_context_temperatures(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_csv = Path(tmp) / "samples.csv.gz"
            rows = [
                {
                    "context_id": "ctx1",
                    "manifest_row": "0",
                    "context_text": "what do you like",
                    "prompt_text": "Caregiver: what do you like\nChild:",
                    "temperature": 1.0,
                    "sample_index": sample_index,
                    "raw_generated_text": "bike",
                    "sampled_response_text": "bike",
                    "generated_token_count": 1,
                    "hit_max_new_tokens": 0,
                    "stopped_by_speaker_boundary": 0,
                    "speaker_boundary_marker": "",
                    "empty_response": 0,
                    "model_used": "toy",
                    "max_new_tokens": 24,
                    "top_p": 0.95,
                    "top_k": 0,
                    "seed_used": 1,
                }
                for sample_index in range(2)
            ]

            self.assertEqual(append_rows(output_csv, rows[:1]), 1)
            self.assertEqual(completed_context_temperatures(output_csv, samples_per_context=2), set())
            self.assertEqual(append_rows(output_csv, rows[1:]), 1)

            completed = completed_context_temperatures(output_csv, samples_per_context=2)

            self.assertEqual(completed, {("ctx1", 1.0)})
            self.assertEqual(len(pd.read_csv(output_csv)), 2)

    def test_build_manifest_filters_and_aggregates_duplicate_contexts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_csv = root / "route1.csv"
            output_csv = root / "manifest.csv"
            pd.DataFrame(
                [
                    {
                        "score_id": "s1",
                        "utterance_id": "u1",
                        "dataset": "Brown",
                        "child_id": "Adam",
                        "age_months": "27",
                        "age_bin": "024-029",
                        "role": "child",
                        "target_variant": "real",
                        "context_k": "k3",
                        "context_text": "what do you like",
                        "target_utterance_clean": "bike",
                        "nb_words": "1",
                    },
                    {
                        "score_id": "s2",
                        "utterance_id": "u2",
                        "dataset": "Brown",
                        "child_id": "Adam",
                        "age_months": "28",
                        "age_bin": "024-029",
                        "role": "child",
                        "target_variant": "real",
                        "context_k": "k3",
                        "context_text": " what  do you like ",
                        "target_utterance_clean": "book",
                        "nb_words": "1",
                    },
                    {
                        "score_id": "s3",
                        "utterance_id": "u3",
                        "dataset": "Brown",
                        "child_id": "Adam",
                        "age_months": "28",
                        "age_bin": "024-029",
                        "role": "child",
                        "target_variant": "random",
                        "context_k": "k3",
                        "context_text": "should be ignored",
                        "target_utterance_clean": "x",
                        "nb_words": "1",
                    },
                ]
            ).to_csv(input_csv, index=False)

            manifest = build_manifest(
                input_csv=input_csv,
                output_csv=output_csv,
                roles=["child"],
                target_variants=["real"],
                context_ks=["k3"],
                chunksize=2,
                min_context_words=1,
                sample_per_age_bin=None,
                max_contexts=None,
                seed=1,
            )

            self.assertEqual(len(manifest), 1)
            self.assertEqual(int(manifest["n_target_rows"].iloc[0]), 2)
            self.assertEqual(manifest["context_text"].iloc[0], "what do you like")

    def test_summarize_samples_writes_entropy_and_expected_lengths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            samples_csv = root / "samples.csv"
            output_csv = root / "summary.csv"
            pd.DataFrame(
                [
                    {"context_id": "c1", "temperature": "1.0", "sampled_response_text": "riding a bike", "prompt_text": "p"},
                    {"context_id": "c1", "temperature": "1.0", "sampled_response_text": "riding a bike", "prompt_text": "p"},
                    {"context_id": "c1", "temperature": "1.0", "sampled_response_text": "reading", "prompt_text": "p"},
                    {"context_id": "c1", "temperature": "1.0", "sampled_response_text": "reading", "prompt_text": "p"},
                ]
            ).to_csv(samples_csv, index=False)

            summary = summarize_samples(samples_csv=samples_csv, output_csv=output_csv, normalization="casefold", top_n=5)

            self.assertEqual(len(summary), 1)
            self.assertAlmostEqual(float(summary["response_entropy_mle_bits"].iloc[0]), 1.0)
            self.assertEqual(int(summary["unique_response_count"].iloc[0]), 2)
            self.assertAlmostEqual(float(summary["mean_sample_word_count"].iloc[0]), 2.0)

    def test_attach_response_entropy_features_preserves_rows_and_marks_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route1_csv = root / "route1.csv"
            features_csv = root / "features.csv"
            output_csv = root / "joined.csv"
            matching_context = "what do you want"
            pd.DataFrame(
                [
                    {"score_id": "s1", "context_text": matching_context, "target_utterance_clean": "juice"},
                    {"score_id": "s2", "context_text": "unseen context", "target_utterance_clean": "ball"},
                ]
            ).to_csv(route1_csv, index=False)
            pd.DataFrame(
                [
                    {
                        "context_id": context_id(matching_context),
                        "temperature": "1.0",
                        "sample_count": "100",
                        "unique_response_count": "12",
                        "response_entropy_mle_bits": "3.1",
                        "response_entropy_miller_madow_bits": "3.2",
                        "response_entropy_normalized_by_sample_cap": "0.47",
                        "response_evenness_observed_types": "0.86",
                        "top_response_probability": "0.18",
                        "mean_sample_word_count": "2.4",
                        "mean_sample_morpheme_count_surface": "2.8",
                        "mean_sample_syllable_count_pkg": "3.2",
                        "model_used": "toy",
                        "top_p": "0.95",
                        "max_new_tokens": "24",
                    }
                ]
            ).to_csv(features_csv, index=False)

            summary = attach_response_entropy_features(
                input_csv=route1_csv,
                features_csv=features_csv,
                output_csv=output_csv,
                temperature=1.0,
                chunksize=1,
            )
            joined = pd.read_csv(output_csv)

            self.assertEqual(summary, {"rows": 2, "matched_rows": 1, "unmatched_rows": 1})
            self.assertEqual(len(joined), 2)
            self.assertTrue(bool(joined.loc[joined["score_id"] == "s1", "response_entropy_context_matched"].iloc[0]))
            self.assertFalse(bool(joined.loc[joined["score_id"] == "s2", "response_entropy_context_matched"].iloc[0]))


if __name__ == "__main__":
    unittest.main()
