from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v24_capsule_helpers", ROOT / "capsule.py")
CAPSULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CAPSULE
assert SPEC.loader
SPEC.loader.exec_module(CAPSULE)


def test_capsule_manifest_round_trip_and_mutation_rejection(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "a.txt").write_text("alpha\n")
    (tmp_path / "nested/b.txt").write_text("beta\n")
    identity = CAPSULE.write_manifest(tmp_path, "MANIFEST.sha256")
    assert CAPSULE.verify_manifest(tmp_path, "MANIFEST.sha256") == {
        "file_count": 2,
        "identity": identity,
    }
    (tmp_path / "nested/b.txt").write_text("changed\n")
    with pytest.raises(ValueError, match="digest mismatch"):
        CAPSULE.verify_manifest(tmp_path, "MANIFEST.sha256")


def test_capsule_manifest_rejects_path_traversal_and_symlink(tmp_path):
    (tmp_path / "a.txt").write_text("alpha\n")
    (tmp_path / "MANIFEST.sha256").write_text(
        f"{CAPSULE.sha256(tmp_path / 'a.txt')}  ../a.txt\n"
    )
    with pytest.raises(ValueError, match="invalid manifest row"):
        CAPSULE.verify_manifest(tmp_path, "MANIFEST.sha256")
    (tmp_path / "MANIFEST.sha256").unlink()
    (tmp_path / "link.txt").symlink_to(tmp_path / "a.txt")
    with pytest.raises(ValueError, match="symlink forbidden"):
        CAPSULE.write_manifest(tmp_path, "MANIFEST.sha256")


def test_runtime_differences_are_explicit():
    expected = {
        "python": "3.14",
        "python_executable_name": "python",
        "platform": "author-os",
        "machine": "arm64",
        "processor": "arm",
        "packages": {"numpy": "2.4.5"},
        "commands": {"git": "author-git"},
    }
    actual = {
        **expected,
        "platform": "reviewer-os",
        "packages": {"numpy": "2.4.6"},
    }
    assert [row["field"] for row in CAPSULE.runtime_differences(expected, actual)] == [
        "platform",
        "packages.numpy",
    ]


def test_review_templates_start_unfilled_and_unresolved():
    for name in (
        "artifact-reproducibility.decision.template.json",
        "scientific-validity.decision.template.json",
    ):
        template = json.loads((ROOT / name).read_text())
        assert template["result"] == "UNFILLED"
        assert template["material_findings_unresolved"] is True
        assert template["evidence"] == []
