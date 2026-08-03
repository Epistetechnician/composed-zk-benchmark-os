from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r27_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


def test_contract_is_fresh_and_staged() -> None:
    packet = MODULE.expected_contract()
    assert packet["run_count"] == 48 and packet["stages"]["sentinel_run_count"] == 9
    assert packet["v41r26_data_or_seeds_reused"] is False
    assert set(packet["seeds"]).isdisjoint({411017, 411031, 411043})


def test_projection_is_independently_reconstructed() -> None:
    assert MODULE.project([1.0, -2.0], [0.0, 1.0]) == [1.0, 0.0]
    assert MODULE.project([1.0, 2.0], [0.0, 1.0]) == [1.0, 2.0]


def test_missing_producer_fails_closed(tmp_path: Path) -> None:
    report = MODULE.validate(tmp_path)
    assert report["valid"] is False and report["runtime_authorized"] is False
