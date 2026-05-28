import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_preprocessing_variant_probe import (  # noqa: E402
    build_output_rows,
    build_probe,
    build_variants,
    drop_target_special_form_tokens,
    expand_parenthetical_letters,
    remove_filler_tokens,
    write_outputs,
)


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestBuildPreprocessingVariantProbe(unittest.TestCase):
    def test_variant_transformations_cover_shortenings_fillers_and_special_forms(self):
        raw = "&-uh y(ou) want ow@i ?"
        variants = {variant.variant_id: variant.text for variant in build_variants(raw, "uh y want ow?")}

        self.assertEqual(expand_parenthetical_letters("y(ou) an(d)"), "you and")
        self.assertEqual(remove_filler_tokens("uh y want ow?"), "y want ow?")
        self.assertEqual(drop_target_special_form_tokens(raw), "uh y want?")
        self.assertEqual(variants["current_clean"], "uh y want ow?")
        self.assertEqual(variants["expand_shortenings"], "uh you want ow?")
        self.assertEqual(variants["remove_fillers"], "y want ow?")
        self.assertEqual(variants["expand_shortenings_remove_fillers"], "you want ow?")
        self.assertEqual(variants["preserve_special_at_suffixes"], "uh y want ow@i?")
        self.assertEqual(variants["drop_special_form_tokens"], "uh y want?")

    def test_build_output_rows_creates_long_and_wide_probe_rows(self):
        base_rows = [
            {
                "dataset": "ToyDataset",
                "child_id": "Toy",
                "source_group": "",
                "session_id": 1,
                "age_raw": "2;00.00",
                "age_months": 24.0,
                "sex": "female",
                "file": "toy.cha",
                "line_no": 2,
                "reference_line": "toy.cha:2",
                "utt_id": 1,
                "utt_id_role": 1,
                "speaker": "CHI",
                "speaker_group": "CHILD",
                "base_category": "filler_shortening_special",
                "has_filler": 1,
                "has_shortening": 1,
                "has_special_form": 1,
                "filler_types": "uh",
                "shortening_raw_tokens": "y(ou)",
                "special_form_raw_tokens": "ow@i",
                "special_form_markers": "i",
                "utterance": "&-uh y(ou) want ow@i ?",
                "utterance_clean": "uh y want ow?",
                "cleaned_word_count": 4,
            }
        ]

        long_rows, wide_rows = build_output_rows(base_rows)

        self.assertEqual(len(wide_rows), 1)
        self.assertEqual(len(long_rows), 7)
        self.assertEqual(wide_rows[0]["variant_expand_shortenings"], "uh you want ow?")
        self.assertEqual(
            [row["variant_id"] for row in long_rows],
            [
                "current_clean",
                "raw_chat_main_tier",
                "expand_shortenings",
                "remove_fillers",
                "expand_shortenings_remove_fillers",
                "preserve_special_at_suffixes",
                "drop_special_form_tokens",
            ],
        )
        self.assertEqual(long_rows[0]["utterance_for_scoring"], "uh y want ow?")
        self.assertEqual(long_rows[0]["word_count"], 4)
        self.assertEqual(long_rows[0]["morph_count"], 4)

    def test_write_outputs_writes_long_and_wide_csvs(self):
        base_rows = [
            {
                "dataset": "ToyDataset",
                "child_id": "Toy",
                "source_group": "",
                "session_id": 1,
                "age_raw": "2;00.00",
                "age_months": 24.0,
                "sex": "female",
                "file": "toy.cha",
                "line_no": 2,
                "reference_line": "toy.cha:2",
                "utt_id": 1,
                "utt_id_role": 1,
                "speaker": "CHI",
                "speaker_group": "CHILD",
                "base_category": "filler_shortening_special",
                "has_filler": 1,
                "has_shortening": 1,
                "has_special_form": 1,
                "filler_types": "uh",
                "shortening_raw_tokens": "y(ou)",
                "special_form_raw_tokens": "ow@i",
                "special_form_markers": "i",
                "utterance": "&-uh y(ou) want ow@i ?",
                "utterance_clean": "uh y want ow?",
                "cleaned_word_count": 4,
            }
        ]
        long_rows, wide_rows = build_output_rows(base_rows)

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "probe"
            write_outputs(
                out_dir,
                long_rows=long_rows,
                wide_rows=wide_rows,
                datasets=("ToyDataset",),
                speakers=("CHI",),
                raw_bases={"ToyDataset": Path(tmp)},
                examples_per_category=1,
                max_base_examples=1,
                max_cleaned_words=12,
            )

            written_long = read_rows(out_dir / "preprocessing_variant_probe_long.csv")
            written_wide = read_rows(out_dir / "preprocessing_variant_probe_wide.csv")

        self.assertEqual(len(written_long), 7)
        self.assertEqual(written_wide[0]["variant_expand_shortenings"], "uh you want ow?")


if __name__ == "__main__":
    unittest.main()
