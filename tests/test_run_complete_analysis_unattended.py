from __future__ import annotations

import unittest
from pathlib import Path


class CompleteAnalysisUnattendedRunnerTests(unittest.TestCase):
    def test_full_tests_gate_all_ready_analysis_components(self) -> None:
        root = Path(__file__).parents[1]
        source = (root / "scripts" / "run_complete_analysis_unattended.sh").read_text(
            encoding="utf-8"
        )
        test_position = source.index("-m unittest discover -s tests")
        analysis_position = source.index("build_complete_analysis_machine.py")
        self.assertLess(test_position, analysis_position)
        self.assertIn("set -euo pipefail", source)
        self.assertIn("word_mistral_nonpbm58", source)
        self.assertIn("BLOCKED_COMPONENTS", source)
        self.assertIn("git diff --check", source)


if __name__ == "__main__":
    unittest.main()
