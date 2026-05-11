#!/usr/bin/env python3
"""
prepare_datasets.py
===================

Stage 0: Unified corpus pre-processor for CHILDES subsets.

For each DATASET = {Providence, Manchester, Brown}:
  For each child directory under the dataset root, create FIVE CSVs:
    • child_utts.csv        — *CHI* utterances
    • mot_utts.csv          — *MOT* utterances
    • fat_utts.csv          — *FAT* utterances
    • caretakers_utts.csv   — *MOT+FAT* utterances merged, in chronological line order
    • child_meta.csv        — a one-row file with arrays aligned to sessions
                              (session_ids, session_ages, session_ages_months, session_paths)

For DATASET = Hall:
  The raw layout is expected to be:
    data/raw_data/Hall/BlackPro/*.cha
    data/raw_data/Hall/BlackWork/*.cha
    data/raw_data/Hall/WhitePro/*.cha
    data/raw_data/Hall/WhiteWork/*.cha

  Each .cha file is treated as one child with one session. Outputs are written by default to:
    data/preprocessed_data/Hall/<child_stem>/

  The Hall group folder (BlackPro, BlackWork, WhitePro, WhiteWork) is stored in
  the CSV column `source_group` and in child_meta.csv, not in the child folder name.

Optionally, also write:
    • session_index.csv — one row per session with counts per role

IMPORTANT CHANGE
----------------
• We keep the utterance text RAW (as in CHAT main tier) in column `utterance`.
• We ALSO compute a canonical cleaned text in `utterance_clean`, used for:
    - word_count
    - syllable counts (multiple strategies)
    - later LM scoring consistency

@-TOKEN POLICY (STRICT)
-----------------------
Before TOKEN_RE extraction for word_count/syllables:
  - keep only base@{c|b|o}  -> replace with base
  - drop all other @ tokens entirely (so 'y@l' is removed, not turned into 'y' + 'l')

Caretakers CSV
--------------
`caretakers_utts.csv` contains MOT + FAT utterances together, with:
  - `speaker` column: MOT or FAT
  - `utt_id_role` column: original per-role utt_id from mot_utts/fat_utts
  - `utt_id` re-numbered to be unique within caretakers_utts.csv
  - rows sorted by (session_id, file, line_no) to preserve CHAT file order
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ────────────────────────────────────────────────────────────────
# Corpus config
# ────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

DEFAULT_ROOTS = {
    # Old-style locations kept for backward compatibility.
    "Providence": [PROJECT_ROOT / "data" / "Providence" / "Providence",
                   Path.cwd() / "data" / "Providence" / "Providence",
                   PROJECT_ROOT / "data" / "preprocessed_data" / "Providence",
                   Path.cwd() / "data" / "preprocessed_data" / "Providence"],
    "Manchester": [PROJECT_ROOT / "data" / "Manchester",
                   Path.cwd() / "data" / "Manchester",
                   PROJECT_ROOT / "data" / "preprocessed_data" / "Manchester",
                   Path.cwd() / "data" / "preprocessed_data" / "Manchester"],
    "Brown":      [PROJECT_ROOT / "data" / "Brown",
                   Path.cwd() / "data" / "Brown",
                   PROJECT_ROOT / "data" / "preprocessed_data" / "Brown",
                   Path.cwd() / "data" / "preprocessed_data" / "Brown"],

    # Hall is downloaded under data/raw_data/Hall in your current project.
    "Hall":      [PROJECT_ROOT / "data" / "raw_data" / "Hall",
                  Path.cwd() / "data" / "raw_data" / "Hall"],
}

DEFAULT_OUTPUT_ROOTS = {
    # If --output-dir is not given, old datasets still write in-place.
    "Providence": None,
    "Manchester": None,
    "Brown": None,

    # For Hall, default to writing processed CSVs away from raw_data.
    "Hall": [PROJECT_ROOT / "data" / "preprocessed_data" / "Hall",
             Path.cwd() / "data" / "preprocessed_data" / "Hall"],
}

SUMMARY_FILENAMES = {
    "Providence": "summary_providence.txt",
    "Manchester": "summary_manchester.txt",
    "Brown":      "summary_brown.txt",
    "Hall":       "summary_hall.txt",
}

MISSING_AGE_REPORT = "missing_age_sessions.txt"

# Punctuation seen as standalone %mor items; ignore these in morpheme counts
PUNCT_TOKENS = {".", "?", "!", ",", ":", ";", "…", "—"}

# Affix codes to count as overt bound morphemes (case-insensitive)
MOR_AFFIX_CODES = {
    "PL", "POSS",          # -s plural, -'s possessive
    "ING", "GER",          # -ing
    "ED", "PAST", "PT",    # -ed / past / participle
    "ER", "COMP",          # -er comparative
    "EST", "SUP",          # -est superlative
}

# Parse CHI demographics from an @ID line:
# @ID: language|corpus|CHI|AGE|SEX|...
CHI_ID_RE = re.compile(
    r"^@ID:[^|]*\|[^|]*\|CHI\|([^|]*)\|([^|]*)\|", re.IGNORECASE)

# Word tokenizer (alpha + diacritics + apostrophes)
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:'[A-Za-zÀ-ÖØ-öø-ÿ]+)*")

# CHAT date lines
BIRTH_RE = re.compile(r"^@Birth of CHI:\s*(.+)\s*$", re.IGNORECASE)
DATE_RE = re.compile(r"^@Date:\s*(.+)\s*$", re.IGNORECASE)

# ────────────────────────────────────────────────────────────────
# Canonical cleaning (shared policy)
# ────────────────────────────────────────────────────────────────

# time bullets: \x15 34413_37325 \x15 (allow spaces + '_' or ':' and optional second number)
_TIMECODE_RE = re.compile(r"\x15\s*\d+(?:[_:]\d+)?\s*\x15")

_BRACKETS_RE = re.compile(r"\[[^\]]*]")        # [...]
_PARENS_RE   = re.compile(r"\([^)]*\)")        # remove only the (...) part, keep surrounding text

# IMPORTANT: keep the words inside <...> (CHAT overlap span), do NOT delete them
_ANGLE_KEEP_RE = re.compile(r"<([^>]*)>")      # <...> -> content

_UNTRANS_RE  = re.compile(r"\b(?:xxx|yyy|www)\b", re.IGNORECASE)

# CHAT + fragments (token-level markers)
_PLUS_MARKER_RE = re.compile(r"(?:(?<=\s)|^)\+(?:[/\.\-]+|\S+)")

# Standalone @markers (token begins with @)
_AT_MARKER_RE = re.compile(r"(?:(?<=\s)|^)@[^\s]+")

# Any token starting with & (covers &=event and &-uh etc.)
_AMP_MARKER_RE = re.compile(r"(?:(?<=\s)|^)&[^\s]+")

# Omission tokens like 0word, 0, 0xxx
_ZERO_MARKER_RE = re.compile(r"(?:(?<=\s)|^)0[^\s]*")

_SPACES_RE = re.compile(r"\s+")

# STRICT @ rule: allow only base@c|b|o (case-insensitive) at whitespace-token level
_ALLOWED_AT_TOKEN_RE = re.compile(r"^([^@\s]+)@([cbo])$", re.IGNORECASE)

# Strip leading/trailing junk but keep letters/diacritics/apostrophes/@ for @-rule checking
_STRIP_OUTER_JUNK_RE = re.compile(r"^[^A-Za-zÀ-ÖØ-öø-ÿ'@]+|[^A-Za-zÀ-ÖØ-öø-ÿ'@]+$")


def _apply_strict_at_policy_whitespace_tokens(s: str) -> str:
    """
    Enforce strict @ policy BEFORE TOKEN_RE extraction:

      - if token contains '@':
          * keep only base@{c|b|o} -> replace token with base
          * drop everything else (e.g., y@l) completely
      - tokens without '@' are kept (after light outer-junk stripping)

    This prevents TOKEN_RE from counting the '@tag' letters as extra "words".
    """
    out: List[str] = []
    for raw in (s or "").split():
        t = raw.replace("<", "").replace(">", "")
        t = _STRIP_OUTER_JUNK_RE.sub("", t).strip()
        if not t:
            continue

        if "@" in t:
            m = _ALLOWED_AT_TOKEN_RE.fullmatch(t)
            if not m:
                continue
            base = m.group(1).replace("<", "").replace(">", "")
            base = _STRIP_OUTER_JUNK_RE.sub("", base).strip()
            if not base:
                continue
            out.append(base)
        else:
            out.append(t)

    return " ".join(out)


def clean_chat_for_counts(text: str) -> str:
    """
    Canonical cleaning used for:
      - word_count
      - syllable counts
      - consistency with later LM scoring / random LM tooling

    Policy:
      - Keep lexical material inside <...> (overlap spans) by unwrapping them.
      - Remove bracketed annotations [...] and parenthetical spans (...).
      - Remove CHAT markers (@..., +..., &..., 0...).
      - Enforce strict @ policy on remaining whitespace tokens:
          keep base@{c|b|o} -> base; drop all other @ tokens
    """
    s = "" if text is None else str(text)

    s = _TIMECODE_RE.sub(" ", s)
    s = _BRACKETS_RE.sub(" ", s)
    s = _PARENS_RE.sub(" ", s)

    # unwrap <...> -> content
    s = _ANGLE_KEEP_RE.sub(r"\1", s)

    s = _UNTRANS_RE.sub(" ", s)

    s = _AT_MARKER_RE.sub(" ", s)
    s = _PLUS_MARKER_RE.sub(" ", s)
    s = _AMP_MARKER_RE.sub(" ", s)
    s = _ZERO_MARKER_RE.sub(" ", s)

    s = _SPACES_RE.sub(" ", s).strip()

    # strict @ post-pass
    s = _apply_strict_at_policy_whitespace_tokens(s)

    s = _SPACES_RE.sub(" ", s).strip()
    return s


def clean_and_count_words(text: str) -> Tuple[str, int, int]:
    """
    Returns:
      cleaned_text, word_count, n_alpha_words
    """
    cleaned = clean_chat_for_counts(text)
    words = TOKEN_RE.findall(cleaned)
    return cleaned, len(words), len(words)

# ────────────────────────────────────────────────────────────────
# Syllable strategies
# ────────────────────────────────────────────────────────────────

_VOWELS_BASIC = "aeiouy"
_VOWELS_NOY   = "aeiou"
_VGROUP_RE_BASIC = re.compile(r"[aeiouy]+", re.IGNORECASE)
_VGROUP_RE_NOY   = re.compile(r"[aeiou]+", re.IGNORECASE)


def _strip_nonletters_ends(word: str) -> str:
    w = word.lower().strip()
    w = re.sub(r"^[^a-z]+|[^a-z]+$", "", w)
    return w


def syllables_basic(word: str) -> int:
    w = _strip_nonletters_ends(word)
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    groups = _VGROUP_RE_BASIC.findall(w)
    n = len(groups)
    if w.endswith("e"):
        n -= 1
    return max(1, n)


def syllables_lenient(word: str) -> int:
    w = _strip_nonletters_ends(word)
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    groups = _VGROUP_RE_BASIC.findall(w)
    return max(1, len(groups))


def syllables_strict_y(word: str) -> int:
    w = _strip_nonletters_ends(word)
    if not w:
        return 0
    if len(w) <= 3:
        return 1

    has_aeiou = bool(_VGROUP_RE_NOY.search(w))
    if has_aeiou:
        groups = _VGROUP_RE_NOY.findall(w)
        n = len(groups)
        if w.endswith("e"):
            n -= 1
        if w.endswith("y"):
            n += 1
        return max(1, n)
    else:
        groups = _VGROUP_RE_BASIC.findall(w)
        n = len(groups)
        if w.endswith("e"):
            n -= 1
        return max(1, n)


def syllables_le(word: str) -> int:
    w = _strip_nonletters_ends(word)
    if not w:
        return 0
    if len(w) <= 3:
        return 1

    n = syllables_basic(w)

    if len(w) >= 3 and w.endswith("le"):
        prev = w[-3]
        if prev not in _VOWELS_BASIC and w[-3:] not in ("lle",):
            n += 1

    if len(w) >= 3 and w.endswith("ed"):
        prev = w[-3]
        if prev in ("t", "d"):
            n += 1

    if len(w) >= 3 and w.endswith("es"):
        prev2 = w[-3:-1]
        if prev2 in ("sh", "ch") or w[-3] in ("s", "x", "z"):
            n += 1

    return max(1, n)


def count_utt_syllables(cleaned_text: str) -> Dict[str, int]:
    words = TOKEN_RE.findall(cleaned_text or "")
    tot_basic = 0
    tot_lenient = 0
    tot_stricty = 0
    tot_le = 0
    for w in words:
        tot_basic += syllables_basic(w)
        tot_lenient += syllables_lenient(w)
        tot_stricty += syllables_strict_y(w)
        tot_le += syllables_le(w)
    return {
        "utt_syllables_basic": tot_basic,
        "utt_syllables_lenient": tot_lenient,
        "utt_syllables_strictY": tot_stricty,
        "utt_syllables_le": tot_le,
        "n_alpha_words": len(words),
    }

# ────────────────────────────────────────────────────────────────
# Date + age helpers
# ────────────────────────────────────────────────────────────────

def resolve_base_dir(dataset: str, base_override: Optional[str]) -> Tuple[Path, List[Path]]:
    if base_override:
        b = Path(base_override).expanduser().resolve()
        return b, [b]
    candidates = DEFAULT_ROOTS[dataset]
    for c in candidates:
        if c.exists():
            return c, candidates
    return candidates[0], candidates


def resolve_output_dir(dataset: str, base_dir: Path, output_override: Optional[str]) -> Path:
    """
    Where processed CSVs are written.

    Old corpora default to the original behavior: write beside the .cha files.
    Hall defaults to data/preprocessed_data/Hall because its raw files live in
    data/raw_data/Hall.
    """
    if output_override:
        return Path(output_override).expanduser().resolve()

    candidates = DEFAULT_OUTPUT_ROOTS.get(dataset)
    if not candidates:
        return base_dir

    for c in candidates:
        if c.exists():
            return c.resolve()

    return candidates[0].resolve()


def parse_chat_date(s: str) -> Optional[datetime]:
    s = s.strip()
    fmts = ["%d-%b-%Y", "%d-%B-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except Exception:
            continue
    return None


def months_between(d1: datetime, d0: datetime) -> float:
    years = d1.year - d0.year
    months = d1.month - d0.month
    days = d1.day - d0.day
    total = years * 12 + months + (days / 30.0)
    return round(float(total), 3)


def age_str_to_months(age: str) -> Optional[float]:
    if not age:
        return None
    s = age.strip()
    m = re.match(r"^\s*(\d+)\s*;\s*(\d{1,2})(?:\.(\d{0,2}))?\s*\.?\s*$", s)
    if m:
        years = int(m.group(1))
        months = int(m.group(2))
        days_str = m.group(3) if m.group(3) is not None else ""
        days = int(days_str) if (days_str and days_str.isdigit()) else 0
        total = years * 12 + months + (days / 30.0)
        return round(total, 3)
    m2 = re.match(r"^\s*(\d+)\s*;\s*$", s)
    if m2:
        years = int(m2.group(1))
        return float(years * 12)
    return None


def extract_chi_age_sex(cha_path: Path) -> Tuple[str, Optional[float], str, Optional[datetime], Optional[datetime]]:
    age_raw, sex = "", ""
    birth_dt: Optional[datetime] = None
    sess_dt: Optional[datetime] = None

    with cha_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not age_raw and line.startswith("@ID:") and "|CHI|" in line:
                m = CHI_ID_RE.match(line)
                if m:
                    age_raw = m.group(1).strip()
                    sex = m.group(2).strip()
            mb = BIRTH_RE.match(line)
            if mb and birth_dt is None:
                birth_dt = parse_chat_date(mb.group(1))
            md = DATE_RE.match(line)
            if md and sess_dt is None:
                sess_dt = parse_chat_date(md.group(1))

    age_m = age_str_to_months(age_raw)
    if age_m is None and birth_dt and sess_dt:
        try:
            age_m = months_between(sess_dt, birth_dt)
        except Exception:
            age_m = None

    return age_raw, age_m, sex, birth_dt, sess_dt


def count_morphemes_from_mor(mor_line: str) -> Optional[int]:
    if not mor_line.lstrip().startswith("%mor:"):
        return None
    body = mor_line.split(":", 1)[1].strip()
    if not body:
        return 0

    total = 0
    for tok in body.split():
        if tok in PUNCT_TOKENS:
            continue
        for sub in tok.split("~"):
            sub = sub.strip()
            if not sub or sub in PUNCT_TOKENS:
                continue
            add = 1
            right = sub.split("|", 1)[1] if "|" in sub else sub
            parts = right.split("-")
            feats = parts[1:] if len(parts) > 1 else []
            add += sum(1 for f in feats if f.upper() in MOR_AFFIX_CODES)
            total += add
    return total

# ────────────────────────────────────────────────────────────────
# CSV schema
# ────────────────────────────────────────────────────────────────

CSV_UTT_COLUMNS = [
    "utt_id", "child_id", "session_id",
    "utterance",
    "utterance_clean",
    "word_count",
    "morph_count",
    "utt_syllables_basic",
    "utt_syllables_lenient",
    "utt_syllables_strictY",
    "utt_syllables_le",
    "n_alpha_words",
    "source_group",
    "file", "line_no",
]

CSV_CARETAKER_COLUMNS = [
    "utt_id",
    "utt_id_role",
    "speaker",
    "child_id", "session_id",
    "utterance",
    "utterance_clean",
    "word_count",
    "morph_count",
    "utt_syllables_basic",
    "utt_syllables_lenient",
    "utt_syllables_strictY",
    "utt_syllables_le",
    "n_alpha_words",
    "source_group",
    "file", "line_no",
]

CSV_META_COLUMNS = ["child_id", "sex", "source_group", "session_ids", "session_ages",
                    "session_ages_months", "session_paths", "n_sessions"]

CSV_SESSION_IDX_COLUMNS = [
    "session_id", "age_raw", "age_months", "path",
    "utts_CHI", "m0_CHI", "words_CHI", "morphs_CHI",
    "utts_MOT", "m0_MOT", "words_MOT", "morphs_MOT",
    "utts_FAT", "m0_FAT", "words_FAT", "morphs_FAT",
]


def _impute_missing_morph_counts_as_zero(rows: List[Dict]) -> None:
    for r in rows:
        if r.get("morph_count") in (None, ""):
            r["morph_count"] = 0


def write_csv(path: Path, columns: List[str], rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        for r in rows:
            sanitized = {k: ("" if r.get(k) is None else r.get(k)) for k in columns}
            w.writerow(sanitized)

# ────────────────────────────────────────────────────────────────
# Core traversal
# ────────────────────────────────────────────────────────────────

def collect_child(base_dir: Path, child_dir: Path,
                  emit_session_counts: bool,
                  child_id_override: Optional[str] = None,
                  cha_files_override: Optional[List[Path]] = None,
                  source_group: str = "") -> Tuple[Dict, List[str]]:
    child_id = child_id_override or child_dir.name
    payload = {
        "sex": "",
        "source_group": source_group,
        "sessions": [],
        "utts": {"CHI": [], "MOT": [], "FAT": []},
        "_next_utt_id": {"CHI": 1, "MOT": 1, "FAT": 1},
        "_session_index_rows": [] if emit_session_counts else None,
    }
    missing_age_paths: List[str] = []

    sessions_info: List[Dict] = []
    cha_files = sorted(cha_files_override) if cha_files_override is not None else sorted(child_dir.glob("*.cha"))
    for cha_file in cha_files:
        age_raw, age_m, sex, birth_dt, sess_dt = extract_chi_age_sex(cha_file)
        rel_path = cha_file.relative_to(base_dir).as_posix()
        if age_m is None:
            missing_age_paths.append(rel_path)
        sessions_info.append({
            "path": rel_path,
            "abs_path": cha_file,
            "age": age_raw,
            "age_m": age_m,
            "sex": sex,
            "birth_dt": birth_dt,
            "sess_dt": sess_dt,
        })

    sessions_info.sort(key=lambda s: (
        s["age_m"] is None,
        s["age_m"] if s["age_m"] is not None else float("inf"),
        s["path"]
    ))

    for session_idx, sess in enumerate(sessions_info, start=1):
        rel_path = sess["path"]
        cha_file = sess["abs_path"]

        if sess["sex"]:
            payload["sex"] = sess["sex"]

        if emit_session_counts:
            counters = {
                "session_id": session_idx,
                "age_raw": sess["age"],
                "age_months": sess["age_m"],
                "path": rel_path,
                "utts_CHI": 0, "m0_CHI": 0, "words_CHI": 0, "morphs_CHI": 0,
                "utts_MOT": 0, "m0_MOT": 0, "words_MOT": 0, "morphs_MOT": 0,
                "utts_FAT": 0, "m0_FAT": 0, "words_FAT": 0, "morphs_FAT": 0,
            }
        else:
            counters = None

        current_row_ref: Optional[Dict] = None

        with cha_file.open(encoding="utf-8", errors="replace") as fh:
            for line_no, raw in enumerate(fh, start=1):
                line = raw.rstrip("\n")

                if line.startswith("%mor:"):
                    if current_row_ref is not None:
                        mc = count_morphemes_from_mor(line)
                        if mc is not None:
                            current_row_ref["morph_count"] = mc
                            if counters is not None:
                                spk = current_row_ref["_speaker"]
                                counters[f"morphs_{spk}"] += (mc or 0)
                    continue

                s = line.lstrip()
                if not s.startswith("*") or ":" not in s:
                    continue
                speaker, utter = s.split(":", 1)
                speaker = speaker[1:].strip().upper()
                utter = utter.rstrip()
                if speaker not in ("CHI", "MOT", "FAT"):
                    current_row_ref = None
                    continue

                utter_raw = utter
                utter_clean, wc, _n_words = clean_and_count_words(utter_raw)
                syls = count_utt_syllables(utter_clean)

                utt_id = payload["_next_utt_id"][speaker]
                row = {
                    "utt_id": utt_id,
                    "child_id": child_id,
                    "session_id": session_idx,
                    "utterance": utter_raw,
                    "utterance_clean": utter_clean,
                    "word_count": wc,
                    "morph_count": None,
                    **syls,
                    "source_group": source_group,
                    "file": rel_path,
                    "line_no": line_no,
                    "_speaker": speaker,
                }

                payload["utts"][speaker].append(row)
                payload["_next_utt_id"][speaker] += 1
                current_row_ref = row

                if counters is not None:
                    counters[f"utts_{speaker}"] += 1
                    counters[f"words_{speaker}"] += wc

        payload["sessions"].append({
            "id": session_idx,
            "age": sess["age"],
            "age_m": sess["age_m"],
            "path": rel_path,
        })

        # ensure morph_count filled for rows in this session (if missing %mor)
        for spk in ("CHI", "MOT", "FAT"):
            for r in payload["utts"][spk]:
                if r["session_id"] == session_idx and (r.get("morph_count") in (None, "")):
                    r["morph_count"] = 0

        if counters is not None:
            for spk in ("CHI", "MOT", "FAT"):
                sess_rows = [r for r in payload["utts"][spk] if r["session_id"] == session_idx]
                counters[f"m0_{spk}"] = sum(1 for r in sess_rows if int(r.get("morph_count") or 0) == 0)
            payload["_session_index_rows"].append(counters)

    return payload, missing_age_paths


def _build_caretakers_rows(payload: Dict) -> List[Dict]:
    combined: List[Dict] = []
    for spk in ("MOT", "FAT"):
        for r in payload["utts"][spk]:
            rr = dict(r)
            rr["utt_id_role"] = rr.get("utt_id")
            rr["speaker"] = spk
            combined.append(rr)

    combined.sort(key=lambda r: (
        int(r.get("session_id") or 0),
        str(r.get("file") or ""),
        int(r.get("line_no") or 0),
    ))

    for i, r in enumerate(combined, start=1):
        r["utt_id"] = i

    for r in combined:
        r.pop("_speaker", None)

    return combined


def write_child_outputs(child_dir: Path,
                        child_id: str,
                        payload: Dict,
                        emit_session_counts: bool) -> None:
    for spk in ("CHI", "MOT", "FAT"):
        for r in payload["utts"][spk]:
            r.pop("_speaker", None)

    for spk in ("CHI", "MOT", "FAT"):
        _impute_missing_morph_counts_as_zero(payload["utts"][spk])

    write_csv(child_dir / "child_utts.csv", CSV_UTT_COLUMNS, payload["utts"]["CHI"])
    write_csv(child_dir / "mot_utts.csv",   CSV_UTT_COLUMNS, payload["utts"]["MOT"])
    write_csv(child_dir / "fat_utts.csv",   CSV_UTT_COLUMNS, payload["utts"]["FAT"])

    caretakers_rows = _build_caretakers_rows(payload)
    _impute_missing_morph_counts_as_zero(caretakers_rows)
    write_csv(child_dir / "caretakers_utts.csv", CSV_CARETAKER_COLUMNS, caretakers_rows)

    session_ids = [s["id"] for s in payload["sessions"]]
    session_ages = [s["age"] for s in payload["sessions"]]
    session_ages_m = [s["age_m"] for s in payload["sessions"]]
    session_paths = [s["path"] for s in payload["sessions"]]

    meta_row = {
        "child_id":               child_id,
        "sex":                    payload["sex"],
        "source_group":           payload.get("source_group", ""),
        "session_ids":            json.dumps(session_ids, ensure_ascii=False),
        "session_ages":           json.dumps(session_ages, ensure_ascii=False),
        "session_ages_months":    json.dumps(session_ages_m, ensure_ascii=False),
        "session_paths":          json.dumps(session_paths, ensure_ascii=False),
        "n_sessions":             len(payload["sessions"]),
    }
    write_csv(child_dir / "child_meta.csv", CSV_META_COLUMNS, [meta_row])

    if emit_session_counts and payload.get("_session_index_rows"):
        write_csv(child_dir / "session_index.csv", CSV_SESSION_IDX_COLUMNS, payload["_session_index_rows"])


def build_summary_lines(dataset: str, base_dir: Path, per_child: Dict[str, Dict], missing_age_map: Dict[str, List[str]]) -> List[str]:
    lines: List[str] = []
    lines.append(f"SUMMARY — {dataset} corpus")
    lines.append(f"Base directory: {base_dir}\n")

    total_children = len(per_child)
    total_sessions = sum(len(info["sessions"]) for info in per_child.values())
    total_chi = sum(len(info["utts"]["CHI"]) for info in per_child.values())
    total_mot = sum(len(info["utts"]["MOT"]) for info in per_child.values())
    total_fat = sum(len(info["utts"]["FAT"]) for info in per_child.values())
    lines.append(f"Children: {total_children}")
    lines.append(f"Total sessions: {total_sessions}")
    lines.append(f"Total utterances — CHI: {total_chi:,} | MOT: {total_mot:,} | FAT: {total_fat:,} | Caretakers(MOT+FAT): {total_mot+total_fat:,}\n")

    for child_id, info in sorted(per_child.items()):
        n_sessions = len(info["sessions"])
        counts = [0] * n_sessions
        for spk in ("CHI", "MOT", "FAT"):
            for row in info["utts"][spk]:
                sid = row["session_id"]
                if 1 <= sid <= n_sessions:
                    counts[sid - 1] += 1

        lines.append(f"{child_id} — sessions: {n_sessions}")
        counts_str = " ".join(str(c) for c in counts) if n_sessions else ""
        lines.append(f"utts_per_session (CHI+MOT+FAT): {counts_str}")

        miss = missing_age_map.get(child_id, [])
        if miss:
            lines.append(f"[WARN] Missing/derived CHI age in {len(miss)} session(s):")
            for p in miss:
                lines.append(f"  - {p}")
        lines.append("")

    return lines


def write_summary_files(dataset: str, base_dir: Path,
                        per_child: Dict[str, Dict],
                        missing_age_map: Dict[str, List[str]]) -> None:
    summary_path = base_dir / SUMMARY_FILENAMES[dataset]
    lines = build_summary_lines(dataset, base_dir, per_child, missing_age_map)
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")

    report_path = base_dir / MISSING_AGE_REPORT
    with report_path.open("w", encoding="utf-8") as fh:
        any_missing = False
        for child_id, misses in sorted(missing_age_map.items()):
            if misses:
                any_missing = True
                fh.write(f"{child_id}:\n")
                for p in misses:
                    fh.write(f"  - {p}\n")
        if not any_missing:
            fh.write("No sessions with missing CHI age detected.\n")

# ────────────────────────────────────────────────────────────────
# Orchestration
# ────────────────────────────────────────────────────────────────

def process_dataset(dataset: str, base_override: Optional[str], output_override: Optional[str], emit_session_counts: bool) -> None:
    base_dir, tried = resolve_base_dir(dataset, base_override)
    if not base_dir.exists():
        msg = [f"[ERROR] Base directory not found for {dataset}: {base_dir}"]
        if tried:
            msg.append("Tried candidates:")
            for c in tried:
                msg.append(f"  - {c}")
        msg.append("Tip: pass an explicit path, e.g.:")
        msg.append(f"  uv run python src/prepare_datasets.py --dataset {dataset} --base-dir <path>")
        sys.exit("\n".join(msg))

    output_dir = resolve_output_dir(dataset, base_dir, output_override)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"==> {dataset} | input base:  {base_dir}")
    print(f"==> {dataset} | output base: {output_dir}")

    per_child: Dict[str, Dict] = {}
    missing_age_map: Dict[str, List[str]] = {}

    if dataset == "Hall":
        # Hall layout:
        #   Hall/BlackPro/*.cha
        #   Hall/BlackWork/*.cha
        #   Hall/WhitePro/*.cha
        #   Hall/WhiteWork/*.cha
        # Each .cha file is treated as one child with one session.
        # Output folder usually uses only the child/file stem.
        # If a stem appears more than once, suffix with the Hall group.
        # If the same stem somehow appears more than once within the same group,
        # suffix with group plus an occurrence index.
        group_dirs = sorted(
            p for p in base_dir.iterdir()
            if p.is_dir() and list(p.glob("*.cha"))
        )

        if not group_dirs:
            sys.exit(f"[ERROR] No Hall group folders with .cha files found under: {base_dir}")

        hall_items = []
        stem_total_counts: Dict[str, int] = {}
        stem_group_counts: Dict[Tuple[str, str], int] = {}

        for group_dir in group_dirs:
            group = group_dir.name
            for cha_file in sorted(group_dir.glob("*.cha")):
                stem = cha_file.stem
                hall_items.append((group, group_dir, cha_file, stem))
                stem_total_counts[stem] = stem_total_counts.get(stem, 0) + 1
                stem_group_counts[(group, stem)] = stem_group_counts.get((group, stem), 0) + 1

        stem_group_seen: Dict[Tuple[str, str], int] = {}

        for group, group_dir, cha_file, stem in hall_items:
            n_total = stem_total_counts[stem]
            n_in_group = stem_group_counts[(group, stem)]
            stem_group_seen[(group, stem)] = stem_group_seen.get((group, stem), 0) + 1
            ith = stem_group_seen[(group, stem)]

            if n_total == 1:
                child_id = stem
            elif n_in_group == 1:
                child_id = f"{stem}_{group}"
            else:
                child_id = f"{stem}_{group}_{ith}"

            print(f"  -> {child_id}  [source_group={group}, original_child_id={stem}]")
            payload, missing_ages = collect_child(
                base_dir=base_dir,
                child_dir=group_dir,
                emit_session_counts=emit_session_counts,
                child_id_override=child_id,
                cha_files_override=[cha_file],
                source_group=group,
            )
            per_child[child_id] = payload
            missing_age_map[child_id] = missing_ages
            write_child_outputs(output_dir / child_id, child_id, payload, emit_session_counts=emit_session_counts)
            if missing_ages:
                print(f"     [WARN] {child_id}: {len(missing_ages)} session(s) with missing/derived CHI age")
    else:
        # Original layout:
        #   DATASET_ROOT/child_id/*.cha
        for child_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
            child_id = child_dir.name
            if not list(child_dir.glob("*.cha")):
                continue
            print(f"  -> {child_id}")
            payload, missing_ages = collect_child(base_dir, child_dir, emit_session_counts=emit_session_counts)
            per_child[child_id] = payload
            missing_age_map[child_id] = missing_ages
            write_child_outputs(output_dir / child_id, child_id, payload, emit_session_counts=emit_session_counts)
            if missing_ages:
                print(f"     [WARN] {child_id}: {len(missing_ages)} session(s) with missing/derived CHI age")

    write_summary_files(dataset, output_dir, per_child, missing_age_map)
    print(f"✔ Wrote summary to {output_dir / SUMMARY_FILENAMES[dataset]}")
    print(f"✔ Wrote missing-age report to {output_dir / MISSING_AGE_REPORT}")


def build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Stage 0: Create per-child CHI/MOT/FAT/caretakers CSVs + child_meta.csv for CHILDES subsets (RAW utterances + strict @ handling for cleaned counts)."
    )
    p.add_argument("--dataset", required=True, choices=["Providence", "Manchester", "Brown", "Hall", "all"],
                   help="Which dataset to prepare (or 'all').")
    p.add_argument("--base-dir", default=None,
                   help="Override input base directory for a single dataset. Ignored if --dataset=all.")
    p.add_argument("--output-dir", default=None,
                   help="Override output directory for processed CSVs. Ignored if --dataset=all.")
    p.add_argument("--emit-session-counts", action="store_true",
                   help="Also write session_index.csv with per-session counts per role.")
    return p


def main(argv: List[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    if args.dataset == "all":
        for ds in ["Providence", "Manchester", "Brown", "Hall"]:
            process_dataset(ds, base_override=None, output_override=None, emit_session_counts=args.emit_session_counts)
    else:
        process_dataset(args.dataset, base_override=args.base_dir, output_override=args.output_dir, emit_session_counts=args.emit_session_counts)


if __name__ == "__main__":
    main()
