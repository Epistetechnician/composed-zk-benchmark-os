import importlib.util
import sys
from pathlib import Path

import numpy as np


PATH = Path(__file__).resolve().parents[1] / "validate_release.py"
SPEC = importlib.util.spec_from_file_location("astral_release_validator_tested", PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


def test_metric_recomputation():
    metrics = VALIDATOR.calculated_metrics([0.0, 1.0, 2.0], [0.0, 1.0, 2.0])
    assert metrics["mse"] == 0
    assert metrics["mae"] == 0
    assert np.isclose(metrics["pearson"], 1)
    assert np.isclose(metrics["calibration_intercept"], 0, atol=1e-12)
    assert np.isclose(metrics["calibration_slope"], 1)


def test_release_spec_covers_v18_through_v23():
    import json

    spec = json.loads((PATH.with_name("release-spec.json")).read_text())
    assert set(spec["bundles"]) == {"v18", "v19", "v20", "v21", "v22", "v23"}
    assert {name for name, row in spec["bundles"].items() if row["assessment"] == "absent"} == {"v19", "v22", "v23"}
    assert spec["claim_ceiling"] == "LocalImmutableValidationCandidate"


def test_detached_worker_flag_is_not_part_of_public_contract():
    source = PATH.read_text()
    assert '--in-detached-worker", action="store_true", help=argparse.SUPPRESS' in source
    assert '"git", "worktree", "add", "--detach"' in source
    assert '"git", "worktree", "remove", "--force"' in source
