import tempfile
import unittest
import zipfile
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from install_childes_training_expansion_archives import (  # noqa: E402
    extract_chat_archive,
    install_datasets,
    selected_chat_members,
)


class TestInstallChildesTrainingExpansionArchives(unittest.TestCase):
    def test_selects_only_requested_corpus_chat_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "Howe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("Eng-UK/Howe/barry1.cha", "@Begin\n")
                archive.writestr("Eng-UK/Other/other.cha", "@Begin\n")
                archive.writestr("Eng-UK/Howe/readme.txt", "metadata")
            with zipfile.ZipFile(archive_path) as archive:
                selected = selected_chat_members(archive, "Howe")
        self.assertEqual([(info.filename, str(relative)) for info, relative in selected], [("Eng-UK/Howe/barry1.cha", "barry1.cha")])

    def test_extract_refuses_to_overwrite_existing_raw_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "Howe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("Howe/barry1.cha", "@Begin\n")
            existing = root / "raw" / "Howe"
            existing.mkdir(parents=True)
            (existing / "old.cha").write_text("@Begin\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                extract_chat_archive(archive_path, "Howe", root / "raw")

    def test_installer_passes_shared_prepared_root_to_dataset_preprocessor(self):
        # The integration contract is data/preprocessed_data/<Dataset>/<Child>,
        # not data/preprocessed_data/<Dataset>/<Dataset>/<Child>.
        import install_childes_training_expansion_archives as installer

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_dir = root / "archives"
            archive_dir.mkdir()
            archive_path = archive_dir / "Thomas.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("010100.cha", "@Begin\n")
            received = []
            original = installer.process_dataset

            def fake_process(dataset, output_root, **_kwargs):
                received.append((dataset, output_root))
                return {"children": 1, "rows": 1}

            installer.process_dataset = fake_process
            try:
                install_datasets(
                    ["Thomas"],
                    archive_dirs=[archive_dir],
                    raw_root=root / "raw",
                    prepared_root=root / "prepared",
                    audit_path=root / "audit.csv",
                )
            finally:
                installer.process_dataset = original

        self.assertEqual(received, [("Thomas", root / "prepared")])


if __name__ == "__main__":
    unittest.main()
