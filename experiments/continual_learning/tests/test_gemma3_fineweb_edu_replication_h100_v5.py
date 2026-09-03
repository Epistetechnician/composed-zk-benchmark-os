"""Hermetic H100 runner and validator contract tests.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v5.
"""

from __future__ import annotations

import json
import base64
import os
import shutil
from pathlib import Path

import pytest
import torch

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_h100_v5 as runner,
)
from experiments.continual_learning import (
    validate_gemma3_fineweb_edu_replication_h100_v5 as validator,
)


def test_norm_adjusted_mix_and_zero_alpha_identity() -> None:
    config = runner.RecirculationConfig(2, 1, 0.15, 0.85)
    source = torch.tensor([[[3.0, 4.0]]], dtype=torch.bfloat16)
    destination = torch.tensor([[[1.0, 0.0]]], dtype=torch.bfloat16)
    mixed = runner.mix_hidden(torch, source, destination, config)
    expected = (0.85 * destination.float()) + (0.15 * source.float() * 1.0 / 5.0)
    assert torch.allclose(mixed.float(), expected, atol=2e-3, rtol=0)
    identity = runner.mix_hidden(
        torch,
        source,
        destination,
        runner.RecirculationConfig(2, 1, 0.0, 1.0),
    )
    assert torch.equal(identity, destination)


def test_hook_carries_previous_token_source_to_destination() -> None:
    class AddOne(torch.nn.Module):
        def forward(self, value: torch.Tensor) -> torch.Tensor:
            return value + 1

    class Text(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.layers = torch.nn.ModuleList([AddOne(), AddOne(), AddOne()])

    class Model(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.model = Text()
            self.anchor = torch.nn.Parameter(torch.ones(1))

    model = Model()
    hooks = runner.RecirculationHooks(
        model, runner.RecirculationConfig(2, 1, 0.15, 0.85)
    )
    try:
        hooks.begin_token()
        value = torch.zeros((1, 1, 1), dtype=torch.bfloat16)
        for layer in model.model.layers:
            value = layer(value)
        hooks.end_token()
        hooks.begin_token()
        value = torch.zeros((1, 1, 1), dtype=torch.bfloat16)
        for layer in model.model.layers:
            value = layer(value)
        hooks.end_token()
    finally:
        hooks.close()
    assert torch.equal(value, torch.full_like(value, 3))


def test_bootstrap_algorithm_is_shared_by_independent_implementations() -> None:
    values = [-0.5, -0.25, 0.0, 0.25]
    assert runner.bootstrap_mean_ci(values) == validator.bootstrap(values)


def test_provider_bundle_has_no_runtime_install_or_provider_submission() -> None:
    root = Path(__file__).parents[1] / "gemma3_fineweb_edu_replication_h100_v5_provider"
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    entrypoint = (root / "run_h100_v5.sh").read_text(encoding="utf-8")
    lock = json.loads((root / "runtime-lock.json").read_text(encoding="utf-8"))
    assert "FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04@sha256:0a1cb6e7bd047a1067efe14efdf0276352d5ca643dfd77963dab1a4f05a003a4" in dockerfile
    assert "ARG BASE_IMAGE" not in dockerfile
    assert "ARG BASE_DIGEST" not in dockerfile
    assert "python3.11 -m venv \"${VIRTUAL_ENV}\"" in dockerfile
    assert "-m pip install" in dockerfile
    assert "--requirement /opt/h100-replication/requirements.lock" in dockerfile
    assert "gman" not in entrypoint.lower()
    assert "network-none-v5" in entrypoint
    assert "H100_RAW_ROOT" in entrypoint
    assert "H100_SOURCE_ROOT" in entrypoint
    assert "--raw-root" in entrypoint
    assert "--source-root" in entrypoint
    assert "--pre-effect" in entrypoint
    assert "pack_gemma3_fineweb_edu_replication_h100_v5.py" in dockerfile
    assert lock["package_install_at_runtime"] is False
    assert lock["accelerate"] == "1.6.0"


def test_result_validator_is_closed_world() -> None:
    assert "hidden_states" not in validator.RESULT_KEYS
    assert "token_ids" not in validator.RESULT_KEYS
    assert validator.RESULT_KEYS == set(validator.RESULT_KEYS)


def test_provider_receipt_validator_requires_exact_binding(tmp_path: Path) -> None:
    launch = {
        "provider": "givemeanode",
        "provider_project": "project-v5",
        "node_type": "h100-1",
        "job_mode": "batch",
        "container_digest": "sha256:" + ("a" * 64),
        "quoted_gpu_usd_per_minute": 0.05,
        "hard_usd_ceiling": 100.0,
        "estimated_max_total_usd": 5.0,
        "max_runtime_minutes": 100.0,
        "manifest_sha256": "b" * 64,
    }
    receipt = {
        "schema": validator.PROVIDER_RECEIPT_SCHEMA,
        "state_slice": validator.STATE_SLICE,
        "provider": "givemeanode",
        "provider_project": "project-v5",
        "node_type": "h100-1",
        "job_mode": "batch",
        "job_id": "job-1",
        "allocation_id": "alloc-1",
        "node_id": "node-1",
        "start_utc": "2026-08-31T00:00:00Z",
        "stop_utc": "2026-08-31T00:30:00Z",
        "quoted_gpu_usd_per_minute": 0.05,
        "charged_usd": 4.0,
        "hard_usd_ceiling": 100.0,
        "estimated_max_total_usd": 5.0,
        "stop_reason": "completed",
        "launch_manifest_sha256": "b" * 64,
        "container_digest": launch["container_digest"],
    }
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    root_key = Ed25519PrivateKey.generate()
    private_key = Ed25519PrivateKey.generate()
    launch["provider_attestation_key_id"] = "gman-test-key-v5"
    launch["provider_trust_root_id"] = "gman-test-root-v5"
    launch["provider_trust_root_public_key"] = base64.b64encode(
        root_key.public_key().public_bytes_raw()
    ).decode("ascii")
    payload_sha256 = validator.provider_payload_digest(receipt)
    receipt["provider_attestation"] = {
        "issuer": "givemeanode",
        "key_id": launch["provider_attestation_key_id"],
        "algorithm": "ed25519",
        "payload_sha256": payload_sha256,
        "signature": base64.b64encode(
            private_key.sign(validator.canonical({
                key: value for key, value in receipt.items()
                if key not in {"provider_attestation", "receipt_sha256"}
            }))
        ).decode("ascii"),
        "trust_root_id": launch["provider_trust_root_id"],
        "attestation_public_key": base64.b64encode(
            private_key.public_key().public_bytes_raw()
        ).decode("ascii"),
        "key_certificate_signature": base64.b64encode(
            root_key.sign(validator.canonical({
                "issuer": "givemeanode",
                "key_id": launch["provider_attestation_key_id"],
                "algorithm": "ed25519",
                "public_key": base64.b64encode(
                    private_key.public_key().public_bytes_raw()
                ).decode("ascii"),
            }))
        ).decode("ascii"),
    }
    receipt["receipt_sha256"] = validator.digest(receipt, "receipt_sha256")
    path = tmp_path / "provider-receipt.json"
    path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
    assert validator.validate_provider_receipt(path, launch, "b" * 64)["receipt_sha256"] == receipt["receipt_sha256"]


def test_validate_rejects_unexpected_result_directory(tmp_path: Path) -> None:
    result_root = tmp_path / "result"
    result_root.mkdir()
    (result_root / "extra").mkdir()
    (result_root / "result.json").write_text("{}", encoding="utf-8")
    (result_root / "result-receipt.json").write_text("{}", encoding="utf-8")
    (result_root / "provider-receipt.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected directory"):
        validator.validate(
            result_root=result_root,
            raw_root=tmp_path / "raw",
            source_root=tmp_path / "source",
            corpus_root=tmp_path / "corpus",
            model_root=tmp_path / "model",
            launch_manifest=tmp_path / "launch.json",
            repo_root=tmp_path / "repo",
        )


def test_independent_validator_rejects_symlinked_custody_entry(tmp_path: Path) -> None:
    root = tmp_path / "sealed-model"
    root.mkdir()
    target = tmp_path / "outside.bin"
    target.write_bytes(b"outside")
    (root / "linked.bin").symlink_to(target)
    os.chmod(root, 0o700)
    try:
        with pytest.raises(ValueError, match="symlink"):
            validator.require_read_only_tree(root, "model bundle")
    finally:
        (root / "linked.bin").unlink()
        os.chmod(root, 0o755)
        shutil.rmtree(root, ignore_errors=False)
        target.unlink()


def test_independent_validator_requires_complete_pair_rederivation() -> None:
    source = Path(validator.__file__).read_text(encoding="utf-8")
    assert "selected_pair != expected_pair" in source
    assert "selected[\"source_layer\"] !=" not in source


def test_runtime_validator_requires_source_custody_and_exact_model_path() -> None:
    source = Path(validator.__file__).read_text(encoding="utf-8")
    assert "source_bundle(raw_root, source_root)" in source
    assert "model path is not the exact launch-manifest model bundle" in source
    assert '"source_manifest_sha256"' in source


def test_runner_blocks_subprocess_paths_and_requires_every_candidate_reach() -> None:
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "subprocess._fork_exec" in source
    assert 'not all(item["reached"] for item in reach)' in source
