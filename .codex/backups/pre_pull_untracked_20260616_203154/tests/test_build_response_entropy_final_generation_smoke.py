import gzip
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import torch

from src.build_response_entropy_final_generation_smoke import (
    ACCEPTED_COLUMNS,
    ATTEMPT_COLUMNS,
    DEFAULT_PROMPT_VARIANTS,
    EndOfTurnStoppingCriteria,
    append_rows,
    build_smoke_manifest,
    classify_quality,
    summarize_final_smoke,
    trim_at_end_of_turn,
)


class FakeTokenizer:
    pad_token_id = 0
    eos_token_id = 0

    def decode(self, ids, skip_special_tokens=True):
        mapping = {
            1: "hello",
            2: "\n",
            3: "still",
            4: " talking",
            5: "\nCaregiver:",
        }
        values = ids.tolist() if hasattr(ids, "tolist") else list(ids)
        return "".join(mapping.get(int(value), "") for value in values)


class ResponseEntropyFinalGenerationSmokeTests(unittest.TestCase):
    def test_end_of_turn_stopping_returns_per_sequence_decisions(self):
        criteria = EndOfTurnStoppingCriteria(
            FakeTokenizer(),
            prompt_token_width=2,
            stop_strings=["\nCaregiver:", "\n"],
        )
        input_ids = torch.tensor(
            [
                [0, 0, 1, 2],
                [0, 0, 3, 4],
                [0, 0, 1, 5],
            ]
        )

        decisions = criteria(input_ids, torch.empty(0))

        self.assertEqual(decisions.tolist(), [True, False, True])

    def test_trim_prefers_specific_boundary_at_same_position(self):
        response, stopped, marker = trim_at_end_of_turn("bike\nCaregiver: okay")

        self.assertEqual(response, "bike")
        self.assertTrue(stopped)
        self.assertEqual(marker, "\\nCaregiver:")

    def test_quality_classification_accepts_clean_and_rejects_hard_flags(self):
        clean = classify_quality(
            raw_generated_text="bike\n",
            sampled_response_text="bike",
            context_text="what do you want",
            hit_max_new_tokens=False,
            stopped_by_end_of_turn=True,
        )
        self.assertEqual(clean["accepted"], 1)
        self.assertEqual(clean["rejection_reason"], "")

        empty = classify_quality(
            raw_generated_text="\n",
            sampled_response_text="",
            context_text="what do you want",
            hit_max_new_tokens=False,
            stopped_by_end_of_turn=True,
        )
        self.assertEqual(empty["accepted"], 0)
        self.assertEqual(empty["rejection_reason"], "empty_response")

        no_boundary = classify_quality(
            raw_generated_text="no no no",
            sampled_response_text="no no no",
            context_text="what do you want",
            hit_max_new_tokens=True,
            stopped_by_end_of_turn=False,
        )
        self.assertEqual(no_boundary["rejection_reason"], "no_boundary_before_cap")

        loop = classify_quality(
            raw_generated_text="like like like like like like\n",
            sampled_response_text="like like like like like like",
            context_text="what do you want",
            hit_max_new_tokens=False,
            stopped_by_end_of_turn=True,
        )
        self.assertEqual(loop["rejection_reason"], "repetition_loop")

        copy = classify_quality(
            raw_generated_text="lettuce she's eating lettuce.\n",
            sampled_response_text="lettuce she's eating lettuce.",
            context_text="lettuce she's eating lettuce.",
            hit_max_new_tokens=False,
            stopped_by_end_of_turn=True,
        )
        self.assertEqual(copy["accepted"], 1)
        self.assertEqual(copy["possible_context_copy"], 1)

    def test_manifest_expands_balanced_contexts_across_prompt_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_manifest = root / "pilot_generation_manifest.csv"
            rows = []
            for idx, count in enumerate([1, 1, 2, 3, 5, 8, 10, 14]):
                rows.append(
                    {
                        "manifest_row": idx,
                        "context_id": f"ctx{idx}",
                        "context_text": "word " * count,
                        "context_word_count": count,
                    }
                )
            pd.DataFrame(rows).to_csv(input_manifest, index=False)

            paths = build_smoke_manifest(
                input_manifest=input_manifest,
                output_dir=root / "out",
                contexts_per_bucket=1,
                prompt_variants=DEFAULT_PROMPT_VARIANTS,
                temperatures=[0.3, 0.5, 0.7, 1.0],
                accepted_samples_per_setting=20,
                max_attempts_per_setting=60,
                max_new_tokens=96,
                seed=1,
                model_name="toy",
            )

            manifest = pd.read_csv(paths["manifest"])
            audit = pd.read_csv(paths["audit"])

            self.assertEqual(manifest["context_id"].nunique(), 4)
            self.assertEqual(len(manifest), 12)
            self.assertEqual(set(manifest["prompt_variant"]), {"Caregiver", "Parent", "Adult"})
            total = audit[audit["audit_scope"] == "total"].iloc[0]
            self.assertEqual(int(total["planned_accepted_samples"]), 4 * 3 * 4 * 20)

    def test_summary_writes_required_tables_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            pd.DataFrame(
                [
                    {
                        "audit_scope": "total",
                        "context_length_bucket": "all",
                        "available_contexts": 2,
                        "selected_base_contexts": 2,
                        "prompt_variants": 3,
                        "temperatures": "0.3,0.5",
                        "accepted_samples_per_setting": 2,
                        "max_attempts_per_setting": 4,
                        "planned_accepted_samples": 24,
                        "max_attempt_rows": 48,
                    }
                ]
            ).to_csv(out / "smoke_manifest_audit.csv", index=False)
            attempts = [
                attempt_row("ctx1", "Caregiver", 0.5, 0, 0, 1, "bike", ""),
                attempt_row("ctx1", "Caregiver", 0.5, 1, 1, 1, "ball", ""),
                attempt_row("ctx1", "Parent", 0.5, 0, 0, 1, "bike", ""),
                attempt_row("ctx1", "Parent", 0.5, 1, "", 0, "", "empty_response"),
                attempt_row("ctx1", "Parent", 0.5, 2, 1, 1, "book", ""),
                attempt_row("ctx2", "Caregiver", 0.5, 0, 0, 1, "dog", ""),
                attempt_row("ctx2", "Caregiver", 0.5, 1, 1, 1, "cat", ""),
                attempt_row("ctx2", "Parent", 0.5, 0, 0, 1, "dog", ""),
                attempt_row("ctx2", "Parent", 0.5, 1, 1, 1, "fish", ""),
            ]
            append_rows(out / "all_attempts.csv.gz", attempts, ATTEMPT_COLUMNS)
            accepted = [row for row in attempts if row["accepted"] == 1]
            append_rows(out / "accepted_samples.csv.gz", accepted, ACCEPTED_COLUMNS)

            paths = summarize_final_smoke(
                output_dir=out,
                fig_dir=root / "figs",
                report_md=root / "report.md",
                report_html=root / "report.html",
            )

            self.assertTrue(paths["report_html"].exists())
            self.assertTrue((out / "rejection_summary_by_setting.csv").exists())
            self.assertTrue((out / "quality_flags_by_setting.csv").exists())
            self.assertTrue((out / "prompt_temperature_rank_correlations.csv").exists())
            self.assertTrue((out / "manual_review_examples.csv").exists())
            rejections = pd.read_csv(out / "rejection_summary_by_setting.csv")
            self.assertIn("empty_response_count", rejections.columns)
            self.assertEqual(int(rejections["accepted_samples"].sum()), len(accepted))


def attempt_row(
    context_id: str,
    prompt_variant: str,
    temperature: float,
    attempt_index: int,
    sample_index,
    accepted: int,
    response: str,
    rejection_reason: str,
) -> dict[str, object]:
    setting_id = f"{context_id}::{prompt_variant}::T{temperature:g}"
    flags = classify_quality(
        raw_generated_text=response + "\n",
        sampled_response_text=response,
        context_text="what do you want",
        hit_max_new_tokens=False,
        stopped_by_end_of_turn=True,
    )
    return {
        "setting_id": setting_id,
        "smoke_manifest_row": "0",
        "smoke_context_row": "0",
        "source_manifest_row": "0",
        "context_id": context_id,
        "context_text": "what do you want",
        "context_word_count": 4,
        "context_length_bucket": "02_two_to_four",
        "prompt_variant": prompt_variant,
        "prompt_template": f"{prompt_variant}: {{context}}\nChild:",
        "prompt_text": f"{prompt_variant}: what do you want\nChild:",
        "temperature": temperature,
        "attempt_index": attempt_index,
        "accepted": accepted,
        "sample_index": sample_index,
        "attempts_needed_for_acceptance": 1 if accepted else "",
        "rejection_reason": rejection_reason,
        "quality_flags": flags["quality_flags"],
        **{column: flags[column] for column in flags if column.endswith("_response") or column in {
            "speaker_label_inside_response",
            "metadata_or_prose_start",
            "repetition_loop",
            "no_end_of_turn_boundary_before_cap",
            "possible_context_copy",
            "very_long_first_line_response",
            "malformed_response",
        }},
        "raw_generated_text": response + "\n",
        "sampled_response_text": response,
        "generated_token_count": 2,
        "hit_max_new_tokens": 0,
        "stopped_by_end_of_turn": 1,
        "end_of_turn_marker": "\\n",
        "model_used": "toy",
        "max_new_tokens": 96,
        "top_p": 0.95,
        "top_k": 0,
        "seed_used": 1,
        "target_accepted_samples": 2,
        "max_attempts_per_setting": 4,
    }


if __name__ == "__main__":
    unittest.main()
