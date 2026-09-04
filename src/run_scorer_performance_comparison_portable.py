#!/usr/bin/env python3
"""Run or restore the scorer comparison through audited portable-product links.

The storage auditor owns mount discovery.  This entry point knows only stable
product names under the local link farm, so it works regardless of the T7's
drive letter or mount directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.build_scorer_performance_comparison import ScorerInput, run_analysis


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LINK_ROOT = ROOT / "results/external/portable_t7"
DEFAULT_OUTPUT_DIR = ROOT / "results/scorer_performance_comparison_20260904"
DEFAULT_FIG_DIR = ROOT / "figs/scorer_performance_comparison_20260904"

CHILD_PRODUCTS = (
    ("Mistral-7B", "mistral_pbm21_word_surprisal"),
    ("Qwen3-14B", "qwen3_14b_pbm21_word_surprisal"),
    ("TinyDialogues-135M", "tinydialogues_pbm21_word_surprisal"),
)
CAREGIVER_FILES = (
    ("Mistral-7B", "mistral-7b-v0.3.response_utility.csv.gz"),
    ("Qwen3-14B", "qwen3-14b.response_utility.csv.gz"),
    ("TinyDialogues-135M", "tinydialogues.response_utility.csv.gz"),
)
HISTORICAL_FILES = (
    "plot_surprisal_vs_length.py",
    "plot_surprisal_vs_length_by_model_age_schemes.py",
)


def require_product(link_root: Path, name: str) -> Path:
    product = link_root / name
    if not product.is_dir():
        raise RuntimeError(
            f"missing audited portable product {name!r} under {link_root}; "
            "run src/audit_portable_project_storage.py --create-links first"
        )
    return product


def resolve_inputs(
    link_root: Path,
) -> tuple[list[ScorerInput], list[ScorerInput], list[Path]]:
    child_scorers = [
        ScorerInput(label, require_product(link_root, product))
        for label, product in CHILD_PRODUCTS
    ]
    caregiver_root = require_product(link_root, "downstream_caregiver_response")
    caregiver_scorers = [
        ScorerInput(label, caregiver_root / "datasets" / filename)
        for label, filename in CAREGIVER_FILES
    ]
    historical_root = require_product(link_root, "scorer_performance_historical_sources")
    historical_sources = [historical_root / filename for filename in HISTORICAL_FILES]
    required_files = [*(item.path for item in caregiver_scorers), *historical_sources]
    missing = [path for path in required_files if not path.is_file()]
    if missing:
        raise RuntimeError("portable products are incomplete: " + ", ".join(str(path) for path in missing))
    return child_scorers, caregiver_scorers, historical_sources


def _refuse_storage_write_through(path: Path, link_root: Path) -> None:
    if path.is_symlink():
        raise RuntimeError(
            f"refusing to run into restored storage link {path}; remove the link "
            "or select a different native output path"
        )
    resolved_path = path.resolve(strict=False)
    if link_root.is_dir():
        for product in link_root.iterdir():
            resolved_product = product.resolve(strict=False)
            if resolved_path == resolved_product or resolved_product in resolved_path.parents:
                raise RuntimeError(
                    f"refusing to run inside portable storage product {product.name!r}: {path}"
                )


def run_from_links(
    *,
    link_root: Path,
    output_dir: Path,
    fig_dir: Path,
    report_md: Path,
    report_html: Path,
    protocol: Path,
    bootstrap_reps: int,
    seed: int,
    duckdb_memory_limit: str,
    duckdb_threads: int,
) -> dict[str, object]:
    _refuse_storage_write_through(output_dir, link_root)
    _refuse_storage_write_through(fig_dir, link_root)
    child_scorers, caregiver_scorers, historical_sources = resolve_inputs(link_root)
    return run_analysis(
        child_scorers,
        caregiver_scorers,
        output_dir,
        fig_dir,
        report_md,
        report_html,
        protocol,
        historical_sources,
        bootstrap_reps,
        seed,
        duckdb_memory_limit,
        duckdb_threads,
    )


def local_link_action(source: Path, destination: Path) -> str:
    if not source.is_dir():
        raise RuntimeError(f"missing completed portable product: {source}")
    if destination.is_symlink():
        if destination.resolve() == source.resolve():
            return "already-linked"
        raise FileExistsError(f"refusing to replace different link: {destination}")
    if destination.exists():
        raise FileExistsError(f"refusing to replace existing path: {destination}")
    return "created"


def create_local_link(source: Path, destination: Path) -> str:
    action = local_link_action(source, destination)
    if action == "already-linked":
        return action
    destination.parent.mkdir(parents=True, exist_ok=True)
    relative_source = os.path.relpath(source, destination.parent)
    destination.symlink_to(relative_source, target_is_directory=True)
    return action


def restore_completed_products(
    link_root: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    fig_dir: Path = DEFAULT_FIG_DIR,
) -> dict[str, str]:
    sources = {
        "analysis": require_product(link_root, "scorer_performance_comparison"),
        "figures": require_product(link_root, "scorer_performance_figures"),
    }
    destinations = {"analysis": output_dir, "figures": fig_dir}
    actions = {
        name: local_link_action(source, destinations[name])
        for name, source in sources.items()
    }
    for name, action in actions.items():
        if action == "created":
            create_local_link(sources[name], destinations[name])
    return actions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--link-root", type=Path, default=DEFAULT_LINK_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="rebuild from audited portable inputs")
    run_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    run_parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    run_parser.add_argument(
        "--report-md",
        type=Path,
        default=ROOT / "docs/scorer_performance_comparison_2026-09-04.md",
    )
    run_parser.add_argument(
        "--report-html",
        type=Path,
        default=ROOT / "docs/scorer_performance_comparison_2026-09-04.html",
    )
    run_parser.add_argument(
        "--protocol",
        type=Path,
        default=ROOT / "docs/scorer_performance_comparison_protocol_2026-09-04.md",
    )
    run_parser.add_argument("--bootstrap-reps", type=int, default=10_000)
    run_parser.add_argument("--seed", type=int, default=20260904)
    run_parser.add_argument("--duckdb-memory-limit", default="2GB")
    run_parser.add_argument("--duckdb-threads", type=int, default=4)

    restore_parser = subparsers.add_parser(
        "restore", help="link the completed audited outputs into this clone"
    )
    restore_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    restore_parser.add_argument("--fig-dir", type=Path, default=DEFAULT_FIG_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "restore":
        report = restore_completed_products(args.link_root, args.output_dir, args.fig_dir)
    else:
        report = run_from_links(
            link_root=args.link_root,
            output_dir=args.output_dir,
            fig_dir=args.fig_dir,
            report_md=args.report_md,
            report_html=args.report_html,
            protocol=args.protocol,
            bootstrap_reps=args.bootstrap_reps,
            seed=args.seed,
            duckdb_memory_limit=args.duckdb_memory_limit,
            duckdb_threads=args.duckdb_threads,
        )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
