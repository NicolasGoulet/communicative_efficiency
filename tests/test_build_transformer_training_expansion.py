import csv
import gzip
import hashlib
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build_transformer_training_expansion import (  # noqa: E402
    PreparedUnit,
    iter_examples,
    reproducible_gzip_text,
    select_validation_units,
)


FIELDNAMES = [
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_raw",
    "age_months",
    "sex",
    "file",
    "line_no",
    "reference_line",
    "utt_id",
    "utt_id_role",
    "speaker",
    "utterance",
    "utterance_clean",
    "cleaned_is_empty",
]


def write_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def row(speaker, line_no, text, age="2;01", age_months="25.0"):
    return {
        "dataset": "Toy",
        "child_id": "one",
        "source_group": "Toy",
        "session_id": "1",
        "age_raw": age,
        "age_months": age_months,
        "sex": "",
        "file": "one.cha",
        "line_no": str(line_no),
        "reference_line": f"one.cha:{line_no}",
        "utt_id": str(line_no),
        "utt_id_role": str(line_no),
        "speaker": speaker,
        "utterance": text,
        "utterance_clean": text,
        "cleaned_is_empty": "0",
    }


class TestTransformerTrainingExpansion(unittest.TestCase):
    def test_context_is_prior_caretaker_turns_only_and_target_has_age_bin(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "Toy" / "one"
            write_rows(folder / "chi.csv", [row("CHI", 4, "child answer.")])
            write_rows(
                folder / "caretakers.csv",
                [row("MOT", 1, "first turn."), row("MOT", 3, "second turn.")],
            )
            unit = PreparedUnit("Toy", "one", folder, folder / "chi.csv", folder / "caretakers.csv")
            examples = list(
                iter_examples(
                    unit,
                    context_utterances=3,
                    max_context_tokens=60,
                    age_bins=[(6, 23), (24, 29)],
                )
            )

        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["context_turns"], ["first turn.", "second turn."])
        self.assertEqual(examples[0]["target_text"], "child answer.")
        self.assertEqual(examples[0]["target_age_bin"], "024-029")

    def test_validation_selection_is_child_disjoint_and_deterministic(self):
        units = [
            PreparedUnit("Toy", f"c{i}", Path(f"/tmp/c{i}"), Path(f"/tmp/c{i}/chi.csv"), Path(f"/tmp/c{i}/caretakers.csv"))
            for i in range(10)
        ]
        selected_one = select_validation_units(units, fraction=0.2, seed=17)
        selected_two = select_validation_units(units, fraction=0.2, seed=17)
        self.assertEqual(selected_one, selected_two)
        self.assertEqual(len(selected_one), 2)
        self.assertTrue(selected_one.issubset({("Toy", f"c{i}") for i in range(10)}))

    def test_gzip_writer_has_reproducible_header_and_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / "one.jsonl.gz", Path(tmp) / "two.jsonl.gz"]
            for path in paths:
                with reproducible_gzip_text(path) as handle:
                    handle.write('{"value":1}\n')
            hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
            with gzip.open(paths[0], "rt", encoding="utf-8") as handle:
                payload = handle.read()
        self.assertEqual(hashes[0], hashes[1])
        self.assertEqual(payload, '{"value":1}\n')


if __name__ == "__main__":
    unittest.main()
