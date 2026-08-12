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


@pytest.mark.parametrize("files", [None, [], "result.json", {"result.json": []}])
def test_validator_rejects_malformed_manifest_files_shape(tmp_path, files):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "result.json").write_text(
        json.dumps({"classification": "NotRunInformationPresenceProbe"})
    )
    (bundle / "manifest.json").write_text(json.dumps({"files": files}))

    with pytest.raises(ValueError):
        VALIDATOR.validate(bundle)


@pytest.mark.parametrize("document", [None, [], "manifest"])
def test_validator_rejects_non_object_manifest_document(tmp_path, document):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="manifest must be an object"):
        VALIDATOR.validate(bundle)


@pytest.mark.parametrize("document", [None, [], "result"])
def test_validator_rejects_non_object_result_document(tmp_path, document):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = bundle / "result.json"
    result.write_text(json.dumps(document))
    (bundle / "manifest.json").write_text(
        json.dumps({"files": {"result.json": VALIDATOR.sha(result)}})
    )
    with pytest.raises(ValueError, match="result must be an object"):
        VALIDATOR.validate(bundle)


@pytest.mark.parametrize("inputs", [None, [], "payload.bin"])
def test_validate_lock_rejects_malformed_inputs_shape(tmp_path, inputs):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "configuration-lock.json").write_text(
        json.dumps({"assessment_results_absent": True, "inputs": inputs})
    )

    with pytest.raises(ValueError, match="lock inputs must be an object"):
        VALIDATOR.validate_lock(bundle)


def test_validate_lock_rejects_missing_ordering_marker(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "configuration-lock.json").write_text(json.dumps({"inputs": {}}))

    with pytest.raises(ValueError, match="configuration lock missing assessment_results_absent"):
        VALIDATOR.validate_lock(bundle)


def test_validate_lock_rejects_missing_inputs(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "configuration-lock.json").write_text(
        json.dumps({"assessment_results_absent": True})
    )

    with pytest.raises(ValueError, match="configuration lock missing inputs"):
        VALIDATOR.validate_lock(bundle)


@pytest.mark.parametrize("document", [None, [], "lock"])
def test_validate_lock_rejects_non_object_lock_document(tmp_path, document):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "configuration-lock.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="configuration lock must be an object"):
        VALIDATOR.validate_lock(bundle)


def test_validator_rejects_manifest_missing_files(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(json.dumps({}))

    with pytest.raises(ValueError, match="manifest missing files"):
        VALIDATOR.validate(bundle)


def test_validator_reports_missing_manifest_before_json_decode(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(ValueError, match="manifest missing: manifest.json"):
        VALIDATOR.validate(bundle)


def test_validator_reports_missing_result_before_json_decode(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(json.dumps({"files": {}}))

    with pytest.raises(ValueError, match="result missing: result.json"):
        VALIDATOR.validate(bundle)


def test_validate_lock_reports_missing_lock_before_json_decode(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(ValueError, match="configuration lock missing: configuration-lock.json"):
        VALIDATOR.validate_lock(bundle)
