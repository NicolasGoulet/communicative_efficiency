#!/usr/bin/env python3
"""
Train a word-level LSTM baseline and generate child-like utterances.

The script is intentionally modular because the experimental logic is likely to
change. The default setup is now an encoder-decoder LSTM:

  encoder input: caretaker context tokens
  decoder input: <bos> + child utterance prefix
  decoder target: child utterance tokens

This directly models the experimental idea "given caretaker context, generate a
child response." The older causal/prefix LSTM is still available with
--architecture causal_lstm. That variant trains examples of the form:

  caretaker context tokens + <bos> -> child utterance tokens

For the causal/prefix variant, the loss is masked over caretaker context tokens,
so context conditions the hidden state without becoming a target sequence to
memorize. By default, generation uses the same caretaker context and samples an
utterance with the same word length as the original child utterance. A separate
free-length mode can instead sample until the model emits <eos>.

PyTorch is imported lazily. The repository's base dependencies do not require
PyTorch, so helper functions and tests can run without it; actual training and
generation require installing torch in the active environment.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import pandas as pd

from add_random_and_unigram_utterances import terminal_punctuation, with_terminal_punctuation
from build_age_word_dicts import ChildUnit, filter_tokens, iter_child_units, tokenize


IGNORE_INDEX = -100
PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"
BOS_TOKEN = "<bos>"
EOS_TOKEN = "<eos>"
NO_CONTEXT_TOKEN = "<noctx>"
SPECIAL_TOKENS = (PAD_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN, NO_CONTEXT_TOKEN)
ARCHITECTURES = ("seq2seq_lstm", "causal_lstm")
GENERATION_LENGTH_MODES = ("same_as_child", "free_until_eos")


@dataclass(frozen=True)
class LSTMConfig:
    """Settings that define one LSTM baseline run."""

    data_dir: str = "data/preprocessed_data"
    datasets: Tuple[str, ...] = ("Brown", "Manchester", "Providence")
    output_dir: str = "results/lstm_generation/default"
    output_filename: str = "chi.lstm_generated.csv"
    output_column: str = "lstm_model_utterance"
    architecture: str = "seq2seq_lstm"
    text_col: str = "utterance_clean"
    bin_months: int = 6
    context_utterances: int = 1
    max_context_tokens: int = 20
    min_age_months: float = 0.0
    max_age_months: float = 120.0
    min_token_len: int = 1
    lowercase: bool = True
    max_train_examples: Optional[int] = None
    max_generate_rows_per_child: Optional[int] = None
    min_freq: int = 1
    max_vocab_size: Optional[int] = 20000
    embedding_dim: int = 128
    hidden_dim: int = 256
    num_layers: int = 1
    dropout: float = 0.0
    epochs: int = 3
    batch_size: int = 32
    learning_rate: float = 0.001
    grad_clip: float = 1.0
    seed: int = 123
    temperature: float = 1.0
    top_k: int = 0
    generation_length_mode: str = "same_as_child"
    max_generated_tokens: int = 50
    min_generated_tokens: int = 1
    device: str = "auto"


@dataclass(frozen=True)
class LSTMExample:
    """One child utterance with the preceding caretaker context."""

    unit: ChildUnit
    row_index: int
    age_months: float
    context_tokens: Tuple[str, ...]
    child_tokens: Tuple[str, ...]
    terminal_punct: str = ""


@dataclass(frozen=True)
class EncodedExample:
    """Numerical training example with masked labels."""

    input_ids: Tuple[int, ...]
    labels: Tuple[int, ...]
    row_index: int


@dataclass(frozen=True)
class EncodedSeq2SeqExample:
    """Numerical encoder-decoder training example."""

    encoder_input_ids: Tuple[int, ...]
    decoder_input_ids: Tuple[int, ...]
    labels: Tuple[int, ...]
    row_index: int


@dataclass
class Vocabulary:
    """Word vocabulary with stable special-token ids."""

    token_to_id: Dict[str, int]
    id_to_token: List[str]

    @classmethod
    def build(
        cls,
        token_sequences: Iterable[Sequence[str]],
        *,
        min_freq: int = 1,
        max_vocab_size: Optional[int] = None,
    ) -> "Vocabulary":
        counter: Counter[str] = Counter()
        for tokens in token_sequences:
            counter.update(tokens)

        ordered_tokens = list(SPECIAL_TOKENS)
        remaining_slots = None
        if max_vocab_size is not None:
            remaining_slots = max(0, int(max_vocab_size) - len(ordered_tokens))

        lexical_items = [
            token
            for token, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
            if count >= min_freq and token not in SPECIAL_TOKENS
        ]
        if remaining_slots is not None:
            lexical_items = lexical_items[:remaining_slots]

        ordered_tokens.extend(lexical_items)
        return cls(
            token_to_id={token: idx for idx, token in enumerate(ordered_tokens)},
            id_to_token=ordered_tokens,
        )

    @property
    def pad_id(self) -> int:
        return self.token_to_id[PAD_TOKEN]

    @property
    def unk_id(self) -> int:
        return self.token_to_id[UNK_TOKEN]

    @property
    def bos_id(self) -> int:
        return self.token_to_id[BOS_TOKEN]

    @property
    def no_context_id(self) -> int:
        return self.token_to_id[NO_CONTEXT_TOKEN]

    def encode_token(self, token: str) -> int:
        return self.token_to_id.get(token, self.unk_id)

    def decode_id(self, token_id: int) -> str:
        if 0 <= token_id < len(self.id_to_token):
            return self.id_to_token[token_id]
        return UNK_TOKEN

    def to_json_dict(self) -> Dict[str, object]:
        return {"id_to_token": self.id_to_token}

    @classmethod
    def from_json_dict(cls, obj: Dict[str, object]) -> "Vocabulary":
        id_to_token = [str(token) for token in obj["id_to_token"]]
        return cls(token_to_id={token: idx for idx, token in enumerate(id_to_token)}, id_to_token=id_to_token)


def require_torch():
    """Import torch only when model training/generation is actually requested."""
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as functional
        from torch.utils.data import DataLoader, Dataset
    except ImportError as exc:
        raise RuntimeError(
            "LSTM training/generation requires PyTorch, but torch is not installed. "
            "Install torch in this environment before running src/generate_lstm_utterances.py."
        ) from exc

    return torch, nn, functional, DataLoader, Dataset


def set_seeds(seed: int) -> None:
    """Seed Python and, if present, PyTorch."""
    random.seed(seed)
    try:
        import torch
    except ImportError:
        return
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def selected_device(torch_module, requested: str):
    """Resolve auto/cpu/cuda device settings."""
    if requested == "auto":
        return torch_module.device("cuda" if torch_module.cuda.is_available() else "cpu")
    return torch_module.device(requested)


def stable_sort_prepared_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Sort prepared rows in conversational order within sessions."""
    out = df.copy()
    for source, target in [
        ("session_id", "_session_sort"),
        ("line_no", "_line_no_sort"),
        ("utt_id", "_utt_id_sort"),
    ]:
        out[target] = pd.to_numeric(out.get(source), errors="coerce")
    if "file" not in out.columns:
        out["file"] = ""
    out = out.sort_values(
        by=["_session_sort", "file", "_line_no_sort", "_utt_id_sort"],
        kind="stable",
    ).reset_index(drop=True)
    return out.drop(columns=["_session_sort", "_line_no_sort", "_utt_id_sort"])


def context_tokens_from_history(
    caretaker_history: Sequence[Sequence[str]],
    *,
    context_utterances: int,
    max_context_tokens: int,
) -> Tuple[str, ...]:
    """
    Select recent caretaker context tokens.

    `context_utterances` controls how many prior caretaker turns are eligible.
    `max_context_tokens` keeps only the tail of the resulting context, which is
    the knob that prevents this baseline from being an unbounded-context model.
    """
    if context_utterances <= 0 or max_context_tokens == 0:
        return tuple()

    selected_turns = caretaker_history[-context_utterances:]
    tokens = [token for turn in selected_turns for token in turn]
    if max_context_tokens > 0:
        tokens = tokens[-max_context_tokens:]
    return tuple(tokens)


def build_lstm_examples_from_frames(
    unit: ChildUnit,
    chi_df: pd.DataFrame,
    caretakers_df: pd.DataFrame,
    *,
    text_col: str,
    context_utterances: int,
    max_context_tokens: int,
    min_age_months: float,
    max_age_months: float,
    min_token_len: int,
    lowercase: bool,
) -> List[LSTMExample]:
    """Build examples from already loaded prepared child/caretaker frames."""
    chi = chi_df.copy()
    caretakers = caretakers_df.copy()
    chi["_role_group"] = "CHI"
    chi["_source_index"] = chi.index
    caretakers["_role_group"] = "CARETAKER"
    caretakers["_source_index"] = -1

    for df in (chi, caretakers):
        for column in ["session_id", "file", "line_no", "utt_id", "age_months", text_col]:
            if column not in df.columns:
                df[column] = pd.NA

    combined = pd.concat([chi, caretakers], ignore_index=True, sort=False)
    combined = stable_sort_prepared_frame(combined)

    caretaker_history_by_session: Dict[str, List[Tuple[str, ...]]] = {}
    examples: List[LSTMExample] = []

    for _, row in combined.iterrows():
        session_key = str(row["session_id"])
        tokens = tuple(filter_tokens(tokenize(row[text_col], lowercase=lowercase), min_token_len))

        if row["_role_group"] == "CARETAKER":
            if tokens:
                caretaker_history_by_session.setdefault(session_key, []).append(tokens)
            continue

        if not tokens:
            continue

        age = pd.to_numeric(row["age_months"], errors="coerce")
        if pd.isna(age) or float(age) < min_age_months or float(age) > max_age_months:
            continue

        context = context_tokens_from_history(
            caretaker_history_by_session.get(session_key, []),
            context_utterances=context_utterances,
            max_context_tokens=max_context_tokens,
        )
        examples.append(
            LSTMExample(
                unit=unit,
                row_index=int(row["_source_index"]),
                age_months=float(age),
                context_tokens=context,
                child_tokens=tokens,
                terminal_punct=terminal_punctuation(row[text_col]),
            )
        )

    examples.sort(key=lambda example: example.row_index)
    return examples


def load_lstm_examples_for_unit(unit: ChildUnit, config: LSTMConfig) -> List[LSTMExample]:
    """Load one prepared child folder into LSTM examples."""
    chi_df = pd.read_csv(unit.chi_csv)
    caretakers_df = pd.read_csv(unit.caretakers_csv) if unit.caretakers_csv and unit.caretakers_csv.exists() else pd.DataFrame()
    return build_lstm_examples_from_frames(
        unit,
        chi_df,
        caretakers_df,
        text_col=config.text_col,
        context_utterances=config.context_utterances,
        max_context_tokens=config.max_context_tokens,
        min_age_months=config.min_age_months,
        max_age_months=config.max_age_months,
        min_token_len=config.min_token_len,
        lowercase=config.lowercase,
    )


def limit_examples(examples: Sequence[LSTMExample], max_examples: Optional[int], seed: int) -> List[LSTMExample]:
    """Return a stable optional random subset of examples."""
    out = list(examples)
    if max_examples is None or max_examples <= 0 or len(out) <= max_examples:
        return out
    rng = random.Random(seed)
    selected_indices = sorted(rng.sample(range(len(out)), max_examples))
    return [out[index] for index in selected_indices]


def encode_training_example(example: LSTMExample, vocab: Vocabulary) -> EncodedExample:
    """
    Encode one masked language-model example.

    Input sequence:
      context tokens + <bos> + all child tokens

    Labels:
      IGNORE for context input positions, then all child tokens plus <eos>.
    """
    if not example.child_tokens:
        return EncodedExample(input_ids=tuple(), labels=tuple(), row_index=example.row_index)

    context_ids = [vocab.encode_token(token) for token in example.context_tokens]
    child_ids = [vocab.encode_token(token) for token in example.child_tokens]
    input_ids = context_ids + [vocab.bos_id] + child_ids
    labels = [IGNORE_INDEX] * len(context_ids) + child_ids + [vocab.token_to_id[EOS_TOKEN]]
    return EncodedExample(input_ids=tuple(input_ids), labels=tuple(labels), row_index=example.row_index)


def encode_seq2seq_example(example: LSTMExample, vocab: Vocabulary) -> EncodedSeq2SeqExample:
    """
    Encode one encoder-decoder training example.

    Encoder input:
      caretaker context tokens, or <noctx> when context is empty

    Decoder input:
      <bos> + all child tokens

    Labels:
      all child tokens plus <eos>
    """
    if not example.child_tokens:
        return EncodedSeq2SeqExample(
            encoder_input_ids=tuple(),
            decoder_input_ids=tuple(),
            labels=tuple(),
            row_index=example.row_index,
        )

    encoder_input_ids = [vocab.encode_token(token) for token in example.context_tokens]
    if not encoder_input_ids:
        encoder_input_ids = [vocab.no_context_id]

    child_ids = [vocab.encode_token(token) for token in example.child_tokens]
    decoder_input_ids = [vocab.bos_id] + child_ids
    return EncodedSeq2SeqExample(
        encoder_input_ids=tuple(encoder_input_ids),
        decoder_input_ids=tuple(decoder_input_ids),
        labels=tuple(child_ids + [vocab.token_to_id[EOS_TOKEN]]),
        row_index=example.row_index,
    )


def save_vocab(path: Path, vocab: Vocabulary) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(vocab.to_json_dict(), handle, ensure_ascii=False, indent=2)


def save_config(path: Path, config: LSTMConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(config)
    payload["datasets"] = list(config.datasets)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)


def write_summary_csv(path: Path, rows: Sequence[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def count_trainable_parameters(model) -> int:
    """Return the number of trainable model parameters."""
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def cuda_memory_snapshot(torch_module, device) -> Dict[str, int]:
    """Return CUDA memory counters for the active device when available."""
    if getattr(device, "type", "") != "cuda" or not torch_module.cuda.is_available():
        return {
            "cuda_memory_allocated_bytes": 0,
            "cuda_memory_reserved_bytes": 0,
            "cuda_max_memory_allocated_bytes": 0,
        }
    return {
        "cuda_memory_allocated_bytes": int(torch_module.cuda.memory_allocated(device)),
        "cuda_memory_reserved_bytes": int(torch_module.cuda.memory_reserved(device)),
        "cuda_max_memory_allocated_bytes": int(torch_module.cuda.max_memory_allocated(device)),
    }


class BatchCSVLogger:
    """Small append-only CSV logger for training-batch telemetry."""

    fieldnames = [
        "epoch",
        "batch_index",
        "batches_in_epoch",
        "loss",
        "target_tokens",
        "cumulative_tokens",
        "elapsed_seconds",
        "tokens_per_second",
        "grad_norm",
        "learning_rate",
        "architecture",
        "device",
        "cuda_memory_allocated_bytes",
        "cuda_memory_reserved_bytes",
        "cuda_max_memory_allocated_bytes",
    ]

    def __init__(self, path: Optional[Path]):
        self.path = path
        self.handle = None
        self.writer = None
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.handle = path.open("w", newline="", encoding="utf-8")
            self.writer = csv.DictWriter(self.handle, fieldnames=self.fieldnames)
            self.writer.writeheader()

    def write(self, row: Dict[str, object]) -> None:
        if self.writer is None or self.handle is None:
            return
        self.writer.writerow(row)
        self.handle.flush()

    def close(self) -> None:
        if self.handle is not None:
            self.handle.close()


def build_torch_objects(nn_module, DatasetBase):
    """Create torch-dependent classes after torch is available."""

    class EncodedLSTMDataset(DatasetBase):
        def __init__(self, encoded_examples: Sequence[EncodedExample]):
            self.encoded_examples = list(encoded_examples)

        def __len__(self) -> int:
            return len(self.encoded_examples)

        def __getitem__(self, index: int) -> EncodedExample:
            return self.encoded_examples[index]

    class EncodedSeq2SeqDataset(DatasetBase):
        def __init__(self, encoded_examples: Sequence[EncodedSeq2SeqExample]):
            self.encoded_examples = list(encoded_examples)

        def __len__(self) -> int:
            return len(self.encoded_examples)

        def __getitem__(self, index: int) -> EncodedSeq2SeqExample:
            return self.encoded_examples[index]

    class WordLSTM(nn_module.Module):
        def __init__(
            self,
            vocab_size: int,
            embedding_dim: int,
            hidden_dim: int,
            num_layers: int,
            dropout: float,
            pad_id: int,
        ):
            super().__init__()
            lstm_dropout = dropout if num_layers > 1 else 0.0
            self.embedding = nn_module.Embedding(vocab_size, embedding_dim, padding_idx=pad_id)
            self.lstm = nn_module.LSTM(
                input_size=embedding_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                dropout=lstm_dropout,
                batch_first=True,
            )
            self.output = nn_module.Linear(hidden_dim, vocab_size)

        def forward(self, input_ids, hidden=None):
            embedded = self.embedding(input_ids)
            out, hidden = self.lstm(embedded, hidden)
            return self.output(out), hidden

    class EncoderDecoderLSTM(nn_module.Module):
        def __init__(
            self,
            vocab_size: int,
            embedding_dim: int,
            hidden_dim: int,
            num_layers: int,
            dropout: float,
            pad_id: int,
        ):
            super().__init__()
            lstm_dropout = dropout if num_layers > 1 else 0.0
            self.embedding = nn_module.Embedding(vocab_size, embedding_dim, padding_idx=pad_id)
            self.encoder = nn_module.LSTM(
                input_size=embedding_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                dropout=lstm_dropout,
                batch_first=True,
            )
            self.decoder = nn_module.LSTM(
                input_size=embedding_dim,
                hidden_size=hidden_dim,
                num_layers=num_layers,
                dropout=lstm_dropout,
                batch_first=True,
            )
            self.output = nn_module.Linear(hidden_dim, vocab_size)

        def encode(self, encoder_input_ids):
            embedded_context = self.embedding(encoder_input_ids)
            _encoder_out, hidden = self.encoder(embedded_context)
            return hidden

        def decode(self, decoder_input_ids, hidden):
            embedded_decoder = self.embedding(decoder_input_ids)
            decoder_out, hidden = self.decoder(embedded_decoder, hidden)
            return self.output(decoder_out), hidden

        def forward(self, encoder_input_ids, decoder_input_ids):
            hidden = self.encode(encoder_input_ids)
            return self.decode(decoder_input_ids, hidden)

    return EncodedLSTMDataset, EncodedSeq2SeqDataset, WordLSTM, EncoderDecoderLSTM


def make_collate_fn(torch_module, pad_id: int):
    """Build a DataLoader collate function for padded masked examples."""

    def collate(batch: Sequence[EncodedExample]):
        max_len = max(len(item.input_ids) for item in batch)
        input_rows = []
        label_rows = []
        for item in batch:
            pad_count = max_len - len(item.input_ids)
            input_rows.append(list(item.input_ids) + [pad_id] * pad_count)
            label_rows.append(list(item.labels) + [IGNORE_INDEX] * pad_count)
        return (
            torch_module.tensor(input_rows, dtype=torch_module.long),
            torch_module.tensor(label_rows, dtype=torch_module.long),
        )

    return collate


def make_seq2seq_collate_fn(torch_module, pad_id: int):
    """Build a DataLoader collate function for padded encoder-decoder examples."""

    def collate(batch: Sequence[EncodedSeq2SeqExample]):
        max_encoder_len = max(len(item.encoder_input_ids) for item in batch)
        max_decoder_len = max(len(item.decoder_input_ids) for item in batch)
        encoder_rows = []
        decoder_rows = []
        label_rows = []
        for item in batch:
            encoder_pad = max_encoder_len - len(item.encoder_input_ids)
            decoder_pad = max_decoder_len - len(item.decoder_input_ids)
            encoder_rows.append(list(item.encoder_input_ids) + [pad_id] * encoder_pad)
            decoder_rows.append(list(item.decoder_input_ids) + [pad_id] * decoder_pad)
            label_rows.append(list(item.labels) + [IGNORE_INDEX] * decoder_pad)
        return (
            torch_module.tensor(encoder_rows, dtype=torch_module.long),
            torch_module.tensor(decoder_rows, dtype=torch_module.long),
            torch_module.tensor(label_rows, dtype=torch_module.long),
        )

    return collate


def train_lstm_model(
    examples: Sequence[LSTMExample],
    vocab: Vocabulary,
    config: LSTMConfig,
    output_dir: Path,
    *,
    batch_log_path: Optional[Path] = None,
    log_every_batches: int = 50,
    progress_prefix: str = "",
):
    """Train the LSTM model and return it with per-epoch summaries."""
    if config.architecture not in ARCHITECTURES:
        raise ValueError(f"Unknown architecture '{config.architecture}'. Expected one of {ARCHITECTURES}.")
    if config.generation_length_mode not in GENERATION_LENGTH_MODES:
        raise ValueError(
            f"Unknown generation length mode '{config.generation_length_mode}'. "
            f"Expected one of {GENERATION_LENGTH_MODES}."
        )

    torch, nn_module, _functional, DataLoader, DatasetBase = require_torch()
    EncodedDataset, EncodedSeq2SeqDataset, WordLSTM, EncoderDecoderLSTM = build_torch_objects(nn_module, DatasetBase)
    device = selected_device(torch, config.device)

    if config.architecture == "seq2seq_lstm":
        encoded = [encode_seq2seq_example(example, vocab) for example in examples]
        encoded = [item for item in encoded if item.encoder_input_ids and item.decoder_input_ids]
        dataset = EncodedSeq2SeqDataset(encoded)
        loader = DataLoader(
            dataset,
            batch_size=config.batch_size,
            shuffle=True,
            collate_fn=make_seq2seq_collate_fn(torch, vocab.pad_id),
        )
        model = EncoderDecoderLSTM(
            vocab_size=len(vocab.id_to_token),
            embedding_dim=config.embedding_dim,
            hidden_dim=config.hidden_dim,
            num_layers=config.num_layers,
            dropout=config.dropout,
            pad_id=vocab.pad_id,
        ).to(device)
    else:
        encoded = [encode_training_example(example, vocab) for example in examples]
        encoded = [item for item in encoded if item.input_ids]
        dataset = EncodedDataset(encoded)
        loader = DataLoader(
            dataset,
            batch_size=config.batch_size,
            shuffle=True,
            collate_fn=make_collate_fn(torch, vocab.pad_id),
        )
        model = WordLSTM(
            vocab_size=len(vocab.id_to_token),
            embedding_dim=config.embedding_dim,
            hidden_dim=config.hidden_dim,
            num_layers=config.num_layers,
            dropout=config.dropout,
            pad_id=vocab.pad_id,
        ).to(device)

    if not encoded:
        raise RuntimeError("No non-empty LSTM training examples were available.")

    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    loss_fn = nn_module.CrossEntropyLoss(ignore_index=IGNORE_INDEX)
    parameter_count = count_trainable_parameters(model)
    device_name = torch.cuda.get_device_name(device) if getattr(device, "type", "") == "cuda" and torch.cuda.is_available() else str(device)

    summaries: List[Dict[str, object]] = []
    batch_logger = BatchCSVLogger(batch_log_path)
    run_start = time.perf_counter()
    try:
        for epoch in range(1, config.epochs + 1):
            model.train()
            epoch_start = time.perf_counter()
            total_loss = 0.0
            total_tokens = 0
            n_batches = len(loader)
            for batch_index, batch in enumerate(loader, start=1):
                optimizer.zero_grad()

                if config.architecture == "seq2seq_lstm":
                    encoder_input_ids, decoder_input_ids, labels = batch
                    encoder_input_ids = encoder_input_ids.to(device)
                    decoder_input_ids = decoder_input_ids.to(device)
                    labels = labels.to(device)
                    logits, _hidden = model(encoder_input_ids, decoder_input_ids)
                else:
                    input_ids, labels = batch
                    input_ids = input_ids.to(device)
                    labels = labels.to(device)
                    logits, _hidden = model(input_ids)

                loss = loss_fn(logits.reshape(-1, len(vocab.id_to_token)), labels.reshape(-1))
                loss.backward()
                grad_norm: object = ""
                if config.grad_clip and config.grad_clip > 0:
                    grad_norm_tensor = torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip)
                    grad_norm = float(grad_norm_tensor.item())
                optimizer.step()

                target_tokens = int((labels != IGNORE_INDEX).sum().item())
                batch_loss = float(loss.item())
                total_loss += batch_loss * max(target_tokens, 1)
                total_tokens += target_tokens
                should_log = (
                    batch_index == 1
                    or batch_index == n_batches
                    or (log_every_batches > 0 and batch_index % log_every_batches == 0)
                )
                if should_log:
                    elapsed = time.perf_counter() - run_start
                    memory = cuda_memory_snapshot(torch, device)
                    batch_logger.write(
                        {
                            "epoch": epoch,
                            "batch_index": batch_index,
                            "batches_in_epoch": n_batches,
                            "loss": batch_loss,
                            "target_tokens": target_tokens,
                            "cumulative_tokens": total_tokens,
                            "elapsed_seconds": elapsed,
                            "tokens_per_second": total_tokens / max(time.perf_counter() - epoch_start, 1e-9),
                            "grad_norm": grad_norm,
                            "learning_rate": config.learning_rate,
                            "architecture": config.architecture,
                            "device": device_name,
                            **memory,
                        }
                    )

            epoch_seconds = time.perf_counter() - epoch_start
            mean_loss = total_loss / total_tokens if total_tokens else math.nan
            memory = cuda_memory_snapshot(torch, device)
            summaries.append(
                {
                    "epoch": epoch,
                    "mean_cross_entropy": mean_loss,
                    "perplexity": math.exp(mean_loss) if math.isfinite(mean_loss) else math.nan,
                    "target_tokens": total_tokens,
                    "training_examples": len(encoded),
                    "batches": n_batches,
                    "epoch_seconds": epoch_seconds,
                    "tokens_per_second": total_tokens / max(epoch_seconds, 1e-9),
                    "architecture": config.architecture,
                    "device": device_name,
                    "vocab_size": len(vocab.id_to_token),
                    "trainable_parameters": parameter_count,
                    **memory,
                }
            )
            prefix = f"{progress_prefix} " if progress_prefix else ""
            print(
                f"[TRAIN] {prefix}epoch={epoch} "
                f"mean_cross_entropy={mean_loss:.4f} "
                f"perplexity={math.exp(mean_loss):.2f} "
                f"target_tokens={total_tokens} "
                f"seconds={epoch_seconds:.1f}",
                flush=True,
            )
    finally:
        batch_logger.close()

    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_dir / "model.pt")
    return model, summaries


def sample_next_id(
    torch_module,
    logits,
    *,
    temperature: float,
    top_k: int,
    banned_ids: Sequence[int],
    allowed_mask=None,
) -> int:
    """Sample one token id from logits with optional top-k and output masking."""
    adjusted = logits.clone()
    if allowed_mask is not None:
        adjusted = adjusted.masked_fill(~allowed_mask, -float("inf"))
    for token_id in banned_ids:
        adjusted[token_id] = -float("inf")

    if not bool(torch_module.isfinite(adjusted).any().item()):
        raise RuntimeError("No valid LSTM output tokens remain after applying generation masks.")

    if temperature <= 0:
        return int(torch_module.argmax(adjusted).item())

    adjusted = adjusted / temperature
    if top_k and top_k > 0 and top_k < adjusted.numel():
        values, indices = torch_module.topk(adjusted, top_k)
        probs = torch_module.softmax(values, dim=-1)
        draw = torch_module.multinomial(probs, num_samples=1)
        return int(indices[draw.item()].item())

    probs = torch_module.softmax(adjusted, dim=-1)
    draw = torch_module.multinomial(probs, num_samples=1)
    return int(draw.item())


def generate_tokens_with_lstm(
    model,
    vocab: Vocabulary,
    example: LSTMExample,
    config: LSTMConfig,
    allowed_output_token_ids: Optional[Sequence[int]] = None,
) -> List[str]:
    """Generate an utterance from a trained LSTM model."""
    if config.generation_length_mode not in GENERATION_LENGTH_MODES:
        raise ValueError(
            f"Unknown generation length mode '{config.generation_length_mode}'. "
            f"Expected one of {GENERATION_LENGTH_MODES}."
        )
    if config.architecture == "seq2seq_lstm":
        return generate_tokens_with_seq2seq_lstm(model, vocab, example, config, allowed_output_token_ids)
    if config.architecture == "causal_lstm":
        return generate_tokens_with_causal_lstm(model, vocab, example, config, allowed_output_token_ids)
    raise ValueError(f"Unknown architecture '{config.architecture}'. Expected one of {ARCHITECTURES}.")


def _banned_generation_ids(vocab: Vocabulary) -> List[int]:
    """Return token ids that should not appear as lexical generated output."""
    return [
        vocab.pad_id,
        vocab.token_to_id[UNK_TOKEN],
        vocab.bos_id,
        vocab.no_context_id,
    ]


def generation_token_budget(example: LSTMExample, config: LSTMConfig) -> int:
    """Return the maximum number of lexical tokens to sample for an example."""
    if config.generation_length_mode == "same_as_child":
        return len(example.child_tokens)
    if config.generation_length_mode == "free_until_eos":
        return max(0, int(config.max_generated_tokens))
    raise ValueError(
        f"Unknown generation length mode '{config.generation_length_mode}'. "
        f"Expected one of {GENERATION_LENGTH_MODES}."
    )


def eos_is_allowed(step_index: int, config: LSTMConfig) -> bool:
    """Return whether <eos> can stop generation at this 0-based step."""
    if config.generation_length_mode != "free_until_eos":
        return False
    return step_index >= max(0, int(config.min_generated_tokens))


def banned_ids_for_step(vocab: Vocabulary, step_index: int, config: LSTMConfig) -> List[int]:
    """Return special tokens banned for one decoding step."""
    banned = _banned_generation_ids(vocab)
    if not eos_is_allowed(step_index, config):
        banned.append(vocab.token_to_id[EOS_TOKEN])
    return banned


def should_stop_on_token(token_id: int, step_index: int, vocab: Vocabulary, config: LSTMConfig) -> bool:
    """Return true when sampled <eos> should stop free-length generation."""
    return token_id == vocab.token_to_id[EOS_TOKEN] and eos_is_allowed(step_index, config)


def build_allowed_generation_mask(torch_module, vocab: Vocabulary, allowed_output_token_ids: Optional[Sequence[int]], device):
    """Return a boolean mask for lexical tokens allowed during generation."""
    if allowed_output_token_ids is None:
        return None
    mask = torch_module.zeros(len(vocab.id_to_token), dtype=torch_module.bool, device=device)
    ids = sorted({int(token_id) for token_id in allowed_output_token_ids if 0 <= int(token_id) < len(vocab.id_to_token)})
    if not ids:
        raise ValueError("allowed_output_token_ids was provided but contained no valid vocabulary ids.")
    mask[torch_module.tensor(ids, dtype=torch_module.long, device=device)] = True
    return mask


def allowed_mask_for_step(torch_module, base_allowed_mask, vocab: Vocabulary, step_index: int, config: LSTMConfig):
    """Return the generation mask for one decoding step, adding <eos> only when allowed."""
    if base_allowed_mask is None:
        return None
    if eos_is_allowed(step_index, config):
        mask = base_allowed_mask.clone()
        mask[vocab.token_to_id[EOS_TOKEN]] = True
        return mask
    return base_allowed_mask


def generate_tokens_with_causal_lstm(
    model,
    vocab: Vocabulary,
    example: LSTMExample,
    config: LSTMConfig,
    allowed_output_token_ids: Optional[Sequence[int]] = None,
) -> List[str]:
    """Generate an utterance from the causal/prefix LSTM."""
    torch, _nn_module, _functional, _DataLoader, _DatasetBase = require_torch()
    device = next(model.parameters()).device
    model.eval()
    base_allowed_mask = build_allowed_generation_mask(torch, vocab, allowed_output_token_ids, device)

    prompt_ids = [vocab.encode_token(token) for token in example.context_tokens] + [vocab.bos_id]
    if not prompt_ids:
        prompt_ids = [vocab.bos_id]

    generated: List[str] = []
    max_steps = generation_token_budget(example, config)
    with torch.no_grad():
        input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
        logits, hidden = model(input_ids)
        next_logits = logits[0, -1]
        for step_index in range(max_steps):
            token_id = sample_next_id(
                torch,
                next_logits,
                temperature=config.temperature,
                top_k=config.top_k,
                banned_ids=banned_ids_for_step(vocab, step_index, config),
                allowed_mask=allowed_mask_for_step(torch, base_allowed_mask, vocab, step_index, config),
            )
            if should_stop_on_token(token_id, step_index, vocab, config):
                break
            token = vocab.decode_id(token_id)
            generated.append(token)
            step_input = torch.tensor([[token_id]], dtype=torch.long, device=device)
            logits, hidden = model(step_input, hidden)
            next_logits = logits[0, -1]

    return generated


def generate_tokens_with_seq2seq_lstm(
    model,
    vocab: Vocabulary,
    example: LSTMExample,
    config: LSTMConfig,
    allowed_output_token_ids: Optional[Sequence[int]] = None,
) -> List[str]:
    """Generate an utterance from the encoder-decoder LSTM."""
    torch, _nn_module, _functional, _DataLoader, _DatasetBase = require_torch()
    device = next(model.parameters()).device
    model.eval()
    base_allowed_mask = build_allowed_generation_mask(torch, vocab, allowed_output_token_ids, device)

    encoder_ids = [vocab.encode_token(token) for token in example.context_tokens]
    if not encoder_ids:
        encoder_ids = [vocab.no_context_id]

    generated: List[str] = []
    max_steps = generation_token_budget(example, config)
    with torch.no_grad():
        encoder_input = torch.tensor([encoder_ids], dtype=torch.long, device=device)
        hidden = model.encode(encoder_input)
        decoder_input = torch.tensor([[vocab.bos_id]], dtype=torch.long, device=device)
        for step_index in range(max_steps):
            logits, hidden = model.decode(decoder_input, hidden)
            token_id = sample_next_id(
                torch,
                logits[0, -1],
                temperature=config.temperature,
                top_k=config.top_k,
                banned_ids=banned_ids_for_step(vocab, step_index, config),
                allowed_mask=allowed_mask_for_step(torch, base_allowed_mask, vocab, step_index, config),
            )
            if should_stop_on_token(token_id, step_index, vocab, config):
                break
            token = vocab.decode_id(token_id)
            generated.append(token)
            decoder_input = torch.tensor([[token_id]], dtype=torch.long, device=device)

    return generated


def write_generated_files(
    units: Sequence[ChildUnit],
    examples_by_unit: Dict[Path, List[LSTMExample]],
    model,
    vocab: Vocabulary,
    config: LSTMConfig,
) -> List[Dict[str, object]]:
    """Write one generated sibling CSV per child folder."""
    rows: List[Dict[str, object]] = []
    for unit in units:
        df = pd.read_csv(unit.chi_csv)
        df[config.output_column] = ""
        examples = examples_by_unit.get(unit.folder, [])
        examples = limit_examples(examples, config.max_generate_rows_per_child, config.seed)

        for example in examples:
            generated_tokens = generate_tokens_with_lstm(model, vocab, example, config)
            df.at[example.row_index, config.output_column] = with_terminal_punctuation(
                generated_tokens,
                example.terminal_punct,
            )

        out_path = unit.folder / config.output_filename
        df.to_csv(out_path, index=False)
        rows.append(
            {
                "dataset": unit.dataset,
                "child": unit.child,
                "source_rows": len(df),
                "generated_rows": len(examples),
                "output_path": str(out_path),
            }
        )
        print(f"[OK] {unit.dataset}/{unit.child}: wrote {out_path}")
    return rows


def parse_args(argv: Optional[Sequence[str]] = None) -> LSTMConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data/preprocessed_data")
    parser.add_argument("--datasets", nargs="+", default=["Brown", "Manchester", "Providence"])
    parser.add_argument("--output_dir", default="results/lstm_generation/default")
    parser.add_argument("--output_filename", default="chi.lstm_generated.csv")
    parser.add_argument("--output_column", default="lstm_model_utterance")
    parser.add_argument("--architecture", choices=ARCHITECTURES, default="seq2seq_lstm")
    parser.add_argument("--text_col", default="utterance_clean")
    parser.add_argument("--bin_months", type=int, default=6)
    parser.add_argument("--context_utterances", type=int, default=1)
    parser.add_argument("--max_context_tokens", type=int, default=20)
    parser.add_argument("--min_age_months", type=float, default=0.0)
    parser.add_argument("--max_age_months", type=float, default=120.0)
    parser.add_argument("--min_token_len", type=int, default=1)
    parser.add_argument("--no_lowercase", action="store_true")
    parser.add_argument("--max_train_examples", type=int, default=None)
    parser.add_argument("--max_generate_rows_per_child", type=int, default=None)
    parser.add_argument("--min_freq", type=int, default=1)
    parser.add_argument("--max_vocab_size", type=int, default=20000)
    parser.add_argument("--embedding_dim", type=int, default=128)
    parser.add_argument("--hidden_dim", type=int, default=256)
    parser.add_argument("--num_layers", type=int, default=1)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--learning_rate", type=float, default=0.001)
    parser.add_argument("--grad_clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_k", type=int, default=0)
    parser.add_argument("--generation_length_mode", choices=GENERATION_LENGTH_MODES, default="same_as_child")
    parser.add_argument("--max_generated_tokens", type=int, default=50)
    parser.add_argument("--min_generated_tokens", type=int, default=1)
    parser.add_argument("--device", default="auto")

    args = parser.parse_args(argv)
    return LSTMConfig(
        data_dir=args.data_dir,
        datasets=tuple(args.datasets),
        output_dir=args.output_dir,
        output_filename=args.output_filename,
        output_column=args.output_column,
        architecture=args.architecture,
        text_col=args.text_col,
        bin_months=args.bin_months,
        context_utterances=args.context_utterances,
        max_context_tokens=args.max_context_tokens,
        min_age_months=args.min_age_months,
        max_age_months=args.max_age_months,
        min_token_len=args.min_token_len,
        lowercase=not args.no_lowercase,
        max_train_examples=args.max_train_examples,
        max_generate_rows_per_child=args.max_generate_rows_per_child,
        min_freq=args.min_freq,
        max_vocab_size=args.max_vocab_size,
        embedding_dim=args.embedding_dim,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        grad_clip=args.grad_clip,
        seed=args.seed,
        temperature=args.temperature,
        top_k=args.top_k,
        generation_length_mode=args.generation_length_mode,
        max_generated_tokens=args.max_generated_tokens,
        min_generated_tokens=args.min_generated_tokens,
        device=args.device,
    )


def main(argv: Optional[Sequence[str]] = None) -> None:
    config = parse_args(argv)
    set_seeds(config.seed)

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_config(output_dir / "config.json", config)

    units = iter_child_units(Path(config.data_dir), config.datasets)
    if not units:
        raise SystemExit(f"No chi.csv files found under {config.data_dir} for datasets={config.datasets}.")

    examples_by_unit: Dict[Path, List[LSTMExample]] = {}
    all_examples: List[LSTMExample] = []
    for unit in units:
        examples = load_lstm_examples_for_unit(unit, config)
        examples_by_unit[unit.folder] = examples
        all_examples.extend(examples)

    train_examples = limit_examples(all_examples, config.max_train_examples, config.seed)
    if not train_examples:
        raise SystemExit("No LSTM training examples available after filtering.")

    vocab = Vocabulary.build(
        (example.context_tokens + example.child_tokens for example in train_examples),
        min_freq=config.min_freq,
        max_vocab_size=config.max_vocab_size,
    )
    save_vocab(output_dir / "vocab.json", vocab)

    print(f"[INFO] units={len(units)} train_examples={len(train_examples)} vocab_size={len(vocab.id_to_token)}")
    model, training_rows = train_lstm_model(train_examples, vocab, config, output_dir)
    write_summary_csv(output_dir / "training_summary.csv", training_rows)

    generation_rows = write_generated_files(units, examples_by_unit, model, vocab, config)
    write_summary_csv(output_dir / "generation_summary.csv", generation_rows)


if __name__ == "__main__":
    main()
