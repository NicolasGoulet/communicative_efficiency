from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from src.import_downstream_caregiver_response_scores import (
    SCHEMA,
    _safe_members,
    audit_archive,
    sha256_bytes,
    sha256_path,
)


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    member = tarfile.TarInfo(name)
    member.size = len(data)
    archive.addfile(member, io.BytesIO(data))


class DownstreamScoreImportTests(unittest.TestCase):
    def test_minimal_archive_passes_hash_contract_and_schema_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "scores.tar.gz"
            target_hash = "a" * 64
            context_hash = "b" * 64
            source_hash = "c" * 64
            header = (
                "source_row,utterance_id,target_text,score_status,context_available,"
                "utterance_sum_bits,model_key,scoring_code_revision\n"
            )
            score_bytes = gzip.compress(
                (header + "0,p1,hello,scored,True,2.5,test-model,revision\n").encode()
            )
            summary = {
                "status": "COMPLETE",
                "schema_version": SCHEMA,
                "scope": "downstream_caregiver_response_v1",
                "model_key": "test-model",
                "contract_id": 0,
                "context_window": "k0",
                "source_sha256": source_hash,
                "target_text_sha256": target_hash,
                "context_text_sha256": context_hash,
                "source_rows": 1,
                "utterance_rows": 1,
                "word_level": False,
                "artifacts": {
                    "utterances.csv.gz": {
                        "bytes": len(score_bytes),
                        "sha256": sha256_bytes(score_bytes),
                    }
                },
            }
            summary_bytes = (json.dumps(summary) + "\n").encode()
            manifest = (
                "contract_id\tscope\tmodel_key\tchild_key\tcorpus\tchild\tmode\t"
                "context_window\tinput_csv\ttext_col\tcontext_col\toutput_relpath\t"
                "source_rows\tnonempty_target_rows\tcontext_available_rows\t"
                "expected_word_rows\tsource_sha256\ttarget_text_sha256\tcontext_text_sha256\n"
                f"0\tdownstream_caregiver_response_v1\ttest-model\tD\tD\tall\tcaregiver_response\t"
                f"k0\tin.csv\ttarget_text\t\tD/unconditional/caregiver_response_surprisal\t"
                f"1\t1\t1\t0\t{source_hash}\t{target_hash}\t{context_hash}\n"
            ).encode()
            completion = {
                "status": "PASS",
                "model_key": "test-model",
                "scope": "downstream_caregiver_response_v1",
                "contracts": 1,
                "audited_contracts": 1,
                "utterance_rows": 1,
                "problem_count": 0,
                "word_level": False,
                "scoring_code_revision": "revision",
            }
            base = "outputs/D/unconditional/caregiver_response_surprisal"
            with tarfile.open(archive_path, "w:gz") as archive:
                add_bytes(archive, "SURPRISAL_COMPLETE", b"PASS\n")
                add_bytes(archive, "manifests/word_output_contracts.tsv", manifest)
                add_bytes(
                    archive,
                    "reports/completion/audit_report.json",
                    json.dumps(completion).encode(),
                )
                add_bytes(archive, f"{base}/contract_summary.json", summary_bytes)
                add_bytes(
                    archive,
                    f"{base}/CONTRACT_COMPLETE",
                    f"{SCHEMA}\n{sha256_bytes(summary_bytes)}\n".encode(),
                )
                add_bytes(archive, f"{base}/utterances.csv.gz", score_bytes)
            spec = {
                "scorer_key": "test-model",
                "archive_bytes": archive_path.stat().st_size,
                "archive_sha256": sha256_path(archive_path),
            }
            config = {
                "expected_contracts": 1,
                "expected_datasets": 1,
                "expected_conditions": ["k0"],
                "expected_utterance_rows": 1,
                "scoring_code_revision": "revision",
            }
            report = audit_archive(archive_path, spec=spec, config=config)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["contracts"], 1)

    def test_symlink_member_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unsafe.tar.gz"
            with tarfile.open(path, "w:gz") as archive:
                member = tarfile.TarInfo("escape")
                member.type = tarfile.SYMTYPE
                member.linkname = "../../outside"
                archive.addfile(member)
            with tarfile.open(path, "r:gz") as archive:
                with self.assertRaisesRegex(ValueError, "unsafe archive member"):
                    _safe_members(archive)


if __name__ == "__main__":
    unittest.main()
