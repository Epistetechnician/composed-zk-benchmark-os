import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import v54, books_v54


class T(unittest.TestCase):
    def test_cap(self):
        self.assertLessEqual(v54.FROZEN54["spend_cap_usd"], 4.80)

    def test_books_fresh_and_bounded(self):
        import json
        ids = [b[0] for b in books_v54.BOOKS]
        self.assertLessEqual(len(ids), 60); self.assertEqual(len(ids), len(set(ids)))
        old = {1695, 974, 5658, 2021, 2891, 2641, 284, 4517, 24, 242, 233, 215, 910, 1074, 2852, 16, 2226, 217, 2814, 4217,
               144, 351, 2775, 62, 45, 289, 805, 416, 543, 1300, 558, 204, 140, 541, 718, 1056, 4300, 219, 3600, 1342}
        self.assertFalse((old - {1342}) & set(ids))


if __name__ == "__main__":
    unittest.main()
