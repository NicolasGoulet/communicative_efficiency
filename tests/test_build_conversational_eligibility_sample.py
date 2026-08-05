from __future__ import annotations

import csv
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from src.build_conversational_eligibility_sample import (
    build_conversational_flags,
    parse_chat_main_tiers,
)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ConversationalEligibilityTests(unittest.TestCase):
    def test_parser_keeps_all_speakers_and_main_line_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.cha"
            path.write_text(
                "@UTF8\n@Situation:\tBook reading\n*INV:\tlook .\n*CHI:\tlook .\n%mor:\tverb|look .\n*MOT:\tyeah .\n",
                encoding="utf-8",
            )
            tiers, metadata = parse_chat_main_tiers(path)
            self.assertEqual([tier.speaker for tier in tiers], ["INV", "CHI", "MOT"])
            self.assertEqual([tier.line_no for tier in tiers], [3, 4, 6])
            self.assertIn("Book reading", metadata)

    def test_builder_flags_raw_adjacency_imitation_and_next_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = root / "bundle"
            raw_root = root / "raw"
            scoring = bundle / "preprocessed_data" / "Brown" / "Adam" / "chi.surprisal_scoring.csv"
            rows = [
                {
                    "dataset": "Brown", "child_id": "Adam", "session_id": "1", "age_months": "24",
                    "age_bin": "024-029", "file": "Adam/a.cha", "line_no": "5", "utt_id": "1",
                    "utterance_id": "u1", "context_k1": "want milk?", "context_k2": "want milk?",
                    "context_k3": "want milk?", "chi_utterance_clean": "want milk.",
                },
                {
                    "dataset": "Brown", "child_id": "Adam", "session_id": "1", "age_months": "24",
                    "age_bin": "024-029", "file": "Adam/a.cha", "line_no": "8", "utt_id": "2",
                    "utterance_id": "u2", "context_k1": "yeah.", "context_k2": "yeah.",
                    "context_k3": "yeah.", "chi_utterance_clean": "ball.",
                },
            ]
            write_csv(scoring, rows)
            write_csv(
                bundle / "manifest.csv",
                [{"dataset": "Brown", "child_id": "Adam", "child_scoring_ready": "1", "child_scoring_csv": str(scoring)}],
            )
            raw_path = raw_root / "Brown" / "Adam" / "a.cha"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_text(
                "@UTF8\n@Situation:\tBook reading\n*MOT:\twant milk ?\n%mor:\tverb|want noun|milk ?\n*CHI:\twant milk .\n*MOT:\tyeah .\n*INV:\tlook there .\n*CHI:\tball .\n*MOT:\twhat ?\n",
                encoding="utf-8",
            )
            output = root / "out" / "flags.csv.gz"
            audit_path = root / "out" / "audit.json"
            manual = root / "out" / "manual.csv"
            audit = build_conversational_flags(
                bundle_root=bundle,
                raw_root=raw_root,
                output_csv=output,
                audit_json=audit_path,
                manual_sample_csv=manual,
                per_stratum=2,
                seed=1,
            )
            self.assertEqual(audit["status"], "PASS")
            with gzip.open(output, "rt", newline="", encoding="utf-8") as handle:
                flagged = list(csv.DictReader(handle))
            self.assertEqual(flagged[0]["primary_responsive_turn_eligible"], "1")
            self.assertEqual(flagged[0]["exact_imitation_candidate"], "1")
            self.assertEqual(flagged[0]["next_caregiver_response_available"], "1")
            self.assertEqual(flagged[0]["next_caregiver_acknowledgement_candidate"], "1")
            self.assertEqual(flagged[0]["session_reading_candidate"], "1")
            self.assertEqual(flagged[1]["previous_main_speaker"], "INV")
            self.assertEqual(flagged[1]["primary_responsive_turn_eligible"], "0")
            self.assertEqual(flagged[1]["next_caregiver_clarification_candidate"], "1")
            saved_audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_audit["counts"]["rows"], 2)
            self.assertTrue(manual.exists())

    def test_missing_raw_file_is_retained_and_requires_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bundle = root / "bundle"
            scoring = bundle / "child.csv"
            write_csv(
                scoring,
                [{
                    "dataset": "Brown", "child_id": "Adam", "session_id": "1", "age_months": "24",
                    "file": "missing.cha", "line_no": "1", "utt_id": "1",
                    "chi_utterance_clean": "hello.", "context_k1": "hi.", "context_k2": "", "context_k3": "",
                }],
            )
            write_csv(
                bundle / "manifest.csv",
                [{"dataset": "Brown", "child_id": "Adam", "child_scoring_ready": "1", "child_scoring_csv": str(scoring)}],
            )
            audit = build_conversational_flags(
                bundle_root=bundle,
                raw_root=root / "raw",
                output_csv=root / "flags.csv.gz",
                audit_json=root / "audit.json",
                manual_sample_csv=root / "manual.csv",
                per_stratum=1,
            )
            self.assertEqual(audit["status"], "REVIEW")
            self.assertEqual(audit["counts"]["unresolved_raw_rows"], 1)


if __name__ == "__main__":
    unittest.main()
