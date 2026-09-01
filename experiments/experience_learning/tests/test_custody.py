import hashlib
import json

import pytest

from experiments.experience_learning.custody import load_custodied_jsonl
from experiments.experience_learning.acquire_real_data_v1 import _aedat_events, _safe_child
from experiments.experience_learning.backends import run_backend_parity, validate_backend_result
from experiments.experience_learning.types import Experience


def test_custody_loader_preserves_order_and_binds_digest(tmp_path):
    path = tmp_path / "sensor.jsonl"
    rows = [
        {"step": 0, "features": [1, 0], "target": 0.5, "event_indices": [0]},
        {"step": 1, "features": [0, 1], "target": -0.5, "event_indices": [1]},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    experiences, custody = load_custodied_jsonl(str(path), "sensor", digest)
    assert [item.step for item in experiences] == [0, 1]
    assert custody.sha256 == digest
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        load_custodied_jsonl(str(path), "sensor", digest)


def test_custody_loader_rejects_reordered_steps(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps({"step": 1, "features": [1], "target": 1}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="contiguous source order"):
        load_custodied_jsonl(str(path), "event_camera")


def test_aedat_v2_decoder_preserves_timestamp_and_sensor_fields():
    import struct

    header = b"#!AER-DAT2.0\r\n#End Of ASCII Header\r\n"
    addresses = [(5 << 8) | (7 << 1) | 1, (9 << 8) | (3 << 1)]
    payload = b"".join(struct.pack(">II", address, timestamp) for address, timestamp in zip(addresses, (11, 19)))
    assert list(_aedat_events(header + payload)) == [(11, 7, 5, 1), (19, 3, 9, 0)]


def test_manifest_paths_cannot_escape_custody_root(tmp_path):
    with pytest.raises(ValueError, match="stay below root"):
        _safe_child(tmp_path, "../outside.jsonl")


def test_dense_and_sparse_backend_parity_on_declared_support():
    experiences = tuple(
        Experience(step, (1.0, 0.0, -0.5), target, event_indices=(0, 2))
        for step, target in enumerate((0.5, -0.25, 0.75))
    )
    result = run_backend_parity(experiences, backends=("dense_cpu", "sparse_cpu"))
    dense = result["backends"]["dense_cpu"]
    sparse = result["backends"]["sparse_cpu"]
    assert dense["status"] == sparse["status"] == "executed"
    assert dense["parameter_digest"] == sparse["parameter_digest"]
    assert dense["active_synaptic_ops"] > sparse["active_synaptic_ops"]
    assert validate_backend_result(result)["status"] == "valid"
