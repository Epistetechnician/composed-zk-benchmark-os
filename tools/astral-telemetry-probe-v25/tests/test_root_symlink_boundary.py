import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "astral_v25_root_symlink_boundary", HERE / "validator_v25.py"
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_validator_rejects_symlinked_bundle_root_before_reading_manifest(tmp_path):
    real_bundle = tmp_path / "real-bundle"
    real_bundle.mkdir()
    (real_bundle / "manifest.json").write_text(json.dumps({"files": {}}))
    bundle_link = tmp_path / "bundle-link"
    bundle_link.symlink_to(real_bundle, target_is_directory=True)

    with pytest.raises(ValueError, match="symlinked bundle root"):
        VALIDATOR.validate(bundle_link)
