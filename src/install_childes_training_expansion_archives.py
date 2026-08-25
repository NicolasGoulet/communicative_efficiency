#!/usr/bin/env python3
"""Safely install authenticated CHILDES ZIPs and run Stage-0 preparation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from prepare_datasets import process_dataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARCHIVE_DIRS = (PROJECT_ROOT / "data" / "zip_files", Path("/home/apaixonada/Downloads"))
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw_data"
DEFAULT_PREPARED_ROOT = PROJECT_ROOT / "data" / "preprocessed_data"
DEFAULT_AUDIT = PROJECT_ROOT / "results" / "transformer_training_expansion" / "installed_source_archives.csv"
DEFAULT_DATASETS = ("Howe", "Edinburgh", "Thomas")
AUDIT_COLUMNS = [
    "dataset",
    "archive",
    "archive_bytes",
    "archive_sha256",
    "chat_members",
    "raw_chat_files",
    "prepared_children",
    "prepared_rows",
    "status",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_archive(dataset: str, archive_dirs: Sequence[Path]) -> Optional[Path]:
    """Find an exact corpus-named ZIP without guessing among partial files."""
    candidate_names = (f"{dataset}.zip", f"{dataset.lower()}.zip")
    for archive_dir in archive_dirs:
        for name in candidate_names:
            candidate = archive_dir.expanduser() / name
            if candidate.is_file():
                return candidate.resolve()
    return None


def safe_member_parts(member_name: str) -> Tuple[str, ...]:
    path = PurePosixPath(member_name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe ZIP member: {member_name!r}")
    return tuple(path.parts)


def selected_chat_members(archive: zipfile.ZipFile, dataset: str) -> List[Tuple[zipfile.ZipInfo, Path]]:
    """Map corpus CHAT members to paths relative to data/raw_data/<Dataset>."""
    candidates: List[Tuple[zipfile.ZipInfo, Tuple[str, ...]]] = []
    for info in archive.infolist():
        if info.is_dir() or not info.filename.lower().endswith(".cha"):
            continue
        parts = safe_member_parts(info.filename)
        candidates.append((info, parts))
    if not candidates:
        raise ValueError("Archive contains no CHAT files")

    dataset_indices = [
        index
        for _info, parts in candidates
        for index, part in enumerate(parts)
        if part.lower() == dataset.lower()
    ]
    use_dataset_component = bool(dataset_indices)
    mapped: List[Tuple[zipfile.ZipInfo, Path]] = []
    for info, parts in candidates:
        relative_parts: Tuple[str, ...]
        if use_dataset_component:
            indices = [index for index, part in enumerate(parts) if part.lower() == dataset.lower()]
            if not indices:
                continue
            relative_parts = parts[indices[-1] + 1 :]
        else:
            relative_parts = parts[1:] if len(parts) > 1 else parts
        if not relative_parts:
            raise ValueError(f"Could not derive relative CHAT path for {info.filename}")
        relative = Path(*relative_parts)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe derived path for {info.filename}")
        mapped.append((info, relative))
    if not mapped:
        raise ValueError(f"Archive contains no CHAT members for {dataset}")
    return mapped


def extract_chat_archive(archive_path: Path, dataset: str, raw_root: Path) -> Tuple[Path, int]:
    """Extract only safe CHAT members into a previously absent corpus tree."""
    target_root = raw_root / dataset
    if target_root.exists() and any(target_root.rglob("*.cha")):
        raise FileExistsError(
            f"Refusing to overwrite existing raw CHAT tree: {target_root}. "
            "Move it aside explicitly before reinstalling."
        )
    target_root.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(archive_path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError(f"ZIP CRC check failed at {bad_member}")
            members = selected_chat_members(archive, dataset)
            for info, relative in members:
                destination = target_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, destination.open("xb") as target:
                    shutil.copyfileobj(source, target)
    except Exception:
        # Do not silently delete a pre-existing corpus. The existence check
        # above guarantees this directory was created by the current attempt.
        if target_root.exists():
            shutil.rmtree(target_root)
        raise
    return target_root, len(members)


def write_audit(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: Dict[str, Dict[str, str]] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            existing = {row["dataset"]: row for row in csv.DictReader(handle)}
    for row in rows:
        existing[str(row["dataset"])] = {key: str(value) for key, value in row.items()}
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing[key] for key in sorted(existing))


def install_datasets(
    datasets: Sequence[str],
    *,
    archive_dirs: Sequence[Path],
    raw_root: Path,
    prepared_root: Path,
    audit_path: Path,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    missing: List[str] = []
    for dataset in datasets:
        archive_path = find_archive(dataset, archive_dirs)
        if archive_path is None:
            missing.append(dataset)
            continue
        raw_dataset_root, member_count = extract_chat_archive(archive_path, dataset, raw_root)
        summary = process_dataset(
            dataset,
            prepared_root,
            base_dir=raw_dataset_root,
            testing=False,
        )
        raw_chat_files = len(list(raw_dataset_root.rglob("*.cha")))
        row = {
            "dataset": dataset,
            "archive": str(archive_path),
            "archive_bytes": archive_path.stat().st_size,
            "archive_sha256": sha256_file(archive_path),
            "chat_members": member_count,
            "raw_chat_files": raw_chat_files,
            "prepared_children": summary["children"],
            "prepared_rows": summary["rows"],
            "status": "installed_and_stage0_prepared",
        }
        rows.append(row)
        print(
            f"[OK] {dataset}: chat_files={raw_chat_files} "
            f"children={summary['children']} prepared_rows={summary['rows']}"
        )
    if rows:
        write_audit(audit_path, rows)
    if missing:
        print(f"[MISSING] Exact ZIP not found for: {', '.join(missing)}")
    return rows


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS))
    parser.add_argument("--archive-dir", action="append", type=Path, dest="archive_dirs")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--prepared-root", type=Path, default=DEFAULT_PREPARED_ROOT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    archive_dirs = tuple(args.archive_dirs or DEFAULT_ARCHIVE_DIRS)
    rows = install_datasets(
        args.datasets,
        archive_dirs=archive_dirs,
        raw_root=args.raw_root.resolve(),
        prepared_root=args.prepared_root.resolve(),
        audit_path=args.audit.resolve(),
    )
    print(f"[SUMMARY] installed={len(rows)} requested={len(args.datasets)}")


if __name__ == "__main__":
    main()
