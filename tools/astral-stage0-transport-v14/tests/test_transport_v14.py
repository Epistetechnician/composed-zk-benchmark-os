from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_transport_v14 import prepare
from transport_v14 import classify, variance_decomposition


class V14Tests(unittest.TestCase):
    def metrics(self, cross, actor, activation, telemetry):
        def cell(value):
            return {"pooled": {"mse": value}}
        return {
            "cross_actor_constant": cell(cross), "actor_constant": cell(actor),
            "actor_activation": cell(activation), "actor_telemetry": cell(telemetry),
        }

    def test_classifications(self):
        self.assertEqual(classify(self.metrics(10, 7, 5, 4)), "CrossActorTransportFailure")
        self.assertEqual(classify(self.metrics(10, 7, 4, 5)), "ActorBaselineShiftOnly")
        self.assertEqual(classify(self.metrics(10, 9, 4, 5)), "LocalTelemetryNonpredictive")
        self.assertEqual(classify(self.metrics(10, 9, 5, 4)), "MixedDiagnostic")

    def test_variance_decomposition_balanced(self):
        rows = [
            {"effect": actor + site, "operator": "zero_ablation", "seed": actor, "site": f"head{site}.cls"}
            for actor in (0, 2) for site in (0, 1) for _ in range(2)
        ]
        result = variance_decomposition(rows)
        self.assertAlmostEqual(result["actor_fraction"], 0.8)
        self.assertAlmostEqual(result["site_operator_fraction"], 0.2)
        self.assertAlmostEqual(result["residual_fraction"], 0.0)

    def test_output_guards(self):
        repo = Path(__file__).resolve().parents[4]
        with self.assertRaises(ValueError):
            prepare(repo.parent, repo)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "occupied").write_text("x")
            with self.assertRaises(ValueError):
                prepare(root, repo)


if __name__ == "__main__":
    unittest.main()
