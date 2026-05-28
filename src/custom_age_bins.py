"""Custom age-bin helpers for early sparse CHILDES months."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence


@dataclass(frozen=True, order=True)
class AgeBin:
    """Inclusive month range used as one age bin."""

    start: int
    end: int

    @property
    def label(self) -> str:
        return f"{self.start:03d}-{self.end:03d}"

    @property
    def width(self) -> int:
        return self.end - self.start + 1

    def contains_month(self, month: int) -> bool:
        return self.start <= month <= self.end


def floor_age_month(age_months: object) -> Optional[int]:
    """Return floor(age_months) as an integer month, or None if invalid."""
    try:
        age = float(age_months)
    except (TypeError, ValueError):
        return None
    if math.isnan(age):
        return None
    return int(math.floor(age))


def count_in_range(month_counts: Mapping[int, int], start: int, end: int) -> int:
    """Sum utterance counts for inclusive integer months."""
    return sum(int(month_counts.get(month, 0)) for month in range(start, end + 1))


def make_standard_bins(start_month: int, max_month: int, bin_months: int = 6) -> List[AgeBin]:
    """Create fixed-width inclusive age bins from start_month through max_month."""
    if bin_months <= 0:
        raise ValueError("bin_months must be positive")
    if max_month < start_month:
        return []
    bins: List[AgeBin] = []
    start = start_month
    while start <= max_month:
        bins.append(AgeBin(start=start, end=min(start + bin_months - 1, max_month)))
        start += bin_months
    return bins


def round_up_to_full_bin_end(start_month: int, max_month: int, bin_months: int) -> int:
    """Return a max month that preserves full fixed-width bins."""
    if max_month < start_month:
        return max_month
    offset = max_month - start_month
    return start_month + ((offset // bin_months) + 1) * bin_months - 1


def make_threshold_early_bins(
    month_counts: Mapping[int, int],
    *,
    threshold: int = 20_000,
    first_start: int = 6,
    first_base_end: int = 17,
    donor_end: int = 23,
    standard_bin_months: int = 6,
    max_month: Optional[int] = None,
) -> List[AgeBin]:
    """
    Build the custom early bins requested for sparse early data.

    The first bin starts as first_start..first_base_end. If it has fewer than
    threshold utterances, months are moved one at a time from the start of the
    donor interval until the first bin reaches threshold or donor_end is
    exhausted. The remaining donor months become the second bin. Later bins are
    fixed-width standard_bin_months intervals.
    """
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    if not (first_start <= first_base_end < donor_end):
        raise ValueError("expected first_start <= first_base_end < donor_end")

    observed_max = max(month_counts.keys(), default=donor_end)
    final_month = max_month if max_month is not None else observed_max
    final_month = max(final_month, donor_end)
    final_month = round_up_to_full_bin_end(donor_end + 1, final_month, standard_bin_months)

    first_end = first_base_end
    while count_in_range(month_counts, first_start, first_end) < threshold and first_end < donor_end:
        first_end += 1

    bins = [AgeBin(first_start, first_end)]
    remainder_start = first_end + 1
    if remainder_start <= donor_end:
        bins.append(AgeBin(remainder_start, donor_end))
    bins.extend(make_standard_bins(donor_end + 1, final_month, standard_bin_months))
    return bins


def make_merged_early_bins(
    *,
    first_start: int = 6,
    first_end: int = 23,
    standard_bin_months: int = 6,
    max_month: Optional[int] = None,
) -> List[AgeBin]:
    """
    Build bins with one merged early interval, then fixed-width intervals.

    This supports the newer decision to use one first bin spanning 006-023,
    justified by the sparsity of speech before 24 months, then preserve the
    existing 6-month intervals from 024 onward.
    """
    if standard_bin_months <= 0:
        raise ValueError("standard_bin_months must be positive")
    if first_start > first_end:
        raise ValueError("expected first_start <= first_end")

    final_month = max_month if max_month is not None else first_end
    final_month = max(final_month, first_end)
    final_month = round_up_to_full_bin_end(first_end + 1, final_month, standard_bin_months)
    return [AgeBin(first_start, first_end), *make_standard_bins(first_end + 1, final_month, standard_bin_months)]


def find_age_bin(age_months: object, bins: Sequence[AgeBin]) -> Optional[AgeBin]:
    """Return the bin containing age_months, or None when outside all bins."""
    month = floor_age_month(age_months)
    if month is None:
        return None
    for age_bin in bins:
        if age_bin.contains_month(month):
            return age_bin
    return None


def age_bins_to_dicts(bins: Iterable[AgeBin]) -> List[Dict[str, int | str]]:
    """Serialize bins as dictionaries."""
    return [
        {"label": age_bin.label, "start": age_bin.start, "end": age_bin.end, "width": age_bin.width}
        for age_bin in bins
    ]


def age_bins_from_dicts(rows: Iterable[Mapping[str, object]]) -> List[AgeBin]:
    """Deserialize bins from dictionaries."""
    return [AgeBin(start=int(row["start"]), end=int(row["end"])) for row in rows]


def write_age_bins_config(
    path: Path,
    *,
    bins: Sequence[AgeBin],
    strategy: str,
    threshold: Optional[int] = None,
    count_basis: str = "child_nonempty_utterances",
) -> None:
    """Write age-bin metadata used by downstream generation."""
    payload = {
        "strategy": strategy,
        "threshold": threshold,
        "count_basis": count_basis,
        "bins": age_bins_to_dicts(bins),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_age_bins_config(path: Path) -> List[AgeBin]:
    """Load age bins from a JSON config, returning an empty list if missing."""
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return age_bins_from_dicts(payload.get("bins", []))
