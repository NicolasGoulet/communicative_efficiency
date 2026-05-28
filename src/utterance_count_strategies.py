#!/usr/bin/env python3
"""
Transparent word, morpheme, and syllable counting strategies.

These are heuristic counters for validation probes, not an authoritative
linguistic annotation layer. The point is to make several plausible strategies
explicit so the project can inspect where they agree and disagree.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import pandas as pd


DATASETS = ("Brown", "Manchester", "Providence", "Hall")
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:'[A-Za-zÀ-ÖØ-öø-ÿ]+)*")
APOSTROPHE_RE = re.compile(r"'")
VOWEL_GROUP_WITH_Y_RE = re.compile(r"[aeiouy]+")
VOWEL_GROUP_NO_Y_RE = re.compile(r"[aeiou]+")
CONSONANT_LE_RE = re.compile(r"[^aeiou]le$")
SPACES_RE = re.compile(r"\s+")
TERMINAL_PUNCT_RE = re.compile(r"[.!?]$")

COMMON_CLITIC_PATTERNS = (
    re.compile(r".+'(m|re|ve|ll|d|s)$", re.IGNORECASE),
    re.compile(r".+n't$", re.IGNORECASE),
)
IRREGULAR_CONTRACTION_MORPHEMES = {
    "can't": 2,
    "cannot": 2,
    "won't": 2,
    "shan't": 2,
}
SUFFIX_EXCEPTIONS = {
    "is",
    "his",
    "this",
    "was",
    "as",
    "yes",
    "us",
    "hers",
    "ours",
    "theirs",
}


@dataclass(frozen=True)
class CountResult:
    """All strategy counts for one utterance."""

    word_count_regex: int
    word_count_whitespace: int
    morpheme_count_words: int
    morpheme_count_clitic_split: int
    morpheme_count_suffix_heuristic: int
    syllable_count_vowel_groups: int
    syllable_count_silent_e: int
    syllable_count_final_le: int
    syllable_count_no_y: int
    count_strategy_disagreement: int


def normalize_text(text: object) -> str:
    """Return a clean string value for counters."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    return SPACES_RE.sub(" ", str(text)).strip()


def word_tokens_regex(text: object) -> List[str]:
    """Return word-like tokens, preserving internal apostrophes."""
    return WORD_RE.findall(normalize_text(text))


def word_tokens_whitespace(text: object) -> List[str]:
    """Return whitespace tokens that contain at least one alphabetic character."""
    out: List[str] = []
    for token in normalize_text(text).split():
        stripped = token.strip()
        if WORD_RE.search(stripped):
            out.append(stripped)
    return out


def count_words_regex(text: object) -> int:
    """Count word-like regex tokens."""
    return len(word_tokens_regex(text))


def count_words_whitespace(text: object) -> int:
    """Count whitespace-delimited tokens with at least one letter."""
    return len(word_tokens_whitespace(text))


def token_has_clitic(token: str) -> bool:
    """Return whether a token contains a common English clitic/contraction."""
    lower = token.lower()
    if lower in IRREGULAR_CONTRACTION_MORPHEMES:
        return True
    return any(pattern.fullmatch(lower) for pattern in COMMON_CLITIC_PATTERNS)


def clitic_morpheme_count_for_token(token: str) -> int:
    """Count a token as one morpheme plus one when it has a common clitic."""
    lower = token.lower()
    if lower in IRREGULAR_CONTRACTION_MORPHEMES:
        return IRREGULAR_CONTRACTION_MORPHEMES[lower]
    return 2 if token_has_clitic(token) else 1


def suffix_extra_morphemes(token: str) -> int:
    """
    Return simple inflectional suffix additions.

    This intentionally only counts obvious orthographic inflections. It is a
    validation heuristic, not a replacement for MOR.
    """
    lower = token.lower().strip("'")
    if not lower or lower in SUFFIX_EXCEPTIONS:
        return 0
    if APOSTROPHE_RE.search(lower):
        return 0
    if len(lower) >= 5 and lower.endswith("ing"):
        return 1
    if len(lower) >= 4 and lower.endswith("ed"):
        return 1
    if len(lower) >= 4 and lower.endswith("es"):
        return 1
    if len(lower) >= 3 and lower.endswith("s"):
        return 1
    return 0


def count_morphemes_words(text: object) -> int:
    """Baseline: one morpheme per regex word token."""
    return count_words_regex(text)


def count_morphemes_clitic_split(text: object) -> int:
    """Count common contractions/clitics as two morphemes."""
    return sum(clitic_morpheme_count_for_token(token) for token in word_tokens_regex(text))


def count_morphemes_suffix_heuristic(text: object) -> int:
    """Count clitics and obvious inflectional suffixes as extra morphemes."""
    total = 0
    for token in word_tokens_regex(text):
        total += clitic_morpheme_count_for_token(token)
        total += suffix_extra_morphemes(token)
    return total


def _word_syllables(
    token: str,
    *,
    include_y: bool,
    subtract_silent_e: bool,
    final_le: bool,
) -> int:
    """Estimate syllables for one word with simple vowel-group rules."""
    word = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ']", "", token.lower())
    if not word:
        return 0

    vowel_re = VOWEL_GROUP_WITH_Y_RE if include_y else VOWEL_GROUP_NO_Y_RE
    count = len(vowel_re.findall(word))

    if subtract_silent_e and len(word) > 2 and word.endswith("e"):
        if final_le and CONSONANT_LE_RE.search(word):
            pass
        else:
            count -= 1

    return max(count, 1)


def word_syllables_vowel_groups(token: str) -> int:
    """Count vowel groups with y as a vowel and no silent-e adjustment."""
    return _word_syllables(token, include_y=True, subtract_silent_e=False, final_le=False)


def word_syllables_silent_e(token: str) -> int:
    """Count vowel groups with y as a vowel and subtract a final silent e."""
    return _word_syllables(token, include_y=True, subtract_silent_e=True, final_le=False)


def word_syllables_final_le(token: str) -> int:
    """Count vowel groups with silent-e adjustment but keep consonant+le words."""
    return _word_syllables(token, include_y=True, subtract_silent_e=True, final_le=True)


def word_syllables_no_y(token: str) -> int:
    """Count vowel groups without treating y as a vowel."""
    return _word_syllables(token, include_y=False, subtract_silent_e=True, final_le=True)


def count_syllables(text: object, word_counter) -> int:
    """Sum a word-level syllable strategy over regex word tokens."""
    return sum(word_counter(token) for token in word_tokens_regex(text))


def count_utterance(text: object) -> CountResult:
    """Return all count strategies for one utterance."""
    word_regex = count_words_regex(text)
    word_whitespace = count_words_whitespace(text)
    morph_words = count_morphemes_words(text)
    morph_clitic = count_morphemes_clitic_split(text)
    morph_suffix = count_morphemes_suffix_heuristic(text)
    syllable_vowel_groups = count_syllables(text, word_syllables_vowel_groups)
    syllable_silent_e = count_syllables(text, word_syllables_silent_e)
    syllable_final_le = count_syllables(text, word_syllables_final_le)
    syllable_no_y = count_syllables(text, word_syllables_no_y)

    disagreement = (
        int(word_regex != word_whitespace)
        + (max(morph_words, morph_clitic, morph_suffix) - min(morph_words, morph_clitic, morph_suffix))
        + (
            max(syllable_vowel_groups, syllable_silent_e, syllable_final_le, syllable_no_y)
            - min(syllable_vowel_groups, syllable_silent_e, syllable_final_le, syllable_no_y)
        )
    )
    return CountResult(
        word_count_regex=word_regex,
        word_count_whitespace=word_whitespace,
        morpheme_count_words=morph_words,
        morpheme_count_clitic_split=morph_clitic,
        morpheme_count_suffix_heuristic=morph_suffix,
        syllable_count_vowel_groups=syllable_vowel_groups,
        syllable_count_silent_e=syllable_silent_e,
        syllable_count_final_le=syllable_final_le,
        syllable_count_no_y=syllable_no_y,
        count_strategy_disagreement=disagreement,
    )


def parse_datasets(value: str) -> Tuple[str, ...]:
    """Parse comma-separated dataset names or all."""
    if value.strip().lower() == "all":
        return DATASETS
    datasets = tuple(part.strip() for part in value.split(",") if part.strip())
    unknown = [dataset for dataset in datasets if dataset not in DATASETS]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown dataset(s): {', '.join(unknown)}")
    return datasets


def parse_speakers(value: str) -> Tuple[str, ...]:
    """Parse comma-separated speaker/group selectors."""
    return tuple(part.strip().upper() for part in value.split(",") if part.strip())


def iter_source_csvs(data_dir: Path, datasets: Sequence[str], speakers: Sequence[str]) -> Iterator[Tuple[Path, str]]:
    """Yield source CSV paths and role labels."""
    include_child = "CHI" in speakers or "CHILD" in speakers or "ALL" in speakers
    include_caretaker = any(speaker in speakers for speaker in ("MOT", "FAT", "CARETAKER", "CARETAKERS", "ALL"))

    for dataset in datasets:
        root = data_dir / dataset
        if not root.exists():
            continue
        for child_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            if include_child and (child_dir / "chi.csv").exists():
                yield child_dir / "chi.csv", "CHILD"
            if include_caretaker and (child_dir / "caretakers.csv").exists():
                yield child_dir / "caretakers.csv", "CARETAKER"


def row_is_wanted_speaker(row: pd.Series, role_label: str, speakers: Sequence[str]) -> bool:
    """Return whether a row matches requested speakers."""
    if "ALL" in speakers:
        return True
    speaker = str(row.get("speaker", "")).upper()
    if role_label == "CHILD":
        return "CHI" in speakers or "CHILD" in speakers or speaker in speakers
    return "CARETAKER" in speakers or "CARETAKERS" in speakers or speaker in speakers


def source_row_to_probe(row: pd.Series, source_path: Path, source_row: int, role_label: str) -> Dict[str, object]:
    """Build one probe row before count columns are added."""
    dataset = str(row.get("dataset", "") or "")
    child_id = str(row.get("child_id", "") or source_path.parent.name)
    utterance_clean = normalize_text(row.get("utterance_clean", ""))
    return {
        "dataset": dataset,
        "child_id": child_id,
        "source_group": str(row.get("source_group", "") or dataset),
        "speaker": str(row.get("speaker", "") or ("CHI" if role_label == "CHILD" else "CARETAKER")),
        "speaker_group": role_label,
        "session_id": str(row.get("session_id", "") or ""),
        "age_months": str(row.get("age_months", "") or ""),
        "file": str(row.get("file", "") or ""),
        "line_no": str(row.get("line_no", "") or ""),
        "utt_id": str(row.get("utt_id", "") or ""),
        "source_csv": source_path.name,
        "source_row": source_row,
        "utterance_clean": utterance_clean,
    }


def load_candidate_rows(
    data_dir: Path,
    datasets: Sequence[str],
    speakers: Sequence[str],
    *,
    min_words: int,
) -> List[Dict[str, object]]:
    """Load scorable cleaned utterance rows and attach count strategies."""
    rows: List[Dict[str, object]] = []
    for source_path, role_label in iter_source_csvs(data_dir, datasets, speakers):
        df = pd.read_csv(source_path, dtype=str, keep_default_na=False, low_memory=False)
        for source_row, row in df.iterrows():
            if not row_is_wanted_speaker(row, role_label, speakers):
                continue
            probe = source_row_to_probe(row, source_path, int(source_row), role_label)
            counts = count_utterance(probe["utterance_clean"])
            if counts.word_count_regex < min_words:
                continue
            probe.update(counts.__dict__)
            rows.append(probe)
    return rows


def select_probe_rows(rows: Sequence[Dict[str, object]], sample_size: int, seed: int) -> List[Dict[str, object]]:
    """
    Select a deterministic inspection sample.

    Half the sample prioritizes rows where strategies disagree, and the rest is
    a seeded random sample from the remaining rows.
    """
    if sample_size <= 0 or len(rows) <= sample_size:
        return list(rows)

    sorted_rows = sorted(
        rows,
        key=lambda row: (
            -int(row["count_strategy_disagreement"]),
            row["dataset"],
            row["child_id"],
            row["source_row"],
        ),
    )
    interesting_count = min(len(sorted_rows), max(1, sample_size // 2))
    selected = sorted_rows[:interesting_count]
    selected_ids = {(row["source_csv"], row["dataset"], row["child_id"], row["source_row"]) for row in selected}

    remaining = [
        row
        for row in rows
        if (row["source_csv"], row["dataset"], row["child_id"], row["source_row"]) not in selected_ids
    ]
    rng = random.Random(seed)
    random_count = sample_size - len(selected)
    if random_count > 0 and remaining:
        selected.extend(rng.sample(remaining, min(random_count, len(remaining))))

    return sorted(selected, key=lambda row: (row["dataset"], row["child_id"], row["source_csv"], int(row["source_row"])))


PROBE_COLUMNS = [
    "dataset",
    "child_id",
    "source_group",
    "speaker",
    "speaker_group",
    "session_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "source_csv",
    "source_row",
    "utterance_clean",
    "word_count_regex",
    "word_count_whitespace",
    "morpheme_count_words",
    "morpheme_count_clitic_split",
    "morpheme_count_suffix_heuristic",
    "syllable_count_vowel_groups",
    "syllable_count_silent_e",
    "syllable_count_final_le",
    "syllable_count_no_y",
    "count_strategy_disagreement",
]


def write_probe_csv(rows: Sequence[Dict[str, object]], output_csv: Path) -> None:
    """Write probe rows with an exact quoted CSV schema."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=PROBE_COLUMNS,
            extrasaction="ignore",
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def build_probe(
    *,
    data_dir: Path,
    datasets: Sequence[str],
    speakers: Sequence[str],
    sample_size: int,
    seed: int,
    min_words: int,
    output_csv: Path,
) -> List[Dict[str, object]]:
    """Build and write the validation probe."""
    candidates = load_candidate_rows(data_dir, datasets, speakers, min_words=min_words)
    selected = select_probe_rows(candidates, sample_size=sample_size, seed=seed)
    write_probe_csv(selected, output_csv)
    return selected


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/preprocessed_data")
    parser.add_argument("--datasets", type=parse_datasets, default=parse_datasets("Brown,Manchester,Providence"))
    parser.add_argument("--speakers", type=parse_speakers, default=parse_speakers("CHI,MOT,FAT"))
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--min-words", type=int, default=1)
    parser.add_argument(
        "--output-csv",
        default="results/count_validation/utterance_count_strategy_probe.csv",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    rows = build_probe(
        data_dir=Path(args.data_dir),
        datasets=args.datasets,
        speakers=args.speakers,
        sample_size=args.sample_size,
        seed=args.seed,
        min_words=args.min_words,
        output_csv=Path(args.output_csv),
    )
    print(f"[OK] wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
