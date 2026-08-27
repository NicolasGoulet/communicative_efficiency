from __future__ import annotations

import csv
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.build_downstream_caregiver_response_analysis import (
    CONDITIONS,
    assemble_scorer_dataset,
    fit_primary_cell_model,
    make_model_cells,
)


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def write_gzip_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, compression="gzip")


class DownstreamCaregiverResponseAnalysisTests(unittest.TestCase):
    def test_assembly_computes_paired_gains_and_validates_target_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff"
            handoff.mkdir()
            target = "yes indeed"
            source = pd.DataFrame(
                [
                    {
                        "response_pair_id": "p1", "dataset": "Brown", "child_id": "Adam",
                        "child_key": "Brown/Adam", "sample_group": "pbm_discovery",
                        "session_id": "1", "age_months": "30", "age_bin": "030-035",
                        "file": "a.cha", "line_no": "10", "next_caregiver_line_no": "11",
                        "target_text_sha256": text_hash(target), "child_text_sha256": text_hash("want milk"),
                        "child_word_count": "2", "child_character_count": "9",
                        "response_word_count": "2", "response_character_count": "10",
                        "base_context_word_count": "3", "primary_eligible": "1",
                        "sensitivity_eligible": "1", "shuffle_available": "1",
                        "shuffle_match_level": "exact", "previous_caretaker_question_type": "polar_question",
                        "child_question_type": "not_question", "next_caregiver_question_type": "not_question",
                        "exact_imitation_candidate": "0", "contained_imitation_candidate": "0",
                        "child_backchannel_candidate": "0", "session_reading_candidate": "0",
                        "session_routine_candidate": "0", "repair_sequence_candidate": "0",
                        "next_caregiver_clarification_candidate": "0",
                        "next_caregiver_acknowledgement_candidate": "0",
                    }
                ]
            )
            input_path = handoff / "inputs/Brown.caregiver_response.csv.gz"
            write_gzip_csv(input_path, source)
            digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
            pd.DataFrame([{"dataset": "Brown", "rows": 1, "input_relpath": "inputs/Brown.caregiver_response.csv.gz", "sha256": digest}]).to_csv(
                handoff / "dataset_inventory.csv", index=False
            )
            (handoff / "audit.json").write_text(json.dumps({"status": "PASS", "totals": {"datasets": 1}}))
            (handoff / "BUILD_COMPLETE_AND_AUDITED").write_text("PASS\n")
            scores = root / "scores"
            values = {
                "unconditional": 20.0,
                "base_context": 15.0,
                "matched_child": 10.0,
                "shuffled_child": 14.0,
                "child_only": 12.0,
            }
            for condition in CONDITIONS:
                out = scores / f"Brown/{condition}/caregiver_response_surprisal"
                out.mkdir(parents=True)
                pd.DataFrame(
                    [{
                        "utterance_id": "p1", "target_text": target, "score_status": "scored",
                        "context_available": True, "utterance_sum_bits": values[condition],
                    }]
                ).to_csv(out / "utterances.csv.gz", index=False, compression="gzip")
                (out / "CONTRACT_COMPLETE").write_text("PASS\n")
            frame, audit = assemble_scorer_dataset(
                handoff_root=handoff, score_root=scores, scorer_key="mistral-7b-v0.3"
            )
            self.assertEqual(audit["status"], "PASS")
            self.assertEqual(frame.loc[0, "downstream_gain_bits"], 5.0)
            self.assertEqual(frame.loc[0, "matched_over_shuffled_bits"], 4.0)
            self.assertEqual(frame.loc[0, "child_only_gain_bits"], 8.0)

    def test_cell_model_recovers_positive_age_slope(self) -> None:
        records = []
        for child_index in range(6):
            for age in (24, 30, 36, 42):
                records.append(
                    {
                        "dataset": f"D{child_index % 2}",
                        "child_key": f"D{child_index % 2}/c{child_index}",
                        "age_bin": f"a{age}",
                        "age_months": age,
                        "child_word_count": 2 + child_index % 2,
                        "response_word_count": 3,
                        "downstream_gain_bits": 0.2 * age + child_index,
                    }
                )
        cells = make_model_cells(pd.DataFrame(records), "downstream_gain_bits")
        summary, coefficients = fit_primary_cell_model(cells)
        self.assertEqual(summary["status"], "PASS")
        self.assertAlmostEqual(summary["age_estimate"], 0.2, places=6)
        self.assertTrue(np.isfinite(coefficients["estimate"]).all())


if __name__ == "__main__":
    unittest.main()
