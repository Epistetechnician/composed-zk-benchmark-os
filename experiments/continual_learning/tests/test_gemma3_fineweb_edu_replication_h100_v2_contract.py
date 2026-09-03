"""Hermetic V2 contract regression tests.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v2.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_h100_v2_contract as contract,
)


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(contract.canonical(value))


def _launch() -> dict[str, object]:
    return {
        "schema": contract.LAUNCH_SCHEMA,
        "state_slice": contract.STATE_SLICE,
        "provider": "givemeanode",
        "provider_project": "project-v2",
        "node_type": "h100-1",
        "job_mode": "batch",
        "container_digest": "sha256:" + "a" * 64,
        "manifest_sha256": "b" * 64,
        "quoted_gpu_usd_per_minute": 0.05,
        "max_runtime_minutes": 20.0,
        "estimated_max_total_usd": 1.0,
        "hard_usd_ceiling": 2.0,
    }


def _provider_receipt(launch: dict[str, object]) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema": contract.PROVIDER_RECEIPT_SCHEMA,
        "state_slice": contract.STATE_SLICE,
        "provider": launch["provider"],
        "provider_project": launch["provider_project"],
        "node_type": launch["node_type"],
        "job_mode": launch["job_mode"],
        "allocation_id": "allocation-v2",
        "node_id": "node-v2",
        "start_utc": "2026-09-01T15:00:00Z",
        "stop_utc": "2026-09-01T15:10:00Z",
        "quoted_gpu_usd_per_minute": launch["quoted_gpu_usd_per_minute"],
        "charged_usd": 0.5,
        "hard_usd_ceiling": launch["hard_usd_ceiling"],
        "estimated_max_total_usd": launch["estimated_max_total_usd"],
        "stop_reason": "completed",
        "launch_manifest_sha256": launch["manifest_sha256"],
        "container_digest": launch["container_digest"],
    }
    payload_digest = contract.provider_payload_digest(receipt)
    receipt["provider_attestation"] = {
        "issuer": "givemeanode",
        "key_id": "provider-key-v2",
        "algorithm": "ed25519",
        "payload_sha256": payload_digest,
        "signature": "c" * 128,
    }
    receipt["receipt_sha256"] = contract.digest(receipt, "receipt_sha256")
    return receipt


def test_manifest_builder_excludes_self_but_binds_reviewed_manifest(tmp_path: Path) -> None:
    files = ("one.txt", "two.txt")
    for name in files:
        (tmp_path / name).write_text(name, encoding="utf-8")
    manifest = contract.build_implementation_manifest(tmp_path, files)
    assert [item["path"] for item in manifest["files"]] == list(files)
    assert "implementation-manifest.json" not in [item["path"] for item in manifest["files"]]
    assert manifest["manifest_sha256"] == contract.digest(manifest, "manifest_sha256")


def test_manifest_rejects_stale_self_digest(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text("one", encoding="utf-8")
    manifest = contract.build_implementation_manifest(tmp_path, ("one.txt",))
    manifest["manifest_sha256"] = "0" * 64
    path = tmp_path / "manifest.json"
    _write_json(path, manifest)
    with pytest.raises(ValueError, match="self digest"):
        contract.validate_implementation_manifest(path, tmp_path, ("one.txt",))


def test_provider_receipt_requires_independent_attestation_verification() -> None:
    launch = _launch()
    receipt = _provider_receipt(launch)
    with pytest.raises(ValueError, match="independently verified"):
        contract.validate_provider_receipt(receipt, launch)
    seen_payload: dict[str, object] = {}

    def verify(payload: dict[str, object], _attestation: dict[str, object]) -> bool:
        seen_payload.update(payload)
        return True

    assert contract.validate_provider_receipt(receipt, launch, verify)["charged_usd"] == 0.5
    assert "provider_attestation" not in seen_payload
    assert "receipt_sha256" not in seen_payload
    assert seen_payload == {
        key: value
        for key, value in receipt.items()
        if key not in {"provider_attestation", "receipt_sha256"}
    }


def test_provider_receipt_rejects_invalid_stop_reason_and_runtime() -> None:
    launch = _launch()
    receipt = _provider_receipt(launch)
    receipt["stop_reason"] = "operator_felt_done"
    with pytest.raises(ValueError, match="stop reason"):
        contract.validate_provider_receipt(receipt, launch, lambda *_: True)

    receipt = _provider_receipt(launch)
    receipt["stop_utc"] = "2026-09-01T14:59:00Z"
    with pytest.raises(ValueError, match="stop time"):
        contract.validate_provider_receipt(receipt, launch, lambda *_: True)


def test_provider_receipt_rejects_over_budget_charge() -> None:
    launch = _launch()
    receipt = _provider_receipt(launch)
    receipt["charged_usd"] = 1.01
    with pytest.raises(ValueError, match="sealed budget"):
        contract.validate_provider_receipt(receipt, launch, lambda *_: True)


def test_result_root_rejects_extra_directory_and_publish_before_validation(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    for name in ("provider-receipt.json", "result.json", "result-receipt.json"):
        (staging / name).write_text("{}\n", encoding="utf-8")
    (staging / "unexpected").mkdir()
    with pytest.raises(ValueError, match="unexpected directory"):
        contract.validate_result_root(staging)

    (staging / "unexpected").rmdir()
    for path in tuple(staging.iterdir()):
        path.unlink()
    staging.rmdir()

    staging.mkdir()
    for name in ("provider-receipt.json", "result.json", "result-receipt.json"):
        (staging / name).write_text("{}\n", encoding="utf-8")
    snapshot = contract.validate_result_root(staging)
    final = tmp_path / "published"
    final.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        contract.publish_no_replace(staging, final, snapshot)


def test_publish_reserves_destination_without_rename_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    for name in ("provider-receipt.json", "result.json", "result-receipt.json"):
        (staging / name).write_text("{}\n", encoding="utf-8")
    snapshot = contract.validate_result_root(staging)

    def unexpected_rename(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("publication must not use replace-capable rename")

    monkeypatch.setattr(contract.os, "rename", unexpected_rename)
    final = contract.publish_no_replace(staging, tmp_path / "published", snapshot)
    assert contract.validate_result_root(final) == snapshot


def test_result_root_seal_detects_post_validation_mutation(tmp_path: Path) -> None:
    root = tmp_path / "staging"
    root.mkdir()
    for name in ("provider-receipt.json", "result.json", "result-receipt.json"):
        (root / name).write_text("{}\n", encoding="utf-8")
    before = contract.validate_result_root(root)
    (root / "result.json").write_text('{"changed":true}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="changed after validation"):
        contract.assert_unchanged(root, before)


def test_manifest_json_is_canonical_and_closed() -> None:
    value = {"b": 2, "a": 1}
    assert contract.canonical(value) == b'{"a":1,"b":2}\n'
    assert json.loads(contract.canonical(value)) == value
    assert datetime.now(timezone.utc).tzinfo is not None


def test_frozen_v2_implementation_manifest_is_current() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    manifest_path = (
        repo_root
        / "docs/research/continual-learning/260-gemma3-fineweb-edu-replication-h100-v2-implementation-manifest.json"
    )
    expected_files = (
        "docs/research/continual-learning/258-gemma3-fineweb-edu-replication-h100-v2-protocol.md",
        "docs/research/continual-learning/259-gemma3-fineweb-edu-replication-h100-v2-review-packet.md",
        "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v2_contract.py",
        "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v2_contract.py",
        "AGENTS.md",
    )
    result = contract.validate_implementation_manifest(
        manifest_path, repo_root, expected_files
    )
    assert result["state_slice"] == contract.STATE_SLICE
