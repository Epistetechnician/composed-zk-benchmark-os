import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "astral_v25_manifest_reserved_name_validator", HERE / "validator_v25.py"
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_validator_rejects_undeclared_nested_manifest_named_file(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = {
        "classification": "NotRunInformationPresenceProbe",
        "confirmation": "NotAuthorized",
        "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C",
        "claim_ceiling": VALIDATOR.CLAIM,
        "assessment_unopened": True,
    }
    (bundle / "result.json").write_text(json.dumps(result))
    (bundle / "qualification.json").write_text(json.dumps({"qualified": False}))
    nested = bundle / "nested"
    nested.mkdir()
    (nested / "manifest.json").write_text("undeclared")
    manifest = {
        "files": {
            "result.json": _sha(bundle / "result.json"),
            "qualification.json": _sha(bundle / "qualification.json"),
        }
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="manifest census mismatch"):
        VALIDATOR.validate(bundle)
