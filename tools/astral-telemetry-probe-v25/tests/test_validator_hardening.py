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
