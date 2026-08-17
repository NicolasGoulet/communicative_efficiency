from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from src.prepare_hall_snapshot import (
    classify_situation,
    parse_hall_chat,
    prepare_hall_snapshot,
    resolve_child_demographics,
)


def write_chat(
    path: Path,
    *,
    child_id: str,
    ses: str = "",
    body: str = "*CHI:\thello .\n*MOT:\thi .\n",
    comment: str = "",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    comment_line = f"@Comment:\t{comment}\n" if comment else ""
    path.write_text(
        "@UTF8\n"
        "@Participants:\tCHI Target_Child, MOT Mother, TEA Teacher, MCH Child\n"
        f"@ID:\teng|Hall|CHI|4;09.|female|TD|{ses}|Target_Child|||\n"
        "@ID:\teng|Hall|MOT||female|||Mother|||\n"
        "@ID:\teng|Hall|TEA|||||Teacher|||\n"
        "@ID:\teng|Hall|MCH|||||Child|||\n"
        f"@Media:\t{child_id}, audio\n"
        f"{comment_line}"
        f"{body}"
        "@End\n",
        encoding="utf-8",
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class HallSnapshotTests(unittest.TestCase):
    def test_setting_classifier_does_not_call_predeparture_home_speech_school(self) -> None:
        self.assertEqual(classify_situation("prior to departure for school"), ("home", 0))
        self.assertEqual(classify_situation("to departure for school"), ("home", 0))
        self.assertEqual(classify_situation("before leaving home"), ("home", 0))
        self.assertEqual(classify_situation("on the way to school"), ("transition", 0))

    def test_parser_preserves_situation_setting_roles_and_turn_adjacency(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ali.cha"
            write_chat(
                path,
                child_id="ali",
                ses="Black,UC",
                body=(
                    "@Situation:\tbefore school at home\n"
                    "*MOT:\tget your coat .\n"
                    "*CHI:\tokay .\n"
                    "@Situation:\tfree play (at school)\n"
                    "*MCH:\tmy turn .\n"
                    "*TEA:\tshare please .\n"
                    "*CHI:\there .\n"
                ),
            )

            document = parse_hall_chat(path, source_group="BlackPro")

        self.assertEqual(document.child_id_ses_raw, "Black,UC")
        self.assertEqual([row["speaker_role_group"] for row in document.rows], [
            "adult_interlocutor", "target_child", "child_peer",
            "adult_interlocutor", "target_child",
        ])
        self.assertEqual([row["setting_auto"] for row in document.rows], [
            "home", "home", "school", "school", "school",
        ])
        self.assertEqual(document.rows[1]["previous_main_speaker"], "MOT")
        self.assertEqual(document.rows[1]["child_after_adult"], 1)
        self.assertEqual(document.rows[-1]["previous_main_speaker"], "TEA")
        self.assertEqual(document.rows[-1]["child_after_adult"], 1)

    def test_demographics_use_child_specific_sources_before_group_inference(self) -> None:
        direct = resolve_child_demographics(
            child_id="ali",
            source_group="BlackPro",
            child_id_ses_raw="Black,UC",
            metadata_row={"race": "", "social_class": ""},
        )
        csv_backed = resolve_child_demographics(
            child_id="bea",
            source_group="WhiteWork",
            child_id_ses_raw="",
            metadata_row={"race": "White", "social_class": "WC"},
        )
        inferred = resolve_child_demographics(
            child_id="rog",
            source_group="BlackWork",
            child_id_ses_raw="",
            metadata_row={"race": "", "social_class": ""},
        )

        self.assertEqual((direct.race, direct.social_class, direct.source), ("Black", "UC", "chi_id"))
        self.assertEqual((csv_backed.race, csv_backed.social_class, csv_backed.source), ("White", "WC", "children_meta_csv"))
        self.assertEqual((inferred.race, inferred.social_class, inferred.source), ("Black", "WC", "source_group_inferred"))
        self.assertTrue(direct.primary_eligible)
        self.assertTrue(csv_backed.primary_eligible)
        self.assertFalse(inferred.primary_eligible)
        self.assertTrue(inferred.sensitivity_eligible)

    def test_end_to_end_writes_lossless_rows_and_explicit_sample_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw = root / "raw"
            output = root / "preprocessed"
            reports = root / "reports"

            write_chat(
                raw / "BlackPro" / "ali.cha",
                child_id="ali",
                ses="Black,UC",
                body="@Situation:\tbefore dinner\n*MOT:\thi .\n*CHI:\thello .\n*TEA:\tgood .\n",
            )
            write_chat(
                raw / "BlackWork" / "rog.cha",
                child_id="rog",
                body="@Situation:\tfree play (at school)\n*TEA:\tgo .\n*CHI:\tgoing .\n",
            )
            write_chat(
                raw / "WhitePro" / "grc.cha",
                child_id="grc",
                ses="White,UC",
                body="*CHI:\t0 .\n",
                comment="transcript missing, but we have the sound",
            )
            asr = raw / "WhiteWork" / "brh.cha"
            asr.parent.mkdir(parents=True)
            asr.write_text(
                "@UTF8\n@Participants:\tPAR0 Participant\n"
                "@Comment:\tthis file was done using ASR and it needs to be revised and checked.\n"
                "*PAR0:\thello .\n@End\n",
                encoding="utf-8",
            )
            (raw / "children_meta.csv").write_text(
                "child_id,age,sex,race,social_class\n"
                "ali,4;09.,female,Black,UC\n"
                "rog,4;09.,male,,\n"
                "grc,4;09.,,White,UC\n"
                "brh,,,,\n",
                encoding="utf-8",
            )

            audit = prepare_hall_snapshot(raw_root=raw, output_root=output, report_root=reports)

            inventory = read_csv(reports / "hall_file_inventory.csv")
            metadata = read_csv(reports / "hall_child_metadata.csv")
            all_rows = read_csv(output / "ali" / "all_speakers.csv")
            chi_rows = read_csv(output / "ali" / "chi.csv")
            adults = read_csv(output / "ali" / "adult_interlocutors.csv")
            scoring = read_csv(reports / "hall_child_snapshot_scoring.csv")
            saved_audit = json.loads((reports / "hall_preprocessing_audit.json").read_text(encoding="utf-8"))

        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["counts"]["files"], 4)
        self.assertEqual(audit["counts"]["primary_children"], 1)
        self.assertEqual(audit["counts"]["sensitivity_children"], 2)
        self.assertEqual(saved_audit, audit)
        self.assertEqual(len(all_rows), 3)
        self.assertEqual(len(chi_rows), 1)
        self.assertEqual({row["speaker"] for row in adults}, {"MOT", "TEA"})
        self.assertEqual({row["child_id"] for row in scoring}, {"ali", "rog"})
        scoring_by_child = {row["child_id"]: row for row in scoring}
        self.assertEqual(scoring_by_child["ali"]["context_k1"], "hi.")
        self.assertEqual(scoring_by_child["rog"]["context_k1"], "go.")
        self.assertEqual(scoring_by_child["ali"]["primary_eligible"], "1")
        self.assertEqual(scoring_by_child["rog"]["primary_eligible"], "0")
        self.assertEqual(scoring_by_child["rog"]["sensitivity_eligible"], "1")

        by_child = {row["child_id"]: row for row in inventory}
        self.assertEqual(by_child["ali"]["analysis_status"], "primary")
        self.assertEqual(by_child["rog"]["analysis_status"], "sensitivity_only")
        self.assertIn("missing_transcript", by_child["grc"]["exclusion_reasons"])
        self.assertIn("no_target_child_tier", by_child["brh"]["exclusion_reasons"])
        self.assertIn("unrevised_asr", by_child["brh"]["exclusion_reasons"])

        metadata_by_child = {row["child_id"]: row for row in metadata}
        self.assertEqual(metadata_by_child["ali"]["demographic_source"], "chi_id")
        self.assertEqual(metadata_by_child["rog"]["demographic_source"], "source_group_inferred")


if __name__ == "__main__":
    unittest.main()
