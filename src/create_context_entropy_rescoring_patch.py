#!/usr/bin/env python3
"""Create a scorer-ready patch manifest for missing Route 1 context entropy.

The context-entropy scorer in ``compute_surprisal_mila`` expects a manifest
with one row per distinct context string:

``manifest_row, context_id, context_col, context_text``

This script converts the Route 1 entropy-join missing-context audit into that
manifest, preserving a richer example table for later provenance checks.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import re
import tarfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence, TextIO


DEFAULT_ROUTE1_DIR = Path("results/route1_analysis_dataset")
DEFAULT_MISSING_CONTEXTS = DEFAULT_ROUTE1_DIR / "missing_context_entropy_contexts.csv"
DEFAULT_OUTPUT_DIR = Path("results/scoring_bundles/route1_missing_context_entropy_patch_2026-06-04")

SPACE_RE = re.compile(r"\s+")
REQUIRED_MISSING_COLUMNS = {
    "context_col",
    "context_text",
    "n_route1_rows",
    "example_dataset",
    "example_child_id",
    "example_file",
    "example_line_no",
    "example_context_k",
}


@dataclass(frozen=True)
class PatchSummary:
    missing_contexts_csv: str
    output_dir: str
    manifest_csv_gz: str
    contexts_with_examples_csv: str
    tarball: str
    missing_context_rows_read: int
    nonempty_context_rows_read: int
    manifest_rows_written: int
    duplicate_context_id_rows_collapsed: int
    total_route1_rows_represented: int


def normalize_context(text: object) -> str:
    """Match ``compute_surprisal_mila`` context normalization."""

    if text is None:
        return ""
    raw = str(text)
    if raw.lower() == "nan":
        return ""
    return SPACE_RE.sub(" ", raw).strip()


def context_id(text: object) -> str:
    """Match ``compute_surprisal_mila.analysis.scripts.context_entropy_common``."""

    normalized = normalize_context(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def open_text_output(path: Path) -> TextIO:
    """Open plain or gzipped text output based on suffix."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if ".gz" in path.suffixes:
        return gzip.open(path, "wt", encoding="utf-8", newline="")
    return path.open("w", encoding="utf-8", newline="")


def read_missing_context_rows(path: Path) -> list[dict[str, str]]:
    """Read and validate the Route 1 missing-context audit."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_MISSING_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def dedupe_manifest_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Return scorer manifest rows, deduplicated by normalized context text."""

    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        normalized = normalize_context(row.get("context_text", ""))
        if not normalized:
            continue
        cid = context_id(normalized)
        previous = by_id.get(cid)
        if previous is None:
            by_id[cid] = {
                "context_id": cid,
                "context_col": normalize_context(row.get("context_col", "")),
                "context_text": normalized,
            }
            continue
        if previous["context_text"] != normalized:
            raise ValueError(
                "context_id collision between "
                f"{previous['context_text']!r} and {normalized!r}"
            )
    manifest = sorted(by_id.values(), key=lambda r: (r["context_col"], r["context_text"], r["context_id"]))
    for idx, row in enumerate(manifest):
        row["manifest_row"] = str(idx)
    return [{"manifest_row": row["manifest_row"], "context_id": row["context_id"], "context_col": row["context_col"], "context_text": row["context_text"]} for row in manifest]


def write_csv(path: Path, rows: Sequence[dict[str, str]], fieldnames: Sequence[str]) -> None:
    """Write rows with an explicit schema."""

    with open_text_output(path) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def add_context_ids_to_example_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Return the missing-context audit rows with normalized text and IDs."""

    out: list[dict[str, str]] = []
    for row in rows:
        enriched = dict(row)
        normalized = normalize_context(enriched.get("context_text", ""))
        enriched["context_text_normalized"] = normalized
        enriched["context_id"] = context_id(normalized) if normalized else ""
        out.append(enriched)
    return out


def write_readme(path: Path, *, manifest_path: Path, examples_path: Path) -> None:
    """Write local scorer instructions for the patch bundle."""

    text = f"""# Route 1 Missing Context-Entropy Patch

This bundle contains only the context strings that were present in the current
Route 1 analysis table but absent from the already-scored context-entropy
manifest.

Files:

- `{manifest_path.name}`: scorer-ready manifest with `manifest_row`,
  `context_id`, `context_col`, and `context_text`.
- `{examples_path.name}`: provenance table from the Route 1 join audit showing
  how many Route 1 rows each context represents and one example row.

The existing entropy run is complete for its original manifest. This patch is
for additional contexts introduced by the final Route 1 table.

Suggested local scoring command from the `compute_surprisal_mila` repo root:

```bash
MODEL="${{MODEL:-/tmp/hf_models/9718118/mistralai__Mistral-7B-v0.3}}"

.venv/bin/python src/score_context_entropy.py \\
  --manifest new_data/route1_missing_context_entropy_patch/{manifest_path.name} \\
  --output mila_results/context_entropy_mistral_route1_patch/context_entropy_features_route1_missing_patch.csv.gz \\
  --model "$MODEL" \\
  --device cuda \\
  --dtype auto \\
  --batch-size 64 \\
  --max-length 512 \\
  --overwrite
```

After scoring, bring
`mila_results/context_entropy_mistral_route1_patch/context_entropy_features_route1_missing_patch.csv.gz`
back to `communicative_efficiency` and concatenate it with the existing
`context_entropy_features.csv.gz` before rerunning the Route 1 entropy attach.
"""
    path.write_text(text, encoding="utf-8")


def create_tarball(output_dir: Path) -> Path:
    """Archive the patch directory for transfer."""

    tarball = output_dir.with_suffix(".tar.gz")
    with tarfile.open(tarball, "w:gz") as tar:
        for path in sorted(output_dir.rglob("*")):
            tar.add(path, arcname=Path(output_dir.name) / path.relative_to(output_dir))
    return tarball


def build_patch(*, missing_contexts_csv: Path, output_dir: Path) -> PatchSummary:
    """Build the context-entropy patch bundle."""

    rows = read_missing_context_rows(missing_contexts_csv)
    nonempty_rows = [row for row in rows if normalize_context(row.get("context_text", ""))]
    manifest_rows = dedupe_manifest_rows(nonempty_rows)
    example_rows = add_context_ids_to_example_rows(rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "context_entropy_patch_manifest.csv.gz"
    examples_path = output_dir / "context_entropy_patch_contexts_with_examples.csv"
    readme_path = output_dir / "README.md"
    summary_path = output_dir / "summary.csv"

    write_csv(
        manifest_path,
        manifest_rows,
        ["manifest_row", "context_id", "context_col", "context_text"],
    )
    example_fieldnames = [
        "context_id",
        "context_col",
        "context_text",
        "context_text_normalized",
        "n_route1_rows",
        "example_dataset",
        "example_child_id",
        "example_file",
        "example_line_no",
        "example_context_k",
    ]
    write_csv(examples_path, example_rows, example_fieldnames)
    write_readme(readme_path, manifest_path=manifest_path, examples_path=examples_path)

    duplicate_collapsed = len(nonempty_rows) - len(manifest_rows)
    total_route1_rows = sum(int(row.get("n_route1_rows") or 0) for row in rows)
    tarball = create_tarball(output_dir)
    summary = PatchSummary(
        missing_contexts_csv=str(missing_contexts_csv),
        output_dir=str(output_dir),
        manifest_csv_gz=str(manifest_path),
        contexts_with_examples_csv=str(examples_path),
        tarball=str(tarball),
        missing_context_rows_read=len(rows),
        nonempty_context_rows_read=len(nonempty_rows),
        manifest_rows_written=len(manifest_rows),
        duplicate_context_id_rows_collapsed=duplicate_collapsed,
        total_route1_rows_represented=total_route1_rows,
    )
    write_csv(summary_path, [asdict(summary)], list(asdict(summary).keys()))
    return summary


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing-contexts-csv", type=Path, default=DEFAULT_MISSING_CONTEXTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_cli().parse_args(argv)
    summary = build_patch(
        missing_contexts_csv=args.missing_contexts_csv,
        output_dir=args.output_dir,
    )
    print("[OK] wrote Route 1 context-entropy patch")
    for key, value in asdict(summary).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
