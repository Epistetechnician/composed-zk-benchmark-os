from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r7_profile_validator", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_update():
    memory = {
        "allocated_bytes": 1,
        "reserved_bytes": 2,
        "peak_allocated_bytes": 3,
        "peak_reserved_bytes": 4,
    }
    return {
        "microbatches": [
            {
                "start": index,
                "end": index + 1,
                "weight": 0.25,
                "target_tokens": 1,
                "memory": memory,
            }
            for index in range(4)
        ]
    }


def test_microbatch_gate_accepts_exact_coverage() -> None:
    assert MODULE.validate_microbatches(valid_update()) == []
    assert MODULE.EXPECTED_RUNTIME["torch"] == "2.10.0+cu128"


def test_microbatch_gate_rejects_weight_and_coverage_drift() -> None:
    update = valid_update()
    update["microbatches"][2]["start"] = 1
    update["microbatches"][3]["weight"] = 0.5
    errors = MODULE.validate_microbatches(update)
    assert "microbatch coverage" in errors
    assert "microbatch weight sum" in errors


def test_missing_profile_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {
        "valid": False,
        "errors": ["profile artifact files missing"],
    }
