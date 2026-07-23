import csv
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_direct_surprisal_wide_table import (  # noqa: E402
    CHILD_MODES,
    CONTEXTS,
    build_wide_tables,
    context_condition,
    scored_filename,
)


class TestBuildDirectSurprisalWideTable(unittest.TestCase):
    def test_builds_context_gains_candidate_gaps_and_preserves_literal_nan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            write_complete_fixture(root)
            output_dir = Path(tmp) / "out"

            manifest = build_wide_tables(
                scored_root=root,
                scorer_id="tiny_fixture",
                output_dir=output_dir,
            )

            children = read_gzip_csv(output_dir / "child_direct_surprisal_wide.csv.gz")
            caretakers = read_gzip_csv(output_dir / "caretaker_direct_surprisal_wide.csv.gz")
            audits = read_csv(output_dir / "source_file_audit.csv")
            saved_manifest = json.loads((output_dir / "manifest.json").read_text())

        self.assertEqual(manifest["children"], 1)
        self.assertEqual(manifest["child_rows"], 2)
        self.assertEqual(manifest["caretaker_rows"], 2)
        self.assertEqual(len(children), 2)
        self.assertEqual(len(caretakers), 2)
        self.assertEqual(children[0]["sample_group"], "pbm_discovery")
        self.assertEqual(children[0]["real_context_gain_k3"], "3")
        self.assertEqual(children[0]["bigram_minus_real_k3_bits"], "5")
        self.assertEqual(children[1]["bigram_target_text"], "nan")
        self.assertEqual(children[1]["bigram_nb_words"], "1")
        self.assertEqual(children[1]["bigram_k0_sum_bits"], "17.0")
        self.assertEqual(caretakers[0]["context_gain_k3"], "2")
        self.assertEqual(saved_manifest["key_mismatch_rows"], 0)
        self.assertEqual(saved_manifest["target_mismatch_rows"], 0)
        self.assertEqual(len(audits), 24)

    def test_fails_on_source_key_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            write_complete_fixture(root)
            broken = fixture_path(root, "real", "k2", "child")
            rows = read_csv(broken)
            rows[0]["utt_id"] = "different"
            write_csv(broken, rows)

            with self.assertRaisesRegex(ValueError, "Source-key mismatch"):
                build_wide_tables(
                    scored_root=root,
                    scorer_id="tiny_fixture",
                    output_dir=Path(tmp) / "out",
                    include_caretaker=False,
                )


def fixture_path(root: Path, mode: str, context: str, role: str) -> Path:
    return (
        root
        / context_condition(context)
        / context
        / "toy-model"
        / "Brown"
        / "Ada"
        / scored_filename(mode, role)
    )


def base_row(utt_id: str, *, age: str = "24.0") -> dict[str, str]:
    return {
        "dataset": "Brown",
        "child_id": "Ada",
        "source_group": "Brown",
        "session_id": "1",
        "age_months": age,
        "file": "Ada/020000.cha",
        "line_no": str(10 + int(utt_id)),
        "utt_id": utt_id,
        "speaker": "CHI",
        "context_k1": "look here",
        "context_k2": "come play look here",
        "context_k3": "hello come play look here",
        "chi_utterance_clean": "red ball" if utt_id == "1" else "yes",
        "random_model_utterance_bin6": "blue cow" if utt_id == "1" else "frog",
        "unigram_model_utterance_bin6": "green dog" if utt_id == "1" else "hat",
        "bigram_model_utterance_bin6": "yellow duck" if utt_id == "1" else "nan",
        "trigram_model_utterance_bin6": "orange cat" if utt_id == "1" else "okay",
        "caretaker_utterance_clean": "hello child" if utt_id == "1" else "come here",
        "model_used": "toy/model",
        "model_revision": "revision-1",
        "tokenizer_revision": "tokenizer-1",
        "scoring_dtype": "fp32",
        "scoring_code_revision": "code-1",
    }


def write_complete_fixture(root: Path) -> None:
    context_discount = {"k0": 0.0, "k1": 1.0, "k2": 2.0, "k3": 3.0}
    mode_extra = {"real": 0.0, "random": 9.0, "unigram": 7.0, "bigram": 5.0, "trigram": 3.0}
    for mode in CHILD_MODES:
        for context in CONTEXTS:
            rows = []
            for utt_id, base_bits in [("1", 10.0), ("2", 12.0)]:
                row = base_row(utt_id)
                bits = base_bits + mode_extra[mode] - context_discount[context]
                row["sum_bits"] = str(bits)
                row["mean_bits_per_token"] = str(bits / 2)
                row["n_eval_tokens"] = "2"
                rows.append(row)
            write_csv(fixture_path(root, mode, context, "child"), rows)

    for context in CONTEXTS:
        rows = []
        for utt_id, base_bits in [("1", 20.0), ("2", 22.0)]:
            row = base_row(utt_id)
            bits = base_bits - (2.0 if context == "k3" else 0.0)
            row["sum_bits"] = str(bits)
            row["mean_bits_per_token"] = str(bits / 2)
            row["n_eval_tokens"] = "2"
            rows.append(row)
        write_csv(fixture_path(root, "caretaker", context, "caretaker"), rows)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_gzip_csv(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
