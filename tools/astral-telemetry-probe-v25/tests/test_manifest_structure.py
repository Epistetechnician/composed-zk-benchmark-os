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


@pytest.mark.parametrize("digest", [None, 0, "", "0" * 63, "0" * 64 + "0", "A" * 64])
def test_validate_lock_rejects_malformed_input_digest(tmp_path, digest):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "payload.bin").write_bytes(b"payload")
    (bundle / "configuration-lock.json").write_text(
        json.dumps({"assessment_results_absent": True, "inputs": {"payload.bin": digest}})
    )

    with pytest.raises(ValueError, match="lock input payload.bin digest must be 64 lowercase hex characters"):
        VALIDATOR.validate_lock(bundle)


@pytest.mark.parametrize("digest", [None, 0, "", "0" * 63, "0" * 64 + "0", "A" * 64])
def test_validate_rejects_malformed_manifest_digest(tmp_path, digest):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = bundle / "result.json"
    result.write_text(json.dumps({"classification": "NotRunInformationPresenceProbe"}))
    (bundle / "manifest.json").write_text(json.dumps({"files": {"result.json": digest}}))

    with pytest.raises(ValueError, match="manifest result.json digest must be 64 lowercase hex characters"):
        VALIDATOR.validate(bundle)


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


def _result_boundary(classification):
    return {
        "classification": classification,
        "confirmation": "NotAuthorized",
        "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C",
        "claim_ceiling": "LocalDevelopmentPrivilegedTelemetryInformationPresence",
        "assessment_unopened": True,
    }


def test_validator_reports_missing_qualification_before_json_decode(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = bundle / "result.json"
    result.write_text(json.dumps(_result_boundary("NotRunInformationPresenceProbe")))
    (bundle / "manifest.json").write_text(
        json.dumps({"files": {"result.json": VALIDATOR.sha(result)}})
    )

    with pytest.raises(ValueError, match="qualification missing: qualification.json"):
        VALIDATOR.validate(bundle)


def test_validator_reports_missing_behavioral_effect_before_json_decode(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    result = bundle / "result.json"
    result.write_text(json.dumps(_result_boundary("ProbeTargetBehaviorallySilent")))
    (bundle / "manifest.json").write_text(
        json.dumps({"files": {"result.json": VALIDATOR.sha(result)}})
    )

    with pytest.raises(ValueError, match="behavioral effect missing: behavioral-effect.json"):
        VALIDATOR.validate(bundle)
