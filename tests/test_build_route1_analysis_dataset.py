import csv
import tempfile
import unittest
from pathlib import Path

import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from build_route1_analysis_dataset import (
    ANALYSIS_COLUMNS,
    build_analysis_dataset,
    count_effort,
    parse_scored_file,
)


class TestBuildRoute1AnalysisDataset(unittest.TestCase):
    def test_count_effort_uses_selected_surface_measures(self):
        counts = count_effort("I'm walking dogs.")

        self.assertEqual(counts.nb_words, 3)
        self.assertEqual(counts.nb_morphemes, 6)
        self.assertGreaterEqual(counts.nb_syllables_cmu_or_pkg, 3)
        self.assertGreaterEqual(counts.nb_syllables_pkg, 3)
        self.assertGreaterEqual(counts.nb_phonemes, 8)

    def test_count_effort_never_zeroes_word_like_filler_or_unicode_forms(self):
        filler = count_effort("hm?")
        eth = count_effort("ð.")

        self.assertEqual(filler.nb_words, 1)
        self.assertGreaterEqual(filler.nb_syllables_cmu_or_pkg, 1)
        self.assertGreaterEqual(filler.nb_phonemes, 1)
        self.assertEqual(eth.nb_words, 1)
        self.assertGreaterEqual(eth.nb_syllables_cmu_or_pkg, 1)
        self.assertGreaterEqual(eth.nb_phonemes, 1)

    def test_parse_scored_file_keeps_variant_and_target_column_aligned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = (
                root
                / "WITH_context"
                / "k2"
                / "mistral"
                / "Brown"
                / "Adam"
                / "chi.surprisal_scoring__trigram.scored.csv"
            )
            path.parent.mkdir(parents=True)
            path.write_text("", encoding="utf-8")

            spec = parse_scored_file(root, path, "toy_source")

        self.assertEqual(spec.score_source, "toy_source")
        self.assertEqual(spec.context_condition, "WITH_context")
        self.assertEqual(spec.context_k, "k2")
        self.assertEqual(spec.role, "child")
        self.assertEqual(spec.target_variant, "trigram")
        self.assertEqual(spec.target_column, "trigram_model_utterance_bin6")

    def test_build_dataset_writes_real_baseline_and_caretaker_rows_with_effort_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            base = root / "WITHOUT_context" / "k0" / "mistral" / "Toy" / "Ada"
            base.mkdir(parents=True)
            row = scored_child_row(
                chi="cat.",
                random="banana.",
                text_cols='["chi_utterance_clean"]',
            )
            write_scored_csv(base / "chi.surprisal_scoring__real.scored.csv", [row])
            random_row = dict(row)
            random_row["text_cols_used"] = '["random_model_utterance_bin6"]'
            random_row["sum_bits"] = "12"
            write_scored_csv(base / "chi.surprisal_scoring__random.scored.csv", [random_row])
            write_scored_csv(
                base / "caretakers.surprisal_scoring__caretaker.scored.csv",
                [
                    scored_caretaker_row(
                        caretaker="hello there.",
                        text_cols='["caretaker_utterance_clean"]',
                    )
                ],
            )

            out = Path(tmp) / "out.csv"
            file_audit = Path(tmp) / "file_audit.csv"
            variant_audit = Path(tmp) / "variant_audit.csv"
            schema = Path(tmp) / "schema.json"
            result = build_analysis_dataset(
                scored_roots=[("toy", root)],
                output_csv=out,
                file_audit_csv=file_audit,
                variant_audit_csv=variant_audit,
                schema_json=schema,
            )
            rows = read_csv(out)
            audits = read_csv(variant_audit)
            schema_exists = schema.is_file()

        self.assertEqual(result["rows_written"], 3)
        self.assertEqual(list(rows[0]), ANALYSIS_COLUMNS)
        by_variant = {row["target_variant"]: row for row in rows}
        self.assertEqual(by_variant["real"]["target_utterance_clean"], "cat.")
        self.assertEqual(by_variant["random"]["target_utterance_clean"], "banana.")
        self.assertEqual(by_variant["caretaker"]["target_utterance_clean"], "hello there.")
        self.assertEqual(by_variant["random"]["nb_words"], "1")
        self.assertEqual(by_variant["random"]["child_real_nb_words"], "1")
        self.assertEqual(by_variant["random"]["same_word_count_as_child_real"], "1")
        self.assertEqual(by_variant["random"]["delta_nb_words_vs_child_real"], "0")
        self.assertEqual(by_variant["random"]["delta_nb_syllables_cmu_or_pkg_vs_child_real"], "2")
        self.assertEqual(by_variant["caretaker"]["child_real_nb_words"], "")
        self.assertTrue(schema_exists)

        random_audit = [
            row
            for row in audits
            if row["target_variant"] == "random" and row["context_k"] == "k0"
        ][0]
        self.assertEqual(random_audit["rows"], "1")
        self.assertEqual(random_audit["mean_same_word_count_as_child_real"], "1")
        self.assertEqual(random_audit["mean_bits_per_token"], "5")

    def test_build_dataset_records_used_context_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            base = root / "WITH_context" / "k1" / "mistral" / "Toy" / "Ada"
            base.mkdir(parents=True)
            row = scored_child_row(
                chi="cat.",
                random="banana.",
                text_cols='["chi_utterance_clean"]',
                context_col_used="context_k1",
                context_k1="look here.",
            )
            write_scored_csv(base / "chi.surprisal_scoring__real.scored.csv", [row])

            out = Path(tmp) / "out.csv"
            build_analysis_dataset(
                scored_roots=[("toy", root)],
                output_csv=out,
                file_audit_csv=Path(tmp) / "file_audit.csv",
                variant_audit_csv=Path(tmp) / "variant_audit.csv",
                schema_json=Path(tmp) / "schema.json",
            )
            rows = read_csv(out)

        self.assertEqual(rows[0]["context_k"], "k1")
        self.assertEqual(rows[0]["context_col_used"], "context_k1")
        self.assertEqual(rows[0]["context_text"], "look here.")
        self.assertTrue(rows[0]["context_text_hash"])

    def test_strict_audit_raises_on_same_length_baseline_word_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            base = root / "WITHOUT_context" / "k0" / "mistral" / "Toy" / "Ada"
            base.mkdir(parents=True)
            row = scored_child_row(
                chi="cat.",
                random="big banana.",
                text_cols='["random_model_utterance_bin6"]',
            )
            write_scored_csv(base / "chi.surprisal_scoring__random.scored.csv", [row])

            with self.assertRaisesRegex(ValueError, "child_word_count_mismatch_rows=1"):
                build_analysis_dataset(
                    scored_roots=[("toy", root)],
                    output_csv=Path(tmp) / "out.csv",
                    file_audit_csv=Path(tmp) / "file_audit.csv",
                    variant_audit_csv=Path(tmp) / "variant_audit.csv",
                    schema_json=Path(tmp) / "schema.json",
                )

    def test_blank_unscored_generated_targets_are_skipped_but_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "scored"
            base = root / "WITHOUT_context" / "k0" / "mistral" / "Toy" / "Ada"
            base.mkdir(parents=True)
            row = scored_child_row(
                chi="cat.",
                random="",
                text_cols='["random_model_utterance_bin6"]',
            )
            row["sum_bits"] = ""
            row["mean_bits_per_token"] = ""
            row["n_eval_tokens"] = ""
            write_scored_csv(base / "chi.surprisal_scoring__random.scored.csv", [row])

            out = Path(tmp) / "out.csv"
            file_audit = Path(tmp) / "file_audit.csv"
            result = build_analysis_dataset(
                scored_roots=[("toy", root)],
                output_csv=out,
                file_audit_csv=file_audit,
                variant_audit_csv=Path(tmp) / "variant_audit.csv",
                schema_json=Path(tmp) / "schema.json",
            )
            rows = read_csv(out)
            audits = read_csv(file_audit)

        self.assertEqual(result["rows_written"], 0)
        self.assertEqual(rows, [])
        self.assertEqual(audits[0]["rows_read"], "1")
        self.assertEqual(audits[0]["rows_written"], "0")
        self.assertEqual(audits[0]["rows_skipped_unscored_or_empty"], "1")
        self.assertEqual(audits[0]["blank_target_rows"], "1")
        self.assertEqual(audits[0]["zero_word_rows"], "1")
        self.assertEqual(audits[0]["missing_sum_bits_rows"], "1")


def scored_child_row(
    *,
    chi: str,
    random: str,
    text_cols: str,
    context_col_used: str = "",
    context_k1: str = "",
) -> dict[str, str]:
    return {
        "dataset": "Toy",
        "child_id": "Ada",
        "source_group": "Toy",
        "session_id": "1",
        "age_months": "23.5",
        "file": "Ada/010000.cha",
        "line_no": "12",
        "utt_id": "7",
        "context_k1": context_k1,
        "context_k2": "",
        "context_k3": "",
        "chi_utterance_clean": chi,
        "random_model_utterance_bin6": random,
        "unigram_model_utterance_bin6": "cat.",
        "bigram_model_utterance_bin6": "cat.",
        "trigram_model_utterance_bin6": "cat.",
        "mean_bits_per_token": "5",
        "sum_bits": "10",
        "n_eval_tokens": "2",
        "model_used": "mistral",
        "units_used": "bits",
        "text_cols_used": text_cols,
        "context_col_used": context_col_used,
        "skip_zero_counts": "False",
        "word_count_col_used": "word_count",
        "morph_count_col_used": "morph_count",
        "min_word_count": "1",
        "min_morph_count": "1",
        "max_rows_used": "",
    }


def scored_caretaker_row(*, caretaker: str, text_cols: str) -> dict[str, str]:
    row = scored_child_row(chi="cat.", random="banana.", text_cols=text_cols)
    row["speaker"] = "MOT"
    row["caretaker_utterance_clean"] = caretaker
    return row


def write_scored_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
