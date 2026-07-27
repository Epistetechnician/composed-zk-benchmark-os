from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v24_release_helpers", ROOT / "release.py")
RELEASE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RELEASE
assert SPEC.loader
SPEC.loader.exec_module(RELEASE)


def test_manifest_round_trip_and_mutation_rejection(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "a.txt").write_text("alpha\n")
    (tmp_path / "nested/b.txt").write_text("beta\n")
    identity = RELEASE.write_manifest(tmp_path, "MANIFEST.sha256")
    state = RELEASE.verify_manifest(tmp_path, "MANIFEST.sha256")
    assert state == {"file_count": 2, "identity": identity}
    (tmp_path / "nested/b.txt").write_text("changed\n")
    with pytest.raises(ValueError, match="digest mismatch"):
        RELEASE.verify_manifest(tmp_path, "MANIFEST.sha256")


def test_manifest_rejects_extra_file_and_symlink(tmp_path):
    (tmp_path / "a.txt").write_text("alpha\n")
    RELEASE.write_manifest(tmp_path, "MANIFEST.sha256")
    (tmp_path / "extra.txt").write_text("extra\n")
    with pytest.raises(ValueError, match="census mismatch"):
        RELEASE.verify_manifest(tmp_path, "MANIFEST.sha256")
    (tmp_path / "extra.txt").unlink()
    (tmp_path / "link.txt").symlink_to(tmp_path / "a.txt")
    with pytest.raises(ValueError, match="symlink forbidden"):
        RELEASE.verify_manifest(tmp_path, "MANIFEST.sha256")


def test_json_manifest_directory_round_trip(tmp_path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    (artifact / "result.json").write_text("{}\n")
    manifest = {"files": {"result.json": RELEASE.sha256(artifact / "result.json")}}
    RELEASE.write_json(artifact / "manifest.json", manifest)
    identity = RELEASE.sha256(artifact / "manifest.json")
    destination = tmp_path / f"astral-v24-{identity}"
    artifact.rename(destination)
    assert RELEASE.verify_json_manifest_directory(
        destination, "manifest.json", "astral-v24", identity
    )["file_count"] == 1


def test_model_inventory_binds_census_bytes_and_digests(tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "weights.bin").write_bytes(b"weights")
    inventory = {
        "files": [
            {
                "path": "weights.bin",
                "bytes": 7,
                "sha256": RELEASE.sha256(model / "weights.bin"),
            }
        ]
    }
    assert RELEASE.verify_model_inventory(model, inventory) == 1
    (model / "weights.bin").write_bytes(b"changed")
    with pytest.raises(ValueError, match="model file mismatch"):
        RELEASE.verify_model_inventory(model, inventory)


def test_release_spec_is_v24_only_and_preserves_external_stops():
    spec = json.loads((ROOT / "release-spec.json").read_text())
    assert spec["artifact_identity"] == "288feb32b4833544d57988a61c9e76f95856777ab4346dea553eee539fcba9c3"
    assert spec["source_commit"] == "de4ac8145ed3e730f9a2ed1495921084a078ab39"
    assert spec["external_states"]["independently_verified"] == "NotRun"
    assert spec["external_states"]["confirmation"] == "NotAuthorized"
    assert spec["external_states"]["stage_0c"] == "Blocked"
