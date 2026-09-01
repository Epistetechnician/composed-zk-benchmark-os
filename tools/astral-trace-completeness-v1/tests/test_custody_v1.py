"""State slice: astral-trace-completeness-native-instrument-v1."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import custody_v1
import protocol


def test_repository_local_custody_is_rejected(tmp_path):
    receipt = custody_v1.validate_custody_root(ROOT, ROOT)
    assert receipt["valid"] is False
    assert any(error.startswith("repository_local:") for error in receipt["errors"])


def test_external_owner_only_custody_is_accepted(tmp_path):
    root = tmp_path / "custody"
    root.mkdir()
    (root / "raw").mkdir()
    (root / "aggregate").mkdir()
    os.chmod(root / "raw", 0o700)
    os.chmod(root / "aggregate", 0o700)
    os.chmod(root, 0o700)
    receipt = custody_v1.validate_custody_root(root, ROOT)
    assert receipt["valid"] is True


def test_non_owner_permissions_are_rejected(tmp_path):
    root = tmp_path / "custody"
    root.mkdir()
    (root / "raw").mkdir()
    (root / "aggregate").mkdir()
    os.chmod(root / "raw", 0o700)
    os.chmod(root / "aggregate", 0o700)
    os.chmod(root, 0o755)
    receipt = custody_v1.validate_custody_root(root, ROOT)
    assert receipt["valid"] is False
    assert "root_permissions_not_0700" in receipt["errors"]


def test_expire_raw_deletes_only_files_older_than_fixed_ttl(tmp_path):
    root = tmp_path / "custody"
    raw = root / "raw"
    aggregate = root / "aggregate"
    raw.mkdir(parents=True)
    aggregate.mkdir()
    os.chmod(root, 0o700)
    os.chmod(raw, 0o700)
    os.chmod(aggregate, 0o700)
    old_file = raw / "old.jsonl"
    new_file = raw / "new.jsonl"
    old_file.write_text("old", encoding="utf-8")
    new_file.write_text("new", encoding="utf-8")
    os.utime(old_file, (0, 0))
    result = custody_v1.expire_raw(root, ROOT, now=protocol.RAW_RETENTION_HOURS * 60 * 60 + 1)
    assert result["deleted"] == ["old.jsonl"]
    assert not old_file.exists()
    assert new_file.exists()
