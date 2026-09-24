"""Independent validator and Lean/store tests for causal records.

State slice: proof-carrying-nano-causal-intervention-record-v1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.proof_carrying_nano_causal_intervention_record_v1.proof import (
    CausalInterventionLeanProofEngine,
    expected_lean_artifact,
)
from tools.proof_carrying_nano_causal_intervention_record_v1.store import (
    CausalInterventionStore,
)
from tools.proof_carrying_nano_jevlike_independent_validation_v1.causal_intervention import (
    IndependentCausalValidationError,
    validate_causal_bundle,
)
from tools.proof_carrying_nano_interp_v1.protocol import canonical_digest

from .test_record import _record


def _bundle(tmp_path: Path) -> dict:
    record = _record()
    proof = CausalInterventionLeanProofEngine().attempt(record)
    assert proof.status == "checked", proof.diagnostics
    with CausalInterventionStore(tmp_path / "store.sqlite3") as store:
        store.commit_record(record)
        store.commit_proof(proof)
        return store.export_bundle(record_digest=record["record_digest"])


def _rebind(bundle: dict) -> None:
    record = bundle["record"]
    operator = record["intervention_operator"]
    operator["operator_digest"] = canonical_digest(
        {key: value for key, value in operator.items() if key != "operator_digest"}
    )
    record["claim"]["operator_digest"] = operator["operator_digest"]
    record["record_digest"] = canonical_digest(
        {key: value for key, value in record.items() if key != "record_digest"}
    )
    for proof in bundle["proofs"]:
        proof["action_digest"] = record["record_digest"]
        proof["proof_digest"] = canonical_digest(
            {key: value for key, value in proof.items() if key != "proof_digest"}
        )
    bundle["bundle_digest"] = canonical_digest(
        {key: value for key, value in bundle.items() if key != "bundle_digest"}
    )


def test_record_bundle_is_record_only_and_independently_validated(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    report = validate_causal_bundle(bundle)
    assert report.valid is True
    assert report.status == "CausalInterventionRecordOnly"
    assert report.assessment_status == "SEALED_UNTIL_INDEPENDENT_REVIEW"
    assert report.checked_proofs == 1


def test_failed_proof_attempt_remains_explicit_and_record_only(tmp_path: Path) -> None:
    record = _record(proof_status="failed")
    proof = CausalInterventionLeanProofEngine().attempt(record)
    assert proof.status == "failed"
    assert proof.diagnostics
    with CausalInterventionStore(tmp_path / "store.sqlite3") as store:
        store.commit_record(record)
        store.commit_proof(proof)
        bundle = store.export_bundle(record_digest=record["record_digest"])
    report = validate_causal_bundle(bundle)
    assert report.valid is True
    assert report.checked_proofs == 0
    assert report.proof_attempts == 1


def test_generated_proof_imports_committed_formal_module() -> None:
    theorem_name, _statement, source = expected_lean_artifact(_record())
    assert theorem_name.startswith("causal_intervention_")
    assert "import NanoInterp.CausalInterventionRecord" in source
    assert "def causalInterventionRecordBinding" not in source


def test_validator_rejects_unbound_checker_environment(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["proofs"][0]["checker_version"] = "lake-env-lean"
    bundle["proofs"][0]["proof_digest"] = canonical_digest(
        {key: value for key, value in bundle["proofs"][0].items() if key != "proof_digest"}
    )
    bundle["bundle_digest"] = canonical_digest(
        {key: value for key, value in bundle.items() if key != "bundle_digest"}
    )
    with pytest.raises(IndependentCausalValidationError, match="checker|environment|toolchain"):
        validate_causal_bundle(bundle)


def test_validator_rejects_malformed_failed_proof_metadata(tmp_path: Path) -> None:
    record = _record(proof_status="failed")
    proof = CausalInterventionLeanProofEngine().attempt(record)
    with CausalInterventionStore(tmp_path / "store.sqlite3") as store:
        store.commit_record(record)
        store.commit_proof(proof)
        bundle = store.export_bundle(record_digest=record["record_digest"])
    bundle["proofs"][0].update(
        {
            "checker": 123,
            "checker_version": None,
            "source": [],
            "statement": False,
            "theorem_name": {"not": "text"},
        }
    )
    bundle["proofs"][0]["proof_digest"] = canonical_digest(
        {key: value for key, value in bundle["proofs"][0].items() if key != "proof_digest"}
    )
    bundle["bundle_digest"] = canonical_digest(
        {key: value for key, value in bundle.items() if key != "bundle_digest"}
    )
    with pytest.raises(IndependentCausalValidationError, match="schema|metadata|type"):
        validate_causal_bundle(bundle)


def test_validator_is_independent_of_causal_producer_modules() -> None:
    source = Path(__file__).parents[2] / "proof_carrying_nano_jevlike_independent_validation_v1" / "causal_intervention.py"
    text = source.read_text(encoding="utf-8")
    assert "proof_carrying_nano_causal_intervention_record_v1" not in text
    assert "CausalInterventionLeanProofEngine" not in text
    assert "CausalInterventionStore" not in text


def test_validator_rejects_donor_target_mismatch_even_after_digest_rebinding(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    parameters = bundle["record"]["intervention_operator"]["parameters"]
    parameters["source_activation_digest"] = bundle["record"]["target"]["activation_digest"]
    _rebind(bundle)
    with pytest.raises(IndependentCausalValidationError, match="donor|source activation"):
        validate_causal_bundle(bundle)


def test_validator_rejects_altered_operator_and_effect_tampering(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["record"]["intervention_operator"]["type"] = "interpolate_token_vector"
    _rebind(bundle)
    with pytest.raises(IndependentCausalValidationError, match="operator"):
        validate_causal_bundle(bundle)

    bundle = _bundle(tmp_path)
    bundle["record"]["effect"]["value"] = "0.500000"
    with pytest.raises(IndependentCausalValidationError, match="effect digest|record digest"):
        validate_causal_bundle(bundle)


def test_validator_rejects_missing_controls_and_replay_divergence(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["record"]["controls"] = []
    bundle["record"]["claim"]["controls_digest"] = canonical_digest([])
    _rebind(bundle)
    with pytest.raises(IndependentCausalValidationError, match="control"):
        validate_causal_bundle(bundle)

    bundle = _bundle(tmp_path)
    bundle["record"]["replay"]["replay_seed"] = 18
    _rebind(bundle)
    with pytest.raises(IndependentCausalValidationError, match="replay"):
        validate_causal_bundle(bundle)


def test_validator_rejects_host_mutation_and_proof_status_mismatch(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    bundle["record"]["host_parameter_digest_after"] = "sha256:" + "f" * 64
    _rebind(bundle)
    with pytest.raises(IndependentCausalValidationError, match="parameter|host"):
        validate_causal_bundle(bundle)

    bundle = _bundle(tmp_path)
    bundle["record"]["proof_status"] = "failed"
    _rebind(bundle)
    with pytest.raises(IndependentCausalValidationError, match="proof status"):
        validate_causal_bundle(bundle)
