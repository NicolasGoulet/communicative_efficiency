import unittest

import pandas as pd

from src.build_two_final_model_candidate_estimator_plots import selected_predictions, summarize_slopes


class TwoFinalModelCandidateEstimatorPlotTests(unittest.TestCase):
    def test_selected_predictions_keeps_requested_formula_estimators_and_fixed_values(self):
        predictions = pd.DataFrame(
            [
                {
                    "formula_id": "F01",
                    "estimator_id": "row_ols_fe_cluster",
                    "fixed_effort_value": 2,
                    "age_months": 18,
                    "predicted_sum_bits": 10.0,
                },
                {
                    "formula_id": "F01",
                    "estimator_id": "agg_gee_gaussian",
                    "fixed_effort_value": 6,
                    "age_months": 18,
                    "predicted_sum_bits": 20.0,
                },
                {
                    "formula_id": "F01",
                    "estimator_id": "agg_gee_gaussian",
                    "fixed_effort_value": 4,
                    "age_months": 18,
                    "predicted_sum_bits": 99.0,
                },
                {
                    "formula_id": "F02",
                    "estimator_id": "row_ols_fe_cluster",
                    "fixed_effort_value": 2,
                    "age_months": 18,
                    "predicted_sum_bits": 99.0,
                },
            ]
        )

        selected = selected_predictions(
            predictions,
            formula_id="F01",
            estimator_ids=("row_ols_fe_cluster", "agg_gee_gaussian"),
            fixed_values=(2, 6),
        )

        self.assertEqual(selected["formula_id"].tolist(), ["F01", "F01"])
        self.assertEqual(selected["estimator_id"].tolist(), ["row_ols_fe_cluster", "agg_gee_gaussian"])
        self.assertEqual(selected["fixed_effort_value"].tolist(), [2, 6])
        self.assertNotIn(99.0, selected["predicted_sum_bits"].tolist())

    def test_summarize_slopes_returns_only_plotted_slices(self):
        slopes = pd.DataFrame(
            [
                {
                    "formula_id": "F01",
                    "formula_label": "Age at fixed effort",
                    "estimator_id": "row_ols_fe_cluster",
                    "estimator_label": "Row",
                    "fixed_effort_value": 2,
                    "slope_bits_per_6_months": -0.7,
                    "direction": "downward",
                },
                {
                    "formula_id": "F01",
                    "formula_label": "Age at fixed effort",
                    "estimator_id": "row_ols_fe_cluster",
                    "estimator_label": "Row",
                    "fixed_effort_value": 3,
                    "slope_bits_per_6_months": -0.7,
                    "direction": "downward",
                },
                {
                    "formula_id": "F02",
                    "formula_label": "Age by effort",
                    "estimator_id": "row_ols_fe_cluster",
                    "estimator_label": "Row",
                    "fixed_effort_value": 2,
                    "slope_bits_per_6_months": -0.8,
                    "direction": "downward",
                },
            ]
        )

        summary = summarize_slopes(
            slopes,
            formula_ids=("F01",),
            estimator_ids=("row_ols_fe_cluster",),
            fixed_values=(2,),
        )

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary.loc[0, "formula_id"], "F01")
        self.assertEqual(summary.loc[0, "fixed_effort_value"], 2)


if __name__ == "__main__":
    unittest.main()
