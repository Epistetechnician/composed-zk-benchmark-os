import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "astral_v25_manifest_structure_validator", HERE / "validator_v25.py"
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


@pytest.mark.parametrize("files", [[], "result.json", {"result.json": []}])
def test_validator_rejects_malformed_manifest_files_shape(tmp_path, files):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "result.json").write_text(
        json.dumps({"classification": "NotRunInformationPresenceProbe"})
    )
    (bundle / "manifest.json").write_text(json.dumps({"files": files}))

    with pytest.raises(ValueError):
        VALIDATOR.validate(bundle)
