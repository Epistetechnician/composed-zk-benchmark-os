"""Hermetic Gutenberg-custody validator tests for V41.

State slice: astral-stage0c-qwen36-directional-block-target-v41.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_module(
    "astral_stage0c_qwen36_gutenberg_validator_v41",
    "validate_gutenberg_corpus_v41.py",
)


class CorpusValidatorV41Tests(unittest.TestCase):
    def test_boundary_check_is_case_insensitive(self) -> None:
        payload = b"header\n*** START OF TEST\nbody\n*** END OF TEST\n"
        self.assertTrue(VALIDATOR._has_boundaries(payload))

    def test_boundary_check_requires_ordered_markers(self) -> None:
        payload = b"*** END OF TEST\nbody\n*** START OF TEST\n"
        self.assertFalse(VALIDATOR._has_boundaries(payload))


if __name__ == "__main__":
    unittest.main()
