"""Tests for the no-model V26 runtime-surface audit.

State slice: astral-causal-channel-separation-v26-runtime-adapter-preflight.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "runtime_surface_v26.py"
SPEC = importlib.util.spec_from_file_location("runtime_surface_v26", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RuntimeSurfaceV26Tests(unittest.TestCase):
    def test_public_final_embedding_surface_is_not_enough(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            header = Path(directory) / "llama.h"
            header.write_text(
                "llama_decode llama_get_embeddings llama_set_adapter_cvec",
                encoding="utf-8",
            )
            result = MODULE.inspect_header(header)
            self.assertEqual(result["classification"], MODULE.INSUFFICIENT)
            self.assertIn("no_public_per_layer_residual_capture", result["reasons"])

    def test_missing_public_control_surface_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            header = Path(directory) / "llama.h"
            header.write_text("llama_decode", encoding="utf-8")
            result = MODULE.inspect_header(header)
            self.assertEqual(result["classification"], MODULE.INSUFFICIENT)
            self.assertTrue(any(reason.startswith("missing_public_symbols:") for reason in result["reasons"]))

    def test_complete_synthetic_surface_is_candidate_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            header = Path(directory) / "llama.h"
            header.write_text(
                "llama_decode llama_get_embeddings llama_set_adapter_cvec "
                "llama_get_hidden_state_layer",
                encoding="utf-8",
            )
            result = MODULE.inspect_header(header)
            self.assertEqual(result["classification"], MODULE.READY)
            self.assertFalse(result["model_execution"])


if __name__ == "__main__":
    unittest.main()
