from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.run_scorer_performance_comparison_portable import (
    CAREGIVER_FILES,
    CHILD_PRODUCTS,
    HISTORICAL_FILES,
    _refuse_storage_write_through,
    create_local_link,
    resolve_inputs,
    restore_completed_products,
)


class PortableScorerComparisonTests(unittest.TestCase):
    def _link_fixture(self, root: Path) -> Path:
        link_root = root / "clone/results/external/portable_t7"
        for _, product in CHILD_PRODUCTS:
            (link_root / product).mkdir(parents=True)
        caregiver = link_root / "downstream_caregiver_response/datasets"
        caregiver.mkdir(parents=True)
        for _, filename in CAREGIVER_FILES:
            (caregiver / filename).write_text("fixture\n", encoding="utf-8")
        historical = link_root / "scorer_performance_historical_sources"
        historical.mkdir(parents=True)
        for filename in HISTORICAL_FILES:
            (historical / filename).write_text("fixture\n", encoding="utf-8")
        (link_root / "scorer_performance_comparison").mkdir()
        (link_root / "scorer_performance_figures").mkdir()
        return link_root

    def test_resolves_all_inputs_from_logical_product_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            link_root = self._link_fixture(Path(temporary))
            child, caregiver, historical = resolve_inputs(link_root)
            self.assertEqual([item.label for item in child], [item[0] for item in CHILD_PRODUCTS])
            self.assertEqual([item.label for item in caregiver], [item[0] for item in CHILD_PRODUCTS])
            self.assertEqual([path.name for path in historical], list(HISTORICAL_FILES))

    def test_restore_creates_relative_links_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            link_root = self._link_fixture(root)
            output = root / "clone/results/comparison"
            figures = root / "clone/figs/comparison"
            self.assertEqual(
                restore_completed_products(link_root, output, figures),
                {"analysis": "created", "figures": "created"},
            )
            self.assertTrue(output.is_symlink())
            self.assertFalse(output.readlink().is_absolute())
            self.assertEqual(
                restore_completed_products(link_root, output, figures),
                {"analysis": "already-linked", "figures": "already-linked"},
            )

    def test_restore_never_replaces_existing_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            destination.mkdir()
            with self.assertRaisesRegex(FileExistsError, "refusing to replace"):
                create_local_link(source, destination)

    def test_restore_validates_both_destinations_before_creating_either(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            link_root = self._link_fixture(root)
            output = root / "clone/results/comparison"
            figures = root / "clone/figs/comparison"
            figures.mkdir(parents=True)
            with self.assertRaisesRegex(FileExistsError, "refusing to replace"):
                restore_completed_products(link_root, output, figures)
            self.assertFalse(output.exists())

    def test_run_guard_rejects_descendant_of_portable_product(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            storage_product = root / "storage/product"
            storage_product.mkdir(parents=True)
            link_root = root / "clone/results/external/portable_t7"
            link_root.mkdir(parents=True)
            (link_root / "product").symlink_to(storage_product, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "inside portable storage product"):
                _refuse_storage_write_through(
                    link_root / "product/new_run",
                    link_root,
                )


if __name__ == "__main__":
    unittest.main()
