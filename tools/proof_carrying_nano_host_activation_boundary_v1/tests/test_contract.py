"""Closed schema, validator, proof, and store tests for activation capture.

State slice: proof-carrying-nano-host-activation-boundary-v1.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from tools.proof_carrying_nano_host_activation_boundary_v1.proof import (
    ActivationLeanProofEngine,
)
from tools.proof_carrying_nano_host_activation_boundary_v1.store import ActivationStore
from tools.proof_carrying_nano_jevlike_independent_validation_v1.activation import (
    IndependentActivationValidationError,
    validate_activation_bundle,
)
from tools.proof_carrying_nano_interp_v1.protocol import canonical_digest

from .test_adapter import _adapter


def _bundle(tmp_path: Path) -> dict:
    capture = _adapter().capture_tokens(
        input_ids=(1, 2, 3),
        attention_mask=(1, 1, 1),
        layer=1,
        site="decoder_block_output",
        token_position=2,
        replay_seed=17,
        timestamp="2026-09-17T12:00:00Z",
    )
    proof = ActivationLeanProofEngine().attempt(capture.action)
    assert proof.status == "checked", proof.diagnostics
    with ActivationStore(tmp_path / "store.sqlite3") as store:
        store.commit_action(capture.action)
        store.commit_proof(proof)
        return store.export_bundle(action_digest=capture.action["action_digest"])


def test_activation_bundle_is_independently_validated_and_checked(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    assert bundle["action"]["activation_schema"] == "host-activation-capture-v1"
    report = validate_activation_bundle(bundle)
    assert report.valid is True
    assert report.checked_proofs == 1
    assert report.status == "ActivationCaptureOnly"


def test_activation_validator_is_independent_of_producer_modules() -> None:
    source = Path(__file__).parents[2] / "proof_carrying_nano_jevlike_independent_validation_v1" / "activation.py"
    text = source.read_text(encoding="utf-8")
    assert "proof_carrying_nano_host_activation_boundary_v1.adapter" not in text
    assert "ActivationLeanProofEngine" not in text
    assert "ActivationStore" not in text


def test_validator_rejects_schema_extra_key_and_digest_rebinding(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["action"]["hook_identity"]["forged"] = True
    with pytest.raises(IndependentActivationValidationError, match="closed|digest"):
        validate_activation_bundle(bundle)

    bundle = _bundle(tmp_path)
    bundle["action"]["outputs"]["hook_reached"] = False
    with pytest.raises(IndependentActivationValidationError, match="digest"):
        validate_activation_bundle(bundle)


def test_validator_rejects_activation_digest_parameter_digest_and_proof_tampering(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["action"]["outputs"]["activation_digest"] = "sha256:" + "f" * 64
    bundle["action"]["action_digest"] = "sha256:" + "0" * 64
    with pytest.raises(IndependentActivationValidationError, match="digest"):
        validate_activation_bundle(bundle)

    bundle = _bundle(tmp_path)
    rebound = deepcopy(bundle)
    rebound["action"]["outputs"]["parameter_digest_after"] = "sha256:" + "f" * 64
    rebound["action"]["action_digest"] = "sha256:" + "1" * 64
    with pytest.raises(IndependentActivationValidationError, match="digest"):
        validate_activation_bundle(rebound)

    bundle = _bundle(tmp_path)
    bundle["proofs"][0]["source"] = bundle["proofs"][0]["source"].replace("by\n  simp [readOnlyActivationBinding]", "by\n  trivial")
    bundle["proofs"][0]["proof_digest"] = canonical_digest(
        {key: value for key, value in bundle["proofs"][0].items() if key != "proof_digest"}
    )
    bundle["bundle_digest"] = canonical_digest(
        {key: value for key, value in bundle.items() if key != "bundle_digest"}
    )
    with pytest.raises(IndependentActivationValidationError, match="proof"):
        validate_activation_bundle(bundle)


def test_validator_rejects_non_read_only_policy_and_wrong_binding(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["action"]["mutation_policy"]["activation_mutation"] = True
    with pytest.raises(IndependentActivationValidationError, match="read-only|digest"):
        validate_activation_bundle(bundle)

    bundle = _bundle(tmp_path)
    bundle["action"]["claim"]["layer"] = 99
    with pytest.raises(IndependentActivationValidationError, match="digest"):
        validate_activation_bundle(bundle)
