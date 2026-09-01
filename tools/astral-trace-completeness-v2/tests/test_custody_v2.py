"""State slice: astral-trace-completeness-gemma3-end-to-end-v2."""

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import custody_v2


def test_custody_requires_external_owner_only_tree(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    external = tmp_path / "external"
    external.mkdir(mode=0o700)
    for name in custody_v2.SUBROOTS:
        (external / name).mkdir(mode=0o700)
    receipt = custody_v2.validate_root(external, repository)
    assert receipt["valid"] is True
    os.chmod(external / "raw", 0o755)
    receipt = custody_v2.validate_root(external, repository)
    assert receipt["valid"] is False
    assert "subroot:raw" in receipt["errors"]

