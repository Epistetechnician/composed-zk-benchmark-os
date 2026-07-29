from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28r5", ROOT / "v28r5.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_protocol_freezes_reference_and_non_scientific_ceiling() -> None:
    assert module.PROTOCOL["reference_file_sha256"].endswith("caa71227")
    assert module.PROTOCOL["runs"] == {"optimized_batch8": 8, "optimized_batch64": 64}
    assert not module.PROTOCOL["scientific_campaign_authorized"]


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    result = module.validate(tmp_path)
    assert not result["valid"]
    assert not result["qualified"]
