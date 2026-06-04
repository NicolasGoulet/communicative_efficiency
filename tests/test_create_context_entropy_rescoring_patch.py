import csv
import gzip
import tempfile
import unittest
from pathlib import Path

import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from create_context_entropy_rescoring_patch import build_patch, context_id, normalize_context


class ContextEntropyRescoringPatchTests(unittest.TestCase):
    def write_missing_contexts(self, path: Path) -> None:
        rows = [
            {
                "context_col": "context_k1",
                "context_text": "  hello   there  ",
                "n_route1_rows": "2",
                "example_dataset": "Brown",
                "example_child_id": "Adam",
                "example_file": "Adam/example.cha",
                "example_line_no": "10",
                "example_context_k": "k1",
            },
            {
                "context_col": "context_k2",
                "context_text": "hello there",
                "n_route1_rows": "3",
                "example_dataset": "Brown",
                "example_child_id": "Adam",
                "example_file": "Adam/example.cha",
                "example_line_no": "11",
                "example_context_k": "k2",
            },
            {
                "context_col": "context_k3",
                "context_text": "different context",
                "n_route1_rows": "5",
                "example_dataset": "Providence",
                "example_child_id": "Naima",
                "example_file": "Naima/example.cha",
                "example_line_no": "20",
                "example_context_k": "k3",
            },
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_normalize_context_matches_entropy_scorer_contract(self):
        self.assertEqual(normalize_context("  hello   there\nfriend "), "hello there friend")
        self.assertEqual(normalize_context(None), "")
        self.assertEqual(normalize_context("nan"), "")

    def test_build_patch_writes_deduplicated_scorer_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            missing = tmp_path / "missing_context_entropy_contexts.csv"
            out_dir = tmp_path / "patch"
            self.write_missing_contexts(missing)

            summary = build_patch(missing_contexts_csv=missing, output_dir=out_dir)

            self.assertEqual(summary.missing_context_rows_read, 3)
            self.assertEqual(summary.nonempty_context_rows_read, 3)
            self.assertEqual(summary.manifest_rows_written, 2)
            self.assertEqual(summary.duplicate_context_id_rows_collapsed, 1)
            self.assertEqual(summary.total_route1_rows_represented, 10)

            manifest_path = out_dir / "context_entropy_patch_manifest.csv.gz"
            with gzip.open(manifest_path, "rt", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(
                list(rows[0]),
                ["manifest_row", "context_id", "context_col", "context_text"],
            )
            self.assertEqual([row["manifest_row"] for row in rows], ["0", "1"])
            self.assertEqual({row["context_text"] for row in rows}, {"hello there", "different context"})
            self.assertEqual(
                {row["context_id"] for row in rows},
                {context_id("hello there"), context_id("different context")},
            )

            self.assertTrue((out_dir / "context_entropy_patch_contexts_with_examples.csv").exists())
            self.assertTrue((out_dir / "README.md").exists())
            self.assertTrue(Path(summary.tarball).exists())


if __name__ == "__main__":
    unittest.main()
