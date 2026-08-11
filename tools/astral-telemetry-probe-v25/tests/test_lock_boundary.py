import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v25_lock_boundary", HERE / "validator_v25.py")
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lock_bundle(root: Path, input_name: str, input_path: Path) -> Path:
    root.mkdir()
    (root / "configuration-lock.json").write_text(
        json.dumps(
            {
                "assessment_results_absent": True,
                "inputs": {input_name: _sha(input_path)},
            }
        )
    )
    return root


@pytest.mark.parametrize("name", ["../outside.json", "/outside.json", "nested/../../outside.json"])
def test_validate_lock_rejects_input_path_escape(tmp_path, name):
    bundle = tmp_path / "bundle"
    source = tmp_path / "source.json"
    source.write_text("source")
    _lock_bundle(bundle, name, source)

    with pytest.raises(ValueError, match="lock input path escapes bundle root"):
        VALIDATOR.validate_lock(bundle)


def test_validate_lock_rejects_symlinked_input_before_hash(tmp_path):
    bundle = tmp_path / "bundle"
    outside = tmp_path / "outside.json"
    outside.write_text("outside")
    input_path = bundle / "input.json"
    bundle.mkdir()
    input_path.symlink_to(outside)
    (bundle / "configuration-lock.json").write_text(
        json.dumps(
            {
                "assessment_results_absent": True,
                "inputs": {"input.json": _sha(outside)},
            }
        )
    )

    with pytest.raises(ValueError, match="symlinked file in bundle"):
        VALIDATOR.validate_lock(bundle)
