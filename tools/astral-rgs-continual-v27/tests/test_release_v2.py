from __future__ import annotations

import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v27_release", HERE / "release_v2.py")
assert SPEC and SPEC.loader
RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE)


def test_manifest_accepts_exact_census_and_hashes(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("b\n", encoding="utf-8")

    RELEASE.write_manifest(tmp_path)

    assert RELEASE.verify_manifest(tmp_path) == []


def test_manifest_rejects_modified_and_undeclared_files(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("a\n", encoding="utf-8")
    RELEASE.write_manifest(tmp_path)
    target.write_text("changed\n", encoding="utf-8")
    (tmp_path / "extra.txt").write_text("extra\n", encoding="utf-8")

    errors = RELEASE.verify_manifest(tmp_path)

    assert "release.file_sha256:a.txt" in errors
    assert "release.file_undeclared:extra.txt" in errors


def test_manifest_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("a\n", encoding="utf-8")
    RELEASE.write_manifest(tmp_path)
    (tmp_path / "link.txt").symlink_to(target)

    errors = RELEASE.verify_manifest(tmp_path)

    assert "release.symlink:link.txt" in errors


def test_tencent_materialization_is_portable_and_survives_source_unlink(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    files = {}
    for name in (
        "source-license",
        "dataset",
        "dataset-license",
        "model",
        "raw",
    ):
        path = source / name
        path.write_text(name + "\n", encoding="utf-8")
        files[name] = path
    packet = {
        "version": "mesh.tencent_clbench_frozen_evaluation.v2",
        "source": {"license_path": str(files["source-license"])},
        "dataset": {
            "path": str(files["dataset"]),
            "license_path": str(files["dataset-license"]),
        },
        "execution": {
            "model_path": str(files["model"]),
            "raw_output_path": str(files["raw"]),
        },
        "grading": {"performed": False},
    }
    release_root = tmp_path / "release"
    target_root = release_root / "evidence/tencent/files"
    target_root.mkdir(parents=True)

    rebound, records = RELEASE._materialize_tencent_packet(
        packet,
        release_root=release_root,
        target_root=target_root,
    )
    files["raw"].unlink()

    assert not Path(rebound["execution"]["raw_output_path"]).is_absolute()
    assert (release_root / rebound["execution"]["raw_output_path"]).is_file()
    assert len(records) == 5
    core = dict(rebound)
    digest = core.pop("packet_sha256")
    assert digest == RELEASE.stable_hash(core)


def test_release_spec_preserves_claim_ceiling() -> None:
    spec = json.loads(RELEASE.RELEASE_SPEC_PATH.read_text(encoding="utf-8"))

    assert spec["claim_boundary"]["immutable_author_development_release"] is True
    assert spec["claim_boundary"]["independent_review"] is False
    assert spec["claim_boundary"]["independent_replication"] is False
    assert spec["claim_boundary"]["continual_learning_solved"] is False
