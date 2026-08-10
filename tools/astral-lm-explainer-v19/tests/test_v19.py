import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v19", ROOT / "v19.py")
V19 = importlib.util.module_from_spec(SPEC)
sys.modules["v19"] = V19
assert SPEC.loader
SPEC.loader.exec_module(V19)


class V19Tests(unittest.TestCase):
    def test_corpus_is_deterministic_complete_and_new(self):
        one = V19.build_corpus()
        self.assertEqual(one, V19.build_corpus())
        self.assertEqual(len(one), 320)
        self.assertEqual(len({x.family_id for x in one}), 320)
        self.assertEqual(sum(x.split == "fit" for x in one), 240)
        self.assertEqual(sum(x.split == "tune" for x in one), 40)
        self.assertEqual(sum(x.split == "assessment" for x in one), 40)
        self.assertTrue(all(x.family_id.startswith("v19-") for x in one))

    def test_ablation_removes_exact_hint(self):
        for row in V19.build_corpus():
            hint = f"[HINT] Choose {row.hint_option}. [/HINT] "
            self.assertEqual(
                row.hinted_prompt.replace(hint, ""), row.ablated_prompt
            )

    def test_majority_ensemble_uses_votes_and_median_probability(self):
        raw = {}
        for seed, prediction, probability in (
            (1901, "YES", 0.9),
            (1913, "NO", 0.1),
            (1931, "YES", 0.7),
        ):
            raw[f"qwen-{seed}"] = [
                {
                    "family_id": "x",
                    "prediction": prediction,
                    "yes_probability": probability,
                }
            ]
        result = V19.majority_ensemble(raw, "qwen")[0]
        self.assertEqual(result["prediction"], "YES")
        self.assertEqual(result["yes_probability"], 0.7)


if __name__ == "__main__":
    unittest.main()
