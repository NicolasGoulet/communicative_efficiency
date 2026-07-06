import tempfile
import unittest
from pathlib import Path
import sys

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from src.build_response_entropy_manifest import context_id
from src.build_route2_response_space_table import build_route2_response_space_table


class Route2ResponseSpaceTableTests(unittest.TestCase):
    def test_builds_real_child_rows_with_response_space_predictors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route1 = root / "route1.csv.gz"
            entropy = root / "context_response_entropy_features.csv.gz"
            effort = root / "generated_response_effort_summary_by_context.csv.gz"
            output = root / "out" / "route2.csv.gz"
            audit_dir = root / "out"

            context_a = "what do you want?"
            context_b = "look at that."
            write_route1(route1, context_a=context_a, context_b=context_b)
            write_entropy(entropy, context_a=context_a, context_b=context_b)
            write_effort(effort, context_a=context_a, context_b=context_b)

            out = build_route2_response_space_table(
                route1_input=route1,
                entropy_features_csv=entropy,
                generated_effort_csv=effort,
                output_csv=output,
                audit_dir=audit_dir,
                prompt_variant="Caregiver",
                temperature=0.5,
                chunksize=2,
                review_per_bucket=3,
                seed=1,
            )

            self.assertEqual(len(out), 2)
            self.assertTrue(output.exists())
            self.assertTrue((audit_dir / "route2_response_space_join_audit.csv").exists())
            self.assertTrue((audit_dir / "route2_response_space_manual_review_sample.csv").exists())
            self.assertTrue((audit_dir / "route2_response_space_excluded_empty_context_rows.csv.gz").exists())

            row_a = out.loc[out["score_id"].eq("s1")].iloc[0]
            self.assertEqual(row_a["response_entropy_context_id"], context_id(context_a))
            self.assertAlmostEqual(row_a["response_entropy_bits"], 1.25)
            self.assertAlmostEqual(row_a["generated_expected_words"], 2.0)
            self.assertAlmostEqual(row_a["child_words_minus_generated_mean"], -1.0)
            self.assertAlmostEqual(row_a["child_words_z_vs_generated"], -2.0)
            self.assertAlmostEqual(row_a["child_words_percentile_in_generated_distribution"], 0.25)
            self.assertAlmostEqual(row_a["child_words_cdf_le_generated_distribution"], 0.5)
            self.assertTrue(bool(row_a["child_shorter_than_generated_median"]))
            self.assertFalse(bool(row_a["child_longer_than_generated_p90"]))

            row_b = out.loc[out["score_id"].eq("s2")].iloc[0]
            self.assertTrue(bool(row_b["fallback_used_for_context"]))
            self.assertAlmostEqual(row_b["response_top_probability"], 0.6)

    def test_duplicate_generated_context_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            route1 = root / "route1.csv.gz"
            entropy = root / "context_response_entropy_features.csv.gz"
            effort = root / "generated_response_effort_summary_by_context.csv.gz"
            context_a = "what do you want?"
            context_b = "look at that."
            write_route1(route1, context_a=context_a, context_b=context_b)
            write_entropy(entropy, context_a=context_a, context_b=context_b)
            effort_rows = effort_rows_for(context_a=context_a, context_b=context_b)
            effort_rows.append(effort_rows[0].copy())
            pd.DataFrame(effort_rows).to_csv(effort, index=False)

            with self.assertRaisesRegex(ValueError, "duplicate context ids"):
                build_route2_response_space_table(
                    route1_input=route1,
                    entropy_features_csv=entropy,
                    generated_effort_csv=effort,
                    output_csv=root / "route2.csv.gz",
                    audit_dir=root,
                    prompt_variant="Caregiver",
                    temperature=0.5,
                    chunksize=2,
                    review_per_bucket=3,
                    seed=1,
                )

    def test_reuses_route1_cache_without_scanning_route1_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "route1_cache.csv.gz"
            excluded_cache = root / "excluded.csv.gz"
            entropy = root / "context_response_entropy_features.csv.gz"
            effort = root / "generated_response_effort_summary_by_context.csv.gz"
            context_a = "what do you want?"
            context_b = "look at that."
            write_route1_cache(cache, context_a=context_a, context_b=context_b)
            pd.DataFrame([{"route2_exclusion_reason": "empty_context_text"}]).to_csv(excluded_cache, index=False)
            write_entropy(entropy, context_a=context_a, context_b=context_b)
            write_effort(effort, context_a=context_a, context_b=context_b)

            out = build_route2_response_space_table(
                route1_input=root / "missing_route1.csv.gz",
                entropy_features_csv=entropy,
                generated_effort_csv=effort,
                output_csv=root / "route2.csv.gz",
                audit_dir=root,
                route1_cache=cache,
                excluded_route1_cache=excluded_cache,
                prompt_variant="Caregiver",
                temperature=0.5,
                chunksize=2,
                review_per_bucket=3,
                seed=1,
            )

            self.assertEqual(len(out), 2)
            audit = pd.read_csv(root / "route2_response_space_join_audit.csv")
            audit_map = dict(zip(audit["metric"], audit["value"].astype(str)))
            self.assertEqual(audit_map["route1_base_cache_used"], "True")
            self.assertEqual(audit_map["route1_rows_scanned"], "0")


def write_route1(path: Path, *, context_a: str, context_b: str) -> None:
    rows = [
        {
            "score_id": "s1",
            "utterance_id": "u1",
            "dataset": "Toy",
            "child_id": "Ada",
            "source_group": "Toy",
            "session_id": "1",
            "age_months": "24.0",
            "age_bin": "024-029",
            "file": "ada.cha",
            "line_no": "10",
            "utt_id": "1",
            "speaker": "CHI",
            "role": "child",
            "target_variant": "real",
            "target_utterance_clean": "yes.",
            "context_k": "k3",
            "context_col_used": "context_k3",
            "context_text": context_a,
            "mean_bits_per_token": "2.0",
            "sum_bits": "4.0",
            "n_eval_tokens": "2",
            "nb_words": "1",
            "nb_morphemes": "1",
            "nb_syllables_cmu_or_pkg": "1",
            "nb_syllables_pkg": "1",
            "nb_phonemes": "3",
            "context_entropy_bits": "3.2",
        },
        {
            "score_id": "s2",
            "utterance_id": "u2",
            "dataset": "Toy",
            "child_id": "Ada",
            "source_group": "Toy",
            "session_id": "1",
            "age_months": "24.0",
            "age_bin": "024-029",
            "file": "ada.cha",
            "line_no": "12",
            "utt_id": "2",
            "speaker": "CHI",
            "role": "child",
            "target_variant": "real",
            "target_utterance_clean": "big red ball.",
            "context_k": "k3",
            "context_col_used": "context_k3",
            "context_text": context_b,
            "mean_bits_per_token": "2.5",
            "sum_bits": "7.5",
            "n_eval_tokens": "3",
            "nb_words": "3",
            "nb_morphemes": "3",
            "nb_syllables_cmu_or_pkg": "3",
            "nb_syllables_pkg": "3",
            "nb_phonemes": "10",
            "context_entropy_bits": "2.8",
        },
        {
            "score_id": "s3",
            "utterance_id": "u3",
            "dataset": "Toy",
            "child_id": "Ada",
            "role": "caretaker",
            "target_variant": "caretaker",
            "target_utterance_clean": "ignored.",
            "context_k": "k3",
            "context_text": context_b,
            "nb_words": "1",
        },
    ]
    pd.DataFrame(rows).to_csv(path, index=False)


def write_route1_cache(path: Path, *, context_a: str, context_b: str) -> None:
    rows = []
    for score_id, utterance_id, context, target, nb_words in [
        ("s1", "u1", context_a, "yes.", "1"),
        ("s2", "u2", context_b, "big red ball.", "3"),
    ]:
        rows.append(
            {
                "score_id": score_id,
                "utterance_id": utterance_id,
                "dataset": "Toy",
                "child_id": "Ada",
                "source_group": "Toy",
                "session_id": "1",
                "age_months": "24.0",
                "age_bin": "024-029",
                "file": "ada.cha",
                "line_no": "10",
                "utt_id": "1",
                "speaker": "CHI",
                "role": "child",
                "target_variant": "real",
                "target_utterance_clean": target,
                "context_k": "k3",
                "context_col_used": "context_k3",
                "context_text": context,
                "sum_bits": "4.0",
                "mean_bits_per_token": "2.0",
                "n_eval_tokens": "2",
                "nb_words": nb_words,
                "response_entropy_context_id": context_id(context),
                "route2_context_word_count": str(len(context.split())),
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def write_entropy(path: Path, *, context_a: str, context_b: str) -> None:
    rows = []
    for context, entropy, fallback in [(context_a, 1.25, "False"), (context_b, 2.5, "True")]:
        cid = context_id(context)
        rows.append(
            {
                "setting_id": f"{cid}::Caregiver::T0.5",
                "context_id": cid,
                "context_text": context,
                "prompt_variant": "Caregiver",
                "temperature": "0.5",
                "target_valid_samples": "100",
                "max_attempts_per_setting": "300",
                "attempts": "110",
                "accepted_valid_samples": "100",
                "invalid_attempts": "10",
                "selected_samples": "100",
                "invalid_fallback_selected": "0" if fallback == "False" else "4",
                "reached_target_valid_samples": "True",
                "exhausted_attempt_cap": "False",
                "fallback_used": fallback,
                "rejection_rate": "0.1",
                "selected_sample_count": "100",
                "valid_selected_count": "100" if fallback == "False" else "96",
                "invalid_selected_count": "0" if fallback == "False" else "4",
                "unique_response_count_selected": "4",
                "unique_response_count_valid_only": "4",
                "empirical_response_entropy_bits_selected": str(entropy),
                "miller_madow_entropy_bits_selected": str(entropy),
                "empirical_response_entropy_bits_valid_only": str(entropy),
                "miller_madow_entropy_bits_valid_only": str(entropy),
                "top_response_text_selected": "yes.",
                "top_response_count_selected": "60",
                "top_response_probability_selected": "0.6",
                "mean_sample_words_selected": "2.0",
                "mean_sample_characters_selected": "8.0",
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def effort_rows_for(*, context_a: str, context_b: str) -> list[dict[str, str]]:
    rows = []
    for context, mean_words, sd, median, p90, fallback, top_probability, hist in [
        (context_a, "2.0", "0.5", "2", "3", "False", "0.5", '[{"value":"1","count":2},{"value":"3","count":2}]'),
        (context_b, "3.5", "1.0", "3", "5", "True", "0.6", '[{"value":"2","count":1},{"value":"3","count":2},{"value":"5","count":1}]'),
    ]:
        cid = context_id(context)
        rows.append(
            {
                "setting_id": f"{cid}::Caregiver::T0.5",
                "shard_index": "0",
                "context_id": cid,
                "context_text": context,
                "context_word_count": "4",
                "context_k_values": "k3",
                "datasets": "Toy",
                "child_ids": "Ada",
                "child_count": "1",
                "n_target_rows": "1",
                "prompt_variant": "Caregiver",
                "temperature": "0.5",
                "target_valid_samples": "100",
                "max_attempts_per_setting": "300",
                "attempts": "110",
                "accepted_valid_samples": "100",
                "invalid_attempts": "10",
                "selected_samples": "100",
                "invalid_fallback_selected": "0" if fallback == "False" else "4",
                "reached_target_valid_samples": "True",
                "exhausted_attempt_cap": "False",
                "fallback_used": fallback,
                "rejection_rate": "0.1",
                "selected_rows_observed": "100",
                "valid_selected_rows_observed": "100" if fallback == "False" else "96",
                "invalid_selected_rows_observed": "0" if fallback == "False" else "4",
                "valid_sample_words_n": "100" if fallback == "False" else "96",
                "valid_sample_words_mean": mean_words,
                "valid_sample_words_sd": sd,
                "valid_sample_words_median": median,
                "valid_sample_words_p90": p90,
                "valid_response_unique_count": "4",
                "valid_response_top_count": "50",
                "valid_response_top_probability": top_probability,
                "valid_response_type_miller_madow_bits": "1.25" if fallback == "False" else "2.5",
                "valid_word_count_hist_json": hist,
                "invalid_selected_top_rejection_reason": "",
            }
        )
    return rows


def write_effort(path: Path, *, context_a: str, context_b: str) -> None:
    pd.DataFrame(effort_rows_for(context_a=context_a, context_b=context_b)).to_csv(path, index=False)


if __name__ == "__main__":
    unittest.main()
