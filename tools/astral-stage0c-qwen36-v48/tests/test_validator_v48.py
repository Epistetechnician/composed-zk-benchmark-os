import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import validate_v48 as validator


def test_validator_forbids_raw_artifact_keys():
    keys = validator._walk_keys({"aggregate": {"logits": [1.0], "mean": 0.0}})
    assert "logits" in keys
    assert "logits" in validator.FORBIDDEN_EXACT_KEYS


def test_validator_allows_declared_aggregate_control_names():
    keys = validator._walk_keys({"controls": {"activation_only": {"mean": 0.0}, "text_only_clean_margin": {"mean": 0.0}}})
    assert not any(key in validator.FORBIDDEN_EXACT_KEYS for key in keys)
