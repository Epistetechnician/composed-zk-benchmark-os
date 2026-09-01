"""Hermetic Oak Lab H100 V3 protocol tests.

State slice: oaklab-experience-learning-h100-replication-v3.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]


def load():
    path = ROOT / "experiments/experience_learning/validate_oaklab_h100_v3_protocol.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_packet_and_compiled_artifact_are_valid() -> None:
    result = load().validate_packet(ROOT)
    assert result["valid"] is True
    assert result["state_slice"] == "oaklab-experience-learning-h100-replication-v3"


def test_campaign_manifest_self_digest_and_compiled_binding() -> None:
    validator = load()
    compiled_sha = validator.sha256_file(ROOT / validator.COMPILED)
    body = {"schema": "oaklab-h100-v3-campaign", "state_slice": validator.STATE_SLICE, "compiled_protocol_sha256": compiled_sha, "code_sha256": "a" * 64, "model_sha256": "b" * 64, "data_sha256": "c" * 64, "backend_sha256": "d" * 64, "guard_sha256": "e" * 64, "tune_lock_sha256": "f" * 64, "provider_receipt_sha256": "1" * 64, "energy_receipt_sha256": "2" * 64, "result_root_sha256": "3" * 64, "hard_usd_ceiling": 10.0}
    manifest = {**body, "manifest_sha256": validator.digest(body, "manifest_sha256")}
    validator.validate_campaign_manifest(manifest, compiled_sha)


def test_provider_receipt_rejects_over_ceiling() -> None:
    validator = load()
    receipt = {"schema": "oaklab-h100-v3-provider-receipt", "state_slice": validator.STATE_SLICE, "allocation_id": "a", "node_id": "n", "start_utc": "2026-01-01T00:00:00Z", "stop_utc": "2026-01-01T00:01:00Z", "charged_usd": 2.0, "hard_usd_ceiling": 1.0, "launch_manifest_sha256": "a" * 64, "raw_trace_sha256": "b" * 64, "public_key_hex": "c" * 64, "signature_hex": "d" * 128}
    receipt["receipt_sha256"] = validator.sha256_bytes(validator.canonical({**{k: v for k, v in receipt.items() if k != "receipt_sha256"}}))
    with pytest.raises(ValueError, match="charge exceeds"):
        validator.validate_provider_receipt(receipt, 1.0, "a" * 64)


def test_result_root_rejects_extra_path(tmp_path: Path) -> None:
    validator = load()
    compiled = validator.validate_compiled(ROOT)
    root = tmp_path / "result"
    root.mkdir()
    for relative in compiled["result_root"]["allowlist"]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}\n")
    (root / "extra.json").write_bytes(b"{}\n")
    with pytest.raises(ValueError, match="file set mismatch"):
        validator.validate_result_root(root, compiled)


def test_energy_trace_requires_monotone_finite_nonnegative_samples(tmp_path: Path) -> None:
    validator = load()
    path = tmp_path / "trace.csv"
    path.write_text("utc_ns,watts\n2,1.0\n1,1.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="monotone"):
        validator.validate_energy_trace(path)
