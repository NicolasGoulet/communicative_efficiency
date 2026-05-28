import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from custom_age_bins import (  # noqa: E402
    AgeBin,
    count_in_range,
    find_age_bin,
    floor_age_month,
    make_merged_early_bins,
    load_age_bins_config,
    make_standard_bins,
    make_threshold_early_bins,
    round_up_to_full_bin_end,
    write_age_bins_config,
)


class TestCustomAgeBins(unittest.TestCase):
    def test_floor_age_month_handles_numeric_and_missing_values(self):
        self.assertEqual(floor_age_month("18.9"), 18)
        self.assertEqual(floor_age_month(23.0), 23)
        self.assertIsNone(floor_age_month(""))
        self.assertIsNone(floor_age_month(float("nan")))

    def test_threshold_early_bins_steal_months_until_first_bin_reaches_threshold(self):
        counts = {
            6: 100,
            12: 900,
            17: 9_000,
            18: 6_000,
            19: 5_000,
            20: 2_000,
            24: 1,
            30: 1,
        }

        bins = make_threshold_early_bins(counts, threshold=20_000, max_month=35)

        self.assertEqual(bins[:4], [AgeBin(6, 19), AgeBin(20, 23), AgeBin(24, 29), AgeBin(30, 35)])
        self.assertLess(count_in_range(counts, 6, 18), 20_000)
        self.assertGreaterEqual(count_in_range(counts, 6, 19), 20_000)

    def test_threshold_early_bins_keep_remainder_only_when_months_remain(self):
        counts = {month: 0 for month in range(6, 24)}

        bins = make_threshold_early_bins(counts, threshold=20_000, max_month=29)

        self.assertEqual(bins, [AgeBin(6, 23), AgeBin(24, 29)])

    def test_standard_bins_are_inclusive_and_partial_at_end(self):
        self.assertEqual(make_standard_bins(24, 32, 6), [AgeBin(24, 29), AgeBin(30, 32)])

    def test_round_up_to_full_bin_end_preserves_later_six_month_intervals(self):
        self.assertEqual(round_up_to_full_bin_end(24, 62, 6), 65)
        self.assertEqual(round_up_to_full_bin_end(24, 65, 6), 65)

    def test_threshold_early_bins_preserve_full_later_six_month_intervals(self):
        bins = make_threshold_early_bins({18: 20_000, 62: 1}, threshold=20_000)

        self.assertEqual(bins[-1], AgeBin(60, 65))

    def test_merged_early_bins_use_one_006_023_bin_then_six_month_bins(self):
        bins = make_merged_early_bins(max_month=62)

        self.assertEqual(
            bins,
            [
                AgeBin(6, 23),
                AgeBin(24, 29),
                AgeBin(30, 35),
                AgeBin(36, 41),
                AgeBin(42, 47),
                AgeBin(48, 53),
                AgeBin(54, 59),
                AgeBin(60, 65),
            ],
        )

    def test_find_age_bin_uses_floor_month(self):
        bins = [AgeBin(6, 18), AgeBin(19, 23)]

        self.assertEqual(find_age_bin(18.99, bins), AgeBin(6, 18))
        self.assertEqual(find_age_bin("19.0", bins), AgeBin(19, 23))
        self.assertIsNone(find_age_bin(5.99, bins))

    def test_write_and_load_age_bins_config_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "age_bins.json"
            bins = [AgeBin(6, 18), AgeBin(19, 23)]

            write_age_bins_config(path, bins=bins, strategy="threshold_early", threshold=20_000)
            loaded = load_age_bins_config(path)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(loaded, bins)
        self.assertEqual(payload["strategy"], "threshold_early")
        self.assertEqual(payload["threshold"], 20_000)


if __name__ == "__main__":
    unittest.main()
