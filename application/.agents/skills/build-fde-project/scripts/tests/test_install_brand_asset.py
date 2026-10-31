from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "install_brand_asset.py"
SPEC = importlib.util.spec_from_file_location("install_brand_asset", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InstallBrandAssetTests(unittest.TestCase):
    def test_installs_into_a_new_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "BrandNewProject"
            state, destination = MODULE.install_logo(
                root, "frontend/public/brand/ff-logo.png"
            )
            self.assertEqual("installed", state)
            self.assertEqual(MODULE.EXPECTED_SHA256, MODULE.sha256(destination))

    def test_installs_and_reuses_exact_logo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state, destination = MODULE.install_logo(
                root, "frontend/public/brand/ff-logo.png"
            )
            self.assertEqual("installed", state)
            self.assertEqual(MODULE.EXPECTED_SHA256, MODULE.sha256(destination))

            state, _ = MODULE.install_logo(
                root, "frontend/public/brand/ff-logo.png"
            )
            self.assertEqual("unchanged", state)

    def test_refuses_overwrite_and_paths_outside_frontend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            destination = root / "frontend/public/brand/ff-logo.png"
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"different")

            with self.assertRaises(FileExistsError):
                MODULE.install_logo(root, "frontend/public/brand/ff-logo.png")
            with self.assertRaises(ValueError):
                MODULE.install_logo(root, "docs/assets/brand/ff-logo.png")


if __name__ == "__main__":
    unittest.main()
