#!/usr/bin/env python3
"""Create a real-utterance scoring handoff for heldout child generalization.

The bundle is intentionally real-child only: it packages the best three
non-PBM heldout children for Mistral surprisal scoring without generated
baseline columns as scoring targets. The copied CSVs still preserve all local
metadata and context columns so downstream analysis can use every predictor
available before scoring.
"""

from __future__ import annotations

import argparse
import csv
import json
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_ROOT = (
    PROJECT_ROOT
    / "data"
    / "big_cleaned_dataset"
    / "default_naturalistic_merged_006_023"
    / "preprocessed_data"
)
DEFAULT_BUNDLE_NAME = "heldout_real_child_generalization_2026-06-16"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "results" / "scoring_bundles" / DEFAULT_BUNDLE_NAME
DEFAULT_TAR_GZ = PROJECT_ROOT / "results" / "scoring_bundles" / f"{DEFAULT_BUNDLE_NAME}.tar.gz"

DEFAULT_CHILDREN = (
    ("Forrester", "Ella"),
    ("Sachs", "Naomi"),
    ("MPI-EVA-Manchester", "Helen"),
)

SOURCE_FILENAME = "chi.surprisal_scoring.csv"
REQUIRED_COLUMNS = (
    "dataset",
    "child_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "context_k1",
    "context_k2",
    "context_k3",
    "chi_utterance_clean",
)
PREDICTOR_COLUMNS = (
    "dataset",
    "child_id",
    "source_group",
    "session_id",
    "age_months",
    "file",
    "line_no",
    "utt_id",
    "context_k1",
    "context_k2",
    "context_k3",
    "chi_utterance_clean",
)


@dataclass(frozen=True)
class ChildSpec:
    dataset: str
    child_id: str

    @property
    def key(self) -> str:
        return f"{self.dataset}/{self.child_id}"


@dataclass(frozen=True)
class ChildAudit:
    dataset: str
    child_id: str
    source_csv: str
    output_csv: str
    rows: int
    blank_target_rows: int
    age_min_months: str
    age_max_months: str
    context_k1_nonblank_rows: int
    context_k2_nonblank_rows: int
    context_k3_nonblank_rows: int
    missing_required_columns: tuple[str, ...]

    def as_row(self) -> dict[str, str]:
        return {
            "dataset": self.dataset,
            "child_id": self.child_id,
            "source_csv": self.source_csv,
            "output_csv": self.output_csv,
            "rows": str(self.rows),
            "blank_target_rows": str(self.blank_target_rows),
            "age_min_months": self.age_min_months,
            "age_max_months": self.age_max_months,
            "context_k1_nonblank_rows": str(self.context_k1_nonblank_rows),
            "context_k2_nonblank_rows": str(self.context_k2_nonblank_rows),
            "context_k3_nonblank_rows": str(self.context_k3_nonblank_rows),
            "missing_required_columns": ";".join(self.missing_required_columns),
        }


def parse_child(value: str) -> ChildSpec:
    if "/" not in value:
        raise argparse.ArgumentTypeError("child must be formatted as DATASET/CHILD")
    dataset, child_id = value.split("/", 1)
    dataset = dataset.strip()
    child_id = child_id.strip()
    if not dataset or not child_id:
        raise argparse.ArgumentTypeError("child must be formatted as DATASET/CHILD")
    return ChildSpec(dataset=dataset, child_id=child_id)


def text(value: object) -> str:
    return "" if value is None else str(value).strip()


def source_path(input_root: Path, child: ChildSpec) -> Path:
    return input_root / child.dataset / child.child_id / SOURCE_FILENAME


def output_path(bundle_root: Path, child: ChildSpec) -> Path:
    return bundle_root / "data" / "preprocessed_data" / child.dataset / child.child_id / SOURCE_FILENAME


def audit_source_csv(path: Path, *, child: ChildSpec, output_csv: Path) -> ChildAudit:
    rows = 0
    blank_target_rows = 0
    ages: list[float] = []
    context_counts = {"context_k1": 0, "context_k2": 0, "context_k3": 0}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing = tuple(column for column in REQUIRED_COLUMNS if column not in fieldnames)
        for row in reader:
            rows += 1
            if not text(row.get("chi_utterance_clean")):
                blank_target_rows += 1
            try:
                ages.append(float(text(row.get("age_months"))))
            except ValueError:
                pass
            for context_col in context_counts:
                if text(row.get(context_col)):
                    context_counts[context_col] += 1

    return ChildAudit(
        dataset=child.dataset,
        child_id=child.child_id,
        source_csv=str(path),
        output_csv=str(output_csv),
        rows=rows,
        blank_target_rows=blank_target_rows,
        age_min_months=f"{min(ages):.3f}" if ages else "",
        age_max_months=f"{max(ages):.3f}" if ages else "",
        context_k1_nonblank_rows=context_counts["context_k1"],
        context_k2_nonblank_rows=context_counts["context_k2"],
        context_k3_nonblank_rows=context_counts["context_k3"],
        missing_required_columns=missing,
    )


def copy_csv_with_exact_rows(source: Path, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with source.open(newline="", encoding="utf-8") as in_handle, dest.open(
        "w", newline="", encoding="utf-8"
    ) as out_handle:
        reader = csv.reader(in_handle)
        writer = csv.writer(out_handle, quoting=csv.QUOTE_ALL, lineterminator="\n")
        for i, row in enumerate(reader):
            writer.writerow(row)
            if i > 0:
                row_count += 1
    return row_count


def write_csv(path: Path, rows: Sequence[Mapping[str, str]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def predictor_rows(audits: Sequence[ChildAudit]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for audit in audits:
        total = max(audit.rows, 1)
        rows.append(
            {
                "dataset": audit.dataset,
                "child_id": audit.child_id,
                "available_before_scoring": ",".join(PREDICTOR_COLUMNS),
                "available_after_real_scoring": "sum_bits,mean_bits_per_token,n_eval_tokens plus scorer metadata",
                "not_available_yet": "context_entropy_bits,response_space_entropy,generated_baseline_scores",
                "context_k1_coverage": f"{audit.context_k1_nonblank_rows / total:.6f}",
                "context_k2_coverage": f"{audit.context_k2_nonblank_rows / total:.6f}",
                "context_k3_coverage": f"{audit.context_k3_nonblank_rows / total:.6f}",
            }
        )
    return rows


def expected_task_rows(audits: Sequence[ChildAudit]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for audit in audits:
        for context_label in ("k0", "k1", "k2", "k3"):
            context_col = "" if context_label == "k0" else f"context_{context_label}"
            rows.append(
                {
                    "dataset": audit.dataset,
                    "child_id": audit.child_id,
                    "mode": "real",
                    "context_label": context_label,
                    "context_col": context_col,
                    "input_csv": audit.output_csv,
                    "text_col": "chi_utterance_clean",
                    "expected_rows": str(audit.rows),
                }
            )
    return rows


def write_scoring_script(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """#!/usr/bin/env bash
# Score heldout real-child utterances locally in compute_surprisal_mila.
#
# Run from the compute_surprisal_mila repo root after extracting this bundle:
#   bash cleaned_data_patches/heldout_real_child_generalization_2026-06-16/scripts/score_heldout_real_children_local.sh

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PATCH_NAME="${PATCH_NAME:-$(basename "$PATCH_ROOT")}"
DATA_ROOT="${DATA_ROOT:-$PATCH_ROOT/data/preprocessed_data}"
OUT_ROOT="${OUT_ROOT:-$PROJECT_ROOT/results/raw_surprisal_${PATCH_NAME}}"
MODEL="${MODEL:-mistralai/Mistral-7B-v0.3}"
MODEL_SLUG="${MODEL_SLUG:-mistralai__Mistral-7B-v0.3}"
TASKS_TSV="${TASKS_TSV:-$PROJECT_ROOT/slurm/tasks_${PATCH_NAME}_mistral.tsv}"

BATCH_SIZE="${BATCH_SIZE:-16}"
UNITS="${UNITS:-bits}"
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-auto}"
MAX_LENGTH="${MAX_LENGTH:-}"
OVERWRITE="${OVERWRITE:-0}"
DRY_RUN="${DRY_RUN:-0}"
PYTHON_CMD="${PYTHON_CMD:-}"

cd "$PROJECT_ROOT"
mkdir -p "$(dirname "$TASKS_TSV")" "$OUT_ROOT"

if [[ ! -d "$DATA_ROOT" ]]; then
  echo "[ERROR] DATA_ROOT not found: $DATA_ROOT" >&2
  echo "        Extract the heldout bundle under cleaned_data_patches/ first." >&2
  exit 2
fi

if [[ -n "$PYTHON_CMD" ]]; then
  read -r -a PYTHON_RUN <<< "$PYTHON_CMD"
elif command -v uv >/dev/null 2>&1; then
  PYTHON_RUN=(uv run python)
elif [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_RUN=("$PROJECT_ROOT/.venv/bin/python")
else
  PYTHON_RUN=(python3)
fi

"${PYTHON_RUN[@]}" src/build_cleaned_scoring_manifest.py \\
  --data-root "$DATA_ROOT" \\
  --output-root "$OUT_ROOT" \\
  --manifest "$TASKS_TSV" \\
  --model-slug "$MODEL_SLUG" \\
  --bin 6 \\
  --modes real \\
  --context-cols context_k1,context_k2,context_k3 \\
  --strict-context-col \\
  --missing-policy error

task_count="$(awk -F'\\t' 'NR > 1 {n++} END {print n + 0}' "$TASKS_TSV")"
if [[ "$task_count" -ne 12 ]]; then
  echo "[ERROR] Expected 12 heldout real-child tasks, got $task_count from $TASKS_TSV" >&2
  exit 2
fi

echo "[INFO] Built $task_count heldout real-child tasks at $TASKS_TSV"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "[OK] DRY_RUN=1, manifest built without scoring."
  exit 0
fi

tail -n +2 "$TASKS_TSV" | while IFS=$'\\t' read -r task_id mode corpus child input_csv text_col context_col output_csv; do
  echo "[INFO] task=$task_id corpus=$corpus child=$child context=${context_col:-k0} output=$output_csv"
  if [[ -f "$output_csv" && "$OVERWRITE" != "1" ]]; then
    echo "[SKIP] exists: $output_csv"
    continue
  fi

  cmd=("${PYTHON_RUN[@]}" src/new_score_utterances.py
    --input "$input_csv"
    --output "$output_csv"
    --model "$MODEL"
    --units "$UNITS"
    --batch-size "$BATCH_SIZE"
    --device "$DEVICE"
    --dtype "$DTYPE"
    --text-col "$text_col"
    --add-metadata
    --score-zero-counts
  )
  if [[ "$OVERWRITE" == "1" ]]; then
    cmd+=(--overwrite)
  fi
  if [[ -n "$MAX_LENGTH" ]]; then
    cmd+=(--max-length "$MAX_LENGTH")
  fi
  if [[ -n "$context_col" ]]; then
    cmd+=(--context-col "$context_col" --strict-context-col)
  fi

  "${cmd[@]}"
done

echo "[OK] Heldout real-child scores written under $OUT_ROOT"
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def write_score_audit_script(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """#!/usr/bin/env python3
\"\"\"Audit heldout real-child scored outputs after local PC scoring.\"\"\"

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def count_rows(path: Path) -> tuple[int, int, int]:
    rows = 0
    finite_sum_bits = 0
    positive_tokens = 0
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            try:
                float(row.get('sum_bits', ''))
                finite_sum_bits += 1
            except ValueError:
                pass
            try:
                if int(float(row.get('n_eval_tokens', '0'))) > 0:
                    positive_tokens += 1
            except ValueError:
                pass
    return rows, finite_sum_bits, positive_tokens


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-root', type=Path, required=True)
    parser.add_argument('--expected-files', type=int, default=12)
    args = parser.parse_args()

    files = sorted(args.out_root.rglob('*.scored.csv'))
    print(f'[INFO] scored_files={len(files)} expected={args.expected_files}')
    if len(files) != args.expected_files:
        raise SystemExit(2)
    total_rows = 0
    total_finite = 0
    total_positive = 0
    for path in files:
        rows, finite, positive = count_rows(path)
        total_rows += rows
        total_finite += finite
        total_positive += positive
        print(f'{path}\\trows={rows}\\tfinite_sum_bits={finite}\\tpositive_tokens={positive}')
    print(f'[OK] total_rows={total_rows} finite_sum_bits={total_finite} positive_tokens={total_positive}')


if __name__ == '__main__':
    main()
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def write_readme(path: Path, *, bundle_name: str, audits: Sequence[ChildAudit]) -> None:
    total_rows = sum(audit.rows for audit in audits)
    table = "\n".join(
        f"- {audit.dataset}/{audit.child_id}: {audit.rows:,} rows, ages "
        f"{audit.age_min_months}-{audit.age_max_months} months"
        for audit in audits
    )
    path.write_text(
        f"""# Heldout Real-Child Generalization Scoring Bundle

Bundle: `{bundle_name}`

This bundle stages real-child utterance scoring for the three best non-PBM
heldout children:

{table}

Total real child rows: {total_rows:,}

Scoring target:

```text
mode: real
text column: chi_utterance_clean
contexts: k0, k1, k2, k3
expected whole-CSV tasks: 12
```

This bundle deliberately does not ask the scorer to score random/unigram/bigram,
trigram, or LSTM generated baselines. The immediate scientific question is
whether PBM-trained real-child Route 1 models generalize to unseen real
children.

Available before scoring: age/session/file metadata, real target text, and
caretaker context text columns `context_k1`, `context_k2`, and `context_k3`.

Not available until separate feature work: context entropy, response-space
entropy, and generated-baseline scores for these children.
""",
        encoding="utf-8",
    )


def write_pc_prompt(path: Path, *, bundle_name: str, tar_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Laptop-Orchestrated Prompt: Score Heldout Real Children On The PC

You are starting from the laptop repository:

```text
/home/apaixonada/EvaPortelance/Projet_1/communicative_efficiency
```

The GPU/scoring machine is reachable over SSH:

```text
alkan@192.168.7.217
```

The scoring repository on the PC is:

```text
/home/alkan/Portelance/compute_surprisal_mila
```

Goal: score real utterances only for the heldout children
`Forrester/Ella`, `Sachs/Naomi`, and `MPI-EVA-Manchester/Helen`.

Do not generate or score random/unigram/bigram/trigram/LSTM baselines in this
task. This is the out-of-child generalization scoring pass.

## First: Sync Code And Bundle

From the laptop, make sure the local communicative-efficiency commit containing
this handoff is pushed, then pull it on the PC. Preserve PC worktree edits;
do not reset or clean:

```bash
git status --short
git push origin main
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/communicative_efficiency && git pull --autostash --ff-only origin main'
```

Also pull the scorer repo on the PC if possible. If this fails due to conflicts,
stop and report the conflict; do not overwrite PC edits:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && git pull --autostash --ff-only origin main'
```

Sync the already-built bundle and this prompt to the scorer repo:

```bash
rsync -avhP \\
  results/scoring_bundles/{tar_name} \\
  docs/heldout_real_child_generalization_pc_scoring_prompt.md \\
  alkan@192.168.7.217:/home/alkan/Portelance/compute_surprisal_mila/new_data/
```

## Remote Dry Run

From the laptop, run the scorer-side dry run over SSH:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && mkdir -p cleaned_data_patches && tar -xzf new_data/{tar_name} -C cleaned_data_patches && DRY_RUN=1 bash cleaned_data_patches/{bundle_name}/scripts/score_heldout_real_children_local.sh'
```

The dry run must report exactly 12 tasks:

```text
3 children x 1 real mode x 4 contexts = 12 tasks
```

## Launch In Background

Launch from the laptop by starting the PC job over SSH:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && mkdir -p results/raw_surprisal_{bundle_name}/logs && nohup env MODEL=mistralai/Mistral-7B-v0.3 DEVICE=cuda DTYPE=auto BATCH_SIZE=16 bash cleaned_data_patches/{bundle_name}/scripts/score_heldout_real_children_local.sh > results/raw_surprisal_{bundle_name}/logs/score_heldout_real_children.log 2>&1 < /dev/null & echo $! > results/raw_surprisal_{bundle_name}/logs/score_heldout_real_children.pid && cat results/raw_surprisal_{bundle_name}/logs/score_heldout_real_children.pid'
```

After launching, stop monitoring continuously. Give the user these status
commands, which are also run from the laptop:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && cat results/raw_surprisal_{bundle_name}/logs/score_heldout_real_children.pid'
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && tail -n 80 results/raw_surprisal_{bundle_name}/logs/score_heldout_real_children.log'
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && find results/raw_surprisal_{bundle_name} -name "*.scored.csv" | wc -l'
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && find results/raw_surprisal_{bundle_name} -name "*.scored.csv" -printf "%TY-%Tm-%Td %TH:%TM %s %p\\n" | sort'
```

Expected completed scored files: 12.

## Completion Audit

When the background run finishes, run the audit over SSH from the laptop:

```bash
ssh alkan@192.168.7.217 'cd /home/alkan/Portelance/compute_surprisal_mila && .venv/bin/python cleaned_data_patches/{bundle_name}/scripts/audit_heldout_real_child_scores.py --out-root results/raw_surprisal_{bundle_name} --expected-files 12'
```

Do not claim the scoring is complete unless the audit passes.
""",
        encoding="utf-8",
    )


def create_tarball(bundle_root: Path, tar_path: Path) -> None:
    tar_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(bundle_root, arcname=bundle_root.name)


def create_bundle(
    *,
    input_root: Path,
    output_root: Path,
    tar_gz: Path,
    children: Sequence[ChildSpec],
) -> list[ChildAudit]:
    output_root.mkdir(parents=True, exist_ok=True)
    audits: list[ChildAudit] = []

    for child in children:
        src = source_path(input_root, child)
        dest = output_path(output_root, child)
        if not src.is_file():
            raise FileNotFoundError(f"Missing source scoring CSV for {child.key}: {src}")
        copied_rows = copy_csv_with_exact_rows(src, dest)
        audit = audit_source_csv(src, child=child, output_csv=dest)
        if copied_rows != audit.rows:
            raise RuntimeError(f"Copied row count mismatch for {child.key}: {copied_rows} != {audit.rows}")
        if audit.missing_required_columns:
            missing = ", ".join(audit.missing_required_columns)
            raise RuntimeError(f"{src} missing required columns: {missing}")
        if audit.blank_target_rows:
            raise RuntimeError(f"{src} has {audit.blank_target_rows} blank target rows")
        audits.append(audit)

    metadata_dir = output_root / "metadata"
    write_csv(
        metadata_dir / "heldout_real_child_manifest.csv",
        [audit.as_row() for audit in audits],
        fieldnames=tuple(audits[0].as_row().keys()) if audits else (),
    )
    write_csv(
        metadata_dir / "predictor_availability.csv",
        predictor_rows(audits),
        fieldnames=(
            "dataset",
            "child_id",
            "available_before_scoring",
            "available_after_real_scoring",
            "not_available_yet",
            "context_k1_coverage",
            "context_k2_coverage",
            "context_k3_coverage",
        ),
    )
    write_csv(
        metadata_dir / "expected_scoring_tasks.csv",
        expected_task_rows(audits),
        fieldnames=(
            "dataset",
            "child_id",
            "mode",
            "context_label",
            "context_col",
            "input_csv",
            "text_col",
            "expected_rows",
        ),
    )
    (metadata_dir / "bundle_summary.json").write_text(
        json.dumps(
            {
                "bundle_name": output_root.name,
                "children": [f"{audit.dataset}/{audit.child_id}" for audit in audits],
                "total_rows": sum(audit.rows for audit in audits),
                "expected_tasks": len(audits) * 4,
                "mode": "real",
                "contexts": ["k0", "k1", "k2", "k3"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    write_scoring_script(output_root / "scripts" / "score_heldout_real_children_local.sh")
    write_score_audit_script(output_root / "scripts" / "audit_heldout_real_child_scores.py")
    write_readme(output_root / "README.md", bundle_name=output_root.name, audits=audits)
    write_pc_prompt(
        PROJECT_ROOT / "docs" / "heldout_real_child_generalization_pc_scoring_prompt.md",
        bundle_name=output_root.name,
        tar_name=tar_gz.name,
    )
    create_tarball(output_root, tar_gz)
    return audits


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--tar-gz", type=Path, default=DEFAULT_TAR_GZ)
    parser.add_argument(
        "--child",
        action="append",
        type=parse_child,
        help="Heldout child formatted DATASET/CHILD. Defaults to Ella, Naomi, Helen.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    children = tuple(args.child) if args.child else tuple(ChildSpec(*child) for child in DEFAULT_CHILDREN)
    audits = create_bundle(
        input_root=args.input_root,
        output_root=args.output_root,
        tar_gz=args.tar_gz,
        children=children,
    )
    print(f"[OK] wrote bundle directory: {args.output_root}")
    print(f"[OK] wrote tarball: {args.tar_gz}")
    print(f"[OK] wrote PC prompt: {PROJECT_ROOT / 'docs' / 'heldout_real_child_generalization_pc_scoring_prompt.md'}")
    print(f"[OK] children={len(audits)} rows={sum(audit.rows for audit in audits)} expected_tasks={len(audits) * 4}")


if __name__ == "__main__":
    main()
