from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v40r2_real_validator", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_stable_hash_is_key_order_independent() -> None:
    assert MODULE._stable_hash({"b": 2, "a": 1}) == MODULE._stable_hash(
        {"a": 1, "b": 2}
    )


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    report = MODULE.validate(tmp_path, tmp_path / "probe.json", tmp_path)
    assert report == {"valid": False, "errors": ["artifact files missing"]}
