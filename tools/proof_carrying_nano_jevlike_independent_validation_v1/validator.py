"""Independent closed-world validator for captured Jevlike bundles.

State slice: proof-carrying-nano-jevlike-independent-validation-v1.

This module uses only the Python standard library. It rederives the bundle
schema, digests, fixed-point arithmetic, selected-index binding, and checked
Lean artifact. It does not call the scorer, store, or proof generator.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "proof-carrying-nano-jevlike-independent-validation-v1"
BUNDLE_STATE_SLICE = "proof-carrying-nano-interp-jevlike-adapter-v1"
BUNDLE_PROTOCOL_ID = BUNDLE_STATE_SLICE
CLAIM_CEILING = "LocalExternalJevlikeQuantizedHypothesisRankingOnly"
OPTION_SET_SCHEMA = "hypothesis-option-set-v1"
ADAPTER_CONFIG_SCHEMA = "jevlike-adapter-config-v1"
QUANTIZATION_SCHEMA = "fixed-point-probability-v1"
PINNED_JEVLIKE_REVISION = "94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452"
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")
ROUNDING = {
    "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
    "ROUND_HALF_UP": ROUND_HALF_UP,
}
OPTION_KINDS = frozenset({"feature", "circuit", "intervention"})


class IndependentBundleValidationError(ValueError):
    """Raised when an exported bundle fails independent validation."""


@dataclass(frozen=True)
class IndependentValidationReport:
    """Scalar result of independent bundle validation."""

    valid: bool
    state_slice: str
    bundle_state_slice: str
    status: str
    claim_ceiling: str
    action_digest: str
    checked_proofs: int
    proof_attempts: int
    checks: tuple[str, ...]


def _fail(message: str) -> None:
    raise IndependentBundleValidationError(message)


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
    except (TypeError, ValueError) as error:
        raise IndependentBundleValidationError("value is not canonical JSON") from error


def _digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical(value)).hexdigest()}"


def _assert_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and SHA256.fullmatch(value) is not None, f"{label} digest is invalid")
    return value


def _closed(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    _require(isinstance(value, dict) and set(value) == keys, f"{label} schema is not closed")
    return value


def _decimal_text(value: Any, label: str) -> Decimal:
    _require(isinstance(value, str) and value != "", f"{label} must be decimal text")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as error:
        raise IndependentBundleValidationError(f"{label} must be decimal text") from error
    _require(number.is_finite() and number >= 0, f"{label} must be finite and non-negative")
    _require(str(number) == value, f"{label} is not canonical decimal text")
    return number


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return identifier if identifier and identifier[0].isalpha() else f"claim_{identifier}"


def _expected_lean_artifact(action: Mapping[str, Any], scores: Sequence[int], denominator: int) -> tuple[str, str, str]:
    selected_index = action["outputs"]["selected_index"]
    action_digest = action["action_digest"]
    theorem_name = _identifier(f"jevlike_ranking_{action_digest[7:19]}")
    score_list = "[" + ", ".join(str(score) for score in scores) + "]"
    comparisons = [
        f"nthOrZero {score_list} {index} ≤ nthOrZero {score_list} {selected_index}"
        for index in range(len(scores))
        if index != selected_index
    ]
    statement = " ∧ ".join(
        [
            f"weightSum {score_list} = {denominator}",
            f"nthOrZero {score_list} {selected_index} = {scores[selected_index]}",
            *comparisons,
        ]
    )
    source = f'''import Std

namespace NanoInterpJevlikeAdapter

/- State slice: {BUNDLE_STATE_SLICE}. -/
def weightSum (values : List Nat) : Nat :=
  match values with
  | [] => 0
  | value :: rest => value + weightSum rest

def nthOrZero (values : List Nat) (index : Nat) : Nat :=
  match values, index with
  | value :: _, 0 => value
  | _ :: rest, index + 1 => nthOrZero rest index
  | _, _ => 0

def actionDigest : String := "{action_digest}"

theorem action_digest_bound : actionDigest = "{action_digest}" := by
  rfl

theorem {theorem_name} : {statement} := by
  decide

end NanoInterpJevlikeAdapter
'''
    return theorem_name, statement, source


def _validate_option_set(value: Any, context: str, scorer_identity: str) -> tuple[list[dict[str, str]], str]:
    option_set = _closed(
        value,
        {"context_digest", "options", "option_set_digest", "schema", "scorer_identity"},
        "option set",
    )
    _require(option_set["schema"] == OPTION_SET_SCHEMA, "option set schema version is invalid")
    _require(option_set["scorer_identity"] == scorer_identity, "option set scorer binding is invalid")
    _require(option_set["context_digest"] == _digest(context), "option set context binding is invalid")
    _assert_digest(option_set["context_digest"], "option set context")
    options = option_set["options"]
    _require(isinstance(options, list) and len(options) >= 2, "option ordering is invalid")
    normalized: list[dict[str, str]] = []
    for option in options:
        item = _closed(option, {"candidate_id", "kind"}, "hypothesis option")
        _require(
            isinstance(item["candidate_id"], str)
            and bool(item["candidate_id"])
            and isinstance(item["kind"], str)
            and item["kind"] in OPTION_KINDS,
            "hypothesis option fields are invalid",
        )
        normalized.append({"candidate_id": item["candidate_id"], "kind": item["kind"]})
    _require(
        len({item["candidate_id"] for item in normalized}) == len(normalized),
        "option ordering contains duplicate candidate IDs",
    )
    unsigned = {
        "context_digest": option_set["context_digest"],
        "options": normalized,
        "schema": OPTION_SET_SCHEMA,
        "scorer_identity": scorer_identity,
    }
    _require(option_set["option_set_digest"] == _digest(unsigned), "option set digest mismatch")
    return normalized, option_set["option_set_digest"]


def _validate_config(provenance: Any, action: Mapping[str, Any]) -> dict[str, Any]:
    expected_keys = {
        "adapter_identity",
        "config",
        "config_digest",
        "device",
        "encoder_identity",
        "quantization_schema",
        "runtime_identity",
        "scorer_checkpoint_digest",
        "seed",
        "upstream_revision",
    }
    provenance = _closed(provenance, expected_keys, "external provenance")
    config = _closed(
        provenance["config"],
        {
            "context_tokens",
            "device",
            "encoder_identity",
            "option_tokens",
            "quantization_scale",
            "rounding",
            "runtime_identity",
            "schema",
            "scorer_checkpoint_digest",
            "seed",
            "upstream_revision",
        },
        "adapter configuration",
    )
    _require(config["schema"] == ADAPTER_CONFIG_SCHEMA, "adapter configuration schema is invalid")
    _require(config["upstream_revision"] == PINNED_JEVLIKE_REVISION, "upstream revision is not pinned")
    _require(REVISION.fullmatch(config["upstream_revision"]) is not None, "upstream revision format is invalid")
    _assert_digest(config["scorer_checkpoint_digest"], "scorer checkpoint")
    _require(
        isinstance(config["device"], str)
        and config["device"] == "cpu"
        and isinstance(config["encoder_identity"], str)
        and bool(config["encoder_identity"])
        and isinstance(config["runtime_identity"], str)
        and bool(config["runtime_identity"]),
        "adapter runtime identity is invalid",
    )
    for key in ("context_tokens", "option_tokens", "quantization_scale"):
        _require(
            isinstance(config[key], int) and not isinstance(config[key], bool) and config[key] > 0,
            f"adapter configuration {key} is invalid",
        )
    _require(isinstance(config["seed"], int) and not isinstance(config["seed"], bool), "adapter seed is invalid")
    _require(config["rounding"] in ROUNDING, "adapter rounding is invalid")
    _require(provenance["config_digest"] == _digest(config), "adapter configuration digest mismatch")
    expected = {
        "adapter_identity": action["nano_identity"],
        "config": config,
        "config_digest": _digest(config),
        "device": config["device"],
        "encoder_identity": config["encoder_identity"],
        "quantization_schema": QUANTIZATION_SCHEMA,
        "runtime_identity": config["runtime_identity"],
        "scorer_checkpoint_digest": config["scorer_checkpoint_digest"],
        "seed": config["seed"],
        "upstream_revision": config["upstream_revision"],
    }
    _require(dict(provenance) == expected, "external provenance is not config-bound")
    return config


def _validate_action(action: Any) -> tuple[list[int], int, str, str]:
    action = _closed(
        action,
        {
            "action_digest",
            "action_version",
            "claim",
            "host_checkpoint_id",
            "host_context_hash",
            "inputs",
            "layer",
            "nano_identity",
            "outputs",
            "protocol_identity",
            "site",
            "state_slice",
            "timestamp",
        },
        "action",
    )
    _assert_digest(action["action_digest"], "action")
    _require(action["state_slice"] == BUNDLE_STATE_SLICE and action["protocol_identity"] == BUNDLE_PROTOCOL_ID, "action identity is invalid")
    _require(
        isinstance(action["action_version"], int)
        and not isinstance(action["action_version"], bool)
        and action["action_version"] >= 1,
        "action version is invalid",
    )
    _require(isinstance(action["timestamp"], str) and bool(action["timestamp"]), "action timestamp is invalid")
    _require(isinstance(action["host_checkpoint_id"], str) and bool(action["host_checkpoint_id"]), "host checkpoint identity is invalid")
    _assert_digest(action["host_context_hash"], "host context")
    _require(isinstance(action["nano_identity"], str) and bool(action["nano_identity"]), "nano identity is invalid")
    _require(isinstance(action["layer"], int) and not isinstance(action["layer"], bool) and action["layer"] >= 0, "action layer is invalid")
    _require(isinstance(action["site"], str) and bool(action["site"]), "action site is invalid")
    _require(action["action_digest"] == _digest({key: value for key, value in action.items() if key != "action_digest"}), "action digest mismatch")

    inputs = _closed(
        action["inputs"],
        {"activation", "context", "context_digest", "external_provenance", "external_scores", "option_set", "prompt", "quantization", "quantized_scores", "seed"},
        "action inputs",
    )
    _require(isinstance(inputs["context"], str) and bool(inputs["context"]), "action context is invalid")
    _require(isinstance(inputs["prompt"], str), "action prompt is invalid")
    _require(inputs["context_digest"] == _digest(inputs["context"]), "action context digest mismatch")
    _assert_digest(inputs["context_digest"], "action context")
    _require(isinstance(inputs["activation"], list) and all(isinstance(x, int) and not isinstance(x, bool) for x in inputs["activation"]), "activation capture is invalid")
    _require(isinstance(inputs["seed"], int) and not isinstance(inputs["seed"], bool), "action seed is invalid")

    config = _validate_config(inputs["external_provenance"], action)
    _require(inputs["external_provenance"]["seed"] == inputs["seed"], "external seed binding is invalid")
    options, option_set_digest = _validate_option_set(inputs["option_set"], inputs["context"], action["nano_identity"])
    _require(inputs["context_digest"] == inputs["option_set"]["context_digest"], "option-set context binding is invalid")
    _require(inputs["external_provenance"]["adapter_identity"] == action["nano_identity"], "adapter identity binding is invalid")

    quantization = _closed(inputs["quantization"], {"rounding", "scale", "schema"}, "quantization")
    _require(quantization["schema"] == QUANTIZATION_SCHEMA, "quantization schema is invalid")
    _require(quantization["rounding"] == config["rounding"] and quantization["scale"] == config["quantization_scale"], "quantization configuration is not bound")
    _require(quantization["rounding"] in ROUNDING and isinstance(quantization["scale"], int) and not isinstance(quantization["scale"], bool) and quantization["scale"] > 0, "quantization configuration is invalid")

    raw_scores = inputs["external_scores"]
    _require(isinstance(raw_scores, list) and len(raw_scores) == len(options), "external score count does not match ordered options")
    quantized = []
    for index, raw in enumerate(raw_scores):
        number = _decimal_text(raw, f"external score {index}")
        quantized.append(int((number * quantization["scale"]).to_integral_value(rounding=ROUNDING[quantization["rounding"]])))
    _require(inputs["quantized_scores"] == quantized, "quantized scores do not match exact probability capture")
    _require(all(isinstance(x, int) and not isinstance(x, bool) and x >= 0 for x in quantized), "quantized scores are invalid")
    denominator = sum(quantized)
    _require(denominator > 0, "quantized score denominator is not positive")

    outputs = _closed(outputs := action["outputs"], {"probabilities", "selected_index", "selected_option", "selected_option_kind", "status"}, "action outputs")
    _require(outputs["status"] == "HypothesisOnly", "action status must remain HypothesisOnly")
    probabilities = outputs["probabilities"]
    _require(
        isinstance(probabilities, list)
        and probabilities == [{"denominator": denominator, "numerator": score} for score in quantized],
        "probability normalization is invalid",
    )
    _require(isinstance(outputs["selected_index"], int) and not isinstance(outputs["selected_index"], bool), "selected index is invalid")
    selected_index = outputs["selected_index"]
    expected_index = max(range(len(quantized)), key=quantized.__getitem__)
    _require(selected_index == expected_index, "selected index is inconsistent with exact probabilities")
    selected = options[selected_index]
    _require(outputs["selected_option"] == selected["candidate_id"] and outputs["selected_option_kind"] == selected["kind"], "selected option is inconsistent with exact probabilities")

    claim = _closed(
        action["claim"],
        {"claim_key", "context_digest", "kind", "option_ids", "option_set_digest", "selected_index", "selected_option", "selected_option_kind", "scorer_identity", "type"},
        "action claim",
    )
    expected_ids = [item["candidate_id"] for item in options]
    _require(claim["type"] == "jevlike_hypothesis_ranking" and claim["kind"] == "hypothesis", "action claim type is invalid")
    _require(claim["option_ids"] == expected_ids, "claim option ordering is invalid")
    _require(claim["option_set_digest"] == option_set_digest and claim["context_digest"] == inputs["context_digest"] and claim["scorer_identity"] == action["nano_identity"], "claim binding is invalid")
    _require(claim["selected_index"] == selected_index and claim["selected_option"] == selected["candidate_id"] and claim["selected_option_kind"] == selected["kind"], "claim selected option binding is invalid")
    expected_key = f"{action['host_checkpoint_id']}:{action['layer']}:{action['site']}:jevlike-ranking:{option_set_digest}"
    _require(claim["claim_key"] == expected_key, "claim key is not digest-bound")
    _require(inputs["option_set"]["option_set_digest"] == option_set_digest, "option-set digest binding is invalid")
    return quantized, denominator, option_set_digest, selected["candidate_id"]


def _check_lean(source: str, project_dir: Path, command: Sequence[str], timeout_seconds: int) -> None:
    _require(bool(command), "Lean command is empty")
    if shutil.which(command[0]) is None:
        _fail(f"Lean checker unavailable: {command[0]}")
    try:
        with tempfile.TemporaryDirectory(prefix="independent-jevlike-proof-") as directory:
            path = Path(directory) / "bundle_proof.lean"
            path.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [*command, str(path)],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise IndependentBundleValidationError(f"Lean checker failed: {error}") from error
    if result.returncode != 0:
        _fail("Lean proof artifact did not check independently")


def _validate_proofs(proofs: Any, action: Mapping[str, Any], scores: Sequence[int], denominator: int, *, project_dir: Path, command: Sequence[str], timeout_seconds: int, check_lean: bool) -> int:
    _require(isinstance(proofs, list) and bool(proofs), "proof attempts are missing")
    checked = 0
    expected_theorem, expected_statement, expected_source = _expected_lean_artifact(action, scores, denominator)
    for proof in proofs:
        proof = _closed(
            proof,
            {"action_digest", "checker", "checker_version", "diagnostics", "proof_digest", "protocol_identity", "source", "state_slice", "statement", "status", "theorem_name"},
            "proof",
        )
        _assert_digest(proof["proof_digest"], "proof")
        _require(proof["proof_digest"] == _digest({key: value for key, value in proof.items() if key != "proof_digest"}), "proof digest mismatch")
        _require(proof["action_digest"] == action["action_digest"], "proof action binding mismatch")
        _require(proof["state_slice"] == BUNDLE_STATE_SLICE and proof["protocol_identity"] == BUNDLE_PROTOCOL_ID, "proof identity is invalid")
        _require(proof["status"] in {"checked", "failed"}, "proof status is invalid")
        _require(isinstance(proof["diagnostics"], list) and all(isinstance(item, str) for item in proof["diagnostics"]), "proof diagnostics are invalid")
        _require(isinstance(proof["checker"], str) and bool(proof["checker"]) and isinstance(proof["checker_version"], str) and bool(proof["checker_version"]), "proof checker identity is invalid")
        _require(isinstance(proof["theorem_name"], str) and isinstance(proof["statement"], str) and isinstance(proof["source"], str), "proof artifact fields are invalid")
        if proof["status"] == "checked":
            checked += 1
            _require(proof["checker"] == "lean-kernel", "checked proof checker is not Lean")
            _require(proof["theorem_name"] == expected_theorem and proof["statement"] == expected_statement and proof["source"] == expected_source, "checked proof artifact is not bound to action arithmetic")
            if check_lean:
                _check_lean(proof["source"], project_dir, command, timeout_seconds)
        else:
            _require(bool(proof["diagnostics"]), "failed proof attempt has no failure diagnostics")
    return checked


def validate_bundle(
    bundle: Mapping[str, Any],
    *,
    project_dir: Path | None = None,
    command: Sequence[str] = ("lake", "env", "lean"),
    timeout_seconds: int = 30,
    check_lean: bool = True,
) -> IndependentValidationReport:
    """Validate a semantic bundle and independently recheck checked proofs."""

    _require(isinstance(bundle, dict), "bundle must be an object")
    _closed(bundle, {"action", "bundle_digest", "proofs", "protocol_identity", "state_slice", "status", "summary"}, "bundle")
    _assert_digest(bundle["bundle_digest"], "bundle")
    _require(bundle["bundle_digest"] == _digest({key: value for key, value in bundle.items() if key != "bundle_digest"}), "bundle digest mismatch")
    _require(bundle["state_slice"] == BUNDLE_STATE_SLICE and bundle["protocol_identity"] == BUNDLE_PROTOCOL_ID, "bundle identity is invalid")
    _require(bundle["status"] == "HypothesisOnly", "bundle status must remain HypothesisOnly")
    _require(isinstance(bundle["summary"], str) and bool(bundle["summary"]), "bundle summary is invalid")
    action = bundle["action"]
    scores, denominator, _option_set_digest, selected_option = _validate_action(action)
    checked = _validate_proofs(
        bundle["proofs"],
        action,
        scores,
        denominator,
        project_dir=project_dir or Path(__file__).parents[2] / "formal" / "proof-carrying-nano-interp-v1",
        command=command,
        timeout_seconds=timeout_seconds,
        check_lean=check_lean,
    )
    expected_summary = (
        f"jevlike_hypothesis_ranking at layer {action['layer']} {action['site']} "
        f"selected {selected_option}; {checked}/{len(bundle['proofs'])} proof attempts kernel-checked."
    )
    _require(bundle["summary"] == expected_summary, "bundle summary is not bound to action and proof status")
    return IndependentValidationReport(
        valid=True,
        state_slice=STATE_SLICE,
        bundle_state_slice=BUNDLE_STATE_SLICE,
        status=bundle["status"],
        claim_ceiling=CLAIM_CEILING,
        action_digest=action["action_digest"],
        checked_proofs=checked,
        proof_attempts=len(bundle["proofs"]),
        checks=("schema", "digests", "exact_probability_capture", "selected_index", "proof_binding", "HypothesisOnly"),
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_bundle_path(
    path: Path,
    *,
    project_dir: Path | None = None,
    command: Sequence[str] = ("lake", "env", "lean"),
    timeout_seconds: int = 30,
    check_lean: bool = True,
) -> IndependentValidationReport:
    """Load canonical bundle bytes and validate them independently."""

    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), "bundle path must be a regular file")
    raw = path.read_bytes()
    try:
        bundle = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IndependentBundleValidationError("bundle is not valid JSON") from error
    _require(raw == _canonical(bundle), "bundle bytes are not canonical")
    return validate_bundle(
        bundle,
        project_dir=project_dir,
        command=command,
        timeout_seconds=timeout_seconds,
        check_lean=check_lean,
    )
