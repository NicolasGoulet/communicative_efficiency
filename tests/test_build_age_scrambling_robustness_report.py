import csv
import tempfile
import unittest
from pathlib import Path

import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_age_scrambling_robustness_report import (
    build_age_scrambling_analysis,
    build_units_from_scored_tree,
    sample_balanced_age_bins,
    scramble_unit_ages,
)


class TestBuildAgeScramblingRobustnessReport(unittest.TestCase):
    def test_build_units_streams_split_scored_tree_and_attaches_entropy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            entropy = Path(tmp) / "entropy.csv"
            rows = toy_rows([20, 25], context_k="k1")
            write_scored_csv(
                root
                / "WITH_context"
                / "k1"
                / "mistral"
                / "Toy"
                / "Ada"
                / "chi.surprisal_scoring__real.scored.csv",
                rows,
            )
            write_entropy_csv(entropy, ["look 20.", "look 25."])

            units, audit = build_units_from_scored_tree(
                scored_root=root,
                score_source="toy",
                entropy_features_csv=entropy,
                context_ks=["k1"],
            )

        self.assertEqual(len(units), 2)
        self.assertEqual(int(units["n_utterances"].sum()), 2)
        self.assertTrue((units["mean_nb_words"] > 0).all())
        self.assertTrue((units["mean_context_entropy_bits"] > 0).all())
        self.assertEqual(int(audit["rows_read"].sum()), 2)
        self.assertEqual(int(audit["entropy_matched_rows"].sum()), 2)

    def test_analysis_stage_writes_split_tree_source_audit_without_long_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            entropy = Path(tmp) / "entropy.csv"
            months = [20, 25, 31, 37, 43, 49]
            entropy_contexts = []
            for context_k in ["k0", "k1", "k2", "k3"]:
                condition = "WITHOUT_context" if context_k == "k0" else "WITH_context"
                write_scored_csv(
                    root
                    / condition
                    / context_k
                    / "mistral"
                    / "Toy"
                    / "Ada"
                    / "chi.surprisal_scoring__real.scored.csv",
                    toy_rows(months, context_k=context_k),
                )
                if context_k != "k0":
                    entropy_contexts.extend([f"look {month}." for month in months])
            write_entropy_csv(entropy, entropy_contexts)

            output_dir = Path(tmp) / "out"
            fig_dir = Path(tmp) / "figs"
            paths = build_age_scrambling_analysis(
                source="scored-tree",
                scored_root=root,
                entropy_features_csv=entropy,
                score_source="toy",
                output_dir=output_dir,
                fig_dir=fig_dir,
                context_ks=["k0", "k1", "k2", "k3"],
                n_reps=2,
                balanced_units_per_bin=1,
            )

            self.assertTrue(paths["unit_frame"].exists())
            self.assertTrue(paths["source_audit"].exists())
            self.assertTrue(paths["summary"].exists())
            with paths["source_audit"].open("r", encoding="utf-8", newline="") as handle:
                source_rows = list(csv.DictReader(handle))
            refit_paths = build_age_scrambling_analysis(
                source="unit-frame",
                unit_frame_input=paths["unit_frame"],
                output_dir=Path(tmp) / "refit",
                fig_dir=Path(tmp) / "refit_figs",
                context_ks=["k0", "k1", "k2", "k3"],
                n_reps=1,
                balanced_units_per_bin=1,
            )
            self.assertTrue(refit_paths["summary"].exists())
        self.assertEqual(len(source_rows), 4)
        self.assertEqual(sum(int(row["rows_kept"]) for row in source_rows), 24)

    def test_sampling_and_scrambling_keep_row_count_but_break_age_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            entropy = Path(tmp) / "entropy.csv"
            write_scored_csv(
                root
                / "WITH_context"
                / "k1"
                / "mistral"
                / "Toy"
                / "Ada"
                / "chi.surprisal_scoring__real.scored.csv",
                toy_rows([20, 25, 31, 37], context_k="k1"),
            )
            write_entropy_csv(entropy, ["look 20.", "look 25.", "look 31.", "look 37."])
            units, _ = build_units_from_scored_tree(
                scored_root=root,
                score_source="toy",
                entropy_features_csv=entropy,
                context_ks=["k1"],
            )
            units["effort_value"] = units["mean_nb_words"]

        sampled = sample_balanced_age_bins(units, rng=__import__("numpy").random.default_rng(7), n_per_bin=2)
        scrambled = scramble_unit_ages(units, rng=__import__("numpy").random.default_rng(7))

        self.assertEqual(len(sampled), 8)
        self.assertEqual(len(scrambled), len(units))
        self.assertCountEqual(scrambled["age_months"].tolist(), units["age_months"].tolist())


def toy_rows(months: list[int], *, context_k: str) -> list[dict[str, str]]:
    rows = []
    for idx, month in enumerate(months, start=1):
        row = {
            "dataset": "Toy",
            "child_id": "Ada",
            "session_id": str(idx),
            "age_months": str(month),
            "file": f"Ada/{month:02d}.cha",
            "line_no": str(idx * 10),
            "utt_id": str(idx),
            "context_k1": "",
            "context_k2": "",
            "context_k3": "",
            "context_col_used": "" if context_k == "k0" else f"context_{context_k}",
            "chi_utterance_clean": f"cat {idx}.",
            "sum_bits": str(10 + idx),
            "mean_bits_per_token": "5",
            "n_eval_tokens": "2",
        }
        if context_k != "k0":
            row[f"context_{context_k}"] = f"look {month}."
        rows.append(row)
    return rows


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


def write_entropy_csv(path: Path, contexts: list[str]) -> None:
    fieldnames = [
        "context_col",
        "context_text",
        "context_id",
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for idx, context in enumerate(contexts):
            for context_col in ["context_k1", "context_k2", "context_k3"]:
                writer.writerow(
                    {
                        "context_col": context_col,
                        "context_text": context,
                        "context_id": f"ctx-{idx}-{context_col}",
                        "context_token_count": "2",
                        "llm_next_entropy_bits": "4.5",
                        "llm_next_top1_prob": "0.1",
                        "llm_next_top5_mass": "0.5",
                        "llm_next_top10_mass": "0.6",
                        "llm_next_top50_mass": "0.8",
                        "llm_next_argmax_bits": "1",
                        "model_used": "toy",
                        "dtype_used": "float32",
                        "max_length_used": "128",
                        "seed_used": "1",
                    }
                )


if __name__ == "__main__":
    unittest.main()
