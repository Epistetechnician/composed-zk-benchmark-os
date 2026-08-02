from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r26_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


def test_contract_has_sixteen_disjoint_panels_and_fortyeight_runs() -> None:
    packet = MODULE.expected_contract()
    assert packet["run_count"] == 48 and len(packet["panels"]) == 16
    assert [i for panel in packet["panels"] for i in panel["acquisition_indices"]] == list(range(64))
    assert [i for panel in packet["panels"] for i in panel["protected_indices"]] == list(range(256))


def test_gate_requires_all_sixteen_independent_panels() -> None:
    assert MODULE.wilson_lower(16, 16) > 0.80
    assert MODULE.wilson_lower(15, 16) < 0.80


def test_missing_producer_fails_closed(tmp_path: Path) -> None:
    report = MODULE.validate(tmp_path)
    assert report["valid"] is False and report["runtime_authorized"] is False
