import gzip
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.build_response_entropy_stopping_probe import (
    build_probe_manifest,
    summarize_probe,
)


class ResponseEntropyStoppingProbeTests(unittest.TestCase):
    def test_manifest_selects_context_length_buckets_under_budget(self):
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

            paths = build_probe_manifest(
                input_manifest=input_manifest,
                output_dir=root / "out",
                contexts_per_bucket=1,
                seed=1,
                max_new_tokens=[12, 24],
                temperatures=[0.5, 0.7],
                samples_per_context=2,
            )

            manifest = pd.read_csv(paths["manifest"])
            spec = paths["spec"].read_text(encoding="utf-8")

            self.assertEqual(len(manifest), 4)
            self.assertEqual(set(manifest["stopping_probe_bucket"]), {"01_one_word", "02_two_to_four", "03_five_to_nine", "04_ten_plus"})
            self.assertIn('"planned_samples": 32', spec)

    def test_summary_classifies_stop_categories_and_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "out"
            out.mkdir()
            pd.DataFrame(
                [
                    {"bucket": "01_one_word", "available_contexts": 1, "selected_contexts": 1},
                ]
            ).to_csv(out / "stopping_probe_manifest_audit.csv", index=False)
            rows = [
                sample_row("ctx1", 12, 0.7, 0, "bike", "bike", hit_max=0, boundary=0),
                sample_row("ctx1", 12, 0.7, 1, "bike\nCaregiver: okay", "bike", hit_max=1, boundary=1),
                sample_row("ctx1", 12, 0.7, 2, "bike bike bike", "bike bike bike", hit_max=1, boundary=0),
            ]
            with gzip.open(out / "stopping_probe_samples_max12.csv.gz", "wt", encoding="utf-8", newline="") as handle:
                pd.DataFrame(rows).to_csv(handle, index=False)

            paths = summarize_probe(
                output_dir=out,
                fig_dir=root / "figs",
                report_md=root / "report.md",
                report_html=root / "report.html",
            )
            categories = pd.read_csv(paths["stop_categories"])
            summary = pd.read_csv(paths["setting_summary"])

            self.assertTrue(paths["report_html"].exists())
            self.assertEqual(set(categories["stop_category"]), {"natural_eos_no_boundary", "boundary_seen_and_generation_hit_cap", "hit_cap_no_boundary"})
            self.assertAlmostEqual(float(summary["hit_max_rate"].iloc[0]), 2 / 3)


def sample_row(
    context_id: str,
    max_new_tokens: int,
    temperature: float,
    sample_index: int,
    raw: str,
    sampled: str,
    *,
    hit_max: int,
    boundary: int,
) -> dict[str, object]:
    return {
        "context_id": context_id,
        "manifest_row": "0",
        "context_text": "what?",
        "prompt_text": "Caregiver: what?\nChild:",
        "temperature": temperature,
        "sample_index": sample_index,
        "raw_generated_text": raw,
        "sampled_response_text": sampled,
        "generated_token_count": max_new_tokens if hit_max else 3,
        "hit_max_new_tokens": hit_max,
        "stopped_by_speaker_boundary": boundary,
        "speaker_boundary_marker": "Caregiver:" if boundary else "",
        "empty_response": 0,
        "model_used": "toy",
        "max_new_tokens": max_new_tokens,
        "top_p": 0.95,
        "top_k": 0,
        "seed_used": 1,
    }


if __name__ == "__main__":
    unittest.main()
