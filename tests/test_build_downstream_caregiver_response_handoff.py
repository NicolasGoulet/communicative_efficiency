from __future__ import annotations

import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.build_downstream_caregiver_response_handoff import (
    assign_deterministic_shuffles,
    build_handoff,
    sha256_file,
)


def write_flags(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def flag_row(
    *, dataset: str, child: str, line: int, text: str, response: str,
    primary: bool = True, context: str = "caregiver asks?",
) -> dict[str, str]:
    return {
        "dataset": dataset,
        "child_id": child,
        "session_id": "1",
        "age_months": "30",
        "age_bin": "030-035",
        "file": f"{child}/a.cha",
        "line_no": str(line),
        "next_main_line_no": str(line + 1),
        "utt_id": str(line),
        "chi_utterance_clean": text,
        "context_k3": context,
        "raw_line_aligned": "1",
        "raw_target_text_matches": "1",
        "next_main_is_caretaker": "1",
        "next_main_utterance_clean": response,
        "primary_responsive_turn_eligible": "1" if primary else "0",
        "context_k1_matches_nearest_caretaker": "1" if primary else "0",
        "previous_caretaker_question_type": "polar_question",
        "child_question_type": "not_question",
        "next_caregiver_question_type": "not_question",
        "exact_imitation_candidate": "0",
        "contained_imitation_candidate": "0",
        "child_backchannel_candidate": "0",
        "session_reading_candidate": "0",
        "session_routine_candidate": "0",
        "repair_sequence_candidate": "0",
        "next_caregiver_clarification_candidate": "0",
        "next_caregiver_acknowledgement_candidate": "0",
    }


class DownstreamCaregiverResponseHandoffTests(unittest.TestCase):
    def test_shuffle_is_exact_matched_deterministic_and_not_self(self) -> None:
        rows = [
            {
                "dataset": "Brown", "age_bin": "030-035", "child_word_count": 2,
                "response_pair_id": f"p{i}", "child_text": text,
                "child_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "child_key": f"Brown/c{i % 2}", "file": f"f{i}.cha", "context_base": "hello",
            }
            for i, text in enumerate(("one two", "three four", "five six", "seven eight"))
        ]
        first = [dict(row) for row in rows]
        second = [dict(row) for row in rows]
        assign_deterministic_shuffles(first, seed=7)
        assign_deterministic_shuffles(second, seed=7)
        self.assertEqual(first, second)
        self.assertTrue(all(row["shuffle_available"] == 1 for row in first))
        self.assertTrue(all(row["shuffle_source_pair_id"] != row["response_pair_id"] for row in first))
        self.assertCountEqual(
            [row["shuffled_child_text"] for row in first],
            [row["child_text"] for row in rows],
        )

    def test_builder_writes_five_conditions_and_reproducible_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "flags.csv.gz"
            rows = [
                flag_row(dataset="Brown", child="Adam", line=10, text="want milk", response="here you go"),
                flag_row(dataset="Brown", child="Eve", line=20, text="more juice", response="all right"),
                flag_row(dataset="Wells", child="Abigail", line=30, text="play ball", response="yes we can"),
                flag_row(
                    dataset="Wells", child="Benjamin", line=40, text="read book",
                    response="which book", primary=False,
                ),
            ]
            write_flags(source, rows)
            audit = root / "source_audit.json"
            audit.write_text(
                json.dumps(
                    {
                        "status": "REVIEW",
                        "counts": {"rows": 4, "eligible_context_k1_mismatches": 1},
                    }
                ),
                encoding="utf-8",
            )
            config = {
                "schema_version": "1.0.0",
                "package_id": "fixture_downstream",
                "source_flags": source.name,
                "source_flags_sha256": sha256_file(source),
                "source_audit": audit.name,
                "shuffle_seed": 4,
                "expected": {
                    "source_rows": 4,
                    "datasets": 2,
                    "children": 4,
                    "sensitivity_rows": 4,
                    "primary_rows": 3,
                    "pbm_primary_rows": 2,
                    "non_pbm_primary_rows": 1,
                },
                "conditions": [
                    {"condition": "unconditional", "context_column": ""},
                    {"condition": "base_context", "context_column": "context_base"},
                    {"condition": "matched_child", "context_column": "context_matched_child"},
                    {"condition": "shuffled_child", "context_column": "context_shuffled_child"},
                    {"condition": "child_only", "context_column": "context_child_only"},
                ],
                "models": [
                    {"model_key": "mistral-7b-v0.3", "model_id": "mistralai/Mistral-7B-v0.3"},
                    {"model_key": "tinydialogues", "model_id": "tiny"},
                    {"model_key": "qwen3-14b", "model_id": "qwen"},
                ],
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output1 = root / "out1"
            output2 = root / "out2"
            result1 = build_handoff(config_path=config_path, output_dir=output1, project_root=root)
            result2 = build_handoff(config_path=config_path, output_dir=output2, project_root=root)
            self.assertEqual(result1["archive_sha256"], result2["archive_sha256"])
            self.assertEqual(result1["contracts_per_model"], 10)
            self.assertEqual(result1["model_contracts_pending"], 30)
            with (output1 / "scoring_contracts_template.csv").open(newline="") as handle:
                contracts = list(csv.DictReader(handle))
            self.assertEqual(len(contracts), 10)
            self.assertEqual({row["scoring_condition"] for row in contracts}, {
                "unconditional", "base_context", "matched_child", "shuffled_child", "child_only"
            })
            with gzip.open(output1 / "inputs/Brown.caregiver_response.csv.gz", "rt", newline="") as handle:
                brown = list(csv.DictReader(handle))
            self.assertEqual(len(brown), 2)
            self.assertTrue(all(row["context_matched_child"].endswith(row["child_text"]) for row in brown))


if __name__ == "__main__":
    unittest.main()
