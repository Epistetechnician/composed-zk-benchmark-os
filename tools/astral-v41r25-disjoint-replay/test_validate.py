from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r25_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


def test_frozen_panels_are_disjoint() -> None:
    assert not set(MODULE.ACQUISITION) & set(MODULE.PRIOR_ACQUISITION)
    assert not set(MODULE.PROTECTED) & set(MODULE.PRIOR_PROTECTED)


def test_missing_sources_fail_closed(tmp_path: Path) -> None:
    report = MODULE.validate(tmp_path)
    assert report["valid"] is False
    assert report["runtime_authorized"] is False
