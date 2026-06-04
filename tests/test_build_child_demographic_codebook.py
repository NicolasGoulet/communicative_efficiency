import csv
import tempfile
import unittest
from pathlib import Path

from src.build_child_demographic_codebook import (
    OUTPUT_COLUMNS,
    build_codebook_rows,
    build_outputs,
    load_overrides,
    summarize_rows,
)


class BuildChildDemographicCodebookTests(unittest.TestCase):
    def test_exact_override_takes_precedence_over_dataset_wildcard(self):
        metadata = [
            {
                "dataset": "Corpus",
                "child_id": "Alice",
                "sex_values": "female",
                "chi_id_group_values": "",
                "chi_id_ses_values": "MC",
                "chi_id_education_values": "",
                "demographic_header_values": "",
                "age_months_min": "12",
                "age_months_max": "24",
                "n_sessions": "2",
                "child_nonempty_utterances": "10",
                "caretaker_nonempty_utterances": "20",
            },
            {
                "dataset": "Corpus",
                "child_id": "Bob",
                "sex_values": "male",
                "chi_id_group_values": "",
                "chi_id_ses_values": "MC",
                "chi_id_education_values": "",
                "demographic_header_values": "some note",
                "age_months_min": "12",
                "age_months_max": "24",
                "n_sessions": "2",
                "child_nonempty_utterances": "11",
                "caretaker_nonempty_utterances": "21",
            },
        ]
        wildcard = {
            "Corpus": {
                "dataset": "Corpus",
                "child_id": "*",
                "ses_category": "middle_class",
                "ses_label": "middle class corpus",
                "ses_scope": "corpus_level",
                "ses_source_type": "official",
                "ses_source_url": "https://example.test/corpus",
                "ses_source_note": "corpus-level note",
                "ses_confidence": "medium",
                "race_ethnicity": "unknown",
                "race_scope": "unknown",
                "race_source_type": "",
                "race_source_url": "",
                "race_source_note": "",
                "race_confidence": "none",
                "parental_education": "unknown",
                "parental_education_scope": "unknown",
                "parental_education_source_url": "",
                "parental_education_source_note": "",
                "notes": "",
            }
        }
        exact = {
            ("Corpus", "Alice"): {
                **wildcard["Corpus"],
                "child_id": "Alice",
                "ses_category": "working_class",
                "ses_label": "working class child",
                "ses_scope": "child_specific",
                "ses_confidence": "high",
                "race_ethnicity": "Black",
                "race_scope": "child_specific",
                "race_source_type": "official",
                "race_source_url": "https://example.test/alice",
                "race_source_note": "child-specific note",
                "race_confidence": "high",
                "notes": "exact row",
            }
        }

        rows = build_codebook_rows(metadata, (exact, wildcard))
        alice = next(row for row in rows if row["child_id"] == "Alice")
        bob = next(row for row in rows if row["child_id"] == "Bob")

        self.assertEqual(alice["ses_category"], "working_class")
        self.assertEqual(alice["race_ethnicity"], "Black")
        self.assertEqual(alice["ses_usable_as_core_predictor"], "yes_with_caution")
        self.assertEqual(alice["race_usable_as_core_predictor"], "yes_with_caution")
        self.assertEqual(bob["ses_category"], "middle_class")
        self.assertEqual(bob["ses_usable_as_core_predictor"], "no_corpus_or_community_level")
        self.assertEqual(bob["local_demographic_header_available"], "yes")

    def test_local_chat_ses_is_used_when_no_manual_override_exists(self):
        metadata = [
            {
                "dataset": "LocalOnly",
                "child_id": "Child",
                "sex_values": "",
                "chi_id_group_values": "TD",
                "chi_id_ses_values": "WC",
                "chi_id_education_values": "",
                "demographic_header_values": "",
                "age_months_min": "",
                "age_months_max": "",
                "n_sessions": "",
                "child_nonempty_utterances": "",
                "caretaker_nonempty_utterances": "",
            }
        ]

        rows = build_codebook_rows(metadata, ({}, {}))

        self.assertEqual(rows[0]["sex"], "unknown")
        self.assertEqual(rows[0]["ses_category"], "working_class")
        self.assertEqual(rows[0]["ses_source_type"], "local_chat_id")
        self.assertEqual(rows[0]["ses_confidence"], "medium")
        self.assertEqual(rows[0]["local_chat_group_values"], "TD")

    def test_build_outputs_writes_full_pbm_and_summary_csvs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_path = root / "metadata.csv"
            overrides_path = root / "overrides.csv"
            output_path = root / "codebook.csv"
            pbm_path = root / "pbm.csv"
            summary_path = root / "summary.csv"
            metadata_fields = [
                "dataset",
                "child_id",
                "sex_values",
                "chi_id_group_values",
                "chi_id_ses_values",
                "chi_id_education_values",
                "demographic_header_values",
                "age_months_min",
                "age_months_max",
                "n_sessions",
                "child_nonempty_utterances",
                "caretaker_nonempty_utterances",
            ]
            with metadata_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=metadata_fields)
                writer.writeheader()
                writer.writerows(
                    [
                        {
                            "dataset": "Brown",
                            "child_id": "Adam",
                            "sex_values": "male",
                            "chi_id_group_values": "TD",
                            "chi_id_ses_values": "",
                            "chi_id_education_values": "",
                            "demographic_header_values": "",
                            "age_months_min": "27",
                            "age_months_max": "62",
                            "n_sessions": "55",
                            "child_nonempty_utterances": "100",
                            "caretaker_nonempty_utterances": "200",
                        },
                        {
                            "dataset": "Other",
                            "child_id": "Kid",
                            "sex_values": "female",
                            "chi_id_group_values": "",
                            "chi_id_ses_values": "",
                            "chi_id_education_values": "",
                            "demographic_header_values": "",
                            "age_months_min": "1",
                            "age_months_max": "2",
                            "n_sessions": "1",
                            "child_nonempty_utterances": "1",
                            "caretaker_nonempty_utterances": "1",
                        },
                    ]
                )
            with overrides_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "dataset",
                        "child_id",
                        "ses_category",
                        "ses_label",
                        "ses_scope",
                        "ses_source_type",
                        "ses_source_url",
                        "ses_source_note",
                        "ses_confidence",
                        "race_ethnicity",
                        "race_scope",
                        "race_source_type",
                        "race_source_url",
                        "race_source_note",
                        "race_confidence",
                        "parental_education",
                        "parental_education_scope",
                        "parental_education_source_url",
                        "parental_education_source_note",
                        "notes",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "dataset": "Brown",
                        "child_id": "Adam",
                        "ses_category": "middle_class",
                        "ses_label": "middle class",
                        "ses_scope": "child_specific",
                        "ses_source_type": "official",
                        "ses_source_url": "https://example.test",
                        "ses_source_note": "note",
                        "ses_confidence": "high",
                        "race_ethnicity": "Black",
                        "race_scope": "child_specific",
                        "race_source_type": "official",
                        "race_source_url": "https://example.test",
                        "race_source_note": "note",
                        "race_confidence": "high",
                        "parental_education": "unknown",
                        "parental_education_scope": "unknown",
                        "parental_education_source_url": "",
                        "parental_education_source_note": "",
                        "notes": "",
                    }
                )

            rows, summary = build_outputs(
                metadata_path, overrides_path, output_path, pbm_path, summary_path
            )

            self.assertEqual(len(rows), 2)
            self.assertTrue(output_path.exists())
            self.assertTrue(pbm_path.exists())
            self.assertTrue(summary_path.exists())
            with pbm_path.open(newline="", encoding="utf-8") as f:
                pbm_rows = list(csv.DictReader(f))
            self.assertEqual(len(pbm_rows), 1)
            self.assertEqual(pbm_rows[0]["dataset"], "Brown")
            self.assertEqual(list(pbm_rows[0].keys()), OUTPUT_COLUMNS)
            total = next(row for row in summary if row["dataset"] == "TOTAL")
            self.assertEqual(total["children"], "2")
            self.assertEqual(total["core_ses_usable_children"], "1")

    def test_summary_counts_dataset_and_total_categories(self):
        rows = [
            {
                "dataset": "A",
                "ses_category": "middle_class",
                "race_ethnicity": "unknown",
                "ses_usable_as_core_predictor": "yes_with_caution",
                "race_usable_as_core_predictor": "no",
            },
            {
                "dataset": "A",
                "ses_category": "unknown",
                "race_ethnicity": "White",
                "ses_usable_as_core_predictor": "no",
                "race_usable_as_core_predictor": "yes_with_caution",
            },
            {
                "dataset": "B",
                "ses_category": "working_class",
                "race_ethnicity": "unknown",
                "ses_usable_as_core_predictor": "no_corpus_or_community_level",
                "race_usable_as_core_predictor": "no",
            },
        ]

        summary = summarize_rows(rows)

        total = next(row for row in summary if row["dataset"] == "TOTAL")
        self.assertEqual(total["children"], "3")
        self.assertEqual(total["ses_known_children"], "2")
        self.assertIn("middle_class:1", total["ses_categories"])
        self.assertIn("working_class:1", total["ses_categories"])
        self.assertEqual(total["race_known_children_or_groups"], "1")

    def test_override_file_shape_is_valid(self):
        exact, wildcard = load_overrides(Path("configs/manual_child_demographic_overrides.csv"))

        self.assertIn(("Brown", "Adam"), exact)
        self.assertIn("Manchester", wildcard)
        self.assertEqual(exact[("Brown", "Adam")]["race_ethnicity"], "Black")


if __name__ == "__main__":
    unittest.main()
