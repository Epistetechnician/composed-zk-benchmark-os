"""Hermetic panel-builder tests for V41.

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


PANEL = load_module("astral_stage0c_qwen36_panel_v41", "panel_v41.py")


class FakeTokenizer:
    def encode(self, text: str) -> list[str]:
        return text.split()


class PanelV41Tests(unittest.TestCase):
    def test_prompt_reaches_fixed_length_with_deterministic_padding(self) -> None:
        tokenizer = FakeTokenizer()
        first = PANEL._prompt("A short passage with enough words for a test.", "silver", "amber", tokenizer)
        second = PANEL._prompt("A short passage with enough words for a test.", "silver", "amber", tokenizer)
        self.assertEqual(len(tokenizer.encode(first)), PANEL.protocol.FIXED_TOKEN_LENGTH)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("Answer:"))

    def test_markup_word_is_not_selected_as_target(self) -> None:
        candidate = {"lower_words": ["thought", "visible"], "normalized": "_thought_ visible"}
        self.assertEqual(PANEL._choose_target(candidate, 76, 6, set()), "visible")

    def test_reserved_concept_is_not_selected_again(self) -> None:
        candidate = {"lower_words": ["thought", "visible"], "normalized": "_thought_ visible"}
        self.assertEqual(PANEL._choose_target(candidate, 76, 6, {"thought"}), "visible")

    def test_counterfactual_prompt_is_distinct(self) -> None:
        tokenizer = FakeTokenizer()
        ordinary = PANEL._prompt("The silver object remains visible.", "silver", "amber", tokenizer)
        counterfactual = PANEL._prompt("The amber object remains visible.", "silver", "amber", tokenizer)
        self.assertNotEqual(ordinary, counterfactual)
        self.assertEqual(len(tokenizer.encode(ordinary)), PANEL.protocol.FIXED_TOKEN_LENGTH)
        self.assertEqual(len(tokenizer.encode(counterfactual)), PANEL.protocol.FIXED_TOKEN_LENGTH)


if __name__ == "__main__":
    unittest.main()
