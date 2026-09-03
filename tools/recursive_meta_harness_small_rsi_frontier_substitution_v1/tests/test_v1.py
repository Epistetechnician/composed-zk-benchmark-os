"""Hermetic tests for the bounded small-RSI substitution contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

from recursive_meta_harness_small_rsi_frontier_substitution_v1 import compiler_v1, protocol_v1, review_v1, runner_v1, validator_v1


def test_manifest_is_frozen_and_execution_is_closed() -> None:
    manifest = compiler_v1.compile_manifest()
    validator_v1.validate_manifest(manifest)
    assert manifest["state_slice"] == protocol_v1.STATE_SLICE
    assert manifest["execution_authorized"] is False
    assert manifest["protocol"]["execution_boundary"]["model_execution_allowed"] is False
    assert manifest["protocol"]["task_plan"]["assessment_access"] == "sealed_until_prediction_lock_and_independent_review"


def test_pending_review_packet_is_bound_and_non_authorizing() -> None:
    packet = review_v1.build_packet(compiler_v1.compile_manifest())
    validator_v1.validate_review_packet(packet)
    assert packet["decision"] == "PENDING_INDEPENDENT_REVIEW"
    assert packet["model_execution_authorized"] is False
    assert packet["operator_may_self_sign"] is False


def test_contract_fixture_is_deterministic_and_independently_validated() -> None:
    first = runner_v1.run_contract_fixture()
    second = runner_v1.run_contract_fixture()
    assert first == second
    validator_v1.validate_fixture(json.loads(json.dumps(first)))
    assert len(first["observations"]) == 192
    assert first["scientific_claim"] is False
    assert first["boundary"]["model_execution"] == "not_run"
    assert first["summary"]["assessment_comparison"] == "sealed_not_computed"
    assert len({row["total_verified_utility_micros"] for row in first["summary"]["arms"].values()}) == 1


def test_full_cost_is_fixed_point_and_missing_components_fail_closed() -> None:
    observation = runner_v1._observation("small_swarm_rsi", "repository_coding", "fit", 0, 0)
    total = protocol_v1.validate_cost(observation["cost"])
    assert total == sum(observation["cost"].values())
    missing = dict(observation["cost"])
    missing.pop("cleanup_micros")
    with pytest.raises(protocol_v1.ProtocolError, match="cost schema"):
        protocol_v1.validate_cost(missing)


def test_hard_constraint_failure_zeroes_verified_utility() -> None:
    observation = runner_v1._observation("small_single", "research_synthesis", "tune", 1, 1)
    observation["constraint_results"] = {**observation["constraint_results"], "authority": False}
    evaluated = protocol_v1.validate_observation(observation)
    assert evaluated["verified_utility_micros"] == 0
    assert evaluated["constraint_failures"] == ["authority"]


def test_assessment_observation_is_rejected_while_sealed() -> None:
    observation = runner_v1._observation("frontier_single", "repository_coding", "assessment", 0, 0)
    with pytest.raises(protocol_v1.ProtocolError, match="assessment is sealed"):
        protocol_v1.validate_observation(observation)


def test_independent_validator_rejects_tampering() -> None:
    fixture = runner_v1.run_contract_fixture()
    tampered = json.loads(json.dumps(fixture))
    tampered["observations"][0]["objective_score_micros"] += 1
    tampered["fixture_sha256"] = protocol_v1.digest({key: value for key, value in tampered.items() if key != "fixture_sha256"})
    with pytest.raises(validator_v1.ValidationError, match="evaluated rows do not match"):
        validator_v1.validate_fixture(tampered)


def test_independent_validator_rejects_manifest_drift() -> None:
    manifest = compiler_v1.compile_manifest()
    tampered = json.loads(json.dumps(manifest))
    tampered["protocol"]["metric"]["non_inferiority_margin_micros"] = -30000
    tampered["protocol_sha256"] = protocol_v1.digest(tampered["protocol"])
    tampered["manifest_sha256"] = protocol_v1.digest({key: value for key, value in tampered.items() if key != "manifest_sha256"})
    with pytest.raises(validator_v1.ValidationError, match="protocol digest"):
        validator_v1.validate_manifest(tampered)


def test_operator_cannot_supply_independent_accept() -> None:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    packet = review_v1.build_packet(compiler_v1.compile_manifest())
    private_key = Ed25519PrivateKey.generate()
    unsigned = {
        "schema_version": review_v1.REVIEW_RECEIPT_SCHEMA_VERSION,
        "state_slice": protocol_v1.STATE_SLICE,
        "protocol_id": protocol_v1.PROTOCOL_ID,
        "review_scope": review_v1.REVIEW_SCOPE,
        "decision": "ACCEPT",
        "packet_sha256": packet["packet_sha256"],
        "reviewer_identity": "operator-1",
        "reviewer_role": "independent reviewer who did not author, configure, or execute this lane",
        "operator_identity": "operator-1",
        "model_execution_authorized": False,
        "assessment_open": False,
        "public_key_hex": private_key.public_key().public_bytes_raw().hex(),
    }
    receipt_sha = protocol_v1.digest(unsigned)
    message = protocol_v1.canonical_bytes({**unsigned, "receipt_sha256": receipt_sha})
    receipt = {**unsigned, "signature_hex": private_key.sign(message).hex(), "receipt_sha256": receipt_sha}
    with pytest.raises(protocol_v1.ProtocolError, match="not independent"):
        review_v1.validate_signed_acceptance(packet, receipt, operator_identity="operator-1")


def test_independent_acceptance_is_cryptographically_bound_but_non_authorizing() -> None:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    packet = review_v1.build_packet(compiler_v1.compile_manifest())
    private_key = Ed25519PrivateKey.generate()
    unsigned = {
        "schema_version": review_v1.REVIEW_RECEIPT_SCHEMA_VERSION,
        "state_slice": protocol_v1.STATE_SLICE,
        "protocol_id": protocol_v1.PROTOCOL_ID,
        "review_scope": review_v1.REVIEW_SCOPE,
        "decision": "ACCEPT",
        "packet_sha256": packet["packet_sha256"],
        "reviewer_identity": "reviewer-1",
        "reviewer_role": review_v1.REVIEWER_ROLE,
        "operator_identity": "operator-1",
        "model_execution_authorized": False,
        "assessment_open": False,
        "public_key_hex": private_key.public_key().public_bytes_raw().hex(),
    }
    receipt_sha = protocol_v1.digest(unsigned)
    message = protocol_v1.canonical_bytes({**unsigned, "receipt_sha256": receipt_sha})
    receipt = {**unsigned, "signature_hex": private_key.sign(message).hex(), "receipt_sha256": receipt_sha}
    review_v1.validate_signed_acceptance(packet, receipt, operator_identity="operator-1")
    assert receipt["model_execution_authorized"] is False
    assert receipt["assessment_open"] is False


def test_review_packet_writer_refuses_overwrite(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    packet_path = tmp_path / "review-packet.json"
    compiler_v1.write_manifest(compiler_v1.compile_manifest(), manifest_path)
    review_v1.write_packet(
        review_v1.build_packet(json.loads(manifest_path.read_text(encoding="utf-8"))),
        packet_path,
    )
    validator_v1.validate_review_packet(json.loads(packet_path.read_text(encoding="utf-8")))
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        review_v1.write_packet(
            review_v1.build_packet(json.loads(manifest_path.read_text(encoding="utf-8"))),
            packet_path,
        )


def test_fixture_writer_refuses_overwrite(tmp_path: Path) -> None:
    fixture = runner_v1.run_contract_fixture()
    output = tmp_path / "fixture.json"
    runner_v1.write_fixture(fixture, output)
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        runner_v1.write_fixture(fixture, output)


def test_manifest_writer_and_cli_artifact_chain(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    fixture_path = tmp_path / "fixture.json"
    compiler_v1.write_manifest(compiler_v1.compile_manifest(), manifest_path)
    runner_v1.write_fixture(runner_v1.run_contract_fixture(), fixture_path)
    validator_v1.validate_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    validator_v1.validate_fixture(json.loads(fixture_path.read_text(encoding="utf-8")))
