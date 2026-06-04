import csv
import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import pandas as pd

from build_age_word_dicts import ChildUnit
from generate_lstm_utterances import (
    BOS_TOKEN,
    EOS_TOKEN,
    IGNORE_INDEX,
    NO_CONTEXT_TOKEN,
    LSTMConfig,
    LSTMExample,
    Vocabulary,
    banned_ids_for_step,
    build_allowed_generation_mask,
    build_lstm_examples_from_frames,
    context_tokens_from_history,
    encode_seq2seq_example,
    encode_training_example,
    eos_is_allowed,
    generation_token_budget,
    limit_examples,
    load_lstm_examples_for_unit,
    parse_args,
    require_torch,
    sample_next_id,
    should_stop_on_token,
    train_lstm_model,
)


def frame(rows):
    return pd.DataFrame(rows)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "session_id",
        "file",
        "line_no",
        "utt_id",
        "speaker",
        "age_months",
        "utterance_clean",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestLSTMGenerationHelpers(unittest.TestCase):
    def test_context_tokens_from_history_respects_turn_limit_and_token_tail(self):
        history = [
            ("do", "you"),
            ("want", "some"),
            ("more", "milk"),
        ]

        selected = context_tokens_from_history(
            history,
            context_utterances=2,
            max_context_tokens=3,
        )

        self.assertEqual(selected, ("some", "more", "milk"))

    def test_context_tokens_from_history_can_disable_context(self):
        history = [("want", "some")]

        selected = context_tokens_from_history(
            history,
            context_utterances=0,
            max_context_tokens=20,
        )

        self.assertEqual(selected, tuple())

    def test_build_lstm_examples_uses_only_prior_caretaker_context_within_session(self):
        unit = ChildUnit(
            dataset="ToySet",
            child="ToyChild",
            folder=Path("ToyChild"),
            chi_csv=Path("ToyChild/chi.csv"),
            caretakers_csv=Path("ToyChild/caretakers.csv"),
        )
        caretakers = frame(
            [
                {
                    "session_id": 1,
                    "file": "a.cha",
                    "line_no": 5,
                    "utt_id": 1,
                    "speaker": "MOT",
                    "age_months": 7,
                    "utterance_clean": "want some",
                },
                {
                    "session_id": 1,
                    "file": "a.cha",
                    "line_no": 20,
                    "utt_id": 3,
                    "speaker": "MOT",
                    "age_months": 7,
                    "utterance_clean": "future words",
                },
                {
                    "session_id": 2,
                    "file": "b.cha",
                    "line_no": 5,
                    "utt_id": 1,
                    "speaker": "MOT",
                    "age_months": 13,
                    "utterance_clean": "new session",
                },
            ]
        )
        chi = frame(
            [
                {
                    "session_id": 1,
                    "file": "a.cha",
                    "line_no": 10,
                    "utt_id": 2,
                    "speaker": "CHI",
                    "age_months": 7,
                    "utterance_clean": "more milk.",
                },
                {
                    "session_id": 2,
                    "file": "b.cha",
                    "line_no": 10,
                    "utt_id": 2,
                    "speaker": "CHI",
                    "age_months": 13,
                    "utterance_clean": "play now",
                },
            ]
        )

        examples = build_lstm_examples_from_frames(
            unit,
            chi,
            caretakers,
            text_col="utterance_clean",
            context_utterances=1,
            max_context_tokens=20,
            min_age_months=0,
            max_age_months=120,
            min_token_len=1,
            lowercase=True,
        )

        self.assertEqual([example.child_tokens for example in examples], [("more", "milk"), ("play", "now")])
        self.assertEqual(
            [example.context_tokens for example in examples],
            [("want", "some"), ("new", "session")],
        )
        self.assertEqual(examples[0].terminal_punct, ".")

    def test_vocabulary_build_respects_min_frequency_and_stable_special_tokens(self):
        vocab = Vocabulary.build(
            [["milk", "more"], ["milk", "please"]],
            min_freq=2,
            max_vocab_size=10,
        )

        self.assertEqual(vocab.id_to_token[:5], ["<pad>", "<unk>", "<bos>", "<eos>", "<noctx>"])
        self.assertIn("milk", vocab.token_to_id)
        self.assertNotIn("more", vocab.token_to_id)

    def test_encode_training_example_masks_context_and_predicts_child_tokens_after_bos(self):
        with tempfile.TemporaryDirectory() as tmp:
            child_dir = Path(tmp) / "ToySet" / "ToyChild"
            write_csv(
                child_dir / "caretakers.csv",
                [
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 5,
                        "utt_id": 1,
                        "speaker": "MOT",
                        "age_months": 7,
                        "utterance_clean": "want some",
                    }
                ],
            )
            write_csv(
                child_dir / "chi.csv",
                [
                    {
                        "session_id": 1,
                        "file": "a.cha",
                        "line_no": 10,
                        "utt_id": 2,
                        "speaker": "CHI",
                        "age_months": 7,
                        "utterance_clean": "more milk",
                    }
                ],
            )
            unit = ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=child_dir,
                chi_csv=child_dir / "chi.csv",
                caretakers_csv=child_dir / "caretakers.csv",
            )
            example = load_lstm_examples_for_unit(unit, LSTMConfig(data_dir=str(child_dir.parent.parent)))[0]

        vocab = Vocabulary.build([example.context_tokens + example.child_tokens])
        encoded = encode_training_example(example, vocab)

        decoded_inputs = [vocab.decode_id(token_id) for token_id in encoded.input_ids]
        decoded_labels = [
            IGNORE_INDEX if token_id == IGNORE_INDEX else vocab.decode_id(token_id)
            for token_id in encoded.labels
        ]

        self.assertEqual(decoded_inputs, ["want", "some", BOS_TOKEN, "more", "milk"])
        self.assertEqual(decoded_labels, [IGNORE_INDEX, IGNORE_INDEX, "more", "milk", EOS_TOKEN])

    def test_encode_seq2seq_example_separates_encoder_context_from_decoder_child_target(self):
        example = LSTMExample(
            unit=ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=Path("ToyChild"),
                chi_csv=Path("ToyChild/chi.csv"),
                caretakers_csv=Path("ToyChild/caretakers.csv"),
            ),
            row_index=0,
            age_months=7.0,
            context_tokens=("want", "some"),
            child_tokens=("more", "milk"),
        )
        vocab = Vocabulary.build([example.context_tokens + example.child_tokens])

        encoded = encode_seq2seq_example(example, vocab)

        self.assertEqual([vocab.decode_id(i) for i in encoded.encoder_input_ids], ["want", "some"])
        self.assertEqual([vocab.decode_id(i) for i in encoded.decoder_input_ids], [BOS_TOKEN, "more", "milk"])
        self.assertEqual([vocab.decode_id(i) for i in encoded.labels], ["more", "milk", EOS_TOKEN])

    def test_encode_seq2seq_example_uses_no_context_token_when_context_is_empty(self):
        example = LSTMExample(
            unit=ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=Path("ToyChild"),
                chi_csv=Path("ToyChild/chi.csv"),
                caretakers_csv=Path("ToyChild/caretakers.csv"),
            ),
            row_index=0,
            age_months=7.0,
            context_tokens=tuple(),
            child_tokens=("more",),
        )
        vocab = Vocabulary.build([example.child_tokens])

        encoded = encode_seq2seq_example(example, vocab)

        self.assertEqual([vocab.decode_id(i) for i in encoded.encoder_input_ids], [NO_CONTEXT_TOKEN])
        self.assertEqual([vocab.decode_id(i) for i in encoded.decoder_input_ids], [BOS_TOKEN, "more"])
        self.assertEqual([vocab.decode_id(i) for i in encoded.labels], ["more", EOS_TOKEN])

    def test_generation_token_budget_uses_child_length_for_fixed_mode(self):
        example = LSTMExample(
            unit=ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=Path("ToyChild"),
                chi_csv=Path("ToyChild/chi.csv"),
                caretakers_csv=Path("ToyChild/caretakers.csv"),
            ),
            row_index=0,
            age_months=7.0,
            context_tokens=("want", "some"),
            child_tokens=("more", "milk"),
        )

        self.assertEqual(generation_token_budget(example, LSTMConfig()), 2)

    def test_generation_token_budget_uses_configured_cap_for_free_mode(self):
        example = LSTMExample(
            unit=ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=Path("ToyChild"),
                chi_csv=Path("ToyChild/chi.csv"),
                caretakers_csv=Path("ToyChild/caretakers.csv"),
            ),
            row_index=0,
            age_months=7.0,
            context_tokens=("want", "some"),
            child_tokens=("more", "milk"),
        )
        config = LSTMConfig(generation_length_mode="free_until_eos", max_generated_tokens=7)

        self.assertEqual(generation_token_budget(example, config), 7)

    def test_eos_is_allowed_only_after_min_tokens_in_free_mode(self):
        fixed_config = LSTMConfig()
        free_config = LSTMConfig(generation_length_mode="free_until_eos", min_generated_tokens=2)

        self.assertFalse(eos_is_allowed(0, fixed_config))
        self.assertFalse(eos_is_allowed(0, free_config))
        self.assertFalse(eos_is_allowed(1, free_config))
        self.assertTrue(eos_is_allowed(2, free_config))

    def test_banned_ids_for_step_bans_eos_in_fixed_mode_and_initial_free_steps(self):
        vocab = Vocabulary.build([["more", "milk"]])
        eos_id = vocab.token_to_id[EOS_TOKEN]

        fixed_banned = banned_ids_for_step(vocab, 5, LSTMConfig())
        early_free_banned = banned_ids_for_step(
            vocab,
            1,
            LSTMConfig(generation_length_mode="free_until_eos", min_generated_tokens=2),
        )
        late_free_banned = banned_ids_for_step(
            vocab,
            2,
            LSTMConfig(generation_length_mode="free_until_eos", min_generated_tokens=2),
        )

        self.assertIn(eos_id, fixed_banned)
        self.assertIn(eos_id, early_free_banned)
        self.assertNotIn(eos_id, late_free_banned)

    def test_should_stop_on_token_only_stops_on_allowed_eos(self):
        vocab = Vocabulary.build([["more", "milk"]])
        eos_id = vocab.token_to_id[EOS_TOKEN]
        more_id = vocab.token_to_id["more"]
        config = LSTMConfig(generation_length_mode="free_until_eos", min_generated_tokens=1)

        self.assertFalse(should_stop_on_token(eos_id, 0, vocab, config))
        self.assertTrue(should_stop_on_token(eos_id, 1, vocab, config))
        self.assertFalse(should_stop_on_token(more_id, 1, vocab, config))

    def test_sample_next_id_respects_allowed_output_mask(self):
        torch, _nn_module, _functional, _DataLoader, _DatasetBase = require_torch()
        vocab = Vocabulary.build([["childword", "parentword"]])
        allowed_mask = build_allowed_generation_mask(
            torch,
            vocab,
            [vocab.token_to_id["childword"]],
            torch.device("cpu"),
        )
        logits = torch.full((len(vocab.id_to_token),), -20.0)
        logits[vocab.token_to_id["parentword"]] = 100.0
        logits[vocab.token_to_id["childword"]] = 0.0

        token_id = sample_next_id(
            torch,
            logits,
            temperature=0.0,
            top_k=0,
            banned_ids=[],
            allowed_mask=allowed_mask,
        )

        self.assertEqual(vocab.decode_id(token_id), "childword")

    def test_limit_examples_samples_a_stable_subset(self):
        examples = list(range(10))

        first = limit_examples(examples, 4, seed=7)
        second = limit_examples(examples, 4, seed=7)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 4)

    def test_require_torch_reports_clear_dependency_error_when_unavailable(self):
        try:
            require_torch()
        except RuntimeError as exc:
            self.assertIn("requires PyTorch", str(exc))
        else:
            self.assertTrue(True)

    def test_parse_args_defaults_to_encoder_decoder_architecture(self):
        config = parse_args([])

        self.assertEqual(config.architecture, "seq2seq_lstm")

    def test_parse_args_can_select_causal_architecture_for_comparison(self):
        config = parse_args(["--architecture", "causal_lstm"])

        self.assertEqual(config.architecture, "causal_lstm")

    def test_parse_args_can_select_free_length_generation_mode(self):
        config = parse_args(
            [
                "--generation_length_mode",
                "free_until_eos",
                "--max_generated_tokens",
                "17",
                "--min_generated_tokens",
                "3",
            ]
        )

        self.assertEqual(config.generation_length_mode, "free_until_eos")
        self.assertEqual(config.max_generated_tokens, 17)
        self.assertEqual(config.min_generated_tokens, 3)

    def test_train_lstm_model_rejects_unknown_architecture_before_torch_is_needed(self):
        example = LSTMExample(
            unit=ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=Path("ToyChild"),
                chi_csv=Path("ToyChild/chi.csv"),
                caretakers_csv=Path("ToyChild/caretakers.csv"),
            ),
            row_index=0,
            age_months=7.0,
            context_tokens=("want", "some"),
            child_tokens=("more", "milk"),
        )
        vocab = Vocabulary.build([example.context_tokens + example.child_tokens])
        config = LSTMConfig(architecture="bogus")

        with self.assertRaises(ValueError):
            train_lstm_model([example], vocab, config, Path("unused"))

    def test_train_lstm_model_rejects_unknown_generation_length_mode_before_torch_is_needed(self):
        example = LSTMExample(
            unit=ChildUnit(
                dataset="ToySet",
                child="ToyChild",
                folder=Path("ToyChild"),
                chi_csv=Path("ToyChild/chi.csv"),
                caretakers_csv=Path("ToyChild/caretakers.csv"),
            ),
            row_index=0,
            age_months=7.0,
            context_tokens=("want", "some"),
            child_tokens=("more", "milk"),
        )
        vocab = Vocabulary.build([example.context_tokens + example.child_tokens])
        config = LSTMConfig(generation_length_mode="bogus")

        with self.assertRaises(ValueError):
            train_lstm_model([example], vocab, config, Path("unused"))


if __name__ == "__main__":
    unittest.main()
