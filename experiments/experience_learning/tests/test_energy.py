import hashlib

import pytest

from experiments.experience_learning.energy import (
    campaign_binding_digest, operation_energy_proxy, read_energy_csv,
)
from experiments.experience_learning.measure_energy_v1 import integrate_power_watts, write_receipt


def test_energy_receipt_is_hardware_and_digest_bound(tmp_path):
    path = tmp_path / "energy.csv"
    path.write_text("run_id,hardware,joules,events\nr1,cpu:test,12.5,5\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = read_energy_csv(str(path), digest)
    assert receipt.joules_per_event == 2.5
    assert operation_energy_proxy(20, 5) == 4.0


def test_energy_receipt_rejects_negative_values(tmp_path):
    path = tmp_path / "energy.csv"
    path.write_text("run_id,hardware,joules,events\nr1,cpu:test,-1,5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-negative"):
        read_energy_csv(str(path))


def test_power_trace_integration_is_trapezoidal_and_digest_bound(tmp_path):
    trace = tmp_path / "trace.csv"
    trace.write_text("timestamp_s,power_w\n0,2\n2,4\n", encoding="utf-8")
    output = tmp_path / "receipt.csv"
    row = write_receipt(output, "run-1", "cpu:test", 8, trace, [(0.0, 2.0), (2.0, 4.0)])
    assert row["duration_s"] == 2.0
    assert row["joules"] == 6.0
    assert read_energy_csv(str(output)).joules_per_event == 0.75


def test_power_trace_rejects_non_monotonic_timestamps():
    with pytest.raises(ValueError, match="strictly increasing"):
        integrate_power_watts(((0.0, 1.0), (0.0, 2.0)))


def test_campaign_bound_energy_receipt_requires_exact_digest_sets(tmp_path):
    trace = tmp_path / "trace.csv"
    trace.write_text("timestamp_s,power_w\n0,2\n2,4\n", encoding="utf-8")
    output = tmp_path / "receipt.csv"
    matrices = ("a" * 64, "b" * 64)
    guards = ("c" * 64,)
    backends = ("d" * 64, "e" * 64)
    manifest = campaign_binding_digest(matrices, guards, backends)
    write_receipt(output, "run-2", "cpu:test", 8, trace, [(0.0, 2.0), (2.0, 4.0)],
                  manifest, matrices, guards, backends)
    receipt = read_energy_csv(str(output), require_campaign_binding=True)
    assert receipt.campaign_bound is True
    assert receipt.campaign_manifest_sha256 == manifest

    broken = tmp_path / "broken.csv"
    broken.write_text(output.read_text(encoding="utf-8").replace(manifest, "f" * 64), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest digest mismatch"):
        read_energy_csv(str(broken), require_campaign_binding=True)


def test_publication_energy_mode_rejects_legacy_receipt(tmp_path):
    path = tmp_path / "legacy.csv"
    path.write_text("run_id,hardware,joules,events\nr1,cpu:test,1.0,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="campaign-bound energy receipt is required"):
        read_energy_csv(str(path), require_campaign_binding=True)
