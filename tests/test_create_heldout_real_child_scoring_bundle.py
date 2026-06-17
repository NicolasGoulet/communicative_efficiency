import csv
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from create_heldout_real_child_scoring_bundle import (
    ChildSpec,
    audit_source_csv,
    create_bundle,
    output_path,
    source_path,
)


HEADER = [
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "context_k1",
    "context_k2",
    "context_k3",
    "chi_utterance_clean",
    "random_model_utterance_bin6",
    "unigram_model_utterance_bin6",
    "bigram_model_utterance_bin6",
    "trigram_model_utterance_bin6",
]


def write_scoring_csv(path: Path, *, dataset: str, child_id: str, rows: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        for i in range(rows):
            writer.writerow(
                {
                    "dataset": dataset,
                    "child_id": child_id,
                    "source_group": dataset,
                    "session_id": f"s{i}",
                    "age_months": f"{12 + i}.25",
                    "file": f"{child_id}/{i:06d}.cha",
                    "line_no": str(i + 10),
                    "utt_id": f"utt-{i}",
                    "context_k1": "look",
                    "context_k2": "look there",
                    "context_k3": "look over there",
                    "chi_utterance_clean": f"child words {i}",
                    "random_model_utterance_bin6": "random words",
                    "unigram_model_utterance_bin6": "unigram words",
                    "bigram_model_utterance_bin6": "bigram words",
                    "trigram_model_utterance_bin6": "trigram words",
                }
            )


class HeldoutRealChildScoringBundleTests(unittest.TestCase):
    def test_audit_source_csv_counts_rows_ages_and_contexts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = ChildSpec("Forrester", "Ella")
            src = source_path(root, child)
            out = output_path(root / "bundle", child)
            write_scoring_csv(src, dataset=child.dataset, child_id=child.child_id, rows=3)

            audit = audit_source_csv(src, child=child, output_csv=out)

            self.assertEqual(audit.rows, 3)
            self.assertEqual(audit.blank_target_rows, 0)
            self.assertEqual(audit.age_min_months, "12.250")
            self.assertEqual(audit.age_max_months, "14.250")
            self.assertEqual(audit.context_k1_nonblank_rows, 3)
            self.assertEqual(audit.context_k2_nonblank_rows, 3)
            self.assertEqual(audit.context_k3_nonblank_rows, 3)
            self.assertEqual(audit.missing_required_columns, ())

    def test_create_bundle_writes_expected_layout_metadata_scripts_and_tarball(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "input"
            output_root = root / "heldout_real_child_generalization_2026-06-16"
            tar_gz = root / "heldout_real_child_generalization_2026-06-16.tar.gz"
            children = [
                ChildSpec("Forrester", "Ella"),
                ChildSpec("Sachs", "Naomi"),
                ChildSpec("MPI-EVA-Manchester", "Helen"),
            ]
            for child in children:
                write_scoring_csv(source_path(input_root, child), dataset=child.dataset, child_id=child.child_id)

            audits = create_bundle(
                input_root=input_root,
                output_root=output_root,
                tar_gz=tar_gz,
                children=children,
            )

            self.assertEqual(sum(audit.rows for audit in audits), 6)
            self.assertTrue((output_root / "README.md").exists())
            self.assertTrue((output_root / "scripts" / "score_heldout_real_children_local.sh").exists())
            self.assertTrue((output_root / "scripts" / "audit_heldout_real_child_scores.py").exists())
            self.assertTrue((output_root / "metadata" / "heldout_real_child_manifest.csv").exists())
            self.assertTrue((output_root / "metadata" / "predictor_availability.csv").exists())
            self.assertTrue((output_root / "metadata" / "expected_scoring_tasks.csv").exists())
            self.assertTrue(tar_gz.exists())

            with (output_root / "metadata" / "expected_scoring_tasks.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                task_rows = list(csv.DictReader(handle))
            self.assertEqual(len(task_rows), 12)
            self.assertEqual({row["mode"] for row in task_rows}, {"real"})
            self.assertEqual({row["context_label"] for row in task_rows}, {"k0", "k1", "k2", "k3"})

            script_text = (output_root / "scripts" / "score_heldout_real_children_local.sh").read_text(
                encoding="utf-8"
            )
            self.assertIn("--modes real", script_text)
            self.assertIn("task_count\" -ne 12", script_text)
            self.assertIn("--strict-context-col", script_text)
            self.assertIn("__NO_CONTEXT__", script_text)

            with tarfile.open(tar_gz, "r:gz") as archive:
                names = set(archive.getnames())
            self.assertIn(
                "heldout_real_child_generalization_2026-06-16/data/preprocessed_data/Forrester/Ella/chi.surprisal_scoring.csv",
                names,
            )

    def test_create_bundle_rejects_blank_real_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = ChildSpec("Forrester", "Ella")
            src = source_path(root / "input", child)
            write_scoring_csv(src, dataset=child.dataset, child_id=child.child_id)
            with src.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["chi_utterance_clean"] = ""
            with src.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=HEADER, quoting=csv.QUOTE_ALL, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)

            with self.assertRaisesRegex(RuntimeError, "blank target rows"):
                create_bundle(
                    input_root=root / "input",
                    output_root=root / "bundle",
                    tar_gz=root / "bundle.tar.gz",
                    children=[child],
                )


if __name__ == "__main__":
    unittest.main()
