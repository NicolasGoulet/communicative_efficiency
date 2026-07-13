import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.child_coverage_data import (
    apply_online_value_patches,
    build_child_metadata_profile,
    field_availability,
    read_online_research_audit,
)
from src.child_coverage_report import md_table


class ChildCoverageReportTests(unittest.TestCase):
    def test_online_patch_fills_unknown_child_value_without_overwriting_known_value(self):
        profile = pd.DataFrame(
            [
                {"dataset": "Corpus", "child_id": "A", "sex": "unknown"},
                {"dataset": "Corpus", "child_id": "B", "sex": "male"},
            ]
        )
        patches = pd.DataFrame(
            [
                {
                    "dataset": "Corpus",
                    "child_id": "A",
                    "field": "sex",
                    "value": "female",
                    "scope": "child_specific",
                    "source_type": "official_page",
                    "source_url": "https://example.test/a",
                    "source_note": "pronoun evidence",
                    "confidence": "medium",
                    "replace_policy": "fill_unknown",
                    "coding_note": "filled local gap",
                },
                {
                    "dataset": "Corpus",
                    "child_id": "B",
                    "field": "sex",
                    "value": "female",
                    "scope": "child_specific",
                    "source_type": "official_page",
                    "source_url": "https://example.test/b",
                    "source_note": "should not replace",
                    "confidence": "medium",
                    "replace_policy": "fill_unknown",
                    "coding_note": "existing value should win",
                },
            ]
        )

        patched = apply_online_value_patches(profile, patches)

        self.assertEqual(patched.loc[patched["child_id"] == "A", "sex"].item(), "female")
        self.assertEqual(patched.loc[patched["child_id"] == "B", "sex"].item(), "male")
        self.assertEqual(
            patched.loc[patched["child_id"] == "A", "sex_source_url"].item(),
            "https://example.test/a",
        )
        self.assertEqual(
            patched.loc[patched["child_id"] == "B", "sex_source_url"].item(),
            "local_extracted_metadata",
        )

    def test_build_profile_applies_online_patch_before_availability_summary(self):
        counts = pd.DataFrame(
            [
                {
                    "dataset": "Corpus",
                    "child_id": "A",
                    "child_utterances": 10,
                    "child_sessions": 2,
                    "child_files": 2,
                    "child_age_min_months": 12,
                    "child_age_max_months": 24,
                    "child_age_bins": 2,
                    "child_label": "Corpus / A",
                }
            ]
        )
        codebook = pd.DataFrame(
            [
                {
                    "dataset": "Corpus",
                    "child_id": "A",
                    "sex": "unknown",
                    "ses_category": "middle_class",
                    "ses_label": "middle class",
                    "ses_scope": "child_specific",
                    "ses_confidence": "high",
                    "race_ethnicity": "unknown",
                    "race_scope": "unknown",
                    "race_confidence": "unknown",
                    "parental_education": "unknown",
                    "parental_education_scope": "unknown",
                    "ses_usable_as_core_predictor": "yes_with_caution",
                    "race_usable_as_core_predictor": "no",
                }
            ]
        )
        patches = pd.DataFrame(
            [
                {
                    "dataset": "Corpus",
                    "child_id": "A",
                    "field": "sex",
                    "value": "female",
                    "scope": "child_specific",
                    "source_type": "official_page",
                    "source_url": "https://example.test",
                    "source_note": "source",
                    "confidence": "medium",
                    "replace_policy": "fill_unknown",
                    "coding_note": "patched",
                }
            ]
        )

        profile = build_child_metadata_profile(counts, codebook, online_patches=patches)
        availability = field_availability(profile)
        sex_row = availability.loc[availability["field"] == "Sex / gender marker"].iloc[0]

        self.assertEqual(profile["sex"].item(), "female")
        self.assertEqual(int(sex_row["known_child_specific"]), 1)
        self.assertEqual(int(sex_row["unknown_or_unavailable"]), 0)

    def test_read_online_research_audit_tolerates_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.csv"
            audit = read_online_research_audit(missing)

        self.assertTrue(audit.empty)
        self.assertIn("dataset", audit.columns)
        self.assertIn("coding_decision", audit.columns)

    def test_md_table_escapes_pipe_characters(self):
        table = md_table(pd.DataFrame([{"note": "a | b"}]))

        self.assertIn("a \\| b", table)


if __name__ == "__main__":
    unittest.main()
