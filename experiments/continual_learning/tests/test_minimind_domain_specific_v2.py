"""Tests for the MiniMind domain-specific continual-learning V2 slice.

State slice: continual-learning-minimind-domain-specific-v2.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import minimind_domain_specific_v2 as experiment
from experiments.continual_learning import validate_minimind_domain_specific_v2 as validator


SOURCE_ROOT = Path(
    "/Users/shaanp/Documents/research-artifacts/"
    "continual-learning-minimind-domain-specific-v2-source-20260902"
)


def test_source_checkout_verifies_commit_remote_license_and_roster() -> None:
    observed = experiment.inspect_source(SOURCE_ROOT)
    manifest = observed["manifest"]
    assert manifest["commit"] == experiment.UPSTREAM_COMMIT
    assert manifest["remote_url"] == "https://github.com/jingyaogong/minimind.git"
    assert manifest["license"] == "Apache-2.0"
    assert [row["path"] for row in manifest["required_files"]] == list(experiment.REQUIRED_SOURCE_FILES)


def test_synthetic_v2_is_deterministic_exact_and_fresh() -> None:
    first = experiment.run_synthetic_campaign()
    second = experiment.run_synthetic_campaign()
    assert first == second
    assert first["state_slice"] == experiment.STATE_SLICE
    assert first["corpus"]["kind"] == "deterministic_exact_synthetic_v2"
    assert first["summary"]["disposition"] == "SyntheticCandidate"
    assert first["summary"]["prediction_lock"]["locked_arm"] == "domain_adapters"
    assert len(first["trials"]) == 108


def test_independent_validator_accepts_written_v2_artifact(tmp_path: Path) -> None:
    artifact = experiment.write_synthetic_campaign(tmp_path / "artifact", SOURCE_ROOT)
    assert validator.validate_artifact(Path(artifact["root"])) == {
        "valid": True,
        "state_slice": experiment.STATE_SLICE,
        "claim_ceiling": experiment.SYNTHETIC_CLAIM_CEILING,
        "disposition": "SyntheticCandidate",
        "trial_count": 108,
    }


def test_exact_order_seed_roster_is_fail_closed() -> None:
    result = experiment.run_synthetic_campaign()
    result["trials"][0]["order_seed"] = 9999
    with pytest.raises(experiment.ProtocolError, match="identity roster"):
        experiment.validate_synthetic_result(result)


def test_independent_validator_rejects_result_tampering(tmp_path: Path) -> None:
    artifact = experiment.write_synthetic_campaign(tmp_path / "artifact", SOURCE_ROOT)
    root = Path(artifact["root"])
    result_path = root / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["trials"][0]["order_seed"] = 9999
    result_path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="identity roster"):
        validator.validate_artifact(root)


def test_model_path_requires_independent_receipt_before_loading(tmp_path: Path) -> None:
    with pytest.raises(experiment.ProtocolError, match="receipt missing"):
        experiment.run_model_campaign(
            output=tmp_path / "model-artifact",
            source_root=SOURCE_ROOT,
            execution_receipt=tmp_path / "missing-receipt.json",
            corpus={},
        )


def test_receipt_requires_complete_frozen_file_digest_set(tmp_path: Path) -> None:
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": experiment.RECEIPT_SCHEMA_VERSION,
                "state_slice": experiment.STATE_SLICE,
                "review_packet_path": str(experiment.REVIEW_PACKET_PATH),
                "review_packet_sha256": experiment.sha256_file(experiment.REVIEW_PACKET_PATH),
                "reviewed_file_digests": {},
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
    with pytest.raises(experiment.ProtocolError, match="frozen-file digest set"):
        experiment.validate_execution_receipt(receipt_path)


def test_corpus_files_must_remain_external() -> None:
    corpus = {
        domain: {split: Path(__file__) for split in experiment.SPLITS}
        for domain in experiment.DOMAINS
    }
    with pytest.raises(experiment.ProtocolError, match="outside the repository"):
        experiment.build_corpus_manifest(corpus)


def test_source_cannot_be_inside_repository() -> None:
    with pytest.raises(experiment.ProtocolError, match="outside the repository"):
        experiment.inspect_source(experiment.REPO_ROOT)
