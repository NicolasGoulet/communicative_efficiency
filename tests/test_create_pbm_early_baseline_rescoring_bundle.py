import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from create_pbm_early_baseline_rescoring_bundle import (  # noqa: E402
    OUTPUT_COLUMNS,
    age_is_in_floor_range,
    create_bundle,
    read_variant_rows,
)


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class TestCreatePbmEarlyBaselineRescoringBundle(unittest.TestCase):
    def test_age_filter_uses_floor_month_and_inclusive_bounds(self):
        """The rescore slice is floor(age_months) 006 through 023, not raw age <= 23.0."""
        self.assertTrue(age_is_in_floor_range("6.0", min_month=6, max_month=23))
        self.assertTrue(age_is_in_floor_range("23.99", min_month=6, max_month=23))
        self.assertFalse(age_is_in_floor_range("5.99", min_month=6, max_month=23))
        self.assertFalse(age_is_in_floor_range("24.0", min_month=6, max_month=23))
        self.assertFalse(age_is_in_floor_range("", min_month=6, max_month=23))

    def test_read_variant_rows_keeps_only_early_nonempty_generated_targets(self):
        """Only the requested generated baseline column is exported for early child ages."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chi.surprisal_scoring.csv"
            fieldnames = [
                "dataset",
                "child_id",
                "session_id",
                "age_months",
                "file",
                "line_no",
                "utt_id",
                "context_k1",
                "context_k2",
                "context_k3",
                "random_model_utterance_bin6",
                "unigram_model_utterance_bin6",
                "bigram_model_utterance_bin6",
                "trigram_model_utterance_bin6",
            ]
            write_csv(
                path,
                [
                    {
                        "dataset": "Brown",
                        "child_id": "Eve",
                        "session_id": "1",
                        "age_months": "23.9",
                        "file": "eve.cha",
                        "line_no": "10",
                        "utt_id": "3",
                        "context_k1": "what now ?",
                        "context_k2": "look . what now ?",
                        "context_k3": "hi . look . what now ?",
                        "random_model_utterance_bin6": "toy go .",
                    },
                    {
                        "dataset": "Brown",
                        "child_id": "Eve",
                        "session_id": "1",
                        "age_months": "24.0",
                        "file": "eve.cha",
                        "line_no": "11",
                        "utt_id": "4",
                        "context_k1": "later .",
                        "random_model_utterance_bin6": "outside .",
                    },
                    {
                        "dataset": "Brown",
                        "child_id": "Eve",
                        "session_id": "1",
                        "age_months": "10.0",
                        "file": "eve.cha",
                        "line_no": "12",
                        "utt_id": "5",
                        "context_k1": "empty target .",
                        "random_model_utterance_bin6": "",
                    },
                ],
                fieldnames,
            )

            rows = read_variant_rows(
                path,
                dataset="Brown",
                child_id="Eve",
                variant="random",
                min_month=6,
                max_month=23,
            )

            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["subset"], "random_chi/bin6")
            self.assertEqual(row["age_floor_month"], "23")
            self.assertEqual(row["age_bin_rescore"], "006-023")
            self.assertEqual(row["source_row"], "2")
            self.assertEqual(row["source_text_col"], "random_model_utterance_bin6")
            self.assertEqual(row["utterance_for_scoring"], "toy go .")
            self.assertEqual(row["word_count"], "3")
            self.assertEqual(row["morph_count"], "3")

    def test_create_bundle_writes_shards_manifest_and_tarball(self):
        """The bundle is scorer-ready: exact headers, sharded subsets, and tarball."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_root = tmp_path / "input"
            output_root = tmp_path / "bundle"
            tar_gz = tmp_path / "bundle.tar.gz"

            fieldnames = [
                "dataset",
                "child_id",
                "session_id",
                "age_months",
                "file",
                "line_no",
                "utt_id",
                "context_k1",
                "context_k2",
                "context_k3",
                "random_model_utterance_bin6",
                "unigram_model_utterance_bin6",
                "bigram_model_utterance_bin6",
                "trigram_model_utterance_bin6",
            ]
            rows = [
                {
                    "dataset": "Brown",
                    "child_id": "Adam",
                    "session_id": "1",
                    "age_months": "7.2",
                    "file": "adam.cha",
                    "line_no": str(i + 1),
                    "utt_id": str(i + 1),
                    "context_k1": "hello .",
                    "random_model_utterance_bin6": f"r{i}",
                    "unigram_model_utterance_bin6": f"u{i}",
                }
                for i in range(3)
            ]
            write_csv(input_root / "Brown" / "Adam" / "chi.surprisal_scoring.csv", rows, fieldnames)

            summary = create_bundle(
                input_root=input_root,
                output_root=output_root,
                datasets=["Brown"],
                variants=["random", "unigram"],
                min_month=6,
                max_month=23,
                chunk_size=2,
                overwrite=True,
                tar_gz=tar_gz,
            )

            self.assertEqual(summary["n_child_files"], 1)
            self.assertEqual(summary["n_rows"], 6)
            self.assertEqual(summary["n_shards"], 4)
            self.assertTrue(tar_gz.exists())

            with (output_root / "manifest.csv").open(newline="", encoding="utf-8") as handle:
                manifest = list(csv.DictReader(handle))
            self.assertEqual([row["subset"] for row in manifest], ["random_chi/bin6", "unigram_chi/bin6"])
            self.assertEqual([row["n_rows"] for row in manifest], ["3", "3"])

            shard = output_root / "random_chi" / "bin6" / "shards" / "random_chi__bin6__part00001.csv"
            with shard.open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                header = next(reader)
                data_rows = list(reader)
            self.assertEqual(header, OUTPUT_COLUMNS)
            self.assertEqual(len(data_rows), 2)
            self.assertEqual(len(data_rows[0]), len(header))

            payload = json.loads(manifest[0]["shards"])
            self.assertEqual(payload[0], "random_chi/bin6/shards/random_chi__bin6__part00001.csv")


if __name__ == "__main__":
    unittest.main()
