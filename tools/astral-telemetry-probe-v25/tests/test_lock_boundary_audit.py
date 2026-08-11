import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "astral_v25_lock_boundary_audit", HERE / "validator_v25.py"
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lock_bundle(root: Path, input_name: str, input_path: Path) -> Path:
    root.mkdir()
    (root / input_path.name).write_bytes(b"input")
    digest = _sha(root / input_path.name)
    (root / "configuration-lock.json").write_text(
        json.dumps({"assessment_results_absent": True, "inputs": {input_name: digest}})
    )
    return root


@pytest.mark.parametrize("name", ["/outside.json", "../outside.json", "nested/../../outside.json"])
def test_lock_only_rejects_input_path_escape(tmp_path, name):
    bundle = _lock_bundle(tmp_path / "bundle", name, Path("input.json"))
    with pytest.raises(ValueError, match="lock input path escapes bundle root"):
        VALIDATOR.validate_lock(bundle)


def test_lock_only_rejects_symlink_before_digest_use(tmp_path):
    bundle = _lock_bundle(tmp_path / "bundle", "input.json", Path("input.json"))
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"outside")
    input_path = bundle / "input.json"
    input_path.unlink()
    input_path.symlink_to(outside)
    with pytest.raises(ValueError, match="symlinked file"):
        VALIDATOR.validate_lock(bundle)
