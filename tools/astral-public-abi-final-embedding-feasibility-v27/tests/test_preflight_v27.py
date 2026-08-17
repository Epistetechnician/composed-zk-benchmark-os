"""Hermetic tests for V27's no-model public-ABI preflight.

State slice: astral-public-abi-final-embedding-feasibility-v27-preflight.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "preflight_v27.py"
SPEC = importlib.util.spec_from_file_location("preflight_v27", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class V27PreflightTests(unittest.TestCase):
    def test_complete_header_but_missing_library_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = root / "llama.h"
            header.write_text(" ".join(MODULE.REQUIRED_SYMBOLS), encoding="utf-8")
            actor = root / "actor.gguf"
            actor.write_bytes(b"synthetic-actor")
            result = MODULE.preflight(header, root / "missing.dylib", actor)
            self.assertEqual(result["classification"], MODULE.STOP)
            self.assertIn("library_missing", result["reasons"])
            self.assertFalse(result["model_execution"])

    def test_missing_header_declaration_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = root / "llama.h"
            header.write_text("llama_decode", encoding="utf-8")
            library = root / "libllama.dylib"
            library.write_bytes(b"not-a-library")
            actor = root / "actor.gguf"
            actor.write_bytes(b"synthetic-actor")
            result = MODULE.preflight(header, library, actor)
            self.assertTrue(any(reason.startswith("header_missing_symbols:") for reason in result["reasons"]))

    def test_symlink_actor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.gguf"
            target.write_bytes(b"synthetic-actor")
            actor = root / "actor.gguf"
            actor.symlink_to(target)
            result = MODULE.preflight(root / "missing.h", root / "missing.dylib", actor)
            self.assertIn("actor_not_regular_local_file", result["reasons"])


if __name__ == "__main__":
    unittest.main()
