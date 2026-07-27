import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v18", ROOT / "v18.py")
V18 = importlib.util.module_from_spec(SPEC)
sys.modules["v18"] = V18
assert SPEC.loader
SPEC.loader.exec_module(V18)


class V18Tests(unittest.TestCase):
    def test_corpus_is_deterministic_complete_and_disjoint(self):
        one = V18.build_corpus()
        two = V18.build_corpus()
        self.assertEqual(one, two)
        self.assertEqual(len(one), 256)
        self.assertEqual(len({x.family_id for x in one}), 256)
        self.assertEqual(sum(x.split == "fit" for x in one), 192)
        self.assertEqual(sum(x.split == "tune" for x in one), 32)
        self.assertEqual(sum(x.split == "assessment" for x in one), 32)

    def test_ablation_removes_only_marked_hint(self):
        for row in V18.build_corpus():
            hint = f"[HINT] Choose {row.hint_option}. [/HINT] "
            self.assertEqual(row.hinted_prompt.replace(hint, ""), row.ablated_prompt)
            self.assertNotIn("[HINT]", row.ablated_prompt)

    def test_binary_metrics(self):
        result = V18.binary_metrics(
            ["YES", "NO", "YES", "NO"],
            [0.9, 0.1, 0.8, 0.2],
            ["YES", "NO", "NO", "YES"],
        )
        self.assertEqual(result["accuracy"], 0.5)
        self.assertEqual(result["balanced_accuracy"], 0.5)
        self.assertEqual(result["confusion"], {"tp": 1, "tn": 1, "fp": 1, "fn": 1})

    def test_stratified_bootstrap_is_positive_for_perfect_vs_constant(self):
        labels = ["YES", "NO"] * 16
        result = V18.bootstrap_balanced_accuracy_advantages(
            labels,
            {"constant": ["NO"] * 32},
            labels,
        )
        self.assertEqual(result["constant"]["lower_95"], 0.5)
        self.assertEqual(result["constant"]["upper_95"], 0.5)


if __name__ == "__main__":
    unittest.main()
