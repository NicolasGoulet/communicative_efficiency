import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_supervisor_candidate_additions_report import (  # noqa: E402
    candidate_figures,
    candidate_summary_table,
    predictor_dictionary,
)


class SupervisorCandidateAdditionsReportTests(unittest.TestCase):
    def test_predictor_dictionary_names_core_new_predictors(self):
        predictors = set(predictor_dictionary()["predictor"])

        self.assertIn("context_entropy_bits", predictors)
        self.assertIn("exact_target_frequency_bits", predictors)
        self.assertIn("question_type", predictors)

    def test_candidate_figures_label_route2_as_exploratory(self):
        figures = candidate_figures()
        route2 = [figure for figure in figures if "Route 2" in figure.title]

        self.assertTrue(route2)
        self.assertTrue(all("Exploratory" in figure.placement for figure in route2))

    def test_candidate_summary_table_keeps_caveats(self):
        summary = candidate_summary_table(candidate_figures())

        caveats = " ".join(summary["caveat"].fillna("").astype(str))
        self.assertIn("Real-child only", caveats)
        self.assertIn("full phone/word informativity", caveats)


if __name__ == "__main__":
    unittest.main()
