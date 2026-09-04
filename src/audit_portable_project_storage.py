#!/usr/bin/env python3
"""Validate and expose immutable project products on relocatable storage.

The link farm created by this module lives below ``results/external`` and is
therefore an input view, not an analysis output location. Existing paths are
never replaced, and the storage tree is never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "configs/portable_storage_products.json"
DEFAULT_LINK_ROOT = ROOT / "results/external/portable_t7"
DEFAULT_AUDIT = DEFAULT_LINK_ROOT / "portable_storage_audit.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def nested_value(payload: Any, dotted_key: str) -> Any:
    value = payload
    for component in dotted_key.split("."):
        if not isinstance(value, dict) or component not in value:
            raise KeyError(dotted_key)
        value = value[component]
    return value


def safe_relative(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"{label} must be a nonempty relative path: {value!r}")
    return path


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("unsupported portable-storage manifest schema")
    products = payload.get("products")
    if not isinstance(products, list) or not products:
        raise ValueError("portable-storage manifest has no products")
    names = [str(product.get("name", "")) for product in products]
    if any(not name for name in names) or len(names) != len(set(names)):
        raise ValueError("portable-storage product names must be unique and nonempty")
    return payload


def validate_product(storage_root: Path, product: dict[str, Any]) -> dict[str, Any]:
    name = str(product["name"])
    repository = safe_relative(str(product["repository"]), f"{name}.repository")
    relative = safe_relative(str(product["relative_path"]), f"{name}.relative_path")
    source = storage_root / repository / relative
    problems: list[str] = []
    checks: list[dict[str, Any]] = []

    if not source.is_dir():
        problems.append(f"missing product directory: {source}")
    for specification in product.get("required_files", []):
        child = safe_relative(str(specification["path"]), f"{name}.required_file")
        path = source / child
        check: dict[str, Any] = {"path": str(child), "exists": path.is_file()}
        if not path.is_file():
            problems.append(f"missing required file: {path}")
        else:
            observed_bytes = path.stat().st_size
            check["bytes"] = observed_bytes
            expected_bytes = specification.get("bytes")
            if expected_bytes is not None and observed_bytes != int(expected_bytes):
                problems.append(
                    f"size mismatch for {path}: expected {expected_bytes}, observed {observed_bytes}"
                )
            expected_hash = specification.get("sha256")
            if expected_hash:
                observed_hash = sha256_file(path)
                check["sha256"] = observed_hash
                if observed_hash != expected_hash:
                    problems.append(
                        f"SHA-256 mismatch for {path}: expected {expected_hash}, observed {observed_hash}"
                    )
        checks.append(check)

    for specification in product.get("json_checks", []):
        child = safe_relative(str(specification["path"]), f"{name}.json_check")
        path = source / child
        dotted_key = str(specification["key"])
        expected = specification.get("expected")
        observed: Any = None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            observed = nested_value(payload, dotted_key)
            if observed != expected:
                problems.append(
                    f"JSON mismatch for {path}:{dotted_key}: expected {expected!r}, observed {observed!r}"
                )
        except (OSError, json.JSONDecodeError, KeyError) as error:
            problems.append(f"cannot verify JSON check {path}:{dotted_key}: {error}")
        checks.append(
            {"path": str(child), "json_key": dotted_key, "expected": expected, "observed": observed}
        )

    return {
        "name": name,
        "repository": str(repository),
        "relative_path": str(relative),
        "source": str(source),
        "status": "PASS" if not problems else "FAIL",
        "checks": checks,
        "problems": problems,
    }


def create_link(link_root: Path, result: dict[str, Any]) -> str:
    source = Path(result["source"])
    destination = link_root / result["name"]
    link_root.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        if destination.resolve() != source.resolve():
            raise FileExistsError(f"existing symlink targets another product: {destination}")
        return "existing"
    if destination.exists():
        raise FileExistsError(f"refusing to replace existing path: {destination}")
    destination.symlink_to(source, target_is_directory=True)
    return "created"


def atomic_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def audit_storage(
    *,
    storage_root: Path,
    manifest_path: Path = DEFAULT_MANIFEST,
    link_root: Path = DEFAULT_LINK_ROOT,
    audit_path: Path = DEFAULT_AUDIT,
    create_links: bool = False,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    results = [validate_product(storage_root, product) for product in manifest["products"]]
    problems = [problem for result in results for problem in result["problems"]]
    if create_links and not problems:
        for result in results:
            result["link"] = str(link_root / result["name"])
            result["link_action"] = create_link(link_root, result)
    audit = {
        "schema_version": "1.0.0",
        "status": "PASS" if not problems else "FAIL",
        "storage_root": str(storage_root),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "link_root": str(link_root),
        "links_requested": create_links,
        "product_count": len(results),
        "products": results,
        "problems": problems,
    }
    atomic_json(audit, audit_path)
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--storage-root",
        type=Path,
        default=os.environ.get("EFF_COMM_STORAGE_ROOT"),
        required="EFF_COMM_STORAGE_ROOT" not in os.environ,
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--link-root", type=Path, default=DEFAULT_LINK_ROOT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--create-links", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = audit_storage(
        storage_root=args.storage_root,
        manifest_path=args.manifest,
        link_root=args.link_root,
        audit_path=args.audit,
        create_links=args.create_links,
    )
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
