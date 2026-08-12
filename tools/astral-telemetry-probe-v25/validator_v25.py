#!/usr/bin/env python3
"""Independent V25 artifact validator."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

FIT_PROBE_GATE = 0.70
ASSESS_PROBE_GATE = 0.75
ASSESS_CHANCE_FLOOR = 0.5
FORK_MARGIN = 0.15
CLAIM = "LocalDevelopmentPrivilegedTelemetryInformationPresence"
STOP_CLASSIFICATIONS = {
    "NotRunInformationPresenceProbe",
    "ProbeTargetBehaviorallySilent",
    "ProbeControlFloorViolation",
}
FORK_CLASSIFICATIONS = {
    "InformationPresenceReportGapObserved",
    "InformationPresenceParityObserved",
    "InformationPresenceNoCandidate",
}
KNOWN_CLASSIFICATIONS = STOP_CLASSIFICATIONS | FORK_CLASSIFICATIONS


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _require_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} digest must be 64 lowercase hex characters")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} digest must be 64 lowercase hex characters")
    return value


def _bundle_path(root: Path, name: str, label: str) -> Path:
    """Resolve a declared bundle path without allowing root escape."""
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError(f"{label} path escapes bundle root: {name!r}")
    parts = Path(name).parts
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"{label} path escapes bundle root: {name!r}")
    bundle_root = root.resolve()
    candidate = (root / name).resolve(strict=False)
    try:
        candidate.relative_to(bundle_root)
    except ValueError as exc:
        raise ValueError(f"{label} path escapes bundle root: {name!r}") from exc
    return candidate


def _reject_symlinks(root: Path) -> None:
    if root.is_symlink():
        raise ValueError("symlinked bundle root")
    if not root.is_dir():
        raise ValueError("bundle root is not a directory")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlinked file in bundle: {path.relative_to(root)}")


def _required_file(root: Path, name: str, label: str) -> Path:
    path = root / name
    if not path.is_file():
        raise ValueError(f"{label} missing: {name}")
    return path


def _read_json(path: Path, label: str) -> Any:
    def reject_nonstandard_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        document: dict[str, Any] = {}
        for key, value in pairs:
            if key in document:
                raise ValueError(f"duplicate JSON key: {key}")
            document[key] = value
        return document

    try:
        return json.loads(
            path.read_text(),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonstandard_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{label} is not valid JSON: {path.name}") from exc


def validate_lock(root: Path) -> dict:
    _reject_symlinks(root)
    if (root / "assessment-results.json").exists():
        raise ValueError("assessment exists before lock validation")
    lock = _read_json(
        _required_file(root, "configuration-lock.json", "configuration lock"),
        "configuration lock",
    )
    if not isinstance(lock, dict):
        raise ValueError("configuration lock must be an object")
    if "assessment_results_absent" not in lock:
        raise ValueError("configuration lock missing assessment_results_absent")
    if lock["assessment_results_absent"] is not True:
        raise ValueError("lock ordering failure")
    if "inputs" not in lock:
        raise ValueError("configuration lock missing inputs")
    inputs = lock["inputs"]
    if not isinstance(inputs, dict):
        raise ValueError("lock inputs must be an object")
    for name, expected in inputs.items():
        path = _bundle_path(root, name, "lock input")
        if not path.is_file():
            raise ValueError(f"lock input missing: {name}")
        if sha(path) != _require_digest(expected, f"lock input {name}"):
            raise ValueError(f"lock digest mismatch: {name}")
    return {"lock_valid": True, "configuration_lock_sha256": sha(root / "configuration-lock.json")}


def _validate_silent(root: Path, result: dict) -> None:
    behavioral = _read_json(
        _required_file(root, "behavioral-effect.json", "behavioral effect"),
        "behavioral effect",
    )
    if not isinstance(behavioral, list):
        raise ValueError("behavioral effect must be an array")
    for index, entry in enumerate(behavioral):
        if not isinstance(entry, dict):
            raise ValueError(f"behavioral effect entry {index} must be an object")
        missing = sorted({"site", "strength", "silent"} - entry.keys())
        if missing:
            raise ValueError(
                f"behavioral effect entry {index} missing fields: {', '.join(missing)}"
            )
        if not isinstance(entry["silent"], bool):
            raise ValueError(f"behavioral effect entry {index} silent must be boolean")
    selected = result.get("selected_configuration")
    if not isinstance(selected, dict):
        raise ValueError("silent stop missing selected configuration")
    if "site" not in selected or "strength" not in selected:
        raise ValueError("silent stop selected configuration missing site or strength")
    cell = next(
        (entry for entry in behavioral
         if entry["site"] == selected["site"] and entry["strength"] == selected["strength"]),
        None,
    )
    if cell is None or not cell["silent"]:
        raise ValueError("silent stop without a silent selected cell")
    selected_effect = result.get("selected_behavioral_effect")
    if not isinstance(selected_effect, dict):
        raise ValueError("silent stop missing selected behavioral effect")
    if cell != selected_effect:
        raise ValueError("silent stop effect record mismatch")


def _validate_fork(result: dict) -> None:
    if result.get("assessment_unopened") is True:
        raise ValueError("fork classification has assessment marked unopened")
    required = {
        "probe_accuracy",
        "self_report_accuracy",
        "fork_margin_observed",
        "bootstrap",
    }
    missing = sorted(field for field in required if field not in result)
    if missing:
        raise ValueError(f"fork result missing required fields: {', '.join(missing)}")
    if not isinstance(result["bootstrap"], dict):
        raise ValueError("fork bootstrap must be an object")
    missing_bootstrap = sorted(
        field for field in ("lower_95", "mean_over_chance", "upper_95")
        if field not in result["bootstrap"]
    )
    if missing_bootstrap:
        raise ValueError(
            "fork bootstrap missing required fields: "
            + ", ".join(missing_bootstrap)
        )
    for field in ("probe_accuracy", "self_report_accuracy", "fork_margin_observed"):
        value = result[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"non-finite fork metric: {field}")
    for field in ("lower_95", "mean_over_chance", "upper_95"):
        value = result["bootstrap"][field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"non-finite bootstrap metric: {field}")
    assessment = result
    probe_pass = (
        assessment["probe_accuracy"] >= ASSESS_PROBE_GATE
        and assessment["bootstrap"]["lower_95"] > ASSESS_CHANCE_FLOOR
    )
    margin = assessment["fork_margin_observed"]
    expected_margin = assessment["probe_accuracy"] - assessment["self_report_accuracy"]
    if abs(margin - expected_margin) > 1e-12:
        raise ValueError("fork margin arithmetic mismatch")
    classification = result["classification"]
    if classification == "InformationPresenceReportGapObserved":
        if not probe_pass or margin < FORK_MARGIN:
            raise ValueError("report gap classification unsupported")
    elif classification == "InformationPresenceParityObserved":
        if not probe_pass or margin >= FORK_MARGIN:
            raise ValueError("parity classification unsupported")
    elif classification == "InformationPresenceNoCandidate":
        if probe_pass:
            raise ValueError("no-candidate classification despite passing probe")


def _validate_result_boundary(result: dict) -> None:
    expected = {
        "confirmation": "NotAuthorized",
        "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C",
        "claim_ceiling": CLAIM,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            raise ValueError(f"result boundary mismatch: {field}")
    if not isinstance(result.get("assessment_unopened"), bool):
        raise ValueError("result boundary mismatch: assessment_unopened")


def validate(root: Path) -> dict:
    _reject_symlinks(root)
    manifest = _read_json(_required_file(root, "manifest.json", "manifest"), "manifest")
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if "files" not in manifest:
        raise ValueError("manifest missing files")
    files = manifest["files"]
    if not isinstance(files, dict):
        raise ValueError("manifest files must be an object")
    actual = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root) != Path("manifest.json")
    }
    for name in files:
        _bundle_path(root, name, "manifest")
    if actual != set(files):
        raise ValueError("manifest census mismatch")
    for name, expected in files.items():
        if sha(_bundle_path(root, name, "manifest")) != _require_digest(
            expected, f"manifest {name}"
        ):
            raise ValueError(f"manifest digest mismatch: {name}")
    result = _read_json(_required_file(root, "result.json", "result"), "result")
    if not isinstance(result, dict):
        raise ValueError("result must be an object")
    classification = result.get("classification")
    if not isinstance(classification, str) or classification not in KNOWN_CLASSIFICATIONS:
        raise ValueError(f"unknown classification: {classification!r}")
    _validate_result_boundary(result)
    if classification in STOP_CLASSIFICATIONS:
        if not result["assessment_unopened"] or (root / "assessment-results.json").exists():
            raise ValueError("qualification stop opened assessment")
    if result["classification"] == "ProbeTargetBehaviorallySilent":
        _validate_silent(root, result)
    if result["classification"] == "ProbeControlFloorViolation":
        violations = result.get("violations")
        if not isinstance(violations, list) or not violations:
            raise ValueError("floor violation stop without violations")
    if result["classification"] in FORK_CLASSIFICATIONS:
        assessment_results = root / "assessment-results.json"
        if not assessment_results.is_file():
            raise ValueError("fork classification without assessment")
        _validate_fork(result)
    if result["classification"] == "NotRunInformationPresenceProbe":
        qualification = _read_json(
            _required_file(root, "qualification.json", "qualification"),
            "qualification",
        )
        if not isinstance(qualification, dict) or "qualified" not in qualification:
            raise ValueError("qualification missing qualified")
        if not isinstance(qualification["qualified"], bool):
            raise ValueError("qualification qualified must be boolean")
        if qualification["qualified"]:
            raise ValueError("stop despite qualified probe")
    return {"valid": True, "classification": result["classification"], "manifest_sha256": sha(root / "manifest.json")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--lock-only", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_lock(args.root) if args.lock_only else validate(args.root)
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
