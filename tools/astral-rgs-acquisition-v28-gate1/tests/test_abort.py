from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28_abort", ROOT / "validate_abort.py")
assert SPEC and SPEC.loader
abort = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = abort
SPEC.loader.exec_module(abort)


def test_non_object_abort_fails_closed(tmp_path: Path) -> None:
    report = abort.validate(packet=None, artifact_root=tmp_path, ledger_path=tmp_path / "missing")
    assert not report["valid_failure_record"]
    assert report["scientific_result_valid"] is False
    assert report["claim_ceiling"] == "NoClaim"
