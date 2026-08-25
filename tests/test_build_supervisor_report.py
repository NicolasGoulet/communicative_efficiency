import sys
import unittest
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_supervisor_report import (  # noqa: E402
    build_age_distribution_summary,
    build_corpus_summary,
    build_sample_summary,
    distribution_view_specs,
    render_data_description,
    render_distribution_gallery,
    render_index,
)


class SupervisorReportRestartTests(unittest.TestCase):
    def test_index_recreates_july_card_pattern_from_editable_markdown(self):
        page = render_index(
            "# Supervisor Report\n\n"
            "Supervisor-facing materials.\n\n"
            "## [Data description](supervisor_data_description.md)\n\n"
            "Corpora, children, and developmental coverage.\n"
        )

        self.assertIn("Supervisor Report", page)
        self.assertEqual(page.count('class="card"'), 1)
        self.assertIn('href="supervisor_data_description.html"', page)
        self.assertIn("Data description", page)
        self.assertNotIn("Route 1", page)
        self.assertNotIn("Route 2", page)
        self.assertNotIn("Word-level", page)

    def test_distribution_views_are_all_two_groups_and_one_per_corpus(self):
        corpora = [
            "Belfast",
            "Brown",
            "Demetras1",
            "Forrester",
            "Kuczaj",
            "Lara",
            "MPI-EVA-Manchester",
            "Manchester",
            "Post",
            "Providence",
            "Sachs",
            "Weist",
            "Wells",
        ]

        views = distribution_view_specs(corpora)

        self.assertEqual(len(views), 16)
        self.assertEqual(views[0]["label"], "All 79 children")
        self.assertEqual(
            views[1]["label"], "Brown, Manchester, and Providence (21 children)"
        )
        self.assertEqual(views[2]["label"], "Other 10 corpora (58 children)")
        self.assertEqual([view["corpus"] for view in views[3:]], corpora)
        self.assertNotIn("PBM", " ".join(view["label"] for view in views))

    def test_age_distribution_summary_builds_group_and_corpus_counts(self):
        child = pd.DataFrame(
            [
                {"dataset": "Brown", "age_bin": "006-023"},
                {"dataset": "Brown", "age_bin": "006-023"},
                {"dataset": "Belfast", "age_bin": "024-029"},
            ]
        )
        caregiver = pd.DataFrame(
            [
                {"dataset": "Brown", "age_bin": "006-023"},
                {"dataset": "Belfast", "age_bin": "024-029"},
                {"dataset": "Belfast", "age_bin": "024-029"},
            ]
        )

        summary = build_age_distribution_summary(
            child,
            caregiver,
            corpora=["Belfast", "Brown"],
        )

        def count(view_id, role, age_bin):
            row = summary[
                summary["view_id"].eq(view_id)
                & summary["role"].eq(role)
                & summary["age_bin"].eq(age_bin)
            ]
            return int(row.iloc[0]["rows"])

        self.assertEqual(count("all_children", "child", "006-023"), 2)
        self.assertEqual(count("three_corpora", "child", "006-023"), 2)
        self.assertEqual(count("other_corpora", "child", "024-029"), 1)
        self.assertEqual(count("corpus_belfast", "caretaker", "024-029"), 2)
        self.assertEqual(count("corpus_brown", "caretaker", "006-023"), 1)

    def test_distribution_gallery_has_sixteen_views_and_overlay_navigation(self):
        views = [
            {
                "id": f"view_{index}",
                "label": f"View {index + 1}",
                "title": f"Title {index + 1}",
                "src": f"plot_{index + 1}.png",
                "corpus": None,
            }
            for index in range(16)
        ]

        gallery = render_distribution_gallery(views)

        self.assertIn('aria-label="Previous distribution"', gallery)
        self.assertIn('aria-label="Next distribution"', gallery)
        self.assertIn("1 of 16", gallery)
        self.assertEqual(gallery.count('"src":"plot_'), 16)

    def test_sample_summary_keeps_the_two_analysis_groups_separate(self):
        sample_flow = pd.DataFrame(
            [
                {
                    "role": role,
                    "scope": scope,
                    "step": "source_rows",
                    "rows": rows,
                    "children": children,
                    "corpora": corpora,
                    "sessions": sessions,
                }
                for role, scope, rows, children, corpora, sessions in [
                    ("child", "pbm_discovery", 100, 2, 1, 10),
                    ("caretaker", "pbm_discovery", 150, 2, 1, 11),
                    ("child", "non_pbm_confirmation", 200, 3, 2, 20),
                    ("caretaker", "non_pbm_confirmation", 250, 3, 2, 21),
                    ("child", "all79_descriptive", 300, 5, 3, 30),
                    ("caretaker", "all79_descriptive", 400, 5, 3, 31),
                ]
            ]
        )

        summary = build_sample_summary(sample_flow)

        self.assertEqual(
            summary["sample"].tolist(),
            [
                "Brown, Manchester, and Providence",
                "Other 10 corpora",
                "All 13 corpora combined",
            ],
        )
        self.assertEqual(summary["child_utterances"].tolist(), [100, 200, 300])
        self.assertEqual(summary["caregiver_utterances"].tolist(), [150, 250, 400])
        self.assertEqual(summary["children"].tolist(), [2, 3, 5])

    def test_corpus_summary_assigns_the_three_corpora_to_the_first_group(self):
        coverage = pd.DataFrame(
            [
                {
                    "role": "child",
                    "scope": "all79_descriptive",
                    "dataset": dataset,
                    "child_key": child,
                    "rows": rows,
                    "sessions": sessions,
                    "age_min": age_min,
                    "age_max": age_max,
                }
                for dataset, child, rows, sessions, age_min, age_max in [
                    ("Brown", "Brown/A", 10, 2, 18.0, 24.0),
                    ("Brown", "Brown/B", 20, 3, 20.0, 30.0),
                    ("Belfast", "Belfast/C", 30, 4, 25.0, 40.0),
                ]
            ]
        )

        summary = build_corpus_summary(coverage)

        brown = summary[summary["corpus"].eq("Brown")].iloc[0]
        belfast = summary[summary["corpus"].eq("Belfast")].iloc[0]
        self.assertEqual(brown["sample_role"], "Brown, Manchester, and Providence")
        self.assertEqual(brown["children"], 2)
        self.assertEqual(brown["child_utterances"], 30)
        self.assertEqual(belfast["sample_role"], "Other 10 corpora")

    def test_data_page_is_rendered_from_markdown_with_gallery(self):
        page = render_data_description(
            "# Data description\n\n"
            "[← Back to report home](supervisor_report.md)\n\n"
            "## Developmental age distributions\n\n"
            "<!-- AGE_DISTRIBUTION_GALLERY_START -->\n"
            "![All children](plot.png)\n"
            "<!-- AGE_DISTRIBUTION_GALLERY_END -->\n\n"
            "## Corpora and children\n",
            distribution_views=[
                {
                    "id": "all_children",
                    "label": "All 79 children",
                    "title": "Longitudinal utterance coverage by developmental age",
                    "src": "../results/example/age.png",
                    "corpus": None,
                }
            ],
        )

        self.assertIn('href="supervisor_report.html"', page)
        self.assertIn("Data description", page)
        self.assertIn("Developmental age distributions", page)
        self.assertIn("Corpora and children", page)
        self.assertIn('src="../results/example/age.png"', page)
        self.assertIn('aria-label="Previous distribution"', page)

    def test_editable_markdown_does_not_expose_internal_workflow_language(self):
        markdown_path = Path(__file__).resolve().parents[1] / "docs/supervisor_data_description.md"
        text = markdown_path.read_text(encoding="utf-8")

        self.assertNotIn("Do not add these rows together", text)
        self.assertNotIn("descriptive coverage only", text)
        self.assertNotIn("strict-naturalistic", text)
        self.assertNotIn("PBM discovery", text)
        self.assertNotIn("Non-PBM confirmation", text)


if __name__ == "__main__":
    unittest.main()
