from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.audit_portable_project_storage import audit_storage


class PortableStorageAuditTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path]:
        storage = root / "storage"
        product = storage / "brain" / "products" / "dyadic"
        product.mkdir(parents=True)
        payload = product / "audit.json"
        payload.write_text('{"status":"PASS","counts":{"rows":3}}\n', encoding="utf-8")
        marker = product / "COMPLETE"
        marker.write_text("complete\n", encoding="utf-8")
        manifest = root / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "products": [
                        {
                            "name": "dyadic",
                            "repository": "brain",
                            "relative_path": "products/dyadic",
                            "required_files": [
                                {
                                    "path": "COMPLETE",
                                    "bytes": marker.stat().st_size,
                                    "sha256": hashlib.sha256(marker.read_bytes()).hexdigest(),
                                }
                            ],
                            "json_checks": [
                                {"path": "audit.json", "key": "status", "expected": "PASS"},
                                {"path": "audit.json", "key": "counts.rows", "expected": 3},
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return storage, manifest

    def test_audit_and_link_farm_pass_without_writing_storage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            storage, manifest = self._fixture(root)
            before = sorted(path.relative_to(storage) for path in storage.rglob("*"))
            audit = audit_storage(
                storage_root=storage,
                manifest_path=manifest,
                link_root=root / "links",
                audit_path=root / "audit.json",
                create_links=True,
            )
            self.assertEqual(audit["status"], "PASS")
            self.assertTrue((root / "links/dyadic").is_symlink())
            self.assertEqual(before, sorted(path.relative_to(storage) for path in storage.rglob("*")))

    def test_missing_or_changed_product_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            storage, manifest = self._fixture(root)
            (storage / "brain/products/dyadic/COMPLETE").write_text("changed\n", encoding="utf-8")
            audit = audit_storage(
                storage_root=storage,
                manifest_path=manifest,
                link_root=root / "links",
                audit_path=root / "audit.json",
                create_links=True,
            )
            self.assertEqual(audit["status"], "FAIL")
            self.assertFalse((root / "links/dyadic").exists())
            self.assertTrue(any("SHA-256 mismatch" in problem for problem in audit["problems"]))

    def test_existing_nonlink_is_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            storage, manifest = self._fixture(root)
            collision = root / "links/dyadic"
            collision.mkdir(parents=True)
            with self.assertRaisesRegex(FileExistsError, "refusing to replace"):
                audit_storage(
                    storage_root=storage,
                    manifest_path=manifest,
                    link_root=root / "links",
                    audit_path=root / "audit.json",
                    create_links=True,
                )


if __name__ == "__main__":
    unittest.main()
