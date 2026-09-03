"""Tests for the MiniMind domain-sequence state slice.

State slice: continual-learning-minimind-domain-specific-v1.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import minimind_domain_specific_v1 as experiment
from experiments.continual_learning import validate_minimind_domain_specific_v1 as validator


SOURCE_ROOT = Path(
    "/Users/shaanp/Documents/research-artifacts/"
    "continual-learning-minimind-domain-specific-v1-source-20260902"
)


def test_source_checkout_is_frozen_and_complete() -> None:
    manifest = experiment.inspect_source(SOURCE_ROOT)
    assert manifest["manifest"]["commit"] == experiment.UPSTREAM_COMMIT
    assert [row["path"] for row in manifest["manifest"]["required_files"]] == list(
        experiment.REQUIRED_SOURCE_FILES
    )


def test_synthetic_campaign_is_deterministic_and_candidate_bounded() -> None:
    first = experiment.run_synthetic_campaign()
    second = experiment.run_synthetic_campaign()
    assert first == second
    assert first["training_executed"] is False
    assert first["model_loaded"] is False
    assert first["inference_executed"] is False
    assert first["summary"]["prediction_lock"]["locked_arm"] == "domain_adapters"
    assert first["summary"]["disposition"] == "SyntheticCandidate"
    assert len(first["trials"]) == 108


def test_independent_validator_accepts_written_artifact(tmp_path: Path) -> None:
    artifact = experiment.write_synthetic_campaign(tmp_path / "artifact", SOURCE_ROOT)
    validated = validator.validate_artifact(Path(artifact["root"]))
    assert validated == {
        "valid": True,
        "state_slice": experiment.STATE_SLICE,
        "claim_ceiling": experiment.CLAIM_CEILING,
        "disposition": "SyntheticCandidate",
        "trial_count": 108,
    }


def test_runner_rejects_trial_tampering() -> None:
    result = experiment.run_synthetic_campaign()
    result["trials"][0]["final_mean_loss"] += 0.01
    with pytest.raises(experiment.ProtocolError, match="trial arithmetic"):
        experiment.validate_synthetic_result(result)


def test_independent_validator_rejects_result_tampering(tmp_path: Path) -> None:
    artifact = experiment.write_synthetic_campaign(tmp_path / "artifact", SOURCE_ROOT)
    root = Path(artifact["root"])
    result_path = root / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["trials"][0]["primary_improvement"] += 0.01
    result_path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="trial arithmetic"):
        validator.validate_artifact(root)


def test_model_path_requires_independent_receipt_before_loading(tmp_path: Path) -> None:
    with pytest.raises(experiment.ProtocolError, match="receipt missing"):
        experiment.run_model_campaign(
            output=tmp_path / "model-artifact",
            source_root=SOURCE_ROOT,
            execution_receipt=tmp_path / "missing-receipt.json",
            corpus={},
        )


def test_execution_receipt_rejects_operator_self_signature(tmp_path: Path) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": experiment.RECEIPT_SCHEMA_VERSION,
                "state_slice": experiment.STATE_SLICE,
                "review_packet_path": str(experiment.REVIEW_PACKET_PATH),
                "review_packet_sha256": "0" * 64,
                "reviewer_role": "independent",
                "reviewer_identity": "same-person",
                "operator_identity": "same-person",
                "disposition": "ACCEPTED_FOR_MODEL_EXECUTION",
                "signature_algorithm": "Ed25519",
                "public_key": "00" * 32,
                "signature": "00" * 64,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(experiment.ProtocolError, match="cannot be the independent reviewer"):
        experiment.validate_execution_receipt(receipt_path)


def test_execution_receipt_rejects_stale_review_packet_digest(tmp_path: Path) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": experiment.RECEIPT_SCHEMA_VERSION,
                "state_slice": experiment.STATE_SLICE,
                "review_packet_path": str(experiment.REVIEW_PACKET_PATH),
                "review_packet_sha256": "0" * 64,
                "reviewer_role": "independent",
                "reviewer_identity": "independent-reviewer",
                "operator_identity": "operator",
                "disposition": "ACCEPTED_FOR_MODEL_EXECUTION",
                "signature_algorithm": "Ed25519",
                "public_key": "00" * 32,
                "signature": "00" * 64,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(experiment.ProtocolError, match="packet digest mismatch"):
        experiment.validate_execution_receipt(receipt_path)


def test_source_cannot_be_inside_repository() -> None:
    with pytest.raises(experiment.ProtocolError, match="outside the repository"):
        experiment.inspect_source(experiment.REPO_ROOT)
