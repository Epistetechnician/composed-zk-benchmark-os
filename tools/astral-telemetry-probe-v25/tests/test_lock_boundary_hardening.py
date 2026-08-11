import json
from pathlib import Path

import pytest

from importlib.util import module_from_spec, spec_from_file_location

HERE = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location("astral_v25_lock_boundary_validator", HERE / "validator_v25.py")
assert SPEC is not None
VALIDATOR = module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


def _lock_bundle(root: Path, input_name: str, payload: bytes = b"payload") -> Path:
    root.mkdir()
    payload_path = root / "payload.bin"
    payload_path.write_bytes(payload)
    (root / "configuration-lock.json").write_text(
        json.dumps(
            {
                "assessment_results_absent": True,
                "inputs": {input_name: VALIDATOR.sha(payload_path)},
            }
        )
    )
    return root


@pytest.mark.parametrize("input_name", ["/outside.bin", "../outside.bin", "nested/../../outside.bin"])
def test_validate_lock_rejects_input_path_escape(tmp_path, input_name):
    bundle = _lock_bundle(tmp_path / "bundle", input_name)
    with pytest.raises(ValueError, match="lock input path escapes bundle root"):
        VALIDATOR.validate_lock(bundle)


def test_validate_lock_rejects_symlinked_input_tree(tmp_path):
    bundle = _lock_bundle(tmp_path / "bundle", "payload.bin")
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    payload = bundle / "payload.bin"
    payload.unlink()
    payload.symlink_to(outside)
    with pytest.raises(ValueError, match="symlinked file"):
        VALIDATOR.validate_lock(bundle)


@pytest.mark.parametrize("absent", [False, 1, "true", "false", None])
def test_validate_lock_requires_boolean_true_ordering_marker(tmp_path, absent):
    bundle = _lock_bundle(tmp_path / "bundle", "payload.bin")
    lock = json.loads((bundle / "configuration-lock.json").read_text())
    lock["assessment_results_absent"] = absent
    (bundle / "configuration-lock.json").write_text(json.dumps(lock))

    with pytest.raises(ValueError, match="lock ordering failure"):
        VALIDATOR.validate_lock(bundle)
