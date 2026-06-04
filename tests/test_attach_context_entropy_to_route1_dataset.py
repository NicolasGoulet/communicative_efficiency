import csv
import gzip
import tempfile
import unittest
from pathlib import Path

import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from attach_context_entropy_to_route1_dataset import (
    ENTROPY_OUTPUT_COLUMNS,
    attach_context_entropy,
    load_entropy_lookup,
    load_entropy_lookups,
)


class TestAttachContextEntropyToRoute1Dataset(unittest.TestCase):
    def test_load_entropy_lookup_uses_context_column_and_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            entropy = Path(tmp) / "entropy.csv.gz"
            write_entropy_features(
                entropy,
                [
                    {
                        "context_col": "context_k1",
                        "context_text": "hello there.",
                        "context_id": "abc",
                        "llm_next_entropy_bits": "4.5",
                    }
                ],
            )

            lookup, counts = load_entropy_lookup(entropy)

        self.assertEqual(counts["rows_read"], 1)
        self.assertEqual(counts["keys"], 1)
        self.assertEqual(lookup[("context_k1", "hello there.")]["llm_next_entropy_bits"], "4.5")

    def test_attach_context_entropy_matches_child_rows_and_blanks_k0_and_caretakers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route1 = root / "route1.csv"
            entropy = root / "entropy.csv.gz"
            output = root / "out.csv.gz"
            audit = root / "audit.csv"
            write_route1_rows(
                route1,
                [
                    route1_row("child", "k1", "context_k1", "hello there."),
                    route1_row("child", "k0", "", ""),
                    route1_row("caretaker", "k1", "context_k1", "hello there."),
                ],
            )
            write_entropy_features(
                entropy,
                [
                    {
                        "context_col": "context_k1",
                        "context_text": "hello there.",
                        "context_id": "abc",
                        "context_token_count": "3",
                        "llm_next_entropy_bits": "4.5",
                        "llm_next_top1_prob": "0.2",
                    }
                ],
            )

            result = attach_context_entropy(
                input_csv=route1,
                entropy_features_csv=entropy,
                output_csv=output,
                audit_csv=audit,
            )
            rows = read_csv_any(output)
            audit_rows = read_csv_any(audit)

        self.assertEqual(result.rows_written, 3)
        self.assertEqual(rows[0]["context_entropy_join_status"], "matched")
        self.assertEqual(rows[0]["context_entropy_bits"], "4.5")
        self.assertEqual(rows[0]["context_entropy_context_id"], "abc")
        self.assertEqual(rows[0]["context_entropy_token_count"], "3")
        self.assertEqual(rows[1]["context_entropy_join_status"], "no_context_k0")
        self.assertEqual(rows[1]["context_entropy_bits"], "")
        self.assertEqual(rows[2]["context_entropy_join_status"], "not_applicable_caretaker")
        self.assertEqual(rows[2]["context_entropy_bits"], "")
        self.assertTrue(set(ENTROPY_OUTPUT_COLUMNS).issubset(rows[0].keys()))
        self.assertEqual(audit_rows[0]["matched_child_context_rows"], "1")
        self.assertEqual(audit_rows[0]["matched_child_context_rows_exact"], "1")
        self.assertEqual(audit_rows[0]["matched_child_context_rows_text_fallback"], "0")
        self.assertEqual(audit_rows[0]["k0_child_rows"], "1")
        self.assertEqual(audit_rows[0]["not_applicable_caretaker_rows"], "1")

    def test_attach_context_entropy_reuses_same_text_across_context_window_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route1 = root / "route1.csv"
            entropy = root / "entropy.csv.gz"
            output = root / "out.csv"
            audit = root / "audit.csv"
            write_route1_rows(route1, [route1_row("child", "k2", "context_k2", "same words.")])
            write_entropy_features(
                entropy,
                [
                    {
                        "context_col": "context_k1",
                        "context_text": "same words.",
                        "context_id": "text-id",
                        "llm_next_entropy_bits": "3.25",
                    }
                ],
            )

            result = attach_context_entropy(
                input_csv=route1,
                entropy_features_csv=entropy,
                output_csv=output,
                audit_csv=audit,
            )
            rows = read_csv_any(output)

        self.assertEqual(result.matched_child_context_rows, 1)
        self.assertEqual(result.matched_child_context_rows_exact, 0)
        self.assertEqual(result.matched_child_context_rows_text_fallback, 1)
        self.assertEqual(rows[0]["context_entropy_join_status"], "matched_text_fallback")
        self.assertEqual(rows[0]["context_entropy_bits"], "3.25")

    def test_strict_mode_rejects_unmatched_child_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route1 = root / "route1.csv"
            entropy = root / "entropy.csv.gz"
            output = root / "out.csv"
            audit = root / "audit.csv"
            write_route1_rows(route1, [route1_row("child", "k1", "context_k1", "not scored.")])
            write_entropy_features(
                entropy,
                [
                    {
                        "context_col": "context_k1",
                        "context_text": "other context.",
                        "context_id": "abc",
                        "llm_next_entropy_bits": "4.5",
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "could not be matched"):
                attach_context_entropy(
                    input_csv=route1,
                    entropy_features_csv=entropy,
                    output_csv=output,
                    audit_csv=audit,
                )

        self.assertFalse(output.exists())
        self.assertFalse(audit.exists())

    def test_load_entropy_lookups_has_text_only_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            entropy = Path(tmp) / "entropy.csv.gz"
            write_entropy_features(
                entropy,
                [
                    {
                        "context_col": "context_k3",
                        "context_text": "shared.",
                        "context_id": "shared",
                        "llm_next_entropy_bits": "7",
                    }
                ],
            )

            exact, text, counts = load_entropy_lookups(entropy)

        self.assertIn(("context_k3", "shared."), exact)
        self.assertIn("shared.", text)
        self.assertEqual(counts["text_keys"], 1)

    def test_allow_missing_child_contexts_publishes_audited_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route1 = root / "route1.csv"
            entropy = root / "entropy.csv.gz"
            output = root / "out.csv"
            audit = root / "audit.csv"
            write_route1_rows(route1, [route1_row("child", "k1", "context_k1", "not scored.")])
            write_entropy_features(entropy, [])

            result = attach_context_entropy(
                input_csv=route1,
                entropy_features_csv=entropy,
                output_csv=output,
                audit_csv=audit,
                strict=False,
            )
            rows = read_csv_any(output)

        self.assertEqual(result.missing_child_context_rows, 1)
        self.assertEqual(rows[0]["context_entropy_join_status"], "missing_entropy")


def route1_row(role: str, context_k: str, context_col: str, context_text: str) -> dict[str, str]:
    return {
        "score_source": "mistral",
        "score_id": f"{role}-{context_k}",
        "utterance_id": f"utt-{role}",
        "role": role,
        "context_k": context_k,
        "context_col_used": context_col,
        "context_text": context_text,
        "target_utterance_clean": "target.",
    }


def write_route1_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "score_source",
        "score_id",
        "utterance_id",
        "role",
        "context_k",
        "context_col_used",
        "context_text",
        "target_utterance_clean",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_entropy_features(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "manifest_row",
        "context_id",
        "context_col",
        "context_text",
        "context_token_count",
        "llm_next_entropy_bits",
        "llm_next_top1_prob",
        "llm_next_top5_mass",
        "llm_next_top10_mass",
        "llm_next_top50_mass",
        "llm_next_argmax_bits",
        "model_used",
        "dtype_used",
        "max_length_used",
        "seed_used",
    ]
    with gzip.open(path, "wt", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for i, row in enumerate(rows):
            complete = {field: "" for field in fieldnames}
            complete.update(row)
            complete["manifest_row"] = complete["manifest_row"] or str(i)
            writer.writerow(complete)


def read_csv_any(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if ".gz" in path.suffixes else open
    with opener(path, "rt", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
