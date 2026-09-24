"""Custody and qualification contract tests.

State slice: proof-carrying-nano-host-activation-boundary-v1.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.proof_carrying_nano_host_activation_boundary_v1.qualification import (
    prepare_checkpoint_custody,
    validate_checkpoint_custody,
)


def test_checkpoint_custody_is_external_owner_only_and_digest_bound(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = tmp_path / "cached-model"
    source.mkdir()
    (source / "config.json").write_text('{"model_type":"llama"}', encoding="utf-8")
    (source / "weights.bin").write_bytes(b"fixed checkpoint bytes")
    custody_root = tmp_path / "custody"

    manifest_path = prepare_checkpoint_custody(
        source,
        custody_root,
        repo_root=repo_root,
    )

    assert manifest_path.parent.stat().st_mode & 0o777 == 0o700
    assert manifest_path.stat().st_mode & 0o777 == 0o400
    manifest = validate_checkpoint_custody(manifest_path, repo_root=repo_root)
    assert manifest["device"] == "cpu"
    assert manifest["network_access"] is False
    assert manifest["files"] == [
        {"path": "config.json", "sha256": manifest["files"][0]["sha256"], "size": 22},
        {"path": "weights.bin", "sha256": manifest["files"][1]["sha256"], "size": 22},
    ]


def test_custody_rejects_checkpoint_source_inside_repository(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = repo_root / "cached-model"
    source.mkdir()
    (source / "config.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="outside the repository"):
        prepare_checkpoint_custody(source, tmp_path / "custody", repo_root=repo_root)


def test_custody_rejects_manifest_tampering(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = tmp_path / "cached-model"
    source.mkdir()
    (source / "config.json").write_text("{}", encoding="utf-8")
    manifest_path = prepare_checkpoint_custody(source, tmp_path / "custody", repo_root=repo_root)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["device"] = "cuda"
    manifest_path.chmod(0o600)
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    manifest_path.chmod(0o400)

    with pytest.raises(ValueError, match="canonical|digest|execution"):
        validate_checkpoint_custody(manifest_path, repo_root=repo_root)
