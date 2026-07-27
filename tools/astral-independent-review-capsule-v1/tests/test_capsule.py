from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "capsule.py"
SPEC = importlib.util.spec_from_file_location("astral_review_capsule", MODULE_PATH)
CAPSULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(CAPSULE)


class CapsuleTests(unittest.TestCase):
    def test_manifest_round_trip_and_mutation_rejection(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "nested").mkdir()
            (root / "a.txt").write_text("alpha\n")
            (root / "nested/b.txt").write_text("beta\n")
            identity = CAPSULE.write_manifest(root, "MANIFEST.sha256")
            state = CAPSULE.verify_manifest(root, "MANIFEST.sha256")
            self.assertEqual(identity, state["identity"])
            self.assertEqual(2, state["file_count"])
            (root / "nested/b.txt").write_text("changed\n")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                CAPSULE.verify_manifest(root, "MANIFEST.sha256")

    def test_manifest_rejects_extra_file_and_symlink(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "a.txt").write_text("alpha\n")
            CAPSULE.write_manifest(root, "MANIFEST.sha256")
            (root / "extra.txt").write_text("extra\n")
            with self.assertRaisesRegex(ValueError, "census mismatch"):
                CAPSULE.verify_manifest(root, "MANIFEST.sha256")
            (root / "extra.txt").unlink()
            (root / "link.txt").symlink_to(root / "a.txt")
            with self.assertRaisesRegex(ValueError, "symlink forbidden"):
                CAPSULE.verify_manifest(root, "MANIFEST.sha256")

    def test_manifest_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "a.txt").write_text("alpha\n")
            manifest = root / "MANIFEST.sha256"
            manifest.write_text(f"{CAPSULE.sha256(root / 'a.txt')}  ../a.txt\n")
            with self.assertRaisesRegex(ValueError, "invalid manifest row"):
                CAPSULE.verify_manifest(root, manifest.name)

    def test_runtime_differences_are_explicit(self):
        expected = {
            "python": "3.14.5",
            "python_executable_name": "python",
            "platform": "author-os",
            "machine": "arm64",
            "processor": "arm",
            "packages": {"numpy": "2.4.5"},
            "commands": {"git": "git version author"},
        }
        actual = {
            **expected,
            "platform": "reviewer-os",
            "packages": {"numpy": "2.4.6"},
        }
        differences = CAPSULE.runtime_differences(expected, actual)
        self.assertEqual(
            ["platform", "packages.numpy"],
            [difference["field"] for difference in differences],
        )


if __name__ == "__main__":
    unittest.main()
