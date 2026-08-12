import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v25_validator_hardening", HERE / "validator_v25.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(VALIDATOR)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bundle(root: Path, files: dict[str, bytes] | None = None) -> Path:
    root.mkdir()
    (root / "result.json").write_text(json.dumps({"classification": "NotRunInformationPresenceProbe"}))
    for name, content in (files or {}).items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    manifest_files = {
        str(path.relative_to(root)): _sha(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    (root / "manifest.json").write_text(json.dumps({"files": manifest_files}))
    return root


def _replace_manifest(root: Path, name: str, digest: str) -> None:
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["files"][name] = digest
    (root / "manifest.json").write_text(json.dumps(manifest))


@pytest.mark.parametrize("name", ["/outside.json", "../outside.json", "nested/../../outside.json"])
def test_validator_rejects_manifest_path_escape(tmp_path, name):
    bundle = _bundle(tmp_path / "bundle")
    _replace_manifest(bundle, name, _sha(bundle / "result.json"))
    with pytest.raises(ValueError, match="manifest path escapes bundle root"):
        VALIDATOR.validate(bundle)


def test_validator_rejects_symlinked_bundle_file(tmp_path):
    bundle = _bundle(tmp_path / "bundle", {"payload.json": b"payload"})
    target = bundle / "outside.json"
    target.write_text("outside")
    payload = bundle / "payload.json"
    payload.unlink()
    payload.symlink_to(target)
    manifest = json.loads((bundle / "manifest.json").read_text())
    manifest["files"]["payload.json"] = _sha(target)
    (bundle / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="symlinked file"):
        VALIDATOR.validate(bundle)


def test_validate_lock_reports_malformed_json_as_bundle_error(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "configuration-lock.json").write_text("{")

    with pytest.raises(ValueError, match="configuration lock is not valid JSON"):
        VALIDATOR.validate_lock(bundle)


def test_validate_lock_rejects_duplicate_json_keys(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "configuration-lock.json").write_text(
        '{"assessment_results_absent": true, "assessment_results_absent": false, "inputs": {}}'
    )

    with pytest.raises(ValueError, match="configuration lock is not valid JSON"):
        VALIDATOR.validate_lock(bundle)


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        ("configuration-lock.json", "configuration lock is not valid JSON"),
        ("manifest.json", "manifest is not valid JSON"),
        ("result.json", "result is not valid JSON"),
    ],
)
def test_validator_rejects_nonstandard_json_constants(tmp_path, document, expected):
    bundle = tmp_path / document.replace(".json", "")
    bundle.mkdir()
    (bundle / document).write_text('{"value": NaN}')
    if document == "result.json":
        (bundle / "manifest.json").write_text(
            json.dumps({"files": {"result.json": _sha(bundle / document)}})
        )

    with pytest.raises(ValueError, match=expected):
        if document == "configuration-lock.json":
            VALIDATOR.validate_lock(bundle)
        else:
            VALIDATOR.validate(bundle)


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        ("manifest.json", "manifest is not valid JSON"),
        ("result.json", "result is not valid JSON"),
        ("qualification.json", "qualification is not valid JSON"),
        ("behavioral-effect.json", "behavioral effect is not valid JSON"),
    ],
)
def test_validate_reports_malformed_classification_documents_as_bundle_errors(
    tmp_path, document, expected
):
    if document == "qualification.json":
        result = {
            "classification": "NotRunInformationPresenceProbe",
            "confirmation": "NotAuthorized",
            "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C",
            "claim_ceiling": "LocalDevelopmentPrivilegedTelemetryInformationPresence",
            "assessment_unopened": True,
        }
        bundle = _bundle(tmp_path / "bundle", {document: b'{"qualified": true}'})
        (bundle / "result.json").write_text(json.dumps(result))
    elif document == "behavioral-effect.json":
        bundle = _bundle(tmp_path / "bundle", {document: b"[]"})
        (bundle / "result.json").write_text(json.dumps(_silent_result()))
    else:
        bundle = _bundle(tmp_path / "bundle")
    (bundle / document).write_text("{")
    if document == "manifest.json":
        pass
    else:
        manifest = json.loads((bundle / "manifest.json").read_text())
        manifest["files"][document] = _sha(bundle / document)
        if document in {"qualification.json", "behavioral-effect.json"}:
            manifest["files"]["result.json"] = _sha(bundle / "result.json")
        (bundle / "manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match=expected):
        VALIDATOR.validate(bundle)


@pytest.mark.parametrize("field,value", [
    ("confirmation", "Authorized"),
    ("stage_0c", "Confirmed"),
    ("stage_1", "Authorized"),
    ("claim_ceiling", "UnboundedClaim"),
])
def test_validator_rejects_tampered_result_boundary(tmp_path, field, value):
    result = {
        "classification": "NotRunInformationPresenceProbe",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": "LocalDevelopmentPrivilegedTelemetryInformationPresence",
        "assessment_unopened": True,
    }
    qualification = {"qualified": False}
    bundle = _bundle(tmp_path / "bundle", {
        "qualification.json": json.dumps(qualification).encode(),
    })
    (bundle / "result.json").write_text(json.dumps({**result, field: value}))
    manifest = json.loads((bundle / "manifest.json").read_text())
    manifest["files"]["result.json"] = _sha(bundle / "result.json")
    (bundle / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=f"result boundary mismatch: {field}"):
        VALIDATOR.validate(bundle)


@pytest.mark.parametrize("value", [0, 1, "false", None])
def test_validator_rejects_non_boolean_assessment_order_marker(tmp_path, value):
    result = {
        "classification": "NotRunInformationPresenceProbe",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": "LocalDevelopmentPrivilegedTelemetryInformationPresence",
        "assessment_unopened": value,
    }
    bundle = _bundle(tmp_path / "bundle", {
        "qualification.json": json.dumps({"qualified": False}).encode(),
    })
    (bundle / "result.json").write_text(json.dumps(result))
    manifest = json.loads((bundle / "manifest.json").read_text())
    manifest["files"]["result.json"] = _sha(bundle / "result.json")
    (bundle / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="result boundary mismatch: assessment_unopened"):
        VALIDATOR.validate(bundle)


def test_validator_rejects_missing_fork_required_fields():
    with pytest.raises(ValueError, match="fork result missing required fields: bootstrap"):
        VALIDATOR._validate_fork({
            "assessment_unopened": False,
            "probe_accuracy": 0.9,
            "self_report_accuracy": 0.8,
            "fork_margin_observed": 0.1,
        })


def test_validator_rejects_non_object_fork_bootstrap():
    with pytest.raises(ValueError, match="fork bootstrap must be an object"):
        VALIDATOR._validate_fork({
            "assessment_unopened": False,
            "probe_accuracy": 0.9,
            "self_report_accuracy": 0.8,
            "fork_margin_observed": 0.1,
            "bootstrap": [],
        })


def test_validator_rejects_incomplete_fork_bootstrap():
    with pytest.raises(
        ValueError,
        match="fork bootstrap missing required fields: lower_95, upper_95",
    ):
        VALIDATOR._validate_fork({
            "assessment_unopened": False,
            "probe_accuracy": 0.9,
            "self_report_accuracy": 0.8,
            "fork_margin_observed": 0.1,
            "bootstrap": {"mean_over_chance": 0.4},
        })


def test_validator_rejects_missing_or_non_boolean_qualification(tmp_path):
    result = {
        "classification": "NotRunInformationPresenceProbe",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C",
        "claim_ceiling": "LocalDevelopmentPrivilegedTelemetryInformationPresence",
        "assessment_unopened": True,
    }
    for qualification, message in (({}, "qualification missing qualified"),
                                   ({"qualified": "false"}, "qualification qualified must be boolean")):
        bundle = _bundle(tmp_path / message.replace(" ", "-"), {
            "qualification.json": json.dumps(qualification).encode(),
        })
        (bundle / "result.json").write_text(json.dumps(result))
        manifest = json.loads((bundle / "manifest.json").read_text())
        manifest["files"]["result.json"] = _sha(bundle / "result.json")
        (bundle / "manifest.json").write_text(json.dumps(manifest))
        with pytest.raises(ValueError, match=message):
            VALIDATOR.validate(bundle)


def _silent_result():
    return {
        "classification": "ProbeTargetBehaviorallySilent",
        "confirmation": "NotAuthorized",
        "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C",
        "claim_ceiling": "LocalDevelopmentPrivilegedTelemetryInformationPresence",
        "assessment_unopened": True,
        "selected_configuration": {"site": 3, "strength": 0.1},
        "selected_behavioral_effect": {"site": 3, "strength": 0.1, "silent": True},
    }


@pytest.mark.parametrize(
    ("behavioral", "message"),
    [
        ({"site": 3}, "behavioral effect must be an array"),
        ([None], "behavioral effect entry 0 must be an object"),
        ([{"site": 3, "strength": 0.1}], "behavioral effect entry 0 missing fields: silent"),
        ([{"site": 3, "strength": 0.1, "silent": "yes"}], "behavioral effect entry 0 silent must be boolean"),
    ],
)
def test_validator_rejects_malformed_silent_behavioral_effect(tmp_path, behavioral, message):
    bundle = _bundle(
        tmp_path / "bundle",
        {"behavioral-effect.json": json.dumps(behavioral).encode()},
    )
    (bundle / "result.json").write_text(json.dumps(_silent_result()))
    manifest = json.loads((bundle / "manifest.json").read_text())
    manifest["files"]["result.json"] = _sha(bundle / "result.json")
    (bundle / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=message):
        VALIDATOR.validate(bundle)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("selected_configuration", "silent stop missing selected configuration"),
        ("selected_behavioral_effect", "silent stop missing selected behavioral effect"),
    ],
)
def test_validator_rejects_missing_silent_result_records(tmp_path, field, message):
    result = _silent_result()
    del result[field]
    bundle = _bundle(
        tmp_path / field,
        {"behavioral-effect.json": json.dumps([{"site": 3, "strength": 0.1, "silent": True}]).encode()},
    )
    (bundle / "result.json").write_text(json.dumps(result))
    manifest = json.loads((bundle / "manifest.json").read_text())
    manifest["files"]["result.json"] = _sha(bundle / "result.json")
    (bundle / "manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match=message):
        VALIDATOR.validate(bundle)
