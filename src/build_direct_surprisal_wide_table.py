#!/usr/bin/env python3
"""Build audited wide direct-surprisal tables from one scored output tree.

The child table has one row per original child utterance. It keeps real and
random/unigram/bigram/trigram target scores under k0-k3 in separate columns,
adds within-target context gains and generated-minus-real gaps, and preserves
enough provenance to join scorers without relying on row position.

The caretaker table has one row per caretaker utterance with k0-k3 scores and
context gains. Input files are streamed in lockstep per child so the full-79
tree can be validated without loading the 28.7-million-cell scored matrix into
memory.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import itertools
import json
import math
import os
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence, TextIO

from build_route1_report_assets import age_to_route1_bin, resolve_age_months
from utterance_count_strategies import normalize_text, word_tokens_regex


CONTEXTS = ("k0", "k1", "k2", "k3")
CHILD_MODES = ("real", "random", "unigram", "bigram", "trigram")
PBM_DATASETS = frozenset({"Brown", "Manchester", "Providence"})

METADATA_COLUMNS = [
    "scorer_id",
    "model_slug",
    "model_used",
    "model_revision",
    "tokenizer_revision",
    "scoring_dtype",
    "scoring_code_revision",
    "dataset",
    "child_id",
    "child_key",
    "sample_group",
    "session_id",
    "age_months",
    "age_months_source",
    "age_bin",
    "file",
    "line_no",
    "utt_id",
    "utterance_id",
]


def child_mode_columns(mode: str) -> list[str]:
    columns = [
        f"{mode}_target_text",
        f"{mode}_target_text_sha256",
        f"{mode}_nb_words",
        f"{mode}_nb_characters",
    ]
    for context in CONTEXTS:
        columns.extend(
            [
                f"{mode}_{context}_sum_bits",
                f"{mode}_{context}_mean_bits_per_token",
                f"{mode}_{context}_n_eval_tokens",
            ]
        )
    for context in CONTEXTS[1:]:
        columns.append(f"{mode}_context_gain_{context}")
    if mode != "real":
        for context in CONTEXTS:
            columns.append(f"{mode}_minus_real_{context}_bits")
    return columns


CHILD_WIDE_COLUMNS = [
    *METADATA_COLUMNS,
    "context_k1",
    "context_k2",
    "context_k3",
    "context_k1_sha256",
    "context_k2_sha256",
    "context_k3_sha256",
    "context_available_k1",
    "context_available_k2",
    "context_available_k3",
    *itertools.chain.from_iterable(child_mode_columns(mode) for mode in CHILD_MODES),
]

CARETAKER_WIDE_COLUMNS = [
    *METADATA_COLUMNS,
    "speaker",
    "target_text",
    "target_text_sha256",
    "nb_words",
    "nb_characters",
    "context_k1",
    "context_k2",
    "context_k3",
    "context_k1_sha256",
    "context_k2_sha256",
    "context_k3_sha256",
    "context_available_k1",
    "context_available_k2",
    "context_available_k3",
    *itertools.chain.from_iterable(
        (
            f"{context}_sum_bits",
            f"{context}_mean_bits_per_token",
            f"{context}_n_eval_tokens",
        )
        for context in CONTEXTS
    ),
    "context_gain_k1",
    "context_gain_k2",
    "context_gain_k3",
]


@dataclass
class FileAudit:
    scorer_id: str
    dataset: str
    child_id: str
    role: str
    mode: str
    context_k: str
    scored_file: str
    rows: int = 0
    blank_target_rows: int = 0
    missing_sum_bits_rows: int = 0
    zero_eval_token_rows: int = 0
    blank_context_rows: int = 0
    key_mismatch_rows: int = 0
    target_mismatch_rows: int = 0


def stable_sha256(value: object) -> str:
    text = normalize_text(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""


def source_key(row: Mapping[str, str]) -> tuple[str, str, str, str, str]:
    return (
        normalize_text(row.get("dataset", "")),
        normalize_text(row.get("child_id", "")),
        normalize_text(row.get("file", "")),
        normalize_text(row.get("line_no", "")),
        normalize_text(row.get("utt_id", "")),
    )


def utterance_id(row: Mapping[str, str], role: str) -> str:
    return stable_sha256("|".join([*source_key(row), role]))[:24]


def parse_float(value: object) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_int(value: object) -> int | None:
    number = parse_float(value)
    if number is None:
        return None
    return int(number)


def fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.12g}"


def difference(left: object, right: object) -> str:
    left_number = parse_float(left)
    right_number = parse_float(right)
    if left_number is None or right_number is None:
        return ""
    return fmt(left_number - right_number)


def count_words(text: object) -> int:
    return len(word_tokens_regex(normalize_text(text)))


def count_characters(text: object) -> int:
    return sum(1 for char in normalize_text(text) if not char.isspace())


def target_column(mode: str, role: str = "child") -> str:
    if role == "caretaker":
        return "caretaker_utterance_clean"
    if mode == "real":
        return "chi_utterance_clean"
    return f"{mode}_model_utterance_bin6"


def context_condition(context: str) -> str:
    return "WITHOUT_context" if context == "k0" else "WITH_context"


def scored_filename(mode: str, role: str) -> str:
    if role == "caretaker":
        return "caretakers.surprisal_scoring__caretaker.scored.csv"
    return f"chi.surprisal_scoring__{mode}.scored.csv"


def model_dirs(scored_root: Path) -> list[Path]:
    base = scored_root / "WITHOUT_context" / "k0"
    if not base.is_dir():
        raise FileNotFoundError(f"Missing scored k0 root: {base}")
    dirs = sorted(path for path in base.iterdir() if path.is_dir())
    if not dirs:
        raise FileNotFoundError(f"No model directory under {base}")
    return dirs


def child_contracts(scored_root: Path) -> list[tuple[str, str, str]]:
    contracts: list[tuple[str, str, str]] = []
    for model_dir in model_dirs(scored_root):
        for path in sorted(model_dir.glob("*/*/chi.surprisal_scoring__real.scored.csv")):
            contracts.append((model_dir.name, path.parent.parent.name, path.parent.name))
    return contracts


def scored_path(
    scored_root: Path,
    model_slug: str,
    dataset: str,
    child: str,
    mode: str,
    context: str,
    role: str,
) -> Path:
    return (
        scored_root
        / context_condition(context)
        / context
        / model_slug
        / dataset
        / child
        / scored_filename(mode, role)
    )


def open_csv_reader(stack: ExitStack, path: Path) -> csv.DictReader:
    handle = stack.enter_context(path.open("r", encoding="utf-8", newline=""))
    return csv.DictReader(handle)


def open_csv_output(path: Path) -> TextIO:
    path.parent.mkdir(parents=True, exist_ok=True)
    if ".gz" in path.suffixes:
        return gzip.open(path, "wt", encoding="utf-8", newline="")
    return path.open("w", encoding="utf-8", newline="")


def temporary_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.tmp")


def scorer_provenance(row: Mapping[str, str], scorer_id: str, model_slug: str) -> dict[str, str]:
    return {
        "scorer_id": scorer_id,
        "model_slug": model_slug,
        "model_used": normalize_text(row.get("model_used", "")),
        "model_revision": normalize_text(row.get("model_revision", "")),
        "tokenizer_revision": normalize_text(row.get("tokenizer_revision", "")),
        "scoring_dtype": normalize_text(row.get("scoring_dtype", "")),
        "scoring_code_revision": normalize_text(row.get("scoring_code_revision", "")),
    }


def base_metadata(
    row: Mapping[str, str], scorer_id: str, model_slug: str, role: str
) -> dict[str, object]:
    age, age_source = resolve_age_months(row.get("age_months", ""), row.get("file", ""))
    dataset = normalize_text(row.get("dataset", ""))
    child = normalize_text(row.get("child_id", ""))
    return {
        **scorer_provenance(row, scorer_id, model_slug),
        "dataset": dataset,
        "child_id": child,
        "child_key": f"{dataset}/{child}",
        "sample_group": "pbm_discovery" if dataset in PBM_DATASETS else "non_pbm_confirmation",
        "session_id": normalize_text(row.get("session_id", "")),
        "age_months": fmt(age),
        "age_months_source": age_source,
        "age_bin": age_to_route1_bin(age) or "",
        "file": normalize_text(row.get("file", "")),
        "line_no": normalize_text(row.get("line_no", "")),
        "utt_id": normalize_text(row.get("utt_id", "")),
        "utterance_id": utterance_id(row, role),
    }


def validate_paths(paths: Mapping[tuple[str, str], Path]) -> None:
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        preview = "\n".join(missing[:20])
        raise FileNotFoundError(f"Missing {len(missing)} scored contract files:\n{preview}")


def process_child_contract(
    *,
    scored_root: Path,
    scorer_id: str,
    model_slug: str,
    dataset: str,
    child: str,
    writer: csv.DictWriter,
) -> tuple[list[FileAudit], int]:
    paths = {
        (mode, context): scored_path(
            scored_root, model_slug, dataset, child, mode, context, "child"
        )
        for mode in CHILD_MODES
        for context in CONTEXTS
    }
    validate_paths(paths)
    audits = {
        key: FileAudit(
            scorer_id=scorer_id,
            dataset=dataset,
            child_id=child,
            role="child",
            mode=key[0],
            context_k=key[1],
            scored_file=str(path),
        )
        for key, path in paths.items()
    }
    rows_written = 0

    with ExitStack() as stack:
        readers = {key: open_csv_reader(stack, path) for key, path in paths.items()}
        keys = list(readers)
        for row_number, row_group in enumerate(
            itertools.zip_longest(*(readers[key] for key in keys)), start=1
        ):
            if any(row is None for row in row_group):
                lengths = {key: audits[key].rows for key in keys}
                raise ValueError(
                    f"Row-count mismatch for {dataset}/{child} at row {row_number}: {lengths}"
                )
            rows = {key: row for key, row in zip(keys, row_group)}
            base = rows[("real", "k0")]
            base_key = source_key(base)
            output: dict[str, object] = base_metadata(
                base, scorer_id, model_slug, "child"
            )

            for key, row in rows.items():
                audit = audits[key]
                audit.rows += 1
                if source_key(row) != base_key:
                    audit.key_mismatch_rows += 1
                    raise ValueError(
                        f"Source-key mismatch for {dataset}/{child} {key} row {row_number}: "
                        f"{source_key(row)} != {base_key}"
                    )

            for context in CONTEXTS[1:]:
                context_text = normalize_text(rows[("real", context)].get(f"context_{context}", ""))
                output[f"context_{context}"] = context_text
                output[f"context_{context}_sha256"] = stable_sha256(context_text)
                output[f"context_available_{context}"] = int(bool(context_text))

            for mode in CHILD_MODES:
                column = target_column(mode)
                target_by_context = {
                    context: normalize_text(rows[(mode, context)].get(column, ""))
                    for context in CONTEXTS
                }
                nonblank_targets = {value for value in target_by_context.values() if value}
                if len(nonblank_targets) > 1:
                    for context in CONTEXTS:
                        audits[(mode, context)].target_mismatch_rows += 1
                    raise ValueError(
                        f"Target mismatch for {dataset}/{child} mode={mode} row={row_number}: "
                        f"{target_by_context}"
                    )
                target = target_by_context["k0"] or next(iter(nonblank_targets), "")
                output[f"{mode}_target_text"] = target
                output[f"{mode}_target_text_sha256"] = stable_sha256(target)
                output[f"{mode}_nb_words"] = count_words(target)
                output[f"{mode}_nb_characters"] = count_characters(target)

                for context in CONTEXTS:
                    row = rows[(mode, context)]
                    audit = audits[(mode, context)]
                    row_target = target_by_context[context]
                    sum_bits = normalize_text(row.get("sum_bits", ""))
                    mean_bits = normalize_text(row.get("mean_bits_per_token", ""))
                    n_eval = normalize_text(row.get("n_eval_tokens", ""))
                    output[f"{mode}_{context}_sum_bits"] = sum_bits
                    output[f"{mode}_{context}_mean_bits_per_token"] = mean_bits
                    output[f"{mode}_{context}_n_eval_tokens"] = n_eval
                    if not row_target:
                        audit.blank_target_rows += 1
                    if parse_float(sum_bits) is None:
                        audit.missing_sum_bits_rows += 1
                    if (parse_int(n_eval) or 0) <= 0:
                        audit.zero_eval_token_rows += 1
                    if context != "k0" and not normalize_text(row.get(f"context_{context}", "")):
                        audit.blank_context_rows += 1

                for context in CONTEXTS[1:]:
                    output[f"{mode}_context_gain_{context}"] = difference(
                        output[f"{mode}_k0_sum_bits"], output[f"{mode}_{context}_sum_bits"]
                    )
                if mode != "real":
                    for context in CONTEXTS:
                        output[f"{mode}_minus_real_{context}_bits"] = difference(
                            output[f"{mode}_{context}_sum_bits"],
                            output[f"real_{context}_sum_bits"],
                        )

            writer.writerow(output)
            rows_written += 1

    return list(audits.values()), rows_written


def process_caretaker_contract(
    *,
    scored_root: Path,
    scorer_id: str,
    model_slug: str,
    dataset: str,
    child: str,
    writer: csv.DictWriter,
) -> tuple[list[FileAudit], int]:
    paths = {
        ("caretaker", context): scored_path(
            scored_root, model_slug, dataset, child, "caretaker", context, "caretaker"
        )
        for context in CONTEXTS
    }
    validate_paths(paths)
    audits = {
        key: FileAudit(
            scorer_id=scorer_id,
            dataset=dataset,
            child_id=child,
            role="caretaker",
            mode="caretaker",
            context_k=key[1],
            scored_file=str(path),
        )
        for key, path in paths.items()
    }
    rows_written = 0

    with ExitStack() as stack:
        readers = {key: open_csv_reader(stack, path) for key, path in paths.items()}
        keys = list(readers)
        for row_number, row_group in enumerate(
            itertools.zip_longest(*(readers[key] for key in keys)), start=1
        ):
            if any(row is None for row in row_group):
                lengths = {key: audits[key].rows for key in keys}
                raise ValueError(
                    f"Caretaker row-count mismatch for {dataset}/{child} at row {row_number}: {lengths}"
                )
            rows = {key: row for key, row in zip(keys, row_group)}
            base = rows[("caretaker", "k0")]
            base_key = source_key(base)
            output: dict[str, object] = base_metadata(
                base, scorer_id, model_slug, "caretaker"
            )
            output["speaker"] = normalize_text(base.get("speaker", ""))

            targets: dict[str, str] = {}
            for key, row in rows.items():
                audit = audits[key]
                audit.rows += 1
                if source_key(row) != base_key:
                    audit.key_mismatch_rows += 1
                    raise ValueError(
                        f"Caretaker source-key mismatch for {dataset}/{child} {key} "
                        f"row {row_number}"
                    )
                targets[key[1]] = normalize_text(row.get("caretaker_utterance_clean", ""))
            nonblank_targets = {value for value in targets.values() if value}
            if len(nonblank_targets) > 1:
                for audit in audits.values():
                    audit.target_mismatch_rows += 1
                raise ValueError(
                    f"Caretaker target mismatch for {dataset}/{child} row {row_number}: {targets}"
                )
            target = targets["k0"] or next(iter(nonblank_targets), "")
            output["target_text"] = target
            output["target_text_sha256"] = stable_sha256(target)
            output["nb_words"] = count_words(target)
            output["nb_characters"] = count_characters(target)

            for context in CONTEXTS[1:]:
                context_text = normalize_text(rows[("caretaker", context)].get(f"context_{context}", ""))
                output[f"context_{context}"] = context_text
                output[f"context_{context}_sha256"] = stable_sha256(context_text)
                output[f"context_available_{context}"] = int(bool(context_text))

            for context in CONTEXTS:
                row = rows[("caretaker", context)]
                audit = audits[("caretaker", context)]
                sum_bits = normalize_text(row.get("sum_bits", ""))
                mean_bits = normalize_text(row.get("mean_bits_per_token", ""))
                n_eval = normalize_text(row.get("n_eval_tokens", ""))
                output[f"{context}_sum_bits"] = sum_bits
                output[f"{context}_mean_bits_per_token"] = mean_bits
                output[f"{context}_n_eval_tokens"] = n_eval
                if not targets[context]:
                    audit.blank_target_rows += 1
                if parse_float(sum_bits) is None:
                    audit.missing_sum_bits_rows += 1
                if (parse_int(n_eval) or 0) <= 0:
                    audit.zero_eval_token_rows += 1
                if context != "k0" and not normalize_text(row.get(f"context_{context}", "")):
                    audit.blank_context_rows += 1
            for context in CONTEXTS[1:]:
                output[f"context_gain_{context}"] = difference(
                    output["k0_sum_bits"], output[f"{context}_sum_bits"]
                )

            writer.writerow(output)
            rows_written += 1

    return list(audits.values()), rows_written


def write_file_audit(audits: Iterable[FileAudit], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(FileAudit.__dataclass_fields__), lineterminator="\n"
        )
        writer.writeheader()
        for audit in audits:
            writer.writerow(asdict(audit))


def validate_audits(audits: Sequence[FileAudit]) -> None:
    fatal_fields = ("key_mismatch_rows", "target_mismatch_rows")
    problems = [
        audit
        for audit in audits
        if any(getattr(audit, field) for field in fatal_fields)
    ]
    if problems:
        raise ValueError(f"Wide-table fatal audit found {len(problems)} problem files")


def build_wide_tables(
    *,
    scored_root: Path,
    scorer_id: str,
    output_dir: Path,
    include_caretaker: bool = True,
    max_children: int | None = None,
) -> dict[str, object]:
    contracts = child_contracts(scored_root)
    if max_children is not None:
        contracts = contracts[:max_children]
    if not contracts:
        raise ValueError(f"No child contracts found under {scored_root}")

    output_dir.mkdir(parents=True, exist_ok=True)
    child_csv = output_dir / "child_direct_surprisal_wide.csv.gz"
    caretaker_csv = output_dir / "caretaker_direct_surprisal_wide.csv.gz"
    audit_csv = output_dir / "source_file_audit.csv"
    manifest_json = output_dir / "manifest.json"
    child_tmp = temporary_path(child_csv)
    caretaker_tmp = temporary_path(caretaker_csv)
    audit_tmp = temporary_path(audit_csv)
    manifest_tmp = temporary_path(manifest_json)
    for path in (child_tmp, caretaker_tmp, audit_tmp, manifest_tmp):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    audits: list[FileAudit] = []
    child_rows = 0
    caretaker_rows = 0
    try:
        with open_csv_output(child_tmp) as handle:
            writer = csv.DictWriter(handle, fieldnames=CHILD_WIDE_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for index, (model_slug, dataset, child) in enumerate(contracts, start=1):
                contract_audits, rows = process_child_contract(
                    scored_root=scored_root,
                    scorer_id=scorer_id,
                    model_slug=model_slug,
                    dataset=dataset,
                    child=child,
                    writer=writer,
                )
                audits.extend(contract_audits)
                child_rows += rows
                print(
                    f"[child {index}/{len(contracts)}] {dataset}/{child}: {rows:,} rows",
                    flush=True,
                )

        if include_caretaker:
            with open_csv_output(caretaker_tmp) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=CARETAKER_WIDE_COLUMNS, lineterminator="\n"
                )
                writer.writeheader()
                for index, (model_slug, dataset, child) in enumerate(contracts, start=1):
                    contract_audits, rows = process_caretaker_contract(
                        scored_root=scored_root,
                        scorer_id=scorer_id,
                        model_slug=model_slug,
                        dataset=dataset,
                        child=child,
                        writer=writer,
                    )
                    audits.extend(contract_audits)
                    caretaker_rows += rows
                    print(
                        f"[caretaker {index}/{len(contracts)}] {dataset}/{child}: {rows:,} rows",
                        flush=True,
                    )

        validate_audits(audits)
        write_file_audit(audits, audit_tmp)
        manifest = {
            "scorer_id": scorer_id,
            "scored_root": str(scored_root),
            "model_slugs": sorted({contract[0] for contract in contracts}),
            "children": len(contracts),
            "datasets": sorted({contract[1] for contract in contracts}),
            "child_rows": child_rows,
            "caretaker_rows": caretaker_rows,
            "child_expected_files": len(contracts) * len(CHILD_MODES) * len(CONTEXTS),
            "caretaker_expected_files": (
                len(contracts) * len(CONTEXTS) if include_caretaker else 0
            ),
            "blank_target_rows": sum(audit.blank_target_rows for audit in audits),
            "missing_sum_bits_rows": sum(audit.missing_sum_bits_rows for audit in audits),
            "zero_eval_token_rows": sum(audit.zero_eval_token_rows for audit in audits),
            "blank_context_rows": sum(audit.blank_context_rows for audit in audits),
            "key_mismatch_rows": sum(audit.key_mismatch_rows for audit in audits),
            "target_mismatch_rows": sum(audit.target_mismatch_rows for audit in audits),
            "child_output": str(child_csv),
            "caretaker_output": str(caretaker_csv) if include_caretaker else "",
            "file_audit": str(audit_csv),
            "context_gain_definition": "sum_bits_k0 - sum_bits_k",
            "candidate_gap_definition": "generated_sum_bits - real_sum_bits",
            "pbm_datasets": sorted(PBM_DATASETS),
        }
        manifest_tmp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        os.replace(child_tmp, child_csv)
        if include_caretaker:
            os.replace(caretaker_tmp, caretaker_csv)
        os.replace(audit_tmp, audit_csv)
        os.replace(manifest_tmp, manifest_json)
    except Exception:
        for path in (child_tmp, caretaker_tmp, audit_tmp, manifest_tmp):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise

    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scored-root", type=Path, required=True)
    parser.add_argument("--scorer-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--no-caretaker", action="store_true")
    parser.add_argument("--max-children", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    manifest = build_wide_tables(
        scored_root=args.scored_root,
        scorer_id=args.scorer_id,
        output_dir=args.output_dir,
        include_caretaker=not args.no_caretaker,
        max_children=args.max_children,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
