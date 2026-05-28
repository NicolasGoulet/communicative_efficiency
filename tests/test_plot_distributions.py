import sys
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from plot_distributions import (
    CLINICAL_PROBE_DATASETS,
    DEFAULT_DATASETS,
    NATURALISTIC_CAREGIVER_CHILD_DATASETS,
    STRICT_NATURALISTIC_PARENT_CHILD_DATASETS,
    STRUCTURED_OBSERVATIONAL_CAREGIVER_CHILD_DATASETS,
    add_age_bins,
    utterance_counts_by_age_bin,
)


class TestPlotDistributions(unittest.TestCase):
    def test_default_datasets_include_mpi_eva_manchester(self):
        self.assertIn("MPI-EVA-Manchester", DEFAULT_DATASETS)

    def test_default_datasets_include_new_naturalistic_longitudinal_datasets(self):
        for dataset in ("Belfast", "Wells"):
            self.assertIn(dataset, DEFAULT_DATASETS)
        for dataset in ("Lara", "Sachs", "Weist", "Kuczaj", "Post", "Demetras1", "Forrester"):
            self.assertIn(dataset, DEFAULT_DATASETS)
        self.assertNotIn("Cummings", DEFAULT_DATASETS)
        self.assertNotIn("Champaign", DEFAULT_DATASETS)
        self.assertNotIn("EHS", DEFAULT_DATASETS)

    def test_dataset_groups_keep_clinical_probes_out_of_naturalistic_default(self):
        self.assertEqual(DEFAULT_DATASETS, STRICT_NATURALISTIC_PARENT_CHILD_DATASETS)
        self.assertEqual(NATURALISTIC_CAREGIVER_CHILD_DATASETS, STRICT_NATURALISTIC_PARENT_CHILD_DATASETS)
        self.assertIn("Cummings", CLINICAL_PROBE_DATASETS)
        self.assertNotIn("Cummings", NATURALISTIC_CAREGIVER_CHILD_DATASETS)
        self.assertIn("Champaign", STRUCTURED_OBSERVATIONAL_CAREGIVER_CHILD_DATASETS)
        self.assertIn("EHS", STRUCTURED_OBSERVATIONAL_CAREGIVER_CHILD_DATASETS)
        self.assertNotIn("Champaign", NATURALISTIC_CAREGIVER_CHILD_DATASETS)
        self.assertNotIn("EHS", NATURALISTIC_CAREGIVER_CHILD_DATASETS)

    def test_utterance_counts_by_age_bin_counts_totals_and_groups(self):
        df = pd.DataFrame(
            {
                "age_months": [12.0, 13.5, 18.0, 19.0, None],
                "dataset": ["A", "B", "A", "B", "A"],
            }
        )
        binned = add_age_bins(df, age_bin_months=6)

        counts = utterance_counts_by_age_bin(binned, "age_bin_6m", "dataset")

        self.assertEqual(counts["age_bin_6m"].tolist(), ["012-017", "018-023"])
        self.assertEqual(counts["all_utterances"].tolist(), [2, 2])
        self.assertEqual(counts["A"].tolist(), [1, 1])
        self.assertEqual(counts["B"].tolist(), [1, 1])


if __name__ == "__main__":
    unittest.main()
