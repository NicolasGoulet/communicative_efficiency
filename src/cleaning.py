#!/usr/bin/env python3
"""
Focused CHAT utterance cleaning.

This script reads raw CHAT main tiers and writes a minimal CSV containing the
raw main-tier utterance plus the cleaned utterance. It deliberately avoids the
heavier counting and metadata work in prepare_datasets.py.

Initial use cases checked by tests:
- Clean one raw CHAT utterance without touching the filesystem.
- Preserve terminal punctuation when CHAT timing or retracing markup follows it.
- Parse one .cha file into raw/cleaned utterance rows for CHI, MOT, and FAT.
- Keep rows whose cleaned utterance is empty so row loss is explicit.
- Filter to a requested speaker set when needed.
- Write a minimal CSV schema that downstream work can rely on.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Iterator, Optional, Sequence


DEFAULT_SPEAKERS = ("CHI", "MOT", "FAT")

CLEANED_CHAT_COLUMNS = [
    "file",
    "line_no",
    "speaker",
    "utterance",
    "utterance_clean",
    "cleaned_is_empty",
]

_TIMECODE_RE = re.compile(r"\x15\s*\d+(?:[_:]\d+)?\s*\x15")
_BRACKETS_RE = re.compile(r"\[[^\]]*]")
_PARENS_RE = re.compile(r"\([^)]*\)")
_ANGLE_KEEP_RE = re.compile(r"<([^>]*)>")
_UNTRANS_RE = re.compile(r"\b(?:xxx|yyy|www)\b", re.IGNORECASE)
_PLUS_MARKER_RE = re.compile(r"(?:(?<=\s)|^)\+(?:[/.\-]+|\S+)")
_FILLER_MARKER_RE = re.compile(
    r"(?:(?<=\s)|^)&-(uh|um|er|eh)(?::[A-Za-z]*)?(?=[\s,.;!?]|$)",
    re.IGNORECASE,
)
_AT_MARKER_RE = re.compile(r"(?:(?<=\s)|^)@[^\s]+")
_AMP_MARKER_RE = re.compile(r"(?:(?<=\s)|^)&[^\s]+")
_ZERO_MARKER_RE = re.compile(r"(?:(?<=\s)|^)0[^\s]*")
_SPACES_RE = re.compile(r"\s+")

_TRAILING_TRANSCRIPT_TIME_RE = re.compile(
    r"(?:\s*(?:\x15\s*\d+(?:[_:]\d+)?\s*\x15|\d+(?:[_:]\d+)))+\s*$"
)
_TERMINAL_SENTENCE_PUNCT_RE = re.compile(r"([.!?])\s*$")
_KEPT_SPECIAL_FORM_MARKERS = (
    "b",  # babbling
    "c",  # child-invented form
    "d",  # dialect form
    "f",  # family-specific form
    "i",  # interjection / interaction
    "k",  # multiple letters
    "l",  # letter
    "ls",  # letter plural
    "n",  # neologism
    "o",  # onomatopoeia
    "p",  # phonologically consistent form
    "wp",  # word play
)
_KEPT_SPECIAL_FORM_MARKER_PATTERN = "|".join(
    re.escape(marker) for marker in sorted(_KEPT_SPECIAL_FORM_MARKERS, key=len, reverse=True)
)
_ALLOWED_AT_TOKEN_RE = re.compile(
    rf"^([^@\s]+)@({_KEPT_SPECIAL_FORM_MARKER_PATTERN})(?:\$[A-Za-z]+)?$",
    re.IGNORECASE,
)
_STRIP_OUTER_JUNK_RE = re.compile(
    r"^[^A-Za-zÀ-ÖØ-öø-ÿ'@]+|[^A-Za-zÀ-ÖØ-öø-ÿ'@]+$"
)


def _terminal_sentence_punctuation(text: str) -> str:
    """
    Return the final sentence punctuation mark that belongs to the utterance.

    Goal: recover a meaningful final ".", "!", or "?" even when CHAT timing
    spans or transcript offsets appear after the punctuation in the raw text.
    """
    s = "" if text is None else str(text).strip()
    if not s:
        return ""

    s = _TRAILING_TRANSCRIPT_TIME_RE.sub("", s).rstrip()
    match = _TERMINAL_SENTENCE_PUNCT_RE.search(s)
    return match.group(1) if match else ""


def _apply_strict_at_policy_whitespace_tokens(text: str) -> str:
    """
    Normalize or remove remaining CHAT tokens that contain @.

    Goal: keep the lexical base of accepted word-like special forms such as
    `dog@c`, `word@b`, `bunko@f`, `uhhuh@i`, `p@ls`, `breaked@n`,
    `aga@p`, and `goobarumba@wp`; drop other @ forms completely so tag
    letters do not become fake words in `utterance_clean`.
    """
    out = []
    for raw in (text or "").split():
        token = raw.replace("<", "").replace(">", "")
        token = _STRIP_OUTER_JUNK_RE.sub("", token).strip()
        if not token:
            continue

        if "@" in token:
            match = _ALLOWED_AT_TOKEN_RE.fullmatch(token)
            if not match:
                continue
            base = _STRIP_OUTER_JUNK_RE.sub("", match.group(1)).strip()
            if base:
                out.append(base)
            continue

        out.append(token)

    return " ".join(out)


def clean_chat_utterance(text: str) -> str:
    """
    Remove CHAT markup from a main-tier utterance while preserving spoken words.

    Goal: convert the raw utterance text from a CHAT main tier into the
    canonical text column that later preprocessing and scoring can inspect.

    The policy mirrors the currently useful parts of prepare_datasets.py:
    unwrap <...>, remove bracketed/parenthetical annotations, preserve common
    fillers such as &-uh, keep requested word-like special forms as words, keep
    @l/@ls/@k letter forms as discourse tokens, and drop other CHAT marker
    tokens.
    """
    s = "" if text is None else str(text)
    terminal_punct = _terminal_sentence_punctuation(s)

    s = _TIMECODE_RE.sub(" ", s)
    s = _BRACKETS_RE.sub(" ", s)
    s = _PARENS_RE.sub(" ", s)
    s = _ANGLE_KEEP_RE.sub(r"\1", s)
    s = _UNTRANS_RE.sub(" ", s)
    s = _FILLER_MARKER_RE.sub(lambda m: f" {m.group(1).lower()} ", s)
    s = _AT_MARKER_RE.sub(" ", s)
    s = _PLUS_MARKER_RE.sub(" ", s)
    s = _AMP_MARKER_RE.sub(" ", s)
    s = _ZERO_MARKER_RE.sub(" ", s)
    s = _SPACES_RE.sub(" ", s).strip()

    s = _apply_strict_at_policy_whitespace_tokens(s)
    s = _SPACES_RE.sub(" ", s).strip()

    if s and terminal_punct:
        s = f"{s}{terminal_punct}"
    return s


def _relative_file_label(cha_path: Path, base_dir: Optional[Path]) -> str:
    """
    Return the file label to store in the output CSV.

    Goal: preserve source provenance with a relative path when a dataset base
    directory is known, while still accepting a standalone .cha file.
    """
    if base_dir is None:
        return cha_path.as_posix()

    try:
        return cha_path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return cha_path.as_posix()


def _normalize_raw_utterance(parts: Sequence[str]) -> str:
    """
    Join raw main-tier lines into the exact raw utterance stored in the CSV.

    Goal: collapse CHAT continuation-line layout whitespace without applying
    any linguistic cleaning to the raw `utterance` column.
    """
    return _SPACES_RE.sub(" ", " ".join(part.strip() for part in parts)).strip()


def iter_cleaned_chat_rows(
    cha_path: Path,
    *,
    base_dir: Optional[Path] = None,
    speakers: Sequence[str] = DEFAULT_SPEAKERS,
) -> Iterator[Dict[str, object]]:
    """
    Yield minimal raw/cleaned rows for selected CHAT main tiers.

    Goal: stream one CHAT file into rows with raw text, cleaned text, speaker,
    source file, source line number, and an explicit empty-cleaned marker.

    Rows are not dropped when cleaning produces an empty utterance; instead the
    `cleaned_is_empty` column records that state explicitly.
    """
    speaker_set = {speaker.upper() for speaker in speakers}
    file_label = _relative_file_label(cha_path, base_dir)

    current_speaker: Optional[str] = None
    current_line_no: Optional[int] = None
    current_parts: list[str] = []

    def flush_current() -> Optional[Dict[str, object]]:
        """
        Finish the current main-tier row, if one is being accumulated.

        Goal: keep the line-scanning loop simple while guaranteeing each row is
        cleaned and emitted exactly once when the parser reaches the next tier,
        a dependent tier, or the end of file.
        """
        nonlocal current_speaker, current_line_no, current_parts
        if current_speaker is None or current_line_no is None:
            return None

        utterance = _normalize_raw_utterance(current_parts)
        cleaned = clean_chat_utterance(utterance)
        row = {
            "file": file_label,
            "line_no": current_line_no,
            "speaker": current_speaker,
            "utterance": utterance,
            "utterance_clean": cleaned,
            "cleaned_is_empty": int(cleaned == ""),
        }
        current_speaker = None
        current_line_no = None
        current_parts = []
        return row

    with cha_path.open(encoding="utf-8", errors="replace") as fh:
        for line_no, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n\r")
            stripped = line.lstrip()

            if stripped.startswith("*") and ":" in stripped:
                pending = flush_current()
                if pending is not None:
                    yield pending

                tier, utterance = stripped.split(":", 1)
                speaker = tier[1:].strip().upper()
                if speaker in speaker_set:
                    current_speaker = speaker
                    current_line_no = line_no
                    current_parts = [utterance.strip()]
                continue

            is_continuation = (
                current_speaker is not None
                and line[:1].isspace()
                and stripped
                and not stripped.startswith(("*", "%", "@"))
            )
            if is_continuation:
                current_parts.append(stripped)
                continue

            pending = flush_current()
            if pending is not None:
                yield pending

    pending = flush_current()
    if pending is not None:
        yield pending


def write_cleaned_chat_csv(
    cha_path: Path,
    output_path: Path,
    *,
    base_dir: Optional[Path] = None,
    speakers: Sequence[str] = DEFAULT_SPEAKERS,
) -> int:
    """
    Write one cleaned CSV for one CHAT file and return the row count.

    Goal: expose a small file-level API for tests, scripts, and future workflow
    code that need one CSV per CHAT transcript.
    """
    rows = list(iter_cleaned_chat_rows(cha_path, base_dir=base_dir, speakers=speakers))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=CLEANED_CHAT_COLUMNS,
            quoting=csv.QUOTE_NONNUMERIC,
        )
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def iter_chat_files(input_path: Path) -> Iterator[Path]:
    """
    Yield CHAT files from either one .cha path or a directory tree.

    Goal: let the command-line interface accept both a single transcript during
    debugging and an entire raw corpus directory during batch preprocessing.
    """
    if input_path.is_file():
        yield input_path
        return

    yield from sorted(input_path.rglob("*.cha"))


def write_cleaned_chat_files(
    input_path: Path,
    output_dir: Path,
    *,
    speakers: Sequence[str] = DEFAULT_SPEAKERS,
) -> int:
    """
    Write mirrored cleaned CSV files for a CHAT file or directory tree.

    Goal: create the maintainable replacement for the old broad preprocessing
    entry point when the only desired output is raw plus cleaned utterances.
    """
    input_path = input_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    base_dir = input_path if input_path.is_dir() else input_path.parent

    total_rows = 0
    wrote_any = False
    for cha_path in iter_chat_files(input_path):
        wrote_any = True
        rel_path = cha_path.resolve().relative_to(base_dir)
        output_path = output_dir / rel_path.with_suffix(".csv")
        total_rows += write_cleaned_chat_csv(
            cha_path,
            output_path,
            base_dir=base_dir,
            speakers=speakers,
        )

    if not wrote_any:
        raise FileNotFoundError(f"No .cha files found under {input_path}")
    return total_rows


def _parse_speaker_list(value: str) -> tuple[str, ...]:
    """
    Parse the CLI speaker filter from a comma-separated string.

    Goal: make speaker selection explicit at the command line while rejecting an
    accidentally empty filter such as `--speakers ""`.
    """
    speakers = tuple(part.strip().upper() for part in value.split(",") if part.strip())
    if not speakers:
        raise argparse.ArgumentTypeError("at least one speaker code is required")
    return speakers


def build_cli() -> argparse.ArgumentParser:
    """
    Build the command-line interface for the focused cleaner.

    Goal: keep argument definitions separate from execution so tests can call
    the parser or main function directly later.
    """
    parser = argparse.ArgumentParser(
        description="Create minimal raw/cleaned utterance CSV files from CHAT transcripts."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input .cha file or directory containing .cha files.",
    )
    parser.add_argument(
        "--output-dir",
        default=Path("data") / "cleaned_utterances",
        type=Path,
        help="Directory where mirrored CSV files are written.",
    )
    parser.add_argument(
        "--speakers",
        default=DEFAULT_SPEAKERS,
        type=_parse_speaker_list,
        help="Comma-separated main-tier speaker codes to keep. Default: CHI,MOT,FAT.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """
    Run the focused cleaner from command-line arguments.

    Goal: connect CLI parsing to the batch writer without hiding the reusable
    cleaning and CSV-writing functions behind command-line-only code.
    """
    args = build_cli().parse_args(argv)
    total_rows = write_cleaned_chat_files(
        args.input,
        args.output_dir,
        speakers=args.speakers,
    )
    print(f"Wrote {total_rows:,} rows to {args.output_dir}")


if __name__ == "__main__":
    main()
