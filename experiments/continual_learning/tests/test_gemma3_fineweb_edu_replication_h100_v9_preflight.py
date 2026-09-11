"""Hermetic H100 launch preflight tests.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v9.
"""

from __future__ import annotations

import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path

import pytest

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_h100_v9_preflight as preflight,
)


def _digest(value: dict[str, object], field: str) -> str:
    body = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(preflight.canonical(body)).hexdigest()


def _manifest() -> dict[str, object]:
    values: dict[str, object] = {
        "schema": preflight.SCHEMA,
        "state_slice": preflight.STATE_SLICE,
        "provider": "givemeanode",
        "node_type": "h100-1",
        "job_mode": "batch",
        "hard_usd_ceiling": "69.00",
        "quoted_gpu_usd_per_minute": "0.05",
        "max_runtime_minutes": 100.0,
        "estimated_max_total_usd": "5.00",
        "provider_project": "project-v9",
        "provider_attestation_key_id": "gman-test-key-v9",
        "provider_trust_root_id": "gman-test-root-v9",
        "provider_trust_root_public_key": "A" * 43 + "=",
        "provider_trust_root_registry_path": "/external/gman-root-registry.json",
        "provider_trust_root_registry_sha256": "3" * 64,
        "container_image": "example/image:locked",
        "container_digest": "sha256:" + "a" * 64,
        "cuda_driver_version": "550.54.15",
        "container_network_mode": "none",
        "code_bundle_path": "/external/code.tar.zst",
        "code_bundle_sha256": "b" * 64,
        "runner_entrypoint": "run_h100_v9.sh",
        "runtime_lock_path": "runtime-lock.json",
        "runtime_lock_sha256": "2" * 64,
        "network_lock": "network-none-v9",
        "implementation_manifest_path": "implementation.json",
        "implementation_manifest_sha256": "1" * 64,
        "model_bundle_path": "/external/model.tar.zst",
        "model_id": "google/gemma-3-1b-pt",
        "model_revision": "a" * 40,
        "model_architecture": "Gemma3ForCausalLM",
        "model_manifest_sha256": "c" * 64,
        "data_bundle_path": "/external/data.tar.zst",
        "source_bundle_path": "/external/source.tar.zst",
        "raw_bundle_path": "/external/raw",
        "data_manifest_sha256": "d" * 64,
        "source_manifest_sha256": "1" * 64,
        "external_storage_namespace": "bucket/namespace-v9",
        "review_receipt_path": "review.json",
        "review_receipt_sha256": "e" * 64,
        "protocol_sha256": "f" * 64,
        "packet_sha256": "0" * 64,
        "launch_command": "./run_h100_v9.sh",
        "launch_command_sha256": hashlib.sha256(b"./run_h100_v9.sh").hexdigest(),
        "stop_rule": preflight.STOP_RULE,
        "assessment_enabled": True,
        "training_enabled": False,
        "network_during_effects": False,
        "effects_run": False,
    }
    values["manifest_sha256"] = _digest(values, "manifest_sha256")
    return values


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def test_schema_is_closed(tmp_path: Path) -> None:
    values = _manifest()
    values["unexpected"] = True
    path = tmp_path / "manifest.json"
    _write(path, values)
    with pytest.raises(ValueError, match="schema is not closed"):
        preflight.validate_launch_manifest(path, tmp_path)


def test_budget_overflow_is_rejected(tmp_path: Path) -> None:
    values = _manifest()
    values["quoted_gpu_usd_per_minute"] = "0.70"
    values["estimated_max_total_usd"] = "70.00"
    values["manifest_sha256"] = _digest(values, "manifest_sha256")
    path = tmp_path / "manifest.json"
    _write(path, values)
    with pytest.raises(ValueError, match="budget arithmetic"):
        preflight.validate_launch_manifest(path, tmp_path)


def test_budget_requires_exact_decimal_product(tmp_path: Path) -> None:
    values = _manifest()
    values["max_runtime_minutes"] = 101.0
    values["manifest_sha256"] = _digest(values, "manifest_sha256")
    path = tmp_path / "manifest.json"
    _write(path, values)
    with pytest.raises(ValueError, match="budget arithmetic"):
        preflight.validate_launch_manifest(path, tmp_path)


def test_budget_rejects_unrounded_product_over_ceiling(tmp_path: Path) -> None:
    values = _manifest()
    values["quoted_gpu_usd_per_minute"] = "0.01"
    values["max_runtime_minutes"] = 6900.4
    values["estimated_max_total_usd"] = "69.00"
    values["manifest_sha256"] = _digest(values, "manifest_sha256")
    path = tmp_path / "manifest.json"
    _write(path, values)
    with pytest.raises(ValueError, match="budget arithmetic"):
        preflight.validate_launch_manifest(path, tmp_path)


def test_budget_rejects_float_rounding_attack(tmp_path: Path) -> None:
    values = _manifest()
    digest_values = dict(values)
    digest_values["hard_usd_ceiling"] = Decimal("69.0000000000000001")
    values["manifest_sha256"] = _digest(digest_values, "manifest_sha256")
    path = tmp_path / "manifest.json"
    encoded = json.dumps(values, sort_keys=True).replace(
        '"hard_usd_ceiling": "69.00"',
        '"hard_usd_ceiling": 69.0000000000000001',
        1,
    )
    path.write_text(encoded + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hard_usd_ceiling"):
        preflight.validate_launch_manifest(path, tmp_path)


def test_code_bundle_digest_is_recomputed(tmp_path: Path) -> None:
    code_bundle = tmp_path / "code.tar.zst"
    code_bundle.write_bytes(b"sealed-code")
    expected = hashlib.sha256(code_bundle.read_bytes()).hexdigest()
    preflight.validate_code_bundle_digest(code_bundle, expected)
    with pytest.raises(ValueError, match="does not match"):
        preflight.validate_code_bundle_digest(code_bundle, "0" * 64)


def test_training_is_rejected(tmp_path: Path) -> None:
    values = _manifest()
    values["training_enabled"] = True
    values["manifest_sha256"] = _digest(values, "manifest_sha256")
    path = tmp_path / "manifest.json"
    _write(path, values)
    with pytest.raises(ValueError, match="training"):
        preflight.validate_launch_manifest(path, tmp_path)


def test_missing_review_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    _write(path, _manifest())
    with pytest.raises((OSError, ValueError)):
        preflight.validate_launch_manifest(path, tmp_path)


def test_mutable_bundle_path_is_rejected_before_review_lookup(tmp_path: Path) -> None:
    values = _manifest()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    bundle = tmp_path / "code-bundle"
    bundle.mkdir()
    os.chmod(bundle, 0o755)
    values["code_bundle_path"] = str(bundle)
    values["manifest_sha256"] = _digest(values, "manifest_sha256")
    path = repo_root / "manifest.json"
    _write(path, values)
    with pytest.raises(ValueError, match="parent is mutable"):
        preflight.validate_launch_manifest(path, repo_root)


def test_stop_rule_must_match_exact_reviewed_text(tmp_path: Path) -> None:
    values = _manifest()
    values["stop_rule"] = "stop at first failed gate or budget boundary"
    values["manifest_sha256"] = _digest(values, "manifest_sha256")
    path = tmp_path / "manifest.json"
    _write(path, values)
    with pytest.raises(ValueError, match="stop_rule is not the exact reviewed stop rule"):
        preflight.validate_launch_manifest(path, tmp_path)
