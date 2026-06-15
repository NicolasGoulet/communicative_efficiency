import csv
import tempfile
import unittest
from pathlib import Path
import sys

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from src.build_response_entropy_pilot_grid import (
    build_pilot_diagnostics,
    build_pilot_manifest,
)


class ResponseEntropyPilotGridTests(unittest.TestCase):
    def test_manifest_stage_balances_strata_and_deduplicates_generation_contexts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scored = root / "scored"
            write_scored_csv(
                scored / "WITH_context" / "k1" / "mistral" / "Toy" / "Ada" / "chi.surprisal_scoring__real.scored.csv",
                [
                    toy_row(age=20, context_k="k1", context="same context."),
                    toy_row(age=25, context_k="k1", context="same context."),
                    toy_row(age=31, context_k="k1", context="new context."),
                ],
            )
            write_scored_csv(
                scored / "WITH_context" / "k2" / "mistral" / "Toy" / "Ada" / "chi.surprisal_scoring__real.scored.csv",
                [
                    toy_row(age=20, context_k="k2", context="same context."),
                    toy_row(age=31, context_k="k2", context="another context."),
                ],
            )

            out = root / "out"
            paths = build_pilot_manifest(
                scored_root=scored,
                output_dir=out,
                fig_dir=root / "figs",
                design_md=root / "design.md",
                design_html=root / "design.html",
                score_source="toy",
                context_ks=["k1", "k2"],
                sample_per_age_bin_context_k=1,
                min_context_words=1,
                temperatures=[0.7, 1.0],
                samples_per_context=4,
                max_new_tokens=12,
                top_p=0.95,
                top_k=0,
                model_name="toy-model",
                prompt_template="Caregiver: {context}\nChild:",
                batch_contexts=1,
                batch_samples=2,
                dtype="float32",
                seed=1,
            )
            selected = pd.read_csv(paths["selected"])
            generation = pd.read_csv(paths["generation_manifest"])
            audit = pd.read_csv(paths["audit"])

            self.assertLessEqual(selected.groupby(["selection_age_bin", "selection_context_k"]).size().max(), 1)
            self.assertLessEqual(len(generation), len(selected))
            self.assertIn("planned generations", paths["design_md"].read_text(encoding="utf-8"))
            self.assertIn("--batch-samples 2", paths["design_md"].read_text(encoding="utf-8"))
            self.assertTrue((audit["selected_context_strata"] <= audit["eligible_context_strata"]).all())

    def test_diagnostics_stage_writes_quality_reliability_and_plots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            samples = root / "samples.csv"
            write_sample_csv(samples)

            paths = build_pilot_diagnostics(
                samples_csv=samples,
                output_dir=root / "out",
                fig_dir=root / "figs",
                diagnostic_md=root / "diagnostics.md",
                diagnostic_html=root / "diagnostics.html",
                normalization="casefold",
                downsample_sizes=[2, 4],
            )
            quality = pd.read_csv(paths["quality"])
            split_half = pd.read_csv(paths["split_half"])
            downsample = pd.read_csv(paths["downsample"])

            self.assertTrue(paths["diagnostic_html"].exists())
            self.assertEqual(set(quality["temperature"].astype(float)), {0.7, 1.0})
            self.assertFalse(split_half.empty)
            self.assertFalse(downsample.empty)
            self.assertTrue(paths["figures"].exists())


def toy_row(*, age: int, context_k: str, context: str) -> dict[str, str]:
    row = {
        "dataset": "Toy",
        "child_id": "Ada",
        "session_id": str(age),
        "age_months": str(age),
        "file": f"Ada/{age:02d}.cha",
        "line_no": str(age),
        "utt_id": str(age),
        "context_k1": "",
        "context_k2": "",
        "context_k3": "",
        "context_col_used": f"context_{context_k}",
        "chi_utterance_clean": "yes.",
    }
    row[f"context_{context_k}"] = context
    return row


def write_scored_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sample_csv(path: Path) -> None:
    rows = []
    responses = {
        ("c1", 0.7): ["yes", "yes", "no", "yes"],
        ("c2", 0.7): ["ball", "ball", "ball", "toy"],
        ("c1", 1.0): ["yes", "no", "maybe", ""],
        ("c2", 1.0): ["ball", "toy", "book", "car"],
    }
    for (context_id, temperature), values in responses.items():
        for sample_index, response in enumerate(values):
            rows.append(
                {
                    "context_id": context_id,
                    "manifest_row": "0",
                    "context_text": "what?",
                    "prompt_text": "Caregiver: what?\nChild:",
                    "temperature": temperature,
                    "sample_index": sample_index,
                    "sampled_response_text": response,
                    "generated_token_count": "3",
                    "hit_max_new_tokens": "0",
                    "stopped_by_speaker_boundary": "1" if sample_index == 3 else "0",
                    "empty_response": "1" if response == "" else "0",
                    "model_used": "toy",
                    "max_new_tokens": "12",
                    "top_p": "0.95",
                    "top_k": "0",
                    "seed_used": "1",
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)


if __name__ == "__main__":
    unittest.main()
