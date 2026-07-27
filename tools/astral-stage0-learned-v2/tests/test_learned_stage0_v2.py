from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v2 as v2


class V2QualificationTests(unittest.TestCase):
    def test_v2_training_never_materializes_holdout(self):
        source = (ROOT / "learned_stage0_v2.py").read_text()
        self.assertNotIn("range(320", source)
        self.assertNotIn("range(384", source)

    def test_candidate_and_scientific_methods_remain_v1(self):
        self.assertEqual(v2.TinyTransformer.architecture_id, "astral.learned-tiny-transformer.v1")


if __name__ == "__main__":
    unittest.main()
