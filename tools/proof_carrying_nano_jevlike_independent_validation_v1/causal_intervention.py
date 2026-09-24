"""Independent validator for causal-intervention record-only bundles.

State slice: proof-carrying-nano-causal-intervention-record-v1.

This module is deliberately self-contained and standard-library-only. It
duplicates the schema, canonical JSON, digest, and Lean-artifact checks rather
than importing the record producer, proof engine, or SQLite store. It validates
declared binding facts; it never treats an effect observation as causal proof.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "proof-carrying-nano-causal-intervention-record-v1"
PROTOCOL_ID = STATE_SLICE
RECORD_SCHEMA = "causal-intervention-record-v1"
OPERATOR_SCHEMA = "exact-activation-replacement-v1"
REPLAY_SCHEMA = "causal-intervention-replay-v1"
SITE = "decoder_block_output"
OPERATOR_TYPE = "replace_token_vector"
OPERATOR_PARAMETERS = frozenset(
    {
        "coefficient",
        "interpolation",
        "source",
        "source_activation_digest",
        "target",
        "target_activation_digest",
    }
)
CONTROL_KINDS = frozenset({"exact_copy", "matched_control", "no_op", "shuffled_donor", "constant_donor"})
CLAIM_TYPE = "causal_intervention_record"
CLAIM_SEMANTICS = "declared_record_binding_only_no_causal_claim"
RECORD_STATUS = "UnreviewedObservation"
ASSESSMENT_STATUS = "SEALED_UNTIL_INDEPENDENT_REVIEW"
BUNDLE_STATUS = "CausalInterventionRecordOnly"
CLAIM_CEILING = "LocalCausalInterventionRecordBindingOnly"
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class IndependentCausalValidationError(ValueError):
    """Raised when a causal record-only bundle violates its contract."""


@dataclass(frozen=True)
class IndependentCausalValidationReport:
    valid: bool
    state_slice: str
    status: str
    assessment_status: str
    claim_ceiling: str
    record_digest: str
    checked_proofs: int
    proof_attempts: int
    checks: tuple[str, ...]


def _fail(message: str) -> None:
    raise IndependentCausalValidationError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise IndependentCausalValidationError("value is not canonical JSON") from exc


def _digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


def _closed(value: Any, keys: set[str] | frozenset[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label} must be an object")
    _require(set(value) == set(keys), f"{label} schema is not closed")
    return value


def _assert_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and SHA256.fullmatch(value) is not None, f"{label} digest is invalid")
    return value


def _require_int(value: Any, label: str, *, minimum: int | None = None) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{label} is invalid")
    if minimum is not None:
        _require(value >= minimum, f"{label} is invalid")


def _decimal_text(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value), f"{label} must be decimal text")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise IndependentCausalValidationError(f"{label} must be decimal text") from exc
    _require(number.is_finite(), f"{label} must be finite")
    _require(str(number) == value, f"{label} is not canonical decimal text")
    return value


def _endpoint(value: Any, label: str) -> dict[str, Any]:
    endpoint = _closed(value, {"activation_digest", "checkpoint_digest", "layer", "site", "token_position"}, label)
    _assert_digest(endpoint["activation_digest"], f"{label} activation")
    _assert_digest(endpoint["checkpoint_digest"], f"{label} checkpoint")
    _require_int(endpoint["layer"], f"{label} layer", minimum=0)
    _require(endpoint["site"] == SITE, f"{label} site is invalid")
    _require_int(endpoint["token_position"], f"{label} token position", minimum=0)
    return endpoint


def _effect(value: Any, label: str) -> dict[str, Any]:
    effect = _closed(value, {"effect_digest", "metric", "units", "value"}, label)
    _require(isinstance(effect["metric"], str) and bool(effect["metric"]), f"{label} metric is invalid")
    _require(isinstance(effect["units"], str) and bool(effect["units"]), f"{label} units are invalid")
    unsigned = {
        "metric": effect["metric"],
        "units": effect["units"],
        "value": _decimal_text(effect["value"], f"{label} value"),
    }
    _assert_digest(effect["effect_digest"], f"{label} digest")
    _require(effect["effect_digest"] == _digest(unsigned), f"{label} digest mismatch")
    return {**unsigned, "effect_digest": effect["effect_digest"]}


def _operator(value: Any, donor: Mapping[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    operator = _closed(value, {"operator_digest", "parameters", "schema", "type"}, "intervention operator")
    _require(operator["schema"] == OPERATOR_SCHEMA, "operator schema is invalid")
    _require(operator["type"] == OPERATOR_TYPE, "operator type is invalid")
    parameters = _closed(operator["parameters"], OPERATOR_PARAMETERS, "operator parameters")
    normalized_parameters = {
        "coefficient": parameters["coefficient"],
        "interpolation": parameters["interpolation"],
        "source": parameters["source"],
        "source_activation_digest": parameters["source_activation_digest"],
        "target": parameters["target"],
        "target_activation_digest": parameters["target_activation_digest"],
    }
    _require(normalized_parameters["coefficient"] == "1", "operator coefficient is not exact")
    _require(normalized_parameters["interpolation"] == "none", "operator interpolation is not exact")
    _require(normalized_parameters["source"] == "donor_activation", "operator source is invalid")
    _require(normalized_parameters["target"] == "target_activation", "operator target is invalid")
    _assert_digest(normalized_parameters["source_activation_digest"], "operator source activation")
    _assert_digest(normalized_parameters["target_activation_digest"], "operator target activation")
    _require(
        normalized_parameters["source_activation_digest"] == donor["activation_digest"],
        "operator donor/source activation binding is invalid",
    )
    _require(
        normalized_parameters["target_activation_digest"] == target["activation_digest"],
        "operator target activation binding is invalid",
    )
    unsigned = {"parameters": normalized_parameters, "schema": OPERATOR_SCHEMA, "type": OPERATOR_TYPE}
    _assert_digest(operator["operator_digest"], "operator")
    _require(operator["operator_digest"] == _digest(unsigned), "operator digest mismatch")
    return {**unsigned, "operator_digest": operator["operator_digest"]}


def _controls(value: Any) -> tuple[list[dict[str, Any]], str]:
    _require(isinstance(value, list) and bool(value), "controls are missing")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_control in enumerate(value):
        control = _closed(raw_control, {"control_id", "effect", "kind", "observation_digest"}, f"control {index}")
        _require(
            isinstance(control["control_id"], str)
            and bool(control["control_id"])
            and control["control_id"] not in seen,
            f"control {index} identity is invalid",
        )
        _require(control["kind"] in CONTROL_KINDS, f"control {index} kind is invalid")
        effect = _effect(control["effect"], f"control {index} effect")
        unsigned = {"control_id": control["control_id"], "effect": effect, "kind": control["kind"]}
        _assert_digest(control["observation_digest"], f"control {index} observation")
        _require(control["observation_digest"] == _digest(unsigned), f"control {index} observation digest mismatch")
        normalized.append({**unsigned, "observation_digest": control["observation_digest"]})
        seen.add(control["control_id"])
    return normalized, _digest(normalized)


def _replay(value: Any) -> dict[str, Any]:
    replay = _closed(
        value,
        {"input_digest", "replay_digest", "replay_index", "replay_seed", "runner_identity", "schema"},
        "replay metadata",
    )
    _assert_digest(replay["input_digest"], "replay input")
    _require_int(replay["replay_index"], "replay index", minimum=0)
    _require_int(replay["replay_seed"], "replay seed", minimum=0)
    _require(isinstance(replay["runner_identity"], str) and bool(replay["runner_identity"]), "replay runner identity is invalid")
    _require(replay["schema"] == REPLAY_SCHEMA, "replay schema is invalid")
    unsigned = {
        "input_digest": replay["input_digest"],
        "replay_index": replay["replay_index"],
        "replay_seed": replay["replay_seed"],
        "runner_identity": replay["runner_identity"],
        "schema": REPLAY_SCHEMA,
    }
    _assert_digest(replay["replay_digest"], "replay")
    _require(replay["replay_digest"] == _digest(unsigned), "replay digest mismatch")
    return {**unsigned, "replay_digest": replay["replay_digest"]}


def _validate_record(value: Any) -> dict[str, Any]:
    record = _closed(
        value,
        {
            "assessment_status", "claim", "controls", "donor", "effect",
            "host_parameter_digest_after", "host_parameter_digest_before", "intervention_operator",
            "nano_identity", "parent_activation_action_digest", "proof_status", "protocol_identity",
            "record_digest", "record_schema", "record_status", "replay", "state_slice", "target", "timestamp",
        },
        "causal intervention record",
    )
    _require(record["state_slice"] == STATE_SLICE and record["protocol_identity"] == PROTOCOL_ID, "causal record identity is invalid")
    _require(record["record_schema"] == RECORD_SCHEMA, "causal record schema is invalid")
    _require(record["record_status"] == RECORD_STATUS, "causal record status is invalid")
    _require(record["assessment_status"] == ASSESSMENT_STATUS, "causal assessment is not review-sealed")
    _require(record["proof_status"] in {"checked", "failed"}, "proof status is invalid")
    _require(isinstance(record["nano_identity"], str) and bool(record["nano_identity"]), "nano identity is invalid")
    _require(isinstance(record["timestamp"], str) and bool(record["timestamp"]), "timestamp is invalid")
    _assert_digest(record["parent_activation_action_digest"], "parent activation action")
    donor = _endpoint(record["donor"], "donor")
    target = _endpoint(record["target"], "target")
    operator = _operator(record["intervention_operator"], donor, target)
    effect = _effect(record["effect"], "effect")
    controls, controls_digest = _controls(record["controls"])
    _assert_digest(record["host_parameter_digest_before"], "host parameter before")
    _assert_digest(record["host_parameter_digest_after"], "host parameter after")
    _require(record["host_parameter_digest_before"] == record["host_parameter_digest_after"], "host parameter digest changed")
    replay = _replay(record["replay"])

    claim = _closed(
        record["claim"],
        {
            "claim_key", "controls_digest", "effect_digest", "host_parameter_digest_after",
            "host_parameter_digest_before", "kind", "operator_digest", "parent_activation_action_digest",
            "semantics", "target_activation_digest", "type",
        },
        "causal record claim",
    )
    _require(claim["type"] == CLAIM_TYPE and claim["kind"] == "observation_record" and claim["semantics"] == CLAIM_SEMANTICS, "causal record claim type is invalid")
    _require(claim["parent_activation_action_digest"] == record["parent_activation_action_digest"], "claim parent activation binding is invalid")
    _require(claim["target_activation_digest"] == target["activation_digest"], "claim target activation binding is invalid")
    _require(claim["operator_digest"] == operator["operator_digest"], "claim operator binding is invalid")
    _require(claim["effect_digest"] == effect["effect_digest"], "claim effect binding is invalid")
    _require(claim["controls_digest"] == controls_digest, "claim controls binding is invalid")
    _require(claim["host_parameter_digest_before"] == record["host_parameter_digest_before"], "claim host parameter-before binding is invalid")
    _require(claim["host_parameter_digest_after"] == record["host_parameter_digest_after"], "claim host parameter-after binding is invalid")
    expected_claim_key = (
        f"{record['parent_activation_action_digest']}:{target['checkpoint_digest']}:{target['layer']}:{target['site']}:{target['token_position']}:{operator['operator_digest']}"
    )
    _require(claim["claim_key"] == expected_claim_key, "causal record claim key is not bound")

    unsigned = {key: value for key, value in record.items() if key != "record_digest"}
    _assert_digest(record["record_digest"], "causal record")
    _require(record["record_digest"] == _digest(unsigned), "causal record digest mismatch")
    return record


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return identifier if identifier and identifier[0].isalpha() else f"claim_{identifier}"


def _checker_environment_identity(project_dir: Path) -> str:
    """Recompute the exact checker-input identities used by ``lake env lean``."""

    digests: list[str] = []
    for filename in ("lean-toolchain", "lake-manifest.json"):
        path = project_dir / filename
        _require(path.is_file() and not path.is_symlink(), f"Lean checker environment file is unavailable: {filename}")
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise IndependentCausalValidationError(f"Lean checker environment cannot be read: {filename}") from exc
        digests.append(f"{filename}=sha256:{hashlib.sha256(content).hexdigest()}")
    return "lake-env-lean;" + ";".join(digests)


def _expected_lean_artifact(record: Mapping[str, Any]) -> tuple[str, str, str]:
    """Duplicate the exact local theorem construction for independent review."""

    theorem_name = _identifier(f"causal_intervention_{record['record_digest'][7:19]}")
    operator = record["intervention_operator"]
    parameters = operator["parameters"]
    claim = record["claim"]
    host_unchanged = record["host_parameter_digest_before"] == record["host_parameter_digest_after"]
    statement = (
        f'NanoInterpCausalInterventionRecord.causalInterventionRecordBinding "{record["state_slice"]}" '
        f'"{record["protocol_identity"]}" "{record["record_schema"]}" '
        f'"{record["claim"]["semantics"]}" "{operator["type"]}" '
        f'"{parameters["interpolation"]}" true "{record["proof_status"]}" '
        f'{str(host_unchanged).lower()} "{record["parent_activation_action_digest"]}" '
        f'"{record["donor"]["activation_digest"]}" "{record["target"]["activation_digest"]}" '
        f'"{record["effect"]["effect_digest"]}" "{claim["controls_digest"]}" '
        f'"{record["record_digest"]}"'
    )
    source = f'''import Std
import NanoInterp.CausalInterventionRecord

namespace NanoInterpCausalInterventionRecordProof

/- State slice: {STATE_SLICE}. -/
def recordDigest : String := "{record["record_digest"]}"

theorem record_digest_bound : recordDigest = "{record["record_digest"]}" := by
  rfl

theorem {_identifier(theorem_name)} : {statement} := by
  simp [NanoInterpCausalInterventionRecord.causalInterventionRecordBinding]

end NanoInterpCausalInterventionRecordProof
'''
    return theorem_name, statement, source


def _check_lean(source: str, project_dir: Path, command: Sequence[str], timeout_seconds: int) -> None:
    _require(bool(command), "Lean command is empty")
    if shutil.which(command[0]) is None:
        _fail(f"Lean checker unavailable: {command[0]}")
    try:
        with tempfile.TemporaryDirectory(prefix="independent-causal-proof-") as directory:
            proof_path = Path(directory) / "causal_record_proof.lean"
            proof_path.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [*command, str(proof_path)], cwd=project_dir,
                capture_output=True, text=True, timeout=timeout_seconds, check=False,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IndependentCausalValidationError(f"Lean checker failed: {exc}") from exc
    if result.returncode != 0:
        _fail("causal record Lean proof artifact did not check independently")


def _validate_proofs(
    value: Any,
    record: Mapping[str, Any],
    *,
    project_dir: Path,
    command: Sequence[str],
    timeout_seconds: int,
    check_lean: bool,
) -> int:
    _require(isinstance(value, list) and bool(value), "causal proof attempts are missing")
    expected_theorem, expected_statement, expected_source = _expected_lean_artifact(record)
    checked = 0
    for raw_proof in value:
        proof = _closed(
            raw_proof,
            {"action_digest", "checker", "checker_version", "diagnostics", "proof_digest", "protocol_identity", "source", "state_slice", "statement", "status", "theorem_name"},
            "causal proof attempt",
        )
        _assert_digest(proof["proof_digest"], "causal proof")
        _require(proof["proof_digest"] == _digest({key: item for key, item in proof.items() if key != "proof_digest"}), "causal proof digest mismatch")
        _assert_digest(proof["action_digest"], "causal proof record")
        _require(proof["action_digest"] == record["record_digest"], "causal proof record binding mismatch")
        _require(proof["state_slice"] == STATE_SLICE and proof["protocol_identity"] == PROTOCOL_ID, "causal proof identity is invalid")
        _require(proof["status"] in {"checked", "failed"}, "causal proof status is invalid")
        _require(isinstance(proof["checker"], str) and bool(proof["checker"]), "causal proof checker metadata is invalid")
        _require(isinstance(proof["checker_version"], str) and bool(proof["checker_version"]), "causal proof checker version metadata is invalid")
        _require(isinstance(proof["theorem_name"], str) and bool(proof["theorem_name"]), "causal proof theorem metadata is invalid")
        _require(isinstance(proof["statement"], str), "causal proof statement metadata is invalid")
        _require(isinstance(proof["source"], str), "causal proof source metadata is invalid")
        _require(isinstance(proof["diagnostics"], list) and all(isinstance(item, str) for item in proof["diagnostics"]), "causal proof diagnostics are invalid")
        if record["proof_status"] == "failed" and proof["status"] == "checked":
            _fail("proof status is inconsistent with checked proof")
        if proof["status"] == "checked":
            checked += 1
            _require(proof["checker"] == "lean-kernel", "checked causal proof checker is invalid")
            _require(
                proof["checker_version"] == _checker_environment_identity(project_dir),
                "checked causal proof checker environment is not bound",
            )
            _require(
                proof["theorem_name"] == expected_theorem
                and proof["statement"] == expected_statement
                and proof["source"] == expected_source,
                "causal proof artifact is not bound to record",
            )
            if check_lean:
                _check_lean(proof["source"], project_dir, command, timeout_seconds)
        else:
            _require(bool(proof["diagnostics"]), "failed causal proof has no diagnostics")
    if record["proof_status"] == "checked":
        _require(checked > 0, "record proof status is checked but no checked proof exists")
    else:
        _require(checked == 0, "record proof status is inconsistent with checked proof")
    return checked


def validate_causal_bundle(
    bundle: Mapping[str, Any],
    *,
    project_dir: Path | None = None,
    command: Sequence[str] = ("lake", "env", "lean"),
    timeout_seconds: int = 30,
    check_lean: bool = True,
) -> IndependentCausalValidationReport:
    """Validate one record-only bundle without using its producer implementation."""

    bundle = _closed(
        bundle,
        {"assessment_status", "bundle_digest", "proofs", "protocol_identity", "record", "state_slice", "status", "summary"},
        "causal bundle",
    )
    _assert_digest(bundle["bundle_digest"], "causal bundle")
    _require(
        bundle["bundle_digest"] == _digest({key: value for key, value in bundle.items() if key != "bundle_digest"}),
        "causal bundle digest mismatch; record digest binding is not current",
    )
    _require(bundle["state_slice"] == STATE_SLICE and bundle["protocol_identity"] == PROTOCOL_ID, "causal bundle identity is invalid")
    _require(bundle["status"] == BUNDLE_STATUS, "causal bundle status is invalid")
    _require(bundle["assessment_status"] == ASSESSMENT_STATUS, "causal bundle assessment status is invalid")
    record = _validate_record(bundle["record"])
    checked = _validate_proofs(
        bundle["proofs"], record,
        project_dir=project_dir or Path(__file__).parents[2] / "formal" / "proof-carrying-nano-interp-v1",
        command=command,
        timeout_seconds=timeout_seconds,
        check_lean=check_lean,
    )
    expected_summary = (
        f"causal_intervention_record at layer {record['target']['layer']} {record['target']['site']} token {record['target']['token_position']}; "
        f"{checked}/{len(bundle['proofs'])} proof attempts kernel-checked."
    )
    _require(bundle["summary"] == expected_summary, "causal bundle summary is not bound")
    return IndependentCausalValidationReport(
        valid=True,
        state_slice=STATE_SLICE,
        status=bundle["status"],
        assessment_status=bundle["assessment_status"],
        claim_ceiling=CLAIM_CEILING,
        record_digest=record["record_digest"],
        checked_proofs=checked,
        proof_attempts=len(bundle["proofs"]),
        checks=("schema", "record_identity", "digest_binding", "operator_syntax", "effect_controls", "replay_binding", "host_parameter_immutability", "proof_status", "lean_proof_binding", "hypothesis_only_seal"),
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_causal_bundle_path(
    path: Path,
    *,
    project_dir: Path | None = None,
    command: Sequence[str] = ("lake", "env", "lean"),
    timeout_seconds: int = 30,
    check_lean: bool = True,
) -> IndependentCausalValidationReport:
    """Load canonical JSON bytes and validate them independently."""

    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), "causal bundle path is invalid")
    raw = path.read_bytes()
    try:
        bundle = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IndependentCausalValidationError("causal bundle is invalid JSON") from exc
    _require(raw == _canonical(bundle), "causal bundle bytes are not canonical")
    return validate_causal_bundle(
        bundle,
        project_dir=project_dir,
        command=command,
        timeout_seconds=timeout_seconds,
        check_lean=check_lean,
    )
