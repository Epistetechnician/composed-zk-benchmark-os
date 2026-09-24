"""Independent validator extension for read-only host activation bundles.

State slice: proof-carrying-nano-host-activation-boundary-v1.

This module intentionally does not import the activation adapter, proof
engine, or store. Its duplicate implementation is the review boundary for
schema, digest, read-only policy, and Lean proof binding.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "proof-carrying-nano-host-activation-boundary-v1"
PROTOCOL_ID = STATE_SLICE
ACTIVATION_SCHEMA = "host-activation-capture-v1"
HOOK_SCHEMA = "torch-forward-hook-identity-v1"
MUTATION_POLICY_SCHEMA = "read-only-host-mutation-policy-v1"
SITE = "decoder_block_output"
ACTION_STATUS = "ActivationCaptured"
BUNDLE_STATUS = "ActivationCaptureOnly"
CLAIM_TYPE = "host_activation_binding"
CLAIM_SEMANTICS = "declared_host_slice_read_only_activation_capture_v1"
CLAIM_CEILING = "LocalCachedSmallTransformerActivationCaptureOnly"


class IndependentActivationValidationError(ValueError):
    """Raised when an activation bundle violates the independent contract."""


@dataclass(frozen=True)
class IndependentActivationValidationReport:
    valid: bool
    state_slice: str
    status: str
    claim_ceiling: str
    action_digest: str
    checked_proofs: int
    proof_attempts: int
    checks: tuple[str, ...]


def _fail(message: str) -> None:
    raise IndependentActivationValidationError(message)


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
        raise IndependentActivationValidationError("value is not canonical JSON") from exc


def _digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


def _closed(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label} must be an object")
    _require(set(value) == keys, f"{label} schema is not closed")
    return value


def _assert_digest(value: Any, label: str) -> None:
    _require(isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None, f"{label} digest is invalid")


def _input_digest(input_ids: Sequence[int], attention_mask: Sequence[int], replay_seed: int) -> str:
    return _digest(
        {
            "attention_mask": list(attention_mask),
            "input_ids": list(input_ids),
            "replay_seed": replay_seed,
        }
    )


def _host_slice_digest(action: Mapping[str, Any]) -> str:
    return _digest(
        {
            "host_checkpoint_digest": action["host_checkpoint_digest"],
            "host_runtime_digest": action["host_runtime_digest"],
            "hook_identity": action["hook_identity"],
            "layer": action["layer"],
            "mutation_policy": action["mutation_policy"],
            "replay_seed": action["replay_seed"],
            "site": action["site"],
            "token_position": action["token_position"],
        }
    )


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return identifier if identifier and identifier[0].isalpha() else f"claim_{identifier}"


def _expected_lean_artifact(action: Mapping[str, Any]) -> tuple[str, str, str]:
    theorem_name = _identifier(f"host_activation_{action['action_digest'][7:19]}")
    outputs = action["outputs"]
    statement = (
        f'readOnlyActivationBinding true true "{outputs["activation_digest"]}" '
        f'"{outputs["parameter_digest_before"]}" "{outputs["parameter_digest_after"]}"'
    )
    source = f'''import Std

namespace NanoInterpHostActivation

/- State slice: {STATE_SLICE}. -/
def readOnlyActivationBinding (hookReached parametersUnchanged : Bool)
    (activationDigest parameterDigestBefore parameterDigestAfter : String) : Prop :=
  hookReached = true ∧ parametersUnchanged = true ∧ activationDigest ≠ "" ∧
    parameterDigestBefore = parameterDigestAfter

def actionDigest : String := "{action["action_digest"]}"

theorem action_digest_bound : actionDigest = "{action["action_digest"]}" := by
  rfl

theorem {theorem_name} : {statement} := by
  simp [readOnlyActivationBinding]

end NanoInterpHostActivation
'''
    return theorem_name, statement, source


def _check_lean(source: str, project_dir: Path, command: Sequence[str], timeout_seconds: int) -> None:
    _require(bool(command), "Lean command is empty")
    if shutil.which(command[0]) is None:
        _fail(f"Lean checker unavailable: {command[0]}")
    try:
        with tempfile.TemporaryDirectory(prefix="independent-host-activation-proof-") as directory:
            proof_path = Path(directory) / "activation_bundle_proof.lean"
            proof_path.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [*command, str(proof_path)],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IndependentActivationValidationError(f"Lean checker failed: {exc}") from exc
    if result.returncode != 0:
        _fail("activation Lean proof artifact did not check independently")


def _validate_action(action: Any) -> None:
    action = _closed(
        action,
        {
            "activation_schema", "action_digest", "action_version", "claim", "host_checkpoint_digest", "host_runtime_digest",
            "hook_identity", "inputs", "layer", "mutation_policy", "nano_identity", "outputs",
            "protocol_identity", "replay_seed", "site", "state_slice", "timestamp", "token_position",
        },
        "activation action",
    )
    _assert_digest(action["action_digest"], "activation action")
    _require(action["action_digest"] == _digest({key: value for key, value in action.items() if key != "action_digest"}), "activation action digest mismatch")
    _require(action["state_slice"] == STATE_SLICE and action["protocol_identity"] == PROTOCOL_ID, "activation action identity is invalid")
    _require(action["activation_schema"] == ACTIVATION_SCHEMA, "activation schema is invalid")
    _require(isinstance(action["action_version"], int) and not isinstance(action["action_version"], bool) and action["action_version"] >= 1, "activation action version is invalid")
    _require(isinstance(action["timestamp"], str) and bool(action["timestamp"]), "activation timestamp is invalid")
    _assert_digest(action["host_checkpoint_digest"], "host checkpoint")
    _assert_digest(action["host_runtime_digest"], "host runtime")
    _require(isinstance(action["nano_identity"], str) and bool(action["nano_identity"]), "activation nano identity is invalid")
    _require(isinstance(action["layer"], int) and not isinstance(action["layer"], bool) and action["layer"] >= 0, "activation layer is invalid")
    _require(action["site"] == SITE, "activation site is invalid")
    _require(isinstance(action["token_position"], int) and not isinstance(action["token_position"], bool) and action["token_position"] >= 0, "activation token position is invalid")
    _require(isinstance(action["replay_seed"], int) and not isinstance(action["replay_seed"], bool), "activation replay seed is invalid")

    hook = _closed(action["hook_identity"], {"capture_point", "module_path", "read_only", "registration", "schema"}, "hook identity")
    _require(hook == {
        "capture_point": "module_output",
        "module_path": f"model.layers.{action['layer']}",
        "read_only": True,
        "registration": "register_forward_hook",
        "schema": HOOK_SCHEMA,
    }, "hook identity is not bound to layer or read-only capture")
    policy = _closed(action["mutation_policy"], {"adapter_mode", "activation_mutation", "allow_forward_hooks", "host_parameter_mutation", "schema"}, "mutation policy")
    _require(policy == {
        "adapter_mode": "read_only",
        "activation_mutation": False,
        "allow_forward_hooks": True,
        "host_parameter_mutation": False,
        "schema": MUTATION_POLICY_SCHEMA,
    }, "mutation policy is not read-only")

    inputs = _closed(action["inputs"], {"attention_mask", "input_digest", "input_ids", "replay_seed"}, "activation inputs")
    _require(isinstance(inputs["input_ids"], list) and bool(inputs["input_ids"]), "activation input ids are invalid")
    _require(all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in inputs["input_ids"]), "activation input ids are invalid")
    _require(isinstance(inputs["attention_mask"], list) and len(inputs["attention_mask"]) == len(inputs["input_ids"]), "activation attention mask is invalid")
    _require(all(value in (0, 1) for value in inputs["attention_mask"]), "activation attention mask is invalid")
    _require(inputs["replay_seed"] == action["replay_seed"], "activation replay seed binding is invalid")
    _require(inputs["input_digest"] == _input_digest(inputs["input_ids"], inputs["attention_mask"], inputs["replay_seed"]), "activation input digest mismatch")
    _assert_digest(inputs["input_digest"], "activation input")

    outputs = _closed(action["outputs"], {"activation_digest", "activation_dtype", "activation_shape", "hook_reached", "parameter_digest_after", "parameter_digest_before", "status"}, "activation outputs")
    _require(outputs["status"] == ACTION_STATUS and outputs["hook_reached"] is True, "activation hook was not reached")
    _assert_digest(outputs["activation_digest"], "activation")
    _require(isinstance(outputs["activation_dtype"], str) and outputs["activation_dtype"] == "torch.float32", "activation dtype is invalid")
    _require(isinstance(outputs["activation_shape"], list) and outputs["activation_shape"] and all(isinstance(value, int) and value > 0 for value in outputs["activation_shape"]), "activation shape is invalid")
    _assert_digest(outputs["parameter_digest_before"], "parameter before")
    _assert_digest(outputs["parameter_digest_after"], "parameter after")
    _require(outputs["parameter_digest_before"] == outputs["parameter_digest_after"], "host parameter digest changed")
    _require(outputs["activation_digest"] == action["claim"]["activation_digest"], "activation claim digest binding is invalid")

    claim = _closed(action["claim"], {"activation_digest", "claim_key", "host_slice_digest", "kind", "layer", "parameter_digest_after", "parameter_digest_before", "semantics", "site", "token_position", "type"}, "activation claim")
    _require(claim["type"] == CLAIM_TYPE and claim["kind"] == "activation" and claim["semantics"] == CLAIM_SEMANTICS, "activation claim type is invalid")
    _require(claim["layer"] == action["layer"] and claim["site"] == action["site"] and claim["token_position"] == action["token_position"], "activation claim location binding is invalid")
    _require(claim["parameter_digest_before"] == outputs["parameter_digest_before"] and claim["parameter_digest_after"] == outputs["parameter_digest_after"], "activation claim parameter binding is invalid")
    _require(claim["host_slice_digest"] == _host_slice_digest(action), "activation host-slice digest mismatch")
    _assert_digest(claim["host_slice_digest"], "activation host slice")
    _require(claim["claim_key"] == f"{action['host_checkpoint_digest']}:{action['layer']}:{action['site']}:{action['token_position']}:{outputs['activation_digest']}", "activation claim key is not bound")


def _validate_proofs(proofs: Any, action: Mapping[str, Any], *, project_dir: Path, command: Sequence[str], timeout_seconds: int, check_lean: bool) -> int:
    _require(isinstance(proofs, list) and bool(proofs), "activation proof attempts are missing")
    expected_theorem, expected_statement, expected_source = _expected_lean_artifact(action)
    checked = 0
    for proof in proofs:
        proof = _closed(proof, {"action_digest", "checker", "checker_version", "diagnostics", "proof_digest", "protocol_identity", "source", "state_slice", "statement", "status", "theorem_name"}, "activation proof")
        _assert_digest(proof["proof_digest"], "activation proof")
        _require(proof["proof_digest"] == _digest({key: value for key, value in proof.items() if key != "proof_digest"}), "activation proof digest mismatch")
        _require(proof["action_digest"] == action["action_digest"], "activation proof action binding mismatch")
        _require(proof["state_slice"] == STATE_SLICE and proof["protocol_identity"] == PROTOCOL_ID, "activation proof identity is invalid")
        _require(proof["status"] in {"checked", "failed"}, "activation proof status is invalid")
        _require(isinstance(proof["diagnostics"], list) and all(isinstance(item, str) for item in proof["diagnostics"]), "activation proof diagnostics are invalid")
        if proof["status"] == "checked":
            checked += 1
            _require(proof["checker"] == "lean-kernel", "checked activation proof checker is invalid")
            _require(proof["theorem_name"] == expected_theorem and proof["statement"] == expected_statement and proof["source"] == expected_source, "activation proof artifact is not bound to action")
            if check_lean:
                _check_lean(proof["source"], project_dir, command, timeout_seconds)
        else:
            _require(bool(proof["diagnostics"]), "failed activation proof has no diagnostics")
    return checked


def validate_activation_bundle(
    bundle: Mapping[str, Any],
    *,
    project_dir: Path | None = None,
    command: Sequence[str] = ("lake", "env", "lean"),
    timeout_seconds: int = 30,
    check_lean: bool = True,
) -> IndependentActivationValidationReport:
    """Validate an activation bundle without using its producer implementation."""

    bundle = _closed(bundle, {"action", "bundle_digest", "proofs", "protocol_identity", "state_slice", "status", "summary"}, "activation bundle")
    _assert_digest(bundle["bundle_digest"], "activation bundle")
    _require(bundle["bundle_digest"] == _digest({key: value for key, value in bundle.items() if key != "bundle_digest"}), "activation bundle digest mismatch")
    _require(bundle["state_slice"] == STATE_SLICE and bundle["protocol_identity"] == PROTOCOL_ID, "activation bundle identity is invalid")
    _require(bundle["status"] == BUNDLE_STATUS, "activation bundle status is invalid")
    _validate_action(bundle["action"])
    checked = _validate_proofs(
        bundle["proofs"],
        bundle["action"],
        project_dir=project_dir or Path(__file__).parents[2] / "formal" / "proof-carrying-nano-interp-v1",
        command=command,
        timeout_seconds=timeout_seconds,
        check_lean=check_lean,
    )
    action = bundle["action"]
    expected_summary = (
        f"host_activation_capture at layer {action['layer']} {action['site']} token {action['token_position']}; "
        f"{checked}/{len(bundle['proofs'])} proof attempts kernel-checked."
    )
    _require(bundle["summary"] == expected_summary, "activation bundle summary is not bound")
    return IndependentActivationValidationReport(
        valid=True,
        state_slice=STATE_SLICE,
        status=bundle["status"],
        claim_ceiling=CLAIM_CEILING,
        action_digest=action["action_digest"],
        checked_proofs=checked,
        proof_attempts=len(bundle["proofs"]),
        checks=("schema", "digests", "hook_binding", "activation_binding", "read_only_policy", "proof_binding"),
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_activation_bundle_path(
    path: Path,
    *,
    project_dir: Path | None = None,
    command: Sequence[str] = ("lake", "env", "lean"),
    timeout_seconds: int = 30,
    check_lean: bool = True,
) -> IndependentActivationValidationReport:
    """Load canonical bundle bytes and validate them independently."""

    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), "activation bundle path is invalid")
    raw = path.read_bytes()
    try:
        bundle = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IndependentActivationValidationError("activation bundle is invalid JSON") from exc
    _require(raw == _canonical(bundle), "activation bundle bytes are not canonical")
    return validate_activation_bundle(
        bundle,
        project_dir=project_dir,
        command=command,
        timeout_seconds=timeout_seconds,
        check_lean=check_lean,
    )
