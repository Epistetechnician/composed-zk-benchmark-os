"""Hermetic Oak Lab H100 V2 protocol tests.

State slice: oaklab-experience-learning-h100-replication-v2.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "experiments/experience_learning/compile_oaklab_h100_v2_protocol.py"
VALIDATOR = ROOT / "experiments/experience_learning/validate_oaklab_h100_v2_protocol.py"


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compiled_packet_is_valid() -> None:
    validator = load(VALIDATOR)
    result = validator.validate_packet(ROOT)
    assert result["valid"] is True
    assert result["state_slice"] == "oaklab-experience-learning-h100-replication-v2"


def test_provider_receipt_rejects_charge_over_ceiling() -> None:
    validator = load(VALIDATOR)
    receipt = {
        "allocation_id": "a",
        "node_id": "n",
        "start_utc": "2026-01-01T00:00:00Z",
        "stop_utc": "2026-01-01T00:01:00Z",
        "quoted_gpu_usd_per_minute": 1.0,
        "charged_usd": 2.0,
        "stop_reason": "completed",
        "raw_trace_sha256": "a" * 64,
        "launch_manifest_sha256": "b" * 64,
    }
    with pytest.raises(ValueError, match="hard USD ceiling"):
        validator.validate_provider_receipt(receipt, 1.0)


def test_result_root_rejects_unlisted_file(tmp_path: Path) -> None:
    validator = load(VALIDATOR)
    compiled = validator.validate_compiled(ROOT)
    root = tmp_path / "result"
    root.mkdir()
    for relative in compiled["result_root_schema"]["allowed_paths"]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}\n")
    (root / "extra.json").write_bytes(b"{}\n")
    with pytest.raises(ValueError, match="file set mismatch"):
        validator.validate_result_root(root, compiled)


def test_result_root_rejects_symlink(tmp_path: Path) -> None:
    validator = load(VALIDATOR)
    compiled = validator.validate_compiled(ROOT)
    root = tmp_path / "result"
    root.mkdir()
    for relative in compiled["result_root_schema"]["allowed_paths"]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}\n")
    target = root / "campaign_manifest.json"
    target.unlink()
    target.symlink_to(root / "provider" / "allocation.json")
    with pytest.raises(ValueError, match="symlink"):
        validator.validate_result_root(root, compiled)
