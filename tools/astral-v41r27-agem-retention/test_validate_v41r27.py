from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r27_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
SENTINEL_PATH = Path(__file__).with_name("validate_sentinel.py")
SENTINEL_SPEC = importlib.util.spec_from_file_location("v41r27_sentinel_validator", SENTINEL_PATH)
assert SENTINEL_SPEC and SENTINEL_SPEC.loader
SENTINEL = importlib.util.module_from_spec(SENTINEL_SPEC); SENTINEL_SPEC.loader.exec_module(SENTINEL)


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


def test_sentinel_specs_are_exact_nine_run_cross_product() -> None:
    specs = SENTINEL.sentinel_specs()
    assert len(specs) == 9
    assert [spec["panel_id"] for spec in specs[::3]] == ["v41r27-panel-0", "v41r27-panel-7", "v41r27-panel-15"]


def test_sentinel_decision_requires_nine_passes() -> None:
    workers = [{"pass": True, "governance_violations": 0} for _ in range(9)]
    assert SENTINEL.decision(workers)["sentinel_keep"] is True
    workers[-1]["pass"] = False
    assert SENTINEL.decision(workers)["sentinel_keep"] is False


def test_missing_sentinel_artifact_fails_closed(tmp_path: Path) -> None:
    assert SENTINEL.validate(tmp_path, tmp_path) == {
        "valid": False, "errors": ["sentinel artifact files missing"]}
