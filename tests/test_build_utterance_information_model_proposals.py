import gzip
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_utterance_information_model_proposals import (
    count_csv_data_rows,
    parse_scored_file,
    source_tree_audit,
    stratified_sample,
)
from src.build_size_controlled_meeting_plots import (
    comparison_frames,
    summarize_exact_effort_frame,
    word_size_bin,
)


class ModelProposalBuilderTests(unittest.TestCase):
    def test_count_csv_data_rows_handles_plain_and_gzip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plain = root / "plain.csv"
            plain.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
            zipped = root / "zipped.csv.gz"
            with gzip.open(zipped, "wt", encoding="utf-8") as handle:
                handle.write("a,b\n1,2\n")

            self.assertEqual(count_csv_data_rows(plain), 2)
            self.assertEqual(count_csv_data_rows(zipped), 1)

    def test_parse_scored_file_extracts_context_role_and_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = (
                root
                / "WITH_context"
                / "k3"
                / "mistralai__Mistral-7B-v0.3"
                / "Brown"
                / "Adam"
                / "chi.surprisal_scoring__trigram.scored.csv"
            )
            path.parent.mkdir(parents=True)
            path.write_text("trigram_model_utterance_bin6,sum_bits\nhi,1.0\nthere,2.0\n", encoding="utf-8")

            parsed = parse_scored_file(path, root)

            self.assertEqual(parsed["dataset"], "Brown")
            self.assertEqual(parsed["child_id"], "Adam")
            self.assertEqual(parsed["role"], "child")
            self.assertEqual(parsed["target_variant"], "trigram")
            self.assertEqual(parsed["context_k"], "k3")
            self.assertEqual(parsed["source_rows"], 2)
            self.assertEqual(parsed["raw_rows"], 2)

    def test_source_tree_audit_detects_matched_and_mismatched_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scored = (
                root
                / "scored"
                / "WITHOUT_context"
                / "mistralai__Mistral-7B-v0.3"
                / "Brown"
                / "Adam"
                / "chi.surprisal_scoring__real.scored.csv"
            )
            scored.parent.mkdir(parents=True)
            scored.write_text("chi_utterance_clean,sum_bits\nhi,1.0\nthere,2.0\n", encoding="utf-8")
            entropy = root / "entropy"
            entropy.mkdir()
            with gzip.open(entropy / "context_entropy_features.csv.gz", "wt", encoding="utf-8") as handle:
                handle.write("context_id,llm_next_entropy_bits\nabc,1.2\n")
            with gzip.open(entropy / "context_entropy_manifest.csv.gz", "wt", encoding="utf-8") as handle:
                handle.write("context_id\nabc\n")

            long_counts = pd.DataFrame(
                [
                    {
                        "dataset": "Brown",
                        "role": "child",
                        "target_variant": "real",
                        "context_k": "k0",
                        "long_rows": 2,
                    }
                ]
            )

            audit, comparison, entropy_audit = source_tree_audit(
                scored_tree=root / "scored",
                context_entropy_dir=entropy,
                long_counts=long_counts,
                output_dir=root / "out",
            )

            self.assertTrue(comparison["status"].eq("matched").all())
            self.assertEqual(int(audit.loc[audit["check"].eq("source_vs_long_mismatched_groups"), "value"].iloc[0]), 0)
            self.assertEqual(int(entropy_audit["rows"].sum()), 2)

    def test_stratified_sample_keeps_at_most_requested_rows_per_group(self):
        frame = pd.DataFrame({"group": ["a"] * 5 + ["b"] * 2, "value": range(7)})

        sample = stratified_sample(frame, ["group"], 3)

        self.assertLessEqual(sample[sample["group"].eq("a")].shape[0], 3)
        self.assertEqual(sample[sample["group"].eq("b")].shape[0], 2)

    def test_word_size_bin_keeps_only_requested_size_ranges(self):
        self.assertEqual(word_size_bin("1"), "1-4 words")
        self.assertEqual(word_size_bin("4"), "1-4 words")
        self.assertEqual(word_size_bin("5"), "5-8 words")
        self.assertEqual(word_size_bin("8"), "5-8 words")
        self.assertIsNone(word_size_bin("0"))
        self.assertIsNone(word_size_bin("9"))
        self.assertIsNone(word_size_bin("not-a-number"))

    def test_comparison_frames_selects_k3_requested_groups_and_size_bins(self):
        frame = pd.DataFrame(
            [
                {"score_id": "1", "age_bin": "024-029", "role": "child", "target_variant": "real", "context_k": "k3", "nb_words": "4"},
                {"score_id": "2", "age_bin": "024-029", "role": "child", "target_variant": "random", "context_k": "k3", "nb_words": "5"},
                {"score_id": "3", "age_bin": "024-029", "role": "child", "target_variant": "trigram", "context_k": "k3", "nb_words": "8"},
                {"score_id": "4", "age_bin": "024-029", "role": "caretaker", "target_variant": "caretaker", "context_k": "k3", "nb_words": "2"},
                {"score_id": "5", "age_bin": "024-029", "role": "child", "target_variant": "bigram", "context_k": "k3", "nb_words": "2"},
                {"score_id": "6", "age_bin": "024-029", "role": "child", "target_variant": "real", "context_k": "k2", "nb_words": "2"},
                {"score_id": "7", "age_bin": "024-029", "role": "child", "target_variant": "real", "context_k": "k3", "nb_words": "9"},
            ]
        )

        baseline, speaker = comparison_frames(frame)

        self.assertEqual(baseline["score_id"].tolist(), ["1", "2", "3"])
        self.assertEqual(speaker["score_id"].tolist(), ["1", "4"])
        self.assertEqual(baseline["comparison"].tolist(), ["Real child", "Random", "Trigram"])
        self.assertEqual(speaker["comparison"].tolist(), ["Child", "Caretaker"])
        self.assertEqual(baseline["size_bin"].tolist(), ["1-4 words", "5-8 words", "5-8 words"])

    def test_summarize_exact_effort_frame_uses_each_effort_count_column(self):
        frame = pd.DataFrame(
            {
                "comparison": ["Real child", "Real child"],
                "age_bin": ["024-029", "024-029"],
                "nb_words": [2, 3],
                "nb_morphemes": [3, 4],
                "nb_syllables_cmu_or_pkg": [4, 5],
                "nb_syllables_pkg": [4, 6],
                "nb_phonemes": [7, 8],
                "bits_per_word": [10.0, 12.0],
                "bits_per_morpheme": [6.0, 7.0],
                "bits_per_syllable_cmu_or_pkg": [5.0, 5.5],
                "bits_per_syllable_pkg": [5.0, 4.5],
                "bits_per_phoneme": [2.0, 2.2],
            }
        )

        summary = summarize_exact_effort_frame(frame)

        self.assertIn("nb_words", set(summary["effort_col"]))
        self.assertIn("nb_morphemes", set(summary["effort_col"]))
        self.assertIn("nb_syllables_cmu_or_pkg", set(summary["effort_col"]))
        self.assertIn("nb_syllables_pkg", set(summary["effort_col"]))
        self.assertIn("nb_phonemes", set(summary["effort_col"]))
        morpheme = summary[(summary["effort_col"].eq("nb_morphemes")) & (summary["effort_value"].eq(3))]
        self.assertEqual(morpheme["mean"].iloc[0], 6.0)


if __name__ == "__main__":
    unittest.main()
