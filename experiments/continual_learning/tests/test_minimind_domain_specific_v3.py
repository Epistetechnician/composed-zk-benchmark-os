"""Hermetic tests for the MiniMind domain-specific continual-learning V3 slice.

State slice: continual-learning-minimind-domain-specific-v3.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from experiments.continual_learning import minimind_domain_specific_v3 as experiment
from experiments.continual_learning import validate_minimind_domain_specific_v3 as validator


SOURCE_ROOT = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-source-20260902")


def _corpus_fixture(tmp_path: Path, *, duplicate: bool = False) -> dict[str, dict[str, Path]]:
    root = tmp_path / experiment.CORPUS_ROOT_NAME
    root.mkdir(mode=0o700, parents=True)
    corpus: dict[str, dict[str, Path]] = {}
    index = 0
    for domain in experiment.DOMAINS:
        corpus[domain] = {}
        for split in experiment.SPLITS:
            path = root / f"{domain}-{split}.jsonl"
            document_id = "duplicate-document" if duplicate and index in {0, 1} else f"v3-document-{index}"
            author_id = "duplicate-author" if duplicate and index in {0, 1} else f"v3-author-{index}"
            path.write_text(json.dumps({"document_id": document_id, "author_id": author_id, "text": f"The {domain} research record for the {split} cohort contains enough tokens for the MiniMind language-model loss."}) + "\n", encoding="utf-8")
            corpus[domain][split] = path
            index += 1
    return corpus


def test_source_checkout_verifies_fresh_v3_identity() -> None:
    observed = experiment.inspect_source(SOURCE_ROOT)
    assert observed["manifest"]["state_slice"] == experiment.STATE_SLICE
    assert observed["manifest"]["commit"] == experiment.UPSTREAM_COMMIT
    assert observed["manifest"]["remote_url"] in {"https://github.com/jingyaogong/minimind", "https://github.com/jingyaogong/minimind.git"}
    assert observed["manifest"]["license"] == "Apache-2.0"


def test_synthetic_v3_is_deterministic_full_factorial_and_aggregate_only() -> None:
    first = experiment.run_synthetic_campaign()
    second = experiment.run_synthetic_campaign()
    assert first == second
    assert first["summary"]["disposition"] == "SyntheticCandidate"
    assert first["prediction_lock"]["locked_arm"] == "domain_adapters"
    assert len(first["aggregate_trials"]) == 108
    assert "trials" not in first
    assert all("stage_metrics" not in trial for trial in first["aggregate_trials"])


def test_independent_validator_accepts_written_v3_artifact(tmp_path: Path) -> None:
    artifact = experiment.write_synthetic_campaign(tmp_path / experiment.SYNTHETIC_ROOT_NAME, SOURCE_ROOT)
    assert validator.validate_artifact(Path(artifact["root"])) == {
        "valid": True,
        "state_slice": experiment.STATE_SLICE,
        "claim_ceiling": experiment.SYNTHETIC_CLAIM_CEILING,
        "disposition": "SyntheticCandidate",
        "trial_count": 108,
    }


def test_validator_rejects_wrong_mode_and_extra_files(tmp_path: Path) -> None:
    artifact = experiment.write_synthetic_campaign(tmp_path / experiment.SYNTHETIC_ROOT_NAME, SOURCE_ROOT)
    root = Path(artifact["root"])
    os.chmod(root, 0o755)
    with pytest.raises(validator.ValidationError, match="owner-only"):
        validator.validate_artifact(root)
    os.chmod(root, 0o700)
    (root / "extra.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="file set"):
        validator.validate_artifact(root)


def test_validator_rejects_tampered_roster_and_guard_schema(tmp_path: Path) -> None:
    artifact = experiment.write_synthetic_campaign(tmp_path / experiment.SYNTHETIC_ROOT_NAME, SOURCE_ROOT)
    root = Path(artifact["root"])
    result_path = root / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["aggregate_trials"][0]["order_seed"] = 9999
    result_path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="identity roster"):
        validator.validate_artifact(root)
    result["aggregate_trials"][0]["order_seed"] = experiment.ORDER_SEEDS[0]
    result["aggregate_trials"][0]["hard_guards"] = {}
    result_path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="hard-guard"):
        validator.validate_artifact(root)


def test_corpus_requires_global_document_and_author_disjointness(tmp_path: Path) -> None:
    with pytest.raises(experiment.ProtocolError, match="document IDs"):
        experiment.build_corpus_manifest(_corpus_fixture(tmp_path, duplicate=True))


def test_corpus_rejects_repository_and_prior_artifact_paths(tmp_path: Path) -> None:
    corpus = _corpus_fixture(tmp_path)
    corpus["materials"]["fit"] = experiment.REPO_ROOT / "README.md"
    with pytest.raises(experiment.ProtocolError, match="external"):
        experiment.build_corpus_manifest(corpus)
    corpus = _corpus_fixture(tmp_path / "second")
    corpus["materials"]["fit"] = experiment.FORBIDDEN_PRIOR_ROOTS[0] / "data.jsonl"
    with pytest.raises(experiment.ProtocolError, match="external regular"):
        experiment.build_corpus_manifest(corpus)


def test_model_path_checks_corpus_before_import_and_receipt(tmp_path: Path) -> None:
    corpus = _corpus_fixture(tmp_path)
    with pytest.raises(experiment.ProtocolError, match="receipt"):
        experiment.run_model_campaign(
            output=tmp_path / experiment.MODEL_ROOT_NAME,
            source_root=SOURCE_ROOT,
            execution_receipt=tmp_path / "missing-receipt.json",
            corpus=corpus,
        )


def test_operator_labeled_receipt_cannot_pass_independence_gate(tmp_path: Path) -> None:
    receipt = {
        "schema_version": experiment.RECEIPT_SCHEMA_VERSION,
        "state_slice": experiment.STATE_SLICE,
        "review_packet_path": str(experiment.REVIEW_PACKET_PATH),
        "review_packet_sha256": "0" * 64,
        "reviewed_file_digests": {},
        "reviewer_registry_path": str(experiment.REVIEWER_REGISTRY_PATH),
        "reviewer_registry_sha256": "0" * 64,
        "reviewer_identity": experiment.OPERATOR_ID,
        "reviewer_role": experiment.REVIEWER_ROLE,
        "reviewer_certificate_sha256": "0" * 64,
        "operator_identity": experiment.OPERATOR_ID,
        "operator_binding_path": str(experiment.OPERATOR_BINDING_PATH),
        "operator_binding_sha256": "0" * 64,
        "reviewer_public_key_hex": "0" * 64,
        "corpus_manifest_sha256": "0" * 64,
        "source_manifest_sha256": "0" * 64,
        "disposition": "ACCEPTED_FOR_MODEL_EXECUTION",
        "signature_algorithm": "Ed25519",
        "signature": "0" * 128,
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(experiment.ProtocolError, match="independence"):
        experiment.validate_execution_receipt(receipt_path)


def test_model_contract_rejects_empty_hard_guards(tmp_path: Path) -> None:
    root = tmp_path / experiment.MODEL_ROOT_NAME
    root.mkdir(mode=0o700)
    (root / "contract.json").write_text(json.dumps({"claim_ceiling": experiment.MODEL_CLAIM_CEILING, "hard_guards": {}}), encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="schema"):
        validator.validate_artifact(root)


def test_source_cannot_be_inside_repository() -> None:
    with pytest.raises(experiment.ProtocolError, match="outside"):
        experiment.inspect_source(experiment.REPO_ROOT)
